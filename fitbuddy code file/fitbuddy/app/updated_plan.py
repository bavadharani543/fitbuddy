"""
Revises an existing workout plan based on free-text user feedback,
using Gemini 3.8 Flash (same model used for the initial generation, for
consistent structure and quality).

Uses the current `google-genai` SDK (the old `google-generativeai`
package reached end-of-life on 2025-11-30 and should not be used for
new projects).
"""
import os
from google import genai

_MODEL_NAME = "gemini-3.5-flash-lite"


def _get_client():
    """Lazily create the client so a missing key doesn't crash app startup."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    return genai.Client(api_key=api_key)


def update_workout_plan(original_plan: str, feedback: str) -> str:
    """Calls Gemini 3.8 Flash with the original plan + feedback and returns a revised plan."""
    prompt = f"""You are a certified fitness coach. Here is a user's current 7-day workout plan:

---
{original_plan}
---

The user has given this feedback: "{feedback}"

Revise the 7-day plan to incorporate the feedback while keeping the overall
structure (Day 1 - Day 7, warm-up / main workout / cooldown per day). Only
change what the feedback implies should change; keep everything else consistent
with the original plan. Return the full updated 7-day plan as plain text."""
    try:
        client = _get_client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as exc:  # pragma: no cover - network/key errors
        return (
            "⚠ Could not reach Gemini 3.8 Flash (check GOOGLE_API_KEY).\n"
            f"Details: {exc}"
        )
