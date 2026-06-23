"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Save, WandSparkles } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CandidateUpload } from "@/components/candidate-upload";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, Field, JsonBlock, LoadingState, PageHeader, Panel, textareaClass } from "@/components/ui";
import { api } from "@/lib/api";
import { compactId, formatDate, formatPercent, safeJson } from "@/lib/format";

export default function JobDetailPage() {
  const params = useParams();
  const jobId = String(params.jobId);
  const queryClient = useQueryClient();
  const [criteriaJson, setCriteriaJson] = useState("[]");
  const [improvedJd, setImprovedJd] = useState("");

  const jobQuery = useQuery({ queryKey: ["job", jobId], queryFn: () => api.getJob(jobId) });
  const candidatesQuery = useQuery({ queryKey: ["candidates", jobId], queryFn: () => api.listCandidates(jobId) });

  useEffect(() => {
    if (jobQuery.data) {
      setCriteriaJson(safeJson(jobQuery.data.criteria_json ?? []));
      setImprovedJd(jobQuery.data.improved_jd ?? "");
    }
  }, [jobQuery.data]);

  const calibrateMutation = useMutation({
    mutationFn: () => api.calibrateJob(jobId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  const saveCriteriaMutation = useMutation({
    mutationFn: () => {
      const parsed = JSON.parse(criteriaJson) as unknown;
      if (!Array.isArray(parsed) || parsed.some((item) => !item || typeof item !== "object" || Array.isArray(item))) {
        throw new Error("Criteria JSON must be an array of objects.");
      }
      return api.updateJobCriteria(jobId, {
        improved_jd: improvedJd.trim() || null,
        criteria_json: parsed as Array<Record<string, unknown>>,
      });
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  const approveMutation = useMutation({
    mutationFn: () => api.approveCriteria(jobId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  const processMutation = useMutation({
    mutationFn: (candidateId: string) => api.processCandidate(candidateId),
    onSuccess: () => void candidatesQuery.refetch(),
  });

  const actionError = calibrateMutation.error || saveCriteriaMutation.error || approveMutation.error || processMutation.error;

  if (jobQuery.isLoading) {
    return <LoadingState label="Loading job" />;
  }

  if (jobQuery.error || !jobQuery.data) {
    return <ErrorState message={jobQuery.error instanceof Error ? jobQuery.error.message : "Could not load job."} />;
  }

  const job = jobQuery.data;

  return (
    <>
      <PageHeader
        title={job.title}
        description={`${job.department || "No department"} · ${job.seniority || "No seniority"} · Created ${formatDate(job.created_at)}`}
        actions={
          <>
            <Link href={`/jobs/${job.id}/candidates`}>
              <Button variant="secondary">Open candidates</Button>
            </Link>
            <Button type="button" variant="secondary" onClick={() => calibrateMutation.mutate()} disabled={calibrateMutation.isPending}>
              <WandSparkles className="h-4 w-4" />
              {calibrateMutation.isPending ? "Calibrating..." : "Run calibration"}
            </Button>
            <Button type="button" onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending}>
              <CheckCircle2 className="h-4 w-4" />
              Approve Criteria
            </Button>
          </>
        }
      />

      {actionError ? <div className="mb-5"><ErrorState message={actionError instanceof Error ? actionError.message : "Job action failed."} /></div> : null}

      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={job.status} />
            <span className="text-sm text-muted">Job ID {compactId(job.id)}</span>
          </div>
          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <TextSection title="Raw JD" value={job.raw_jd} />
            <div>
              <Field label="Improved JD">
                <textarea className={textareaClass} value={improvedJd} onChange={(event) => setImprovedJd(event.target.value)} />
              </Field>
            </div>
          </div>
        </Panel>

        <Panel>
          <h2 className="text-lg font-semibold">Job metadata</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <Meta label="Location" value={job.location} />
            <Meta label="Employment type" value={job.employment_type} />
            <Meta label="Salary range" value={job.salary_range} />
            <Meta label="Updated" value={formatDate(job.updated_at)} />
          </dl>
        </Panel>
      </div>

      <Panel className="mt-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Criteria</h2>
            <p className="mt-1 text-sm text-muted">Edit the criteria JSON if needed, then save before approval.</p>
          </div>
          <Button type="button" variant="secondary" onClick={() => saveCriteriaMutation.mutate()} disabled={saveCriteriaMutation.isPending}>
            <Save className="h-4 w-4" />
            Save Criteria JSON
          </Button>
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_420px]">
          <CriteriaTable criteria={job.criteria_json ?? []} />
          <Field label="Criteria JSON">
            <textarea className="min-h-[420px] w-full rounded-md border border-line bg-slate-950 px-3 py-2 font-mono text-xs leading-5 text-slate-100 outline-none focus:border-accent focus:ring-2 focus:ring-accent/15" value={criteriaJson} onChange={(event) => setCriteriaJson(event.target.value)} />
          </Field>
        </div>
      </Panel>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <ListPanel title="Must-haves" items={job.must_haves_json} />
        <ListPanel title="Nice-to-haves" items={job.nice_to_haves_json} />
        <ListPanel title="Disqualifiers" items={job.disqualifiers_json} />
        <ListPanel title="Soft skills" items={job.soft_skills_json} />
        <ListPanel title="Knockout areas" items={job.knockout_areas_json} />
      </div>

      <div className="mt-6">
        <CandidateUpload jobId={job.id} />
      </div>

      <Panel className="mt-6 overflow-hidden p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-5">
          <div>
            <h2 className="text-lg font-semibold">Candidates</h2>
            <p className="mt-1 text-sm text-muted">Latest scores are read from persisted backend candidate score records.</p>
          </div>
          <Link href={`/jobs/${job.id}/candidates`}>
            <Button variant="secondary">View full list</Button>
          </Link>
        </div>
        {candidatesQuery.isLoading ? <div className="p-5"><LoadingState label="Loading candidates" /></div> : null}
        {candidatesQuery.error ? <div className="p-5"><ErrorState message={candidatesQuery.error instanceof Error ? candidatesQuery.error.message : "Could not load candidates."} /></div> : null}
        {candidatesQuery.data?.length === 0 ? <div className="p-5"><EmptyState title="No candidates uploaded" /></div> : null}
        {candidatesQuery.data && candidatesQuery.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {candidatesQuery.data.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-semibold">{candidate.name || "Unnamed"}</td>
                    <td className="px-4 py-3">{candidate.email || "Not set"}</td>
                    <td className="px-4 py-3"><StatusBadge status={candidate.status} /></td>
                    <td className="px-4 py-3 text-muted">{candidate.latest_score ? formatPercent(candidate.latest_score.overall_score) : "No score"}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Link href={`/candidates/${candidate.id}`}><Button variant="secondary">View</Button></Link>
                        <Button type="button" variant="secondary" disabled={processMutation.isPending} onClick={() => processMutation.mutate(candidate.id)}>
                          Process
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

function TextSection({ title, value }: { title: string; value: string | null }) {
  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold">{title}</h2>
      <div className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-4 text-sm leading-6">{value || "Not generated yet."}</div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <dt className="text-xs font-semibold uppercase text-muted">{label}</dt>
      <dd className="mt-1 break-words font-medium">{value || "Not set"}</dd>
    </div>
  );
}

function CriteriaTable({ criteria }: { criteria: Array<Record<string, unknown>> }) {
  if (!criteria.length) {
    return <EmptyState title="No criteria generated yet" body="Run calibration to ask the backend to generate criteria." />;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
          <tr>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Description</th>
            <th className="px-4 py-3">Weight</th>
            <th className="px-4 py-3">Evidence guidance</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line bg-white">
          {criteria.map((item, index) => (
            <tr key={index}>
              <td className="px-4 py-3 font-semibold">{String(item.name ?? "Unnamed")}</td>
              <td className="px-4 py-3">{String(item.description ?? "")}</td>
              <td className="px-4 py-3">{String(item.weight ?? "")}</td>
              <td className="px-4 py-3">{String(item.evidence_guidance ?? "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ListPanel({ title, items }: { title: string; items: string[] | null }) {
  return (
    <Panel>
      <h2 className="text-lg font-semibold">{title}</h2>
      {items && items.length ? (
        <ul className="mt-3 grid gap-2 text-sm">
          {items.map((item, index) => (
            <li key={`${title}-${index}`} className="rounded-md border border-line bg-white px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-3"><JsonBlock value={items} /></div>
      )}
    </Panel>
  );
}
