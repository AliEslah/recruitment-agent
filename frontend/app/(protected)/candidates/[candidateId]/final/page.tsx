"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DecisionForm } from "@/components/decision-form";
import { FinalScorecardPanel } from "@/components/result-panels";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, Panel } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import type { FinalScorecard, HumanDecision } from "@/lib/types";

function isFinalScorecard(value: FinalScorecard | { candidate_id: string; status: string }): value is FinalScorecard {
  return "overall_fit" in value;
}

export default function FinalScorecardPage() {
  const params = useParams();
  const candidateId = String(params.candidateId);
  const queryClient = useQueryClient();

  const candidateQuery = useQuery({ queryKey: ["candidate", candidateId], queryFn: () => api.getCandidate(candidateId) });
  const scorecardQuery = useQuery({ queryKey: ["final-scorecard", candidateId], queryFn: () => api.getFinalScorecard(candidateId) });
  const scorecardUnavailable = scorecardQuery.error instanceof ApiError && scorecardQuery.error.status === 409;

  const createMutation = useMutation({
    mutationFn: (force: boolean) => api.createFinalScorecard(candidateId, force),
    onSuccess: (scorecard) => queryClient.setQueryData(["final-scorecard", candidateId], scorecard),
  });

  const decisionMutation = useMutation({
    mutationFn: ({ decision, reason }: { decision: HumanDecision; reason: string }) => api.finalDecision(candidateId, decision, reason),
    onSuccess: (result) => {
      if (isFinalScorecard(result)) {
        queryClient.setQueryData(["final-scorecard", candidateId], result);
      }
      void queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] });
    },
  });

  const error = candidateQuery.error || (!scorecardUnavailable ? scorecardQuery.error : null) || createMutation.error || decisionMutation.error;

  if (candidateQuery.isLoading) {
    return <LoadingState label="Loading candidate" />;
  }

  if (candidateQuery.error || !candidateQuery.data) {
    return <ErrorState message={candidateQuery.error instanceof Error ? candidateQuery.error.message : "Could not load candidate."} />;
  }

  const scorecard = createMutation.data ?? scorecardQuery.data;

  return (
    <>
      <PageHeader
        title="Final scorecard"
        description={candidateQuery.data.name || candidateQuery.data.email || candidateQuery.data.id}
        actions={
          <>
            <Link href={`/candidates/${candidateId}`}><Button variant="secondary">Candidate</Button></Link>
            <Button type="button" disabled={createMutation.isPending} onClick={() => createMutation.mutate(false)}>
              <RefreshCcw className="h-4 w-4" />
              {createMutation.isPending ? "Generating..." : "Generate Final Scorecard"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={createMutation.isPending}
              onClick={() => window.confirm("Force rerun final scorecard?") && createMutation.mutate(true)}
            >
              Force rerun
            </Button>
          </>
        }
      />
      {error ? <div className="mb-5"><ErrorState message={error instanceof Error ? error.message : "Final scorecard action failed."} /></div> : null}
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={candidateQuery.data.status} />
          <span className="text-sm text-muted">{candidateQuery.data.email || "No email"}</span>
        </div>
      </Panel>

      <div className="mt-6">
        {scorecard ? <FinalScorecardPanel scorecard={scorecard} /> : <EmptyState title="No final scorecard generated yet" body="Generate a final scorecard after resume scoring and interview evaluation are available." />}
      </div>

      <Panel className="mt-6">
        <h2 className="text-lg font-semibold">Final human decision</h2>
        <p className="mt-1 text-sm text-muted">Approve, reject, or hold. The backend requires a reason and records the final decision stage.</p>
        <div className="mt-4">
          <DecisionForm pending={decisionMutation.isPending} label="Submitting final decision" onSubmit={(decision, reason) => decisionMutation.mutate({ decision, reason })} />
        </div>
      </Panel>
    </>
  );
}
