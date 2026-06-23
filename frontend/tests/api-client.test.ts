import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError } from "../src/lib/api";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("ApiClient auth headers", () => {
  it("attaches bearer token to protected requests", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ ok: true })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.request("/api/v1/jobs");

    const [, init] = vi.mocked(fetcher).mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
  });

  it("does not attach bearer token to public requests", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ ok: true })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.request("/api/v1/interview-entry/raw-token", { auth: false });

    const [, init] = vi.mocked(fetcher).mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
  });

  it("does not attach bearer token through candidate interview methods", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ message: "ok" })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.sendOtp("raw-token");
    await client.verifyOtp("raw-token", "123456");
    await client.startInterview("raw-token");
    await client.answerInterview("raw-token", "Answer", "nonce-123");
    await client.completeInterview("raw-token", "nonce-123");
    await client.submitCandidateInterviewFeedback("raw-token", { rating: 5, comment: "Clear flow." });

    for (const [, init] of vi.mocked(fetcher).mock.calls) {
      const headers = init?.headers as Headers;
      expect(headers.get("Authorization")).toBeNull();
    }
  });

  it("sends client_session_nonce on answer and complete calls", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ message: "ok" })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.answerInterview("raw-token", "Answer", "nonce-123");
    await client.completeInterview("raw-token", "nonce-123");

    const answerInit = vi.mocked(fetcher).mock.calls[0][1];
    const completeInit = vi.mocked(fetcher).mock.calls[1][1];
    expect(JSON.parse(String(answerInit?.body))).toEqual({ answer: "Answer", client_session_nonce: "nonce-123" });
    expect(JSON.parse(String(completeInit?.body))).toEqual({ client_session_nonce: "nonce-123" });
  });

  it("uses force=true query params for evaluation and final scorecard reruns", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ ok: true })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.evaluateInterview("session-123", true);
    await client.createFinalScorecard("candidate-123", true);

    expect(vi.mocked(fetcher).mock.calls[0][0]).toBe("http://api.test/api/v1/interviews/session-123/evaluate?force=true");
    expect(vi.mocked(fetcher).mock.calls[1][0]).toBe("http://api.test/api/v1/candidates/candidate-123/final-scorecard?force=true");
  });

  it("calls latest score and interview discovery endpoints with auth", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ ok: true })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.getLatestCandidateScore("candidate-123");
    await client.listCandidateInterviews("candidate-123");
    await client.listJobInterviews("job-123");

    expect(vi.mocked(fetcher).mock.calls[0][0]).toBe("http://api.test/api/v1/candidates/candidate-123/score/latest");
    expect(vi.mocked(fetcher).mock.calls[1][0]).toBe("http://api.test/api/v1/candidates/candidate-123/interviews");
    expect(vi.mocked(fetcher).mock.calls[2][0]).toBe("http://api.test/api/v1/jobs/job-123/interviews");
    for (const [, init] of vi.mocked(fetcher).mock.calls) {
      const headers = init?.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer token-123");
    }
  });

  it("calls pilot template and feedback endpoints with the expected auth mode", async () => {
    const fetcher = vi.fn(async () => jsonResponse({ ok: true })) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "token-123",
    });

    await client.listRoleTemplates();
    await client.submitFeedback({ feedback_type: "GENERAL_FEEDBACK", rating: 4, comment: "Useful" });
    await client.adminFeedback();
    await client.adminPilotSummary();

    expect(vi.mocked(fetcher).mock.calls[0][0]).toBe("http://api.test/api/v1/templates/roles");
    expect(vi.mocked(fetcher).mock.calls[1][0]).toBe("http://api.test/api/v1/feedback");
    expect(vi.mocked(fetcher).mock.calls[2][0]).toBe("http://api.test/api/v1/admin/feedback");
    expect(vi.mocked(fetcher).mock.calls[3][0]).toBe("http://api.test/api/v1/admin/pilot-summary");
    for (const [, init] of vi.mocked(fetcher).mock.calls) {
      const headers = init?.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer token-123");
    }
  });

  it("raises ApiError and calls unauthorized handler on 401", async () => {
    const onUnauthorized = vi.fn();
    const fetcher = vi.fn(async () => jsonResponse({ detail: "Not authenticated" }, 401)) as unknown as typeof fetch;
    const client = new ApiClient({
      baseUrl: "http://api.test",
      fetcher,
      getToken: () => "expired",
      onUnauthorized,
    });

    await expect(client.request("/api/v1/jobs")).rejects.toBeInstanceOf(ApiError);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });
});
