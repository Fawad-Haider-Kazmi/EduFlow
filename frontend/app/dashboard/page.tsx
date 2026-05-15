"use client";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { Clock, FileText, BarChart3, Building2, TrendingUp, ArrowRight, Upload, CheckCircle, AlertTriangle, BookOpen } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher, apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// ─── Shared helpers ───────────────────────────────────────────────────────────
const DEMO_STUDENT_ID  = "cccccccc-0001-0001-0001-000000000001";
const DEMO_ASSIGNMENT_ID = "dddddddd-0003-0001-0001-000000000003";

function StatCard({ label, value, sub, icon: Icon, color }: any) {
  return (
    <div className="stat-card" style={{ "--accent-color": color } as any}>
      <div className="stat-icon"><Icon size={20} /></div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value ?? "—"}</div>
      <div className="stat-sub">{sub}</div>
    </div>
  );
}

function PipelineMini({ step }: { step: number }) {
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
      {Array.from({ length: 9 }, (_, i) => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: "50%",
          background: i + 1 < step ? "var(--teal)" : i + 1 === step ? "#f59e0b" : "var(--slate-200)",
        }} />
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, [string, string]> = {
    completed:         ["badge-approved", "Approved"],
    pending_review:    ["badge-pending",  "Pending Review"],
    processing:        ["badge-progress", "Processing"],
    queued:            ["badge-neutral",  "Queued"],
    flagged_integrity: ["badge-flagged",  "Integrity Flag"],
    flagged_teacher:   ["badge-flagged",  "Flagged"],
    error:             ["badge-flagged",  "Error"],
  };
  const [cls, label] = map[status] || ["badge-neutral", status];
  return <span className={`badge ${cls}`}>{label}</span>;
}

// ─── STUDENT DASHBOARD ────────────────────────────────────────────────────────
function StudentDashboard() {
  const { data: submissions } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 8000 });
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter to demo student's submissions
  const mySubmissions = (submissions || []).filter(s => s.student_name === "Ahmed Ali");
  const latest = mySubmissions[0];
  const avgScore = mySubmissions.filter(s => s.percentage).reduce((a, s) => a + s.percentage, 0) / Math.max(mySubmissions.filter(s => s.percentage).length, 1);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setSubmitting(true); setError(null);
    try {
      await apiFetch("/api/submissions", {
        method: "POST",
        body: JSON.stringify({ student_id: DEMO_STUDENT_ID, assignment_id: DEMO_ASSIGNMENT_ID, raw_text: text }),
      });
      setText(""); setSubmitted(true);
      setTimeout(() => setSubmitted(false), 4000);
    } catch (e: any) { setError(e.message); }
    finally { setSubmitting(false); }
  };

  return (
    <main className="page-content">
      <div style={{ maxWidth: 600, marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.5 }}>My Assignments</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Ahmed Ali · Class 8-A · Government Girls Secondary School</p>
      </div>

      {/* Stats */}
      <div className="stat-grid">
        <StatCard label="Assignments Submitted" value={mySubmissions.length} sub="Total" icon={FileText} color="var(--teal)" />
        <StatCard label="Average Score" value={avgScore ? `${Math.round(avgScore)}%` : "—"} sub="Across all" icon={BarChart3} color="#8b5cf6" />
        <StatCard label="Pending Feedback" value={mySubmissions.filter(s => s.status === "pending_review" || s.status === "processing").length} sub="Being graded" icon={Clock} color="#f59e0b" />
        <StatCard label="Completed" value={mySubmissions.filter(s => s.status === "completed").length} sub="With feedback" icon={CheckCircle} color="#10b981" />
      </div>

      {/* Upload assignment */}
      <div style={{ background: "white", borderRadius: 12, padding: 24, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,.08)", borderTop: "3px solid var(--teal)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <Upload size={16} color="var(--teal)" />
          <span style={{ fontWeight: 700, color: "var(--slate-900)", fontSize: 15 }}>Submit New Assignment</span>
        </div>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Type or paste your essay here... (minimum 50 words)"
          style={{
            width: "100%", minHeight: 160, padding: "12px 14px", fontSize: 13,
            border: "1px solid #E2E8F0", borderRadius: 8, resize: "vertical",
            fontFamily: "Inter, sans-serif", color: "var(--slate-800)", lineHeight: 1.7,
            outline: "none", boxSizing: "border-box",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting || text.trim().length < 10}
            style={{ flexShrink: 0 }}
          >
            <Upload size={14} /> {submitting ? "Submitting..." : "Submit Assignment"}
          </button>
          <span style={{ fontSize: 12, color: "var(--slate-400)" }}>
            {text.trim().split(/\s+/).filter(Boolean).length} words · AI grading starts automatically
          </span>
        </div>
        {submitted && (
          <div className="alert alert-teal" style={{ marginTop: 12, fontSize: 13 }}>
            <CheckCircle size={14} /> Submitted! Your assignment is now being graded by the AI pipeline.
          </div>
        )}
        {error && (
          <div className="alert alert-amber" style={{ marginTop: 12, fontSize: 13 }}>
            <AlertTriangle size={13} /> {error}
          </div>
        )}
      </div>

      {/* Recent submissions */}
      {mySubmissions.length > 0 && (
        <div className="table-card">
          <div className="table-header">
            <span className="table-title">My Recent Submissions</span>
            <Link href="/submissions" className="btn btn-ghost btn-sm">View all <ArrowRight size={12} /></Link>
          </div>
          <table>
            <thead><tr><th>Assignment</th><th>Score</th><th>Status</th><th>Date</th><th></th></tr></thead>
            <tbody>
              {mySubmissions.slice(0, 5).map(s => (
                <tr key={s.id} onClick={() => window.location.href = `/submissions/${s.id}`}>
                  <td className="td-primary" style={{ maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                  <td style={{ fontWeight: 700, color: !s.percentage ? "var(--slate-400)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                    {s.percentage != null ? `${s.percentage}%` : "—"}
                  </td>
                  <td><StatusBadge status={s.status} /></td>
                  <td style={{ fontSize: 12, color: "var(--slate-400)" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
                  <td><Link href={`/submissions/${s.id}`} className="btn btn-ghost btn-sm">View</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

// ─── SCHOOL ADMIN DASHBOARD ───────────────────────────────────────────────────
function AdminDashboard() {
  const { data: summary } = useSWR<any>("/api/analytics/summary", swrFetcher, { refreshInterval: 15000 });
  const { data: submissions } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 10000 });

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.5 }}>School Overview</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Government Girls Secondary School, Karachi</p>
      </div>
      <div className="stat-grid">
        <StatCard label="Total Submissions" value={submissions?.length ?? 0} sub="All classes" icon={FileText} color="var(--teal)" />
        <StatCard label="School Average" value={summary ? `${summary.class_average}%` : "—"} sub="Cross-class" icon={BarChart3} color="#8b5cf6" />
        <StatCard label="Interventions" value={summary?.intervention_students ?? 0} sub="Students at risk" icon={TrendingUp} color="#f59e0b" />
        <StatCard label="Ghost School Alerts" value={summary?.ghost_school_alerts ?? 0} sub="Require attention" icon={Building2} color="#ef4444" />
      </div>
      <div className="table-card">
        <div className="table-header"><span className="table-title">All Submissions — School View</span></div>
        <table>
          <thead><tr><th>Student</th><th>Assignment</th><th>Score</th><th>Status</th><th>Date</th></tr></thead>
          <tbody>
            {(submissions || []).slice(0, 12).map(s => (
              <tr key={s.id} onClick={() => window.location.href = `/submissions/${s.id}`}>
                <td className="td-primary">{s.student_name}</td>
                <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                <td style={{ fontWeight: 700, color: !s.percentage ? "var(--slate-400)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                  {s.percentage != null ? `${s.percentage}%` : "—"}
                </td>
                <td><StatusBadge status={s.status} /></td>
                <td style={{ fontSize: 12, color: "var(--slate-400)" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

// ─── DEO OFFICER DASHBOARD ────────────────────────────────────────────────────
function DeoDashboard() {
  const { data: summary } = useSWR<any>("/api/analytics/summary", swrFetcher, { refreshInterval: 15000 });
  const { data: alerts } = useSWR<any>("/api/schools/alerts", swrFetcher, { refreshInterval: 20000 });

  const ghosts = alerts?.ghost_school || [{ school_name: "Quetta Secondary School", district: "Quetta", weeks_silent: 3, escalation_step: 1 }];

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.5 }}>District Education Overview</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>DEO Office — Karachi District</p>
      </div>
      <div className="stat-grid">
        <StatCard label="Schools Monitored" value="24" sub="Registered" icon={Building2} color="var(--teal)" />
        <StatCard label="Ghost School Flags" value={ghosts.length} sub="Need action" icon={AlertTriangle} color="#ef4444" />
        <StatCard label="District Average" value={summary ? `${summary.class_average}%` : "—"} sub="All schools" icon={BarChart3} color="#8b5cf6" />
        <StatCard label="Interventions" value={summary?.intervention_students ?? 0} sub="Students at risk" icon={TrendingUp} color="#f59e0b" />
      </div>
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 12 }}>Ghost School Escalations</div>
      {ghosts.map((a: any, i: number) => (
        <div key={i} style={{ background: "white", borderRadius: 12, padding: 20, marginBottom: 12, borderLeft: "4px solid #ef4444", boxShadow: "0 1px 3px rgba(0,0,0,.08)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 700, color: "var(--slate-900)", fontSize: 15 }}>{a.school_name}</div>
            <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 4 }}>{a.district} · {a.weeks_silent}w no submissions · Step {a.escalation_step}</div>
          </div>
          <Link href="/alerts" className="btn btn-danger btn-sm">View Escalation</Link>
        </div>
      ))}
    </main>
  );
}

// ─── CLASS TEACHER DASHBOARD ──────────────────────────────────────────────────
function TeacherDashboard() {
  const { user } = useAuth();
  const { data: summary } = useSWR<any>("/api/analytics/summary", swrFetcher, { refreshInterval: 15000 });
  const { data: submissions } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 10000 });
  const pending = (submissions || []).filter(s => s.status === "pending_review");

  return (
    <main className="page-content">
      <div style={{ maxWidth: 600, marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--slate-900)", whiteSpace: "nowrap", letterSpacing: -0.5 }}>
          Good afternoon,{" "}{user.name.replace(/^(Ms\.|Mr\.|Mrs\.|Dr\.|Prof\.)\s+/, "").split(" ")[0]}
        </h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {user.school} &mdash; {user.class}
        </p>
      </div>
      <div className="stat-grid">
        <StatCard label="Pending Reviews" value={summary?.pending_reviews ?? 0} sub="Need your action" icon={Clock} color="var(--teal)" />
        <StatCard label="Class Average" value={summary ? `${summary.class_average}%` : "—"} sub="Across all assignments" icon={BarChart3} color="#8b5cf6" />
        <StatCard label="Active Interventions" value={summary?.intervention_students ?? 0} sub="Taleem Gap plans" icon={TrendingUp} color="#f59e0b" />
        <StatCard label="Ghost School Alerts" value={summary?.ghost_school_alerts ?? 0} sub="Awaiting response" icon={Building2} color="#ef4444" />
      </div>

      {pending.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 12 }}>Requires Your Review</div>
          {pending.slice(0, 3).map(s => (
            <div key={s.id} className="animate-in" style={{ background: "white", borderRadius: 12, borderLeft: "3px solid #f59e0b", boxShadow: "0 1px 3px rgba(0,0,0,.08)", padding: "14px 20px", marginBottom: 10, display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, color: "var(--slate-900)", fontSize: 14, whiteSpace: "nowrap" }}>{s.student_name}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 3 }}>
                  <span style={{ fontSize: 12, color: "var(--slate-500)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 400 }}>{s.assignment_title}</span>
                  <span style={{ color: "var(--slate-300)" }}>·</span>
                  <span style={{ fontSize: 11, color: "var(--slate-400)", whiteSpace: "nowrap" }}>{new Date(s.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>
              <Link href={`/submissions/${s.id}`} className="btn btn-primary btn-sm" style={{ flexShrink: 0 }}>Review <ArrowRight size={12} /></Link>
            </div>
          ))}
        </div>
      )}

      <div className="table-card">
        <div className="table-header">
          <span className="table-title">Recent Submissions</span>
          <Link href="/submissions" className="btn btn-ghost btn-sm">View all <ArrowRight size={12} /></Link>
        </div>
        <table>
          <thead><tr><th>Student</th><th>Assignment</th><th>Language</th><th>Score</th><th>Status</th><th>Date</th></tr></thead>
          <tbody>
            {(submissions || []).slice(0, 8).map(s => (
              <tr key={s.id} onClick={() => window.location.href = `/submissions/${s.id}`}>
                <td className="td-primary">{s.student_name}</td>
                <td className="truncate" style={{ maxWidth: 160 }}>{s.assignment_title}</td>
                <td><span className="badge badge-neutral" style={{ fontSize: 10 }}>{s.original_language || "english"}</span></td>
                <td style={{ fontWeight: 700, color: !s.percentage ? "var(--slate-400)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                  {s.percentage != null ? `${s.percentage}%` : "—"}
                </td>
                <td><StatusBadge status={s.status} /></td>
                <td style={{ fontSize: 12, color: "var(--slate-400)" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { role } = useAuth();
  const title = { class_teacher: "Dashboard", school_admin: "School Overview", student: "My Assignments", deo_officer: "District Overview" }[role] || "Dashboard";

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title={title} />
        {role === "student"      && <StudentDashboard />}
        {role === "school_admin" && <AdminDashboard />}
        {role === "deo_officer"  && <DeoDashboard />}
        {(role === "class_teacher" || !role) && <TeacherDashboard />}
      </div>
    </div>
  );
}
