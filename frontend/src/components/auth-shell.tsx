"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { BriefcaseBusiness, ClipboardList, LayoutDashboard, LogOut, Shield, UserRoundSearch } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { AuthContextValue } from "@/lib/auth";
import { LoadingState } from "./ui";

const AuthContext = createContext<AuthContextValue | null>(null);

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/interviews", label: "Interviews", icon: ClipboardList },
];

export function useCurrentUser() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useCurrentUser must be used inside AuthShell");
  }
  return value.user;
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState<boolean | null>(null);

  useEffect(() => {
    const tokenExists = Boolean(getToken());
    setHasToken(tokenExists);
    if (!tokenExists) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [pathname, router]);

  const userQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => api.me(),
    enabled: hasToken === true,
  });

  if (hasToken !== true || userQuery.isLoading) {
    return (
      <main className="min-h-screen bg-background p-6">
        <LoadingState label="Checking session" />
      </main>
    );
  }

  if (userQuery.isError || !userQuery.data) {
    return (
      <main className="min-h-screen bg-background p-6">
        <LoadingState label="Redirecting to login" />
      </main>
    );
  }

  const logout = () => {
    clearToken();
    queryClient.clear();
    router.replace("/login");
  };

  const user = userQuery.data;
  const visibleNav = user.role === "ADMIN" ? [...navItems, { href: "/admin", label: "Admin", icon: Shield }] : navItems;

  return (
    <AuthContext.Provider value={{ user, logout }}>
      <div className="min-h-screen bg-background text-foreground">
        <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
          <Link href="/" className="flex items-center gap-3 rounded-md px-2 py-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-accent text-white">
              <UserRoundSearch className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold">Recruitment Agent</p>
              <p className="text-xs text-muted">Frontend alpha</p>
            </div>
          </Link>
          <nav className="mt-8 grid gap-1">
            {visibleNav.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition",
                    active ? "bg-emerald-50 text-accent" : "text-muted hover:bg-slate-50 hover:text-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="lg:pl-64">
          <header className="sticky top-0 z-20 border-b border-line bg-white/95 px-5 py-3 backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{user.name}</p>
                <p className="truncate text-xs text-muted">
                  {user.email} · {user.role.replace("_", " ")}
                </p>
              </div>
              <button
                type="button"
                onClick={logout}
                className="inline-flex min-h-10 items-center gap-2 rounded-md border border-line px-3 text-sm font-semibold text-muted transition hover:bg-slate-50 hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
        </div>
      </div>
    </AuthContext.Provider>
  );
}
