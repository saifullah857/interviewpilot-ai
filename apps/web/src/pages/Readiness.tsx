import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge, Card, EmptyState, ErrorState, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type CompanyFocus, type MatchRow, type ResumeItem, type Readiness as R } from '../lib/api'

const TONE: Record<string, 'ok' | 'warn' | 'bad' | 'neutral'> = { good: 'ok', improve: 'warn', weak: 'bad', resume_only: 'neutral', not_shown: 'neutral' }
const LINK: Record<string, string> = { screening: '/app/screening', coding: '/app/coding', interview: '/app/interview', assessment: '/app/assessment/setup', resume: '/app/resume' }

function Table({ title, rows, nameOf, onPick }: { title: string; rows: MatchRow[]; nameOf: (r: MatchRow) => string; onPick?: (r: MatchRow) => void }) {
  return (
    <Card className="overflow-x-auto">
      <h2 className="mb-2 font-semibold">{title}</h2>
      <table className="w-full text-left text-sm"><caption className="sr-only">{title}</caption>
        <thead className="text-ink-mute"><tr><th className="py-1 font-medium">Name</th><th className="font-medium">Estimate</th><th className="font-medium">Matching skills</th><th className="font-medium">Missing required</th></tr></thead>
        <tbody>{rows.map(r => (
          <tr key={nameOf(r)} className="border-t border-line align-top">
            <td className="py-1 pr-2">{onPick ? <button className="text-info underline" onClick={() => onPick(r)}>{nameOf(r)}</button> : nameOf(r)}</td>
            <td className="pr-2">{r.value === null ? '-' : `${r.value}%`}<span className="block text-xs text-ink-mute">{r.label}</span></td>
            <td className="pr-2">{r.matching_skills.join(', ') || '-'}</td><td>{r.missing_required.join(', ') || '-'}</td>
          </tr>))}</tbody>
      </table>
    </Card>
  )
}

export default function Readiness() {
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [companies, setCompanies] = useState<CompanyFocus[]>([])
  const [resumes, setResumes] = useState<ResumeItem[]>([])
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [resumeId, setResumeId] = useState('')
  const [rep, setRep] = useState<R | null>(null)
  const [roleRows, setRoleRows] = useState<MatchRow[]>([])
  const [companyRows, setCompanyRows] = useState<MatchRow[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.roles().then(setRoles).catch(() => setRoles([]))
    api.codingCompanies().then(r => setCompanies(r.companies)).catch(() => setCompanies([]))
    api.resumes().then(setResumes).catch(() => setResumes([]))
  }, [])
  useEffect(() => {
    if (!role) { setRep(null); return }
    const p: Record<string, string> = { role, ...(company ? { company } : {}), ...(resumeId ? { resume_id: resumeId } : {}) }
    const q: Record<string, string> = { ...(resumeId ? { resume_id: resumeId } : {}) }
    setBusy(true); setError('')
    Promise.all([api.readiness(p), api.readinessRoles({ ...q, ...(company ? { company } : {}) }), api.readinessCompanies({ role, ...q })])
      .then(([a, b, c]) => { setRep(a); setRoleRows(b.items); setCompanyRows(c.items) })
      .catch(e => setError(e instanceof ApiError ? e.message : 'Could not calculate readiness.'))
      .finally(() => setBusy(false))
  }, [role, company, resumeId])

  const ov = rep?.overall
  return (
    <>
      <PageHeader title="Company readiness" intro="Pick a role and, if you like, a software house. The numbers come from your own resume and results and show exactly how they were calculated." />
      <p className="mb-4 rounded-lg border border-line bg-canvas p-3 text-sm text-ink-soft">This is a preparation estimate, <b>not a hiring probability</b> and not a promise of selection. Company focus comes from the project's rough notes and is not verified information about what a company asks.</p>
      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <Select id="rd-role" label="Role" value={role} onChange={e => setRole(e.target.value)}><option value="">Choose a role</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
          <Select id="rd-company" label="Software house (optional)" value={company} onChange={e => setCompany(e.target.value)}><option value="">Any / general</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select>
          <Select id="rd-resume" label="Resume" value={resumeId} onChange={e => setResumeId(e.target.value)}><option value="">Latest analysed resume</option>{resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}</Select>
        </div>
      </Card>
      {error && <ErrorState>{error}</ErrorState>}
      {!role && <EmptyState title="Choose a role to begin">Your readiness is calculated for one role at a time.</EmptyState>}
      {busy && <Spinner label="Calculating" />}
      {rep && ov && !busy && (
        <>
          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <Card>
              <p className="text-sm text-ink-soft">{rep.company?.name ?? 'General'} · {rep.role.title}</p>
              <p className="mt-1 font-display text-4xl font-bold">{ov.value === null ? '-' : `${ov.value}%`}</p>
              <p className="mt-1 font-medium">{ov.label}</p>
              <p className="mt-2 text-xs text-ink-mute">Evidence: {rep.evidence_count} of 4 result types (screening, assessment, coding, interview). {ov.explanation}</p>
            </Card>
            <Card className="lg:col-span-2">
              <h2 className="font-semibold">How the score is calculated</h2>
              <div className="mt-2 h-48"><ResponsiveContainer><BarChart data={rep.components.filter(c => c.value !== null).map(c => ({ name: c.name, value: c.value }))} layout="vertical" margin={{ left: 40 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} fontSize={11} /><YAxis type="category" dataKey="name" width={150} fontSize={11} /><Tooltip /><Bar dataKey="value" name="Score" fill="#2563eb" /></BarChart></ResponsiveContainer></div>
            </Card>
          </div>
          <Card className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm"><caption className="sr-only">Score parts</caption>
              <thead className="text-ink-mute"><tr><th className="py-1 font-medium">Part</th><th className="font-medium">Score</th><th className="font-medium">Weight used</th><th className="font-medium">How it is worked out</th></tr></thead>
              <tbody>{rep.components.map(c => (
                <tr key={c.key} className="border-t border-line align-top"><td className="py-1 pr-2">{c.name}</td><td className="pr-2">{c.value === null ? <Badge>Not assessed</Badge> : `${c.value}%`}</td><td className="pr-2">{c.value === null ? '0% (left out)' : `${c.effective_weight}%`}</td><td className="text-ink-soft">{c.value === null ? c.reason : c.how}</td></tr>))}</tbody>
            </table>
          </Card>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card className="overflow-x-auto">
              <h2 className="mb-2 font-semibold">Skill gap</h2>
              <table className="w-full text-left text-sm"><caption className="sr-only">Skill gap</caption>
                <thead className="text-ink-mute"><tr><th className="py-1 font-medium">Skill</th><th className="font-medium">Need</th><th className="font-medium">Status</th></tr></thead>
                <tbody>{rep.skill_gap.map(g => (
                  <tr key={g.skill} className="border-t border-line"><td className="py-1">{g.skill}</td><td>{g.importance}</td><td><Badge tone={TONE[g.status]}>{g.status_text}{g.score !== null ? ` ${g.score}%` : ''}</Badge></td></tr>))}</tbody>
              </table>
              <p className="mt-2 text-xs text-ink-mute">A skill is called strong or weak only when you have answered questions on it. Otherwise it is shown as not assessed.</p>
            </Card>
            <Card>
              <h2 className="font-semibold">What to do next</h2>
              {rep.next_actions.length === 0 ? <p className="mt-2 text-sm text-ink-soft">Nothing urgent. Keep practising.</p> : (
                <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm">{rep.next_actions.map((a, i) => <li key={i}><Link className="text-info underline" to={LINK[a.type] ?? '/app'}>{a.text}</Link><span className="block text-xs text-ink-mute">{a.why}</span></li>)}</ol>)}
              {rep.suggested_coding.length > 0 && <p className="mt-3 text-sm"><b>Coding to try:</b> {rep.suggested_coding.map(c => `${c.title} (${c.difficulty})`).join(', ')}. <Link className="text-info underline" to="/app/coding">Open coding</Link></p>}
              {rep.suggested_questions.length > 0 && <div className="mt-3 text-sm"><b>Questions to study:</b><ul className="list-disc pl-5">{rep.suggested_questions.map(q => <li key={q.slug}>{q.prompt}</li>)}</ul><Link className="text-info underline" to="/app/questions">Open the question bank</Link></div>}
            </Card>
          </div>
          <div className="mt-4 space-y-4">
            <Table title="Best-matching companies for this role" rows={companyRows} nameOf={r => r.company?.name ?? ''} onPick={r => setCompany(r.company?.slug ?? '')} />
            <Table title="Role recommendations" rows={roleRows} nameOf={r => r.role?.title ?? ''} onPick={r => setRole(r.role?.slug ?? '')} />
          </div>
          <p className="mt-4 text-xs text-ink-mute">{rep.disclaimer}</p>
        </>
      )}
    </>
  )
}
