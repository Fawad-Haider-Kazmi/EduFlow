"use client";
import { createContext, useContext, useState, ReactNode } from "react";
import { Role, DEMO_USER, USER_BY_ROLE, User } from "@/lib/auth";

interface AuthCtx { user: User; role: Role; setRole: (r: Role) => void }
const Ctx = createContext<AuthCtx>({ user: DEMO_USER, role: "class_teacher", setRole: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("class_teacher");
  const user = { ...USER_BY_ROLE[role], role };
  return <Ctx.Provider value={{ user, role, setRole }}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
