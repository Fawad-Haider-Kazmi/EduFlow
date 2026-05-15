"use client";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/submissions": "Submissions",
  "/analytics": "Analytics",
  "/alerts": "Alerts",
  "/students": "Students",
  "/review": "Grade Review",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || (pathname.startsWith("/submissions/") ? "Submission Review" : "EduFlow");
  return (
    <div className="shell">
      <Sidebar />
      <div className="main-area">
        <Navbar title={title} />
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
