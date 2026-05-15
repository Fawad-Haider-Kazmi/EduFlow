"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { NAV_BY_ROLE } from "@/lib/auth";

export function useRoleGuard() {
  const { role } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Build the allowed list from the role's own nav links
    const navAllowed = NAV_BY_ROLE[role].map(l => l.href);
    // Always allow dashboard and submission detail view for all roles
    const alwaysAllowed = ["/dashboard", "/submissions"];
    const allAllowed = [...new Set([...navAllowed, ...alwaysAllowed])];

    const isAllowed = allAllowed.some(
      p => pathname === p || pathname.startsWith(p + "/")
    );

    if (!isAllowed) {
      router.replace("/dashboard");
    }
  }, [role, pathname, router]);
}
