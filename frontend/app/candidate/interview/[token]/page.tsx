"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Mail, Play, Send } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { FeedbackForm } from "@/components/feedback-form";
import { StatusBadge } from "@/components/status-badge";
import { Button, EmptyState, ErrorState, Field, LoadingState, PageHeader, Panel, inputClass, textareaClass } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { LiveInterviewTurn } from "@/lib/types";

export default function CandidateInterviewPage() {
  const params = useParams();
  const token = String(params.token);
  const nonceKey = `candidate-interview:${token}:nonce`;
  const turnKey = `candidate-interview:${token}:turn`;

  const [otp, setOtp] = useState("");
  const [answer, setAnswer] = useState("");
  const [nonce, setNonce] = useState("");
  const [turn, setTurn] = useState<LiveInterviewTurn | null>(null);
  const [completedMessage, setCompletedMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedNonce = window.sessionStorage.getItem(nonceKey);
    const storedTurn = window.sessionStorage.getItem(turnKey);
    if (storedNonce) {
      setNonce(storedNonce);
    }
    if (storedTurn) {
      try {
        setTurn(JSON.parse(storedTurn) as LiveInterviewTurn);
      } catch {
        window.sessionStorage.removeItem(turnKey);
      }
    }
  }, [nonceKey, turnKey]);

  const entryQuery = useQuery({ queryKey: ["interview-entry", token], queryFn: () => api.interviewEntry(token) });
  const sendOtpMutation = useMutation({ mutationFn: () => api.sendOtp(token), onSuccess: () => void entryQuery.refetch() });
  const verifyOtpMutation = useMutation({ mutationFn: () => api.verifyOtp(token, otp), onSuccess: () => void entryQuery.refetch() });
  const completeMutation = useMutation({
    mutationFn: (clientNonce: string) => api.completeInterview(token, clientNonce),
    onSuccess: (response) => {
      setCompletedMessage(response.message);
      window.sessionStorage.removeItem(nonceKey);
      window.sessionStorage.removeItem(turnKey);
    },
  });

  const applyTurn = (nextTurn: LiveInterviewTurn) => {
    setTurn(nextTurn);
    window.sessionStorage.setItem(turnKey, JSON.stringify(nextTurn));
    if (nextTurn.client_session_nonce) {
      setNonce(nextTurn.client_session_nonce);
      window.sessionStorage.setItem(nonceKey, nextTurn.client_session_nonce);
    }
    if (nextTurn.completed || nextTurn.status === "COMPLETED") {
      setCompletedMessage("Interview completed.");
      if (nonce || nextTurn.client_session_nonce) {
        completeMutation.mutate(nextTurn.client_session_nonce || nonce);
      }
    }
  };

  const startMutation = useMutation({
    mutationFn: () => api.startInterview(token),
    onSuccess: applyTurn,
  });

  const answerMutation = useMutation({
    mutationFn: () => api.answerInterview(token, answer, nonce),
    onSuccess: (response) => {
      setAnswer("");
      applyTurn(response);
    },
  });

  const error =
    entryQuery.error ||
    sendOtpMutation.error ||
    verifyOtpMutation.error ||
    startMutation.error ||
    answerMutation.error ||
    completeMutation.error;

  if (entryQuery.isLoading) {
    return (
      <main className="min-h-screen bg-background px-5 py-8">
        <LoadingState label="Loading interview entry" />
      </main>
    );
  }

  if (entryQuery.error || !entryQuery.data) {
    return (
      <main className="min-h-screen bg-background px-5 py-8">
        <div className="mx-auto max-w-3xl">
          <ErrorState
            title="Interview unavailable"
            message={entryQuery.error instanceof Error ? entryQuery.error.message : "This token may be invalid, expired, or completed."}
          />
        </div>
      </main>
    );
  }

  const entry = entryQuery.data;
  const otpVerified = entry.otp_verified || verifyOtpMutation.isSuccess;
  const isCompleted = completedMessage || turn?.completed || turn?.status === "COMPLETED" || entry.status === "COMPLETED";
  const activeWithoutRestoredTurn = otpVerified && entry.status === "ACTIVE" && !turn && !isCompleted;

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <div className="mx-auto max-w-3xl">
        <PageHeader title="Candidate interview" description="Complete the interview in this browser session. Your OTP is sent through the local email flow." />
        {error ? <div className="mb-5"><ErrorState message={error instanceof Error ? error.message : "Interview action failed."} /></div> : null}
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={entry.status} />
            <span className="text-sm text-muted">Expires {formatDate(entry.expires_at)}</span>
          </div>
          <div className="mt-5 rounded-md border border-line bg-white p-4 text-sm leading-6 text-muted">
            Read each question and answer in writing. Keep this tab open after starting because the backend returns a one-time client session nonce for this browser session.
          </div>
        </Panel>

        {!otpVerified ? (
          <Panel className="mt-6">
            <h2 className="text-lg font-semibold">Verify OTP</h2>
            <p className="mt-1 text-sm text-muted">Send the OTP, then copy it from Mailpit/local SMTP into this form.</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button type="button" variant="secondary" disabled={sendOtpMutation.isPending} onClick={() => sendOtpMutation.mutate()}>
                <Mail className="h-4 w-4" />
                {sendOtpMutation.isPending ? "Sending..." : "Send OTP"}
              </Button>
              {sendOtpMutation.data ? <span className="self-center text-sm font-medium text-success">{sendOtpMutation.data.message}</span> : null}
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
              <Field label="OTP">
                <input className={inputClass} value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" />
              </Field>
              <Button type="button" disabled={verifyOtpMutation.isPending || !otp.trim()} onClick={() => verifyOtpMutation.mutate()}>
                <CheckCircle2 className="h-4 w-4" />
                Verify OTP
              </Button>
            </div>
          </Panel>
        ) : null}

        {otpVerified && !turn && !activeWithoutRestoredTurn && !isCompleted ? (
          <Panel className="mt-6">
            <h2 className="text-lg font-semibold">Start interview</h2>
            <p className="mt-1 text-sm text-muted">Starting locks this interview to the current browser session.</p>
            <Button className="mt-4" type="button" disabled={startMutation.isPending} onClick={() => startMutation.mutate()}>
              <Play className="h-4 w-4" />
              {startMutation.isPending ? "Starting..." : "Start interview"}
            </Button>
          </Panel>
        ) : null}

        {activeWithoutRestoredTurn ? (
          <Panel className="mt-6">
            <h2 className="text-lg font-semibold">Interview session already active</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              This interview has already been started, but this tab could not restore the current question. Return to the original tab if it is still open.
              If the browser session was lost, contact the recruiter for a new invite.
            </p>
          </Panel>
        ) : null}

        {turn && !isCompleted ? (
          <Panel className="mt-6">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge status={turn.status} />
              <span className="text-sm text-muted">Question {turn.current_question_index}</span>
            </div>
            {turn.message ? (
              <div className="mt-5 rounded-md border border-line bg-white p-5 text-lg font-semibold leading-7">{turn.message}</div>
            ) : (
              <EmptyState title="No next question returned" body="The backend did not return another question. Submit completion if the interview is finished." />
            )}
            <div className="mt-5 grid gap-4">
              <Field label="Your answer">
                <textarea className={textareaClass} value={answer} onChange={(event) => setAnswer(event.target.value)} />
              </Field>
              <Button type="button" disabled={answerMutation.isPending || !answer.trim() || !nonce} onClick={() => answerMutation.mutate()}>
                <Send className="h-4 w-4" />
                {answerMutation.isPending ? "Submitting..." : "Submit answer"}
              </Button>
            </div>
          </Panel>
        ) : null}

        {isCompleted ? (
          <Panel className="mt-6">
            <CheckCircle2 className="h-8 w-8 text-success" />
            <h2 className="mt-4 text-lg font-semibold">Interview completed</h2>
            <p className="mt-1 text-sm text-muted">{completedMessage || "Your interview has been completed. Thank you."}</p>
            <div className="mt-5 border-t border-line pt-5">
              <FeedbackForm
                contextLabel="Rate the interview experience. This feedback is linked only to this interview session."
                onSubmit={(rating, comment) => api.submitCandidateInterviewFeedback(token, { rating, comment: comment || null })}
              />
            </div>
          </Panel>
        ) : null}
      </div>
    </main>
  );
}
