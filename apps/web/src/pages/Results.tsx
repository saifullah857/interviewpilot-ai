import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge, Button, Card, EmptyState, ErrorState, LinkButton, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type Progress, type ReportSources, type ReportSummary } from '../lib/api'

const date = (s: string) => new Date(s).toLocaleDateString('en-GB')

export default function Results() {
  const nav = useNavigate()
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [role, setRole] = useState('')
  const [reports, setReports] = useState<ReportSummary[] | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [src, setSrc] = useState<ReportSources | null>(null)
  const [sel, setSel] = useState({ assessment: '', coding: '', interview: '', resume: '' })
  const [horizon, setHorizon] = useState<7 | 30>(7)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    api.roles().then(r => { setRoles(r); if (r[0]) setRole(r[0].slug) }).catch(() => setRoles([]))
    api.reports().then(setReports).catch(e => setLoadError(e instanceof ApiError ? e.message : 'Could not load your reports.'))
    api.reportProgress().then(setProgress).catch(() => setProgress(null))
  }, [])
  useEffect(() => {
    if (!role) return
    setSrc(null); setSel({ assessment: '', coding: '', interview: '', resume: '' })
    api.reportSources(role).then(s => { setSrc(s); setSel(x => ({ ...x, resume: s.resumes[0]?.id ?? '' })) }).catch(() => setSrc({ assessments: [], coding_sessions: [], interviews: [], resumes: [] }))
  }, [role])

  const chosen = !!(sel.assessment || sel.coding || sel.interview)
  async function create() {
    setBusy(true); setError('')
    try {
      const r = await api.createReport({ role, horizon, assessment_id: sel.assessment || undefined, coding_session_id: sel.coding || undefined, interview_id: sel.interview || undefined, resume_id: sel.resume || undefined })
      nav(`/app/results/${r.id}`)
    } catch (e) { setError(e instanceof ApiError ? e.message : 'Could not create the report.'); setBusy(false) }
  }

  if (loadError) return <ErrorState>{loadError}</ErrorState>
  if (!reports) return <Spinner label="Loading your results" />
  const points = (progress?.series ?? []).filter(p => p.overall !== null).map((p, i) => ({ attempt: i + 1, overall: p.overall, date: date(p.created_at) }))
  const none = !src || (src.assessments.length + src.coding_sessions.length + src.interviews.length === 0)
  return (
    <>
      <PageHeader title="Results" intro="Reports combine your finished assessments, coding sessions and interviews. Measured results and AI judgements are kept apart. They are preparation indicators, not hiring predictions." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Create a report</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Select id="rp-role" label="Target role" value={role} onChange={e => setRole(e.target.value)}>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
            <Select id="rp-days" label="Improvement plan" value={horizon} onChange={e => setHorizon(Number(e.target.value) as 7 | 30)}><option value={7}>7 days</option><option value={30}>30 days</option></Select>
          </div>
          {!src ? <p className="mt-3 text-sm text-ink-soft">Loading finished work…</p> : none ? (
            <div className="mt-3"><EmptyState title="Nothing finished for this role yet" action={<LinkButton to="/app/assessment/setup">Start practising</LinkButton>}>Finish an assessment, a coding session or an interview with feedback for this role first.</EmptyState></div>
          ) : (
            <div className="mt-3 grid gap-3">
              <Select id="rp-a" label="Assessment" value={sel.assessment} onChange={e => setSel({ ...sel, assessment: e.target.value })}><option value="">None</option>{src.assessments.map(a => <option key={a.id} value={a.id}>{date(a.created_at)}: {a.mcq_correct}/{a.mcq_total} multiple choice{a.mode === 'company' ? ' (company)' : ''}</option>)}</Select>
              <Select id="rp-c" label="Coding session" value={sel.coding} onChange={e => setSel({ ...sel, coding: e.target.value })}><option value="">None</option>{src.coding_sessions.map(c => <option key={c.id} value={c.id}>{date(c.created_at)}: {c.problems} problem(s), {c.executed ? `${c.tests_passed}/${c.tests_total} tests passed` : 'code was not executed'}</option>)}</Select>
              <Select id="rp-i" label="Interview" value={sel.interview} onChange={e => setSel({ ...sel, interview: e.target.value })}><option value="">None</option>{src.interviews.map(i => <option key={i.id} value={i.id}>{date(i.created_at)}: {i.answers_given ?? '?'} answers, indicator {i.indicator ?? 'n/a'}</option>)}</Select>
              <Select id="rp-r" label="Resume (for the fit score)" value={sel.resume} onChange={e => setSel({ ...sel, resume: e.target.value })}><option value="">None</option>{src.resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}</Select>
            </div>
          )}
          {error && <p role="alert" className="mt-3 text-sm text-bad">{error}</p>}
          <Button className="mt-4" disabled={!chosen || busy} onClick={create}>Create report</Button>
          <p className="mt-2 text-xs text-ink-mute">Anything you leave out is shown as missing, never guessed.</p>
        </Card>
        <Card>
          <h2 className="mb-2 font-semibold">Progress over reports</h2>
          {points.length < 2 ? <p className="text-sm text-ink-soft">{points.length === 0 ? 'No scored reports yet.' : 'Create one more report to see a trend.'}</p> : (
            <>
              <div className="h-56" role="img" aria-label={`Line chart of overall preparation indicator over ${points.length} reports`}>
                <ResponsiveContainer width="100%" height="100%"><LineChart data={points}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="attempt" tick={{ fontSize: 12 }} /><YAxis domain={[0, 100]} /><Tooltip /><Line dataKey="overall" stroke="#B84A0D" strokeWidth={2} /></LineChart></ResponsiveContainer>
              </div>
              <p className="mt-2 text-xs text-ink-mute">{progress?.note}</p>
            </>
          )}
        </Card>
      </div>
      <h2 className="mb-2 mt-8 text-lg font-semibold">Your reports</h2>
      {reports.length === 0 ? <p className="text-sm text-ink-soft">No reports yet.</p> : (
        <ul className="divide-y divide-line rounded-xl border border-line bg-surface" aria-label="Reports">
          {reports.map(r => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
              <span><b>{r.role.title}</b>{r.company ? ` · ${r.company.name}` : ' · general'} · {date(r.created_at)}</span>
              <span className="flex items-center gap-2">
                <Badge tone={r.overall === null ? 'neutral' : 'brand'}>{r.overall === null ? 'No overall score' : `Overall ${r.overall}`}</Badge>
                {r.missing.length > 0 && <Badge tone="warn">{r.missing.length} missing</Badge>}
                <Link className="font-semibold text-info underline" to={`/app/results/${r.id}`}>Open</Link>
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
