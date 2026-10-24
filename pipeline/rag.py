"""
pipeline/rag.py
===============
Agentic RAG search CLI.

Usage:
    python -m pipeline.rag "Find me a song that captures the emotional intensity of Interstellar"
    python -m pipeline.rag "What movies feel like Bohemian Rhapsody?"
    python -m pipeline.rag "Find characters with a moral conflict like The Joker"

Pipeline (5 steps):
    A. Intent Extraction  (LLM)  — parse which entity + what to find
    B. Context Retrieval  (DB)   — fetch the reference entity's emotional logic
    C. Query Generation   (LLM)  — turn that emotional logic into a dense search string
    D. Vector Search      (DB)   — embed the search string, find top matches
    E. Final Answer       (LLM)  — synthesise a human-readable recommendation
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

from groq import Groq

from pipeline import config, db, llm, trend
from pipeline.live_enrich import enrich_live
from pipeline.search_db import get_entity_by_name, vector_search


# ------------------------------------------------------------------
# Tunables
# ------------------------------------------------------------------
SHORTLIST_K = 10          # candidates retrieved and scored by the reasoning scorer
MAX_IDEAS = 4             # ideas shown to the user
WRITE_TOP = 5             # only this many candidates get a written why/idea (keeps output tokens low)
MIN_R = 0.35              # reasoning score below this is not shown as an idea
MIN_EMOTIONAL = 0.4       # ...and neither is an entry whose emotional match is below this
# Score = LAMBDA_COS * cos(rescaled on a fixed range) + LAMBDA_R * R + LAMBDA_T * T,
# where T is the live trend signal (songs only, see pipeline/trend.py). A candidate
# without T is scored on the other two terms alone, rescaled to the same 0..1 range.
# Initial guesses, to be tuned with the evaluation harness (pipeline/eval).
LAMBDA_COS = 0.35
LAMBDA_R = 0.50
LAMBDA_T = 0.15
# R is the weighted mean of the rubric dimensions below.
R_WEIGHTS = {"emotional_match": 0.5, "tone": 0.25, "usability": 0.25}


# ------------------------------------------------------------------
# Groq client (shared with llm_synthesize but kept local here for clarity)
# ------------------------------------------------------------------
def _get_client() -> Groq:
    return llm.get_client()


def _call_llm(client: Groq, prompt: str) -> str:
    return llm.chat(prompt, temperature=0.1, client=client)


def _extract_json(text: str) -> dict:
    """Extract the last complete JSON object from LLM output."""
    last_close = text.rfind("}")
    if last_close == -1:
        return {}
    depth = 0
    for i in range(last_close, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[i: last_close + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


# ------------------------------------------------------------------
# Step A: Intent extraction
# ------------------------------------------------------------------
_INTENT_PROMPT = """\
You are a router for a media knowledge database.
The database contains four types of records: movies, characters, relationships, and songs.

Analyze the user's query and respond with ONLY a JSON object with these exact fields:
{{
  "reference_entity": "<name of the specific movie, character, or song the user mentions, or null>",
  "reference_type": "<what the reference entity is: movie | character | song | null>",
  "reference_context": "<for a character: the movie it is from; for a song: the artist; otherwise null>",
  "target_type": "<what they want to find: movies | characters | relationships | songs | null>",
  "matching_concept": "<the attribute they want to match, e.g. 'emotional intensity', 'tone', 'character dynamic'>"
}}

User query: {query}
"""

def step_a_extract_intent(client: Groq, query: str) -> dict:
    print("  [A] Parsing query intent …")
    raw = _call_llm(client, _INTENT_PROMPT.format(query=query))
    intent = _extract_json(raw)
    print(f"       reference_entity = {intent.get('reference_entity')!r}")
    print(f"       reference_type   = {intent.get('reference_type')!r}")
    print(f"       target_type      = {intent.get('target_type')!r}")
    print(f"       matching_concept = {intent.get('matching_concept')!r}")
    return intent


# ------------------------------------------------------------------
# Step B: Context retrieval (DB)
# ------------------------------------------------------------------
def step_b_get_context(conn, reference_entity: str | None) -> dict | None:
    if not reference_entity:
        return None
    print(f"  [B] Fetching '{reference_entity}' from database …")
    entity = get_entity_by_name(conn, reference_entity)
    if entity:
        print(f"       Found: [{entity['type']}] {entity['name']}")
    else:
        print(f"       ⚠️  '{reference_entity}' not found in DB — will fall back to query embedding.")
    return entity


# ------------------------------------------------------------------
# Step B2: live lookup when the reference is not in the database
# ------------------------------------------------------------------
def step_b2_live_lookup(intent: dict) -> dict | None:
    name = intent.get("reference_entity")
    print(f"  [B2] '{name}' not in database — looking it up live …")
    entity = enrich_live(name, intent.get("reference_type"), intent.get("reference_context"))
    if entity:
        print(f"       Grounded live from {entity['sources']}: [{entity['type']}] {entity['name']}")
    else:
        print("       Could not ground it live — falling back to the raw query.")
    return entity


# ------------------------------------------------------------------
# Step C: Search string generation (LLM)
# ------------------------------------------------------------------
_SEARCH_STRING_PROMPT = """\
You are building a semantic search query for a vector database.

A user wants to find {target_type} that match the {matching_concept} of the following entity:

Entity name: {entity_name}
Description: {description}
Core emotional logic: {core_emotional_logic}

Write a single dense paragraph (3-5 sentences) that captures the essence of what we are searching for.
This paragraph will be embedded and used for cosine similarity search, so it must be rich in emotional,
thematic, and tonal vocabulary — NOT a question or instruction.

Return ONLY the paragraph. No JSON, no preamble, no explanation.
"""

def step_c_generate_search_string(client: Groq, entity: dict, target_type: str, matching_concept: str) -> str:
    print("  [C] Generating semantic search string …")
    prompt = _SEARCH_STRING_PROMPT.format(
        target_type=target_type or "content",
        matching_concept=matching_concept or "emotional themes",
        entity_name=entity["name"],
        description=entity["description"] or "",
        core_emotional_logic=entity["core_emotional_logic"] or "",
    )
    search_string = _call_llm(client, prompt).strip()
    print(f"       Search string: \"{search_string[:120]}…\"")
    return search_string


# ------------------------------------------------------------------
# Step D: Vector search (DB)
# ------------------------------------------------------------------
def step_d_vector_search(conn, search_string: str, target_type: str | None, exclude_id: str | None = None, top_k: int = SHORTLIST_K) -> list[dict]:
    print("  [D] Searching vector database …")
    # Map singular to table name
    type_map = {"movie": "movies", "character": "characters", "relationship": "relationships", "song": "songs"}
    filter_type = type_map.get(target_type or "", target_type)
    results = vector_search(conn, search_string, filter_type=filter_type, top_k=top_k, exclude_id=exclude_id)
    for r in results:
        print(f"       {r['similarity']:.3f}  [{r['type']}] {r['name']}")
    return results


# ------------------------------------------------------------------
# Confidence assessment
# ------------------------------------------------------------------
# Calibrated on the live data (nomic embeddings): found references score ~0.69-0.73,
# missing references ~0.60, open questions ~0.66, nonsense ~0.52-0.56.
LOW_SIMILARITY = 0.62


def assess_confidence(intent: dict, entity: dict | None, results: list[dict]) -> tuple[str, str]:
    """Return (level, reason) where level is "high", "medium" or "low"."""
    ref = intent.get("reference_entity")
    top = results[0]["similarity"] if results else 0.0
    if ref and not entity:
        return "low", f"\u201c{ref}\u201d isn\u2019t in the database, so these are only loose matches on your wording."
    if top < LOW_SIMILARITY:
        return "low", "Nothing in the database is a close match for this, so these are only the nearest entries."
    if entity and entity.get("source") == "live":
        return "medium", f"\u201c{entity['name']}\u201d isn\u2019t in our database, so its details were looked up live from {entity['sources']}."
    if ref:
        return "high", ""
    return "medium", ""


# ------------------------------------------------------------------
# Step E: Reasoning scorer + final answer (one LLM call)
# ------------------------------------------------------------------
_ANSWER_PROMPT = """\
You are a creative assistant for short-film and reel creators.

The user asked: "{query}"

A semantic search of our media knowledge database found these candidate entries:

{context_block}

Score EVERY candidate against the request using this rubric. Each score is a number from 0.0 to 1.0.
- "emotional_match": does the entry share the same emotional decision, tension or arc the user is after? (most important)
- "tone": does its mood, intensity and feel fit?
- "usability": could a creator realistically use it for what the user described?
Be strict: 0.8+ only for a clearly strong fit, and give low scores to entries that merely sound similar.
{write_rule}
Keep every field short — output length is limited.
Use ONLY the information above. Do NOT invent facts that are not above.
{caution}
Return ONLY valid JSON in exactly this shape:
{{
  "summary": "one sentence on what kind of entries fit the request; do NOT name or rank a specific entry",
  "scores": [
    {{
      "source": <candidate number from the list above>,
      "emotional_match": 0.0,
      "tone": 0.0,
      "usability": 0.0,
      "why": "at most 25 words on why it fits, citing its emotional logic",
      "idea": "at most 25 words: how a creator could use it in a short film or reel"
    }}
  ]
}}
"""

_LOW_CONFIDENCE_CAUTION = """
IMPORTANT: {reason}
You have NO information about anything the user mentions that is not listed above, so do not claim to know it.
These entries are only loosely related, matched on the wording of the question.
- The summary must start by saying plainly that these are loose matches and not a confident answer.
- Keep "why" and "idea" tentative ("might", "could"), and base them only on the entries above.
- Give low scores if nothing plausibly fits.
"""


def _clamp01(x) -> float | None:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return None


# Cosine only separates good from bad inside a narrow band (nonsense ~0.52-0.56, strong ~0.73),
# so it is rescaled on a FIXED range. Min-max inside the shortlist would stretch tiny, noisy gaps.
COS_FLOOR, COS_CEIL = 0.50, 0.80


def _normalise_cos(sims: list[float]) -> list[float]:
    return [max(0.0, min(1.0, (x - COS_FLOOR) / (COS_CEIL - COS_FLOOR))) for x in sims]


def score_candidates(
    client: Groq,
    query: str,
    results: list[dict],
    confidence: str = "high",
    reason: str = "",
    write_text: bool = True,
) -> tuple[str, dict[int, dict]]:
    """
    One LLM call: score every shortlisted candidate with the rubric.

    Returns (summary, {index into `results`: {"dims", "r_score", "why", "idea"}}).
    Candidates the LLM skipped or scored invalidly are simply absent from the dict.
    write_text=False asks for numbers only (cheaper; used by the evaluation harness).
    """
    # Present candidates in a seeded-shuffled order so the LLM is not biased by retrieval rank.
    order = list(range(len(results)))
    random.Random(query).shuffle(order)
    context_parts = []
    for shown, idx in enumerate(order, 1):
        r = results[idx]
        context_parts.append(
            f"[{shown}] [{r['type'].upper()}] {r['name']}\n"
            f"    Description: {r['description']}\n"
            f"    Core emotional logic: {r['core_emotional_logic']}"
        )
    caution = _LOW_CONFIDENCE_CAUTION.format(reason=reason) if confidence == "low" else ""
    write_rule = (
        f'Write "why" and "idea" ONLY for the {WRITE_TOP} candidates you score highest; use empty strings for all the others.'
        if write_text else
        'Leave "why" and "idea" as empty strings for every candidate.'
    )
    raw = _call_llm(client, _ANSWER_PROMPT.format(
        query=query, context_block="\n\n".join(context_parts), caution=caution, write_rule=write_rule))
    parsed = _extract_json(raw)

    scores: dict[int, dict] = {}
    for item in parsed.get("scores") or []:
        if not isinstance(item, dict):
            continue
        try:
            shown = int(item.get("source"))
        except (TypeError, ValueError):
            continue
        if not 1 <= shown <= len(order):
            continue
        idx = order[shown - 1]
        if idx in scores:
            continue
        dims = {k: _clamp01(item.get(k)) for k in R_WEIGHTS}
        if any(v is None for v in dims.values()):
            continue
        scores[idx] = {
            "dims": {k: round(v, 2) for k, v in dims.items()},
            "r_score": round(sum(R_WEIGHTS[k] * dims[k] for k in R_WEIGHTS), 3),
            "why": str(item.get("why") or "").strip(),
            "idea": str(item.get("idea") or "").strip(),
        }
    return str(parsed.get("summary") or "").strip(), scores


def rank_candidates(
    results: list[dict],
    scores: dict[int, dict],
    lam_cos: float = LAMBDA_COS,
    lam_r: float = LAMBDA_R,
    trends: dict[int, dict] | None = None,
    lam_t: float = LAMBDA_T,
) -> list[dict]:
    """
    Rank ALL candidates by  score = (lam_cos*cos + lam_r*R + lam_t*T) / (sum of the weights used).
    A candidate the LLM did not score gets R = 0; one without a trend simply skips the T term.
    Pass trends=None (as the evaluation harness does) to rank without any trend. Pure function.
    """
    cos_n = _normalise_cos([r["similarity"] for r in results])
    ranked = []
    for idx, r in enumerate(results):
        sc = scores.get(idx)
        r_score = sc["r_score"] if sc else 0.0
        tr = (trends or {}).get(idx)
        num = lam_cos * cos_n[idx] + lam_r * r_score
        den = lam_cos + lam_r
        if tr is not None:
            num += lam_t * tr["score"]
            den += lam_t
        ranked.append({
            "idx": idx,
            "type": r["type"],
            "name": r["name"],
            "similarity": r["similarity"],
            "r_score": r_score if sc else None,
            "score": round(num / den, 3) if den else 0.0,
            "trend": tr,
            "dims": sc["dims"] if sc else None,
            "why": sc["why"] if sc else "",
            "idea": sc["idea"] if sc else "",
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def step_e_generate_answer(
    client: Groq,
    query: str,
    results: list[dict],
    confidence: str = "high",
    reason: str = "",
    lam_cos: float = LAMBDA_COS,
    lam_r: float = LAMBDA_R,
) -> dict:
    """
    Reasoning scorer + final answer. Returns
    {"summary": str, "ideas": [{rank, type, name, similarity, r_score, score, dims, why, idea}]}.
    """
    print("  [E] Scoring candidates and writing the answer …\n")
    summary, scores = score_candidates(client, query, results, confidence, reason)

    if scores:
        trends = trend.get_trends(results)   # songs only; {} if Last.fm is unavailable
        ranked = rank_candidates(results, scores, lam_cos, lam_r, trends)
        ideas = [
            x for x in ranked
            if x["r_score"] is not None and x["r_score"] >= MIN_R and x["dims"]["emotional_match"] >= MIN_EMOTIONAL
        ][:MAX_IDEAS]
        for i, x in enumerate(ideas, 1):
            x["rank"] = i
            del x["idx"]
        # no fit at all is a legitimate answer when we are not confident
        if ideas or confidence == "low":
            return {"summary": summary, "ideas": ideas}

    # LLM gave no usable scores — fall back to the retrieval order, unscored.
    return {
        "summary": reason if confidence == "low" and reason else "Here are the closest matches found in the database.",
        "ideas": [
            {"rank": i, "type": r["type"], "name": r["name"], "similarity": r["similarity"],
             "r_score": None, "score": None, "dims": None, "trend": None,
             "why": r["core_emotional_logic"] or "", "idea": ""}
            for i, r in enumerate(results[:MAX_IDEAS], 1)
        ],
    }


# ------------------------------------------------------------------
# Retrieval (steps A-D) — reusable on its own, e.g. by the evaluation harness
# ------------------------------------------------------------------
def retrieve(
    conn,
    client: Groq,
    query: str,
    *,
    rewrite: bool = True,
    live: bool = True,
    top_k: int = SHORTLIST_K,
    intent: dict | None = None,
) -> dict:
    """
    Run steps A-D.

    rewrite=False embeds the raw query (the naive baseline v = f(q)).
    live=False skips the live lookup for references that are not in the database.
    intent lets a caller reuse an already-extracted intent (skips step A).
    """
    intent = intent or step_a_extract_intent(client, query)
    reference_entity = intent.get("reference_entity")
    target_type = intent.get("target_type")
    matching_concept = intent.get("matching_concept") or "emotional themes"

    entity = None
    if rewrite:
        entity = step_b_get_context(conn, reference_entity)
        if entity is None and reference_entity and live:
            entity = step_b2_live_lookup(intent)

    if entity:
        search_string = step_c_generate_search_string(client, entity, target_type, matching_concept)
    else:
        print("  [C] No reference entity — using query directly as search string.")
        search_string = query

    results = step_d_vector_search(
        conn, search_string, target_type,
        exclude_id=entity.get("id") if entity else None, top_k=top_k,
    )
    return {"intent": intent, "entity": entity, "search_string": search_string, "results": results}


# ------------------------------------------------------------------
# Main orchestrator
# ------------------------------------------------------------------
def run_rag_data(query: str, client: Groq | None = None) -> dict:
    """Run the full pipeline and return a structured result (used by the API)."""
    client = client or _get_client()
    conn = db.get_conn()
    try:
        r = retrieve(conn, client, query)
        intent, entity, results = r["intent"], r["entity"], r["results"]
        confidence, confidence_reason = assess_confidence(intent, entity, results)
        answer = (
            step_e_generate_answer(client, query, results, confidence, confidence_reason)
            if results else {"summary": "", "ideas": []}
        )

        return {
            "query": query,
            "intent": intent,
            "reference": entity,
            "reference_source": ("live" if entity.get("source") == "live" else "database") if entity else None,
            "search_string": r["search_string"],
            "results": results,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "summary": answer["summary"],
            "ideas": answer["ideas"],
        }
    finally:
        conn.close()


def run_rag(query: str) -> None:
    print(f"\n🔍  Agentic RAG Search")
    print(f"    Query: \"{query}\"\n")
    try:
        out = run_rag_data(query)
    except llm.LLMError as exc:
        print(f"❌  {exc.user_message}", file=sys.stderr)
        sys.exit(1)
    if not out["results"]:
        print("❌  No results found in the database.")
        return
    print("=" * 60)
    if out["confidence"] == "low":
        print(f"⚠️  LOW CONFIDENCE — {out['confidence_reason']}\n")
    print(out["summary"])
    for idea in out["ideas"]:
        fit = f"  (fit {idea['r_score']:.2f})" if idea.get("r_score") is not None else ""
        print(f"\n{idea['rank']}. [{idea['type']}] {idea['name']}{fit}")
        print(f"   Why:  {idea['why']}")
        if idea["idea"]:
            print(f"   Idea: {idea['idea']}")
    print("=" * 60)
    print("\n📚  Sources retrieved from database:")
    for r in out["results"]:
        print(f"   • [{r['type']}] {r['name']}  (similarity: {r['similarity']:.3f})")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="IdeAgent Agentic RAG Search",
        epilog="""Examples:
  python -m pipeline.rag "Find me a song that captures the emotional intensity of Interstellar"
  python -m pipeline.rag "What movies feel similar to Bohemian Rhapsody?"
  python -m pipeline.rag "Find characters with a moral conflict similar to The Joker"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Your natural language search query")
    args = parser.parse_args()
    run_rag(args.query)


if __name__ == "__main__":
    main()
