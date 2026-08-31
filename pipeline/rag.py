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
import sys

from groq import Groq

from pipeline import config, db
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
    return resp.choices[0].message.content


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
def step_d_vector_search(conn, search_string: str, target_type: str | None) -> list[dict]:
    print("  [D] Searching vector database …")
    # Map singular to table name
    type_map = {"movie": "movies", "character": "characters", "relationship": "relationships", "song": "songs"}
    filter_type = type_map.get(target_type or "", target_type)
    results = vector_search(conn, search_string, filter_type=filter_type, top_k=5)
    for r in results:
        print(f"       {r['similarity']:.3f}  [{r['type']}] {r['name']}")
    return results


# ------------------------------------------------------------------
# Step E: Final answer (LLM)
# ------------------------------------------------------------------
_ANSWER_PROMPT = """\
You are a creative media recommendation assistant.

The user asked: "{query}"

Based on a semantic search of our media knowledge database, here are the most relevant entries found:

{context_block}

Using ONLY the information above, write a helpful, conversational recommendation that:
1. Directly answers the user's question.
2. Explains WHY each recommended item fits the request.
3. References the emotional logic and themes from the database entries.

Be specific and insightful. Do NOT invent information not present above.
"""

def step_e_generate_answer(client: Groq, query: str, results: list[dict]) -> str:
    print("  [E] Generating final answer …\n")
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[{i}] [{r['type'].upper()}] {r['name']}\n"
            f"    Description: {r['description']}\n"
            f"    Core emotional logic: {r['core_emotional_logic']}"
        )
    context_block = "\n\n".join(context_parts)
    return _call_llm(client, _ANSWER_PROMPT.format(query=query, context_block=context_block))


# ------------------------------------------------------------------
# Main orchestrator
# ------------------------------------------------------------------
def run_rag(query: str) -> None:
    print(f"\n🔍  Agentic RAG Search")
    print(f"    Query: \"{query}\"\n")

    client = _get_client()
    conn = db.get_conn()

    try:
        # A: Parse intent
        intent = step_a_extract_intent(client, query)
        reference_entity = intent.get("reference_entity")
        target_type      = intent.get("target_type")
        matching_concept = intent.get("matching_concept", "emotional themes")

        # B: Fetch reference entity from DB (if named)
        entity = step_b_get_context(conn, reference_entity)

        # C: Generate a dense search string
        if entity:
            search_string = step_c_generate_search_string(client, entity, target_type, matching_concept)
        else:
            # No specific entity found — fall back to embedding the raw query
            print("  [C] No reference entity — using query directly as search string.")
            search_string = query

        # D: Vector search
        results = step_d_vector_search(conn, search_string, target_type)

        if not results:
            print("❌  No results found in the database.")
            return

        # E: Generate final answer
        answer = step_e_generate_answer(client, query, results)

        # Print results
        print("=" * 60)
        print(answer)
        print("=" * 60)
        print("\n📚  Sources retrieved from database:")
        for r in results:
            print(f"   • [{r['type']}] {r['name']}  (similarity: {r['similarity']:.3f})")

    finally:
        conn.close()


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
