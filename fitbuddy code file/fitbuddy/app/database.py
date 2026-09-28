"""
SQLite persistence layer for FitBuddy, using SQLAlchemy ORM.

Tables
------
users : one row per registered user
plans : one row per user, holding the original AI-generated plan,
        the (optional) feedback-updated plan, and the nutrition tip.
"""
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

DATABASE_URL = "sqlite:///./fitbuddy.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------- models --
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    intensity = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan", back_populates="user", uselist=False)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, nullable=False)
    original_plan = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plan")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------- helpers --
def save_user(db: Session, user_input) -> User:
    """Create the user record if it doesn't exist yet, else return the existing one."""
    user = db.query(User).filter(User.user_id == user_input.user_id).first()
    if user is None:
        user = User(
            user_id=user_input.user_id,
            name=user_input.name,
            age=user_input.age,
            weight=user_input.weight,
            goal=user_input.goal,
            intensity=user_input.intensity,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def save_plan(db: Session, user_id: str, workout_plan: str, nutrition_tip: str) -> Plan:
    plan = db.query(Plan).filter(Plan.user_id == user_id).first()
    if plan is None:
        plan = Plan(user_id=user_id, original_plan=workout_plan, nutrition_tip=nutrition_tip)
        db.add(plan)
    else:
        plan.original_plan = workout_plan
        plan.nutrition_tip = nutrition_tip
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, user_id: str, updated_plan: str, feedback: str) -> Plan:
    plan = db.query(Plan).filter(Plan.user_id == user_id).first()
    if plan is None:
        raise ValueError(f"No plan found for user_id={user_id}")
    plan.updated_plan = updated_plan
    plan.feedback = feedback
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()


def get_original_plan(db: Session, user_id: str) -> Plan | None:
    return db.query(Plan).filter(Plan.user_id == user_id).first()


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()
