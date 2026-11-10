export type EvidenceLabel =
  | 'official_verified'
  | 'public_candidate_report'
  | 'ai_generated_practice'
  | 'unverified_or_outdated'

export const EVIDENCE_META: Record<EvidenceLabel, { text: string; hint: string; tone: 'ok' | 'info' | 'warn' | 'bad' }> = {
  official_verified: { text: 'Officially verified', hint: 'Supported by an official company source.', tone: 'ok' },
  public_candidate_report: { text: 'Public candidate report', hint: 'Described by a candidate; may not reflect current practice.', tone: 'info' },
  ai_generated_practice: { text: 'AI-generated practice', hint: 'Made for practice. Not an actual company question.', tone: 'warn' },
  unverified_or_outdated: { text: 'Unverified or outdated', hint: 'Not enough evidence, or needs rechecking.', tone: 'bad' },
}
