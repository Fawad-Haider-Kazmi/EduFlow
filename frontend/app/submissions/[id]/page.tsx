"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import useSWR from "swr";
import { ArrowLeft, CheckCircle, Flag, AlertTriangle, Globe, FileText, Shield, BarChart3 } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher, apiFetch, API_BASE } from "@/lib/api";

function PipelineBar({ step }: { step: number }) {
  const steps = ["Zubaan","Ingest","Integrity\n+Grade","Check","Review","Feedback","Notify","Analytics","Done"];
  return (
    <div className="pipeline-bar" style={{ padding: "16px 0" }}>
      {steps.map((s, i) => {
        const n = i+1, state = n < step ? "done" : n === step ? "active" : "pending";
        return (
          <div key={i} className={`pipeline-step ${state}`}>
            <div className={`step-circle ${state}`}>
              {state === "done" ? <CheckCircle size={12} /> : <span style={{ fontSize: 11, fontWeight: 700 }}>{n}</span>}
            </div>
            <div className={`step-label ${state}`} style={{ whiteSpace: "pre-line" }}>{s}</div>
          </div>
        );
      })}
    </div>
  );
}

function IntegrityPanel({ integrity }: { integrity: any }) {
  if (!integrity) return null;
  const plag = integrity.plagiarism_score ?? 0;
  const ai   = integrity.ai_generated_score ?? 0;
  const color = (v: number) => v > 70 ? "#ef4444" : v > 40 ? "#f59e0b" : "var(--teal)";
  return (
    <div className="card animate-in" style={{ borderLeft: integrity.flag ? "3px solid #ef4444" : "3px solid var(--teal)" }}>
      <div className="flex items-center justify-between mb-4">
        <div className="section-label" style={{ margin: 0 }}>Integrity Report</div>
        <span className={`badge ${integrity.flag ? "badge-flagged" : "badge-approved"}`}>
          <Shield size={10} /> {integrity.flag ? "Flagged" : "Clean"}
        </span>
      </div>
      <div className="grid-2">
        {[["Plagiarism", plag, integrity.plagiarism_evidence], ["AI-Generated", ai, integrity.ai_evidence]].map(([label, val, ev], i) => (
          <div key={i}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted">{label as string}</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: color(val as number) }}>{val as number}%</span>
            </div>
            <div className="progress-bar mb-2">
              <div className="progress-fill" style={{ width: `${val}%`, background: color(val as number) }} />
            </div>
            <p className="text-sm text-muted">{ev as string}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function GradingPanel({ grading }: { grading: any }) {
  if (!grading?.criteria_scores) return null;
  return (
    <div className="card animate-in">
      <div className="flex items-center justify-between mb-4">
        <div className="section-label" style={{ margin: 0 }}>Grading Breakdown</div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: grading.percentage >= 50 ? "var(--teal)" : "#ef4444", letterSpacing: -1 }}>
            {grading.percentage}%
          </div>
          <div className="text-sm text-muted">{grading.total_score}/{grading.total_max} pts</div>
        </div>
      </div>
      {grading.language_barrier_note && (
        <div className="alert alert-blue mb-4"><Globe size={14} /><span>{grading.language_barrier_note}</span></div>
      )}
      {grading.criteria_scores.map((c: any, i: number) => {
        const pct = c.max > 0 ? (c.score / c.max) * 100 : 0;
        const col = pct >= 70 ? "var(--teal)" : pct >= 50 ? "#f59e0b" : "#ef4444";
        return (
          <div key={i} className="criterion-row">
            <div className="criterion-header">
              <span className="criterion-name">{c.criterion}</span>
              <span className="criterion-score" style={{ color: col }}>{c.score}/{c.max}</span>
            </div>
            <div className="progress-bar mb-2"><div className="progress-fill" style={{ width: `${pct}%`, background: col }} /></div>
            <p className="criterion-rationale">{c.rationale}</p>
            {c.cited_text && <p className="criterion-cite">"{c.cited_text}"</p>}
          </div>
        );
      })}
    </div>
  );
}

export default function SubmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: sub, mutate, isLoading } = useSWR<any>(`/api/submissions/${id}`, swrFetcher, { refreshInterval: 5000 });
  const [overrideScore, setOverrideScore] = useState<number | null>(null);
  const [flagReason, setFlagReason] = useState("");
  const [showFlag, setShowFlag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const ws = new WebSocket(`${API_BASE.replace("http","ws")}/ws/pipeline/${id}`);
    ws.onmessage = () => mutate();
    return () => ws.close();
  }, [id, mutate]);

  if (isLoading) return (
    <div className="shell"><Sidebar />
      <div className="main-area"><Navbar title="Loading..." />
        <main className="page-content" style={{ display:"flex", alignItems:"center", justifyContent:"center", color:"var(--slate-400)" }}>Loading submission...</main>
      </div>
    </div>
  );
  if (!sub) return null;

  const isPending = sub.status === "pending_review";
  const effectiveScore = overrideScore ?? sub.grading?.total_score ?? 0;
  const effectivePct = sub.grading?.total_max > 0 ? Math.round((effectiveScore / sub.grading.total_max) * 100) : 0;

  const handleApprove = async () => {
    setLoading(true);
    setActionError(null);
    try {
      const endpoint = overrideScore !== null && overrideScore !== sub.grading?.total_score ? "override" : "approve";
      const body = endpoint === "override" ? { override_score: overrideScore } : undefined;
      await apiFetch(`/api/review/${id}/${endpoint}`, { method: "POST", body: body ? JSON.stringify(body) : undefined });
      await mutate();
      router.push("/submissions");
    } catch (err: any) {
      setActionError(err.message || "Could not approve submission. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFlag = async () => {
    if (!flagReason) return;
    setLoading(true);
    setActionError(null);
    try {
      await apiFetch(`/api/review/${id}/flag`, { method: "POST", body: JSON.stringify({ reason: flagReason }) });
      await mutate();
      router.push("/submissions");
    } catch (err: any) {
      setActionError(err.message || "Could not flag submission. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Stop processing this submission? This will reset it so you can submit a new task.")) return;
    setCancelLoading(true);
    try {
      await apiFetch(`/api/submissions/${id}/cancel`, { method: "POST" });
      await mutate();
      router.push("/submissions");
    } catch (err: any) {
      setActionError(err.message || "Could not cancel submission.");
      setCancelLoading(false);
    }
  };

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title="Submission Review" />
        <main className="page-content">
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <Link href="/submissions" className="btn btn-ghost btn-sm"><ArrowLeft size={14} /> Back</Link>
            <div style={{ flex: 1 }}>
              <h1 className="page-title">{sub.student?.name} — {sub.assignment?.title}</h1>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm text-muted">Grade {sub.student?.grade} &bull; {sub.student?.language}</span>
                {sub.status === "pending_review" && <span className="badge badge-pending">Awaiting Review</span>}
                {sub.status === "completed"      && <span className="badge badge-approved">Completed</span>}
                {sub.status === "processing"     && <span className="badge badge-progress">Processing…</span>}
                {sub.status === "queued"         && <span className="badge badge-neutral">Queued</span>}
                {sub.status === "cancelled"      && <span className="badge badge-flagged">Cancelled</span>}
                {sub.integrity?.flag             && <span className="badge badge-flagged"><AlertTriangle size={10} /> Integrity Flag</span>}
              </div>
            </div>
            {/* Stop Processing button — only visible when pipeline is still running */}
            {(sub.status === "processing" || sub.status === "queued") && (
              <button
                className="btn btn-danger btn-sm"
                onClick={handleCancel}
                disabled={cancelLoading}
                style={{ flexShrink: 0 }}
              >
                ✕ {cancelLoading ? "Stopping…" : "Stop Processing"}
              </button>
            )}
          </div>

          {/* Pipeline */}
          <div className="card mb-6" style={{ padding: "12px 24px" }}>
            <PipelineBar step={sub.pipeline_step || 0} />
          </div>

          {/* Integrity warning */}
          {sub.integrity?.flag && (
            <div className="alert alert-amber mb-6">
              <AlertTriangle size={16} />
              <div><strong>Integrity concerns detected.</strong> Plagiarism: {sub.integrity.plagiarism_score}% &bull; AI-generated: {sub.integrity.ai_generated_score}%. Review evidence before approving.</div>
            </div>
          )}

          <div className="split-pane mb-6">
            {/* Left */}
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
              <div className="card">
                <div className="section-label"><FileText size={12} style={{ display:"inline", marginRight:4 }} />Student Submission</div>
                <div className="text-sm text-muted mb-3">{sub.original_language} &bull; {sub.word_count || "—"} words{sub.was_translated ? " &bull; Translated to English" : ""}</div>
                {sub.was_translated && (
                  <>
                    <div className="section-label" style={{ fontSize:10 }}>Original</div>
                    <div style={{ background:"var(--slate-50)", borderRadius:6, padding:12, fontSize:13, color:"var(--slate-700)", lineHeight:1.8, marginBottom:12, fontFamily:"serif" }}>
                      {sub.raw_text}
                    </div>
                    <div className="section-label" style={{ fontSize:10 }}>English Translation</div>
                  </>
                )}
                <div style={{ background:"var(--slate-50)", borderRadius:6, padding:12, fontSize:13, color:"var(--slate-800)", lineHeight:1.8 }}>
                  {sub.translated_text || sub.raw_text}
                </div>
              </div>
              <IntegrityPanel integrity={sub.integrity} />
            </div>

            {/* Right */}
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
              <GradingPanel grading={sub.grading} />

              {/* HITL Card */}
              {isPending && (
                <div className="card animate-in" style={{ borderTop:"3px solid var(--teal)" }}>
                  <div className="section-label">Your Decision</div>
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted">Score Override (optional)</span>
                      <span style={{ fontSize:20, fontWeight:800, color:"var(--teal)" }}>
                        {effectiveScore}/{sub.grading?.total_max || 50} ({effectivePct}%)
                      </span>
                    </div>
                    <input
                      type="range" min={0} max={sub.grading?.total_max || 50} step={1}
                      value={overrideScore ?? sub.grading?.total_score ?? 0}
                      onChange={e => setOverrideScore(Number(e.target.value))}
                    />
                    {overrideScore !== null && overrideScore !== sub.grading?.total_score && (
                      <div className="alert alert-amber mt-3" style={{ fontSize:12, padding:"8px 12px" }}>
                        Overriding AI grade: {sub.grading?.total_score} &rarr; {overrideScore}
                      </div>
                    )}
                  </div>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {actionError && (
                      <div className="alert alert-amber" style={{ fontSize: 12 }}>
                        <AlertTriangle size={13} />
                        <span>{actionError}</span>
                      </div>
                    )}
                    <button id="approve-btn" className="btn btn-primary" onClick={handleApprove} disabled={loading}>
                      <CheckCircle size={14} />
                      {loading ? "Processing..." : overrideScore !== null && overrideScore !== sub.grading?.total_score ? "Override & Approve" : "Approve Grade"}
                    </button>
                    <button className="btn btn-danger" onClick={() => setShowFlag(f => !f)} disabled={loading}>
                      <Flag size={14} /> Flag for Investigation
                    </button>
                  </div>
                  {showFlag && (
                    <div className="mt-3">
                      <input className="input mb-2" placeholder="Reason for flagging..." value={flagReason} onChange={e => setFlagReason(e.target.value)} />
                      <button className="btn btn-danger btn-sm" onClick={handleFlag} disabled={!flagReason || loading}>Confirm Flag</button>
                    </div>
                  )}
                  <div className="divider" />
                  <p className="text-sm text-muted">Review deadline: {sub.review?.deadline ? new Date(sub.review.deadline).toLocaleString() : "24 hours"}</p>
                </div>
              )}

              {/* Feedback */}
              {sub.feedback?.english && (
                <div className="card animate-in">
                  <div className="section-label">Generated Feedback</div>
                  <div style={{ background:"var(--slate-50)", borderRadius:6, padding:14, fontSize:13, color:"var(--slate-800)", lineHeight:1.8, whiteSpace:"pre-wrap" }}>
                    {sub.feedback.english}
                  </div>
                  {sub.feedback.translated && (
                    <>
                      <div className="section-label mt-3" style={{ fontSize:10 }}>Translated ({sub.original_language})</div>
                      <div style={{ background:"var(--slate-50)", borderRadius:6, padding:14, fontSize:13, color:"var(--slate-600)", lineHeight:1.8, fontFamily:"serif" }}>
                        {sub.feedback.translated}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Agent logs */}
          {sub.agent_logs?.length > 0 && (
            <div className="card">
              <div className="section-label">Agent Execution Log</div>
              <div className="log-panel">
                {sub.agent_logs.map((l: any, i: number) => (
                  <div key={i} className={`log-line ${l.status === "success" ? "success" : l.status === "failed" ? "error" : "running"}`}>
                    [{l.called_at?.slice(11,19)}] {l.agent}{l.duration_ms ? ` (${l.duration_ms}ms)` : ""} — {l.status.toUpperCase()}
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
