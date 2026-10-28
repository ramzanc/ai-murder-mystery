import type {
  CaseReveal,
  InvestigationSession,
  PublicCase,
  PublicEvidence,
  QuestionTopic,
  TheoryDraft,
  TheorySubmission,
} from "@/lib/types";

const API_ROOT = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/backend-api";

type FastApiDetail = string | Array<{ msg?: string }>;

interface FastApiErrorBody {
  detail?: FastApiDetail;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function errorMessage(body: FastApiErrorBody | null, fallback: string): string {
  if (typeof body?.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body?.detail)) {
    const messages = body.detail
      .map((item) => item.msg)
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as FastApiErrorBody | null;
    throw new ApiError(
      errorMessage(body, `Request failed with status ${response.status}.`),
      response.status,
    );
  }

  return (await response.json()) as T;
}

export function getCase(caseId: string): Promise<PublicCase> {
  return request<PublicCase>(`/cases/${encodeURIComponent(caseId)}`);
}

export function createSession(caseId: string): Promise<InvestigationSession> {
  return request<InvestigationSession>("/sessions", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId }),
  });
}

export function getSession(sessionId: string): Promise<InvestigationSession> {
  return request<InvestigationSession>(
    `/sessions/${encodeURIComponent(sessionId)}`,
  );
}

export function getEvidence(sessionId: string): Promise<PublicEvidence[]> {
  return request<PublicEvidence[]>(
    `/sessions/${encodeURIComponent(sessionId)}/evidence`,
  );
}

export function askQuestion(
  sessionId: string,
  suspectId: string,
  topic: QuestionTopic,
): Promise<InvestigationSession> {
  return request<InvestigationSession>(
    `/sessions/${encodeURIComponent(sessionId)}/questions`,
    {
      method: "POST",
      body: JSON.stringify({ suspect_id: suspectId, topic }),
    },
  );
}

export function submitTheory(
  sessionId: string,
  theory: TheoryDraft,
): Promise<TheorySubmission> {
  return request<TheorySubmission>(
    `/sessions/${encodeURIComponent(sessionId)}/theory`,
    {
      method: "POST",
      body: JSON.stringify(theory),
    },
  );
}

export function getReveal(sessionId: string): Promise<CaseReveal> {
  return request<CaseReveal>(
    `/sessions/${encodeURIComponent(sessionId)}/reveal`,
  );
}
