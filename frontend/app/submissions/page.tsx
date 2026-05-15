"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { ArrowRight, Search, Upload, CheckCircle, AlertTriangle, MessageSquare } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher, apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const DEMO_STUDENT_ID   = "cccccccc-0001-0001-0001-000000000001";
const DEMO_ASSIGNMENT_ID = "dddddddd-0003-0001-0001-000000000003";
const FILTERS = ["all", "pending_review", "completed", "flagged_integrity", "processing", "error"];

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

function PipelineDots({ step }: { step: number }) {
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {Array.from({ length: 9 }, (_, i) => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: "50%",
          background: i + 1 < step ? "var(--teal)" : i + 1 === step ? "#f59e0b" : "var(--slate-200)",
        }} />
      ))}
    </div>
  );
}

// ─── STUDENT: My Feedback ─────────────────────────────────────────────────────
function StudentFeedback() {
  const { data: submissions } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 8000 });
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mine = (submissions || []).filter(s => s.student_name === "Ahmed Ali");

  const handleSubmit = async () => {
    if (text.trim().length < 30) return;
    setSubmitting(true); setError(null);
    try {
      await apiFetch("/api/submissions", {
        method: "POST",
        body: JSON.stringify({ student_id: DEMO_STUDENT_ID, assignment_id: DEMO_ASSIGNMENT_ID, raw_text: text }),
      });
      setText(""); setDone(true);
      setTimeout(() => setDone(false), 5000);
    } catch (e: any) { setError(e.message || "Submission failed"); }
    finally { setSubmitting(false); }
  };

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>My Feedback</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Your submitted assignments and AI-generated feedback.</p>
      </div>

      {/* Upload card */}
      <div style={{ background: "white", borderRadius: 12, padding: 24, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,.08)", borderTop: "3px solid var(--teal)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          <Upload size={15} color="var(--teal)" />
          <span style={{ fontWeight: 700, color: "var(--slate-900)", fontSize: 14 }}>Submit a New Assignment</span>
        </div>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Write or paste your essay here..."
          style={{
            width: "100%", minHeight: 140, padding: "12px 14px", fontSize: 13,
            border: "1px solid #E2E8F0", borderRadius: 8, resize: "vertical",
            fontFamily: "Inter, sans-serif", lineHeight: 1.7, outline: "none",
            boxSizing: "border-box", color: "var(--slate-800)",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 10 }}>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || text.trim().length < 10}>
            <Upload size={13} /> {submitting ? "Submitting..." : "Submit for AI Grading"}
          </button>
          <span style={{ fontSize: 12, color: "var(--slate-400)" }}>
            {text.trim().split(/\s+/).filter(Boolean).length} words · graded automatically in ~10s
          </span>
        </div>
        {done && <div className="alert alert-teal" style={{ marginTop: 12, fontSize: 13 }}><CheckCircle size={13} /> Submitted! AI pipeline started — refresh in a few seconds.</div>}
        {error && <div className="alert alert-amber" style={{ marginTop: 12, fontSize: 13 }}><AlertTriangle size={13} /> {error}</div>}
      </div>

      {/* My submissions */}
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 12 }}>
        My Submissions ({mine.length})
      </div>
      {mine.length === 0 ? (
        <div style={{ background: "white", borderRadius: 12, padding: 48, textAlign: "center", color: "var(--slate-400)", fontSize: 14, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
          <MessageSquare size={32} style={{ margin: "0 auto 12px", opacity: .4 }} /><br />No submissions yet. Submit your first assignment above.
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr><th>Assignment</th><th>Score</th><th>Status</th><th>Date</th><th></th></tr></thead>
            <tbody>
              {mine.map(s => (
                <tr key={s.id} onClick={() => window.location.href = `/submissions/${s.id}`}>
                  <td className="td-primary" style={{ maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                  <td style={{ fontWeight: 700, color: !s.percentage ? "var(--slate-400)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                    {s.percentage != null ? `${s.percentage}%` : "—"}
                  </td>
                  <td><StatusBadge status={s.status} /></td>
                  <td style={{ fontSize: 12, color: "var(--slate-400)", whiteSpace: "nowrap" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
                  <td><Link href={`/submissions/${s.id}`} className="btn btn-ghost btn-sm">View Feedback</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

// ─── ADMIN: Classes grouped by Subject ───────────────────────────────────────
const DEMO_CLASSES = [
  { subject: "English",     teacher: "Ms. Ayesha Raza",   class: "Class 8-A" },
  { subject: "Mathematics", teacher: "Mr. Imran Hussain", class: "Class 8-A" },
  { subject: "Science",     teacher: "Ms. Nadia Tariq",   class: "Class 7-B" },
  { subject: "Urdu",        teacher: "Mr. Asif Kamal",    class: "Class 9-C" },
];

function AdminClassesView() {
  const { data: submissions, isLoading } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 10000 });
  const [expanded, setExpanded] = useState<string | null>(null);

  // Build class-level summary rows
  const classRows = DEMO_CLASSES.map(cls => {
    // For demo, English class gets the real submissions; others get simulated data
    const rows = cls.subject === "English" ? (submissions || []) : [];
    const completed = rows.filter(s => s.status === "completed");
    const avgScore = completed.length
      ? Math.round(completed.reduce((a, s) => a + (s.percentage || 0), 0) / completed.length)
      : Math.floor(55 + Math.random() * 25);
    const total = cls.subject === "English" ? rows.length : Math.floor(8 + Math.random() * 12);
    const pending = cls.subject === "English"
      ? rows.filter(s => s.status === "pending_review").length
      : Math.floor(Math.random() * 3);
    return { ...cls, total, avgScore, pending, rows };
  });

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>All Classes</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Submissions grouped by subject and teacher.</p>
      </div>

      {/* Summary stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Total Subjects",    value: DEMO_CLASSES.length,                                               color: "var(--teal)" },
          { label: "Total Submissions", value: isLoading ? "…" : classRows.reduce((a, r) => a + r.total, 0),     color: "#8b5cf6" },
          { label: "Pending Reviews",   value: isLoading ? "…" : classRows.reduce((a, r) => a + r.pending, 0),   color: "#f59e0b" },
          { label: "School Average",    value: `${Math.round(classRows.reduce((a, r) => a + r.avgScore, 0) / classRows.length)}%`, color: "#10b981" },
        ].map((c, i) => (
          <div key={i} style={{ background: "white", borderRadius: 10, padding: "16px 20px", boxShadow: "0 1px 3px rgba(0,0,0,.08)", borderTop: `3px solid ${c.color}` }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 6 }}>{c.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: c.color, letterSpacing: -1 }}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* Class rows */}
      {classRows.map(cls => (
        <div key={cls.subject} style={{ background: "white", borderRadius: 12, marginBottom: 10, boxShadow: "0 1px 3px rgba(0,0,0,.08)", overflow: "hidden" }}>
          {/* Row header */}
          <div
            onClick={() => setExpanded(expanded === cls.subject ? null : cls.subject)}
            style={{ display: "flex", alignItems: "center", padding: "16px 24px", cursor: "pointer", gap: 16, borderBottom: expanded === cls.subject ? "1px solid #F1F5F9" : "none" }}
          >
            {/* Subject badge */}
            <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--navy)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: 11, fontWeight: 700, flexShrink: 0, letterSpacing: .5 }}>
              {cls.subject.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, color: "var(--slate-900)", fontSize: 14, whiteSpace: "nowrap" }}>{cls.subject}</div>
              <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 2, whiteSpace: "nowrap" }}>{cls.teacher} · {cls.class}</div>
            </div>
            <div style={{ display: "flex", gap: 24, alignItems: "center", flexShrink: 0 }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--slate-900)" }}>{cls.total}</div>
                <div style={{ fontSize: 10, color: "var(--slate-400)", textTransform: "uppercase", letterSpacing: ".5px" }}>Submissions</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: cls.avgScore >= 60 ? "var(--teal)" : cls.avgScore >= 45 ? "#f59e0b" : "#ef4444" }}>{cls.avgScore}%</div>
                <div style={{ fontSize: 10, color: "var(--slate-400)", textTransform: "uppercase", letterSpacing: ".5px" }}>Avg Score</div>
              </div>
              {cls.pending > 0 && (
                <span className="badge badge-pending" style={{ flexShrink: 0 }}>{cls.pending} pending</span>
              )}
              <div style={{ color: "var(--slate-400)", fontSize: 18, lineHeight: 1 }}>{expanded === cls.subject ? "▲" : "▼"}</div>
            </div>
          </div>

          {/* Expanded: individual submissions for this subject */}
          {expanded === cls.subject && (
            <div style={{ padding: "0 8px 8px" }}>
              {cls.rows.length === 0 ? (
                <div style={{ padding: "20px 16px", fontSize: 13, color: "var(--slate-400)", textAlign: "center" }}>
                  Demo data — live submissions will appear here once teachers start using the system.
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #F1F5F9" }}>
                      {["Student", "Assignment", "Score", "Status", "Date"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", fontSize: 11, fontWeight: 600, color: "var(--slate-500)", textAlign: "left", textTransform: "uppercase", letterSpacing: ".5px" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cls.rows.map((s: any) => (
                      <tr key={s.id} onClick={() => window.location.href = `/submissions/${s.id}`} style={{ cursor: "pointer", borderBottom: "1px solid #F8FAFC" }}>
                        <td style={{ padding: "10px 12px", fontWeight: 600, fontSize: 13, color: "var(--slate-800)", whiteSpace: "nowrap" }}>{s.student_name}</td>
                        <td style={{ padding: "10px 12px", fontSize: 13, color: "var(--slate-600)", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                        <td style={{ padding: "10px 12px", fontWeight: 700, color: !s.percentage ? "var(--slate-300)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                          {s.percentage != null ? `${s.percentage}%` : "—"}
                        </td>
                        <td style={{ padding: "10px 12px" }}><StatusBadge status={s.status} /></td>
                        <td style={{ padding: "10px 12px", fontSize: 12, color: "var(--slate-400)", whiteSpace: "nowrap" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      ))}
    </main>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function SubmissionsPage() {
  const { role } = useAuth();

  const config: Record<string, { title: string; subtitle: string }> = {
    class_teacher: { title: "Submissions",   subtitle: "All student submissions and pipeline status." },
    deo_officer:   { title: "Ghost Schools", subtitle: "Submission patterns — district-wide view." },
  };

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title={
          role === "student"      ? "My Feedback"  :
          role === "school_admin" ? "All Classes"  :
          config[role]?.title || "Submissions"
        } />
        {role === "student"      && <StudentFeedback />}
        {role === "school_admin" && <AdminClassesView />}
        {(role === "class_teacher" || role === "deo_officer") && (
          <AllSubmissions title={config[role]?.title || "Submissions"} subtitle={config[role]?.subtitle || ""} />
        )}
      </div>
    </div>
  );
}

function AllSubmissions({ title, subtitle }: { title: string; subtitle: string }) {
  const router = useRouter();
  const { data: submissions, isLoading } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 8000 });
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = (submissions || []).filter(s => {
    if (filter !== "all" && s.status !== filter) return false;
    if (search) {
      const q = search.toLowerCase();
      return s.student_name?.toLowerCase().includes(q) || s.assignment_title?.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>{title}</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>{subtitle}</p>
      </div>

      {/* Search + Filter */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24, flexWrap: "wrap" }}>
        <div style={{ position: "relative", flex: "0 0 auto", minWidth: 200, maxWidth: 280 }}>
          <Search size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--slate-400)" }} />
          <input className="input" style={{ paddingLeft: 30 }} placeholder="Search student or assignment..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              display: "inline-flex", alignItems: "center", padding: "6px 14px",
              borderRadius: 20, fontSize: 13, cursor: "pointer", whiteSpace: "nowrap",
              border: `1px solid ${filter === f ? "var(--teal)" : "#E2E8F0"}`,
              background: filter === f ? "var(--teal)" : "white",
              color: filter === f ? "white" : "var(--slate-500)",
              fontWeight: filter === f ? 600 : 400, transition: "all .15s",
            }}>{f === "all" ? "All" : f.replace(/_/g, " ")}</button>
          ))}
        </div>
      </div>

      <div className="table-card">
        <div className="table-header"><span className="table-title">{filtered.length} submission{filtered.length !== 1 ? "s" : ""}</span></div>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--slate-400)" }}>Loading...</div>
        ) : (
          <table>
            <thead><tr><th>Student</th><th>Assignment</th><th>Language</th><th>Score</th><th>Pipeline</th><th>Status</th><th>Submitted</th><th></th></tr></thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.id} onClick={() => router.push(`/submissions/${s.id}`)}>
                  <td className="td-primary" style={{ whiteSpace: "nowrap" }}>{s.student_name}</td>
                  <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                  <td><span className="badge badge-neutral" style={{ fontSize: 10 }}>{s.original_language || "english"}</span></td>
                  <td style={{ fontWeight: 700, color: !s.percentage ? "var(--slate-400)" : s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                    {s.percentage != null ? `${s.percentage}%` : "—"}
                  </td>
                  <td><PipelineDots step={s.pipeline_step || 0} /></td>
                  <td><StatusBadge status={s.status} /></td>
                  <td style={{ fontSize: 12, color: "var(--slate-400)", whiteSpace: "nowrap" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
                  <td onClick={e => e.stopPropagation()}>
                    {s.status === "pending_review" && (
                      <Link href={`/submissions/${s.id}`} className="btn btn-primary btn-sm">Review <ArrowRight size={11} /></Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}


