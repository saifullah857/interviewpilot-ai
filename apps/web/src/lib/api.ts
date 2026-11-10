export interface Me {
  id: string
  email: string
  role: string
  created_at: string
  profile: { display_name: string; education_level: string | null; target_roles: string[] }
  consents: { voice_transcript: boolean; analytics: boolean }
}

export interface Company {
  slug: string; name: string; description: string; tech_focus: string[]; localities: string[]
  website: string | null; careers_url: string | null; last_verified_at: string | null; needs_recheck: boolean; evidence_count: number
}
export interface Source { id: string; url: string; source_type: string; label: string; stored_label: string; retrieved_at: string; excerpt: string }
export interface Requirement { id: string; kind: string; role_title: string | null; text: string; skills: string[]; years_experience: number | null; scope: string; label: string; source_url: string; retrieved_at: string }
export interface CompanyDetail extends Company { locations: { id: string; locality: string; address: string | null; is_lahore: boolean }[]; sources: Source[]; requirements: Requirement[] }
export interface ResearchRun { id: string; status: 'running' | 'succeeded' | 'partial' | 'unavailable' | 'failed'; error_code: string | null; summary: Record<string, unknown> & { message?: string; warnings?: string[]; conflicts?: { role: string; years: number[] }[] }; started_at: string; finished_at: string | null; cached?: boolean }
export interface AdminFinding { id: string; kind: string; role_title: string | null; text: string; skills: string[]; years_experience: number | null; scope: string; label: string; source_url: string; source_type: string; retrieved_at: string; status: string; source_id: string; source_status: string }
export interface CompanyList { items: Company[]; total: number; page: number; page_size: number }
export interface AdminSource extends Source { supports_lahore: boolean; status: string }
export interface AdminCompanyItem { id: string; slug: string; name: string; verification_status: string; locations: number; sources: number; last_verified_at: string | null }
export interface AdminCompany {
  id: string; slug: string; name: string; website: string | null; careers_url: string | null; description: string; tech_focus: string[]
  verification_status: string; last_verified_at: string | null
  locations: { id: string; locality: string; address: string | null; is_lahore: boolean; verified_at: string | null }[]
  sources: AdminSource[]
  verifications: { id: string; decision: string; notes: string; evidence_ids: string[]; created_at: string }[]
  findings: AdminFinding[]
  latest_run: ResearchRun | null
}
export interface Decision { decision: 'verified' | 'rejected' | 'marked_stale'; evidence_ids: string[]; notes: string }

export interface ParsedResume {
  education: { institution: string; degree: string | null; field: string | null; period: string | null; evidence: string }[]
  experience: { title: string; organization: string | null; period: string | null; summary: string; technologies: string[]; evidence: string }[]
  projects: { name: string; description: string; technologies: string[]; evidence: string }[]
  skills: { name: string; category: string; source: 'stated' | 'inferred'; evidence: string }[]
  achievements: { text: string; measurable: boolean; evidence: string }[]
  inferences: { statement: string; basis: string; confidence: 'low' | 'medium' }[]
}
export interface ResumeVersion {
  id: string; created_at: string; provider: string; model: string; schema_version: string; parsed: ParsedResume
  report: { retries: number; dropped_ungrounded: number; downgraded_to_inferred: number; injection_signals: string[]; truncated: boolean }
}
export interface ResumeItem {
  id: string; filename: string; kind: string; size_bytes: number; pages: number; created_at: string; analyzed: boolean; duplicate: boolean
  latest: ResumeVersion | null; injection_signals: string[]; truncated: boolean
}
export interface FitGroup { matched: { skill: string; source: 'stated' | 'inferred'; evidence: string }[]; missing: string[]; coverage_stated: number; coverage_with_inferred: number }
export interface CompanyFit {
  available: boolean; reason?: string; company: { slug: string; name: string }; role: string
  skills?: { skill: string; weight: number; have: 'stated' | 'inferred' | null; reasons: string[]; sources: { url: string; label: string }[] }[]
  coverage_stated?: number; coverage_with_inferred?: number; evidence_count?: number; notes?: string[]
}
export interface Fit { company?: CompanyFit; role: { slug: string; title: string }; catalog_version: string; catalog_note: string; required: FitGroup; preferred: FitGroup; notes: string[]; disclaimer: string; resume_version_id: string }

export interface Question {
  id: string; position: number; type: 'mcq' | 'short_answer'; category: string; prompt: string; options: { index: number; text: string }[]
  difficulty: string; topic: string; label: string; informed_by: { url: string; label: string }[]; max_points: number
}
export interface SavedAnswer { question_id: string; selected_index: number | null; response_text: string | null }
export interface Assessment {
  id: string; status: 'generating' | 'ready' | 'in_progress' | 'submitted' | 'failed'; mode: 'general' | 'company'; role: { slug: string; title: string }
  company: { slug: string; name: string } | null; notice: string | null; question_count: number; duration_minutes: number; created_at: string
  started_at: string | null; deadline_at: string | null; submitted_at: string | null; auto_submitted: boolean; server_now: string
  error_code: string | null; message: string | null; generation: { accepted: number; target: number; dropped: number; warnings: string[] }
  score: { mcq_correct: number; mcq_total: number } | null; questions?: Question[] | null; answers?: SavedAnswer[] | null
}
export interface ReviewQuestion extends Question {
  correct_index: number | null; reference_points: string[]; explanation: string; selected_index: number | null; response_text: string | null
  is_correct: boolean | null; needs_evaluation: boolean
}
export interface Review {
  assessment: Assessment; questions: ReviewQuestion[]
  result: { mcq_correct: number; mcq_total: number; mcq_unanswered: number; short_answered: number; short_total: number; evaluated: boolean; by_topic: { topic: string; correct: number; total: number }[]; note: string }
}

export interface BankQuestion { slug: string; kind: string; category: string; difficulty: string; roles: string[]; companies: string[]; topics: string[]; prompt: string; options: string[]; source_label: string; source_title: string }
export interface ScreeningSummary { id: string; status: string; company: { slug: string; name: string } | null; role: string; level: string; submitted_at: string | null; correct: number | null; total: number; score: number | null }
export interface ScreeningSession { id: string; status: string; company: { slug: string; name: string } | null; role: string; level: string; started_at: string; deadline_at: string; server_now: string; total: number; answered: number; questions: BankQuestion[]; answers: Record<string, number> }
export interface ScreeningResult { session: ScreeningSummary; auto_submitted: boolean; by_category: { name: string; correct: number; total: number; score: number }[]; by_difficulty: { name: string; correct: number; total: number; score: number }[]; next_step: { next_level?: string; weak_categories?: string[]; strong_categories?: string[]; message?: string }; review: { slug: string; category: string; difficulty: string; kind: string; prompt: string; options: string[]; chosen: number | null; answer_index: number; correct: boolean; explanation: string }[]; note: string }
export interface ReadinessComponent { key: string; name: string; weight: number; effective_weight: number; how: string; status: string; value: number | null; reason: string; evidence_count: number }
export interface Readiness {
  company: { slug: string; name: string; focus: string[]; note: string } | null
  role: { slug: string; title: string }
  resume: { id: string; filename: string } | null
  overall: { value: number | null; label: string; confidence: string; explanation: string }
  evidence_count: number
  components: ReadinessComponent[]
  strengths: string[]
  weak_areas: string[]
  skill_gap: { skill: string; importance: string; status: string; status_text: string; score: number | null; evidence_source: string | null; on_resume: boolean; category: string | null }[]
  next_actions: { type: string; text: string; why: string; params: Record<string, string | null> }[]
  suggested_coding: { slug: string; title: string; difficulty: string }[]
  suggested_questions: { slug: string; category: string; kind: string; difficulty: string; prompt: string }[]
  disclaimer: string
}
export interface MatchRow { value: number | null; label: string; confidence: string; evidence_count: number; matching_skills: string[]; missing_required: string[]; role?: { slug: string; title: string }; company?: { slug: string; name: string }; focus?: string[] }
export interface AdminQuestion { id: string; slug: string; kind: string; category: string; difficulty: string; roles: string[]; companies: string[]; topics: string[]; prompt: string; ideal_answer: string; key_points: string[]; follow_ups: string[]; options: string[]; answer_index: number | null; explanation: string; source_label: string; source_note: string; enabled: boolean }
export interface CompanySet { company: { slug: string; name: string; focus: string[]; note: string }; role: string | null; total: number; counts: Record<string, number>; solved: number; problems: { slug: string; title: string; difficulty: string; topics: string[]; ds: string[]; why: string[]; solved: boolean }[] }
export interface BankReveal { slug: string; ideal_answer: string; key_points: string[]; follow_ups: string[]; answer_index: number | null; explanation: string; source_label: string; source_note: string }
export interface BankStats { total: number; companies: { slug: string; name: string; total: number; kind: Record<string, number>; difficulty: Record<string, number>; source: Record<string, number> }[]; source: Record<string, number> }
export interface CodingProblemSummary { slug: string; title: string; difficulty: string; minutes: number; topics: string[]; roles: string[]; tags?: string[]; ds?: string[] }
export interface CodingProblem extends CodingProblemSummary {
  statement: string; constraints: string[]; signature: string; starter_code: string; examples: { args: unknown[]; output: unknown; explanation: string }[]
  visible_tests: { id: string; args: unknown[]; expected: unknown }[]; hidden_count: number; per_test_ms: number; label: string
}
export interface CodingResult {
  id: string; hidden: boolean; label: string; status: 'passed' | 'failed' | 'error' | 'timeout' | 'not_run'; runtime_ms: number | null
  args?: unknown[] | null; expected?: unknown; actual?: string | null; error?: string | null; stdout?: string | null
}
export interface CodingFeedback { complexity: string; strengths: string[]; improvements: string[]; readability: string; label: string; note: string }
export interface CodingSubmission {
  id: string; kind: 'run' | 'submit'; problem: string; status: string; executed: boolean; compile_error: string | null; passed_count: number | null; total_count: number
  runtime_ms: number | null; runner_backend: string; message: string | null; results: CodingResult[]; created_at: string; feedback: CodingFeedback | null
}
export interface CodingSession {
  id: string; status: 'in_progress' | 'submitted'; assessment_id: string | null; problem_slugs: string[]; problems: CodingProblem[] | null; drafts: Record<string, string>
  progress: { problem: string; runs: number; submits: number; last_submit: CodingSubmission | null }[]; started_at: string; deadline_at: string; submitted_at: string | null; company?: CodingPlan['company']; language?: string; plan?: Partial<CodingPlan>
  auto_submitted: boolean; server_now: string; runs_left: number; submits_left: number
}
export interface CodingSessionSummary { id: string; status: string; problem_slugs: string[]; started_at: string; deadline_at: string; submitted_at: string | null; tests_passed: number | null; tests_total: number; executed: boolean; company?: { slug: string; name: string } | null; score?: number | null; solved?: number; problems?: number }
export interface CodingPlan { role?: string; company: { slug: string; name: string; focus: string[]; note: string } | null; resume: { languages: string[]; skills: string[]; focus: string[] } | null; language: string; language_note: string | null; reasons: Record<string, string> }
export interface CompanyFocus { slug: string; name: string; tech_focus: string[]; focus: string[]; focus_tags: string[] }
export interface Dashboard {
  summary: { coding_sessions: number; problems_solved: number; bank_size: number; reports: number; average_coding_score: number | null; screening_tests: number; average_screening_score: number | null; best_coding_score: number | null; latest_overall: number | null }
  coding: { id: string; date: string | null; company: { name: string } | null; score: number | null; passed: number | null; total: number | null; solved: number; problems_count: number; executed: boolean; problems: { slug: string; title: string; difficulty: string; submitted: boolean; executed: boolean; passed: number | null; total: number | null; score: number | null }[] }[]
  topics: { name: string; passed: number; total: number; score: number }[]
  difficulty: { name: string; passed: number; total: number; score: number }[]
  structures: { name: string; passed: number; total: number; score: number }[]
  reports: { id: string; date: string; role: string; overall: number | null; components: Record<string, number>; auto: boolean }[]
  screening: { id: string; date: string | null; score: number | null; correct: number; total: number; level: string; company: string | null }[]
  screening_categories: { name: string; passed: number; total: number; score: number }[]
  weak_topics: { name: string; score: number }[]
  strong_topics: { name: string; score: number }[]
}
export interface CodingReview {
  session: CodingSession
  problems: { problem: CodingProblem; approach: string; complexity: Record<string, string>; reference_solution: string; final_code: string; runs: number; submits: number; submission: CodingSubmission | null; passed_count: number | null; total_count: number; solved: boolean }[]
  summary: { solved: number; problems: number; tests_passed: number | null; tests_total: number; executed: boolean; note: string }
}
export interface RunnerStatus { mode: string; executes_code: boolean; reachable: boolean; backend: string; message: string }

export interface InterviewTurn {
  id: string; position: number; speaker: 'interviewer' | 'candidate'; kind: 'opening' | 'question' | 'follow_up' | 'answer' | 'skipped' | 'closing'
  text: string; topic: string | null; source: string; informed_by: { n: number; url: string; label: string }[]; created_at: string
}
export interface Interview {
  id: string; status: 'active' | 'completed' | 'interrupted'; mode: 'general' | 'company'; role: { slug: string; title: string }; company: { slug: string; name: string } | null
  input_mode: 'voice' | 'text'; question_target: number; questions_asked: number; answers_given: number; awaiting_answer: boolean; label: string; notice: string
  save_transcript: boolean; transcript_available: boolean; transcript_purged_at: string | null; evaluated: boolean; events: { kind: string; at: string }[]
  provider: string; model: string; started_at: string; last_activity_at: string; ended_at: string | null; server_now: string; idle_minutes: number; turns: InterviewTurn[] | null
}
export interface InterviewEvaluation {
  rubric_version: string; label: string; indicator: number | null; answers_scored: number; evidence_level: 'limited' | 'adequate'
  criteria: { key: string; name: string; description: string; score: number; max: number; rationale: string; evidence_turns: number[]; low_evidence: boolean }[]
  strengths: string[]; improvements: string[]; per_answer: { turn: number; question: string; note: string; stronger_answer_hint: string }[]; caveats: string[]
  provider: string; model: string; created_at: string; injection_signals: string[]; transcript_kept: boolean
}
export interface InterviewReview { interview: Interview; evaluation: InterviewEvaluation | null }
export type InterviewEventKind = 'mic_denied' | 'speech_unsupported' | 'speech_error' | 'tts_unavailable'

export interface ReportComponent {
  key: string; name: string; kind: 'objective' | 'subjective'; weight: number; status: 'available' | 'missing' | 'not_run' | 'not_scored'; value: number | null
  reason: string; low_evidence: boolean; detail: Record<string, unknown>; sources: string[]; how: string
}
export interface ReportGap { label: string; severity: 'high' | 'medium' | 'low'; kind: 'objective' | 'subjective' | 'both'; evidence: { source: string; detail: string }[] }
export interface Report {
  id: string; created_at: string; role: { slug: string; title: string }; company: { slug: string; name: string } | null; mode: 'general' | 'company'; horizon: 7 | 30
  rubric_version: string; rubric: { version: string; overall: string }; sources_used: Record<string, string | null>; components: ReportComponent[]
  overall: { value: number | null; included: string[]; subjective_share: number; how: string; note: string; limited: boolean; missing: { key: string; name: string; status: string; reason: string }[] }
  gaps: ReportGap[]; strengths: { label: string; kind: string; source: string; evidence: string }[]
  practice_questions: { type: 'question' | 'coding'; prompt?: string; topic?: string; title?: string; slug?: string; label: string }[]
  sources: { url: string; label: string; kind: string; role_title: string | null; text: string }[]
  roadmap: { source: 'ai' | 'built_in'; horizon: number; note: string; items: { when: string; focus: string; tasks: string[]; minutes: number }[] }
  notes: string[]
  previous: { report_id: string; created_at: string; overall_before: number | null; overall_after: number | null; overall_delta: number | null; components: { key: string; before: number; after: number; delta: number }[]; note: string } | null
  disclaimer: string; provider: string; model: string
}
export interface ReportSummary { auto?: boolean; id: string; created_at: string; role: { slug: string; title: string }; company: { slug: string; name: string } | null; mode: string; horizon: number; overall: number | null; scores: Record<string, number>; included: string[]; missing: string[] }
export interface ReportSources {
  assessments: { id: string; created_at: string; mode: string; mcq_correct: number; mcq_total: number }[]
  coding_sessions: { id: string; created_at: string; problems: number; executed: boolean; tests_passed: number | null; tests_total: number }[]
  interviews: { id: string; created_at: string; answers_given: number | null; evaluated: boolean; indicator: number | null }[]
  resumes: { id: string; filename: string }[]
}
export interface Progress { series: { report_id: string; created_at: string; role: string; overall: number | null; scores: Record<string, number> }[]; latest_change: number | null; note: string }

export interface RoleRank { slug: string; title: string; family: string; score: number; matched: string[]; missing: string[] }
export interface DiscoverCompany {
  slug: string; name: string; status: 'verified_lahore' | 'candidate' | 'stale' | 'pending_review'; status_label: string; localities: string[]; tech_focus: string[]
  focus_areas: string[]; website: string | null; last_verified_at: string | null; needs_recheck: boolean; researched: boolean
  match: { score: number; reasons: string[]; basis: string } | null
}
export interface Recommendations { roles: RoleRank[]; role: RoleRank; companies: DiscoverCompany[] }
export interface DiscoverDetail extends CompanyDetail {
  status: DiscoverCompany['status']; status_label: string; auto_verified: boolean; focus_areas: string[]; focus_note: string | null
  latest_run: { id: string; status: 'running' | 'succeeded' | 'partial' | 'unavailable' | 'failed'; error_code: string | null; summary: Record<string, unknown> & { message?: string }; started_at: string; finished_at: string | null } | null
}

export class ApiError extends Error {
  status: number
  code: string
  details?: { field: string; message: string }[]
  constructor(status: number, code: string, message: string, details?: { field: string; message: string }[]) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api/v1'
let csrfToken: string | null = null
let refreshing: Promise<boolean> | null = null

async function getCsrf(): Promise<string> {
  if (!csrfToken) {
    const r = await fetch(`${BASE}/auth/csrf`, { credentials: 'include' })
    csrfToken = (await r.json()).csrf_token as string
  }
  return csrfToken
}

async function raw(method: string, path: string, body?: unknown): Promise<Response> {
  const headers: Record<string, string> = {}
  const isForm = body instanceof FormData  // the browser sets the multipart boundary itself
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRF-Token'] = await getCsrf()
  return fetch(`${BASE}${path}`, { method, headers, credentials: 'include', body: body === undefined ? undefined : isForm ? body : JSON.stringify(body) })
}

/** One refresh at a time: parallel refreshes would look like token reuse to the server and log the user out. */
function refreshSession(): Promise<boolean> {
  refreshing ??= raw('POST', '/auth/refresh').then(r => r.ok).finally(() => { refreshing = null })
  return refreshing
}

async function request<T>(method: string, path: string, body?: unknown, retry = true): Promise<T> {
  let res: Response
  try {
    res = await raw(method, path, body)
    if (res.status === 403) {
      const e = await res.clone().json().catch(() => null)
      if (e?.error?.code === 'csrf_failed') { csrfToken = null; res = await raw(method, path, body) }
    }
  } catch {
    throw new ApiError(0, 'network_error', 'Cannot reach the server. Check that the API is running and try again.')
  }
  if (res.status === 401 && retry && !path.startsWith('/auth/')) {
    if (await refreshSession()) return request<T>(method, path, body, false)
  }
  if (res.status === 204) return undefined as T
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const err = data?.error
    throw new ApiError(res.status, err?.code ?? 'http_error', err?.message ?? 'Request failed.', err?.details)
  }
  return data as T
}

export const api = {
  me: () => request<Me>('GET', '/me'),
  signup: (email: string, password: string, display_name: string) => request<Me>('POST', '/auth/signup', { email, password, display_name }),
  login: (email: string, password: string) => request<Me>('POST', '/auth/login', { email, password }),
  logout: () => request<void>('POST', '/auth/logout'),
  updateProfile: (display_name: string) => request<Me>('PATCH', '/me', { display_name }),
  updateConsents: (c: Partial<Me['consents']>) => request<Me['consents']>('PATCH', '/me/consents', c),
  companies: (p: { q?: string; locality?: string; tech?: string; page?: number }) => {
    const qs = new URLSearchParams()
    Object.entries(p).forEach(([k, v]) => v !== undefined && v !== '' && qs.set(k, String(v)))
    return request<CompanyList>('GET', `/companies?${qs}`)
  },
  localities: () => request<string[]>('GET', '/companies/localities'),
  company: (slug: string) => request<CompanyDetail>('GET', `/companies/${encodeURIComponent(slug)}`),
  adminCompanies: (status?: string) => request<AdminCompanyItem[]>('GET', `/admin/companies${status ? `?status=${status}` : ''}`),
  adminCompany: (id: string) => request<AdminCompany>('GET', `/admin/companies/${id}`),
  adminCreateCompany: (b: { name: string; website?: string; description?: string; tech_focus?: string[] }) => request<AdminCompany>('POST', '/admin/companies', b),
  adminUpdateCompany: (id: string, b: { website?: string | null; careers_url?: string | null; description?: string; tech_focus?: string[] }) => request<AdminCompany>('PATCH', `/admin/companies/${id}`, b),
  adminAddLocation: (id: string, b: { locality: string; address?: string; is_lahore: boolean }) => request<AdminCompany>('POST', `/admin/companies/${id}/locations`, b),
  adminAddSource: (id: string, b: { url: string; source_type: string; label: string; supports_lahore: boolean; excerpt: string; retrieved_at: string }) =>
    request<AdminCompany>('POST', `/admin/companies/${id}/sources`, b),
  adminDecide: (id: string, b: Decision) => request<AdminCompany>('POST', `/admin/companies/${id}/verification`, b),
  discoverRecommendations: (resumeId: string, role?: string, q?: string) => {
    const qs = new URLSearchParams({ resume_id: resumeId }); if (role) qs.set('role', role); if (q) qs.set('q', q)
    return request<Recommendations>('GET', `/discover/recommendations?${qs}`)
  },
  discoverCompanies: (q?: string, family?: string) => {
    const qs = new URLSearchParams(); if (q) qs.set('q', q); if (family) qs.set('family', family)
    return request<{ items: DiscoverCompany[] }>('GET', `/discover/companies?${qs}`)
  },
  discoverCompany: (slug: string) => request<DiscoverDetail>('GET', `/discover/companies/${encodeURIComponent(slug)}`),
  startCompanyResearch: (slug: string, force = false) => request<{ id: string; status: string; cached: boolean }>('POST', `/discover/companies/${encodeURIComponent(slug)}/research${force ? '?force=true' : ''}`),
  roles: () => request<{ slug: string; title: string }[]>('GET', '/roles'),
  resumes: () => request<ResumeItem[]>('GET', '/resumes'),
  uploadResume: (file: File) => { const f = new FormData(); f.append('file', file); return request<ResumeItem>('POST', '/resumes', f) },
  analyzeResume: (id: string) => request<ResumeItem>('POST', `/resumes/${id}/analyze`),
  deleteResume: (id: string) => request<void>('DELETE', `/resumes/${id}`),
  resumeFit: (id: string, role: string, company?: string) => request<Fit>('GET', `/resumes/${id}/fit?role=${encodeURIComponent(role)}${company ? `&company=${encodeURIComponent(company)}` : ''}`),
  adminStartResearch: (id: string, force = false) => request<ResearchRun>('POST', `/admin/companies/${id}/research${force ? '?force=true' : ''}`),
  adminSetFinding: (id: string, fid: string, status: 'unreviewed' | 'active' | 'rejected') => request<AdminCompany>('PATCH', `/admin/companies/${id}/findings/${fid}`, { status }),
  adminSetSource: (id: string, sid: string, status: 'unreviewed' | 'active' | 'rejected') => request<AdminCompany>('PATCH', `/admin/companies/${id}/sources/${sid}`, { status }),
  assessments: () => request<Assessment[]>('GET', '/assessments'),
  assessment: (id: string) => request<Assessment>('GET', `/assessments/${id}`),
  createAssessment: (b: { resume_id: string; role: string; company?: string; question_count: number; duration_minutes?: number }) => request<Assessment>('POST', '/assessments', b),
  startAssessment: (id: string) => request<Assessment>('POST', `/assessments/${id}/start`),
  saveAnswers: (id: string, answers: { question_id: string; selected_index?: number | null; response_text?: string | null }[]) => request<Assessment>('PUT', `/assessments/${id}/answers`, { answers }),
  submitAssessment: (id: string) => request<Review>('POST', `/assessments/${id}/submit`),
  reviewAssessment: (id: string) => request<Review>('GET', `/assessments/${id}/review`),
  deleteAssessment: (id: string) => request<void>('DELETE', `/assessments/${id}`),
  codingRunner: () => request<RunnerStatus>('GET', '/coding/runner'),
  codingProblems: (p: { role?: string; difficulty?: string } = {}) => { const qs = new URLSearchParams(); Object.entries(p).forEach(([k, v]) => v && qs.set(k, v)); return request<CodingProblemSummary[]>('GET', `/coding/problems?${qs}`) },
  bankQuestions: (p: Record<string, string>) => request<{ total: number; items: BankQuestion[]; source_titles: Record<string, string> }>('GET', `/questions?${new URLSearchParams({ limit: '100', ...p }).toString()}`),
  createScreening: (b: { role: string; company?: string; level: string; count: number }) => request<ScreeningSession>('POST', '/screening/sessions', b),
  screeningSessions: () => request<ScreeningSummary[]>('GET', '/screening/sessions'),
  screeningSession: (id: string) => request<ScreeningSession>('GET', `/screening/sessions/${id}`),
  screeningAnswer: (id: string, question: string, choice: number | null) => request<ScreeningSession>('PUT', `/screening/sessions/${id}/answers`, { question, choice }),
  screeningSubmit: (id: string) => request<ScreeningResult>('POST', `/screening/sessions/${id}/submit`),
  screeningReview: (id: string) => request<ScreeningResult>('GET', `/screening/sessions/${id}/review`),
  readiness: (p: Record<string, string>) => request<Readiness>('GET', `/readiness?${new URLSearchParams(p).toString()}`),
  readinessRoles: (p: Record<string, string>) => request<{ items: MatchRow[]; has_resume: boolean; disclaimer: string }>('GET', `/readiness/roles?${new URLSearchParams(p).toString()}`),
  readinessCompanies: (p: Record<string, string>) => request<{ role: string; items: MatchRow[]; has_resume: boolean; disclaimer: string; focus_note: string }>('GET', `/readiness/companies?${new URLSearchParams(p).toString()}`),
  adminQuestions: (p: Record<string, string>) => request<{ total: number; items: AdminQuestion[] }>('GET', `/admin/questions?${new URLSearchParams({ limit: '100', ...p }).toString()}`),
  adminCreateQuestion: (b: Omit<AdminQuestion, 'id'>) => request<AdminQuestion>('POST', '/admin/questions', b),
  adminUpdateQuestion: (slug: string, b: Partial<Omit<AdminQuestion, 'id' | 'slug'>>) => request<AdminQuestion>('PATCH', `/admin/questions/${slug}`, b),
  adminDeleteQuestion: (slug: string) => request<void>('DELETE', `/admin/questions/${slug}`),
  bankReveal: (slug: string) => request<BankReveal>('POST', `/questions/${slug}/reveal`),
  bankStats: () => request<BankStats>('GET', '/questions/stats'),
  codingCompanySet: (slug: string, role?: string) => request<CompanySet>('GET', `/coding/companies/${slug}/set${role ? `?role=${role}` : ''}`),
  codingCompanies: () => request<{ companies: CompanyFocus[]; disclaimer: string }>('GET', '/coding/companies'),
  dashboard: () => request<Dashboard>('GET', '/reports/dashboard'),
  codingSessions: () => request<CodingSessionSummary[]>('GET', '/coding/sessions'),
  createCodingSession: (b: { problem_slugs?: string[]; assessment_id?: string; role?: string; count?: number; company?: string; resume_id?: string; company_set?: boolean }) => request<CodingSession>('POST', '/coding/sessions', b),
  codingSession: (id: string) => request<CodingSession>('GET', `/coding/sessions/${id}`),
  saveCodingDraft: (id: string, slug: string, code: string) => request<CodingSession>('PUT', `/coding/sessions/${id}/drafts/${slug}`, { code }),
  runCode: (id: string, problem: string, code: string) => request<CodingSubmission>('POST', `/coding/sessions/${id}/run`, { problem, code }),
  submitCode: (id: string, problem: string, code: string) => request<CodingSubmission>('POST', `/coding/sessions/${id}/submit`, { problem, code }),
  finishCoding: (id: string) => request<CodingReview>('POST', `/coding/sessions/${id}/finish`),
  codingReview: (id: string) => request<CodingReview>('GET', `/coding/sessions/${id}/review`),
  codingFeedback: (submissionId: string) => request<CodingFeedback>('POST', `/coding/submissions/${submissionId}/feedback`),
  deleteCodingSession: (id: string) => request<void>('DELETE', `/coding/sessions/${id}`),
  interviews: () => request<Interview[]>('GET', '/interviews'),
  interview: (id: string) => request<Interview>('GET', `/interviews/${id}`),
  createInterview: (b: { resume_id: string; role: string; company?: string; question_count: number; input_mode: 'voice' | 'text'; consent: boolean; save_transcript?: boolean }) => request<Interview>('POST', '/interviews', b),
  answerInterview: (id: string, b: { text?: string; source?: 'typed' | 'speech'; skip?: boolean }) => request<Interview>('POST', `/interviews/${id}/answer`, b),
  interviewEvent: (id: string, kind: InterviewEventKind) => request<Interview>('POST', `/interviews/${id}/event`, { kind }),
  endInterview: (id: string) => request<Interview>('POST', `/interviews/${id}/end`),
  resumeInterview: (id: string) => request<Interview>('POST', `/interviews/${id}/resume`),
  evaluateInterview: (id: string) => request<InterviewReview>('POST', `/interviews/${id}/evaluate`),
  interviewReview: (id: string) => request<InterviewReview>('GET', `/interviews/${id}/review`),
  deleteInterviewTranscript: (id: string) => request<Interview>('DELETE', `/interviews/${id}/transcript`),
  deleteInterview: (id: string) => request<void>('DELETE', `/interviews/${id}`),
  reports: (role?: string) => request<ReportSummary[]>('GET', `/reports${role ? `?role=${encodeURIComponent(role)}` : ''}`),
  report: (id: string) => request<Report>('GET', `/reports/${id}`),
  createReport: (b: { role: string; resume_id?: string; assessment_id?: string; coding_session_id?: string; interview_id?: string; horizon: 7 | 30 }) => request<Report>('POST', '/reports', b),
  reportRoadmap: (id: string, horizon: 7 | 30) => request<Report>('POST', `/reports/${id}/roadmap`, { horizon }),
  deleteReport: (id: string) => request<void>('DELETE', `/reports/${id}`),
  reportSources: (role: string) => request<ReportSources>('GET', `/reports/sources?role=${encodeURIComponent(role)}`),
  reportProgress: (role?: string) => request<Progress>('GET', `/reports/progress${role ? `?role=${encodeURIComponent(role)}` : ''}`),
  changePassword: (current_password: string, new_password: string) => request<void>('POST', '/me/password', { current_password, new_password }),
  deleteAccount: (password: string) => request<void>('DELETE', '/me', { password }),
}
