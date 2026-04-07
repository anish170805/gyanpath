"use client";

import React, { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopNavBar } from "./components/TopNavBar";
import { ResourcePanel } from "./components/ResourcePanel";
import { BottomInputBar } from "./components/BottomInputBar";
import { ChatMessage } from "./components/ChatMessage";
import { LessonCard } from "./components/LessonCard";
import { QuizCard } from "./components/QuizCard";
import { Icon } from "./components/Icon";
import { useLearningSession } from "./hooks/useLearningSession";
import ReactMarkdown from "react-markdown";

// ─── small local helpers ────────────────────────────────────────────────────

/** Parse the first fenced code block out of a markdown string. */
function extractCodeSnippet(text: string): string | undefined {
  const m = text.match(/```(?:\w+)?\n([\s\S]*?)```/);
  return m ? m[1].trim() : undefined;
}

/** Strip fenced code blocks so they don't show up twice. */
function stripCodeBlocks(text: string): string {
  return text.replace(/```[\s\S]*?```/g, "").trim();
}

/** Extract KEY TAKEAWAYS section from a lesson string. */
function extractKeyTakeaway(text: string): string | undefined {
  const m = text.match(/KEY TAKEAWAYS?[:\s]+([\s\S]*?)(?:\n[A-Z ]+:|$)/i);
  return m ? m[1].replace(/^[-•\s]+/gm, "").trim().split("\n")[0] : undefined;
}

/** Extract tags from KEY POINTS section. */
function extractTags(text: string): string[] {
  const m = text.match(/KEY POINTS[:\s]+([\s\S]*?)(?:\n[A-Z ]+:|$)/i);
  if (!m) return [];
  return m[1]
    .split("\n")
    .map((l) => l.replace(/^[-•\s]+/, "").trim())
    .filter(Boolean)
    .slice(0, 3);
}

// ─── Loading overlay ────────────────────────────────────────────────────────

function LoadingOverlay({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-16 text-on-surface-variant">
      <img src="/GyanPath.jpeg" alt="GyanPath Logo" className="w-16 h-16 rounded-2xl object-cover shadow-lg border border-primary/20 animate-pulse" />
      <div className="flex flex-col items-center gap-2">
        <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-sm font-medium">{message || "Thinking…"}</p>
      </div>
    </div>
  );
}

// ─── Topic input screen ─────────────────────────────────────────────────────

function TopicScreen({ onStart }: { onStart: (t: string) => void }) {
  const [value, setValue] = useState("");
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 gap-8">
      <div className="text-center space-y-4 flex flex-col items-center">
        <img src="/GyanPath.jpeg" alt="GyanPath Logo" className="w-24 h-24 rounded-3xl object-cover shadow-2xl border-2 border-primary/20 mb-2" />
        <div>
          <h2 className="font-headline text-4xl font-bold text-primary tracking-tight">GyanPath</h2>
          <p className="text-on-surface-variant text-sm mt-1 uppercase tracking-widest font-semibold opacity-70">AI Learning Agent</p>
        </div>
      </div>
      <div className="w-full max-w-md flex flex-col gap-3">
        <input
          className="w-full bg-surface-container-high border border-outline-variant/20 rounded-xl px-5 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/40"
          placeholder="e.g. LangGraph, React Hooks, Machine Learning…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && value.trim() && onStart(value.trim())}
        />
        <button
          className="w-full py-3 rounded-xl bg-primary text-on-primary font-bold text-sm hover:brightness-110 transition-all disabled:opacity-40"
          disabled={!value.trim()}
          onClick={() => onStart(value.trim())}
        >
          Start Learning
        </button>
      </div>
    </div>
  );
}

// ─── Quiz answer section ─────────────────────────────────────────────────────

interface AnswerFormProps {
  questions: { question: string }[];
  answers: string[];
  onAnswerChange: (i: number, v: string) => void;
  onSubmit: () => void;
}

function AnswerForm({ questions, answers, onAnswerChange, onSubmit }: AnswerFormProps) {
  const allFilled = answers.every((a) => a.trim().length > 0);
  return (
    <div className="flex flex-col items-start gap-4 w-full">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-secondary/20 flex items-center justify-center text-secondary">
          <Icon name="quiz" className="text-lg" />
        </div>
        <span className="font-headline font-bold text-lg text-secondary">Knowledge Check</span>
      </div>
      <div className="w-full bg-surface-container-high rounded-xl p-6 border border-outline-variant/10 space-y-6">
        {questions.map((q, i) => (
          <div key={i} className="space-y-2">
            <p className="text-sm text-on-surface font-medium">Q{i + 1}: {q.question}</p>
            <textarea
              rows={3}
              className="w-full bg-surface-container-highest rounded-lg p-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 border border-outline-variant/10 focus:outline-none focus:ring-2 focus:ring-secondary/40 resize-none"
              placeholder="Type your answer here…"
              value={answers[i] ?? ""}
              onChange={(e) => onAnswerChange(i, e.target.value)}
            />
          </div>
        ))}
        <button
          className="w-full py-3 rounded-xl bg-secondary text-on-secondary font-bold text-sm hover:brightness-110 transition-all disabled:opacity-40"
          disabled={!allFilled}
          onClick={onSubmit}
        >
          Submit Answers
        </button>
      </div>
    </div>
  );
}

// ─── Quiz evaluation section ─────────────────────────────────────────────────

function EvaluationCard({
  score,
  total,
  feedback,
  onChallenge,
  onNext,
}: {
  score: number;
  total: number;
  feedback: string;
  onChallenge: () => void;
  onNext: () => void;
}) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  return (
    <div className="flex flex-col items-start gap-4 w-full">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-tertiary/20 flex items-center justify-center text-tertiary">
          <Icon name="analytics" className="text-lg" />
        </div>
        <span className="font-headline font-bold text-lg text-tertiary">Quiz Results</span>
      </div>
      <div className="w-full bg-surface-container rounded-xl p-6 border border-outline-variant/5 space-y-4">
        <div className="flex items-center gap-6">
          <div className="w-16 h-16 rounded-full border-4 border-secondary/40 flex items-center justify-center shrink-0">
            <span className="text-lg font-bold text-secondary">{pct}%</span>
          </div>
          <div>
            <h4 className="font-bold text-on-surface">
              {score}/{total} correct
            </h4>
            <p className="text-xs text-on-surface-variant mt-1">
              {pct >= 70 ? "Great work! Ready for a challenge?" : "Keep practising — you're improving!"}
            </p>
          </div>
        </div>
        <div className="bg-surface-container-high rounded-lg p-4 text-xs text-on-surface-variant whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
          {feedback}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onChallenge}
            className="flex-1 py-2.5 rounded-xl bg-secondary text-on-secondary font-bold text-sm hover:brightness-110 transition-all"
          >
            🏆 Accept Challenge
          </button>
          <button
            onClick={onNext}
            className="flex-1 py-2.5 rounded-xl border border-outline-variant/20 text-on-surface-variant font-bold text-sm hover:bg-surface-container-high transition-all"
          >
            Skip →
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Project brief section ────────────────────────────────────────────────────

function ProjectCard({
  brief,
  onNext,
}: {
  brief: string;
  onNext: () => void;
}) {
  return (
    <div className="flex flex-col items-start gap-4 w-full">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
          <Icon name="rocket_launch" className="text-lg" />
        </div>
        <span className="font-headline font-bold text-lg text-primary">Your Challenge Project</span>
      </div>
      <div className="w-full glass-panel rounded-xl p-6 border border-primary/10 space-y-4">
        <div className="text-sm text-on-surface leading-relaxed font-body prose prose-invert prose-primary max-w-none">
          <ReactMarkdown>
            {brief}
          </ReactMarkdown>
        </div>
        <button
          onClick={onNext}
          className="w-full py-3 rounded-xl bg-primary text-on-primary font-bold text-sm hover:brightness-110 transition-all flex items-center justify-center gap-2"
        >
          Continue Learning
          <Icon name="arrow_forward" className="text-lg" />
        </button>
      </div>
    </div>
  );
}

// ─── Roadmap Review section ──────────────────────────────────────────────────

function RoadmapReviewCard({
  roadmap,
  onAdd,
  onEdit,
  onDelete,
  onConfirm,
}: {
  roadmap: string[];
  onAdd: (task: string) => void;
  onEdit: (index: number, task: string) => void;
  onDelete: (index: number) => void;
  onConfirm: () => void;
}) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editText, setEditText] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [newTaskText, setNewTaskText] = useState("");
  const [deletingIndex, setDeletingIndex] = useState<number | null>(null);

  const handleEditStart = (index: number, task: string) => {
    setEditingIndex(index);
    setEditText(task);
    setDeletingIndex(null);
  };

  const handleEditSave = () => {
    if (editingIndex !== null && editText.trim()) {
      onEdit(editingIndex, editText.trim());
      setEditingIndex(null);
      setEditText("");
    }
  };

  const handleAddSave = () => {
    if (newTaskText.trim()) {
      onAdd(newTaskText.trim());
      setIsAdding(false);
      setNewTaskText("");
    }
  };

  return (
    <div className="flex flex-col items-start gap-4 w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary shadow-sm shadow-primary/10">
          <Icon name="list_alt" className="text-xl" />
        </div>
        <div>
          <span className="font-headline font-bold text-xl text-on-surface tracking-tight">Review Your Roadmap</span>
          <p className="text-xs text-on-surface-variant font-medium opacity-70">Customised learning path for you</p>
        </div>
      </div>
      
      <div className="w-full bg-surface-container/50 backdrop-blur-sm rounded-2xl border border-outline-variant/10 overflow-hidden shadow-xl">
        <div className="p-1">
          {roadmap.map((task, i) => (
            <div key={i} className="flex items-center justify-between p-3.5 border-b border-outline-variant/5 last:border-b-0 group hover:bg-surface-container-high/40 transition-colors rounded-xl mx-1 my-0.5">
              <div className="flex items-center gap-4 flex-1">
                <span className="w-7 h-7 rounded-lg bg-surface-container-highest flex items-center justify-center text-xs font-bold text-primary shrink-0 border border-outline-variant/10">
                  {i + 1}
                </span>
                
                {editingIndex === i ? (
                  <div className="flex-1 flex gap-2">
                    <input
                      autoFocus
                      className="flex-1 bg-surface-container-highest border border-primary/30 rounded-lg px-3 py-1.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40"
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleEditSave();
                        if (e.key === "Escape") setEditingIndex(null);
                      }}
                    />
                    <button onClick={handleEditSave} className="p-1.5 text-secondary hover:bg-secondary/10 rounded-lg transition-colors">
                      <Icon name="check" className="text-sm" />
                    </button>
                    <button onClick={() => setEditingIndex(null)} className="p-1.5 text-on-surface-variant hover:bg-surface-container-highest rounded-lg transition-colors">
                      <Icon name="close" className="text-sm" />
                    </button>
                  </div>
                ) : (
                  <span className="text-sm text-on-surface font-medium leading-relaxed">{task}</span>
                )}
              </div>

              {editingIndex !== i && (
                <div className="flex items-center gap-1.5 ml-2">
                  {deletingIndex === i ? (
                    <div className="flex items-center gap-2 bg-error/10 p-1 rounded-lg border border-error/20 animate-in fade-in zoom-in-95 duration-200">
                      <span className="text-[10px] font-bold text-error px-1 uppercase tracking-wider">Confirm?</span>
                      <button 
                        onClick={() => { onDelete(i); setDeletingIndex(null); }}
                        className="p-1 text-on-error-container bg-error/20 hover:bg-error/30 rounded-md transition-colors"
                        title="Yes, Delete"
                      >
                        <Icon name="check" className="text-xs" />
                      </button>
                      <button 
                        onClick={() => setDeletingIndex(null)}
                        className="p-1 text-on-surface-variant hover:bg-surface-container-highest rounded-md transition-colors"
                        title="Cancel"
                      >
                        <Icon name="close" className="text-xs" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                      <button 
                        onClick={() => handleEditStart(i, task)}
                        className="p-2 text-on-surface-variant hover:text-primary hover:bg-primary/10 rounded-full transition-all"
                        title="Edit Task"
                      >
                        <Icon name="edit" className="text-sm" />
                      </button>
                      <button 
                        onClick={() => { setDeletingIndex(i); setEditingIndex(null); }}
                        className="p-2 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-full transition-all"
                        title="Delete Task"
                      >
                        <Icon name="delete" className="text-sm" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {isAdding ? (
            <div className="p-3.5 mx-1 my-0.5 bg-primary/5 rounded-xl border border-primary/20 flex gap-3 items-center animate-in slide-in-from-top-2 duration-300">
              <span className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                +
              </span>
              <input
                autoFocus
                className="flex-1 bg-surface-container-highest border border-primary/30 rounded-lg px-3 py-1.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40"
                placeholder="Task description..."
                value={newTaskText}
                onChange={(e) => setNewTaskText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAddSave();
                  if (e.key === "Escape") setIsAdding(false);
                }}
              />
              <button 
                onClick={handleAddSave}
                disabled={!newTaskText.trim()}
                className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors disabled:opacity-30"
              >
                <Icon name="check" className="text-sm" />
              </button>
              <button 
                onClick={() => setIsAdding(false)}
                className="p-2 text-on-surface-variant hover:bg-surface-container-highest rounded-lg transition-colors"
              >
                <Icon name="close" className="text-sm" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setIsAdding(true); setEditingIndex(null); setDeletingIndex(null); }}
              className="w-full p-4 flex items-center justify-center gap-2 text-sm font-bold text-on-surface-variant hover:text-primary hover:bg-primary/5 transition-all group"
            >
              <div className="w-5 h-5 rounded-full border-2 border-dashed border-on-surface-variant/30 flex items-center justify-center group-hover:border-primary/50 transition-colors">
                <Icon name="add" className="text-xs" />
              </div>
              Add Another Topic
            </button>
          )}
        </div>
      </div>
      
      <div className="w-full flex flex-col sm:flex-row gap-4 mt-2">
        <button
          onClick={onConfirm}
          className="flex-1 py-4 rounded-2xl bg-primary text-on-primary font-bold text-base hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-primary/30 flex items-center justify-center gap-3 group"
        >
          Confirm & Start Learning
          <Icon name="rocket_launch" className="text-xl group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
        </button>
      </div>
    </div>
  );
}

// ─── Finished screen ─────────────────────────────────────────────────────────

function FinishedScreen({ topic }: { topic: string }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 gap-6 text-center">
      <div className="w-20 h-20 rounded-full bg-secondary/20 flex items-center justify-center">
        <Icon name="school" className="text-4xl text-secondary" />
      </div>
      <div>
        <h2 className="font-headline text-2xl font-bold text-secondary">Course Complete! 🎓</h2>
        <p className="text-on-surface-variant text-sm mt-2">
          You've finished the entire <span className="text-on-surface font-semibold">{topic}</span> curriculum.
        </p>
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [resourcePanelOpen, setResourcePanelOpen] = useState(true);

  const {
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
  } = useLearningSession();

  const { phase } = state;
  const showResources = ["lesson", "quiz", "evaluation", "project", "challenge"].includes(phase);

  // Build the scrollable chat-stream content based on current phase
  const renderMainContent = () => {
    if (phase === "idle") return null;

    if (phase === "loading") return <LoadingOverlay message={state.loadingMessage} />;

    if (phase === "error") {
      return (
        <div className="bg-error-container text-on-error-container rounded-xl p-5 text-sm">
          <strong>Something went wrong:</strong> {state.error}
        </div>
      );
    }

    if (phase === "finished") return <FinishedScreen topic={state.topic} />;

    if (phase === "roadmap") {
      return (
        <>
          <ChatMessage role="user" content={`I want to learn: ${state.topic}`} />
          <RoadmapReviewCard
            roadmap={state.roadmap}
            onAdd={(task) => modifyRoadmap("add", { task })}
            onEdit={(index, task) => modifyRoadmap("edit", { index, task })}
            onDelete={(index) => modifyRoadmap("delete", { index })}
            onConfirm={confirmRoadmap}
          />
        </>
      );
    }

    return (
      <>
        {/* User's topic bubble */}
        <ChatMessage role="user" content={`I want to learn: ${state.topic}`} />

        {/* Lesson — hide during project phase so the brief is the focus */}
        {state.lesson && phase !== "project" && (
          <LessonCard
            title={`Lesson: ${state.currentTask}`}
            tags={extractTags(state.lesson)}
            codeSnippet={extractCodeSnippet(state.lesson)}
            keyTakeaway={extractKeyTakeaway(state.lesson)}
            content={
              <ReactMarkdown>
                {stripCodeBlocks(state.lesson)}
              </ReactMarkdown>
            }
          />
        )}

        {/* Quiz answer form */}
        {phase === "quiz" && (
          <AnswerForm
            questions={state.quizQuestions}
            answers={state.quizAnswers}
            onAnswerChange={setAnswer}
            onSubmit={submitQuiz}
          />
        )}

        {/* Evaluation results */}
        {phase === "evaluation" && (
          <EvaluationCard
            score={state.quizScore}
            total={state.quizTotal}
            feedback={state.quizFeedback}
            onChallenge={() => resolveChallenge(true)}
            onNext={() => resolveChallenge(false).then(() => goNextLesson())}
          />
        )}

        {/* Challenge project brief */}
        {phase === "project" && state.projectBrief && (
          <ProjectCard brief={state.projectBrief} onNext={continueAfterProject} />
        )}
      </>
    );
  };

  return (
    <>
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        roadmap={state.roadmap}
        currentTaskIndex={state.currentTaskIndex}
        progressPct={state.progressPct}
        isFinished={phase === "finished"}
      />

      <main className={`lg:ml-64 ${showResources && resourcePanelOpen ? 'xl:mr-80' : ''} flex-1 flex flex-col h-full relative`}>
        <TopNavBar 
          onMenuClick={() => setSidebarOpen(!sidebarOpen)} 
          isResourcesOpen={resourcePanelOpen}
          onResourcesClick={() => setResourcePanelOpen(!resourcePanelOpen)}
          showResources={showResources}
        />

        <div className="flex-1 overflow-y-auto px-4 lg:px-8 pt-24 pb-48 lg:pb-32 space-y-8 max-w-4xl mx-auto w-full">
          {phase === "idle" ? (
            <TopicScreen onStart={startSession} />
          ) : (
            renderMainContent()
          )}
        </div>

        {/* Bottom action bar — only visible during lesson / quiz phases */}
        {(phase === "lesson" || phase === "quiz") && (
          <BottomInputBar
            onSendMessage={() => {}}
            onTakeQuiz={phase === "lesson" ? beginQuiz : undefined}
            onNextLesson={phase === "lesson" ? goNextLesson : undefined}
          />
        )}
      </main>

      {showResources && resourcePanelOpen && (
        <ResourcePanel resources={state.resources} taskTitle={state.currentTask} />
      )}
    </>
  );
}
