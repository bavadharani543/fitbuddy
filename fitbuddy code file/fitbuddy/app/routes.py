import re

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import (
    get_db,
    save_user,
    save_plan,
    update_plan,
    get_user,
    get_original_plan,
    get_all_users,
)

from app.schemas import UserInput
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan


router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ============================================================
# CONVERT GEMINI WORKOUT TEXT INTO SEPARATE DAY CARDS
# ============================================================

def parse_workout_days(workout_text: str):
    """
    Convert Gemini's workout text into separate Day 1-Day 7 cards.
    Handles common Gemini formats such as:
    
    Day 1: ...
    Day 1 - ...
    Day 1
    DAY 1
    **Day 1**
    Day 1: Focus: ...
    """

    if not workout_text:
        return []

    # Normalize line endings
    text = workout_text.replace("\r\n", "\n").replace("\r", "\n")

    # Find every Day 1 ... Day 7 heading.
    # Allows Markdown ** around the heading.
    day_pattern = re.compile(
        r"(?im)^[ \t]*(?:\*\*)?[ \t]*Day[ \t]*([1-7])"
        r"(?:[ \t]*\*\*)?"
        r"[ \t]*(?::|-)?[ \t]*(.*)$"
    )

    matches = list(day_pattern.finditer(text))

    days = []

    for index, match in enumerate(matches):

        day_number = int(match.group(1))

        # Text after "Day X"
        heading_text = match.group(2).strip()

        # Remove Markdown formatting
        heading_text = re.sub(r"\*\*", "", heading_text).strip()
        heading_text = re.sub(r"^[:\-]\s*", "", heading_text).strip()

        # Determine where this day's content ends
        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        content = text[start:end].strip()

        # If the heading contains "Focus:", extract it nicely
        focus_match = re.match(
            r"(?i)^focus\s*:\s*(.*)",
            heading_text
        )

        if focus_match:
            focus = focus_match.group(1).strip()
        elif heading_text:
            focus = heading_text
        else:
            # Try to find Focus inside the first part of the content
            content_focus_match = re.search(
                r"(?i)focus\s*:\s*([^\n]+)",
                content
            )

            if content_focus_match:
                focus = content_focus_match.group(1).strip()

                # Remove focus line from displayed content
                content = re.sub(
                    r"(?i)focus\s*:\s*[^\n]+\n?",
                    "",
                    content,
                    count=1
                ).strip()
            else:
                focus = "Workout"

        # Remove Markdown bold markers
        content = re.sub(r"\*\*", "", content)

        # Clean excessive spaces while preserving line breaks
        content = re.sub(r"[ \t]+", " ", content)

        # Put common sections on separate lines
        content = re.sub(
            r"(?i)\s*(Warm[- ]?up\s*:)",
            r"\n\n\1 ",
            content
        )

        content = re.sub(
            r"(?i)\s*(Exercises?\s*:)",
            r"\n\n\1 ",
            content
        )

        content = re.sub(
            r"(?i)\s*(Rest(?:ing)? time(?: between sets)?\s*:)",
            r"\n\n\1 ",
            content
        )

        content = re.sub(
            r"(?i)\s*(Cooldown\s*:)",
            r"\n\n\1 ",
            content
        )

        # Put numbered exercises on separate lines
        content = re.sub(
            r"\s+(\d+)\.\s+",
            r"\n\1. ",
            content
        )

        # Clean excessive blank lines
        content = re.sub(
            r"\n{3,}",
            "\n\n",
            content
        ).strip()

        days.append(
            {
                "day": day_number,
                "focus": focus,
                "content": content,
                "is_rest": "rest" in focus.lower(),
            }
        )

    # Safety fallback
    if not days:
        days.append(
            {
                "day": 1,
                "focus": "Workout Plan",
                "content": text.strip(),
                "is_rest": False,
            }
        )

    return days


# ============================================================
# HOME PAGE
# ============================================================

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )


# ============================================================
# GENERATE WORKOUT
# ============================================================

@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    user_id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):

    # Create validated user input
    user_input = UserInput(
        user_id=user_id,
        name=name,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )

    # Generate workout using Gemini
    workout_plan = generate_workout_gemini(
        name=user_input.name,
        age=user_input.age,
        weight=user_input.weight,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )

    # Generate nutrition tip
    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=user_input.goal
    )

    # Save user
    save_user(
        db,
        user_input
    )

    # Save generated plan
    save_plan(
        db,
        user_id=user_input.user_id,
        workout_plan=workout_plan,
        nutrition_tip=nutrition_tip,
    )

    # Convert workout into separate day cards
    workout_days = parse_workout_days(workout_plan)

    # Display result page
    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "user": user_input,
            "workout_plan": workout_plan,
            "workout_days": workout_days,
            "nutrition_tip": nutrition_tip,
            "updated_plan": None,
            "updated_workout_days": [],
            "feedback_submitted": False,
        },
    )


# ============================================================
# SUBMIT FEEDBACK / UPDATE WORKOUT
# ============================================================

@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):

    # Find user
    user = get_user(
        db,
        user_id
    )

    # Find original plan
    plan = get_original_plan(
        db,
        user_id
    )

    if user is None or plan is None:
        raise HTTPException(
            status_code=404,
            detail=f"No user/plan found for user_id={user_id}"
        )

    # Use latest plan if there is already an updated plan
    base_plan = plan.updated_plan or plan.original_plan

    # Generate revised workout
    revised_plan = update_workout_plan(
        original_plan=base_plan,
        feedback=feedback,
    )

    # Generate nutrition tip again
    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=user.goal
    )

    # Save revised plan
    update_plan(
        db,
        user_id=user_id,
        updated_plan=revised_plan,
        feedback=feedback,
    )

    # Convert both plans into separate cards
    workout_days = parse_workout_days(
        plan.original_plan
    )

    updated_workout_days = parse_workout_days(
        revised_plan
    )

    # Display updated result page
    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "user": user,
            "workout_plan": plan.original_plan,
            "workout_days": workout_days,
            "updated_plan": revised_plan,
            "updated_workout_days": updated_workout_days,
            "nutrition_tip": nutrition_tip,
            "feedback_submitted": True,
        },
    )


# ============================================================
# VIEW ALL USERS
# ============================================================

@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):

    users = get_all_users(db)

    return templates.TemplateResponse(
        request,
        "all_users.html",
        {
            "users": users
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "FitBuddy - AI Fitness Plan Generator"
    }