"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LogIn, UserRoundSearch } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Button, ErrorState, Field, inputClass, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { getToken, setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (getToken()) {
      router.replace("/");
    }
  }, [router]);

  const loginMutation = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: (response) => {
      setToken(response.access_token);
      queryClient.setQueryData(["me"], response.user);
      const next = new URLSearchParams(window.location.search).get("next") || "/";
      router.replace(next);
    },
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    loginMutation.mutate();
  };

  return (
    <main className="grid min-h-screen place-items-center bg-background px-5 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-accent text-white">
            <UserRoundSearch className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Recruitment Agent</h1>
            <p className="text-sm text-muted">Sign in to the recruiter workspace.</p>
          </div>
        </div>
        <Panel>
          <form onSubmit={onSubmit} className="grid gap-4">
            <Field label="Email">
              <input className={inputClass} type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
            </Field>
            <Field label="Password">
              <input className={inputClass} type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
            </Field>
            <Button type="submit" disabled={loginMutation.isPending}>
              <LogIn className="h-4 w-4" />
              {loginMutation.isPending ? "Signing in..." : "Login"}
            </Button>
            {loginMutation.error ? <ErrorState title="Login failed" message={loginMutation.error instanceof Error ? loginMutation.error.message : "Invalid login."} /> : null}
          </form>
        </Panel>
      </div>
    </main>
  );
}
