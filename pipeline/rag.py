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
import re
import sys

from groq import Groq

from pipeline import config, db
from pipeline.live_enrich import enrich_live
from pipeline.search_db import get_entity_by_name, vector_search


# ------------------------------------------------------------------
# Groq client (shared with llm_synthesize but kept local here for clarity)
# ------------------------------------------------------------------
def _get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌  GROQ_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return Groq(api_key=api_key)


def _call_llm(client: Groq, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return re.sub(r"<think>.*?</think>", "", resp.choices[0].message.content or "", flags=re.S).strip()


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
def step_d_vector_search(conn, search_string: str, target_type: str | None, exclude_id: str | None = None) -> list[dict]:
    print("  [D] Searching vector database …")
    # Map singular to table name
    type_map = {"movie": "movies", "character": "characters", "relationship": "relationships", "song": "songs"}
    filter_type = type_map.get(target_type or "", target_type)
    results = vector_search(conn, search_string, filter_type=filter_type, top_k=5, exclude_id=exclude_id)
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
# Step E: Final answer (LLM)
# ------------------------------------------------------------------
_ANSWER_PROMPT = """\
You are a creative assistant for short-film and reel creators.

The user asked: "{query}"

A semantic search of our media knowledge database found these entries:

{context_block}

Using ONLY the information above, pick the entries that genuinely fit the request and rank them best first.
Skip entries that do not fit. Do NOT invent facts that are not above.
{caution}
Return ONLY valid JSON in exactly this shape:
{{
  "summary": "1-2 sentences that directly answer the user's request",
  "ideas": [
    {{
      "source": <entry number from the list above>,
      "why": "1-2 sentences on why this entry fits, citing its emotional logic",
      "idea": "one concrete sentence: how a creator could use it in a short film or reel"
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
- If no entry plausibly fits, return an empty "ideas" list.
"""


def step_e_generate_answer(client: Groq, query: str, results: list[dict], confidence: str = "high", reason: str = "") -> dict:
    """Return {"summary": str, "ideas": [{rank, why, idea, type, name, similarity, ...}]}."""
    print("  [E] Generating final answer …\n")
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[{i}] [{r['type'].upper()}] {r['name']}\n"
            f"    Description: {r['description']}\n"
            f"    Core emotional logic: {r['core_emotional_logic']}"
        )
    context_block = "\n\n".join(context_parts)
    caution = _LOW_CONFIDENCE_CAUTION.format(reason=reason) if confidence == "low" else ""
    raw = _call_llm(client, _ANSWER_PROMPT.format(query=query, context_block=context_block, caution=caution))
    parsed = _extract_json(raw)

    ideas, seen = [], set()
    for item in parsed.get("ideas") or []:
        try:
            src = int(item.get("source"))
        except (TypeError, ValueError, AttributeError):
            continue
        if not 1 <= src <= len(results) or src in seen:
            continue
        seen.add(src)
        r = results[src - 1]
        ideas.append({
            "rank": len(ideas) + 1,
            "type": r["type"],
            "name": r["name"],
            "similarity": r["similarity"],
            "why": str(item.get("why") or "").strip(),
            "idea": str(item.get("idea") or "").strip(),
        })

    if ideas or (parsed and confidence == "low"):
        # a low-confidence answer may legitimately contain no ideas
        return {"summary": str(parsed.get("summary") or "").strip(), "ideas": ideas}

    # LLM did not return usable JSON — fall back to the retrieval order.
    return {
        "summary": reason if confidence == "low" and reason else (raw or "Here are the closest matches found in the database."),
        "ideas": [
            {"rank": i, "type": r["type"], "name": r["name"], "similarity": r["similarity"],
             "why": r["core_emotional_logic"] or "", "idea": ""}
            for i, r in enumerate(results, 1)
        ],
    }


# ------------------------------------------------------------------
# Main orchestrator
# ------------------------------------------------------------------
def run_rag_data(query: str, client: Groq | None = None) -> dict:
    """Run the 5-step pipeline and return a structured result (used by the API)."""
    client = client or _get_client()
    conn = db.get_conn()
    try:
        intent = step_a_extract_intent(client, query)
        reference_entity = intent.get("reference_entity")
        target_type      = intent.get("target_type")
        matching_concept = intent.get("matching_concept") or "emotional themes"

        entity = step_b_get_context(conn, reference_entity)
        if entity is None and reference_entity:
            entity = step_b2_live_lookup(intent)

        if entity:
            search_string = step_c_generate_search_string(client, entity, target_type, matching_concept)
        else:
            print("  [C] No reference entity — using query directly as search string.")
            search_string = query

        results = step_d_vector_search(conn, search_string, target_type, exclude_id=entity.get("id") if entity else None)
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
            "search_string": search_string,
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
    out = run_rag_data(query)
    if not out["results"]:
        print("❌  No results found in the database.")
        return
    print("=" * 60)
    if out["confidence"] == "low":
        print(f"⚠️  LOW CONFIDENCE — {out['confidence_reason']}\n")
    print(out["summary"])
    for idea in out["ideas"]:
        print(f"\n{idea['rank']}. [{idea['type']}] {idea['name']}")
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
