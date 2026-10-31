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

import os
import json
import time

from groq import Groq

from pipeline import config

# ------------------------------------------------------------------
# Groq client (lazy-initialised)
# ------------------------------------------------------------------
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = config.require(
            "GROQ_API_KEY",
            os.environ.get("GROQ_API_KEY"),
            hint="Free API key: https://console.groq.com/keys",
        )
        _client = Groq(api_key=api_key)
    return _client


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

    response = None
    target_model = config.LLM_MODEL
    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            break
        except Exception as e:
            err_str = str(e).lower()
            if "tokens per day" in err_str or "tpd" in err_str:
                if target_model != "openai/gpt-oss-20b" and target_model != "openai/gpt-oss-120b":
                    print(f"    ⚠️  Daily limit hit for {target_model}. Failing over to openai/gpt-oss-20b …")
                    target_model = "openai/gpt-oss-20b"
                    continue
                elif target_model == "openai/gpt-oss-20b":
                    print(f"    ⚠️  Daily limit hit for {target_model}. Failing over to openai/gpt-oss-120b …")
                    target_model = "openai/gpt-oss-120b"
                    continue
            if "rate_limit" in err_str or "429" in err_str:
                wait_time = 10 * (attempt + 1)
                print(f"    ⏳ Rate limit on {target_model}. Waiting {wait_time}s (attempt {attempt+1}/5) …")
                time.sleep(wait_time)
            else:
                raise

    if response is None:
        raise RuntimeError(f"Failed to get response from Groq after retries for {entity_type}")

    response_text = response.choices[0].message.content
    
    # Robustly extract JSON object from the response.
    # LLMs may output chain-of-thought, markdown code blocks, or trailing text.
    import re
    cleaned_dict = None

    # Strategy 1: markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response_text)
    if match:
        try:
            cand = json.loads(match.group(1), strict=False)
            if isinstance(cand, dict) and "description" in cand and "core_emotional_logic" in cand:
                cleaned_dict = cand
        except Exception:
            pass

    # Strategy 2: scan backwards from the last '}' to find matching '{'
    if cleaned_dict is None:
        last_close = response_text.rfind("}")
        if last_close != -1:
            depth = 0
            for i in range(last_close, -1, -1):
                if response_text[i] == "}":
                    depth += 1
                elif response_text[i] == "{":
                    depth -= 1
                    if depth == 0:
                        candidate_str = response_text[i : last_close + 1]
                        try:
                            cand = json.loads(candidate_str, strict=False)
                            if isinstance(cand, dict) and "description" in cand and "core_emotional_logic" in cand:
                                cleaned_dict = cand
                                break
                        except Exception:
                            pass

    # Strategy 3: search for widest substring between { and } that contains target keys
    if cleaned_dict is None:
        first_open = response_text.find("{")
        last_close = response_text.rfind("}")
        if first_open != -1 and last_close != -1 and last_close > first_open:
            candidate_str = response_text[first_open : last_close + 1]
            try:
                cand = json.loads(candidate_str, strict=False)
                if isinstance(cand, dict) and "description" in cand:
                    cleaned_dict = cand
            except Exception:
                # Try cleaning trailing commas
                try:
                    c_clean = re.sub(r",\s*([\}\]])", r"\1", candidate_str)
                    cand = json.loads(c_clean, strict=False)
                    if isinstance(cand, dict) and "description" in cand:
                        cleaned_dict = cand
                except Exception:
                    pass

    # Strategy 4: raw text fallback
    if cleaned_dict is None:
        try:
            cleaned_dict = json.loads(response_text.strip(), strict=False)
        except Exception as e:
            raise ValueError(
                f"LLM returned non-JSON response for {entity_type}:\n{response_text}"
            ) from e

    result = cleaned_dict
    if "description" not in result or "core_emotional_logic" not in result:
        raise ValueError(
            f"LLM response missing required fields for {entity_type}:\n{result}"
        )

    return {
        "description": result["description"].strip(),
        "core_emotional_logic": result["core_emotional_logic"].strip(),
    }
