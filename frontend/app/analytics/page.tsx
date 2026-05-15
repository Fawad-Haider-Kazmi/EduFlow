"use client";
import useSWR from "swr";
import { TrendingDown, TrendingUp, Minus, AlertTriangle, BarChart3 } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { swrFetcher } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, Title, Tooltip, Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

const CHART_DEFAULTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#64748b", font: { family: "Inter", size: 11 } } },
    tooltip: { backgroundColor: "#fff", borderColor: "#e2e8f0", borderWidth: 1, titleColor: "#0f172a", bodyColor: "#64748b" },
  },
  scales: {
    x: { grid: { color: "rgba(0,0,0,.04)" }, ticks: { color: "#94a3b8", font: { family: "Inter", size: 11 } } },
    y: { grid: { color: "rgba(0,0,0,.04)" }, ticks: { color: "#94a3b8", font: { family: "Inter", size: 11 } }, min: 0, max: 100 },
  },
};

const FALLBACK = {
  class_average: 64,
  weakest_criteria: ["Use of Evidence", "Critical Thinking"],
  criterion_breakdown: [
    { criterion: "Argument Clarity",  class_avg: 74 },
    { criterion: "Use of Evidence",   class_avg: 44 },
    { criterion: "Structure",         class_avg: 81 },
    { criterion: "Language Quality",  class_avg: 68 },
    { criterion: "Critical Thinking", class_avg: 51 },
  ],
  student_trends: [
    { name: "Ahmed Ali",        last_3: [58, 65, 72], trend: "improving" },
    { name: "Sara Malik",       last_3: [61, 63, 62], trend: "stable"    },
    { name: "Bilal Ahmed",      last_3: [55, 47, 44], trend: "declining" },
    { name: "Fatima Noor",      last_3: [48, 42, 38], trend: "declining" },
    { name: "Zain Ul Abideen", last_3: [75, 82, 88], trend: "improving" },
  ],
  teacher_summary: "Most students struggled with Use of Evidence (avg 44%) and Critical Thinking (avg 51%). 2 students flagged for Taleem Gap intervention.",
};

// ─── Student: My Progress ─────────────────────────────────────────────────────
function StudentProgress() {
  const { data } = useSWR<any>("/api/analytics/class/demo", swrFetcher, { refreshInterval: 30000 });
  const d = data || FALLBACK;

  // Find Ahmed Ali's data
  const me = d.student_trends.find((s: any) => s.name === "Ahmed Ali") || d.student_trends[0];
  const myScores = me?.last_3 || [0, 0, 0];
  const myTrend = me?.trend || "stable";
  const myAvg = Math.round(myScores.reduce((a: number, b: number) => a + b, 0) / myScores.length);

  const lineData = {
    labels: ["Assignment 1", "Assignment 2", "Assignment 3"],
    datasets: [{
      label: "My Score (%)",
      data: myScores,
      borderColor: "#0ea5e9",
      backgroundColor: "rgba(14,165,233,.12)",
      fill: true, tension: 0.3, pointRadius: 5,
    }, {
      label: "Class Average (%)",
      data: [d.class_average, d.class_average, d.class_average],
      borderColor: "#94a3b8",
      backgroundColor: "transparent",
      borderDash: [4, 4], tension: 0, pointRadius: 0,
    }],
  };

  const critColors = d.criterion_breakdown.map((c: any) =>
    c.class_avg >= 70 ? "rgba(14,165,233,.7)" : c.class_avg >= 50 ? "rgba(245,158,11,.7)" : "rgba(239,68,68,.7)"
  );
  const barData = {
    labels: d.criterion_breakdown.map((c: any) => c.criterion),
    datasets: [{ label: "Class Average (%)", data: d.criterion_breakdown.map((c: any) => c.class_avg), backgroundColor: critColors, borderRadius: 6 }],
  };

  const TrendIcon = myTrend === "improving" ? TrendingUp : myTrend === "declining" ? TrendingDown : Minus;
  const trendColor = myTrend === "improving" ? "var(--teal)" : myTrend === "declining" ? "#ef4444" : "var(--slate-400)";

  return (
    <main className="page-content">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>My Progress</h1>
        <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>Ahmed Ali · Class 8-A performance tracker</p>
      </div>

      {/* Personal stat row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
        {[
          { label: "My Average", value: `${myAvg}%`, sub: "Last 3 assignments", color: "var(--teal)" },
          { label: "Class Average", value: `${d.class_average}%`, sub: "Benchmark", color: "#8b5cf6" },
          { label: "My Trend", value: myTrend.charAt(0).toUpperCase() + myTrend.slice(1), sub: "Recent direction", color: trendColor },
        ].map((c, i) => (
          <div key={i} style={{ background: "white", borderRadius: 12, padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,.08)", borderTop: `3px solid ${c.color}` }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".5px", color: "var(--slate-500)", marginBottom: 6 }}>{c.label}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: c.color, letterSpacing: -1, display: "flex", alignItems: "center", gap: 8 }}>
              {c.value} {c.label === "My Trend" && <TrendIcon size={20} color={c.color} />}
            </div>
            <div style={{ fontSize: 12, color: "var(--slate-400)", marginTop: 4 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* AI Summary */}
      <div style={{ background: "white", borderRadius: 12, borderLeft: "4px solid var(--teal)", padding: 20, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <BarChart3 size={15} color="var(--teal)" />
          <span style={{ fontWeight: 700, fontSize: 13, color: "var(--slate-900)" }}>Teacher's AI Summary for your Class</span>
        </div>
        <p style={{ fontSize: 13, color: "var(--slate-700)", lineHeight: 1.7, margin: 0 }}>{d.teacher_summary}</p>
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div className="card">
          <div className="section-label">My Score vs Class Average</div>
          <div style={{ height: 220 }}><Line data={lineData} options={CHART_DEFAULTS as any} /></div>
        </div>
        <div className="card">
          <div className="section-label">Class Criterion Breakdown</div>
          <div style={{ height: 220 }}>
            <Bar data={barData} options={{ ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } } as any} />
          </div>
          <div className="mt-3">
            <div style={{ fontSize: 12, color: "var(--slate-500)", marginBottom: 6 }}>Class weak areas:</div>
            {d.weakest_criteria.map((c: string, i: number) => <span key={i} className="badge badge-flagged" style={{ marginRight: 6, fontSize: 10 }}>{c}</span>)}
          </div>
        </div>
      </div>
    </main>
  );
}

// ─── Teacher / Admin / DEO: Class Analytics ───────────────────────────────────
function ClassAnalytics({ title, subtitle }: { title: string; subtitle: string }) {
  const { data } = useSWR<any>("/api/analytics/class/demo", swrFetcher, { refreshInterval: 30000 });
  const d = data || FALLBACK;

  const critColors = d.criterion_breakdown.map((c: any) =>
    c.class_avg >= 70 ? "rgba(14,165,233,.7)" : c.class_avg >= 50 ? "rgba(245,158,11,.7)" : "rgba(239,68,68,.7)"
  );
  const barData = {
    labels: d.criterion_breakdown.map((c: any) => c.criterion),
    datasets: [{ label: "Class Average (%)", data: d.criterion_breakdown.map((c: any) => c.class_avg), backgroundColor: critColors, borderRadius: 6 }],
  };
  const lineColors = ["#0ea5e9", "#8b5cf6", "#ef4444", "#f59e0b", "#10b981"];
  const lineData = {
    labels: ["Assignment 1", "Assignment 2", "Assignment 3"],
    datasets: d.student_trends.map((s: any, i: number) => ({
      label: s.name, data: s.last_3, borderColor: lineColors[i],
      backgroundColor: `${lineColors[i]}18`, fill: false, tension: 0.3, pointRadius: 4,
    })),
  };

  const TrendIcon = ({ t }: { t: string }) =>
    t === "improving" ? <TrendingUp size={12} /> : t === "declining" ? <TrendingDown size={12} /> : <Minus size={12} />;

  return (
    <main className="page-content">
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--slate-900)", letterSpacing: -0.3 }}>{title}</h1>
          <p style={{ fontSize: 13, color: "var(--slate-500)", marginTop: 4 }}>{subtitle}</p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 32, fontWeight: 800, color: "var(--slate-900)", letterSpacing: -1 }}>{d.class_average}%</div>
          <div style={{ fontSize: 12, color: "var(--slate-400)" }}>Class Average</div>
        </div>
      </div>

      <div style={{ background: "white", borderRadius: 12, borderLeft: "4px solid var(--teal)", padding: 24, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <BarChart3 size={16} color="var(--teal)" />
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--slate-900)" }}>AI Summary</span>
        </div>
        <p style={{ fontSize: 14, color: "var(--slate-700)", lineHeight: 1.7, maxWidth: 800, margin: 0 }}>{d.teacher_summary}</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        <div className="card">
          <div className="section-label">Score by Criterion</div>
          <div style={{ height: 240 }}>
            <Bar data={barData} options={{ ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } } as any} />
          </div>
          <div className="mt-3">
            <div className="text-sm text-muted mb-2">Weakest areas:</div>
            {d.weakest_criteria.map((c: string, i: number) => <span key={i} className="badge badge-flagged" style={{ marginRight: 6 }}>{c}</span>)}
          </div>
        </div>
        <div className="card">
          <div className="section-label">Student Trends — Last 3 Assignments</div>
          <div style={{ height: 240 }}><Line data={lineData} options={CHART_DEFAULTS as any} /></div>
        </div>
      </div>

      <div className="table-card">
        <div className="table-header"><span className="table-title">Student Performance</span></div>
        <table>
          <thead><tr><th>Student</th><th>Assign 1</th><th>Assign 2</th><th>Assign 3</th><th>Trend</th><th>Intervention</th></tr></thead>
          <tbody>
            {d.student_trends.map((s: any, i: number) => (
              <tr key={i}>
                <td className="td-primary">{s.name}</td>
                {s.last_3.map((score: number, j: number) => (
                  <td key={j} style={{ fontWeight: 700, color: score >= 70 ? "var(--teal)" : score >= 50 ? "#f59e0b" : "#ef4444" }}>{score}%</td>
                ))}
                <td>
                  <span className={`badge ${s.trend === "improving" ? "badge-approved" : s.trend === "declining" ? "badge-flagged" : "badge-neutral"}`}>
                    <TrendIcon t={s.trend} /> {s.trend}
                  </span>
                </td>
                <td>
                  {s.last_3[2] < 50 && s.last_3[1] < 50
                    ? <span className="badge badge-pending"><AlertTriangle size={10} /> Taleem Gap</span>
                    : <span className="badge badge-neutral">—</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function AnalyticsPage() {
  const { role } = useAuth();

  const config: Record<string, { title: string; subtitle: string }> = {
    class_teacher: { title: "Class Analytics",    subtitle: "Performance trends and intervention flags." },
    school_admin:  { title: "School Reports",     subtitle: "Aggregated analytics across all classes." },
    deo_officer:   { title: "District Reports",   subtitle: "District-wide performance and school comparisons." },
  };

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title={role === "student" ? "My Progress" : (config[role]?.title || "Analytics")} />
        {role === "student"
          ? <StudentProgress />
          : <ClassAnalytics title={config[role]?.title || "Analytics"} subtitle={config[role]?.subtitle || ""} />
        }
      </div>
    </div>
  );
}
