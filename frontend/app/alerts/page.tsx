"use client";
import useSWR from "swr";
import { AlertTriangle, Building2, CheckCircle, Clock, Target, MessageSquare, BookOpen } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const GHOST_DEMO = [{
  school_name: "Quetta Secondary School", district: "Quetta", flag_type: "ghost_school",
  weeks_silent: 3, escalation_step: 1, admin_notified: true, deo_escalated: false,
  created_at: new Date(Date.now() - 6 * 3600000).toISOString(),
}];
const INTERVENTION_DEMO = [
  { student_name: "Bilal Ahmed",  dropout_risk: false },
  { student_name: "Fatima Noor", dropout_risk: true  },
];
const ESCALATION_STEPS = [
  { label: "Alert detected" },
  { label: "Admin notified" },
  { label: "48h wait" },
  { label: "Escalate to DEO" },
];

// ─── Student: My Recovery Plan ────────────────────────────────────────────────
function StudentRecoveryPlan() {
  const { data: submissions } = useSWR<any[]>("/api/submissions", swrFetcher, { refreshInterval: 10000 });
  const mine = (submissions || []).filter(s => s.student_name === "Ahmed Ali");
  const avgScore = mine.filter(s => s.percentage).reduce((a, s) => a + s.percentage, 0) / Math.max(mine.filter(s => s.percentage).length, 1);
  const needsIntervention = avgScore < 50 && mine.length > 0;

  const PLAN_TASKS = [
    { day: "Day 1–3",  task: "Review rubric criteria: Argument Clarity & Evidence",    done: true },
    { day: "Day 4–6",  task: "Write 3 practice paragraphs with cited evidence",        done: true },
    { day: "Day 7–9",  task: "Peer feedback exercise on Structure scoring",            done: false },
    { day: "Day 10–12", task: "Submit revised essay draft for AI pre-check",           done: false },
    { day: "Day 13–14", task: "Final review session with teacher",                     done: false },
  ];

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>My Recovery Plan</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>
          Ahmed Ali · {needsIntervention ? "Taleem Gap intervention active" : "No active intervention — keep it up!"}
        </p>
      </div>

      {!needsIntervention ? (
        <div style={{ background: "white", borderRadius: 12, padding: 48, textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
          <CheckCircle size={40} color="var(--teal)" style={{ margin: "0 auto 16px" }} />
          <div style={{ fontWeight: 600, color: "var(--slate-900)", fontSize: 16 }}>No Active Recovery Plan</div>
          <div style={{ color: "var(--slate-500)", fontSize: 13, marginTop: 8, maxWidth: 400, margin: "8px auto 0" }}>
            You're performing well! If your average drops below 50%, an AI-generated recovery plan will appear here automatically.
          </div>
        </div>
      ) : (
        <>
          <div style={{ background: "white", borderRadius: 12, borderLeft: "4px solid #f59e0b", padding: 20, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <AlertTriangle size={15} color="#f59e0b" />
              <span style={{ fontWeight: 700, fontSize: 13, color: "var(--slate-900)" }}>Taleem Gap Intervention Active</span>
            </div>
            <p style={{ fontSize: 13, color: "var(--slate-700)", lineHeight: 1.7, margin: 0 }}>
              Your average is below 50%. A 14-day SNC-aligned recovery plan has been created for you. Daily tasks are sent to your parent at 5 PM via Telegram. Help: <strong>0800-26477</strong>
            </p>
          </div>

          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 16 }}>14-Day Recovery Tasks</div>
          {PLAN_TASKS.map((t, i) => (
            <div key={i} style={{ background: "white", borderRadius: 10, padding: "14px 20px", marginBottom: 10, boxShadow: "0 1px 3px rgba(0,0,0,.06)", display: "flex", alignItems: "center", gap: 16, opacity: t.done ? 1 : 0.75 }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", background: t.done ? "var(--teal)" : "var(--slate-100)", color: t.done ? "white" : "var(--slate-400)" }}>
                {t.done ? <CheckCircle size={14} /> : <span style={{ fontSize: 11, fontWeight: 700 }}>{i + 1}</span>}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--slate-500)", marginBottom: 2 }}>{t.day}</div>
                <div style={{ fontSize: 13, color: t.done ? "var(--slate-400)" : "var(--slate-800)", textDecoration: t.done ? "line-through" : "none" }}>{t.task}</div>
              </div>
              {t.done && <span className="badge badge-approved" style={{ fontSize: 10 }}>Done</span>}
            </div>
          ))}
        </>
      )}

      {/* Announcements */}
      <div style={{ marginTop: 24, background: "white", borderRadius: 12, padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          <MessageSquare size={15} color="var(--teal)" />
          <span style={{ fontWeight: 700, fontSize: 13, color: "var(--slate-900)" }}>Government Support Resources</span>
        </div>
        {[
          { title: "Ehsaas Wazaifa", desc: "Monthly stipend for at-risk students. Call 0800-26477 to apply.", icon: BookOpen },
          { title: "Taleem Online Portal", desc: "Free SNC-aligned video lessons — all subjects, all grades.", icon: Target },
        ].map((r, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "12px 0", borderTop: i > 0 ? "1px solid #F1F5F9" : "none" }}>
            <r.icon size={16} color="var(--slate-400)" style={{ marginTop: 2, flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, color: "var(--slate-800)" }}>{r.title}</div>
              <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 2 }}>{r.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

// ─── Teacher / Admin / DEO: Ghost School Alerts ───────────────────────────────
function GhostSchoolAlerts({ title, subtitle }: { title: string; subtitle: string }) {
  const { data: alertsData } = useSWR<any>("/api/schools/alerts", swrFetcher, { refreshInterval: 20000 });
  const ghosts       = alertsData?.ghost_school  || GHOST_DEMO;
  const interventions = alertsData?.intervention || INTERVENTION_DEMO;
  const errors       = alertsData?.errors        || [];

  return (
    <main className="page-content">
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>{title}</h1>
          <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>{subtitle}</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {ghosts.length > 0 && <span className="badge badge-flagged"><Building2 size={10} /> {ghosts.length} Ghost</span>}
          {interventions.length > 0 && <span className="badge badge-pending"><Target size={10} /> {interventions.length} Interventions</span>}
        </div>
      </div>

      {/* Ghost Schools */}
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em", color: "#94a3b8", marginBottom: 16 }}>Ghost School Alerts</div>
      {ghosts.length === 0
        ? <div className="card" style={{ fontSize: 13, color: "var(--slate-400)" }}>No ghost school alerts — all schools submitting normally.</div>
        : ghosts.map((a: any, i: number) => (
          <div key={i} style={{ background: "white", borderRadius: 12, padding: 24, marginBottom: 16, borderLeft: `4px solid ${a.deo_escalated ? "#ef4444" : "#F59E0B"}`, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }} className="animate-in">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "var(--slate-900)", display: "flex", alignItems: "center", gap: 6 }}>
                  <Building2 size={15} color="var(--slate-500)" /> {a.school_name}
                </div>
                <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 4 }}>{a.district} · {a.flag_type.replace(/_/g, " ")}</div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <span className="badge badge-neutral"><Clock size={9} /> {a.weeks_silent}w silent</span>
                {a.deo_escalated
                  ? <span className="badge badge-flagged">Escalated to DEO</span>
                  : <span className="badge badge-pending">Step 1: Admin Notified</span>
                }
              </div>
            </div>
            {/* Escalation timeline */}
            <div style={{ display: "flex", gap: 0, alignItems: "center", marginBottom: 16 }}>
              {ESCALATION_STEPS.map((step, si) => {
                const done = si === 0 || (si === 1 && a.admin_notified) || (si === 2 && a.escalation_step >= 2) || (si === 3 && a.deo_escalated);
                return (
                  <div key={si} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                    <div style={{ width: 26, height: 26, borderRadius: "50%", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", background: done ? "var(--teal)" : "var(--slate-100)", border: `1px solid ${done ? "var(--teal)" : "var(--slate-200)"}`, color: done ? "white" : "var(--slate-400)", fontSize: 11, fontWeight: 700 }}>
                      {done ? <CheckCircle size={12} /> : si + 1}
                    </div>
                    <div style={{ marginLeft: 6, marginRight: si < 3 ? 12 : 0, flex: 1 }}>
                      <div style={{ fontSize: 11, color: done ? "var(--teal)" : "var(--slate-400)", fontWeight: done ? 600 : 400, whiteSpace: "nowrap" }}>{step.label}</div>
                    </div>
                    {si < 3 && <div style={{ height: 1, flex: 1, background: done ? "var(--teal)" : "var(--slate-200)", marginRight: 6 }} />}
                  </div>
                );
              })}
            </div>
            <div className="alert alert-amber" style={{ fontSize: 12 }}>
              <AlertTriangle size={13} />
              <div>Admin notified and given 48 hours to respond. DEO escalation blocked until admin non-response is confirmed.</div>
            </div>
          </div>
        ))
      }

      <div style={{ height: 1, background: "var(--slate-100)", margin: "24px 0" }} />

      {/* Taleem Gap Programs */}
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em", color: "#94a3b8", marginBottom: 16 }}>Active Taleem Gap Programs</div>
      {interventions.length === 0
        ? <div className="card" style={{ fontSize: 13, color: "var(--slate-400)" }}>No students currently in active intervention.</div>
        : interventions.map((s: any, i: number) => (
          <div key={i} style={{ background: "white", borderRadius: 12, padding: 20, marginBottom: 10, borderLeft: `3px solid ${s.dropout_risk ? "#ef4444" : "var(--teal)"}`, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }} className="animate-in">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontWeight: 700, color: "var(--slate-900)", fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
                  <Target size={14} color="var(--slate-500)" /> {s.student_name}
                  {s.dropout_risk && <span className="badge badge-flagged"><AlertTriangle size={9} /> Dropout Risk</span>}
                </div>
                <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 4 }}>14-day SNC-aligned recovery plan · Daily tasks via Telegram at 5 PM</div>
              </div>
            </div>
            {s.dropout_risk && (
              <div className="alert alert-amber" style={{ marginTop: 12, fontSize: 12 }}>
                <MessageSquare size={13} />
                <div>Dropout risk alert sent to parent via Telegram. Ehsaas Wazaifa info and helpline <strong>0800-26477</strong> included.</div>
              </div>
            )}
          </div>
        ))
      }

      {errors.length > 0 && (
        <>
          <div style={{ height: 1, background: "var(--slate-100)", margin: "24px 0" }} />
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em", color: "#94a3b8", marginBottom: 16 }}>Pipeline Errors</div>
          {errors.map((e: any, i: number) => (
            <div key={i} className="card" style={{ borderLeft: "3px solid #ef4444", marginBottom: 10 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: 600, color: "#ef4444", fontSize: 13 }}>Submission {e.submission_id?.slice(0, 8)}...</div>
                  <div style={{ fontSize: 12, color: "var(--slate-500)", marginTop: 4 }}>{e.error}</div>
                </div>
                <a href={`/submissions/${e.submission_id}`} className="btn btn-danger btn-sm">Inspect</a>
              </div>
            </div>
          ))}
        </>
      )}
    </main>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function AlertsPage() {
  const { role } = useAuth();

  const config: Record<string, { title: string; subtitle: string }> = {
    class_teacher: { title: "Improvement Plans",   subtitle: "Ghost school flags and Taleem Gap interventions." },
    school_admin:  { title: "Ghost School Alerts", subtitle: "Schools that have gone silent — escalation tracking." },
    deo_officer:   { title: "Escalations",         subtitle: "Schools escalated to DEO for non-response." },
  };

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title={role === "student" ? "My Recovery Plan" : (config[role]?.title || "Alerts")} />
        {role === "student"
          ? <StudentRecoveryPlan />
          : <GhostSchoolAlerts title={config[role]?.title || "Alerts"} subtitle={config[role]?.subtitle || ""} />
        }
      </div>
    </div>
  );
}
