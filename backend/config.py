from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    # Defaults to SQLite for local dev. Switch to postgresql+asyncpg://... for production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduflow.db"

    # ── Gemini LLM ────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = "your-gemini-api-key"
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # ── Google Cloud ──────────────────────────────────────────────────────────
    GOOGLE_CLOUD_PROJECT: str = "eduflow-pakistan"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GCS_BUCKET: str = "eduflow-submissions"

    # ── Telegram Bot (replaces Twilio) ───────────────────────────────────────
    # Get token from @BotFather on Telegram — free, no approval needed
    TELEGRAM_BOT_TOKEN: str = ""

    # ── Google OAuth ──────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    # ── App ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # ── Demo Mode ─────────────────────────────────────────────────────────────
    # When True: agents return rich mock data instantly (no LLM latency in demo)
    DEMO_MODE: bool = True
    DEMO_TEACHER_EMAIL: str = "ayesha.raza@lahoremodel.edu.pk"
    DEMO_AUTO_LOGIN: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
