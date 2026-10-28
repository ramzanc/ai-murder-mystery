export type EvidenceKind = "physical" | "digital" | "document" | string;

export type QuestionTopic = "alibi" | "secret";

export interface PublicDossier {
  summary: string;
  location: string;
  incident_time: string;
}

export interface PublicVictim {
  id: string;
  name: string;
  age: number;
  public_profile: string;
}

export interface PublicSuspect {
  id: string;
  name: string;
  age: number;
  occupation: string;
  relationship_to_victim: string;
  public_profile: string;
}

export interface PublicEvidence {
  id: string;
  title: string;
  description: string;
  kind: EvidenceKind;
}

export interface AccusationOptions {
  motives: string[];
  methods: string[];
}

export interface PublicCase {
  id: string;
  title: string;
  difficulty: string;
  dossier: PublicDossier;
  victim: PublicVictim;
  suspects: PublicSuspect[];
  initial_evidence: PublicEvidence[];
  accusation_options: AccusationOptions;
}

export interface QuestionEvent {
  sequence: number;
  suspect_id: string;
  topic: QuestionTopic;
  question: string;
  answer: string;
}

export interface InvestigationSession {
  id: string;
  case_id: string;
  events: QuestionEvent[];
  discovered_evidence_ids: string[];
  is_finalized: boolean;
  official_score: number | null;
}

export interface TheoryDraft {
  killer_id: string;
  motive: string;
  method: string;
  evidence_ids: string[];
}

export interface TheoryScore {
  killer_correct: boolean;
  motive_correct: boolean;
  method_correct: boolean;
  matching_evidence_ids: string[];
  killer_points: number;
  motive_points: number;
  method_points: number;
  evidence_points: number;
  total_points: number;
  solved: boolean;
}

export interface TheorySubmission {
  session: InvestigationSession;
  score: TheoryScore;
}

export interface RevealEvidence {
  id: string;
  title: string;
  description: string;
}

export interface CaseReveal {
  killer_id: string;
  killer_name: string;
  motive: string;
  method: string;
  key_evidence: RevealEvidence[];
  explanation: string;
}
