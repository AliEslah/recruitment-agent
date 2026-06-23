"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { CandidateUpload } from "@/components/candidate-upload";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, Panel, inputClass } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate, formatPercent } from "@/lib/format";

export default function JobCandidatesPage() {
  const params = useParams();
  const jobId = String(params.jobId);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const candidatesQuery = useQuery({ queryKey: ["candidates", jobId], queryFn: () => api.listCandidates(jobId) });
  const processMutation = useMutation({
    mutationFn: (candidateId: string) => api.processCandidate(candidateId),
    onSuccess: () => void candidatesQuery.refetch(),
  });

  const statuses = useMemo(() => ["ALL", ...Array.from(new Set((candidatesQuery.data ?? []).map((candidate) => candidate.status)))], [candidatesQuery.data]);
  const candidates = useMemo(
    () => (candidatesQuery.data ?? []).filter((candidate) => statusFilter === "ALL" || candidate.status === statusFilter),
    [candidatesQuery.data, statusFilter],
  );

  return (
    <>
      <PageHeader title="Job candidates" description="Upload resumes, process candidates, and open candidate profiles." actions={<Link href={`/jobs/${jobId}`}><Button variant="secondary">Back to job</Button></Link>} />

      <CandidateUpload jobId={jobId} />

      <Panel className="mt-6 overflow-hidden p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-5">
          <div>
            <h2 className="text-lg font-semibold">Candidates</h2>
            <p className="mt-1 text-sm text-muted">Latest scores are read from persisted backend candidate score records.</p>
          </div>
          <select className={inputClass + " w-56"} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            {statuses.map((status) => (
              <option key={status} value={status}>{status.replaceAll("_", " ")}</option>
            ))}
          </select>
        </div>
        {candidatesQuery.isLoading ? <div className="p-5"><LoadingState label="Loading candidates" /></div> : null}
        {candidatesQuery.error ? <div className="p-5"><ErrorState message={candidatesQuery.error instanceof Error ? candidatesQuery.error.message : "Could not load candidates."} /></div> : null}
        {processMutation.error ? <div className="p-5"><ErrorState message={processMutation.error instanceof Error ? processMutation.error.message : "Could not process candidate."} /></div> : null}
        {candidates.length === 0 && !candidatesQuery.isLoading ? <div className="p-5"><EmptyState title="No candidates match this filter" /></div> : null}
        {candidates.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Recommendation</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {candidates.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-semibold">{candidate.name || "Unnamed"}</td>
                    <td className="px-4 py-3">{candidate.email || "Not set"}</td>
                    <td className="px-4 py-3"><StatusBadge status={candidate.status} /></td>
                    <td className="px-4 py-3 text-muted">{candidate.latest_score ? formatPercent(candidate.latest_score.overall_score) : "No score"}</td>
                    <td className="px-4 py-3 text-muted">{candidate.latest_score?.recommendation.replaceAll("_", " ") ?? "No score"}</td>
                    <td className="px-4 py-3 text-muted">{formatDate(candidate.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Link href={`/candidates/${candidate.id}`}><Button variant="secondary">View</Button></Link>
                        <Button type="button" variant="secondary" disabled={processMutation.isPending} onClick={() => processMutation.mutate(candidate.id)}>
                          Process candidate
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Panel>
    </>
  );
}
