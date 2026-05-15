"""
EduFlow — Google OAuth Router
GET  /auth/login    — redirects to Google OAuth
GET  /auth/callback — exchanges code for token, creates/updates teacher record
GET  /auth/me       — returns current teacher profile
GET  /auth/demo     — auto-login as demo teacher (DEMO_MODE only)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Teacher, School, get_db
from config import settings
import httpx

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/login")
async def login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Google OAuth not configured. Use /auth/demo in DEMO_MODE.")
    params = (
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.OAUTH_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(GOOGLE_AUTH_URL + params)


@router.get("/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(400, "OAuth token exchange failed")

        user_resp = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_resp.json()

    teacher = await _get_or_create_teacher(db, user_info)
    return RedirectResponse(f"{settings.FRONTEND_URL}?teacher_id={teacher.id}&name={teacher.name}")


@router.get("/demo")
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Auto-login for demo — returns the seeded demo teacher. DEMO_MODE only."""
    if not settings.DEMO_MODE:
        raise HTTPException(403, "Demo login is only available in DEMO_MODE.")
    result = await db.execute(
        select(Teacher).where(Teacher.email == settings.DEMO_TEACHER_EMAIL)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(404, "Demo teacher not found — run seed.py first.")
    return {
        "teacher_id": str(teacher.id),
        "name": teacher.name,
        "email": teacher.email,
        "school_id": str(teacher.school_id),
    }


@router.get("/me")
async def me(teacher_id: str, db: AsyncSession = Depends(get_db)):
    teacher = await db.get(Teacher, uuid.UUID(teacher_id))
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    return {"id": str(teacher.id), "name": teacher.name, "email": teacher.email}


async def _get_or_create_teacher(db: AsyncSession, user_info: dict) -> Teacher:
    email = user_info.get("email", "")
    result = await db.execute(select(Teacher).where(Teacher.email == email))
    teacher = result.scalar_one_or_none()
    if teacher:
        teacher.google_id = user_info.get("sub")
        await db.commit()
        return teacher
    # Auto-assign to first school in DB
    school_result = await db.execute(select(School).limit(1))
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(500, "No schools seeded. Run seed.py first.")
    new_teacher = Teacher(
        name=user_info.get("name", email),
        email=email,
        google_id=user_info.get("sub"),
        school_id=school.id,
    )
    db.add(new_teacher)
    await db.commit()
    await db.refresh(new_teacher)
    return new_teacher
