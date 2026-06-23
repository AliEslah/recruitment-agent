"use client";

import { CheckCircle2, CirclePause, XCircle } from "lucide-react";
import { useState } from "react";
import type { HumanDecision } from "@/lib/types";
import { Button, Field, textareaClass } from "./ui";

export function DecisionForm({
  label = "Submit decision",
  pending,
  onSubmit,
}: {
  label?: string;
  pending?: boolean;
  onSubmit: (decision: HumanDecision, reason: string) => void;
}) {
  const [reason, setReason] = useState("");

  const submit = (decision: HumanDecision) => {
    onSubmit(decision, reason);
  };

  return (
    <div className="grid gap-3">
      <Field label="Decision reason">
        <textarea
          className={textareaClass}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Reason is required by the backend."
        />
      </Field>
      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={pending || !reason.trim()} onClick={() => submit("APPROVE")}>
          <CheckCircle2 className="h-4 w-4" />
          Approve
        </Button>
        <Button type="button" variant="danger" disabled={pending || !reason.trim()} onClick={() => submit("REJECT")}>
          <XCircle className="h-4 w-4" />
          Reject
        </Button>
        <Button type="button" variant="secondary" disabled={pending || !reason.trim()} onClick={() => submit("HOLD")}>
          <CirclePause className="h-4 w-4" />
          Hold
        </Button>
        <span className="self-center text-sm text-muted">{pending ? `${label}...` : null}</span>
      </div>
    </div>
  );
}
