import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("pilot UI content", () => {
  it("keeps the final scorecard advisory disclaimer visible", () => {
    const scorecardPanel = readFileSync(resolve(__dirname, "../src/components/result-panels.tsx"), "utf-8");

    expect(scorecardPanel).toContain("AI-generated recommendations are advisory");
    expect(scorecardPanel).toContain("qualified human reviewer");
  });

  it("uses browser print for scorecard export", () => {
    const finalPage = readFileSync(resolve(__dirname, "../app/(protected)/candidates/[candidateId]/final/page.tsx"), "utf-8");

    expect(finalPage).toContain("Print / Save as PDF");
    expect(finalPage).toContain("window.print()");
  });
});
