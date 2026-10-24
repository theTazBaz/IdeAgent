"""
pipeline/llm_synthesize.py
==========================
Calls Groq LLM to synthesize enriched descriptions from raw scraped facts.

The LLM is the synthesis and reasoning layer — never the source of truth.
Every prompt explicitly instructs the model to use ONLY the provided facts
and not draw on its own internal knowledge.

Output is always JSON: {"description": "...", "core_emotional_logic": "..."}
"""
from __future__ import annotations

import json

from groq import Groq

from pipeline import config, llm

# ------------------------------------------------------------------
# Groq client (shared, with retries — see pipeline/llm.py)
# ------------------------------------------------------------------
def _get_client() -> Groq:
    return llm.get_client()


# ------------------------------------------------------------------
# Prompts (one per entity type)
# ------------------------------------------------------------------
_PROMPTS: dict[str, str] = {
    "movie": """\
You are a creative analyst building a content recommendation system for short-film creators.
Given the following factual data about a movie, synthesize it into a structured description.

FACTS:
{facts_json}

Return ONLY valid JSON with exactly these two fields:
{{
  "description": "A 3-5 sentence enriched description covering theme, tone, narrative style, and emotional core. Use ONLY the provided facts.",
  "core_emotional_logic": "One sentence capturing the central emotional decision or tension that defines this film."
}}

⚠️  Do NOT use knowledge from your own memory. Base your answer solely on the FACTS above.""",

    "character": """\
You are a creative analyst building a content recommendation system for short-film creators.
Given the following factual data about a character, synthesize it into a structured description.

FACTS:
{facts_json}

Return ONLY valid JSON with exactly these two fields:
{{
  "description": "A 3-5 sentence description of this character's individual traits, psychology, and role. Do NOT include relational logic about their relationships with other characters — those belong on a separate Relationship record.",
  "core_emotional_logic": "One sentence capturing the central emotional decision or defining internal tension within this character, in isolation."
}}

⚠️  Do NOT use knowledge from your own memory. Base your answer solely on the FACTS above.""",

    "relationship": """\
You are a creative analyst building a content recommendation system for short-film creators.
Given factual data about a relationship between two characters, synthesize it.

FACTS:
{facts_json}

Return ONLY valid JSON with exactly these two fields:
{{
  "description": "A 3-5 sentence description of the dynamic, tension, and narrative logic between these two characters. Describe what drives their interaction and what is at stake.",
  "core_emotional_logic": "One sentence capturing the central emotional opposition or co-dependence that defines this relationship."
}}

⚠️  Do NOT use knowledge from your own memory. Base your answer solely on the FACTS above.""",

    "song": """\
You are a creative analyst building a content recommendation system for short-film creators.
Given factual data about a song, synthesize it into a structured description.

FACTS:
{facts_json}

Return ONLY valid JSON with exactly these two fields:
{{
  "description": "A 3-5 sentence description of the song's emotional character, lyrical themes, sonic quality, and mood. Ground the description in the facts provided.",
  "core_emotional_logic": "One sentence capturing the central emotional experience or decision the song expresses."
}}

⚠️  Do NOT use knowledge from your own memory. Base your answer solely on the FACTS above.""",
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def synthesize(entity_type: str, raw_facts: dict) -> dict:
    """
    Call Groq to synthesize a description from raw scraped facts.

    Args:
        entity_type: One of "movie", "character", "relationship", "song"
        raw_facts:   Dict of scraped data (TMDB, Spotify, Wikipedia, Fandom, etc.)

    Returns:
        {"description": str, "core_emotional_logic": str}

    Raises:
        KeyError:          if entity_type is not one of the four valid types
        EnvironmentError:  if GROQ_API_KEY is not set
        ValueError:        if the LLM response cannot be parsed as valid JSON
    """
    if entity_type not in _PROMPTS:
        raise KeyError(f"Unknown entity_type: {entity_type!r}. Must be one of {list(_PROMPTS)}")

    client = _get_client()
    prompt = _PROMPTS[entity_type].format(facts_json=json.dumps(raw_facts, indent=2))

    response_text = llm.chat(prompt, temperature=0.2, client=client)

    # Robustly extract the LAST complete JSON object from the response.
    # Qwen emits a long chain-of-thought before the final JSON block, so we
    # scan backwards from the last '}' to find its matching '{'.
    cleaned_text = None
    last_close = response_text.rfind("}")
    if last_close != -1:
        depth = 0
        for i in range(last_close, -1, -1):
            if response_text[i] == "}":
                depth += 1
            elif response_text[i] == "{":
                depth -= 1
                if depth == 0:
                    cleaned_text = response_text[i : last_close + 1]
                    break

    if not cleaned_text:
        cleaned_text = response_text.strip()

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned non-JSON response for {entity_type}:\n{response_text}"
        ) from e

    if "description" not in result or "core_emotional_logic" not in result:
        raise ValueError(
            f"LLM response missing required fields for {entity_type}:\n{result}"
        )

    return {
        "description": result["description"].strip(),
        "core_emotional_logic": result["core_emotional_logic"].strip(),
    }
