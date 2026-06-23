"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { Button, ErrorState, Field, inputClass, Panel } from "./ui";

export function CandidateUpload({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) {
        throw new Error("Select a resume file first.");
      }
      return api.uploadResume(jobId, { name, email, phone, file });
    },
    onSuccess: (candidate) => {
      setMessage(`Uploaded ${candidate.name || candidate.email || candidate.id}.`);
      setName("");
      setEmail("");
      setPhone("");
      setFile(null);
      void queryClient.invalidateQueries({ queryKey: ["candidates", jobId] });
    },
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    setMessage(null);
    uploadMutation.mutate();
  };

  const error = uploadMutation.error instanceof ApiError || uploadMutation.error instanceof Error ? uploadMutation.error.message : null;

  return (
    <Panel>
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Upload candidate resume</h2>
        <p className="mt-1 text-sm text-muted">Creates a real backend candidate record and attaches the uploaded file.</p>
      </div>
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label="Name">
          <input className={inputClass} value={name} onChange={(event) => setName(event.target.value)} placeholder="Jane Candidate" />
        </Field>
        <Field label="Email">
          <input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="jane@example.com" />
        </Field>
        <Field label="Phone">
          <input className={inputClass} value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+1 555 0100" />
        </Field>
        <Field label="Resume file">
          <input
            className={inputClass}
            type="file"
            accept=".pdf,.txt,.doc,.docx"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </Field>
        <div className="md:col-span-2 flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={uploadMutation.isPending}>
            <Upload className="h-4 w-4" />
            {uploadMutation.isPending ? "Uploading..." : "Upload resume"}
          </Button>
          {message ? <span className="text-sm font-medium text-success">{message}</span> : null}
        </div>
        {error ? (
          <div className="md:col-span-2">
            <ErrorState message={error} />
          </div>
        ) : null}
      </form>
    </Panel>
  );
}
