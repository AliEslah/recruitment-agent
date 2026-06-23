"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, BriefcaseBusiness, ClipboardList, Database, Server, Shield } from "lucide-react";
import Link from "next/link";
import { useCurrentUser } from "@/components/auth-shell";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const user = useCurrentUser();
  const backendHealth = useQuery({ queryKey: ["health"], queryFn: () => api.health("") });
  const dbHealth = useQuery({ queryKey: ["health", "db"], queryFn: () => api.health("/db") });
  const llmHealth = useQuery({ queryKey: ["health", "llm"], queryFn: () => api.health("/llm"), enabled: false });

  const cards = [
    { href: "/jobs", title: "Jobs", body: "Create roles, calibrate JD criteria, and review candidates.", icon: BriefcaseBusiness },
    { href: "/jobs", title: "Candidates", body: "Open a job to upload resumes and process candidate scoring.", icon: Activity },
    { href: "/interviews", title: "Interviews", body: "Open a known session to review plans, send invites, and evaluate transcripts.", icon: ClipboardList },
  ];

  return (
    <>
      <PageHeader title="Dashboard" description="Recruiter and hiring manager workspace for the MVP flow." />
      <div className="grid gap-5 lg:grid-cols-3">
        <Panel>
          <p className="text-sm font-semibold">Current user</p>
          <p className="mt-3 text-lg font-semibold">{user.name}</p>
          <p className="text-sm text-muted">{user.email}</p>
          <div className="mt-3">
            <StatusBadge status={user.role} />
          </div>
        </Panel>
        <HealthCard title="Backend" icon={<Server className="h-4 w-4" />} loading={backendHealth.isLoading} error={backendHealth.error} status={backendHealth.data?.status} />
        <HealthCard title="Database" icon={<Database className="h-4 w-4" />} loading={dbHealth.isLoading} error={dbHealth.error} status={dbHealth.data?.status} />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link key={card.title} href={card.href} className="rounded-lg border border-line bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:border-accent">
              <Icon className="h-5 w-5 text-accent" />
              <h2 className="mt-4 text-lg font-semibold">{card.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{card.body}</p>
            </Link>
          );
        })}
        {user.role === "ADMIN" ? (
          <Link href="/admin" className="rounded-lg border border-line bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:border-accent">
            <Shield className="h-5 w-5 text-accent" />
            <h2 className="mt-4 text-lg font-semibold">Admin logs</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Review LLM usage, audit records, and communication logs.</p>
          </Link>
        ) : null}
      </div>

      <div className="mt-6">
        <Panel>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">LLM health</h2>
              <p className="mt-1 text-sm text-muted">Manual check because it calls the local LM Studio server.</p>
            </div>
            <Button type="button" variant="secondary" onClick={() => void llmHealth.refetch()} disabled={llmHealth.isFetching}>
              Check LLM health
            </Button>
          </div>
          <div className="mt-4">
            {llmHealth.isFetching ? <EmptyState title="Checking LM Studio..." /> : null}
            {llmHealth.error ? <ErrorState message={llmHealth.error instanceof Error ? llmHealth.error.message : "LLM health check failed."} /> : null}
            {llmHealth.data ? <StatusBadge status={`${llmHealth.data.service}: ${llmHealth.data.status}`} /> : null}
          </div>
        </Panel>
      </div>
    </>
  );
}

function HealthCard({
  title,
  icon,
  loading,
  error,
  status,
}: {
  title: string;
  icon: React.ReactNode;
  loading: boolean;
  error: unknown;
  status?: string;
}) {
  return (
    <Panel>
      <div className="flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </div>
      <div className="mt-4">
        {loading ? <p className="text-sm text-muted">Checking...</p> : null}
        {error ? <ErrorState message={error instanceof Error ? error.message : "Health check failed."} /> : null}
        {status ? <StatusBadge status={status} /> : null}
      </div>
    </Panel>
  );
}
