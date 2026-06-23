import type { CandidateScore, FinalScorecard, InterviewEvaluation } from "@/lib/types";
import { formatPercent } from "@/lib/format";
import { JsonBlock, Panel } from "./ui";

function StringList({ items }: { items: string[] }) {
  if (!items.length) {
    return <p className="text-sm text-muted">No items returned.</p>;
  }
  return (
    <ul className="grid gap-2 text-sm text-foreground">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="rounded-md border border-line bg-white px-3 py-2">
          {item}
        </li>
      ))}
    </ul>
  );
}

export function CandidateScorePanel({ score }: { score: CandidateScore }) {
  return (
    <Panel>
      <h2 className="text-lg font-semibold">Candidate score</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Metric label="Overall score" value={formatPercent(score.overall_score)} />
        <Metric label="Recommendation" value={score.recommendation.replaceAll("_", " ")} />
        <Metric label="Confidence" value={formatPercent(score.confidence)} />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Section title="Strengths">
          <StringList items={score.strengths_json} />
        </Section>
        <Section title="Weaknesses">
          <StringList items={score.weaknesses_json} />
        </Section>
        <Section title="Risks">
          <StringList items={score.risks_json} />
        </Section>
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Section title="Criteria score breakdown">
          <JsonBlock value={score.criteria_scores_json} />
        </Section>
        <Section title="Evidence">
          <JsonBlock value={score.evidence_json} />
        </Section>
      </div>
    </Panel>
  );
}

export function InterviewEvaluationPanel({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <Panel>
      <h2 className="text-lg font-semibold">Interview evaluation</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Metric label="Overall score" value={formatPercent(evaluation.overall_score)} />
        <Metric label="Recommendation" value={evaluation.recommendation} />
        <Metric label="Confidence" value={formatPercent(evaluation.confidence)} />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Section title="Strengths">
          <StringList items={evaluation.strengths_json} />
        </Section>
        <Section title="Weaknesses">
          <StringList items={evaluation.weaknesses_json} />
        </Section>
        <Section title="Red flags">
          <StringList items={evaluation.red_flags_json} />
        </Section>
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Section title="Competency scores">
          <JsonBlock value={evaluation.competency_scores_json} />
        </Section>
        <Section title="Soft skill scores">
          <JsonBlock value={evaluation.soft_skill_scores_json} />
        </Section>
        <Section title="Evidence">
          <JsonBlock value={evaluation.evidence_json} />
        </Section>
        <Section title="Missing evidence">
          <StringList items={evaluation.missing_evidence_json} />
        </Section>
      </div>
    </Panel>
  );
}

export function FinalScorecardPanel({ scorecard }: { scorecard: FinalScorecard }) {
  return (
    <Panel>
      <h2 className="text-lg font-semibold">Final scorecard</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-5">
        <Metric label="Resume" value={formatPercent(scorecard.resume_score)} />
        <Metric label="Interview" value={formatPercent(scorecard.interview_score)} />
        <Metric label="Soft skill" value={formatPercent(scorecard.soft_skill_score)} />
        <Metric label="Overall fit" value={formatPercent(scorecard.overall_fit)} />
        <Metric label="Risk level" value={scorecard.risk_level} />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Section title="Candidate fit narrative">
          <p className="rounded-md border border-line bg-white p-4 text-sm leading-6">{scorecard.candidate_fit_narrative}</p>
        </Section>
        <Section title="Recommendation">
          <p className="rounded-md border border-line bg-white p-4 text-sm leading-6">{scorecard.recommendation}</p>
        </Section>
        <Section title="Evidence summary">
          <JsonBlock value={scorecard.evidence_summary_json} />
        </Section>
        <Section title="Missing evidence">
          <StringList items={scorecard.missing_evidence_json} />
        </Section>
      </div>
      <p className="mt-4 text-sm text-muted">Confidence: {formatPercent(scorecard.confidence)}</p>
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-normal text-muted">{label}</p>
      <p className="mt-2 break-words text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-foreground">{title}</h3>
      {children}
    </div>
  );
}
