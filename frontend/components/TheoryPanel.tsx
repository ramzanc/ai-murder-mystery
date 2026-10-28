"use client";

import { FormEvent, useState } from "react";

import type {
  CaseReveal,
  PublicCase,
  PublicEvidence,
  TheoryDraft,
  TheoryScore,
} from "@/lib/types";

interface TheoryPanelProps {
  caseData: PublicCase;
  evidence: PublicEvidence[];
  finalized: boolean;
  officialScore: number | null;
  score: TheoryScore | null;
  reveal: CaseReveal | null;
  revealUnavailable: boolean;
  pending: boolean;
  onSubmit: (theory: TheoryDraft) => Promise<void>;
  onRestart: () => Promise<void>;
}

function ResultMark({ correct }: { correct: boolean }) {
  return <span className={correct ? "result-correct" : "result-wrong"}>{correct ? "Correct" : "Incorrect"}</span>;
}

export function TheoryPanel({
  caseData,
  evidence,
  finalized,
  officialScore,
  score,
  reveal,
  revealUnavailable,
  pending,
  onSubmit,
  onRestart,
}: TheoryPanelProps) {
  const [killerId, setKillerId] = useState("");
  const [motive, setMotive] = useState("");
  const [method, setMethod] = useState("");
  const [evidenceIds, setEvidenceIds] = useState<string[]>([]);

  function toggleEvidence(evidenceId: string) {
    setEvidenceIds((current) => {
      if (current.includes(evidenceId)) {
        return current.filter((id) => id !== evidenceId);
      }

      if (current.length === 3) {
        return current;
      }

      return [...current, evidenceId];
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      killer_id: killerId,
      motive,
      method,
      evidence_ids: evidenceIds,
    });
  }

  if (finalized) {
    const solved = score?.solved ?? officialScore === 100;

    return (
      <section className="theory-panel result-panel" aria-labelledby="result-title">
        <p className="eyebrow">Official result</p>
        <div className="result-heading">
          <h2 id="result-title">{solved ? "Case solved" : "Accusation recorded"}</h2>
          <strong>{score?.total_points ?? officialScore ?? 0} / 100</strong>
        </div>

        {score && (
          <dl className="score-breakdown">
            <div>
              <dt>Killer</dt>
              <dd><ResultMark correct={score.killer_correct} /> · {score.killer_points} pts</dd>
            </div>
            <div>
              <dt>Motive</dt>
              <dd><ResultMark correct={score.motive_correct} /> · {score.motive_points} pts</dd>
            </div>
            <div>
              <dt>Method</dt>
              <dd><ResultMark correct={score.method_correct} /> · {score.method_points} pts</dd>
            </div>
            <div>
              <dt>Evidence</dt>
              <dd>{score.matching_evidence_ids.length} matched · {score.evidence_points} pts</dd>
            </div>
          </dl>
        )}

        {reveal && (
          <div className="reveal" aria-labelledby="reveal-title">
            <p className="eyebrow">Canonical reconstruction</p>
            <h3 id="reveal-title">{reveal.killer_name}</h3>
            <dl className="reveal-facts">
              <div>
                <dt>Motive</dt>
                <dd>{reveal.motive}</dd>
              </div>
              <div>
                <dt>Method</dt>
                <dd>{reveal.method}</dd>
              </div>
            </dl>
            <p>{reveal.explanation}</p>
            <div className="key-evidence">
              <strong>Key evidence</strong>
              <ul>
                {reveal.key_evidence.map((item) => (
                  <li key={item.id}>{item.title}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {revealUnavailable && (
          <p className="notice">
            The score is final. The backend reveal route is not available yet, so the canonical reconstruction remains locked in this build.
          </p>
        )}

        <button
          className="button button-secondary restart-button"
          disabled={pending}
          onClick={() => void onRestart()}
          type="button"
        >
          {pending ? "Starting new investigation…" : "Start new investigation"}
        </button>
      </section>
    );
  }

  const isComplete = Boolean(killerId && motive && method && evidenceIds.length >= 2);

  return (
    <section className="theory-panel" aria-labelledby="theory-title">
      <div className="section-heading">
        <p className="eyebrow">Final accusation</p>
        <h2 id="theory-title">Submit your theory</h2>
        <p>
          You get one official submission. Choose a suspect, motive, method, and two or three evidence items.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Suspect
            <select required value={killerId} onChange={(event) => setKillerId(event.target.value)}>
              <option value="">Select a suspect</option>
              {caseData.suspects.map((suspect) => (
                <option key={suspect.id} value={suspect.id}>{suspect.name}</option>
              ))}
            </select>
          </label>

          <label>
            Motive
            <select required value={motive} onChange={(event) => setMotive(event.target.value)}>
              <option value="">Select a motive</option>
              {caseData.accusation_options.motives.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>

          <label className="full-width">
            Method
            <select required value={method} onChange={(event) => setMethod(event.target.value)}>
              <option value="">Select a method</option>
              {caseData.accusation_options.methods.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
        </div>

        <fieldset className="evidence-picker">
          <legend>Supporting evidence <span>Choose 2–3</span></legend>
          {evidence.map((item) => {
            const checked = evidenceIds.includes(item.id);
            const limitReached = evidenceIds.length === 3 && !checked;

            return (
              <label key={item.id} className={checked ? "evidence-option selected" : "evidence-option"}>
                <input
                  checked={checked}
                  disabled={limitReached}
                  onChange={() => toggleEvidence(item.id)}
                  type="checkbox"
                />
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.kind}</small>
                </span>
              </label>
            );
          })}
        </fieldset>

        <button className="button button-primary submit-button" disabled={!isComplete || pending} type="submit">
          {pending ? "Submitting accusation…" : "Submit official accusation"}
        </button>
      </form>
    </section>
  );
}
