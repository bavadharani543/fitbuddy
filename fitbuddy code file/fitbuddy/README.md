# FitBuddy — AI Fitness Plan Generator

FitBuddy generates a personalized 7‑day workout plan and a nutrition/recovery
tip from a user's age, weight, fitness goal, and preferred intensity — using
Google's **Gemini 1.5 Pro** (workout plan + feedback-based revisions) and
**Gemini Flash** (fast nutrition tips). Built with **FastAPI**, **Jinja2**,
and **SQLite** (via SQLAlchemy).

## Features

- **Home page** (`/`) — form to enter name, user ID, age, weight, goal, intensity
- **Plan generation** (`POST /generate-workout`) — calls Gemini 1.5 Pro for the
  workout plan and Gemini Flash for a nutrition tip, saves both, and displays
  the result
- **Feedback loop** (`POST /submit-feedback`) — resubmits the plan + your
  feedback to Gemini 1.5 Pro to produce a revised plan, keeping the original
  on record
- **Admin dashboard** (`/view-all-users`) — table of every user with their
  original and updated plans, for coaches/admins
- Interactive API docs at `/docs` (FastAPI's built-in Swagger UI)

## Project structure

```
fitbuddy/
├── app/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── routes.py                  # All route handlers
│   ├── schemas.py                 # Pydantic models (UserInput, FeedbackRequest)
│   ├── database.py                # SQLAlchemy models + persistence helpers
│   ├── gemini_generator.py        # generate_workout_gemini() — Gemini 1.5 Pro
│   ├── gemini_flash_generator.py  # generate_nutrition_tip_with_flash() — Gemini Flash
│   └── updated_plan.py            # update_workout_plan() — feedback revisions
├── templates/
│   ├── index.html                 # input form
│   ├── result.html                # plan + tip + feedback form
│   └── all_users.html             # admin dashboard
├── static/css/style.css
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv fitbuddy-env
   source fitbuddy-env/bin/activate      # Windows: fitbuddy-env\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your Gemini API key**

   Copy `.env.example` to `.env` and fill in your key (get one at
   [ai.google.dev](https://ai.google.dev/)):

   ```bash
   cp .env.example .env
   # edit .env:
   # GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Run the server**

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open the app**

   - App: <http://127.0.0.1:8000>
   - API docs: <http://127.0.0.1:8000/docs>

The SQLite database file (`fitbuddy.db`) is created automatically on first
run in the project root.

## Notes

- If `GOOGLE_API_KEY` is missing or invalid, the Gemini calls fail gracefully
  and return an on-screen warning instead of crashing the app, so you can
  still exercise the rest of the flow (forms, storage, admin view) without a
  key.
- Swap `gemini-1.5-pro` / `gemini-1.5-flash` for other available Gemini model
  names (e.g. newer `gemini-2.x` models) in `app/gemini_generator.py`,
  `app/gemini_flash_generator.py`, and `app/updated_plan.py` if your account
  uses different model IDs.
- This project uses the current **`google-genai`** SDK (`from google import
  genai`, `genai.Client(...)`). The original `google-generativeai` package
  reached end-of-life on 2025-11-30 and is no longer supported — don't
  install it for new work.
