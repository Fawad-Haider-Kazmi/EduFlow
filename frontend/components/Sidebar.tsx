"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { NAV_BY_ROLE, getInitials } from "@/lib/auth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import {
  Home, FileText, CheckCircle, BookOpen, BarChart3, Target,
  AlertTriangle, Users, MessageSquare, TrendingUp, Building2,
  GraduationCap,
} from "lucide-react";

const ICON_MAP: Record<string, React.ReactNode> = {
  Home: <Home size={15} />, FileText: <FileText size={15} />, CheckCircle: <CheckCircle size={15} />,
  BookOpen: <BookOpen size={15} />, BarChart3: <BarChart3 size={15} />, Target: <Target size={15} />,
  AlertTriangle: <AlertTriangle size={15} />, Users: <Users size={15} />, MessageSquare: <MessageSquare size={15} />,
  TrendingUp: <TrendingUp size={15} />, Building2: <Building2 size={15} />,
};

export default function Sidebar() {
  const { user, role } = useAuth();
  const pathname = usePathname();
  const links = NAV_BY_ROLE[role];
  useRoleGuard(); // A2: redirects students away from teacher-only pages

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-dot"><GraduationCap size={18} color="white" /></div>
        <div>
          <div className="logo-text-main">EduFlow</div>
          <div className="logo-text-sub">Pakistan AI Platform</div>
        </div>
      </div>

      <div className="sidebar-section-label">Navigation</div>
      <nav>
        {links.map(l => (
          <Link
            key={l.href}
            href={l.href}
            className={`nav-link ${pathname === l.href || (l.href !== "/dashboard" && pathname.startsWith(l.href)) ? "active" : ""}`}
          >
            {ICON_MAP[l.icon] || <Home size={15} />}
            <span>{l.label}</span>
            {l.badge ? <span className="nav-badge">{l.badge}</span> : null}
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="avatar" style={{ width: 36, height: 36, fontSize: 13, fontWeight: 600 }}>{getInitials(user.name)}</div>
        <div>
          <div className="avatar-name">{user.name}</div>
          <div className="avatar-role">{user.class}</div>
        </div>
      </div>
    </aside>
  );
}
