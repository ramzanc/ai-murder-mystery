import type { PublicCase, PublicEvidence } from "@/lib/types";

interface CaseDossierProps {
  caseData: PublicCase;
  evidence: PublicEvidence[];
}

export function CaseDossier({ caseData, evidence }: CaseDossierProps) {
  return (
    <aside className="dossier" aria-labelledby="dossier-title">
      <div className="section-heading">
        <p className="eyebrow">Case dossier</p>
        <h2 id="dossier-title">Known facts</h2>
      </div>

      <p className="dossier-summary">{caseData.dossier.summary}</p>

      <dl className="fact-list">
        <div>
          <dt>Location</dt>
          <dd>{caseData.dossier.location}</dd>
        </div>
        <div>
          <dt>Incident</dt>
          <dd>{caseData.dossier.incident_time}</dd>
        </div>
        <div>
          <dt>Difficulty</dt>
          <dd className="capitalize">{caseData.difficulty}</dd>
        </div>
      </dl>

      <section className="victim-card" aria-labelledby="victim-title">
        <p className="eyebrow">Victim</p>
        <h3 id="victim-title">{caseData.victim.name}</h3>
        <p className="muted">Age {caseData.victim.age}</p>
        <p>{caseData.victim.public_profile}</p>
      </section>

      <section className="evidence-section" aria-labelledby="evidence-title">
        <div className="evidence-heading">
          <div>
            <p className="eyebrow">Evidence locker</p>
            <h3 id="evidence-title">Discovered items</h3>
          </div>
          <span className="count" aria-label={`${evidence.length} evidence items`}>
            {evidence.length}
          </span>
        </div>

        {evidence.length === 0 ? (
          <p className="empty-state">No evidence has been logged.</p>
        ) : (
          <ol className="evidence-list">
            {evidence.map((item) => (
              <li key={item.id}>
                <div className="evidence-meta">
                  <strong>{item.title}</strong>
                  <span>{item.kind}</span>
                </div>
                <p>{item.description}</p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </aside>
  );
}
