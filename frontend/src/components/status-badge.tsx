import { Badge } from "./ui";

export function StatusBadge({ status }: { status: string }) {
  const success = ["APPROVED", "SHORTLISTED", "COMPLETED", "SCORED", "CRITERIA_GENERATED"];
  const warning = ["DRAFT", "NEEDS_REVIEW", "FINAL_REVIEW", "OTP_PENDING", "ACTIVE", "INTERVIEW_ACTIVE"];
  const danger = ["REJECTED", "REJECTED_FINAL", "EXPIRED", "CANCELLED"];
  const tone = success.includes(status) ? "success" : warning.includes(status) ? "warning" : danger.includes(status) ? "danger" : "neutral";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
