"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useCurrentUser } from "@/components/auth-shell";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, JsonBlock, LoadingState, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { compactId, formatDate } from "@/lib/format";
import type { AuditLog, CommunicationLog, LlmCallLog, PilotDashboardSummary, PilotFeedback } from "@/lib/types";

type Tab = "pilot" | "llm" | "audit" | "communications" | "feedback";
type QueryLike<T> = {
  isLoading: boolean;
  error: unknown;
  data?: T | null;
};

export default function AdminPage() {
  const user = useCurrentUser();
  const [tab, setTab] = useState<Tab>("pilot");
  const isAdmin = user.role === "ADMIN";

  const llmQuery = useQuery({ queryKey: ["admin", "llm"], queryFn: () => api.adminLlmUsage(), enabled: isAdmin });
  const auditQuery = useQuery({ queryKey: ["admin", "audit"], queryFn: () => api.adminAudit(), enabled: isAdmin });
  const communicationsQuery = useQuery({ queryKey: ["admin", "communications"], queryFn: () => api.adminCommunications(), enabled: isAdmin });
  const feedbackQuery = useQuery({ queryKey: ["admin", "feedback"], queryFn: () => api.adminFeedback(), enabled: isAdmin });
  const pilotQuery = useQuery({ queryKey: ["admin", "pilot-summary"], queryFn: () => api.adminPilotSummary(), enabled: isAdmin });

  if (!isAdmin) {
    return (
      <>
        <PageHeader title="Admin" />
        <ErrorState title="Forbidden" message="This page is only available to ADMIN users." />
      </>
    );
  }

  return (
    <>
      <PageHeader title="Admin logs" description="Role-protected backend logs for LLM usage, audit events, and communications." />
      <Panel>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant={tab === "llm" ? "primary" : "secondary"} onClick={() => setTab("llm")}>LLM usage</Button>
          <Button type="button" variant={tab === "audit" ? "primary" : "secondary"} onClick={() => setTab("audit")}>Audit logs</Button>
          <Button type="button" variant={tab === "communications" ? "primary" : "secondary"} onClick={() => setTab("communications")}>Communication logs</Button>
          <Button type="button" variant={tab === "feedback" ? "primary" : "secondary"} onClick={() => setTab("feedback")}>Feedback</Button>
          <Button type="button" variant={tab === "pilot" ? "primary" : "secondary"} onClick={() => setTab("pilot")}>Pilot</Button>
        </div>
      </Panel>
      <div className="mt-6">
        {tab === "pilot" ? <PilotSummary query={pilotQuery} /> : null}
        {tab === "llm" ? <LlmUsage query={llmQuery} /> : null}
        {tab === "audit" ? <AuditLogs query={auditQuery} /> : null}
        {tab === "communications" ? <CommunicationLogs query={communicationsQuery} /> : null}
        {tab === "feedback" ? <FeedbackLogs query={feedbackQuery} /> : null}
      </div>
    </>
  );
}

function PilotSummary({ query }: { query: QueryLike<PilotDashboardSummary> }) {
  if (query.isLoading) return <LoadingState label="Loading pilot summary" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load pilot summary."} />;
  if (!query.data) return <EmptyState title="No pilot summary" />;
  return (
    <div className="grid gap-5">
      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard label="Jobs" value={query.data.jobs_count} />
        <MetricCard label="Candidates" value={query.data.candidates_count} />
        <MetricCard label="Completed interviews" value={query.data.interviews_completed_count} />
        <MetricCard label="Feedback" value={query.data.feedback_count} />
      </div>
      <FeedbackLogs query={{ ...query, data: query.data.recent_feedback }} />
      <LlmUsage query={{ ...query, data: query.data.recent_llm_failures }} emptyTitle="No recent LLM failures" />
      <AuditLogs query={{ ...query, data: query.data.recent_audit_events }} />
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Panel>
      <p className="text-sm font-semibold text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </Panel>
  );
}

function LlmUsage({ query, emptyTitle = "No LLM usage logs" }: { query: QueryLike<LlmCallLog[]>; emptyTitle?: string }) {
  if (query.isLoading) return <LoadingState label="Loading LLM usage" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load LLM usage."} />;
  if (!query.data?.length) return <EmptyState title={emptyTitle} />;
  return (
    <Panel className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-3">Task</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Cache</th>
              <th className="px-4 py-3">Tokens</th>
              <th className="px-4 py-3">Latency</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {query.data.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-semibold">{row.task}</td>
                <td className="px-4 py-3">{row.model || "Not set"}</td>
                <td className="px-4 py-3"><StatusBadge status={row.status} /></td>
                <td className="px-4 py-3">{row.cache_hit ? "Hit" : "Miss"}</td>
                <td className="px-4 py-3">{row.input_tokens ?? "-"} / {row.output_tokens ?? "-"}</td>
                <td className="px-4 py-3">{row.latency_ms}ms</td>
                <td className="px-4 py-3 text-muted">{formatDate(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function AuditLogs({ query }: { query: QueryLike<AuditLog[]> }) {
  if (query.isLoading) return <LoadingState label="Loading audit logs" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load audit logs."} />;
  if (!query.data?.length) return <EmptyState title="No audit logs" />;
  return (
    <Panel className="grid gap-3">
      {query.data.map((row) => (
        <div key={row.id} className="rounded-md border border-line bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={row.action} />
            <span className="text-sm text-muted">{row.entity_type} {compactId(row.entity_id)}</span>
            <span className="text-sm text-muted">{formatDate(row.created_at)}</span>
          </div>
          <div className="mt-3">
            <JsonBlock value={row.metadata_json} />
          </div>
        </div>
      ))}
    </Panel>
  );
}

function CommunicationLogs({ query }: { query: QueryLike<CommunicationLog[]> }) {
  if (query.isLoading) return <LoadingState label="Loading communication logs" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load communication logs."} />;
  if (!query.data?.length) return <EmptyState title="No communication logs" />;
  return (
    <Panel className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-3">Recipient</th>
              <th className="px-4 py-3">Subject</th>
              <th className="px-4 py-3">Body</th>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Channel</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {query.data.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-semibold">{row.recipient}</td>
                <td className="px-4 py-3 break-words">{row.subject}</td>
                <td className="max-w-xl px-4 py-3">
                  <p className="max-h-32 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-white p-3 text-xs leading-5">
                    {row.body}
                  </p>
                  {row.metadata_json ? <div className="mt-2"><JsonBlock value={row.metadata_json} /></div> : null}
                </td>
                <td className="px-4 py-3">{row.provider}</td>
                <td className="px-4 py-3">{row.channel}</td>
                <td className="px-4 py-3"><StatusBadge status={row.status} /></td>
                <td className="px-4 py-3 text-muted">{formatDate(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function FeedbackLogs({ query }: { query: QueryLike<PilotFeedback[]> }) {
  if (query.isLoading) return <LoadingState label="Loading feedback" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load feedback."} />;
  if (!query.data?.length) return <EmptyState title="No feedback" />;
  return (
    <Panel className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[920px] text-left text-sm">
          <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Rating</th>
              <th className="px-4 py-3">Comment</th>
              <th className="px-4 py-3">Context</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {query.data.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50">
                <td className="px-4 py-3"><StatusBadge status={row.feedback_type} /></td>
                <td className="px-4 py-3 font-semibold">{row.rating}/5</td>
                <td className="max-w-md px-4 py-3">
                  <p className="max-h-28 overflow-auto whitespace-pre-wrap break-words">{row.comment || "No comment"}</p>
                </td>
                <td className="px-4 py-3 text-muted">
                  {row.job_id ? <p>Job {compactId(row.job_id)}</p> : null}
                  {row.candidate_id ? <p>Candidate {compactId(row.candidate_id)}</p> : null}
                  {row.interview_session_id ? <p>Interview {compactId(row.interview_session_id)}</p> : null}
                </td>
                <td className="px-4 py-3 text-muted">{formatDate(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
