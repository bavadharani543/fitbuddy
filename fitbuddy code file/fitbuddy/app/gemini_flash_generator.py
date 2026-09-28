"""
FitBuddy - AI Nutrition Tip Generator
"""

import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"


def _get_client():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    return genai.Client(api_key=api_key)


def _fallback_nutrition(goal):
    return f"""
Starter Nutrition Guide for {goal}

• Prioritize protein: Include eggs, chicken, fish, milk, curd,
  paneer, tofu, lentils, beans, or other protein-rich foods.

• Eat enough carbohydrates: Rice, oats, potatoes, fruits,
  whole-grain foods, and other carbohydrate sources can help
  provide energy for training.

• Include healthy fats: Nuts, seeds, avocado, and suitable
  cooking oils can provide additional energy and nutrients.

• Stay hydrated: Drink water regularly throughout the day,
  especially before and after exercise.

• Eat balanced meals: Try to include protein, carbohydrates,
  vegetables or fruits, and healthy fats across your meals.

This is a general nutrition guide and not a substitute for
individual medical or dietary advice.
"""


def generate_nutrition_tip_with_flash(goal):

    prompt = f"""
You are a professional fitness nutrition assistant.

The user's fitness goal is:
{goal}

Give a simple practical nutrition guide.

Include:
- Protein sources
- Carbohydrate sources
- Healthy fats
- Hydration
- General meal guidance

Use clear bullet points.
Avoid extreme dieting advice.
"""


    for attempt in range(1, 3):

        try:
            print(
                f"Nutrition Gemini request "
                f"attempt {attempt}/2..."
            )

            client = _get_client()

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            if response and response.text:
                print("Nutrition Gemini generation successful.")
                return response.text.strip()

        except Exception as exc:

            error_text = str(exc)

            print(
                f"Nutrition Gemini attempt "
                f"{attempt}/2 failed: {error_text}"
            )

            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < 2:
                    time.sleep(3)
                    continue

            break

    print("Using built-in nutrition fallback.")

    return _fallback_nutrition(goal)