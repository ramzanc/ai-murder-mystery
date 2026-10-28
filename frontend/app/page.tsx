"use client";

import { useCallback, useEffect, useState } from "react";

import { CaseDossier } from "@/components/CaseDossier";
import { SuspectPanel } from "@/components/SuspectPanel";
import { TheoryPanel } from "@/components/TheoryPanel";
import {
  ApiError,
  askQuestion,
  createSession,
  getCase,
  getEvidence,
  getReveal,
  getSession,
  submitTheory,
} from "@/lib/api";
import type {
  CaseReveal,
  InvestigationSession,
  PublicCase,
  PublicEvidence,
  QuestionTopic,
  TheoryDraft,
  TheoryScore,
} from "@/lib/types";

const CASE_ID = "case_ashcroft_study";
const SESSION_STORAGE_KEY = `daily-detective:${CASE_ID}:session`;

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

export default function HomePage() {
  const [caseData, setCaseData] = useState<PublicCase | null>(null);
  const [session, setSession] = useState<InvestigationSession | null>(null);
  const [evidence, setEvidence] = useState<PublicEvidence[]>([]);
  const [score, setScore] = useState<TheoryScore | null>(null);
  const [reveal, setReveal] = useState<CaseReveal | null>(null);
  const [revealUnavailable, setRevealUnavailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadReveal = useCallback(async (sessionId: string) => {
    try {
      const loadedReveal = await getReveal(sessionId);
      setReveal(loadedReveal);
      setRevealUnavailable(false);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) {
        setRevealUnavailable(true);
        return;
      }

      throw caught;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const loadedCase = await getCase(CASE_ID);
        if (cancelled) return;
        setCaseData(loadedCase);

        const storedSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);
        if (!storedSessionId) return;

        try {
          const [loadedSession, loadedEvidence] = await Promise.all([
            getSession(storedSessionId),
            getEvidence(storedSessionId),
          ]);

          if (loadedSession.case_id !== loadedCase.id) {
            throw new Error("Saved session belongs to a different case.");
          }

          if (cancelled) return;
          setSession(loadedSession);
          setEvidence(loadedEvidence);

          if (loadedSession.is_finalized) {
            await loadReveal(loadedSession.id);
          }
        } catch (resumeError) {
          if (cancelled) return;
          window.localStorage.removeItem(SESSION_STORAGE_KEY);
          setNotice(`Your saved investigation could not be resumed. ${getErrorMessage(resumeError)}`);
        }
      } catch (loadError) {
        if (!cancelled) setError(getErrorMessage(loadError));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [loadReveal]);

  async function handleStart() {
    setPendingAction("start");
    setError(null);
    setNotice(null);

    try {
      const newSession = await createSession(CASE_ID);
      const loadedEvidence = await getEvidence(newSession.id);
      window.localStorage.setItem(SESSION_STORAGE_KEY, newSession.id);
      setSession(newSession);
      setEvidence(loadedEvidence);
      setScore(null);
      setReveal(null);
      setRevealUnavailable(false);
    } catch (startError) {
      setError(getErrorMessage(startError));
    } finally {
      setPendingAction(null);
    }
  }

  async function handleQuestion(suspectId: string, topic: QuestionTopic) {
    if (!session) return;

    const action = `question:${suspectId}:${topic}`;
    setPendingAction(action);
    setError(null);

    try {
      const updatedSession = await askQuestion(session.id, suspectId, topic);
      const updatedEvidence = await getEvidence(session.id);
      setSession(updatedSession);
      setEvidence(updatedEvidence);
    } catch (questionError) {
      setError(getErrorMessage(questionError));
    } finally {
      setPendingAction(null);
    }
  }

  async function handleTheory(theory: TheoryDraft) {
    if (!session) return;

    setPendingAction("theory");
    setError(null);

    try {
      const submission = await submitTheory(session.id, theory);
      setSession(submission.session);
      setScore(submission.score);
      await loadReveal(session.id);
    } catch (theoryError) {
      setError(getErrorMessage(theoryError));
    } finally {
      setPendingAction(null);
    }
  }

  if (loading) {
    return (
      <main className="centered-state">
        <p className="eyebrow">Daily Detective</p>
        <h1>Opening case file…</h1>
      </main>
    );
  }

  if (!caseData) {
    return (
      <main className="centered-state">
        <p className="eyebrow">Connection error</p>
        <h1>Case file unavailable</h1>
        <p>{error ?? "The case could not be loaded."}</p>
        <button className="button button-primary" onClick={() => window.location.reload()} type="button">
          Try again
        </button>
      </main>
    );
  }

  if (!session) {
    return (
      <main className="start-page">
        <div className="start-card">
          <p className="eyebrow">Daily Detective · Case 001</p>
          <h1>{caseData.title}</h1>
          <p className="start-summary">{caseData.dossier.summary}</p>
          <dl className="start-facts">
            <div><dt>Location</dt><dd>{caseData.dossier.location}</dd></div>
            <div><dt>Time</dt><dd>{caseData.dossier.incident_time}</dd></div>
            <div><dt>Suspects</dt><dd>{caseData.suspects.length}</dd></div>
          </dl>
          {notice && <p className="notice" role="status">{notice}</p>}
          {error && <p className="error-message" role="alert">{error}</p>}
          <button className="button button-primary start-button" disabled={pendingAction === "start"} onClick={handleStart} type="button">
            {pendingAction === "start" ? "Starting investigation…" : "Start investigation"}
          </button>
          <p className="fine-print">Guest session. Progress is stored by the server and resumed on this browser.</p>
        </div>
      </main>
    );
  }

  return (
    <main>
      <header className="masthead">
        <div>
          <p className="brand">Daily Detective</p>
          <h1>{caseData.title}</h1>
        </div>
        <div className="session-status">
          <span className={session.is_finalized ? "status-dot finalized" : "status-dot"} />
          {session.is_finalized ? "Case closed" : "Investigation active"}
        </div>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button onClick={() => setError(null)} type="button">Dismiss</button>
        </div>
      )}

      <div className="case-layout">
        <CaseDossier caseData={caseData} evidence={evidence} />

        <div className="investigation-column">
          <section aria-labelledby="suspects-title">
            <div className="section-heading suspects-heading">
              <p className="eyebrow">Interviews</p>
              <h2 id="suspects-title">Suspects</h2>
              <p>Ask each suspect about the two supported topics. Answers are recorded in the official session.</p>
            </div>

            <div className="suspect-list">
              {caseData.suspects.map((suspect) => {
                const prefix = `question:${suspect.id}:`;
                const pendingForSuspect = pendingAction?.startsWith(prefix) ?? false;
                const topic = pendingForSuspect
                  ? (pendingAction?.slice(prefix.length) as QuestionTopic)
                  : null;

                return (
                  <SuspectPanel
                    disabled={Boolean(pendingAction) || session.is_finalized}
                    events={session.events.filter((event) => event.suspect_id === suspect.id)}
                    key={suspect.id}
                    onQuestion={handleQuestion}
                    pendingTopic={topic}
                    suspect={suspect}
                  />
                );
              })}
            </div>
          </section>

          <TheoryPanel
            caseData={caseData}
            evidence={evidence}
            finalized={session.is_finalized}
            officialScore={session.official_score}
            onRestart={handleStart}
            onSubmit={handleTheory}
            pending={Boolean(pendingAction)}
            reveal={reveal}
            revealUnavailable={revealUnavailable}
            score={score}
          />
        </div>
      </div>
    </main>
  );
}
