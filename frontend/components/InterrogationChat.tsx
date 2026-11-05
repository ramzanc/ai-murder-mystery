import { FormEvent, useState } from "react";

import type {
  InterrogationResponse,
  PublicEvidence,
  PublicSuspect,
} from "@/lib/types";

interface InterrogationChatProps {
  suspect: PublicSuspect;
  evidence: PublicEvidence[];
  turns: InterrogationResponse[];
  disabled: boolean;
  pending: boolean;
  onAsk: (
    suspectId: string,
    question: string,
    evidenceIds: string[],
  ) => Promise<boolean>;
}

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

export function InterrogationChat({
  suspect,
  evidence,
  turns,
  disabled,
  pending,
  onAsk,
}: InterrogationChatProps) {
  const [question, setQuestion] = useState("");
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || disabled || pending) return;

    const succeeded = await onAsk(
      suspect.id,
      normalizedQuestion,
      selectedEvidenceIds,
    );

    if (succeeded) {
      setQuestion("");
      setSelectedEvidenceIds([]);
    }
  }

  function toggleEvidence(evidenceId: string) {
    setSelectedEvidenceIds((current) =>
      current.includes(evidenceId)
        ? current.filter((id) => id !== evidenceId)
        : [...current, evidenceId],
    );
  }

  return (
    <section className="ai-interrogation" aria-labelledby="ai-interrogation-title">
      <div className="ai-interrogation-heading">
        <div>
          <p className="eyebrow">Live AI interview</p>
          <h3 id="ai-interrogation-title">Question {suspect.name}</h3>
        </div>
        <span className="live-badge">First live suspect</span>
      </div>

      <p className="ai-interrogation-intro">
        Ask a free-text question. Python limits what the suspect may know and do
        before the model writes the answer.
      </p>

      <div className="ai-transcript" aria-live="polite">
        {turns.length === 0 ? (
          <p className="empty-state">
            No live questions yet. Try asking about the timeline, an alibi, or
            a discovered clue.
          </p>
        ) : (
          turns.map((turn, index) => (
            <article className="ai-exchange" key={`${turn.question}-${index}`}>
              <p className="detective-message">
                <span>Detective</span>
                {turn.question}
              </p>
              <p className="suspect-message">
                <span>{suspect.name}</span>
                {turn.dialogue}
              </p>
              <details className="interaction-trace">
                <summary>Response trace</summary>
                <dl>
                  <div><dt>Intent</dt><dd>{humanize(turn.trace.intent)}</dd></div>
                  <div><dt>Tactic</dt><dd>{humanize(turn.trace.tactic)}</dd></div>
                  <div><dt>Model</dt><dd>{turn.trace.model}</dd></div>
                  <div><dt>Latency</dt><dd>{turn.trace.latency.total_ms.toFixed(0)} ms</dd></div>
                </dl>
              </details>
            </article>
          ))
        )}
        {pending && <p className="thinking-state">{suspect.name} is considering the question…</p>}
      </div>

      <form className="ai-question-form" onSubmit={handleSubmit}>
        {evidence.length > 0 && (
          <fieldset className="chat-evidence-picker" disabled={disabled || pending}>
            <legend>Present evidence <span>optional</span></legend>
            <div>
              {evidence.map((item) => (
                <label key={item.id}>
                  <input
                    checked={selectedEvidenceIds.includes(item.id)}
                    onChange={() => toggleEvidence(item.id)}
                    type="checkbox"
                  />
                  <span>{item.title}</span>
                </label>
              ))}
            </div>
          </fieldset>
        )}

        <label className="question-field">
          <span>Your question</span>
          <textarea
            disabled={disabled || pending}
            maxLength={1000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={`Ask ${suspect.name} in your own words…`}
            rows={3}
            value={question}
          />
        </label>
        <div className="question-submit-row">
          <small>{question.length}/1000</small>
          <button
            className="button button-primary"
            disabled={disabled || pending || question.trim().length === 0}
            type="submit"
          >
            {pending ? "Generating answer…" : "Ask question"}
          </button>
        </div>
      </form>
    </section>
  );
}
