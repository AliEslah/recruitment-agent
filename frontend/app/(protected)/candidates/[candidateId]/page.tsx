"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ClipboardList, FileText, RefreshCcw } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { DecisionForm } from "@/components/decision-form";
import { CandidateScorePanel } from "@/components/result-panels";
import { StatusBadge } from "@/components/status-badge";
import { Badge, Button, EmptyState, ErrorState, JsonBlock, LoadingState, PageHeader, Panel } from "@/components/ui";
import { ApiError, api, isCandidateScore } from "@/lib/api";
import { compactId, formatDate } from "@/lib/format";
import type { HumanDecision, InterviewSessionSummary } from "@/lib/types";

export default function CandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const candidateId = String(params.candidateId);

  const candidateQuery = useQuery({ queryKey: ["candidate", candidateId], queryFn: () => api.getCandidate(candidateId) });
  const scoreQuery = useQuery({ queryKey: ["candidate-score", candidateId], queryFn: () => api.getLatestCandidateScore(candidateId) });
  const interviewsQuery = useQuery({ queryKey: ["candidate-interviews", candidateId], queryFn: () => api.listCandidateInterviews(candidateId) });
  const scoreUnavailable = scoreQuery.error instanceof ApiError && scoreQuery.error.status === 409;

  const processMutation = useMutation({
    mutationFn: (force: boolean) => api.processCandidate(candidateId, force),
    onSuccess: (result) => {
      if (isCandidateScore(result)) {
        queryClient.setQueryData(["candidate-score", candidateId], result);
      }
      void queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] });
      void queryClient.invalidateQueries({ queryKey: ["candidate-score", candidateId] });
    },
  });

  const decisionMutation = useMutation({
    mutationFn: ({ decision, reason }: { decision: HumanDecision; reason: string }) => api.shortlistDecision(candidateId, decision, reason),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] }),
  });

  const planMutation = useMutation({
    mutationFn: () => api.createInterviewPlan(candidateId),
    onSuccess: (session) => router.push(`/interviews/${session.id}/plan`),
  });

  const error =
    candidateQuery.error ||
    (!scoreUnavailable ? scoreQuery.error : null) ||
    interviewsQuery.error ||
    processMutation.error ||
    decisionMutation.error ||
    planMutation.error;

  if (candidateQuery.isLoading) {
    return <LoadingState label="Loading candidate" />;
  }

  if (candidateQuery.error || !candidateQuery.data) {
    return <ErrorState message={candidateQuery.error instanceof Error ? candidateQuery.error.message : "Could not load candidate."} />;
  }

  const candidate = candidateQuery.data;
  const processedScore = processMutation.data && isCandidateScore(processMutation.data) ? processMutation.data : null;
  const score = processedScore ?? scoreQuery.data;

  return (
    <>
      <PageHeader
        title={candidate.name || candidate.email || "Candidate"}
        description={`Candidate ID ${compactId(candidate.id)} · Created ${formatDate(candidate.created_at)}`}
        actions={
          <>
            <Link href={`/jobs/${candidate.job_id}`}><Button variant="secondary">Back to job</Button></Link>
            <Link href={`/candidates/${candidate.id}/final`}><Button variant="secondary"><FileText className="h-4 w-4" />Final scorecard</Button></Link>
          </>
        }
      />

      {error ? <div className="mb-5"><ErrorState message={error instanceof Error ? error.message : "Candidate action failed."} /></div> : null}

      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={candidate.status} />
            <span className="text-sm text-muted">{candidate.email || "No email"}</span>
            <span className="text-sm text-muted">{candidate.phone || "No phone"}</span>
          </div>
          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <ProfileSection title="Parsed profile" value={candidate.parsed_profile_json} />
            <ProfileSection title="Enriched profile" value={candidate.enriched_profile_json} />
          </div>
        </Panel>
        <Panel>
          <h2 className="text-lg font-semibold">Actions</h2>
          <div className="mt-4 grid gap-3">
            <Button type="button" disabled={processMutation.isPending} onClick={() => processMutation.mutate(false)}>
              <RefreshCcw className="h-4 w-4" />
              {processMutation.isPending ? "Processing..." : "Process Candidate"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={processMutation.isPending}
              onClick={() => window.confirm("Force rerun candidate processing?") && processMutation.mutate(true)}
            >
              Force process rerun
            </Button>
            <Button type="button" variant="secondary" disabled={planMutation.isPending || candidate.status !== "SHORTLISTED"} onClick={() => planMutation.mutate()}>
              <ClipboardList className="h-4 w-4" />
              {planMutation.isPending ? "Generating..." : "Generate interview plan"}
            </Button>
            {candidate.status !== "SHORTLISTED" ? <p className="text-xs leading-5 text-muted">Interview planning requires SHORTLISTED status and a generated score.</p> : null}
          </div>
        </Panel>
      </div>

      <div className="mt-6">
        {scoreQuery.isLoading ? (
          <LoadingState label="Loading latest score" />
        ) : score ? (
          <CandidateScorePanel score={score} />
        ) : (
          <EmptyState
            title="No score generated yet"
            body="Run Process Candidate to generate and display the latest persisted score returned by the backend."
          />
        )}
      </div>

      <Panel className="mt-6 overflow-hidden p-0">
        <div className="border-b border-line p-5">
          <h2 className="text-lg font-semibold">Interview sessions</h2>
          <p className="mt-1 text-sm text-muted">Generated interview plans and evaluations for this candidate.</p>
        </div>
        <InterviewSessionsTable interviews={interviewsQuery.data ?? []} loading={interviewsQuery.isLoading} />
      </Panel>

      <Panel className="mt-6">
        <h2 className="text-lg font-semibold">Shortlist decision</h2>
        <p className="mt-1 text-sm text-muted">Approve, reject, or hold. The backend requires a reason and records the authenticated user.</p>
        <div className="mt-4">
          <DecisionForm pending={decisionMutation.isPending} onSubmit={(decision, reason) => decisionMutation.mutate({ decision, reason })} />
        </div>
      </Panel>
    </>
  );
}

function InterviewSessionsTable({ interviews, loading }: { interviews: InterviewSessionSummary[]; loading: boolean }) {
  if (loading) {
    return <div className="p-5"><LoadingState label="Loading interviews" /></div>;
  }
  if (!interviews.length) {
    return <div className="p-5"><EmptyState title="No interviews created" body="Generate an interview plan after the candidate is shortlisted." /></div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b border-line bg-slate-50 text-xs uppercase text-muted">
          <tr>
            <th className="px-4 py-3">Session</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Questions</th>
            <th className="px-4 py-3">Evaluation</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {interviews.map((interview) => (
            <tr key={interview.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 font-semibold">{compactId(interview.id)}</td>
              <td className="px-4 py-3"><StatusBadge status={interview.status} /></td>
              <td className="px-4 py-3 text-muted">{interview.question_count}</td>
              <td className="px-4 py-3">
                <Badge tone={interview.evaluation_status === "EVALUATED" ? "success" : "neutral"}>
                  {interview.evaluation_status.replaceAll("_", " ")}
                </Badge>
              </td>
              <td className="px-4 py-3 text-muted">{formatDate(interview.created_at)}</td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <Link href={`/interviews/${interview.id}/plan`}>
                    <Button type="button" variant="secondary">
                      Plan
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href={`/interviews/${interview.id}/evaluation`}>
                    <Button type="button" variant="secondary">
                      Evaluation
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProfileSection({ title, value }: { title: string; value: Record<string, unknown> | null }) {
  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold">{title}</h2>
      {value ? <JsonBlock value={value} /> : <EmptyState title="Not available" body="This profile field has not been returned by the backend yet." />}
    </div>
  );
}
