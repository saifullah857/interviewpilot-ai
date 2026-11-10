import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Button, Card, EmptyState, LinkButton, PageHeader, Select } from '../components/ui'
import { api, ApiError, type DiscoverCompany, type ResumeItem } from '../lib/api'

const COUNTS = [10, 15, 20, 25, 30]

export default function AssessmentSetup() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [resumes, setResumes] = useState<ResumeItem[] | null>(null)
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [companies, setCompanies] = useState<DiscoverCompany[]>([])
  const [resumeId, setResumeId] = useState('')
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [count, setCount] = useState(20)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.resumes().then(r => { const ok = r.filter(x => x.analyzed); setResumes(ok); setResumeId(ok.find(x => x.id === params.get('resume'))?.id ?? ok[0]?.id ?? '') }).catch(() => setResumes([]))
    api.roles().then(r => { setRoles(r); setRole(r.find(x => x.slug === params.get('role'))?.slug ?? r[0]?.slug ?? '') }).catch(() => setRoles([]))
    api.discoverCompanies().then(d => { setCompanies(d.items); const c = params.get('company'); if (c && d.items.some(x => x.slug === c)) setCompany(c) }).catch(() => setCompanies([]))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- read the URL preselection once on load
  }, [])

  async function generate() {
    setBusy(true); setError('')
    try {
      const a = await api.createAssessment({ resume_id: resumeId, role, company: company || undefined, question_count: count })
      nav(`/app/assessment/${a.id}`)
    } catch (e) { setError(e instanceof ApiError ? e.message : 'Something went wrong. Try again.') } finally { setBusy(false) }
  }

  if (!resumes) return <p role="status" className="p-6 text-ink-soft">Loading…</p>
  if (resumes.length === 0) {
    return <><PageHeader title="Set up your practice" /><EmptyState title="Analyse a resume first" action={<LinkButton to="/app/resume">Go to Resume</LinkButton>}>Practice questions are written from your analysed resume and the role you pick.</EmptyState></>
  }
  return (
    <>
      <PageHeader title="Set up your practice" intro="Choose a role. Add a verified Lahore company to get company-informed practice where approved evidence exists." />
      <Card className="max-w-xl space-y-4">
        <Select id="resume" label="Resume" value={resumeId} onChange={e => setResumeId(e.target.value)}>{resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}</Select>
        <Select id="role" label="Target role" value={role} onChange={e => setRole(e.target.value)}>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
        <Select id="company" label="Lahore software house (optional)" value={company} onChange={e => setCompany(e.target.value)}>
          <option value="">No company: general role preparation</option>
          {companies.map(c => <option key={c.slug} value={c.slug}>{c.name}{c.status === 'verified_lahore' ? '' : ' (not checked yet)'}</option>)}
        </Select>
        <Select id="count" label="Number of questions" value={String(count)} onChange={e => setCount(Number(e.target.value))}>{COUNTS.map(n => <option key={n} value={n}>{n}</option>)}</Select>
        <p role="status" className="rounded-lg bg-canvas p-3 text-sm text-ink-soft">
          {company ? (companies.find(c => c.slug === company)?.status === 'verified_lahore' ? 'Company-informed questions are used only where the research on that company applies to your role. Otherwise you get general role preparation, and we tell you.' : 'This company has not been researched yet, so you will get general role preparation. Open the company and press “Research this company” first for company-informed practice.') : 'This will be general role preparation, not specific to any company.'}
        </p>
        <p className="text-xs text-ink-mute">Questions are written by an AI from your resume details (contact details removed) and checked automatically. They are practice questions, never real questions from a company. Writing them usually takes under a minute; if the AI is busy, built-in practice questions fill the gap and we tell you.</p>
        {error && <p role="alert" className="text-sm text-bad">{error}</p>}
        <Button onClick={generate} disabled={busy || !resumeId || !role}>{busy ? 'Starting…' : 'Write my assessment'}</Button>
        {companies.length === 0 && <p className="text-xs text-ink-mute">No companies listed yet. Run <code>python -m app.cli import-seed</code> in apps\api, then reload.</p>}
      </Card>
      <p className="mt-4 text-sm"><Link className="text-info underline" to="/app/history">Your earlier assessments</Link></p>
    </>
  )
}

