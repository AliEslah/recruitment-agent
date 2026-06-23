import { AuthShell } from "@/components/auth-shell";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return <AuthShell>{children}</AuthShell>;
}
