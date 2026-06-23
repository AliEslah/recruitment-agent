"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button, Field, inputClass, PageHeader, Panel } from "@/components/ui";

export default function InterviewsPage() {
  const [sessionId, setSessionId] = useState("");
  const trimmed = sessionId.trim();

  return (
    <>
      <PageHeader title="Interviews" description="Open interview sessions from candidate detail, or paste a known session ID." />
      <Panel>
        <div className="grid gap-4 md:grid-cols-[1fr_auto_auto] md:items-end">
          <Field label="Interview session ID">
            <input className={inputClass} value={sessionId} onChange={(event) => setSessionId(event.target.value)} placeholder="UUID from generated interview plan" />
          </Field>
          <Link aria-disabled={!trimmed} href={trimmed ? `/interviews/${trimmed}/plan` : "/interviews"}>
            <Button type="button" variant="secondary" disabled={!trimmed}>
              Plan
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link aria-disabled={!trimmed} href={trimmed ? `/interviews/${trimmed}/evaluation` : "/interviews"}>
            <Button type="button" disabled={!trimmed}>
              Evaluation
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </Panel>
    </>
  );
}
