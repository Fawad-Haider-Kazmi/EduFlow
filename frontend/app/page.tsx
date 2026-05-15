"use client";
import Link from "next/link";
import {
  Globe, Cpu, Shield, BookOpen, BarChart3, MessageSquare,
  Users, Target, Building2, CheckCircle, ArrowRight, ChevronRight,
} from "lucide-react";

const AGENTS = [
  { name: "Zubaan Agent",        desc: "Bidirectional language bridge — Urdu, Sindhi, Pashto, Roman Urdu", model: "gemini-2.5-flash", icon: Globe,        teal: false },
  { name: "Ingestion Agent",     desc: "Normalises content, parses rubric into structured criteria",        model: "gemini-2.5-flash", icon: Cpu,          teal: false },
  { name: "Integrity Agent",     desc: "FAISS plagiarism check + stylometric AI-content detection",         model: "gemini-2.5-flash", icon: Shield,       teal: false },
  { name: "Grading Agent",       desc: "Per-criterion rubric scoring with cited evidence",                  model: "gemini-2.5-flash", icon: BookOpen,     teal: false },
  { name: "Feedback Agent",      desc: "Warm, age-appropriate student report in English",                   model: "gemini-2.5-flash", icon: MessageSquare,teal: false },
  { name: "Analytics Agent",     desc: "Class-wide trend tracking and intervention flagging",               model: "gemini-2.5-flash", icon: BarChart3,    teal: false },
  { name: "Waalid Agent",        desc: "Parent Telegram summary in Urdu, Roman Urdu or English",           model: "gemini-2.5-flash", icon: Users,        teal: true  },
  { name: "Taleem Gap Agent",    desc: "14-day SNC-aligned recovery plan delivered daily via Telegram",     model: "gemini-2.5-flash", icon: Target,       teal: true  },
  { name: "Ghost School Detector",desc: "Daily cron — detects silent schools and escalates to DEO",        model: "gemini-2.5-flash", icon: Building2,    teal: true  },
];

const PIPELINE_DEMO = [
  { label: "Zubaan", done: true  },
  { label: "Ingest", done: true  },
  { label: "Integrity", done: true  },
  { label: "Grade",  done: true  },
  { label: "Review", done: false, active: true },
  { label: "Feedback", done: false },
  { label: "Notify", done: false },
  { label: "Analytics", done: false },
];

export default function LandingPage() {
  return (
    <div className="landing">
      {/* ── Navbar ── */}
      <nav className="landing-nav">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, background: "var(--teal)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <BookOpen size={14} color="white" />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15, color: "white" }}>EduFlow</span>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,.35)", marginLeft: 4 }}>Pakistan</span>
        </div>
        <Link href="/dashboard">
          <button className="btn btn-outline btn-sm" style={{ borderColor: "var(--teal)", color: "var(--teal)" }}>
            Sign In <ChevronRight size={13} />
          </button>
        </Link>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <div>
          <div className="hero-label">AI-Powered Education Platform</div>
          <h1 className="hero-title">AI-Powered Education for Every Pakistani Student</h1>
          <p className="hero-sub">
            9 specialized agents working together to grade, intervene, and protect 25 million learners.
            From Karachi to Gilgit — in every language.
          </p>
          <div className="hero-btns">
            <Link href="/dashboard">
              <button className="btn btn-primary btn-lg">
                Enter Dashboard <ArrowRight size={16} />
              </button>
            </Link>
            <a href="#how">
              <button className="btn btn-lg" style={{ background: "rgba(255,255,255,.08)", color: "white", border: "1px solid rgba(255,255,255,.15)" }}>
                See How It Works
              </button>
            </a>
          </div>
        </div>

        {/* Animated pipeline card */}
        <div className="hero-card">
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--teal)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 16 }}>
            Live Agent Pipeline
          </div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,.7)", marginBottom: 20 }}>
            Ahmed Ali — Pakistan Independence Essay
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {PIPELINE_DEMO.map((s, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  background: s.done ? "var(--teal)" : s.active ? "var(--teal)" : "rgba(255,255,255,.08)",
                  border: s.active ? "none" : s.done ? "none" : "1px solid rgba(255,255,255,.15)",
                  animation: s.active ? "pulse-ring 1.5s infinite" : "none",
                  fontSize: 10, color: s.done || s.active ? "white" : "rgba(255,255,255,.3)", fontWeight: 700,
                }}>
                  {s.done ? <CheckCircle size={12} /> : i + 1}
                </div>
                <span style={{ fontSize: 9, color: s.done ? "var(--teal)" : s.active ? "white" : "rgba(255,255,255,.3)" }}>{s.label}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20, padding: "10px 12px", background: "rgba(14,165,233,.08)", borderRadius: 6, borderLeft: "2px solid var(--teal)", fontSize: 12, color: "rgba(255,255,255,.6)" }}>
            Awaiting teacher review — 23h 41m remaining
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <div className="stats-bar">
        {[
          { num: "25.37M", desc: "out-of-school children in Pakistan" },
          { num: "77%",    desc: "of children cannot read by age 10" },
          { num: "48%",    desc: "of teachers are unqualified" },
          { num: "0.8%",   desc: "of GDP spent on education" },
        ].map((s, i) => (
          <div key={i} className="stat-item">
            <div className="stat-number" style={{ color: i % 2 === 0 ? "var(--slate-900)" : "#dc2626" }}>{s.num}</div>
            <div className="stat-desc">{s.desc}</div>
          </div>
        ))}
      </div>

      {/* ── How It Works ── */}
      <section className="how-section" id="how">
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, color: "var(--teal)", marginBottom: 8 }}>How It Works</div>
          <h2 style={{ fontSize: 32, fontWeight: 800, color: "white", letterSpacing: -1 }}>From submission to intervention in minutes</h2>
        </div>
        <div className="how-grid">
          {[
            { n: "01", title: "Submit", desc: "Students submit in any language — Urdu, Sindhi, Pashto, Roman Urdu, or English — in any format. Voice, text, image, or code." },
            { n: "02", title: "Analyze", desc: "9 agents run in parallel: language detection, integrity checks, rubric-based grading, class-wide calibration — all in seconds." },
            { n: "03", title: "Act",     desc: "Feedback delivered in the student's language. Parents notified via Telegram. Learning gaps closed with a 14-day plan. Ghost schools flagged to the DEO." },
          ].map(c => (
            <div key={c.n} className="how-card">
              <div className="how-num">{c.n}</div>
              <div className="how-title">{c.title}</div>
              <div className="how-desc">{c.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Agent Showcase ── */}
      <section className="agents-section">
        <div style={{ paddingLeft: 64, marginBottom: 4 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, color: "var(--teal)", marginBottom: 8 }}>The 9 Agents</div>
          <h2 style={{ fontSize: 28, fontWeight: 800, color: "white", letterSpacing: -.5 }}>Specialized intelligence, coordinated by the Orchestrator</h2>
        </div>
        <div className="agents-scroll">
          {AGENTS.map((a, i) => (
            <div key={i} className={`agent-card ${a.teal ? "teal" : ""}`}>
              <div className="agent-icon"><a.icon size={18} /></div>
              <div className="agent-name">{a.name}</div>
              <div className="agent-desc">{a.desc}</div>
              <span className="agent-model">{a.model}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        Built for Pakistan's 25M learners — EduFlow Pakistan 2026
      </footer>
    </div>
  );
}
