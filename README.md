# EduFlow Pakistan — AI Multi-Agent Education Platform

> Addressing Pakistan's education crisis through AI-powered grading, feedback, and school monitoring.

---

## Quick Start (Local Demo)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running on localhost:5432

### 2. Backend

```bash
cd backend

# Create virtualenv
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure env
copy ..\env.example .env
# Edit .env — set GEMINI_API_KEY at minimum
# DEMO_MODE=True means no real API calls are needed for the demo

# Seed demo data
python seed.py

# Start server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: http://localhost:3000

### 4. Demo Login

The dashboard auto-logs in as **Ms. Ayesha Raza** via `GET /auth/demo`.  
No Google OAuth credentials needed in DEMO_MODE.

---

## Architecture

```
Student Submission
      │
      ▼
[Step 1] Zubaan Agent          — Language detection + translation
      │
      ▼
[Step 2] Ingestion Agent        — Content normalisation + rubric parsing
      │
      ▼
[Step 3] ┌─────────────────────┐ ← PARALLEL
         │  Integrity Agent    │   Plagiarism + AI detection (FAISS)
         │  Grading Agent      │   Per-criterion rubric scoring (Gemini)
         └─────────────────────┘
      │
      ▼
[Step 4] Integrity threshold check (>70% → flag)
      │
      ▼
[Step 5] Human-in-the-Loop     — Teacher approve / override / flag
      │ (24h timeout → reminder)
      ▼
[Step 6] Feedback Agent         — Student report generation (Gemini)
      │
      ▼
[Step 7] ┌─────────────────────┐ ← PARALLEL
         │  Zubaan Agent (out) │   Translate feedback to student language
         │  Waalid Agent       │   WhatsApp summary to parent
         └─────────────────────┘
      │
      ▼
[Step 8] Analytics Agent        — Class trends + intervention detection
         └── [Taleem Gap Agent] — 14-day recovery plan (if triggered)
      
[Step 9] Ghost School Detector  — Daily cron, separate from submission flow
```

---

## Agents

| # | Agent | Trigger | Purpose |
|---|-------|---------|---------|
| 1 | Zubaan (input) | Every submission | Language detection + translation |
| 2 | Ingestion | Every submission | Content normalisation + rubric parsing |
| 3 | Integrity | Parallel with Grading | Plagiarism (FAISS) + AI detection |
| 4 | Grading | Parallel with Integrity | Per-criterion rubric scoring |
| 5 | Feedback | After teacher approval | Student report generation |
| 6 | Zubaan (output) | After feedback | Translate report to student language |
| 7 | Waalid | After feedback | WhatsApp parent summary |
| 8 | Analytics | After every approval | Class trends + intervention flagging |
| 9 | Taleem Gap | If 2× below 50% | 14-day SNC-aligned recovery plan |
| 10 | Ghost School | Daily cron | School submission pattern monitoring |

---

## Environment Variables

See `.env.example` for full list.

**Minimum required for demo:**
```
GEMINI_API_KEY=your-key-here
DEMO_MODE=True
```

---

## Cloud Run Deployment

```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/eduflow .

# Deploy
gcloud run deploy eduflow \
  --image gcr.io/YOUR_PROJECT/eduflow \
  --platform managed \
  --region asia-south1 \
  --set-env-vars DEMO_MODE=True,GEMINI_API_KEY=your-key
```
