/**
 * api.ts — typed fetch wrappers for every GyanPath backend endpoint.
 *
 * All functions throw on non-2xx responses so callers can catch with
 * a single try/catch.  The error message is the raw text from the server.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// ─── generic helper ──────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── types that mirror the Pydantic schemas ───────────────────────────────────

export interface Resource {
  title: string;
  url: string;
  type: "docs" | "video" | "article";
  start_timestamp: string | null;
  end_timestamp: string | null;
  reason: string | null;
}

export interface StartResponse {
  session_id: string;
  topic: string;
  roadmap: string[];
  current_task: string;
  current_task_index: number;
  total_tasks: number;
  lesson: string | null;
  resources: Resource[] | null;
  progress_pct: number;
}

export interface RoadmapEditResponse {
  session_id: string;
  roadmap: string[];
  confirmed: boolean;
  current_task?: string;
  current_task_index?: number;
  total_tasks?: number;
  lesson?: string;
  resources?: Resource[];
  progress_pct?: number;
}

export interface NextResponse {
  session_id: string;
  current_task: string;
  current_task_index: number;
  total_tasks: number;
  lesson: string;
  resources: Resource[];
  progress_pct: number;
  finished: boolean;
}

export interface QuizQuestion {
  question: string;
}

export interface QuizStartResponse {
  session_id: string;
  task_title: string;
  questions: QuizQuestion[];
  quiz_text: string;
}

export interface QuizSubmitResponse {
  session_id: string;
  score: number;
  total: number;
  feedback: string;
  next_action: "challenge" | "next_lesson" | "finished";
}

export interface ChallengeResponse {
  session_id: string;
  accepted: boolean;
  project: string | null;
  finished: boolean;
  current_task: string | null;
  current_task_index: number | null;
  total_tasks: number | null;
  lesson: string | null;
  resources: Resource[] | null;
  progress_pct: number | null;
}

export interface ResourcesResponse {
  session_id: string;
  task_title: string;
  resources: Resource[];
}

export interface SessionStatusResponse {
  session_id: string;
  topic: string;
  current_task_index: number;
  total_tasks: number;
  roadmap: string[];
  progress_pct: number;
  finished: boolean;
  phase: "lesson" | "quiz" | "challenge" | "done";
}

// ─── endpoint wrappers ────────────────────────────────────────────────────────

/** Start a new session.  Returns roadmap + first lesson. */
export function startSession(topic: string) {
  return apiFetch<StartResponse>("/start", {
    method: "POST",
    body: JSON.stringify({ topic }),
  });
}

/** Edit the roadmap (add / delete / edit / confirm). */
export function editRoadmap(
  sessionId: string,
  action: "add" | "delete" | "edit" | "confirm",
  opts?: { task?: string; index?: number }
) {
  return apiFetch<RoadmapEditResponse>("/roadmap/edit", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, action, ...opts }),
  });
}

/** Skip quiz and move to the next lesson. */
export function nextLesson(sessionId: string) {
  return apiFetch<NextResponse>("/next", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/** Accept the quiz offer — returns questions (no correct answers). */
export function startQuiz(sessionId: string) {
  return apiFetch<QuizStartResponse>("/quiz/start", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/** Submit answers — returns score + per-question feedback. */
export function submitQuiz(sessionId: string, answers: string[]) {
  return apiFetch<QuizSubmitResponse>("/quiz/submit", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, answers }),
  });
}

/** Accept or decline the project challenge. */
export function handleChallenge(sessionId: string, accepted: boolean) {
  return apiFetch<ChallengeResponse>("/challenge", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, accepted }),
  });
}

/** Fetch resources for the current lesson. */
export function getResources(sessionId: string) {
  return apiFetch<ResourcesResponse>(`/resources/${sessionId}`);
}

/** Get lightweight session status (phase, progress, roadmap). */
export function getSessionStatus(sessionId: string) {
  return apiFetch<SessionStatusResponse>(`/session/${sessionId}`);
}
