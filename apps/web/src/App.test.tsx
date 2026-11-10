import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { EvidenceBadge } from './components/ui'
import { api, ApiError, type AdminCompany, type AdminFinding, type Assessment, type CodingProblem, type CodingReview, type CodingSession, type CodingSubmission, type CompanyDetail, type Fit, type Interview, type InterviewEvaluation, type Me, type Report, type ReportSources, type Review, type ResumeItem } from './lib/api'

vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }: { value?: string; onChange?: (v: string) => void }) => <textarea aria-label="Python code editor" value={value ?? ''} onChange={e => onChange?.(e.target.value)} />,
}))
vi.mock('recharts', () => {
  const Stub = ({ children }: { children?: unknown }) => <div>{children as never}</div>
  return { ResponsiveContainer: Stub, BarChart: Stub, LineChart: Stub, Bar: Stub, Line: Stub, CartesianGrid: Stub, XAxis: Stub, YAxis: Stub, Tooltip: Stub }
})
vi.mock('./lib/api', async importOriginal => {
  const actual = await importOriginal<typeof import('./lib/api')>()
  return { ...actual, api: { me: vi.fn(), login: vi.fn(), signup: vi.fn(), logout: vi.fn(), updateProfile: vi.fn(), updateConsents: vi.fn(), deleteAccount: vi.fn(), companies: vi.fn(), localities: vi.fn(), company: vi.fn(), discoverCompanies: vi.fn(), discoverCompany: vi.fn(), discoverRecommendations: vi.fn(), startCompanyResearch: vi.fn(), adminCompanies: vi.fn(), adminCompany: vi.fn(), adminCreateCompany: vi.fn(), adminQuestions: vi.fn(), adminCreateQuestion: vi.fn(), adminUpdateQuestion: vi.fn(), adminDeleteQuestion: vi.fn(), codingRunner: vi.fn(), codingCompanies: vi.fn(), codingCompanySet: vi.fn(), bankQuestions: vi.fn(), readiness: vi.fn(), readinessRoles: vi.fn(), readinessCompanies: vi.fn(), createScreening: vi.fn(), screeningSessions: vi.fn(), screeningSession: vi.fn(), screeningAnswer: vi.fn(), screeningSubmit: vi.fn(), screeningReview: vi.fn(), bankReveal: vi.fn(), bankStats: vi.fn(), dashboard: vi.fn(), codingProblems: vi.fn(), codingSessions: vi.fn(), createCodingSession: vi.fn(), codingSession: vi.fn(), saveCodingDraft: vi.fn(), runCode: vi.fn(), submitCode: vi.fn(), finishCoding: vi.fn(), codingReview: vi.fn(), codingFeedback: vi.fn(), deleteCodingSession: vi.fn(), assessments: vi.fn(), assessment: vi.fn(), createAssessment: vi.fn(), startAssessment: vi.fn(), saveAnswers: vi.fn(), submitAssessment: vi.fn(), reviewAssessment: vi.fn(), deleteAssessment: vi.fn(), adminStartResearch: vi.fn(), adminSetFinding: vi.fn(), adminSetSource: vi.fn(), roles: vi.fn(), resumes: vi.fn(), uploadResume: vi.fn(), analyzeResume: vi.fn(), deleteResume: vi.fn(), resumeFit: vi.fn(), adminUpdateCompany: vi.fn(), adminAddLocation: vi.fn(), adminAddSource: vi.fn(), adminDecide: vi.fn(), interviews: vi.fn(), interview: vi.fn(), createInterview: vi.fn(), answerInterview: vi.fn(), interviewEvent: vi.fn(), endInterview: vi.fn(), resumeInterview: vi.fn(), evaluateInterview: vi.fn(), interviewReview: vi.fn(), deleteInterviewTranscript: vi.fn(), deleteInterview: vi.fn(), changePassword: vi.fn(), reports: vi.fn(), report: vi.fn(), createReport: vi.fn(), reportRoadmap: vi.fn(), deleteReport: vi.fn(), reportSources: vi.fn(), reportProgress: vi.fn() } }
})

const ME: Me = {
  id: '1', email: 'ali@example.com', role: 'user', created_at: '2026-10-14T00:00:00Z',
  profile: { display_name: 'Ali', education_level: null, target_roles: [] },
  consents: { voice_transcript: false, analytics: false },
}
const ADMIN: Me = { ...ME, role: 'admin' }
const DETAIL: CompanyDetail = {
  slug: 'acme', name: 'Acme Software', description: 'Builds things.', tech_focus: ['Python'], localities: ['Gulberg'], website: 'https://acme.example.com', careers_url: null,
  last_verified_at: '2026-10-01T00:00:00Z', needs_recheck: false, evidence_count: 1, locations: [{ id: 'l1', locality: 'Gulberg', address: null, is_lahore: true }],
  sources: [{ id: 's1', url: 'https://acme.example.com/contact', source_type: 'official_website', label: 'official_verified', stored_label: 'official_verified', retrieved_at: '2026-10-01T00:00:00Z', excerpt: 'Lists a Lahore office.' }],
  requirements: [],
}
const DDETAIL = { ...DETAIL, status: 'verified_lahore' as const, status_label: 'Lahore presence confirmed', auto_verified: false, focus_areas: ['Backend'], focus_note: null, latest_run: null }
const DITEM = { slug: 'acme', name: 'Acme Software', status: 'verified_lahore' as const, status_label: 'Lahore presence confirmed', localities: ['Gulberg'], tech_focus: ['Python'], focus_areas: ['Backend'], website: null, last_verified_at: null, needs_recheck: false, researched: false, match: { score: 72, reasons: ['Your resume shows: python'], basis: 'hint' } }
const REC = { roles: [{ slug: 'python-developer', title: 'Python Developer', family: 'backend', score: 60, matched: ['python'], missing: ['git'] }], role: { slug: 'python-developer', title: 'Python Developer', family: 'backend', score: 60, matched: ['python'], missing: ['git'] }, companies: [DITEM] }
const LIST = (items = [DETAIL]) => ({ items, total: items.length, page: 1, page_size: 20 })
const ADMIN_DETAIL: AdminCompany = {
  id: 'c1', slug: 'acme', name: 'Acme Software', website: null, careers_url: null, description: '', tech_focus: [], verification_status: 'candidate', last_verified_at: null,
  locations: [{ id: 'l1', locality: 'Gulberg', address: null, is_lahore: true, verified_at: null }],
  sources: [{ id: 's1', url: 'https://acme.example.com/contact', source_type: 'official_website', label: 'official_verified', stored_label: 'official_verified', retrieved_at: '2026-10-01T00:00:00Z', excerpt: '', supports_lahore: true, status: 'unreviewed' }],
  verifications: [], findings: [], latest_run: null,
}
const loggedIn = () => vi.mocked(api.me).mockResolvedValue(ME)
const loggedOut = () => vi.mocked(api.me).mockRejectedValue(new ApiError(401, 'not_authenticated', 'You need to log in.'))
const go = (path: string) => render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>)

beforeEach(() => {
  vi.resetAllMocks()
  loggedIn()
  vi.mocked(api.companies).mockResolvedValue(LIST([]))
  vi.mocked(api.localities).mockResolvedValue([])
  vi.mocked(api.company).mockResolvedValue(DETAIL)
  vi.mocked(api.discoverCompanies).mockResolvedValue({ items: [] })
  vi.mocked(api.discoverCompany).mockResolvedValue(DDETAIL)
  vi.mocked(api.discoverRecommendations).mockResolvedValue(REC)
  vi.mocked(api.resumes).mockResolvedValue([])
  vi.mocked(api.assessments).mockResolvedValue([])
  vi.mocked(api.codingRunner).mockResolvedValue({ mode: 'mock', executes_code: false, reachable: true, backend: 'mock', message: 'Development mock: submitted code is NOT run, so there are no pass or fail results.' })
  vi.mocked(api.codingSessions).mockResolvedValue([])
  vi.mocked(api.codingCompanySet).mockResolvedValue({ company: { slug: 'netsol-technologies', name: 'NetSol Technologies', focus: [], note: '' }, role: null, total: 25, counts: { easy: 10, medium: 10, hard: 5 }, solved: 1, problems: [{ slug: 'bank-ledger', title: 'Bank Ledger', difficulty: 'medium', topics: [], ds: [], why: ['money and ledger logic'], solved: true }, { slug: 'edit-distance', title: 'Edit Distance', difficulty: 'hard', topics: [], ds: [], why: ['dynamic programming'], solved: false }] })
  vi.mocked(api.codingCompanies).mockResolvedValue({ companies: [{ slug: 'netsol-technologies', name: 'NetSol Technologies', tech_focus: ['fintech'], focus: ['money and ledger logic'], focus_tags: ['fintech'] }], disclaimer: 'Practice emphasis, not real company questions.' })
  vi.mocked(api.codingProblems).mockResolvedValue([{ slug: 'two-sum', title: 'Two Sum', difficulty: 'easy', minutes: 15, topics: ['arrays'], roles: ['python-developer'] }, { slug: 'valid-parentheses', title: 'Valid Parentheses', difficulty: 'easy', minutes: 15, topics: ['stacks'], roles: ['python-developer'] }])
  vi.mocked(api.roles).mockResolvedValue([{ slug: 'python-developer', title: 'Python Developer' }])
  vi.mocked(api.readinessRoles).mockResolvedValue({ items: [], has_resume: false, disclaimer: '' })
  vi.mocked(api.readinessCompanies).mockResolvedValue({ role: '', items: [], has_resume: false, disclaimer: '', focus_note: '' })
  vi.mocked(api.interviews).mockResolvedValue([])
  vi.mocked(api.reports).mockResolvedValue([])
  vi.mocked(api.reportProgress).mockResolvedValue({ series: [], latest_change: null, note: 'Each point comes from a stored report.' })
  vi.mocked(api.reportSources).mockResolvedValue({ assessments: [], coding_sessions: [], interviews: [], resumes: [] })
  setSpeech(false)
})

const ROUTES: [string, RegExp][] = [
  ['/', /Prepare for the interview/], ['/login', /Log in/], ['/signup', /Create your account/],
  ['/app', /Dashboard/], ['/app/companies', /Lahore software houses/], ['/app/companies/acme', /Acme Software/], ['/app/resume', /^Resume$/], ['/app/assessment/setup', /Set up your practice/],
  ['/app/coding', /Coding practice/], ['/app/interview', /Voice interview/], ['/app/results', /^Results$/],
  ['/app/history', /Assessment history/], ['/app/settings', /Profile and settings/], ['/missing', /Page not found/],
]

describe('routes', () => {
  it('shows a not-found page when a company is not verified or does not exist', async () => {
    vi.mocked(api.discoverCompany).mockRejectedValue(new ApiError(404, 'not_found', 'Company not found.'))
    go('/app/companies/nope')
    expect(await screen.findByRole('heading', { name: 'Company not found' })).toBeInTheDocument()
  })

  it.each(ROUTES)('renders %s', async (path, heading) => {
    if (['/', '/login', '/signup', '/missing'].includes(path)) loggedOut()
    go(path)
    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
  })
})

describe('authentication', () => {
  it('sends logged-out visitors from /app to the login page', async () => {
    loggedOut()
    go('/app/results')
    expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
  })

  it('redirects a logged-in user away from the login page', async () => {
    go('/login')
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
  })

  it('shows the server message when login fails', async () => {
    loggedOut()
    vi.mocked(api.login).mockRejectedValue(new ApiError(401, 'invalid_credentials', 'Email or password is incorrect.'))
    const user = userEvent.setup()
    go('/login')
    await user.type(await screen.findByLabelText('Email'), 'ali@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong password')
    await user.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect.')
  })

  it('validates the form before calling the API', async () => {
    loggedOut()
    const user = userEvent.setup()
    go('/signup')
    await user.type(await screen.findByLabelText('Email'), 'nope')
    await user.type(screen.getByLabelText('Password'), 'short')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
    expect(screen.getByText('Use at least 8 characters.')).toBeInTheDocument()
    expect(api.signup).not.toHaveBeenCalled()
  })

  it('opens the dashboard after a successful login', async () => {
    loggedOut()
    vi.mocked(api.login).mockResolvedValue(ME)
    const user = userEvent.setup()
    go('/login')
    await user.type(await screen.findByLabelText('Email'), 'ali@example.com')
    await user.type(screen.getByLabelText('Password'), 'correct horse battery')
    await user.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(api.login).toHaveBeenCalledWith('ali@example.com', 'correct horse battery')
  })

  it('logs out and returns to the login page', async () => {
    vi.mocked(api.logout).mockResolvedValue(undefined)
    const user = userEvent.setup()
    go('/app')
    await user.click((await screen.findAllByRole('button', { name: /Log out/ }))[0])
    expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(api.logout).toHaveBeenCalled()
  })

  it('saves the voice-transcript consent through the API', async () => {
    vi.mocked(api.updateConsents).mockResolvedValue({ voice_transcript: true, analytics: false })
    const user = userEvent.setup()
    go('/app/settings')
    await user.click(await screen.findByRole('checkbox', { name: /Save my voice interview transcripts/ }))
    await waitFor(() => expect(api.updateConsents).toHaveBeenCalledWith({ voice_transcript: true }))
  })

  it('asks for the password before deleting an account', async () => {
    vi.mocked(api.deleteAccount).mockRejectedValue(new ApiError(403, 'wrong_password', 'Password is incorrect.'))
    const user = userEvent.setup()
    go('/app/settings')
    await user.click(await screen.findByRole('button', { name: 'Delete my account' }))
    await user.type(screen.getByLabelText('Confirm with your password'), 'nope nope nope')
    await user.click(screen.getByRole('button', { name: 'Permanently delete' }))
    expect(await screen.findByText('Password is incorrect.')).toBeInTheDocument()
  })
})

describe('Lahore directory', () => {
  it('explains how to load companies when the list is empty', async () => {
    go('/app/companies')
    expect(await screen.findByText('No companies match')).toBeInTheDocument()
    expect(screen.getByText(/import-seed/)).toBeInTheDocument()
  })

  it('lists companies with an honest status, including candidates that were not checked yet', async () => {
    vi.mocked(api.discoverCompanies).mockResolvedValue({ items: [DITEM, { ...DITEM, slug: 'beta', name: 'Beta Labs', status: 'candidate', status_label: 'Lahore candidate: not checked yet', localities: [] }] })
    go('/app/companies')
    expect(await screen.findByRole('link', { name: 'Acme Software' })).toBeInTheDocument()
    expect(screen.getByText('Gulberg, Lahore')).toBeInTheDocument()
    expect(screen.getByText('Lahore candidate: not checked yet')).toBeInTheDocument()
    expect(screen.getByText('Lahore presence confirmed')).toBeInTheDocument()
  })

  it('sends the focus-area filter to the API', async () => {
    const user = userEvent.setup()
    go('/app/companies')
    await screen.findByText('No companies match')
    await user.selectOptions(screen.getByLabelText('Focus area'), 'ai-ml')
    await vi.waitFor(() => expect(api.discoverCompanies).toHaveBeenLastCalledWith('', 'ai-ml'))
  })

  it('shows an error state when the API fails', async () => {
    vi.mocked(api.discoverCompanies).mockRejectedValue(new ApiError(500, 'internal_error', 'Something went wrong on our side.'))
    go('/app/companies')
    expect(await screen.findByText('Something went wrong on our side.')).toBeInTheDocument()
  })

  it('starts the research agent from the company page', async () => {
    vi.mocked(api.discoverCompany).mockResolvedValue({ ...DDETAIL, status: 'candidate', status_label: 'Lahore candidate: not checked yet', latest_run: null })
    vi.mocked(api.startCompanyResearch).mockResolvedValue({ id: 'r1', status: 'running', cached: false })
    const user = userEvent.setup()
    go('/app/companies/acme')
    await user.click(await screen.findByRole('button', { name: 'Research this company' }))
    expect(api.startCompanyResearch).toHaveBeenCalledWith('acme', false)
  })

  it('shows sources with their evidence label and link on the detail page', async () => {
    go('/app/companies/acme')
    expect(await screen.findByText('Officially verified')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'acme.example.com' })).toHaveAttribute('href', 'https://acme.example.com/contact')
  })

  it('flags evidence that has outlived its freshness limit', async () => {
    vi.mocked(api.discoverCompany).mockResolvedValue({ ...DDETAIL, sources: [{ ...DETAIL.sources[0], label: 'unverified_or_outdated' }] })
    go('/app/companies/acme')
    expect(await screen.findByText('Unverified or outdated')).toBeInTheDocument()
    expect(screen.getByText(/older than its freshness limit/)).toBeInTheDocument()
  })
})

describe('company review (admin)', () => {
  it('hides the review page and nav link from normal users', async () => {
    go('/app/admin')
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Company review/ })).not.toBeInTheDocument()
  })

  it('lets an admin verify a company using selected evidence', async () => {
    vi.mocked(api.me).mockResolvedValue(ADMIN)
    vi.mocked(api.adminCompanies).mockResolvedValue([{ id: 'c1', slug: 'acme', name: 'Acme Software', verification_status: 'candidate', locations: 1, sources: 1, last_verified_at: null }])
    vi.mocked(api.adminCompany).mockResolvedValue(ADMIN_DETAIL)
    vi.mocked(api.adminDecide).mockResolvedValue({ ...ADMIN_DETAIL, verification_status: 'verified_lahore' })
    const user = userEvent.setup()
    go('/app/admin')
    await user.click(await screen.findByRole('button', { name: /Acme Software/ }))
    await user.click(await screen.findByRole('checkbox', { name: /Use source https:\/\/acme.example.com\/contact/ }))
    await user.type(screen.getByLabelText('Review notes'), 'Checked the contact page myself.')
    await user.click(screen.getByRole('button', { name: 'Verify as Lahore company' }))
    await waitFor(() => expect(api.adminDecide).toHaveBeenCalledWith('c1', { decision: 'verified', evidence_ids: ['s1'], notes: 'Checked the contact page myself.' }))
    expect(await screen.findByText(/It now appears in the directory/)).toBeInTheDocument()
  })

  it('saves company details without touching the status', async () => {
    vi.mocked(api.me).mockResolvedValue(ADMIN)
    vi.mocked(api.adminCompanies).mockResolvedValue([{ id: 'c1', slug: 'acme', name: 'Acme Software', verification_status: 'candidate', locations: 1, sources: 1, last_verified_at: null }])
    vi.mocked(api.adminCompany).mockResolvedValue(ADMIN_DETAIL)
    vi.mocked(api.adminUpdateCompany).mockResolvedValue({ ...ADMIN_DETAIL, website: 'https://acme.example.com', tech_focus: ['Python', 'SQL'] })
    const user = userEvent.setup()
    go('/app/admin')
    await user.click(await screen.findByRole('button', { name: /Acme Software/ }))
    await user.type(await screen.findByLabelText('Technologies (comma separated)'), 'Python, SQL')
    await user.click(screen.getByRole('button', { name: 'Save details' }))
    await waitFor(() => expect(api.adminUpdateCompany).toHaveBeenCalledWith('c1', { website: null, careers_url: null, description: '', tech_focus: ['Python', 'SQL'] }))
  })

  it('shows what is missing when verification is refused', async () => {
    vi.mocked(api.me).mockResolvedValue(ADMIN)
    vi.mocked(api.adminCompanies).mockResolvedValue([{ id: 'c1', slug: 'acme', name: 'Acme Software', verification_status: 'candidate', locations: 1, sources: 1, last_verified_at: null }])
    vi.mocked(api.adminCompany).mockResolvedValue(ADMIN_DETAIL)
    const err = new ApiError(422, 'verification_requirements_not_met', 'This company cannot be verified yet.')
    err.details = ['Select at least one official_verified source that supports the Lahore presence.'] as never
    vi.mocked(api.adminDecide).mockRejectedValue(err)
    const user = userEvent.setup()
    go('/app/admin')
    await user.click(await screen.findByRole('button', { name: /Acme Software/ }))
    await user.click(await screen.findByRole('button', { name: 'Verify as Lahore company' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Select at least one official_verified source')
  })
})

const RESUME: ResumeItem = { id: 'r1', filename: 'cv.pdf', kind: 'pdf', size_bytes: 1000, pages: 1, created_at: '2026-10-14T00:00:00Z', analyzed: false, duplicate: false, latest: null, injection_signals: [], truncated: false }
const ANALYSED: ResumeItem = {
  ...RESUME, analyzed: true,
  latest: {
    id: 'v1', created_at: '2026-10-14T00:00:00Z', provider: 'groq', model: 'm', schema_version: '1',
    report: { retries: 0, dropped_ungrounded: 2, downgraded_to_inferred: 0, injection_signals: [], truncated: false },
    parsed: {
      education: [], projects: [], achievements: [],
      experience: [{ title: 'Python Intern', organization: 'Example Tech', period: null, summary: 'Built APIs.', technologies: [], evidence: 'x' }],
      skills: [{ name: 'Python', category: 'language', source: 'stated', evidence: 'Python' }, { name: 'Machine Learning', category: 'concept', source: 'inferred', evidence: '' }],
      inferences: [{ statement: 'Likely early-career', basis: 'internship', confidence: 'medium' }],
    },
  },
}
const FIT: Fit = {
  role: { slug: 'python-developer', title: 'Python Developer' }, catalog_version: 'v', catalog_note: 'General list, not from any company.', disclaimer: 'This is a preparation hint, not a prediction of being hired.',
  required: { matched: [{ skill: 'python', source: 'stated', evidence: '' }], missing: ['git'], coverage_stated: 0.5, coverage_with_inferred: 0.5 },
  preferred: { matched: [], missing: ['docker'], coverage_stated: 0, coverage_with_inferred: 0 }, notes: [], resume_version_id: 'v1',
}

describe('resume page', () => {
  it('shows the empty state and the privacy notice', async () => {
    go('/app/resume')
    expect(await screen.findByText('No resumes yet')).toBeInTheDocument()
    expect(screen.getByText(/sent to Groq, our AI provider/)).toBeInTheDocument()
  })

  it('rejects the wrong file type without calling the API', async () => {
    const user = userEvent.setup({ applyAccept: false })
    go('/app/resume')
    await user.upload(await screen.findByLabelText(/Choose a resume file/), new File(['x'], 'notes.txt', { type: 'text/plain' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose a PDF or DOCX file.')
    expect(api.uploadResume).not.toHaveBeenCalled()
  })

  it('uploads a resume and lists it', async () => {
    vi.mocked(api.uploadResume).mockResolvedValue(RESUME)
    vi.mocked(api.resumes).mockResolvedValueOnce([]).mockResolvedValue([RESUME])
    const user = userEvent.setup()
    go('/app/resume')
    await user.upload(await screen.findByLabelText(/Choose a resume file/), new File(['%PDF-'], 'cv.pdf', { type: 'application/pdf' }))
    expect(await screen.findByRole('button', { name: 'Analyse with AI' })).toBeInTheDocument()
    expect(api.uploadResume).toHaveBeenCalledTimes(1)
  })

  it('shows the server message when an upload is refused', async () => {
    vi.mocked(api.uploadResume).mockRejectedValue(new ApiError(422, 'no_text', 'No readable text was found.'))
    const user = userEvent.setup()
    go('/app/resume')
    await user.upload(await screen.findByLabelText(/Choose a resume file/), new File(['%PDF-'], 'scan.pdf', { type: 'application/pdf' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No readable text was found.')
  })

  it('analyses a resume and separates stated skills from AI inferences', async () => {
    vi.mocked(api.resumes).mockResolvedValue([RESUME])
    vi.mocked(api.analyzeResume).mockResolvedValue(ANALYSED)
    const user = userEvent.setup()
    go('/app/resume')
    await user.click(await screen.findByRole('button', { name: 'Analyse with AI' }))
    expect(await screen.findByText('Machine Learning')).toBeInTheDocument()
    expect(screen.getAllByText('Stated').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Inferred').length).toBeGreaterThan(0)
    expect(screen.getByText('AI conclusions')).toBeInTheDocument()
    expect(screen.getByText(/2 item\(s\) were removed because the AI could not point to matching text/)).toBeInTheDocument()
  })

  it('explains when AI analysis is not configured', async () => {
    vi.mocked(api.resumes).mockResolvedValue([RESUME])
    vi.mocked(api.analyzeResume).mockRejectedValue(new ApiError(503, 'llm_not_configured', "AI analysis isn't set up on this server yet."))
    const user = userEvent.setup()
    go('/app/resume')
    await user.click(await screen.findByRole('button', { name: 'Analyse with AI' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("AI analysis isn't set up")
  })

  it('compares an analysed resume with a role and shows the disclaimer', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.resumeFit).mockResolvedValue(FIT)
    const user = userEvent.setup()
    go('/app/resume')
    await user.selectOptions(await screen.findByLabelText('Target role'), 'python-developer')
    expect(await screen.findByText('Missing: git')).toBeInTheDocument()
    expect(screen.getByText(/not a prediction of being hired/)).toBeInTheDocument()
    expect(api.resumeFit).toHaveBeenCalledWith('r1', 'python-developer', undefined)
  })

  it('asks before deleting and then deletes', async () => {
    vi.mocked(api.resumes).mockResolvedValueOnce([RESUME]).mockResolvedValue([])
    vi.mocked(api.deleteResume).mockResolvedValue(undefined)
    const user = userEvent.setup()
    go('/app/resume')
    await user.click(await screen.findByRole('button', { name: 'Delete' }))
    expect(api.deleteResume).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Yes, delete it' }))
    await waitFor(() => expect(api.deleteResume).toHaveBeenCalledWith('r1'))
  })

  it('shows resume status on the dashboard', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    go('/app')
    expect(await screen.findByText('cv.pdf is analysed.')).toBeInTheDocument()
  })
})

const FINDING: AdminFinding = {
  id: 'f1', kind: 'role_requirement', role_title: 'Python Developer', text: 'Needs Python and SQL.', skills: ['Python', 'SQL'], years_experience: 2, scope: 'lahore',
  label: 'official_verified', source_url: 'https://acme.example.com/careers/python', source_type: 'careers_page', retrieved_at: '2026-10-14T00:00:00Z', status: 'unreviewed', source_id: 's2', source_status: 'unreviewed',
}
const VERIFIED_ADMIN: AdminCompany = { ...ADMIN_DETAIL, verification_status: 'verified_lahore' }
const ADMIN_ROW = { id: 'c1', slug: 'acme', name: 'Acme Software', verification_status: 'verified_lahore', locations: 1, sources: 1, last_verified_at: null }

async function openAdmin(detail: AdminCompany) {
  vi.mocked(api.me).mockResolvedValue(ADMIN)
  vi.mocked(api.adminCompanies).mockResolvedValue([{ ...ADMIN_ROW, verification_status: detail.verification_status }])
  vi.mocked(api.adminCompany).mockResolvedValue(detail)
  const user = userEvent.setup()
  go('/app/admin')
  await user.click(await screen.findByRole('button', { name: /Acme Software/ }))
  return user
}

describe('company research (admin)', () => {
  it('only offers research for verified companies', async () => {
    await openAdmin({ ...ADMIN_DETAIL, verification_status: 'candidate' })
    expect(await screen.findByText(/Research is available once the company is verified/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Run research' })).not.toBeInTheDocument()
  })

  it('starts a run and shows the outcome, warnings and conflicts', async () => {
    const done: AdminCompany = {
      ...VERIFIED_ADMIN, findings: [FINDING],
      latest_run: { id: 'r1', status: 'succeeded', error_code: null, started_at: 'x', finished_at: 'y', summary: { message: 'Saved 1 finding(s) from 2 source(s). Review and approve before users can see them.', warnings: ['ai_output_rejected'], conflicts: [{ role: 'python developer', years: [2, 5] }] } },
    }
    vi.mocked(api.adminStartResearch).mockResolvedValue({ id: 'r1', status: 'running', error_code: null, summary: {}, started_at: 'x', finished_at: null })
    const user = await openAdmin(VERIFIED_ADMIN)
    vi.mocked(api.adminCompany).mockResolvedValue(done)
    await user.click(await screen.findByRole('button', { name: 'Run research' }))
    expect(api.adminStartResearch).toHaveBeenCalledWith('c1', false)
    expect(await screen.findByText(/Saved 1 finding/)).toBeInTheDocument()
    expect(screen.getByText(/failed our checks/)).toBeInTheDocument()
    expect(screen.getByText(/Sources disagree: python developer \(2 vs 5 years\)/)).toBeInTheDocument()
    expect(screen.getByText('Mentions Lahore')).toBeInTheDocument()
  })

  it('passes the refresh option through', async () => {
    vi.mocked(api.adminStartResearch).mockResolvedValue({ id: 'r1', status: 'running', error_code: null, summary: {}, started_at: 'x', finished_at: null })
    const user = await openAdmin(VERIFIED_ADMIN)
    await user.click(await screen.findByRole('checkbox', { name: /Refresh even if a recent run exists/ }))
    await user.click(screen.getByRole('button', { name: 'Run research' }))
    expect(api.adminStartResearch).toHaveBeenCalledWith('c1', true)
  })

  it('explains when live research is not set up', async () => {
    vi.mocked(api.adminStartResearch).mockRejectedValue(new ApiError(503, 'research_not_configured', "Live research isn't set up on this server (no search key)."))
    const user = await openAdmin(VERIFIED_ADMIN)
    await user.click(await screen.findByRole('button', { name: 'Run research' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("Live research isn't set up")
  })

  it('shows an unavailable run without inventing results', async () => {
    await openAdmin({ ...VERIFIED_ADMIN, latest_run: { id: 'r1', status: 'unavailable', error_code: 'research_unavailable', started_at: 'x', finished_at: 'y', summary: { message: 'The search provider is unavailable. Nothing was changed; existing approved evidence is unaffected.' } } })
    expect(await screen.findByText(/search provider is unavailable/)).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Research findings' })).not.toBeInTheDocument()
  })

  it('approves and rejects findings', async () => {
    vi.mocked(api.adminSetFinding).mockResolvedValue({ ...VERIFIED_ADMIN, findings: [{ ...FINDING, status: 'active' }] })
    const user = await openAdmin({ ...VERIFIED_ADMIN, findings: [FINDING] })
    await user.click(await screen.findByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(api.adminSetFinding).toHaveBeenCalledWith('c1', 'f1', 'active'))
    expect(await screen.findByText('Finding approved.')).toBeInTheDocument()
  })

  it('polls while a run is in progress', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      await openAdmin({ ...VERIFIED_ADMIN, latest_run: { id: 'r1', status: 'running', error_code: null, started_at: 'x', finished_at: null, summary: {} } })
      expect(await screen.findByRole('button', { name: 'Researching…' })).toBeDisabled()
      const before = vi.mocked(api.adminCompany).mock.calls.length
      await vi.advanceTimersByTimeAsync(3100)
      expect(vi.mocked(api.adminCompany).mock.calls.length).toBeGreaterThan(before)
    } finally { vi.useRealTimers() }
  })

  it('lets a reviewer reject a source', async () => {
    vi.mocked(api.adminSetSource).mockResolvedValue(VERIFIED_ADMIN)
    const user = await openAdmin(VERIFIED_ADMIN)
    await user.click(await screen.findByRole('button', { name: 'Reject source' }))
    await waitFor(() => expect(api.adminSetSource).toHaveBeenCalledWith('c1', 's1', 'rejected'))
  })
})

describe('company requirements and company comparison', () => {
  const REQ = { id: 'q1', kind: 'role_requirement', role_title: 'Python Developer', text: 'Needs Python and SQL.', skills: ['Python', 'SQL'], years_experience: 2, scope: 'unspecified', label: 'unverified_or_outdated', source_url: 'https://acme.example.com/careers/python', retrieved_at: '2025-01-01T00:00:00Z' }

  it('shows approved hiring information with its label, scope and source', async () => {
    vi.mocked(api.discoverCompany).mockResolvedValue({ ...DDETAIL, requirements: [REQ, { ...REQ, id: 'q2', kind: 'interview_format', role_title: null, text: 'A take-home task.', years_experience: null, label: 'public_candidate_report', scope: 'lahore' }] })
    go('/app/companies/acme')
    expect(await screen.findByText('Role requirements')).toBeInTheDocument()
    expect(screen.getByText('How interviews are reported to work')).toBeInTheDocument()
    expect(screen.getByText('Unverified or outdated')).toBeInTheDocument()
    expect(screen.getByText('Public candidate report')).toBeInTheDocument()
    expect(screen.getByText('Location not stated')).toBeInTheDocument()
    expect(screen.getByText('2+ years')).toBeInTheDocument()
  })

  it('says when there is no reviewed information', async () => {
    go('/app/companies/acme')
    expect(await screen.findByText('No hiring information has been found yet.')).toBeInTheDocument()
  })

  it('compares a resume with a company and explains each skill', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.discoverRecommendations).mockResolvedValue(REC)
    vi.mocked(api.resumeFit).mockResolvedValue({
      ...FIT,
      company: { available: true, company: { slug: 'acme', name: 'Acme Software' }, role: 'Python Developer', coverage_stated: 0.5, coverage_with_inferred: 0.75, evidence_count: 2,
        skills: [{ skill: 'python', weight: 1, have: 'stated', reasons: ['Official source (2026-10-14)'], sources: [{ url: 'https://acme.example.com/careers/python', label: 'official_verified' }] }, { skill: 'git', weight: 0.5, have: null, reasons: ['Candidate report (2026-10-14)'], sources: [] }],
        notes: ['Weights: official source 1.0, candidate report 0.5, outdated or unverified 0.25.'] },
    })
    const user = userEvent.setup()
    go('/app/resume')
    await screen.findByRole('option', { name: 'Acme Software' })
    await user.selectOptions(await screen.findByLabelText('Lahore company (optional)'), 'acme')
    await user.selectOptions(screen.getByLabelText('Target role'), 'python-developer')
    expect(await screen.findByText('Compared with Acme Software')).toBeInTheDocument()
    expect(screen.getByText('Not in your resume')).toBeInTheDocument()
    expect(screen.getByText(/Official source \(2026-10-14\)/)).toBeInTheDocument()
    expect(api.resumeFit).toHaveBeenLastCalledWith('r1', 'python-developer', 'acme')
  })

  it('shows why company-specific comparison is unavailable', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.discoverRecommendations).mockResolvedValue(REC)
    vi.mocked(api.resumeFit).mockResolvedValue({ ...FIT, company: { available: false, reason: 'No approved company evidence applies to this role yet, so only the general comparison is shown.', company: { slug: 'acme', name: 'Acme Software' }, role: 'Python Developer' } })
    const user = userEvent.setup()
    go('/app/resume')
    await user.selectOptions(await screen.findByLabelText('Target role'), 'python-developer')
    await screen.findByRole('option', { name: 'Acme Software' })
    await user.selectOptions(screen.getByLabelText('Lahore company (optional)'), 'acme')
    expect(await screen.findByText(/No approved company evidence applies/)).toBeInTheDocument()
  })
})

const NOW = '2026-10-15T10:00:00Z'
const QS = [
  { id: 'q1', position: 1, type: 'mcq' as const, category: 'technical', prompt: 'Which statement about Python lists is accurate?', options: [{ index: 0, text: 'Lists are immutable' }, { index: 1, text: 'Lists are mutable' }, { index: 2, text: 'Lists cannot nest' }, { index: 3, text: 'Lists are sets' }], difficulty: 'easy', topic: 'python fundamentals', label: 'ai_generated_practice', informed_by: [], max_points: 1 },
  { id: 'q2', position: 2, type: 'short_answer' as const, category: 'company_informed', prompt: 'Explain how you would design a small REST API for orders.', options: [], difficulty: 'medium', topic: 'python design', label: 'ai_generated_practice', informed_by: [{ url: 'https://acme.example.com/careers', label: 'official_verified' }], max_points: 3 },
]
const ASSESS: Assessment = {
  id: 'a1', status: 'ready', mode: 'general', role: { slug: 'python-developer', title: 'Python Developer' }, company: null, notice: null, question_count: 2, duration_minutes: 30, created_at: NOW,
  started_at: null, deadline_at: null, submitted_at: null, auto_submitted: false, server_now: NOW, error_code: null, message: null, generation: { accepted: 2, target: 2, dropped: 3, warnings: [] }, score: null, questions: null, answers: null,
}
const RUNNING: Assessment = { ...ASSESS, status: 'in_progress', started_at: NOW, deadline_at: '2026-10-15T10:30:00Z', questions: QS, answers: [] }
const REVIEW: Review = {
  assessment: { ...ASSESS, status: 'submitted', submitted_at: NOW, score: { mcq_correct: 0, mcq_total: 1 } },
  questions: [
    { ...QS[0], correct_index: 1, reference_points: [], explanation: 'Lists can be changed after creation.', selected_index: 0, response_text: null, is_correct: false, needs_evaluation: false },
    { ...QS[1], correct_index: null, reference_points: ['Resources and verbs', 'Validation and errors'], explanation: 'Good APIs are predictable.', selected_index: null, response_text: 'I would use FastAPI.', is_correct: null, needs_evaluation: true },
  ],
  result: { mcq_correct: 0, mcq_total: 1, mcq_unanswered: 0, short_answered: 1, short_total: 1, evaluated: false, by_topic: [{ topic: 'python fundamentals', correct: 0, total: 1 }], note: 'Short answers are not scored yet.' },
}

describe('assessment setup', () => {
  it('asks for an analysed resume first', async () => {
    go('/app/assessment/setup')
    expect(await screen.findByText('Analyse a resume first')).toBeInTheDocument()
  })

  it('creates an assessment and opens its page', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.discoverCompanies).mockResolvedValue({ items: [DITEM] })
    vi.mocked(api.createAssessment).mockResolvedValue({ ...ASSESS, status: 'generating' })
    vi.mocked(api.assessment).mockResolvedValue({ ...ASSESS, status: 'generating' })
    const user = userEvent.setup()
    go('/app/assessment/setup')
    await user.selectOptions(await screen.findByLabelText('Lahore software house (optional)'), 'acme')
    await user.selectOptions(screen.getByLabelText('Number of questions'), '15')
    await user.click(screen.getByRole('button', { name: 'Write my assessment' }))
    await waitFor(() => expect(api.createAssessment).toHaveBeenCalledWith({ resume_id: 'r1', role: 'python-developer', company: 'acme', question_count: 15 }))
    expect(await screen.findByText(/Writing and checking your questions/)).toBeInTheDocument()
  })

  it('shows the server message when AI is not set up', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.createAssessment).mockRejectedValue(new ApiError(503, 'llm_not_configured', "AI isn't set up on this server yet, so assessments can't be written."))
    const user = userEvent.setup()
    go('/app/assessment/setup')
    await user.click(await screen.findByRole('button', { name: 'Write my assessment' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("AI isn't set up")
  })
})

describe('assessment page', () => {
  it('explains a failed generation honestly', async () => {
    vi.mocked(api.assessment).mockResolvedValue({ ...ASSESS, status: 'failed', error_code: 'insufficient_valid_questions', message: 'Too few questions passed our quality checks, so none were kept.' })
    go('/app/assessment/a1')
    expect(await screen.findByText(/Too few questions passed our quality checks/)).toBeInTheDocument()
  })

  it('shows the rules, honest labelling and a notice when company evidence was missing', async () => {
    vi.mocked(api.assessment).mockResolvedValue({ ...ASSESS, notice: 'No approved evidence about Acme Software applies to this role yet, so this is general role preparation.' })
    go('/app/assessment/a1')
    expect(await screen.findByText('General role preparation')).toBeInTheDocument()
    expect(screen.getByText(/No approved evidence about Acme Software/)).toBeInTheDocument()
    expect(screen.getByText(/Every question is AI-generated practice/)).toBeInTheDocument()
    expect(screen.getByText(/3 draft question\(s\) were discarded/)).toBeInTheDocument()
  })

  it('starts the test and opens the question page', async () => {
    vi.mocked(api.assessment).mockResolvedValueOnce(ASSESS).mockResolvedValue(RUNNING)
    vi.mocked(api.startAssessment).mockResolvedValue(RUNNING)
    const user = userEvent.setup()
    go('/app/assessment/a1')
    await user.click(await screen.findByRole('button', { name: 'Start now' }))
    expect(await screen.findByText('Which statement about Python lists is accurate?')).toBeInTheDocument()
  })

  it('sends finished assessments to their review', async () => {
    vi.mocked(api.assessment).mockResolvedValue({ ...ASSESS, status: 'submitted' })
    vi.mocked(api.reviewAssessment).mockResolvedValue(REVIEW)
    go('/app/assessment/a1')
    expect(await screen.findByRole('heading', { name: 'Your results' })).toBeInTheDocument()
  })
})

describe('taking the test', () => {
  const future = () => ({ ...RUNNING, server_now: new Date().toISOString(), deadline_at: new Date(Date.now() + 25 * 60_000).toISOString() })

  it('labels every question as AI-generated practice and never shows an answer key', async () => {
    vi.mocked(api.assessment).mockResolvedValue(future())
    go('/app/assessment/a1/take')
    expect(await screen.findByText('AI-generated practice')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent(/2[45]:\d\d/)
    expect(screen.queryByText(/correct answer/i)).not.toBeInTheDocument()
  })

  it('autosaves a selected option and can clear it', async () => {
    vi.mocked(api.assessment).mockResolvedValue(future())
    vi.mocked(api.saveAnswers).mockResolvedValue(future())
    const user = userEvent.setup()
    go('/app/assessment/a1/take')
    await user.click(await screen.findByRole('radio', { name: 'Lists are mutable' }))
    expect(screen.getByText('Unsaved changes…')).toBeInTheDocument()
    await waitFor(() => expect(api.saveAnswers).toHaveBeenCalledWith('a1', [{ question_id: 'q1', selected_index: 1, response_text: null }]), { timeout: 4000 })
    expect(await screen.findByText('All answers saved')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Clear my answer' }))
    await waitFor(() => expect(api.saveAnswers).toHaveBeenLastCalledWith('a1', [{ question_id: 'q1', selected_index: null, response_text: null }]), { timeout: 4000 })
  })

  it('restores saved answers, shows company sources for company-informed practice, and navigates', async () => {
    vi.mocked(api.assessment).mockResolvedValue({ ...future(), answers: [{ question_id: 'q1', selected_index: 1, response_text: null }] })
    const user = userEvent.setup()
    go('/app/assessment/a1/take')
    expect(await screen.findByRole('radio', { name: 'Lists are mutable' })).toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Next question' }))
    expect(await screen.findByText('Inspired by approved sources')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'acme.example.com' })).toBeInTheDocument()
    expect(screen.getByText(/It is not a question the company asked/)).toBeInTheDocument()
    expect(screen.getByText(/not scored yet/)).toBeInTheDocument()
  })

  it('keeps unsaved text and shows a retry message when saving fails', async () => {
    vi.mocked(api.assessment).mockResolvedValue(future())
    vi.mocked(api.saveAnswers).mockRejectedValue(new ApiError(0, 'network_error', 'Cannot reach the server.'))
    const user = userEvent.setup()
    go('/app/assessment/a1/take')
    await user.click(await screen.findByRole('button', { name: 'Next question' }))
    await user.type(screen.getByRole('textbox'), 'My draft answer')
    expect(await screen.findByText('Could not save. Retrying…', {}, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveValue('My draft answer')
  })

  it('asks for confirmation, counts blanks, then submits', async () => {
    vi.mocked(api.assessment).mockResolvedValue(future())
    vi.mocked(api.saveAnswers).mockResolvedValue(future())
    vi.mocked(api.submitAssessment).mockResolvedValue(REVIEW)
    vi.mocked(api.reviewAssessment).mockResolvedValue(REVIEW)
    const user = userEvent.setup()
    go('/app/assessment/a1/take')
    await user.click((await screen.findAllByRole('button', { name: 'Submit' }))[0])
    expect(await screen.findByText(/2 question\(s\) are not answered/)).toBeInTheDocument()
    expect(api.submitAssessment).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Submit now' }))
    await waitFor(() => expect(api.submitAssessment).toHaveBeenCalledWith('a1'))
    expect(await screen.findByRole('heading', { name: 'Your results' })).toBeInTheDocument()
  })

  it('submits automatically when the server deadline has passed', async () => {
    const past = { ...RUNNING, server_now: new Date().toISOString(), deadline_at: new Date(Date.now() - 1000).toISOString() }
    vi.mocked(api.assessment).mockResolvedValue(past)
    vi.mocked(api.submitAssessment).mockResolvedValue({ ...REVIEW, assessment: { ...REVIEW.assessment, auto_submitted: true } })
    vi.mocked(api.reviewAssessment).mockResolvedValue({ ...REVIEW, assessment: { ...REVIEW.assessment, auto_submitted: true } })
    go('/app/assessment/a1/take')
    await waitFor(() => expect(api.submitAssessment).toHaveBeenCalledTimes(1))
    expect(await screen.findByText(/submitted automatically/)).toBeInTheDocument()
  })

  it('follows the server clock rather than the laptop clock', async () => {
    const skewed = { ...RUNNING, server_now: new Date(Date.now() + 3_600_000).toISOString(), deadline_at: new Date(Date.now() + 3_600_000 + 10 * 60_000).toISOString() }
    vi.mocked(api.assessment).mockResolvedValue(skewed)
    go('/app/assessment/a1/take')
    await screen.findByRole('timer')
    await waitFor(() => expect(screen.getByRole('timer')).toHaveTextContent(/(09|10):\d\d/))
    expect(api.submitAssessment).not.toHaveBeenCalled()
  })

  it('goes to the review when the server says time expired while saving', async () => {
    vi.mocked(api.assessment).mockResolvedValue(future())
    vi.mocked(api.saveAnswers).mockRejectedValue(new ApiError(409, 'time_expired', 'Time ran out and the assessment was submitted automatically.'))
    vi.mocked(api.reviewAssessment).mockResolvedValue(REVIEW)
    const user = userEvent.setup()
    go('/app/assessment/a1/take')
    await user.click(await screen.findByRole('radio', { name: 'Lists are immutable' }))
    expect(await screen.findByRole('heading', { name: 'Your results' }, { timeout: 4000 })).toBeInTheDocument()
  })
})

describe('review and history', () => {
  it('shows objective scores, what was right, and that short answers are not scored', async () => {
    vi.mocked(api.reviewAssessment).mockResolvedValue(REVIEW)
    go('/app/assessment/a1/review')
    expect(await screen.findByText('0 / 1')).toBeInTheDocument()
    expect(screen.getByText('Incorrect')).toBeInTheDocument()
    expect(screen.getByText('Not scored yet')).toBeInTheDocument()
    expect(screen.getByText(/Lists are mutable.*\(correct answer\)/)).toBeInTheDocument()
    expect(screen.getByText('Resources and verbs')).toBeInTheDocument()
    expect(screen.getByText('I would use FastAPI.')).toBeInTheDocument()
    expect(screen.getAllByText('AI-generated practice')).toHaveLength(2)
  })

  it('says when the review is not available yet', async () => {
    vi.mocked(api.reviewAssessment).mockRejectedValue(new ApiError(409, 'not_submitted', 'Answers and explanations are shown after you submit.'))
    go('/app/assessment/a1/review')
    expect(await screen.findByText('Not submitted yet')).toBeInTheDocument()
  })

  it('lists assessments with scores and deletes after confirmation', async () => {
    vi.mocked(api.assessments).mockResolvedValueOnce([REVIEW.assessment, { ...ASSESS, id: 'a2', status: 'failed' }]).mockResolvedValue([])
    vi.mocked(api.deleteAssessment).mockResolvedValue(undefined)
    const user = userEvent.setup()
    go('/app/history')
    expect(await screen.findByText('0 / 1')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    await user.click(screen.getAllByRole('button', { name: 'Delete' })[0])
    expect(api.deleteAssessment).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Yes, delete' }))
    await waitFor(() => expect(api.deleteAssessment).toHaveBeenCalledWith('a1'))
    expect(await screen.findByText('No assessments yet')).toBeInTheDocument()
  })

  it('shows real recent results on the dashboard', async () => {
    vi.mocked(api.assessments).mockResolvedValue([REVIEW.assessment])
    go('/app')
    expect(await screen.findByText(/0\/1 multiple choice/)).toBeInTheDocument()
  })
})

const CP: CodingProblem = {
  slug: 'two-sum', title: 'Two Sum', difficulty: 'easy', minutes: 15, topics: ['arrays'], roles: ['python-developer'], statement: 'Given a list `nums` and a `target`, return the indices of the two numbers that add up to the target.\n\nExactly one pair exists.',
  constraints: ['2 <= len(nums) <= 10000'], signature: 'def two_sum(nums, target):', starter_code: 'def two_sum(nums, target):\n    pass\n', examples: [{ args: [[2, 7], 9], output: [0, 1], explanation: 'Because `2 + 7 = 9`.' }],
  visible_tests: [{ id: 'v1', args: [[2, 7], 9], expected: [0, 1] }], hidden_count: 7, per_test_ms: 2000, label: 'ai_generated_practice',
}
const CP2: CodingProblem = { ...CP, slug: 'valid-parentheses', title: 'Valid Parentheses', statement: 'Check that brackets are balanced and closed in the correct order.\n\nThe empty string is valid.', signature: 'def is_valid(s):', starter_code: 'def is_valid(s):\n    pass\n' }
const sNow = () => new Date().toISOString()
const SESSION = (over: Partial<CodingSession> = {}): CodingSession => ({
  id: 's1', status: 'in_progress', assessment_id: null, problem_slugs: ['two-sum', 'valid-parentheses'], problems: [CP, CP2], drafts: {}, progress: [{ problem: 'two-sum', runs: 0, submits: 0, last_submit: null }, { problem: 'valid-parentheses', runs: 0, submits: 0, last_submit: null }],
  started_at: sNow(), deadline_at: new Date(Date.now() + 30 * 60_000).toISOString(), submitted_at: null, auto_submitted: false, server_now: sNow(), runs_left: 30, submits_left: 5, ...over,
})
const SUB = (over: Partial<CodingSubmission> = {}): CodingSubmission => ({
  id: 'sub1', kind: 'run', problem: 'two-sum', status: 'not_executed', executed: false, compile_error: null, passed_count: null, total_count: 1, runtime_ms: null, runner_backend: 'mock',
  message: 'The code runner is a development mock, so your code was NOT run. There are no pass or fail results.', created_at: sNow(), feedback: null,
  results: [{ id: 'v1', hidden: false, label: 'Test v1', status: 'not_run', runtime_ms: null, args: [[2, 7], 9], expected: [0, 1], actual: null, error: null, stdout: null }], ...over,
})
const EXECUTED = SUB({
  kind: 'submit', status: 'completed', executed: true, passed_count: 1, total_count: 3, runtime_ms: 4.5,
  results: [
    { id: 'v1', hidden: false, label: 'Test v1', status: 'passed', runtime_ms: 1.5, args: [[2, 7], 9], expected: [0, 1], actual: '[0, 1]', error: null, stdout: null },
    { id: 'hidden-1', hidden: true, label: 'Hidden test 1', status: 'failed', runtime_ms: 1.5 },
    { id: 'hidden-2', hidden: true, label: 'Hidden test 2', status: 'timeout', runtime_ms: 2000 },
  ],
})

describe('coding practice list', () => {
  it('warns that the code runner is a mock and lists problems', async () => {
    go('/app/coding')
    expect(await screen.findByText(/Code runner not connected/)).toBeInTheDocument()
    expect(screen.getByText(/nothing is run or scored yet/)).toBeInTheDocument()
    expect(screen.getByText('Two Sum')).toBeInTheDocument()
    expect(screen.getByText(/not questions from any company/)).toBeInTheDocument()
  })

  it('starts a session with chosen problems, at most three', async () => {
    vi.mocked(api.createCodingSession).mockResolvedValue(SESSION())
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding')
    await user.click(await screen.findByRole('checkbox', { name: 'Select Two Sum' }))
    await user.click(screen.getByRole('button', { name: /Start with 1 problem/ }))
    await waitFor(() => expect(api.createCodingSession).toHaveBeenCalledWith({ problem_slugs: ['two-sum'] }))
    expect(await screen.findByRole('heading', { name: 'Two Sum' })).toBeInTheDocument()
  })

  it('starts a smart role challenge', async () => {
    vi.mocked(api.createCodingSession).mockResolvedValue(SESSION())
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding')
    await user.selectOptions(await screen.findByLabelText('Role'), 'python-developer')
    await user.click(screen.getByRole('button', { name: 'Start a coding challenge' }))
    await waitFor(() => expect(api.createCodingSession).toHaveBeenCalledWith({ role: 'python-developer', count: 3 }))
  })

  it('opens the session already in progress instead of failing', async () => {
    const err = new ApiError(409, 'session_in_progress', 'Finish or resume your current coding session first.')
    err.details = { session_id: 's1' } as never
    vi.mocked(api.createCodingSession).mockRejectedValue(err)
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding')
    await user.click(await screen.findByRole('checkbox', { name: 'Select Two Sum' }))
    await user.click(screen.getByRole('button', { name: /Start with 1 problem/ }))
    expect(await screen.findByRole('heading', { name: 'Two Sum' })).toBeInTheDocument()
  })

  it('shows an empty state with the admin command when the bank is empty', async () => {
    vi.mocked(api.codingProblems).mockResolvedValue([])
    go('/app/coding')
    expect(await screen.findByText('No problems yet')).toBeInTheDocument()
  })

  it('redirects the old sample coding address', async () => {
    go('/app/assessment/coding')
    expect(await screen.findByRole('heading', { name: 'Coding practice' })).toBeInTheDocument()
  })
})

describe('coding session', () => {
  beforeEach(() => { vi.mocked(api.codingSession).mockResolvedValue(SESSION()) })

  it('shows the problem, constraints, examples, honest label and mock banner', async () => {
    go('/app/coding/s1')
    expect(await screen.findByRole('heading', { name: 'Two Sum' })).toBeInTheDocument()
    expect(screen.getByText('2 <= len(nums) <= 10000')).toBeInTheDocument()
    expect(screen.getByText(/input: \[\[2,7\],9\]/)).toBeInTheDocument()
    expect(screen.getByText('AI-generated practice')).toBeInTheDocument()
    expect(screen.getByText(/Code runner not connected/)).toBeInTheDocument()
    expect(screen.getByText(/checks 7 hidden tests, which show only pass or fail/)).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent(/(29|30):\d\d/)
    expect(screen.getByLabelText('Python code editor')).toHaveValue('def two_sum(nums, target):\n    pass\n')
  })

  it('autosaves the draft and keeps separate code per problem', async () => {
    vi.mocked(api.saveCodingDraft).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding/s1')
    const editor = await screen.findByLabelText('Python code editor')
    await user.clear(editor)
    await user.type(editor, 'x = 1')
    await waitFor(() => expect(api.saveCodingDraft).toHaveBeenCalledWith('s1', 'two-sum', 'x = 1'), { timeout: 4000 })
    await user.click(screen.getByRole('tab', { name: /Valid Parentheses/ }))
    expect(await screen.findByRole('heading', { name: 'Valid Parentheses' })).toBeInTheDocument()
    expect(screen.getByLabelText('Python code editor')).toHaveValue('def is_valid(s):\n    pass\n')
    await user.click(screen.getByRole('tab', { name: /Two Sum/ }))
    expect(screen.getByLabelText('Python code editor')).toHaveValue('x = 1')
  })

  it('restores a saved draft', async () => {
    vi.mocked(api.codingSession).mockResolvedValue(SESSION({ drafts: { 'two-sum': 'def two_sum(a, b):\n    return [0, 1]\n' } }))
    go('/app/coding/s1')
    expect(await screen.findByLabelText('Python code editor')).toHaveValue('def two_sum(a, b):\n    return [0, 1]\n')
  })

  it('says plainly that nothing was run when the runner is the mock', async () => {
    vi.mocked(api.runCode).mockResolvedValue(SUB())
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Run' }))
    await waitFor(() => expect(api.runCode).toHaveBeenCalledWith('s1', 'two-sum', 'def two_sum(nums, target):\n    pass\n'))
    expect(await screen.findByText(/Nothing was run/)).toBeInTheDocument()
    expect(screen.getByText('none run', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('Not run')).toBeInTheDocument()
    expect(screen.queryByText(/passed$/)).not.toBeInTheDocument()
  })

  it('shows real results with visible details and hides everything about hidden tests', async () => {
    vi.mocked(api.submitCode).mockResolvedValue(EXECUTED)
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Submit' }))
    expect(await screen.findByText(/1 of 3 passed/)).toBeInTheDocument()
    expect(screen.getByText('Passed')).toBeInTheDocument()
    expect(screen.getByText('Hidden test 1')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('Timed out')).toBeInTheDocument()
    expect(screen.getAllByText(/Inputs and expected values of hidden tests are not shown/)).toHaveLength(2)
    expect(screen.getByText(/your output:/)).toBeInTheDocument()
  })

  it('shows compile errors', async () => {
    vi.mocked(api.runCode).mockResolvedValue(SUB({ executed: true, status: 'completed', passed_count: 0, compile_error: 'SyntaxError: bad (line 1)', message: null }))
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Run' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('SyntaxError: bad (line 1)')
  })

  it('explains runner and limit errors', async () => {
    vi.mocked(api.runCode).mockRejectedValue(new ApiError(503, 'runner_unavailable', 'The code runner is unavailable right now. Nothing was counted; try again shortly.'))
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Run' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('code runner is unavailable')
  })

  it('goes to the results when the server says time expired', async () => {
    vi.mocked(api.runCode).mockRejectedValue(new ApiError(409, 'time_expired', 'Time ran out and the session was submitted automatically.'))
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_NOT_RUN)
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Run' }))
    expect(await screen.findByRole('heading', { name: 'Coding results' })).toBeInTheDocument()
  })

  it('asks before finishing and lists what was not submitted', async () => {
    vi.mocked(api.finishCoding).mockResolvedValue(REVIEW_NOT_RUN)
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_NOT_RUN)
    const user = userEvent.setup()
    go('/app/coding/s1')
    await user.click(await screen.findByRole('button', { name: 'Finish session' }))
    expect(await screen.findByText(/Not submitted yet: Two Sum, Valid Parentheses/)).toBeInTheDocument()
    expect(api.finishCoding).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Finish now' }))
    await waitFor(() => expect(api.finishCoding).toHaveBeenCalledWith('s1'))
    expect(await screen.findByRole('heading', { name: 'Coding results' })).toBeInTheDocument()
  })

  it('finishes automatically when the server deadline has passed', async () => {
    vi.mocked(api.codingSession).mockResolvedValue(SESSION({ server_now: sNow(), deadline_at: new Date(Date.now() - 1000).toISOString() }))
    vi.mocked(api.finishCoding).mockResolvedValue(REVIEW_NOT_RUN)
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_NOT_RUN)
    go('/app/coding/s1')
    await waitFor(() => expect(api.finishCoding).toHaveBeenCalledTimes(1))
  })

  it('sends finished sessions to their review', async () => {
    vi.mocked(api.codingSession).mockResolvedValue(SESSION({ status: 'submitted', problems: null }))
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_NOT_RUN)
    go('/app/coding/s1')
    expect(await screen.findByRole('heading', { name: 'Coding results' })).toBeInTheDocument()
  })
})

const REVIEW_NOT_RUN: CodingReview = {
  session: SESSION({ status: 'submitted', problems: null, auto_submitted: false }),
  problems: [{ problem: CP, approach: 'Scan once and remember each value in a dictionary.', complexity: { time: 'O(n)', space: 'O(n)' }, reference_solution: 'def two_sum(nums, target):\n    seen = {}\n', final_code: 'def two_sum(nums, target):\n    return [0, 1]\n', runs: 1, submits: 1, submission: SUB({ kind: 'submit' }), passed_count: null, total_count: 8, solved: false }],
  summary: { solved: 0, problems: 1, tests_passed: null, tests_total: 8, executed: false, note: 'Not every problem was submitted to a code runner that executes code, so there is no complete correctness score.' },
}
const REVIEW_RUN: CodingReview = { ...REVIEW_NOT_RUN, problems: [{ ...REVIEW_NOT_RUN.problems[0], submission: EXECUTED, passed_count: 3, total_count: 3, solved: true }], summary: { solved: 1, problems: 1, tests_passed: 3, tests_total: 3, executed: true, note: 'Correctness is the number of tests your last submission passed, measured by the code runner.' } }

describe('coding review', () => {
  it('shows "not run" instead of a score when no code was executed', async () => {
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_NOT_RUN)
    go('/app/coding/s1/review')
    expect(await screen.findByText('Not run', { selector: 'p' })).toBeInTheDocument()
    expect(screen.getByText('n/a')).toBeInTheDocument()
    expect(screen.getByText(/no complete correctness score/)).toBeInTheDocument()
    expect(screen.getByText('Reference solution')).toBeInTheDocument()
    expect(screen.getByText(/Scan once and remember/)).toBeInTheDocument()
    expect(screen.getByText('Time O(n), space O(n)')).toBeInTheDocument()
  })

  it('shows objective scores when code was executed', async () => {
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_RUN)
    go('/app/coding/s1/review')
    expect(await screen.findByText('1 / 1')).toBeInTheDocument()
    expect(screen.getByText('3 / 3')).toBeInTheDocument()
    expect(screen.getByText('Solved')).toBeInTheDocument()
  })

  it('keeps AI commentary clearly labelled as subjective', async () => {
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_RUN)
    vi.mocked(api.codingFeedback).mockResolvedValue({ complexity: 'Time O(n).', strengths: ['Single pass'], improvements: ['Add a docstring'], readability: 'Clear names.', label: 'ai_commentary_subjective', note: 'Subjective AI commentary. It does not affect your test results.' })
    const user = userEvent.setup()
    go('/app/coding/s1/review')
    await user.click(await screen.findByRole('button', { name: /Get AI feedback/ }))
    expect(await screen.findByText('Subjective')).toBeInTheDocument()
    expect(screen.getByText(/does not affect your test results/)).toBeInTheDocument()
    expect(api.codingFeedback).toHaveBeenCalledWith('sub1')
  })

  it('shows a clear message when AI feedback is unavailable', async () => {
    vi.mocked(api.codingReview).mockResolvedValue(REVIEW_RUN)
    vi.mocked(api.codingFeedback).mockRejectedValue(new ApiError(503, 'llm_not_configured', "AI isn't set up on this server, so feedback isn't available."))
    const user = userEvent.setup()
    go('/app/coding/s1/review')
    await user.click(await screen.findByRole('button', { name: /Get AI feedback/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent("AI isn't set up")
  })

  it('is locked until the session is finished', async () => {
    vi.mocked(api.codingReview).mockRejectedValue(new ApiError(409, 'not_submitted', 'Solutions and explanations are shown after you finish the session.'))
    go('/app/coding/s1/review')
    expect(await screen.findByText('Not finished yet')).toBeInTheDocument()
  })

  it('starts a coding challenge from a finished assessment', async () => {
    vi.mocked(api.reviewAssessment).mockResolvedValue(REVIEW)
    vi.mocked(api.createCodingSession).mockResolvedValue(SESSION())
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/assessment/a1/review')
    await user.click(await screen.findByRole('button', { name: 'Continue to the coding challenge' }))
    await waitFor(() => expect(api.createCodingSession).toHaveBeenCalledWith({ assessment_id: 'a1', count: 2 }))
    expect(await screen.findByRole('heading', { name: 'Two Sum' })).toBeInTheDocument()
  })
})

describe('evidence labels', () => {
  it('shows human-readable labels', () => {
    render(<EvidenceBadge label="ai_generated_practice" />)
    expect(screen.getByText('AI-generated practice')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------- voice interview
type FakeRec = { lang: string; continuous: boolean; interimResults: boolean; onresult: ((e: unknown) => void) | null; onerror: ((e: { error: string }) => void) | null; onend: (() => void) | null; start: () => void; stop: () => void; abort: () => void }
let rec: FakeRec | null = null
function setSpeech(on: boolean) {
  const w = window as unknown as Record<string, unknown>
  rec = null
  if (on) {
    w.SpeechRecognition = class {
      lang = ''; continuous = false; interimResults = false
      onresult: FakeRec['onresult'] = null; onerror: FakeRec['onerror'] = null; onend: FakeRec['onend'] = null
      start = vi.fn(); abort = vi.fn()
      stop = vi.fn(() => this.onend?.())
      constructor() { rec = this as unknown as FakeRec }
    }
  } else { delete w.SpeechRecognition; delete w.webkitSpeechRecognition }
}
const T = (position: number, speaker: 'interviewer' | 'candidate', kind: 'opening' | 'question' | 'follow_up' | 'answer' | 'skipped' | 'closing', text: string, extra: object = {}) =>
  ({ id: `t${position}`, position, speaker, kind, text, topic: null, source: speaker === 'interviewer' ? 'ai' : 'typed', informed_by: [], created_at: '2026-10-24T00:00:00Z', ...extra }) as NonNullable<Interview['turns']>[number]
const IV = (over: Partial<Interview> = {}): Interview => ({
  id: 'i1', status: 'active', mode: 'general', role: { slug: 'python-developer', title: 'Python Developer' }, company: null, input_mode: 'text', question_target: 4, questions_asked: 1, answers_given: 0,
  awaiting_answer: true, label: 'ai_generated_practice', notice: 'Practice only. An AI writes the questions; they are not real questions from any company.', save_transcript: false, transcript_available: true,
  transcript_purged_at: null, evaluated: false, events: [], provider: 'groq', model: 'm', started_at: '2026-10-24T00:00:00Z', last_activity_at: '2026-10-24T00:00:00Z', ended_at: null,
  server_now: '2026-10-24T00:01:00Z', idle_minutes: 30,
  turns: [T(1, 'interviewer', 'opening', 'Hello, I am an AI interviewer.', { source: 'system' }), T(2, 'interviewer', 'question', 'Tell me about your project Sentiment Analyzer.')], ...over,
})
const EVAL: InterviewEvaluation = {
  rubric_version: 'voice-1', label: 'ai_evaluation_subjective', indicator: 62, answers_scored: 2, evidence_level: 'limited',
  criteria: [
    { key: 'technical_correctness', name: 'Technical correctness', description: '', score: 3, max: 4, rationale: 'Mostly accurate.', evidence_turns: [3], low_evidence: false },
    { key: 'specificity', name: 'Specificity and evidence', description: '', score: 1, max: 4, rationale: 'Few concrete details.', evidence_turns: [], low_evidence: true },
  ],
  strengths: ['Clear design choice.'], improvements: ['Describe testing.'], per_answer: [{ turn: 3, question: 'Tell me about your project.', note: 'Good detail.', stronger_answer_hint: 'Name a result.' }],
  caveats: ['Scores are subjective AI judgements of the text of your answers, not test results and not a prediction of hiring decisions.'], provider: 'groq', model: 'm', created_at: '2026-10-24T00:00:00Z', injection_signals: [], transcript_kept: true,
}

describe('voice interview setup', () => {
  it('keeps Start disabled until consent is given, and sends consent with the request', async () => {
    const user = userEvent.setup()
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.createInterview).mockResolvedValue(IV())
    vi.mocked(api.interview).mockResolvedValue(IV())
    go('/app/interview')
    const start = await screen.findByRole('button', { name: 'Start interview' })
    await waitFor(() => expect(screen.getByLabelText('Resume')).toHaveValue('r1'))
    expect(start).toBeDisabled()
    await user.click(screen.getByRole('checkbox', { name: /I have read the privacy notice/ }))
    expect(start).toBeEnabled()
    await user.click(start)
    await waitFor(() => expect(api.createInterview).toHaveBeenCalledWith(expect.objectContaining({ resume_id: 'r1', role: 'python-developer', consent: true, input_mode: 'text', save_transcript: false })))
    expect(await screen.findByRole('heading', { name: 'Interview room' })).toBeInTheDocument()
  })

  it('states the privacy facts and warns when there is no analysed resume', async () => {
    go('/app/interview')
    expect(await screen.findByText('No analysed resume yet')).toBeInTheDocument()
    expect(screen.getByText(/can't see you and does not assess your face, voice/)).toBeInTheDocument()
    expect(screen.getByText(/some browsers send the audio to the browser vendor/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start interview' })).toBeDisabled()
  })

  it('disables speaking when the browser has no speech recognition', async () => {
    go('/app/interview')
    expect(await screen.findByRole('radio', { name: /Speaking/ })).toBeDisabled()
    expect(screen.getByText(/not supported in this browser/)).toBeInTheDocument()
  })

  it('offers to continue an interview in progress', async () => {
    vi.mocked(api.interviews).mockResolvedValue([IV()])
    go('/app/interview')
    expect(await screen.findByRole('link', { name: 'Continue it' })).toHaveAttribute('href', '/app/interview/i1')
  })

  it('shows the server error when starting fails', async () => {
    const user = userEvent.setup()
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.createInterview).mockRejectedValue(new ApiError(503, 'llm_not_configured', "AI isn't set up on this server yet, so interviews can't run."))
    go('/app/interview')
    await waitFor(() => expect(screen.getByLabelText('Resume')).toHaveValue('r1'))
    await user.click(screen.getByRole('checkbox', { name: /I have read the privacy notice/ }))
    await user.click(screen.getByRole('button', { name: 'Start interview' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("AI isn't set up")
  })
})

describe('interview room', () => {
  it('shows the honest label, the transcript and the current question', async () => {
    vi.mocked(api.interview).mockResolvedValue(IV())
    go('/app/interview/i1')
    expect(await screen.findByRole('heading', { name: 'Interview room' })).toBeInTheDocument()
    expect(screen.getByText('AI-generated practice')).toBeInTheDocument()
    expect(screen.getByText('Tell me about your project Sentiment Analyzer.')).toBeInTheDocument()
    expect(screen.getByText(/Question 1 of 4/)).toBeInTheDocument()
    expect(screen.getByText(/not real questions from any company/)).toBeInTheDocument()
  })

  it('sends a typed answer, shows the follow-up, and keeps the answer if sending fails', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interview).mockResolvedValue(IV())
    go('/app/interview/i1')
    const box = await screen.findByLabelText(/Your answer/)
    await user.type(box, 'I used FastAPI and Redis.')
    vi.mocked(api.answerInterview).mockRejectedValueOnce(new ApiError(429, 'rate_limited', 'Too many interview requests. Try again later.'))
    await user.click(screen.getByRole('button', { name: /Send answer/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Too many interview requests')
    expect(box).toHaveValue('I used FastAPI and Redis.')
    vi.mocked(api.answerInterview).mockResolvedValue(IV({ questions_asked: 1, answers_given: 1, turns: [...IV().turns!, T(3, 'candidate', 'answer', 'I used FastAPI and Redis.'), T(4, 'interviewer', 'follow_up', 'Why did you choose Redis over memory?')] }))
    await user.click(screen.getByRole('button', { name: /Send answer/ }))
    expect(await screen.findByText('Why did you choose Redis over memory?')).toBeInTheDocument()
    expect(api.answerInterview).toHaveBeenLastCalledWith('i1', { text: 'I used FastAPI and Redis.', source: 'typed' })
    expect(screen.getByText('Follow-up')).toBeInTheDocument()
    expect(box).toHaveValue('')
  })

  it('lets the candidate skip, and labels built-in fallback questions and cited evidence', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interview).mockResolvedValue(IV({ turns: [T(1, 'interviewer', 'opening', 'Hello.'), T(2, 'interviewer', 'question', 'A built-in question about SQL?', { source: 'fallback', informed_by: [{ n: 1, url: 'https://acme.example.com/careers', label: 'official_verified' }] })] }))
    vi.mocked(api.answerInterview).mockResolvedValue(IV())
    go('/app/interview/i1')
    expect(await screen.findByText('Built-in question')).toBeInTheDocument()
    expect(screen.getByText('Officially verified').closest('a')).toHaveAttribute('href', 'https://acme.example.com/careers')
    await user.click(screen.getByRole('button', { name: /Skip question/ }))
    expect(api.answerInterview).toHaveBeenCalledWith('i1', { skip: true })
  })

  it('ends the interview and goes to the feedback page', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interview).mockResolvedValue(IV())
    vi.mocked(api.endInterview).mockResolvedValue(IV({ status: 'completed' }))
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: IV({ status: 'completed', awaiting_answer: false, answers_given: 1 }), evaluation: null })
    go('/app/interview/i1')
    await user.click(await screen.findByRole('button', { name: 'End interview' }))
    expect(await screen.findByRole('heading', { name: 'Interview feedback' })).toBeInTheDocument()
  })

  it('offers resume for an interrupted interview', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interview).mockResolvedValue(IV({ status: 'interrupted', awaiting_answer: false }))
    vi.mocked(api.resumeInterview).mockResolvedValue(IV())
    go('/app/interview/i1')
    expect(await screen.findByText(/interrupted after 30 minutes/)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Your answer/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Resume' }))
    expect(await screen.findByLabelText(/Your answer/)).toBeInTheDocument()
  })

  it('shows not-found for someone else\'s or a missing interview', async () => {
    vi.mocked(api.interview).mockRejectedValue(new ApiError(404, 'not_found', 'Interview not found.'))
    go('/app/interview/zzz')
    expect(await screen.findByRole('heading', { name: 'Interview not found' })).toBeInTheDocument()
  })

  it('falls back to typing and tells the server when speech recognition is unsupported', async () => {
    vi.mocked(api.interview).mockResolvedValue(IV({ input_mode: 'voice' }))
    vi.mocked(api.interviewEvent).mockResolvedValue(IV({ input_mode: 'text', events: [{ kind: 'speech_unsupported', at: 'x' }] }))
    go('/app/interview/i1')
    await waitFor(() => expect(api.interviewEvent).toHaveBeenCalledWith('i1', 'speech_unsupported'))
    expect(await screen.findByLabelText(/Your answer/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Speak my answer/ })).not.toBeInTheDocument()
  })

  it('puts recognised speech in the box for checking, never sending it automatically', async () => {
    const user = userEvent.setup()
    setSpeech(true)
    vi.mocked(api.interview).mockResolvedValue(IV({ input_mode: 'voice' }))
    go('/app/interview/i1')
    await user.click(await screen.findByRole('button', { name: /Speak my answer/ }))
    expect(rec!.start).toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /Stop listening/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('status')).toHaveTextContent(/Listening/)
    act(() => rec!.onresult!({ results: [[{ transcript: 'I built it with fast API' }]].map(r => Object.assign(r, { isFinal: true })) }))
    const box = screen.getByLabelText(/Your answer/)
    expect(box).toHaveValue('I built it with fast API')
    expect(api.answerInterview).not.toHaveBeenCalled()
    await user.clear(box); await user.type(box, 'I built it with FastAPI')
    vi.mocked(api.answerInterview).mockResolvedValue(IV())
    await user.click(screen.getByRole('button', { name: /Send answer/ }))
    expect(api.answerInterview).toHaveBeenCalledWith('i1', { text: 'I built it with FastAPI', source: 'typed' })
  })

  it('handles microphone denial by switching to typing', async () => {
    const user = userEvent.setup()
    setSpeech(true)
    vi.mocked(api.interview).mockResolvedValue(IV({ input_mode: 'voice' }))
    vi.mocked(api.interviewEvent).mockResolvedValue(IV({ input_mode: 'text', events: [{ kind: 'mic_denied', at: 'x' }] }))
    go('/app/interview/i1')
    await user.click(await screen.findByRole('button', { name: /Speak my answer/ }))
    act(() => rec!.onerror!({ error: 'not-allowed' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/Microphone access was blocked/)
    expect(api.interviewEvent).toHaveBeenCalledWith('i1', 'mic_denied')
    await waitFor(() => expect(screen.queryByRole('button', { name: /Speak my answer/ })).not.toBeInTheDocument())
    expect(screen.getByLabelText(/Your answer/)).toBeEnabled()
  })

  it('reports a speech error and a quiet microphone differently', async () => {
    const user = userEvent.setup()
    setSpeech(true)
    vi.mocked(api.interview).mockResolvedValue(IV({ input_mode: 'voice' }))
    vi.mocked(api.interviewEvent).mockResolvedValue(IV({ input_mode: 'voice' }))
    go('/app/interview/i1')
    await user.click(await screen.findByRole('button', { name: /Speak my answer/ }))
    act(() => rec!.onerror!({ error: 'no-speech' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/didn't hear anything/)
    expect(api.interviewEvent).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: /Speak my answer/ }))
    act(() => rec!.onerror!({ error: 'network' }))
    await waitFor(() => expect(api.interviewEvent).toHaveBeenCalledWith('i1', 'speech_error'))
  })

  it('shows the completed state with a link to feedback', async () => {
    vi.mocked(api.interview).mockResolvedValue(IV({ status: 'completed', awaiting_answer: false, turns: [...IV().turns!, T(3, 'interviewer', 'closing', 'That is the end.', { source: 'system' })] }))
    go('/app/interview/i1')
    expect(await screen.findByText(/The interview is complete/)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Your answer/)).not.toBeInTheDocument()
  })
})

describe('interview feedback', () => {
  const done = IV({ status: 'completed', awaiting_answer: false, answers_given: 2, save_transcript: true, evaluated: true, turns: [...IV().turns!, T(3, 'candidate', 'answer', 'I used FastAPI.')] })

  it('shows scores with their evidence, caveats and honest labels', async () => {
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: done, evaluation: EVAL })
    go('/app/interview/i1/review')
    expect(await screen.findByText('62 / 100')).toBeInTheDocument()
    expect(screen.getByText('AI judgement, subjective')).toBeInTheDocument()
    expect(screen.getByText('Limited evidence')).toBeInTheDocument()
    expect(screen.getByText(/not test results and not a prediction of hiring decisions/)).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Technical correctness' })).toHaveAttribute('aria-valuenow', '3')
    expect(screen.getByText('Cites no specific answer')).toBeInTheDocument()
    expect(screen.getByText('Show your answer (turn 3)')).toBeInTheDocument()
    expect(screen.getByText('A stronger answer could: Name a result.')).toBeInTheDocument()
    expect(screen.getByText('AI-written practice questions')).toBeInTheDocument()
  })

  it('asks for feedback only once the interview is over and shows server errors', async () => {
    const user = userEvent.setup()
    const ended = IV({ status: 'completed', awaiting_answer: false, answers_given: 2 })
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: ended, evaluation: null })
    vi.mocked(api.evaluateInterview).mockRejectedValueOnce(new ApiError(502, 'evaluation_failed', "The AI returned something we couldn't validate. Nothing was saved; try again."))
    go('/app/interview/i1/review')
    await user.click(await screen.findByRole('button', { name: 'Get feedback on my answers' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("couldn't validate")
    vi.mocked(api.evaluateInterview).mockResolvedValue({ interview: { ...ended, evaluated: true }, evaluation: EVAL })
    await user.click(screen.getByRole('button', { name: 'Get feedback on my answers' }))
    expect(await screen.findByText('62 / 100')).toBeInTheDocument()
  })

  it('blocks feedback when there are no answers or the transcript is gone', async () => {
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: IV({ status: 'completed', answers_given: 0, awaiting_answer: false }), evaluation: null })
    go('/app/interview/i1/review')
    expect(await screen.findByText(/nothing to evaluate/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Get feedback on my answers' })).toBeDisabled()
  })

  it('explains a transcript that was not kept, while scores remain', async () => {
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: { ...done, save_transcript: false, transcript_available: false, transcript_purged_at: 'x', turns: null }, evaluation: { ...EVAL, transcript_kept: false } })
    go('/app/interview/i1/review')
    expect(await screen.findByText(/transcript was not kept, as you chose/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Delete transcript' })).not.toBeInTheDocument()
  })

  it('deletes the transcript only after confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: done, evaluation: EVAL })
    vi.mocked(api.deleteInterviewTranscript).mockResolvedValue({ ...done, transcript_available: false, turns: null, transcript_purged_at: 'x' })
    go('/app/interview/i1/review')
    await user.click(await screen.findByRole('button', { name: 'Delete transcript' }))
    expect(api.deleteInterviewTranscript).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Yes, delete the transcript' }))
    await waitFor(() => expect(api.deleteInterviewTranscript).toHaveBeenCalledWith('i1'))
    expect(await screen.findByText(/transcript was deleted/)).toBeInTheDocument()
  })

  it('deletes the whole interview after confirmation and returns to the list', async () => {
    const user = userEvent.setup()
    vi.mocked(api.interviewReview).mockResolvedValue({ interview: done, evaluation: EVAL })
    vi.mocked(api.deleteInterview).mockResolvedValue(undefined)
    go('/app/interview/i1/review')
    await user.click(await screen.findByRole('button', { name: 'Delete this interview' }))
    await user.click(screen.getByRole('button', { name: 'Yes, delete this interview' }))
    expect(await screen.findByRole('heading', { name: 'Voice interview' })).toBeInTheDocument()
    expect(api.deleteInterview).toHaveBeenCalledWith('i1')
  })
})

// ---------------------------------------------------------------- results and reports
const COMP = (over: Partial<Report['components'][number]>): Report['components'][number] => ({
  key: 'technical_knowledge', name: 'Technical knowledge', kind: 'objective', weight: 0.35, status: 'available', value: 70, reason: '7 of 10 multiple-choice questions correct.', low_evidence: false, detail: {}, sources: [], how: 'Multiple-choice questions answered correctly.', ...over,
})
const REPORT = (over: Partial<Report> = {}): Report => ({
  id: 'rp1', created_at: '2026-10-24T00:00:00Z', role: { slug: 'python-developer', title: 'Python Developer' }, company: null, mode: 'general', horizon: 7, rubric_version: 'report-1', rubric: { version: 'report-1', overall: '' },
  sources_used: {}, components: [
    COMP({}),
    COMP({ key: 'coding_correctness', name: 'Coding correctness', status: 'not_run', value: null, reason: 'The code runner did not execute your code, so there is no correctness score. Nothing was guessed.' }),
    COMP({ key: 'interview_performance', name: 'Interview performance', kind: 'subjective', weight: 0.3, value: 62, low_evidence: true, reason: 'Average of the four interview criteria; AI judgement of the text of your answers.' }),
    COMP({ key: 'complexity_analysis', name: 'Complexity analysis', kind: 'subjective', weight: 0, status: 'not_scored', value: null, reason: 'Not scored in this version.' }),
  ],
  overall: { value: 67, included: ['technical_knowledge', 'interview_performance'], subjective_share: 46, how: 'Weighted average of the components that exist.', note: 'Based on 2 of 3 scored components; the rest are missing (see below).', limited: true, missing: [{ key: 'coding_correctness', name: 'Coding correctness', status: 'not_run', reason: 'The code runner did not execute your code.' }] },
  gaps: [{ label: 'SQL', severity: 'high', kind: 'objective', evidence: [{ source: 'assessment', detail: '1 of 4 correct' }] }, { label: 'Reasoning', severity: 'medium', kind: 'subjective', evidence: [{ source: 'interview', detail: 'Scored 1 of 4 by the AI interview evaluation' }] }],
  strengths: [{ label: 'Python', kind: 'objective', source: 'assessment', evidence: '4 of 4 correct' }],
  practice_questions: [{ type: 'question', prompt: 'What does a JOIN do?', topic: 'SQL', label: 'ai_generated_practice' }, { type: 'coding', title: 'Two Sum', slug: 'two-sum', label: 'ai_generated_practice' }],
  sources: [], roadmap: { source: 'built_in', horizon: 7, note: 'A built-in plan made from your gaps.', items: [{ when: 'Day 1', focus: 'SQL', tasks: ['Redo the questions you missed on SQL.', 'Explain SQL in five sentences.'], minutes: 60 }] },
  notes: ['The interview rested on fewer than three answers, so its scores are limited evidence.'], previous: null,
  disclaimer: 'Scores are preparation indicators, not guarantees of selection or hiring.', provider: '', model: '', ...over,
})
const SRC: ReportSources = {
  assessments: [{ id: 'a1', created_at: '2026-10-20T00:00:00Z', mode: 'general', mcq_correct: 7, mcq_total: 10 }],
  coding_sessions: [{ id: 'c1', created_at: '2026-10-21T00:00:00Z', problems: 1, executed: false, tests_passed: null, tests_total: 8 }],
  interviews: [{ id: 'i1', created_at: '2026-10-22T00:00:00Z', answers_given: 3, evaluated: true, indicator: 62 }],
  resumes: [{ id: 'r1', filename: 'cv.pdf' }],
}

describe('results page', () => {
  it('explains when nothing is finished yet', async () => {
    go('/app/results')
    expect(await screen.findByText('Nothing finished for this role yet')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create report' })).toBeDisabled()
    expect(screen.getByText('No scored reports yet.')).toBeInTheDocument()
  })

  it('builds a report from the chosen results, warns about unexecuted code, and opens it', async () => {
    const user = userEvent.setup()
    vi.mocked(api.reportSources).mockResolvedValue(SRC)
    vi.mocked(api.createReport).mockResolvedValue(REPORT())
    vi.mocked(api.report).mockResolvedValue(REPORT())
    go('/app/results')
    const a = await screen.findByLabelText('Assessment')
    expect(screen.getByRole('option', { name: /code was not executed/ })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByLabelText(/Resume \(for the fit score\)/)).toHaveValue('r1'))
    expect(screen.getByRole('button', { name: 'Create report' })).toBeDisabled()
    await user.selectOptions(a, 'a1')
    await user.selectOptions(screen.getByLabelText('Interview'), 'i1')
    await user.selectOptions(screen.getByLabelText('Improvement plan'), '30')
    await user.click(screen.getByRole('button', { name: 'Create report' }))
    await waitFor(() => expect(api.createReport).toHaveBeenCalledWith({ role: 'python-developer', horizon: 30, assessment_id: 'a1', coding_session_id: undefined, interview_id: 'i1', resume_id: 'r1' }))
    expect(await screen.findByRole('heading', { name: 'Report' })).toBeInTheDocument()
  })

  it('shows the server error when a report cannot be created', async () => {
    const user = userEvent.setup()
    vi.mocked(api.reportSources).mockResolvedValue(SRC)
    vi.mocked(api.createReport).mockRejectedValue(new ApiError(409, 'not_evaluated', 'Get feedback on the interview before using it in a report.'))
    go('/app/results')
    await user.selectOptions(await screen.findByLabelText('Interview'), 'i1')
    await user.click(screen.getByRole('button', { name: 'Create report' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Get feedback on the interview')
  })

  it('lists reports and charts progress from real data only when there are two scored points', async () => {
    vi.mocked(api.reports).mockResolvedValue([
      { id: 'rp1', created_at: '2026-10-24T00:00:00Z', role: { slug: 'python-developer', title: 'Python Developer' }, company: null, mode: 'general', horizon: 7, overall: 67, scores: {}, included: [], missing: ['coding_correctness'] },
      { id: 'rp0', created_at: '2026-10-20T00:00:00Z', role: { slug: 'python-developer', title: 'Python Developer' }, company: { slug: 'acme', name: 'Acme Software' }, mode: 'company', horizon: 7, overall: null, scores: {}, included: [], missing: [] },
    ])
    vi.mocked(api.reportProgress).mockResolvedValue({ series: [{ report_id: 'rp0', created_at: '2026-10-20T00:00:00Z', role: 'python-developer', overall: 50, scores: {} }, { report_id: 'rp1', created_at: '2026-10-24T00:00:00Z', role: 'python-developer', overall: 67, scores: {} }], latest_change: 17, note: 'Compare trends, not single points.' })
    go('/app/results')
    expect(await screen.findByText('Overall 67')).toBeInTheDocument()
    expect(screen.getByText('No overall score')).toBeInTheDocument()
    expect(screen.getByText('1 missing')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Open' })[0]).toHaveAttribute('href', '/app/results/rp1')
    expect(screen.getByRole('img', { name: /over 2 reports/ })).toBeInTheDocument()
    expect(screen.getByText('Compare trends, not single points.')).toBeInTheDocument()
  })
})

describe('report view', () => {
  it('keeps measured results apart from AI judgement and says what is missing or not run', async () => {
    vi.mocked(api.report).mockResolvedValue(REPORT())
    go('/app/results/rp1')
    expect(await screen.findByText('67 / 100')).toBeInTheDocument()
    expect(screen.getByText('46% AI judgement')).toBeInTheDocument()
    const measured = within(screen.getByRole('list', { name: 'Measured results' }))
    const judged = within(screen.getByRole('list', { name: 'AI judgement' }))
    expect(measured.getByText('Technical knowledge')).toBeInTheDocument()
    expect(measured.getByText('Not run')).toBeInTheDocument()
    expect(measured.getByText(/Nothing was guessed/)).toBeInTheDocument()
    expect(measured.queryByText('Interview performance')).not.toBeInTheDocument()
    expect(judged.getByText('Interview performance')).toBeInTheDocument()
    expect(judged.getByText('Limited evidence')).toBeInTheDocument()
    expect(judged.getByText('Not scored')).toBeInTheDocument()
    expect(screen.getByText(/Based on 2 of 3 scored components/)).toBeInTheDocument()
    expect(screen.getByText(/The code runner did not execute your code\./)).toBeInTheDocument()
    expect(screen.getByText(/not guarantees of selection or hiring/)).toBeInTheDocument()
  })

  it('shows gaps with severity and evidence, strengths, and labelled practice', async () => {
    vi.mocked(api.report).mockResolvedValue(REPORT())
    go('/app/results/rp1')
    expect(await screen.findByText('1 of 4 correct')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('measured')).toBeInTheDocument()
    expect(screen.getAllByText('AI judgement').length).toBeGreaterThan(1)
    expect(screen.getByText('Scored 1 of 4 by the AI interview evaluation')).toBeInTheDocument()
    expect(screen.getByText('4 of 4 correct', { exact: false })).toBeInTheDocument()
    const practice = within(screen.getByRole('list', { name: 'Practice suggestions' }))
    expect(practice.getByText('What does a JOIN do?')).toBeInTheDocument()
    expect(practice.getByText('Coding: Two Sum')).toBeInTheDocument()
    expect(practice.getAllByText('AI-generated practice')).toHaveLength(2)
  })

  it('shows the 7-day plan, says who wrote it, and switches to 30 days', async () => {
    const user = userEvent.setup()
    vi.mocked(api.report).mockResolvedValue(REPORT())
    vi.mocked(api.reportRoadmap).mockResolvedValue(REPORT({ horizon: 30, roadmap: { source: 'ai', horizon: 30, note: 'Written by an AI from your gap list, then checked.', items: [{ when: 'Week 1', focus: 'SQL', tasks: ['Practise joins.', 'Write three queries.'], minutes: 90 }] } }))
    go('/app/results/rp1')
    expect(await screen.findByRole('heading', { name: '7-day improvement plan' })).toBeInTheDocument()
    expect(screen.getByText('Built-in plan')).toBeInTheDocument()
    expect(within(screen.getByRole('list', { name: 'Improvement plan' })).getByText('Day 1: SQL')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '7 days' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: '30 days' }))
    expect(api.reportRoadmap).toHaveBeenCalledWith('rp1', 30)
    expect(await screen.findByRole('heading', { name: '30-day improvement plan' })).toBeInTheDocument()
    expect(screen.getByText('Written by AI, checked')).toBeInTheDocument()
    expect(screen.getByText('Week 1: SQL')).toBeInTheDocument()
  })

  it('compares with the previous report and tells you not to over-read it', async () => {
    vi.mocked(api.report).mockResolvedValue(REPORT({ previous: { report_id: 'rp0', created_at: '2026-10-20T00:00:00Z', overall_before: 50, overall_after: 67, overall_delta: 17, components: [{ key: 'technical_knowledge', before: 50, after: 70, delta: 20 }], note: 'Each attempt uses different questions, so small changes are not meaningful.' } }))
    go('/app/results/rp1')
    expect(await screen.findByText(/Overall: 50 to 67 \(\+17\)/)).toBeInTheDocument()
    expect(screen.getByText('Technical knowledge: 50 to 70 (+20)')).toBeInTheDocument()
    expect(screen.getByText(/different questions/)).toBeInTheDocument()
  })

  it('cites only approved company research, with labels and links', async () => {
    vi.mocked(api.report).mockResolvedValue(REPORT({ mode: 'company', company: { slug: 'acme', name: 'Acme Software' }, sources: [{ url: 'https://acme.example.com/careers', label: 'official_verified', kind: 'role_requirement', role_title: 'Python Developer', text: 'Needs Python and SQL.' }] }))
    go('/app/results/rp1')
    const link = await screen.findByRole('link', { name: 'https://acme.example.com/careers' })
    expect(link).toHaveAttribute('href', 'https://acme.example.com/careers')
    expect(screen.getByText('Officially verified')).toBeInTheDocument()
  })

  it('handles a report with no score, no gaps and no strengths', async () => {
    vi.mocked(api.report).mockResolvedValue(REPORT({ overall: { value: null, included: [], subjective_share: 0, how: '', note: 'No scored component is available yet, so there is no overall indicator.', limited: true, missing: [] }, gaps: [], strengths: [], practice_questions: [] }))
    go('/app/results/rp1')
    expect(await screen.findByText('No score yet')).toBeInTheDocument()
    expect(screen.getByText(/No gaps were found/)).toBeInTheDocument()
    expect(screen.getByText(/No clear strengths yet/)).toBeInTheDocument()
  })

  it('shows not-found, and deletes only after confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(api.report).mockRejectedValueOnce(new ApiError(404, 'not_found', 'Report not found.'))
    go('/app/results/zzz')
    expect(await screen.findByRole('heading', { name: 'Report not found' })).toBeInTheDocument()
    vi.mocked(api.report).mockResolvedValue(REPORT())
    vi.mocked(api.deleteReport).mockResolvedValue(undefined)
    go('/app/results/rp1')
    await user.click(await screen.findByRole('button', { name: 'Delete report' }))
    expect(api.deleteReport).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Yes, delete this report' }))
    expect(await screen.findByRole('heading', { name: 'Results' })).toBeInTheDocument()
    expect(api.deleteReport).toHaveBeenCalledWith('rp1')
  })

  it('shows an error when the plan cannot be changed', async () => {
    const user = userEvent.setup()
    vi.mocked(api.report).mockResolvedValue(REPORT())
    vi.mocked(api.reportRoadmap).mockRejectedValue(new ApiError(429, 'rate_limited', 'Too many requests. Try again later.'))
    go('/app/results/rp1')
    await user.click(await screen.findByRole('button', { name: '30 days' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Too many requests')
  })
})

describe('dashboard with reports', () => {
  it('shows real skill gaps from the latest report and a next action, with no sample labels', async () => {
    vi.mocked(api.resumes).mockResolvedValue([ANALYSED])
    vi.mocked(api.reports).mockResolvedValue([{ id: 'rp1', created_at: '2026-10-24T00:00:00Z', role: { slug: 'python-developer', title: 'Python Developer' }, company: null, mode: 'general', horizon: 7, overall: 67, scores: {}, included: [], missing: [] }])
    vi.mocked(api.report).mockResolvedValue(REPORT())
    vi.mocked(api.assessments).mockResolvedValue([])
    go('/app')
    expect(await screen.findByText('SQL')).toBeInTheDocument()
    expect(screen.getByText('Reasoning')).toBeInTheDocument()
    expect(screen.queryByText(/sample/i)).not.toBeInTheDocument()
  })

  it('says gaps appear after a report when there is none yet', async () => {
    go('/app')
    expect(await screen.findByText('Gaps appear here after you create a report.')).toBeInTheDocument()
    expect(screen.getByText(/Upload a resume to unlock/)).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------- change password
describe('change password', () => {
  const fill = async (user: ReturnType<typeof userEvent.setup>, cur: string, next: string, again: string) => {
    await user.type(await screen.findByLabelText('Current password'), cur)
    await user.type(screen.getByLabelText(/New password/), next)
    await user.type(screen.getByLabelText('Repeat the new password'), again)
  }

  it('changes the password, clears the fields and says other devices were signed out', async () => {
    const user = userEvent.setup()
    vi.mocked(api.changePassword).mockResolvedValue(undefined)
    go('/app/settings')
    await fill(user, 'old password 1', 'new password 22', 'new password 22')
    await user.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByText(/Your other devices were signed out/)).toBeInTheDocument()
    expect(api.changePassword).toHaveBeenCalledWith('old password 1', 'new password 22')
    expect(screen.getByLabelText('Current password')).toHaveValue('')
    expect(screen.getByLabelText(/New password/)).toHaveValue('')
  })

  it('checks length and matching in the browser before calling the server', async () => {
    const user = userEvent.setup()
    go('/app/settings')
    await fill(user, 'old password 1', 'short', 'short')
    await user.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('at least 8 characters')
    await user.clear(screen.getByLabelText(/New password/)); await user.clear(screen.getByLabelText('Repeat the new password'))
    await user.type(screen.getByLabelText(/New password/), 'new password 22'); await user.type(screen.getByLabelText('Repeat the new password'), 'another one 333')
    await user.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('do not match')
    expect(api.changePassword).not.toHaveBeenCalled()
  })

  it('shows the server message for a wrong current password and keeps what was typed', async () => {
    const user = userEvent.setup()
    vi.mocked(api.changePassword).mockRejectedValue(new ApiError(403, 'wrong_password', 'Your current password is incorrect.'))
    go('/app/settings')
    await fill(user, 'not it', 'new password 22', 'new password 22')
    await user.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('current password is incorrect')
    expect(screen.getByLabelText(/New password/)).toHaveValue('new password 22')
  })

  it('keeps the button disabled until all three fields are filled', async () => {
    go('/app/settings')
    expect(await screen.findByRole('button', { name: 'Change password' })).toBeDisabled()
  })
})

describe('smart coding challenge', () => {
  it('sends the chosen software house to the API and explains focus is not real company data', async () => {
    vi.mocked(api.createCodingSession).mockResolvedValue(SESSION())
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding')
    await screen.findByRole('option', { name: 'NetSol Technologies' })
    await user.selectOptions(await screen.findByLabelText('Role'), 'python-developer')
    await user.selectOptions(screen.getByLabelText('Software house (optional)'), 'netsol-technologies')
    expect(screen.getByText(/not real company questions/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Start a coding challenge' }))
    await waitFor(() => expect(api.createCodingSession).toHaveBeenCalledWith({ role: 'python-developer', count: 3, company: 'netsol-technologies' }))
  })
})

describe('question bank', () => {
  it('filters by company, labels every question as practice and reveals the ideal answer on request', async () => {
    vi.mocked(api.bankStats).mockResolvedValue({ total: 25, companies: [{ slug: 'arbisoft', name: 'Arbisoft', total: 25, kind: {}, difficulty: {}, source: {} }], source: {} })
    vi.mocked(api.bankQuestions).mockResolvedValue({ total: 1, source_titles: {}, items: [{ slug: 'arbisoft-tech-01', kind: 'technical', category: 'python', difficulty: 'easy', roles: ['python-developer'], companies: ['arbisoft'], topics: [], prompt: 'What is the difference between a list and a tuple?', options: [], source_label: 'company_focused_practice', source_title: 'Company-focused practice' }] })
    vi.mocked(api.bankReveal).mockResolvedValue({ slug: 'arbisoft-tech-01', ideal_answer: 'A list is mutable and a tuple is not.', key_points: ['Mutable vs immutable'], follow_ups: [], answer_index: null, explanation: '', source_label: 'company_focused_practice', source_note: '' })
    const user = userEvent.setup()
    go('/app/questions')
    expect(await screen.findByText(/not the company's real interview questions/)).toBeInTheDocument()
    await screen.findByRole('option', { name: /Arbisoft/ })
    await user.selectOptions(screen.getByLabelText('Company'), 'arbisoft')
    await waitFor(() => expect(api.bankQuestions).toHaveBeenCalledWith(expect.objectContaining({ company: 'arbisoft' })))
    expect(await screen.findByText('Company-focused practice')).toBeInTheDocument()
    expect(screen.queryByText(/A list is mutable/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Show ideal answer' }))
    expect(await screen.findByText(/A list is mutable and a tuple is not/)).toBeInTheDocument()
  })
})

describe('online screening', () => {
  const Q = { slug: 'scr-001-python', kind: 'output', category: 'python', difficulty: 'easy', roles: [], companies: [], topics: [], prompt: 'What does this Python program print?\n\n```python\nprint([1, 2, 3] * 2)\n```', options: ['[1, 2, 3, 1, 2, 3]', '[2, 4, 6]', '[1, 2, 3, 2]'], source_label: 'company_focused_practice', source_title: '' }
  const S = (over = {}) => ({ id: 's1', status: 'in_progress', company: null, role: 'python-developer', level: 'mixed', started_at: new Date().toISOString(), deadline_at: new Date(Date.now() + 600000).toISOString(), server_now: new Date().toISOString(), total: 1, answered: 0, questions: [Q], answers: {} as Record<string, number>, ...over })

  it('starts a test with the chosen company and level', async () => {
    vi.mocked(api.screeningSessions).mockResolvedValue([])
    vi.mocked(api.createScreening).mockResolvedValue(S())
    vi.mocked(api.screeningSession).mockResolvedValue(S())
    const user = userEvent.setup()
    go('/app/screening')
    await screen.findByRole('option', { name: 'Python Developer' })
    await screen.findByRole('option', { name: 'NetSol Technologies' })
    await user.selectOptions(screen.getByLabelText('Role'), 'python-developer')
    await user.selectOptions(screen.getByLabelText('Software house (optional)'), 'netsol-technologies')
    await user.selectOptions(screen.getByLabelText('Difficulty'), 'easy')
    await user.click(screen.getByRole('button', { name: 'Start test' }))
    await waitFor(() => expect(api.createScreening).toHaveBeenCalledWith({ role: 'python-developer', level: 'easy', count: 20, company: 'netsol-technologies' }))
  })

  it('shows the code, saves a chosen answer and warns before submitting unanswered questions', async () => {
    vi.mocked(api.screeningSession).mockResolvedValue(S())
    vi.mocked(api.screeningAnswer).mockResolvedValue(S({ answers: { 'scr-001-python': 0 }, answered: 1 }))
    const user = userEvent.setup()
    go('/app/screening/s1')
    expect(await screen.findByText('print([1, 2, 3] * 2)')).toBeInTheDocument()
    await user.click(screen.getByLabelText('[1, 2, 3, 1, 2, 3]'))
    await waitFor(() => expect(api.screeningAnswer).toHaveBeenCalledWith('s1', 'scr-001-python', 0))
    expect(screen.getByRole('timer')).toBeInTheDocument()
  })

  it('shows the score, the next step and the explanation after submitting', async () => {
    vi.mocked(api.screeningReview).mockResolvedValue({ session: { id: 's1', status: 'submitted', company: null, role: 'python-developer', level: 'mixed', submitted_at: new Date().toISOString(), correct: 0, total: 1, score: 0 }, auto_submitted: false, by_category: [{ name: 'python', correct: 0, total: 1, score: 0 }], by_difficulty: [{ name: 'easy', correct: 0, total: 1, score: 0 }], next_step: { message: 'Build the basics first with easy questions.', weak_categories: ['python'] }, review: [{ slug: 'scr-001-python', category: 'python', difficulty: 'easy', kind: 'output', prompt: Q.prompt, options: Q.options, chosen: null, answer_index: 0, correct: false, explanation: 'Multiplying a list repeats its items.' }], note: 'Scored by fixed rules.' })
    go('/app/screening/s1/result')
    expect(await screen.findByText('0%')).toBeInTheDocument()
    expect(screen.getByText('Build the basics first with easy questions.')).toBeInTheDocument()
    expect(screen.getByText('Skipped')).toBeInTheDocument()
    expect(screen.getByText('Multiplying a list repeats its items.')).toBeInTheDocument()
    expect(screen.getByText('correct answer')).toBeInTheDocument()
  })
})

describe('company readiness', () => {
  it('shows how the score is built, leaves unassessed parts out and never claims a hiring probability', async () => {
    const comp = (key: string, name: string, value: number | null, w: number, eff: number) => ({ key, name, weight: w, effective_weight: eff, how: `how ${key}`, status: value === null ? 'not_assessed' : 'available', value, reason: value === null ? 'No result yet.' : '', evidence_count: value === null ? 0 : 1 })
    vi.mocked(api.readiness).mockResolvedValue({ company: { slug: 'arbisoft', name: 'Arbisoft', focus: ['strings'], note: 'n' }, role: { slug: 'python-developer', title: 'Python Developer' }, resume: null, overall: { value: 62, label: 'Good match', confidence: 'limited', explanation: 'Weighted average.' }, evidence_count: 1, components: [comp('skill_match', 'Skill match', 70, 15, 33), comp('screening', 'Online screening', 55, 20, 44), comp('coding_correctness', 'Coding', null, 25, 0)], strengths: [], weak_areas: [], skill_gap: [{ skill: 'python', importance: 'required', status: 'weak', status_text: 'Weak (assessed)', score: 30, evidence_source: 'screening', on_resume: true, category: 'python' }, { skill: 'docker', importance: 'preferred', status: 'not_shown', status_text: 'Not assessed and not on resume', score: null, evidence_source: null, on_resume: false, category: 'cloud' }], next_actions: [{ type: 'coding', text: 'Do a smart coding challenge for this company.', why: 'No coding result yet.', params: {} }], suggested_coding: [], suggested_questions: [], disclaimer: 'This is an internal preparation estimate. It is not a hiring probability.' })
    vi.mocked(api.readinessRoles).mockResolvedValue({ items: [], has_resume: true, disclaimer: '' })
    vi.mocked(api.readinessCompanies).mockResolvedValue({ role: 'Python Developer', items: [], has_resume: true, disclaimer: '', focus_note: '' })
    const user = userEvent.setup()
    go('/app/readiness')
    expect(await screen.findByText(/not a hiring probability/i)).toBeInTheDocument()
    await screen.findByRole('option', { name: 'Python Developer' })
    await user.selectOptions(screen.getByLabelText('Role'), 'python-developer')
    expect(await screen.findByText('62%')).toBeInTheDocument()
    expect(screen.getByText('Good match')).toBeInTheDocument()
    expect(screen.getByText('Not assessed')).toBeInTheDocument()
    expect(screen.getByText('0% (left out)')).toBeInTheDocument()
    expect(screen.getByText(/Weak \(assessed\) 30%/)).toBeInTheDocument()
    expect(screen.getByText('Do a smart coding challenge for this company.')).toBeInTheDocument()
    await waitFor(() => expect(api.readiness).toHaveBeenCalledWith({ role: 'python-developer' }))
  })
})

describe('manage questions (admin)', () => {
  const Q = { id: 'q1', slug: 'arbisoft-tech-01', kind: 'technical', category: 'python', difficulty: 'easy', roles: ['python-developer'], companies: ['arbisoft'], topics: [], prompt: 'What is the difference between a list and a tuple in Python?', ideal_answer: 'A list is mutable and a tuple is not.', key_points: ['Mutable', 'Hashable'], follow_ups: [], options: [], answer_index: null, explanation: '', source_label: 'company_focused_practice', source_note: '', enabled: true }

  it('is hidden from normal users', async () => {
    go('/app/admin/questions')
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Manage questions/ })).not.toBeInTheDocument()
  })

  it('lets an admin disable a question and shows the server message when a new one is rejected', async () => {
    vi.mocked(api.me).mockResolvedValue(ADMIN)
    vi.mocked(api.adminQuestions).mockResolvedValue({ total: 1, items: [Q] })
    vi.mocked(api.adminUpdateQuestion).mockResolvedValue({ ...Q, enabled: false })
    vi.mocked(api.adminCreateQuestion).mockRejectedValue(new ApiError(422, 'invalid_question', 'a technical question needs an ideal answer and at least 2 key points'))
    const user = userEvent.setup()
    go('/app/admin/questions')
    expect(await screen.findByText('arbisoft-tech-01')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Disable' }))
    await waitFor(() => expect(api.adminUpdateQuestion).toHaveBeenCalledWith('arbisoft-tech-01', { enabled: false }))
    await user.click(screen.getByRole('button', { name: 'Add question' }))
    await user.type(screen.getByLabelText('Slug'), 'arbisoft-tech-30')
    await user.type(screen.getByLabelText('Question'), 'Explain what a Python list comprehension is.')
    await user.click(screen.getByRole('button', { name: 'Save question' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('at least 2 key points')
    expect(api.adminCreateQuestion).toHaveBeenCalledWith(expect.objectContaining({ slug: 'arbisoft-tech-30', kind: 'technical', source_label: 'company_focused_practice' }))
  })
})

describe('dashboard recommendations', () => {
  it('shows the best roles and companies with the preparation-estimate wording', async () => {
    vi.mocked(api.readinessRoles).mockResolvedValue({ has_resume: true, disclaimer: '', items: [{ role: { slug: 'python-developer', title: 'Python Developer' }, value: 71, label: 'Good match', confidence: 'limited', evidence_count: 1, matching_skills: ['python'], missing_required: [] }] })
    vi.mocked(api.readinessCompanies).mockResolvedValue({ role: 'Python Developer', has_resume: true, disclaimer: '', focus_note: '', items: [{ company: { slug: 'arbisoft', name: 'Arbisoft' }, value: 74, label: 'Good match', confidence: 'limited', evidence_count: 1, matching_skills: ['python'], missing_required: [] }] })
    go('/app')
    expect(await screen.findByText('Recommended for you')).toBeInTheDocument()
    expect(await screen.findByText(/Arbisoft: 74%/)).toBeInTheDocument()
    expect(screen.getByText(/not a hiring probability/)).toBeInTheDocument()
    await waitFor(() => expect(api.readinessCompanies).toHaveBeenCalledWith({ role: 'python-developer' }))
  })
})

describe('company coding set', () => {
  it('shows the 25-problem set of the chosen company and can start a session from it', async () => {
    vi.mocked(api.createCodingSession).mockResolvedValue(SESSION())
    vi.mocked(api.codingSession).mockResolvedValue(SESSION())
    const user = userEvent.setup()
    go('/app/coding')
    await screen.findByRole('option', { name: 'NetSol Technologies' })
    await user.selectOptions(await screen.findByLabelText('Role'), 'python-developer')
    await user.selectOptions(screen.getByLabelText('Software house (optional)'), 'netsol-technologies')
    expect(await screen.findByText(/practice set: 25 problems \(10 easy, 10 medium, 5 hard\), 1 solved/)).toBeInTheDocument()
    await user.click(screen.getByLabelText(/Take the problems from this company's set/))
    await user.click(screen.getByRole('button', { name: 'Start a coding challenge' }))
    await waitFor(() => expect(api.createCodingSession).toHaveBeenCalledWith({ role: 'python-developer', count: 3, company: 'netsol-technologies', company_set: true }))
  })
})
