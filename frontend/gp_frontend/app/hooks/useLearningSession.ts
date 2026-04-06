/**
 * useLearningSession.ts
 *
 * Single source of truth for all learning-agent interactions.
 *
 * The hook owns every piece of UI-visible state and exposes one
 * action per user intent.  Components never call api.ts directly.
 *
 * State machine (mirrors the backend phases):
 *
 *   "idle"        → user hasn't typed a topic yet
 *   "loading"     → any network request in flight
 *   "lesson"      → lesson is displayed, waiting for quiz/next decision
 *   "quiz"        → questions shown, collecting answers
 *   "evaluation"  → quiz was submitted, showing score/feedback
 *   "challenge"   → "Ready for a challenge?" prompt visible
 *   "project"     → project brief is shown
 *   "finished"    → entire roadmap completed
 *   "error"       → something went wrong
 */

"use client";

import { useReducer, useCallback } from "react";
import * as api from "../lib/api";
import type {
  Resource,
  QuizQuestion,
  StartResponse,
  NextResponse,
  QuizStartResponse,
  QuizSubmitResponse,
  ChallengeResponse,
} from "../lib/api";

// ─── State shape ─────────────────────────────────────────────────────────────

export type UIPhase =
  | "idle"
  | "loading"
  | "roadmap"
  | "lesson"
  | "quiz"
  | "evaluation"
  | "challenge"
  | "project"
  | "finished"
  | "error";

export interface SessionState {
  phase: UIPhase;
  loadingMessage: string;

  // Session
  sessionId: string | null;
  topic: string;

  // Roadmap
  roadmap: string[];
  currentTaskIndex: number;
  totalTasks: number;
  progressPct: number;

  // Lesson
  currentTask: string;
  lesson: string;
  resources: Resource[];

  // Quiz
  quizQuestions: QuizQuestion[];
  quizText: string;
  quizAnswers: string[];          // one entry per question, built up as user types
  quizScore: number;
  quizTotal: number;
  quizFeedback: string;

  // Challenge / project
  projectBrief: string | null;
  isEndOfRoadmap: boolean;      // NEW: track if this was the last project

  // Error
  error: string | null;
}

const INITIAL_STATE: SessionState = {
  phase: "idle",
  loadingMessage: "",
  sessionId: null,
  topic: "",
  roadmap: [],
  currentTaskIndex: 0,
  totalTasks: 0,
  progressPct: 0,
  currentTask: "",
  lesson: "",
  resources: [],
  quizQuestions: [],
  quizText: "",
  quizAnswers: [],
  quizScore: 0,
  quizTotal: 0,
  quizFeedback: "",
  projectBrief: null,
  isEndOfRoadmap: false,
  error: null,
};

// ─── Reducer ─────────────────────────────────────────────────────────────────

type Action =
  | { type: "LOADING"; message: string }
  | { type: "ERROR"; error: string }
  | { type: "SESSION_STARTED"; data: StartResponse }
  | { type: "ROADMAP_UPDATED"; data: api.RoadmapEditResponse }
  | { type: "LESSON_LOADED_FROM_CONFIRM"; data: api.RoadmapEditResponse }
  | { type: "LESSON_LOADED"; data: NextResponse }
  | { type: "QUIZ_STARTED"; data: QuizStartResponse }
  | { type: "ANSWER_CHANGED"; index: number; value: string }
  | { type: "QUIZ_EVALUATED"; data: QuizSubmitResponse }
  | { type: "CHALLENGE_RESOLVED"; data: ChallengeResponse }
  | { type: "FINISHED"; data: api.NextResponse };

function reducer(state: SessionState, action: Action): SessionState {
  switch (action.type) {
    case "LOADING":
      return { ...state, phase: "loading", loadingMessage: action.message, error: null };

    case "ERROR":
      return { ...state, phase: "error", error: action.error };

    case "SESSION_STARTED":
      return {
        ...state,
        phase: "roadmap",
        sessionId: action.data.session_id,
        topic: action.data.topic,
        roadmap: action.data.roadmap,
        currentTask: action.data.current_task || "",
        currentTaskIndex: action.data.current_task_index || 0,
        totalTasks: action.data.total_tasks || 0,
        lesson: action.data.lesson || "",
        resources: action.data.resources || [],
        progressPct: action.data.progress_pct || 0,
        quizAnswers: [],
      };

    case "ROADMAP_UPDATED":
      return {
        ...state,
        phase: "roadmap",
        roadmap: action.data.roadmap,
      };

    case "LESSON_LOADED_FROM_CONFIRM":
      return {
        ...state,
        phase: "lesson",
        roadmap: action.data.roadmap,
        currentTask: action.data.current_task || "",
        currentTaskIndex: action.data.current_task_index || 0,
        totalTasks: action.data.total_tasks || 0,
        lesson: action.data.lesson || "",
        resources: action.data.resources || [],
        progressPct: action.data.progress_pct || 0,
        quizQuestions: [],
        quizAnswers: [],
        quizFeedback: "",
        projectBrief: null,
      };

    case "LESSON_LOADED":
      return {
        ...state,
        phase: action.data.finished ? "finished" : "lesson",
        currentTask: action.data.current_task,
        currentTaskIndex: action.data.current_task_index,
        totalTasks: action.data.total_tasks,
        lesson: action.data.lesson,
        resources: action.data.resources,
        progressPct: action.data.progress_pct,
        quizQuestions: [],
        quizAnswers: [],
        quizFeedback: "",
        projectBrief: null,
      };

    case "QUIZ_STARTED":
      return {
        ...state,
        phase: "quiz",
        quizQuestions: action.data.questions,
        quizText: action.data.quiz_text,
        quizAnswers: action.data.questions.map(() => ""),
      };

    case "ANSWER_CHANGED": {
      const updated = [...state.quizAnswers];
      updated[action.index] = action.value;
      return { ...state, quizAnswers: updated };
    }

    case "QUIZ_EVALUATED":
      return {
        ...state,
        phase: "evaluation",
        quizScore: action.data.score,
        quizTotal: action.data.total,
        quizFeedback: action.data.feedback,
      };

    case "CHALLENGE_RESOLVED":
      if (action.data.accepted && action.data.project) {
        // Show project brief; the next lesson data is already embedded in
        // the response — we store it now so "Continue Learning" is instant.
        return {
          ...state,
          phase: "project",
          projectBrief: action.data.project,
          // Pre-load next lesson (or finished flag) from this same response
          currentTask: action.data.current_task ?? state.currentTask,
          currentTaskIndex: action.data.current_task_index ?? state.currentTaskIndex,
          totalTasks: action.data.total_tasks ?? state.totalTasks,
          lesson: action.data.lesson ?? state.lesson,
          resources: action.data.resources ?? state.resources,
          progressPct: action.data.progress_pct ?? state.progressPct,
          isEndOfRoadmap: action.data.finished ?? false,
        };
      }
      // Declined — next lesson data is also in the response
      if (action.data.finished) {
        return {
          ...state,
          phase: "finished",
          progressPct: action.data.progress_pct ?? 100,
        };
      }
      return {
        ...state,
        phase: "lesson",
        currentTask: action.data.current_task ?? state.currentTask,
        currentTaskIndex: action.data.current_task_index ?? state.currentTaskIndex,
        totalTasks: action.data.total_tasks ?? state.totalTasks,
        lesson: action.data.lesson ?? state.lesson,
        resources: action.data.resources ?? state.resources,
        progressPct: action.data.progress_pct ?? state.progressPct,
        projectBrief: null,
      };

    case "FINISHED":
      return {
        ...state,
        phase: "finished",
        progressPct: action.data.progress_pct ?? 100,
      };

    default:
      return state;
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useLearningSession() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  // ── Start ──────────────────────────────────────────────────────────────────
  const startSession = useCallback(async (topic: string) => {
    dispatch({ type: "LOADING", message: "Building your personalised roadmap…" });
    try {
      const data = await api.startSession(topic);
      dispatch({ type: "SESSION_STARTED", data });
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, []);

  // ── Edit Roadmap ───────────────────────────────────────────────────────────
  const modifyRoadmap = useCallback(async (action: "add" | "delete" | "edit", opts?: { task?: string; index?: number }) => {
    if (!state.sessionId) return;
    dispatch({ type: "LOADING", message: "Updating roadmap…" });
    try {
      const data = await api.editRoadmap(state.sessionId, action, opts);
      dispatch({ type: "ROADMAP_UPDATED", data });
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId]);

  // ── Confirm Roadmap ────────────────────────────────────────────────────────
  const confirmRoadmap = useCallback(async () => {
    if (!state.sessionId) return;
    dispatch({ type: "LOADING", message: "Preparing your first lesson…" });
    try {
      const data = await api.editRoadmap(state.sessionId, "confirm");
      dispatch({ type: "LESSON_LOADED_FROM_CONFIRM", data });
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId]);

  // ── Next lesson (skip quiz) ────────────────────────────────────────────────
  const goNextLesson = useCallback(async () => {
    if (!state.sessionId) return;
    dispatch({ type: "LOADING", message: "Loading next lesson…" });
    try {
      const data = await api.nextLesson(state.sessionId);
      if (data.finished) {
        dispatch({ type: "FINISHED", data });
      } else {
        dispatch({ type: "LESSON_LOADED", data });
      }
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId]);

  // ── Start quiz ─────────────────────────────────────────────────────────────
  const beginQuiz = useCallback(async () => {
    if (!state.sessionId) return;
    dispatch({ type: "LOADING", message: "Generating quiz questions…" });
    try {
      const data = await api.startQuiz(state.sessionId);
      dispatch({ type: "QUIZ_STARTED", data });
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId]);

  // ── Update a single answer ─────────────────────────────────────────────────
  const setAnswer = useCallback((index: number, value: string) => {
    dispatch({ type: "ANSWER_CHANGED", index, value });
  }, []);

  // ── Submit quiz ────────────────────────────────────────────────────────────
  const submitQuiz = useCallback(async () => {
    if (!state.sessionId) return;
    dispatch({ type: "LOADING", message: "Evaluating your answers…" });
    try {
      const data = await api.submitQuiz(state.sessionId, state.quizAnswers);
      dispatch({ type: "QUIZ_EVALUATED", data });
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId, state.quizAnswers]);

  // ── Accept / decline challenge ─────────────────────────────────────────────
  const resolveChallenge = useCallback(async (accepted: boolean) => {
    if (!state.sessionId) return;
    dispatch({
      type: "LOADING",
      message: accepted ? "Generating your project brief…" : "Moving on…",
    });
    try {
      const data = await api.handleChallenge(state.sessionId, accepted);
      dispatch({ type: "CHALLENGE_RESOLVED", data });
      // If declined (or project shown), load next lesson on the next user action.
    } catch (e) {
      dispatch({ type: "ERROR", error: String(e) });
    }
  }, [state.sessionId]);

  // ── After project is shown, user clicks "Next Lesson" ─────────────────────
  // The next lesson was already pre-loaded into state during resolveChallenge,
  // so we just flip the phase — no extra network round-trip needed.
  const continueAfterProject = useCallback(() => {
    dispatch({ type: "LESSON_LOADED", data: {
      session_id: state.sessionId ?? "",
      current_task: state.currentTask,
      current_task_index: state.currentTaskIndex,
      total_tasks: state.totalTasks,
      lesson: state.lesson,
      resources: state.resources,
      progress_pct: state.progressPct,
      finished: state.isEndOfRoadmap,
    } });
  }, [state.sessionId, state.currentTask, state.currentTaskIndex, state.totalTasks, state.lesson, state.resources, state.progressPct, state.isEndOfRoadmap]);

  return {
    state,
    startSession,
    modifyRoadmap,
    confirmRoadmap,
    goNextLesson,
    beginQuiz,
    setAnswer,
    submitQuiz,
    resolveChallenge,
    continueAfterProject,
  };
}
