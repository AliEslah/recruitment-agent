import type { User } from "./types";

const TOKEN_KEY = "recruitment-agent.access-token";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
}

export function redirectToLogin(): void {
  if (typeof window === "undefined") {
    return;
  }
  const next = window.location.pathname === "/login" ? "" : `?next=${encodeURIComponent(window.location.pathname)}`;
  window.location.assign(`/login${next}`);
}

export type AuthContextValue = {
  user: User;
  logout: () => void;
};
