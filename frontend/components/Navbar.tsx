"use client";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ROLE_OPTIONS, Role } from "@/lib/auth";
import { ChevronDown, Bell } from "lucide-react";

export default function Navbar({ title }: { title: string }) {
  const { role, setRole } = useAuth();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const current = ROLE_OPTIONS.find(r => r.role === role);

  // Outside-click closes the dropdown
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <header style={{
      position: "fixed", top: 0, left: 240, right: 0, height: 64,
      background: "white", borderBottom: "1px solid #E2E8F0",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 32px", zIndex: 40,
    }}>
      <span style={{ fontSize: 16, fontWeight: 600, color: "var(--slate-900)" }}>{title}</span>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button className="btn btn-ghost btn-sm" style={{ color: "var(--slate-500)" }}>
          <Bell size={16} />
        </button>

        {/* Role switcher — single wrapper owns both trigger and dropdown */}
        <div ref={dropdownRef} style={{ position: "relative" }}>
          <button
            className="role-btn"
            onClick={() => setOpen(o => !o)}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <span>{current?.label || role}</span>
            <ChevronDown size={14} style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform .15s" }} />
          </button>

          {open && (
            <div style={{
              position: "absolute", top: "calc(100% + 6px)", right: 0, zIndex: 50,
              minWidth: 260, background: "white", borderRadius: 12,
              boxShadow: "0 8px 24px rgba(0,0,0,.12)", border: "1px solid #E2E8F0",
              overflow: "hidden",
            }}>
              {ROLE_OPTIONS.map(opt => (
                <div
                  key={opt.role}
                  className={`role-option ${opt.role === role ? "selected" : ""}`}
                  onClick={() => { setRole(opt.role as Role); setOpen(false); }}
                >
                  {opt.label}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
