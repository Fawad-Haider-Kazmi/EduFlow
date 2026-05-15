"""
EduFlow Pakistan — SQLAlchemy models + async DB engine.
All tables are created on startup via create_all().
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, String as SAString
import json, uuid as _uuid

# Cross-dialect UUID: TEXT on SQLite, native UUID on PostgreSQL
class UUID(TypeDecorator):
    impl = SAString(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None: return None
        return str(value)
    def process_result_value(self, value, dialect):
        if value is None: return None
        return _uuid.UUID(str(value))
    @property
    def python_type(self): return _uuid.UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ═════════════════════════════════════════════════════════════════════════════
#  MODELS
# ═════════════════════════════════════════════════════════════════════════════

class School(Base):
    __tablename__ = "schools"

    id             = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name           = Column(String(255), nullable=False)
    district       = Column(String(100))
    province       = Column(String(100))
    admin_email    = Column(String(255))
    registered_at  = Column(DateTime, default=datetime.utcnow)
    is_active      = Column(Boolean, default=True)
    last_submission_date = Column(DateTime, nullable=True)

    teachers   = relationship("Teacher", back_populates="school")
    students   = relationship("Student", back_populates="school")
    alerts     = relationship("GhostSchoolAlert", back_populates="school")


class Teacher(Base):
    __tablename__ = "teachers"

    id         = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name       = Column(String(255), nullable=False)
    email      = Column(String(255), unique=True, nullable=False)
    google_id  = Column(String(255), nullable=True)
    school_id  = Column(UUID(), ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    school      = relationship("School", back_populates="teachers")
    students    = relationship("Student", back_populates="teacher")
    assignments = relationship("Assignment", back_populates="teacher")


class Student(Base):
    __tablename__ = "students"

    id                 = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name               = Column(String(255), nullable=False)
    school_id          = Column(UUID(), ForeignKey("schools.id"), nullable=False)
    teacher_id         = Column(UUID(), ForeignKey("teachers.id"), nullable=False)
    grade_level        = Column(String(50))   # primary / secondary / higher
    age                = Column(Integer)
    preferred_language = Column(String(50), default="english")
    parent_phone       = Column(String(50), nullable=True)
    dropout_risk       = Column(Boolean, default=False)
    taleem_gap_active  = Column(Boolean, default=False)
    created_at         = Column(DateTime, default=datetime.utcnow)

    school      = relationship("School", back_populates="students")
    teacher     = relationship("Teacher", back_populates="students")
    submissions = relationship("Submission", back_populates="student")
    taleem_gap_plans = relationship("TaleemGapPlan", back_populates="student")


class Assignment(Base):
    __tablename__ = "assignments"

    id          = Column(UUID(), primary_key=True, default=uuid.uuid4)
    title       = Column(String(255), nullable=False)
    teacher_id  = Column(UUID(), ForeignKey("teachers.id"), nullable=False)
    rubric_text = Column(Text)
    due_date    = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    teacher     = relationship("Teacher", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    """
    Central record — tracks every student submission through the 9-step pipeline.
    pipeline_step mirrors the PROCESSING ORDER (1-9).
    status: queued → processing → pending_review → approved → completed | flagged | error
    """
    __tablename__ = "submissions"

    id            = Column(UUID(), primary_key=True, default=uuid.uuid4)
    student_id    = Column(UUID(), ForeignKey("students.id"), nullable=False)
    assignment_id = Column(UUID(), ForeignKey("assignments.id"), nullable=False)
    submitted_at  = Column(DateTime, default=datetime.utcnow)
    raw_text      = Column(Text, nullable=False)
    status        = Column(String(50), default="queued")
    pipeline_step = Column(Integer, default=0)

    # ── Step 1 — Zubaan (input) ───────────────────────────────────────────────
    original_language    = Column(String(50), nullable=True)
    was_translated       = Column(Boolean, default=False)
    translated_text      = Column(Text, nullable=True)
    language_barrier_risk = Column(Boolean, default=False)
    rubric_translated    = Column(Text, nullable=True)

    # ── Step 2 — Ingestion ────────────────────────────────────────────────────
    submission_type = Column(String(50), nullable=True)   # essay/code/math/short-answer
    cleaned_content = Column(Text, nullable=True)
    rubric_criteria = Column(JSON, nullable=True)         # list of criterion objects
    word_count      = Column(Integer, nullable=True)

    # ── Step 3 — Integrity ────────────────────────────────────────────────────
    plagiarism_score    = Column(Float, nullable=True)
    plagiarism_evidence = Column(Text, nullable=True)
    ai_generated_score  = Column(Float, nullable=True)
    ai_evidence         = Column(Text, nullable=True)
    integrity_flag      = Column(Boolean, default=False)

    # ── Step 4 — Grading ──────────────────────────────────────────────────────
    criteria_scores      = Column(JSON, nullable=True)
    total_score          = Column(Float, nullable=True)
    total_max            = Column(Float, nullable=True)
    percentage           = Column(Float, nullable=True)
    needs_intervention   = Column(Boolean, default=False)
    language_barrier_note = Column(Text, nullable=True)

    # ── Step 5 — HITL ─────────────────────────────────────────────────────────
    teacher_approved       = Column(Boolean, nullable=True)
    teacher_override_score = Column(Float, nullable=True)
    reviewed_at            = Column(DateTime, nullable=True)

    # ── Step 6 — Feedback ─────────────────────────────────────────────────────
    feedback_english    = Column(Text, nullable=True)
    feedback_translated = Column(Text, nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────────
    error_message = Column(Text, nullable=True)

    student    = relationship("Student", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
    agent_logs = relationship("AgentLog", back_populates="submission", order_by="AgentLog.called_at")
    review     = relationship("ReviewCheckpoint", back_populates="submission", uselist=False)


class AgentLog(Base):
    """One row per agent call — every call is logged, including retries and failures."""
    __tablename__ = "agent_logs"

    id            = Column(UUID(), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(), ForeignKey("submissions.id"), nullable=False)
    agent_name    = Column(String(100), nullable=False)
    called_at     = Column(DateTime, default=datetime.utcnow)
    completed_at  = Column(DateTime, nullable=True)
    duration_ms   = Column(Integer, nullable=True)
    input_data    = Column(JSON, nullable=True)
    output_data   = Column(JSON, nullable=True)
    status        = Column(String(50), default="running")  # running/success/failed/retried
    error_message = Column(Text, nullable=True)
    attempt       = Column(Integer, default=1)

    submission = relationship("Submission", back_populates="agent_logs")


class ReviewCheckpoint(Base):
    """HITL state machine — one per submission."""
    __tablename__ = "review_checkpoints"

    id            = Column(UUID(), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(), ForeignKey("submissions.id"), unique=True, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    deadline      = Column(DateTime, nullable=False)     # created_at + 24h
    status        = Column(String(50), default="pending")  # pending/approved/overridden/flagged
    override_score = Column(Float, nullable=True)
    reviewed_at   = Column(DateTime, nullable=True)
    reminder_sent = Column(Boolean, default=False)

    submission = relationship("Submission", back_populates="review")


class GhostSchoolAlert(Base):
    __tablename__ = "ghost_school_alerts"

    id                  = Column(UUID(), primary_key=True, default=uuid.uuid4)
    school_id           = Column(UUID(), ForeignKey("schools.id"), nullable=False)
    flag_type           = Column(String(50))  # ghost_school / mass_copying / school_disruption
    weeks_silent        = Column(Integer, default=0)
    last_submission_date = Column(DateTime, nullable=True)
    escalation_step     = Column(Integer, default=1)
    admin_notified      = Column(Boolean, default=False)
    admin_notified_at   = Column(DateTime, nullable=True)
    admin_response      = Column(Text, nullable=True)
    deo_escalated       = Column(Boolean, default=False)
    deo_escalated_at    = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    resolved            = Column(Boolean, default=False)

    school = relationship("School", back_populates="alerts")


class TaleemGapPlan(Base):
    __tablename__ = "taleem_gap_plans"

    id              = Column(UUID(), primary_key=True, default=uuid.uuid4)
    student_id      = Column(UUID(), ForeignKey("students.id"), nullable=False)
    root_cause      = Column(String(50))   # concept_gap/language_barrier/absenteeism/mixed
    plan_data       = Column(JSON)          # {day: N, tasks: [...]} × 14
    started_at      = Column(DateTime, default=datetime.utcnow)
    current_day     = Column(Integer, default=1)
    completed_tasks = Column(Integer, default=0)
    total_tasks     = Column(Integer, default=42)  # 3 tasks × 14 days
    status          = Column(String(50), default="active")  # active/completed/cancelled
    teacher_cancelled = Column(Boolean, default=False)

    student = relationship("Student", back_populates="taleem_gap_plans")


# ── Init helper ───────────────────────────────────────────────────────────────
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
