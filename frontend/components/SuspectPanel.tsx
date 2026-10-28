import type {
  PublicSuspect,
  QuestionEvent,
  QuestionTopic,
} from "@/lib/types";

interface SuspectPanelProps {
  suspect: PublicSuspect;
  events: QuestionEvent[];
  disabled: boolean;
  pendingTopic: QuestionTopic | null;
  onQuestion: (suspectId: string, topic: QuestionTopic) => void;
}

const TOPIC_LABELS: Record<QuestionTopic, string> = {
  alibi: "Ask about alibi",
  secret: "Ask what they are hiding",
};

export function SuspectPanel({
  suspect,
  events,
  disabled,
  pendingTopic,
  onQuestion,
}: SuspectPanelProps) {
  return (
    <article className="suspect-card" aria-labelledby={`${suspect.id}-name`}>
      <header className="suspect-header">
        <div>
          <p className="eyebrow">{suspect.relationship_to_victim}</p>
          <h3 id={`${suspect.id}-name`}>{suspect.name}</h3>
        </div>
        <div className="suspect-detail">
          <span>{suspect.occupation}</span>
          <span>Age {suspect.age}</span>
        </div>
      </header>

      <p className="suspect-profile">{suspect.public_profile}</p>

      <div className="question-actions" aria-label={`Question ${suspect.name}`}>
        {(Object.keys(TOPIC_LABELS) as QuestionTopic[]).map((topic) => (
          <button
            className="button button-secondary"
            disabled={disabled}
            key={topic}
            onClick={() => onQuestion(suspect.id, topic)}
            type="button"
          >
            {pendingTopic === topic ? "Recording answer…" : TOPIC_LABELS[topic]}
          </button>
        ))}
      </div>

      {events.length > 0 && (
        <div className="transcript" aria-label={`Interview notes for ${suspect.name}`}>
          {events.map((event) => (
            <div className="exchange" key={event.sequence}>
              <p className="question-line">
                <span>Q{event.sequence}</span>
                {event.question}
              </p>
              <p className="answer-line">{event.answer}</p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
