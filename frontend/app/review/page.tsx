"use client";
import Link from "next/link";
import useSWR from "swr";
import { CheckCircle, Clock, AlertTriangle, ArrowRight, FileText } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher } from "@/lib/api";

function PipelineMini({ step }: { step: number }) {
  return (
    <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
      {Array.from({ length: 9 }, (_, i) => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: "50%",
          background: i + 1 < step ? "var(--teal)" : i + 1 === step ? "#f59e0b" : "var(--slate-200)",
        }} />
      ))}
    </div>
  );
}

export default function GradeReviewPage() {
  const { data: submissions, isLoading } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 8000 });

  const pending = (submissions || []).filter(s => s.status === "pending_review");
  const flagged = (submissions || []).filter(s => s.status === "flagged_integrity");

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title="Grade Review" />
        <main className="page-content">
          {/* Header */}
          <div style={{ marginBottom: 24 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>Grade Review</h1>
            <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Submissions awaiting your human-in-the-loop decision.</p>
          </div>

          {/* Summary chips */}
          <div style={{ display: "flex", gap: 12, marginBottom: 28 }}>
            <div style={{ background: "white", borderRadius: 10, padding: "12px 20px", boxShadow: "0 1px 3px rgba(0,0,0,.08)", display: "flex", alignItems: "center", gap: 10, borderTop: "3px solid var(--teal)" }}>
              <Clock size={16} color="var(--teal)" />
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", lineHeight: 1 }}>{pending.length}</div>
                <div style={{ fontSize: 11, color: "var(--slate-500)", marginTop: 2 }}>Pending Review</div>
              </div>
            </div>
            <div style={{ background: "white", borderRadius: 10, padding: "12px 20px", boxShadow: "0 1px 3px rgba(0,0,0,.08)", display: "flex", alignItems: "center", gap: 10, borderTop: "3px solid #ef4444" }}>
              <AlertTriangle size={16} color="#ef4444" />
              <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", lineHeight: 1 }}>{flagged.length}</div>
                <div style={{ fontSize: 11, color: "var(--slate-500)", marginTop: 2 }}>Integrity Flagged</div>
              </div>
            </div>
          </div>

          {/* Pending review table */}
          {isLoading ? (
            <div className="card" style={{ textAlign: "center", color: "var(--slate-400)", padding: 48 }}>Loading submissions...</div>
          ) : pending.length === 0 && flagged.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: 64 }}>
              <CheckCircle size={40} color="var(--teal)" style={{ margin: "0 auto 16px" }} />
              <div style={{ fontWeight: 600, color: "var(--slate-900)", fontSize: 16 }}>All caught up!</div>
              <div style={{ color: "var(--slate-500)", fontSize: 13, marginTop: 6 }}>No submissions are waiting for your review.</div>
            </div>
          ) : (
            <>
              {pending.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 12 }}>
                    Awaiting Review — {pending.length} submission{pending.length !== 1 ? "s" : ""}
                  </div>
                  <div className="table-card">
                    <table>
                      <thead>
                        <tr>
                          <th>Student</th>
                          <th>Assignment</th>
                          <th>AI Score</th>
                          <th>Language</th>
                          <th>Pipeline</th>
                          <th>Submitted</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {pending.map(s => (
                          <tr key={s.id}>
                            <td className="td-primary" style={{ whiteSpace: "nowrap" }}>{s.student_name}</td>
                            <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                            <td style={{ fontWeight: 700, color: s.percentage >= 50 ? "var(--teal)" : "#ef4444" }}>
                              {s.percentage != null ? `${s.percentage}%` : "—"}
                            </td>
                            <td><span className="badge badge-neutral" style={{ fontSize: 10 }}>{s.original_language || "english"}</span></td>
                            <td><PipelineMini step={s.pipeline_step || 0} /></td>
                            <td style={{ fontSize: 12, color: "var(--slate-400)", whiteSpace: "nowrap" }}>{new Date(s.submitted_at).toLocaleDateString()}</td>
                            <td>
                              <Link href={`/submissions/${s.id}`} className="btn btn-primary btn-sm">
                                Review <ArrowRight size={11} />
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {flagged.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "#ef4444", marginBottom: 12 }}>
                    Integrity Flagged — Requires Manual Check
                  </div>
                  <div className="table-card">
                    <table>
                      <thead>
                        <tr>
                          <th>Student</th>
                          <th>Assignment</th>
                          <th>AI Score</th>
                          <th>Flag Reason</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {flagged.map(s => (
                          <tr key={s.id}>
                            <td className="td-primary" style={{ whiteSpace: "nowrap" }}>{s.student_name}</td>
                            <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.assignment_title}</td>
                            <td style={{ fontWeight: 700, color: "#ef4444" }}>{s.percentage != null ? `${s.percentage}%` : "—"}</td>
                            <td><span className="badge badge-flagged"><AlertTriangle size={9} /> Integrity flag</span></td>
                            <td>
                              <Link href={`/submissions/${s.id}`} className="btn btn-danger btn-sm">
                                Inspect <FileText size={11} />
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
