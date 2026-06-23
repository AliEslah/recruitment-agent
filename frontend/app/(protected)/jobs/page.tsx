"use client";

import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function JobsPage() {
  const jobsQuery = useQuery({ queryKey: ["jobs"], queryFn: () => api.listJobs() });

  return (
    <>
      <PageHeader
        title="Jobs"
        description="Real jobs from the FastAPI backend."
        actions={
          <Link href="/jobs/new">
            <Button>
              <Plus className="h-4 w-4" />
              Create job
            </Button>
          </Link>
        }
      />
      {jobsQuery.isLoading ? <LoadingState label="Loading jobs" /> : null}
      {jobsQuery.error ? <ErrorState message={jobsQuery.error instanceof Error ? jobsQuery.error.message : "Could not load jobs."} /> : null}
      {jobsQuery.data?.length === 0 ? <EmptyState title="No jobs yet" body="Create a job to start the MVP flow." /> : null}
      {jobsQuery.data && jobsQuery.data.length > 0 ? (
        <Panel className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
                <tr>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Seniority</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {jobsQuery.data.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-semibold">
                      <Link className="text-accent hover:underline" href={`/jobs/${job.id}`}>
                        {job.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{job.department || "Not set"}</td>
                    <td className="px-4 py-3">{job.seniority || "Not set"}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-4 py-3 text-muted">{formatDate(job.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      ) : null}
    </>
  );
}
