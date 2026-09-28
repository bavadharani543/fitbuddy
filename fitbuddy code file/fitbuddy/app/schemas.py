"""
Pydantic request/response schemas for FitBuddy.
"""
from pydantic import BaseModel, Field
from typing import Optional


class UserInput(BaseModel):
    """Data collected from the homepage form (index.html)."""
    user_id: str = Field(..., description="Unique identifier chosen by the user")
    name: str
    age: int
    weight: float
    goal: str          # e.g. "weight loss", "muscle gain", "flexibility", "general wellness"
    intensity: str      # "low" | "medium" | "high"


class FeedbackRequest(BaseModel):
    """Data collected from the feedback form (result.html)."""
    user_id: str
    feedback: str        # e.g. "more focus on cardio", "include more rest days"
