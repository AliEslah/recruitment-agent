"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { InterviewEvaluationPanel } from "@/components/result-panels";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, JsonBlock, LoadingState, PageHeader, Panel } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function InterviewEvaluationPage() {
  const params = useParams();
  const sessionId = String(params.sessionId);
  const queryClient = useQueryClient();

  const sessionQuery = useQuery({ queryKey: ["interview", sessionId], queryFn: () => api.getInterview(sessionId) });
  const transcriptQuery = useQuery({ queryKey: ["transcript", sessionId], queryFn: () => api.getTranscript(sessionId) });
  const evaluationQuery = useQuery({ queryKey: ["interview-evaluation", sessionId], queryFn: () => api.getInterviewEvaluation(sessionId) });
  const evaluationUnavailable = evaluationQuery.error instanceof ApiError && evaluationQuery.error.status === 409;

  const evaluateMutation = useMutation({
    mutationFn: (force: boolean) => api.evaluateInterview(sessionId, force),
    onSuccess: (evaluation) => queryClient.setQueryData(["interview-evaluation", sessionId], evaluation),
  });

  const error = sessionQuery.error || transcriptQuery.error || (!evaluationUnavailable ? evaluationQuery.error : null) || evaluateMutation.error;

  if (sessionQuery.isLoading || transcriptQuery.isLoading) {
    return <LoadingState label="Loading interview evaluation" />;
  }

  if (sessionQuery.error || transcriptQuery.error || !sessionQuery.data) {
    return <ErrorState message={error instanceof Error ? error.message : "Could not load interview."} />;
  }

  const evaluation = evaluateMutation.data ?? evaluationQuery.data;

  return (
    <>
      <PageHeader
        title="Interview evaluation"
        description={`Transcript and evaluation for session ${sessionId}`}
        actions={
          <>
            <Link href={`/interviews/${sessionId}/plan`}><Button variant="secondary">Plan</Button></Link>
            <Button type="button" disabled={evaluateMutation.isPending} onClick={() => evaluateMutation.mutate(false)}>
              <RefreshCcw className="h-4 w-4" />
              {evaluateMutation.isPending ? "Evaluating..." : "Evaluate Interview"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={evaluateMutation.isPending}
              onClick={() => window.confirm("Force rerun interview evaluation?") && evaluateMutation.mutate(true)}
            >
              Force rerun
            </Button>
          </>
        }
      />
      {error ? <div className="mb-5"><ErrorState message={error instanceof Error ? error.message : "Evaluation action failed."} /></div> : null}
      <Panel>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={sessionQuery.data.status} />
          <span className="text-sm text-muted">Started {formatDate(sessionQuery.data.started_at)}</span>
          <span className="text-sm text-muted">Ended {formatDate(sessionQuery.data.ended_at)}</span>
        </div>
      </Panel>

      <Panel className="mt-6">
        <h2 className="text-lg font-semibold">Transcript</h2>
        {transcriptQuery.data?.length ? (
          <div className="mt-4 grid gap-3">
            {transcriptQuery.data.map((message) => (
              <div key={message.id} className="rounded-md border border-line bg-white p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <StatusBadge status={message.role} />
                  {message.question_type ? <StatusBadge status={message.question_type} /> : null}
                  <span className="text-xs text-muted">{formatDate(message.created_at)}</span>
                </div>
                <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                {message.metadata_json ? <div className="mt-3"><JsonBlock value={message.metadata_json} /></div> : null}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No transcript messages yet" body="The candidate interview must be completed before evaluation has useful evidence." />
        )}
      </Panel>

      <div className="mt-6">
        {evaluation ? <InterviewEvaluationPanel evaluation={evaluation} /> : <EmptyState title="No evaluation generated yet" body="Run Evaluate Interview to create or load the backend evaluation." />}
      </div>
    </>
  );
}
