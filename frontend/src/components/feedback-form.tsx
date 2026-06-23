"use client";

import { useMutation } from "@tanstack/react-query";
import { MessageSquarePlus } from "lucide-react";
import { FormEvent, useState } from "react";
import { Button, Field, textareaClass } from "@/components/ui";

export function FeedbackForm({
  onSubmit,
  contextLabel,
}: {
  onSubmit: (rating: number, comment: string) => Promise<unknown>;
  contextLabel?: string;
}) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const mutation = useMutation({
    mutationFn: () => onSubmit(rating, comment.trim()),
    onSuccess: () => setComment(""),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={submit} className="grid gap-4">
      {contextLabel ? <p className="text-sm leading-6 text-muted">{contextLabel}</p> : null}
      <Field label="Rating">
        <select className="min-h-10 w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/15" value={rating} onChange={(event) => setRating(Number(event.target.value))}>
          {[5, 4, 3, 2, 1].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Comment">
        <textarea className={textareaClass} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="What worked, what was confusing, or what should be changed?" />
      </Field>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={mutation.isPending}>
          <MessageSquarePlus className="h-4 w-4" />
          {mutation.isPending ? "Submitting..." : "Submit feedback"}
        </Button>
        {mutation.isSuccess ? <span className="text-sm font-medium text-success">Feedback submitted.</span> : null}
        {mutation.error ? <span className="text-sm font-medium text-danger">{mutation.error instanceof Error ? mutation.error.message : "Feedback failed."}</span> : null}
      </div>
    </form>
  );
}
