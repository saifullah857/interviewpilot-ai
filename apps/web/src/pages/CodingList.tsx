import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type CodingProblemSummary, type CodingSessionSummary, type CompanyFocus, type CompanySet, type ResumeItem, type RunnerStatus } from '../lib/api'

const TONE: Record<string, 'ok' | 'warn' | 'bad'> = { easy: 'ok', medium: 'warn', hard: 'bad' }

export default function CodingList() {
  const nav = useNavigate()
  const [problems, setProblems] = useState<CodingProblemSummary[] | null>(null)
  const [sessions, setSessions] = useState<CodingSessionSummary[]>([])
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [runner, setRunner] = useState<RunnerStatus | null>(null)
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [resumeId, setResumeId] = useState('')
  const [companies, setCompanies] = useState<CompanyFocus[]>([])
  const [disclaimer, setDisclaimer] = useState('')
  const [resumes, setResumes] = useState<ResumeItem[]>([])
  const [useSet, setUseSet] = useState(false)
  const [setView, setSetView] = useState<CompanySet | null>(null)
  const [picked, setPicked] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.codingRunner().then(setRunner).catch(() => setRunner(null))
    api.roles().then(setRoles).catch(() => setRoles([]))
    api.codingSessions().then(setSessions).catch(() => setSessions([]))
    api.codingCompanies().then(r => { setCompanies(r.companies); setDisclaimer(r.disclaimer) }).catch(() => setCompanies([]))
    api.resumes().then(setResumes).catch(() => setResumes([]))
  }, [])
  useEffect(() => {
    if (!company) { setSetView(null); setUseSet(false); return }
    api.codingCompanySet(company, role || undefined).then(setSetView).catch(() => setSetView(null))
  }, [company, role])
  useEffect(() => { api.codingProblems({ role }).then(setProblems).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load problems.')) }, [role])

  async function start(body: Parameters<typeof api.createCodingSession>[0]) {
    setBusy(true); setError('')
    try { const s = await api.createCodingSession(body); nav(`/app/coding/${s.id}`) }
    catch (e) {
      if (e instanceof ApiError && e.code === 'session_in_progress') { const id = (e.details as unknown as { session_id?: string } | undefined)?.session_id; if (id) { nav(`/app/coding/${id}`); return } }
      setError(e instanceof ApiError ? e.message : 'Could not start.'); setBusy(false)
    }
  }
  const toggle = (slug: string) => setPicked(p => (p.includes(slug) ? p.filter(x => x !== slug) : p.length < 3 ? [...p, slug] : p))

  if (error && !problems) return <ErrorState>{error}</ErrorState>
  if (!problems) return <Spinner label="Loading problems" />
  return (
    <>
      <PageHeader title="Coding practice" intro="Timed Python problems. Visible tests show you what is checked; hidden tests are checked when you submit." />
      {runner && !runner.executes_code && (
        <p role="status" className="mb-4 rounded-lg bg-warn-soft p-3 text-sm text-warn"><b>Code runner not connected.</b> {runner.message} You can read problems and write code, but nothing is run or scored yet.</p>
      )}
      {runner && runner.executes_code && !runner.reachable && <p role="alert" className="mb-4 rounded-lg bg-bad-soft p-3 text-sm text-bad">{runner.message}</p>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
            <div className="w-64"><Select id="cr" label="Show problems for" value={role} onChange={e => setRole(e.target.value)}><option value="">All roles</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select></div>
            <Button disabled={picked.length === 0 || busy} onClick={() => start({ problem_slugs: picked })}>Start with {picked.length || 'selected'} problem{picked.length === 1 ? '' : 's'}</Button>
          </div>
          {problems.length === 0 ? <EmptyState title="No problems yet">Ask an admin to run <code>python -m app.cli import-problems</code>.</EmptyState> : (
            <ul className="divide-y divide-line" aria-label="Problems">
              {problems.map(p => (
                <li key={p.slug} className="flex items-start gap-3 py-3">
                  <input type="checkbox" className="mt-1" aria-label={`Select ${p.title}`} checked={picked.includes(p.slug)} onChange={() => toggle(p.slug)} />
                  <div className="flex-1"><p className="font-medium">{p.title}</p><div className="mt-1 flex flex-wrap gap-1.5"><Badge tone={TONE[p.difficulty]}>{p.difficulty}</Badge><Badge>{p.minutes} min</Badge>{p.topics.map(t => <Badge key={t} tone="neutral">{t}</Badge>)}{(p.ds ?? []).filter(x => ['list', 'tuple', 'dict', 'set'].includes(x)).length >= 3 && <Badge tone="info">{(p.ds ?? []).filter(x => ['list', 'tuple', 'dict', 'set'].includes(x)).join(' + ')}</Badge>}</div></div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-ink-mute">Choose up to 3. These are general practice problems written for InterviewPilot AI, not questions from any company.</p>
        </Card>
        <div className="space-y-4">
          <Card>
            <h2 className="font-semibold">Smart challenge</h2>
            <p className="mt-1 text-sm text-ink-soft">Three problems for your role. Pick a software house to practise its usual focus, and a resume so the problems follow your skills.</p>
            <div className="mt-3 space-y-3">
              <Select id="qs" label="Role" value={role} onChange={e => setRole(e.target.value)}><option value="">Choose a role</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
              <Select id="qc" label="Software house (optional)" value={company} onChange={e => setCompany(e.target.value)}><option value="">Any / general</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select>
              <Select id="qr" label="Resume (optional)" value={resumeId} onChange={e => setResumeId(e.target.value)}><option value="">Do not use a resume</option>{resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}</Select>
            </div>
            {company && <p className="mt-2 text-xs text-ink-soft">Focus: {companies.find(c => c.slug === company)?.focus.join(', ')}</p>}
            {setView && (
              <details className="mt-3 rounded-lg border border-line p-3 text-sm">
                <summary className="cursor-pointer font-medium">{setView.company.name} practice set: {setView.total} problems ({setView.counts.easy ?? 0} easy, {setView.counts.medium ?? 0} medium, {setView.counts.hard ?? 0} hard), {setView.solved} solved</summary>
                <ol className="mt-2 list-decimal space-y-1 pl-5">{setView.problems.map(p => <li key={p.slug}>{p.solved ? '✓ ' : ''}{p.title} <Badge tone={p.difficulty === 'easy' ? 'ok' : p.difficulty === 'medium' ? 'warn' : 'bad'}>{p.difficulty}</Badge>{p.why.length > 0 && <span className="text-xs text-ink-mute"> {p.why.join(', ')}</span>}</li>)}</ol>
              </details>
            )}
            {company && role && <label className="mt-3 flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={useSet} onChange={e => setUseSet(e.target.checked)} /><span>Take the problems from this company's set and skip the ones I have already solved</span></label>}
            <Button className="mt-3 w-full" disabled={!role || busy} onClick={() => start({ role, count: 3, ...(company ? { company } : {}), ...(resumeId ? { resume_id: resumeId } : {}), ...(useSet && company ? { company_set: true } : {}) })}>Start a coding challenge</Button>
            {disclaimer && <p className="mt-2 text-xs text-ink-mute">{disclaimer}</p>}
            {error && <p role="alert" className="mt-2 text-sm text-bad">{error}</p>}
          </Card>
          <Card>
            <h2 className="mb-2 font-semibold">Your sessions</h2>
            {sessions.length === 0 ? <p className="text-sm text-ink-soft">None yet.</p> : (
              <ul className="space-y-2 text-sm">
                {sessions.slice(0, 6).map(s => (
                  <li key={s.id} className="flex items-center justify-between gap-2">
                    <Link className="text-info underline" to={s.status === 'submitted' ? `/app/coding/${s.id}/review` : `/app/coding/${s.id}`}>{s.problem_slugs.join(', ')}</Link>
                    <Badge tone={s.status === 'submitted' ? 'ok' : 'info'}>{s.status === 'submitted' ? (s.executed ? `${s.score ?? 0}% · ${s.tests_passed}/${s.tests_total} tests` : 'not run') : 'in progress'}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}
