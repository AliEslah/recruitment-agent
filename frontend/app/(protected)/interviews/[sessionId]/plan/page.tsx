"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail, Save } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, Field, LoadingState, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { compactId, formatDate, safeJson } from "@/lib/format";
import type { InterviewPlan, QuestionType } from "@/lib/types";

const questionTypes: QuestionType[] = ["FIXED", "RESUME_VALIDATION", "SOFT_SKILL", "KNOCKOUT", "DYNAMIC"];

export default function InterviewPlanPage() {
  const params = useParams();
  const sessionId = String(params.sessionId);
  const queryClient = useQueryClient();
  const [planJson, setPlanJson] = useState("{}");

  const sessionQuery = useQuery({ queryKey: ["interview", sessionId], queryFn: () => api.getInterview(sessionId) });
  const planQuery = useQuery({ queryKey: ["interview-plan", sessionId], queryFn: () => api.getInterviewPlan(sessionId) });
  const candidateQuery = useQuery({
    queryKey: ["candidate", sessionQuery.data?.candidate_id],
    queryFn: () => api.getCandidate(sessionQuery.data?.candidate_id ?? ""),
    enabled: Boolean(sessionQuery.data?.candidate_id),
  });

  useEffect(() => {
    if (planQuery.data) {
      setPlanJson(safeJson(planQuery.data));
    }
  }, [planQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const parsed = JSON.parse(planJson) as InterviewPlan;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Interview plan JSON must be an object.");
      }
      return api.updateInterviewPlan(sessionId, parsed);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["interview-plan", sessionId] });
      void queryClient.invalidateQueries({ queryKey: ["interview", sessionId] });
    },
  });

  const inviteMutation = useMutation({ mutationFn: () => api.sendInterviewInvite(sessionId) });
  const questions = useMemo(() => planQuery.data?.questions ?? [], [planQuery.data]);
  const error = sessionQuery.error || planQuery.error || candidateQuery.error || saveMutation.error || inviteMutation.error;

  if (sessionQuery.isLoading || planQuery.isLoading) {
    return <LoadingState label="Loading interview plan" />;
  }

  if (sessionQuery.error || planQuery.error || !sessionQuery.data) {
    return <ErrorState message={error instanceof Error ? error.message : "Could not load interview plan."} />;
  }

  const session = sessionQuery.data;

  return (
    <>
      <PageHeader
        title="Interview plan"
        description={`Session ${compactId(session.id)} · Candidate ${compactId(session.candidate_id)}`}
        actions={
          <>
            <Link href={`/candidates/${session.candidate_id}`}><Button variant="secondary">Candidate</Button></Link>
            <Link href={`/interviews/${session.id}/evaluation`}><Button variant="secondary">Evaluation</Button></Link>
            <Button type="button" disabled={inviteMutation.isPending} onClick={() => inviteMutation.mutate()}>
              <Mail className="h-4 w-4" />
              {inviteMutation.isPending ? "Sending..." : "Send Invite"}
            </Button>
          </>
        }
      />
      {error ? <div className="mb-5"><ErrorState message={error instanceof Error ? error.message : "Interview action failed."} /></div> : null}
      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={session.status} />
            <span className="text-sm text-muted">Expires {formatDate(session.expires_at)}</span>
            <span className="text-sm text-muted">Candidate email: {candidateQuery.data?.email || "Not loaded"}</span>
          </div>
          {inviteMutation.data ? (
            <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-success">
              {inviteMutation.data.message} Expires {formatDate(inviteMutation.data.expires_at)}. Open Mailpit/local SMTP to retrieve the candidate email.
            </div>
          ) : null}
          <div className="mt-5 grid gap-5">
            {questionTypes.map((type) => {
              const typedQuestions = questions.filter((question) => question.type === type);
              return (
                <div key={type}>
                  <h2 className="mb-2 text-sm font-semibold">{type.replaceAll("_", " ")}</h2>
                  {typedQuestions.length ? (
                    <div className="grid gap-3">
                      {typedQuestions.map((question, index) => (
                        <div key={`${type}-${index}`} className="rounded-md border border-line bg-white p-4">
                          <p className="font-semibold">{question.question}</p>
                          <dl className="mt-3 grid gap-2 text-sm text-muted md:grid-cols-3">
                            <div><dt className="font-semibold text-foreground">Purpose</dt><dd>{question.purpose || "Not set"}</dd></div>
                            <div><dt className="font-semibold text-foreground">Weight</dt><dd>{question.weight ?? "Not set"}</dd></div>
                            <div><dt className="font-semibold text-foreground">Mandatory</dt><dd>{question.is_mandatory ? "Yes" : "No"}</dd></div>
                          </dl>
                          {question.evaluation_criteria ? <p className="mt-3 text-sm text-muted">{question.evaluation_criteria}</p> : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title={`No ${type.replaceAll("_", " ").toLowerCase()} questions`} />
                  )}
                </div>
              );
            })}
          </div>
        </Panel>
        <Panel>
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Plan JSON</h2>
            <Button type="button" variant="secondary" disabled={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
              <Save className="h-4 w-4" />
              Save
            </Button>
          </div>
          <Field label="Editable interview_plan_json">
            <textarea className="mt-3 min-h-[560px] w-full rounded-md border border-line bg-slate-950 px-3 py-2 font-mono text-xs leading-5 text-slate-100 outline-none focus:border-accent focus:ring-2 focus:ring-accent/15" value={planJson} onChange={(event) => setPlanJson(event.target.value)} />
          </Field>
        </Panel>
      </div>
    </>
  );
}
