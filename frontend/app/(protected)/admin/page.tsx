"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useCurrentUser } from "@/components/auth-shell";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, JsonBlock, LoadingState, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { compactId, formatDate } from "@/lib/format";

type Tab = "llm" | "audit" | "communications";

export default function AdminPage() {
  const user = useCurrentUser();
  const [tab, setTab] = useState<Tab>("llm");
  const isAdmin = user.role === "ADMIN";

  const llmQuery = useQuery({ queryKey: ["admin", "llm"], queryFn: () => api.adminLlmUsage(), enabled: isAdmin });
  const auditQuery = useQuery({ queryKey: ["admin", "audit"], queryFn: () => api.adminAudit(), enabled: isAdmin });
  const communicationsQuery = useQuery({ queryKey: ["admin", "communications"], queryFn: () => api.adminCommunications(), enabled: isAdmin });

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
        </div>
      </Panel>
      <div className="mt-6">
        {tab === "llm" ? <LlmUsage query={llmQuery} /> : null}
        {tab === "audit" ? <AuditLogs query={auditQuery} /> : null}
        {tab === "communications" ? <CommunicationLogs query={communicationsQuery} /> : null}
      </div>
    </>
  );
}

function LlmUsage({ query }: { query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof api.adminLlmUsage>>>> }) {
  if (query.isLoading) return <LoadingState label="Loading LLM usage" />;
  if (query.error) return <ErrorState message={query.error instanceof Error ? query.error.message : "Could not load LLM usage."} />;
  if (!query.data?.length) return <EmptyState title="No LLM usage logs" />;
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

function AuditLogs({ query }: { query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof api.adminAudit>>>> }) {
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

function CommunicationLogs({ query }: { query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof api.adminCommunications>>>> }) {
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
