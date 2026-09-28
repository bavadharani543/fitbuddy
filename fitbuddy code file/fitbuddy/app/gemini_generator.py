"""
FitBuddy - AI Workout Plan Generator

Uses Google's Gemini 3.8 Flash model with the current google-genai SDK.
"""

import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

_MODEL_NAME = "gemini-3.5-flash-lite"


def _get_client():
    """Create the Gemini client using GOOGLE_API_KEY."""
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    return genai.Client(api_key=api_key)


def _build_prompt(
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> str:

    return f"""
You are a certified fitness coach.

Create a practical and safe 7-day workout plan for this user.

User profile:
- Name: {name}
- Age: {age}
- Weight: {weight} kg
- Fitness goal: {goal}
- Workout intensity: {intensity}

For each day from Day 1 to Day 7 include:

1. Daily focus
2. Warm-up for 5-10 minutes
3. 4-6 main exercises
4. Sets and repetitions
5. Rest time between sets
6. Short cooldown/recovery advice

Include an appropriate rest or active recovery day.

Make the plan practical for a normal person and avoid extreme training.

Format clearly using:

Day 1
Focus:
Warm-up:
Exercises:
Cooldown:

Day 2
Focus:
Warm-up:
Exercises:
Cooldown:

Continue through Day 7.

Return only the workout plan.
"""


def generate_workout_gemini(
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> str:

    prompt = _build_prompt(
        name=name,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )

    max_retries = 4

    for attempt in range(1, max_retries + 1):

        try:
            print(
                f"Workout Gemini request "
                f"attempt {attempt}/{max_retries}..."
            )

            client = _get_client()

            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
            )

            if response and response.text:
                print("Workout Gemini generation successful.")
                return response.text.strip()

            raise RuntimeError("Gemini returned an empty response.")

        except Exception as exc:

            error_text = str(exc)

            print(
                f"Workout Gemini attempt "
                f"{attempt}/{max_retries} failed: {error_text}"
            )

            # Temporary Gemini capacity/service error
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < max_retries:

                    # Increasing delay between attempts
                    wait_seconds = attempt * 3

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)
                    continue

            # Other errors should not be retried repeatedly.
            return (
                "⚠ Could not generate the workout plan right now.\n"
                "Please try again in a moment.\n\n"
                f"Details: {error_text}"
            )

    return (
        "⚠ Gemini is temporarily unavailable.\n"
        "Please try generating your workout plan again."
    )
