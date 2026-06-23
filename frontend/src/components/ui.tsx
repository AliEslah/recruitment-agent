import clsx from "clsx";
import { AlertCircle, Loader2 } from "lucide-react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-accent text-white hover:bg-accentDark",
        variant === "secondary" && "border border-line bg-white text-foreground hover:bg-slate-50",
        variant === "danger" && "bg-danger text-white hover:bg-red-800",
        variant === "ghost" && "text-muted hover:bg-slate-100 hover:text-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "success" | "warning" | "danger" }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
        tone === "neutral" && "border-slate-200 bg-slate-50 text-slate-700",
        tone === "success" && "border-emerald-200 bg-emerald-50 text-success",
        tone === "warning" && "border-amber-200 bg-amber-50 text-warning",
        tone === "danger" && "border-red-200 bg-red-50 text-danger",
      )}
    >
      {children}
    </span>
  );
}

export function Panel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={clsx("rounded-lg border border-line bg-panel p-5 shadow-soft", className)}>{children}</section>;
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-foreground">{title}</h1>
        {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center gap-2 rounded-lg border border-dashed border-line bg-white text-sm text-muted">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white p-6 text-sm text-muted">
      <p className="font-semibold text-foreground">{title}</p>
      {body ? <p className="mt-1 leading-6">{body}</p> : null}
    </div>
  );
}

export function ErrorState({ title = "Request failed", message }: { title?: string; message: string }) {
  return (
    <div className="flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-danger">
      <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
      <div>
        <p className="font-semibold">{title}</p>
        <p className="mt-1">{message}</p>
      </div>
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="grid gap-1.5 text-sm font-medium text-foreground">
      <span>{label}</span>
      {children}
      {hint ? <span className="text-xs font-normal text-muted">{hint}</span> : null}
    </label>
  );
}

export const inputClass =
  "min-h-10 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-foreground outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-accent/15";

export const textareaClass =
  "min-h-28 w-full rounded-md border border-line bg-white px-3 py-2 text-sm leading-6 text-foreground outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-accent/15";

export function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-md border border-line bg-slate-950 p-4 text-xs leading-5 text-slate-100">
      {JSON.stringify(value ?? null, null, 2)}
    </pre>
  );
}
