import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Badge, Button, Card, EmptyState, LinkButton, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type DiscoverCompany, type Interview, type ResumeItem } from '../lib/api'
import { useAuth } from '../lib/auth'
import { speechSupport } from '../lib/speech'

const TONE = { active: 'info', completed: 'ok', interrupted: 'warn' } as const

export default function Voice() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const { user } = useAuth()
  const support = speechSupport()
  const [resumes, setResumes] = useState<ResumeItem[] | null>(null)
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [companies, setCompanies] = useState<DiscoverCompany[]>([])
  const [past, setPast] = useState<Interview[]>([])
  const [resumeId, setResumeId] = useState('')
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [count, setCount] = useState(6)
  const [mode, setMode] = useState<'voice' | 'text'>('text')
  const [consent, setConsent] = useState(false)
  const [keep, setKeep] = useState(user?.consents.voice_transcript ?? false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.resumes().then(r => { const ok = r.filter(x => x.analyzed); setResumes(ok); if (ok[0]) setResumeId(ok[0].id) }).catch(() => setResumes([]))
    api.roles().then(r => { setRoles(r); const want = params.get('role'); if (r[0]) setRole(r.find(x => x.slug === want)?.slug ?? r[0].slug) }).catch(() => setRoles([]))
    api.discoverCompanies().then(c => { setCompanies(c.items); const x = params.get('company'); if (x && c.items.some(i => i.slug === x)) setCompany(x) }).catch(() => setCompanies([]))
    api.interviews().then(setPast).catch(() => setPast([]))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- read the URL preselection once on load
  }, [])

  async function start() {
    setBusy(true); setError('')
    try {
      const i = await api.createInterview({ resume_id: resumeId, role, company: company || undefined, question_count: count, input_mode: mode, consent, save_transcript: keep })
      nav(`/app/interview/${i.id}`)
    } catch (e) {
      if (e instanceof ApiError && e.code === 'interview_in_progress') { const id = (e.details as unknown as { interview_id?: string } | undefined)?.interview_id; if (id) { nav(`/app/interview/${id}`); return } }
      setError(e instanceof ApiError ? e.message : 'Could not start the interview.'); setBusy(false)
    }
  }

  if (!resumes) return <Spinner label="Loading" />
  const open = past.find(i => i.status === 'active')
  return (
    <>
      <PageHeader title="Voice interview" intro="An AI interviewer asks practice questions based on your resume and target role, and follows up on what you say." />
      {open && <p role="status" className="mb-4 rounded-lg bg-info-soft p-3 text-sm text-info">You have an interview in progress. <Link className="font-semibold underline" to={`/app/interview/${open.id}`}>Continue it</Link></p>}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <h2 className="font-semibold">Set up your practice interview</h2>
          {resumes.length === 0 && <div className="mt-3"><EmptyState title="No analysed resume yet" action={<LinkButton to="/app/resume">Go to Resume</LinkButton>}>The interviewer needs your analysed resume to ask about your projects.</EmptyState></div>}
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Select id="iv-resume" label="Resume" value={resumeId} onChange={e => setResumeId(e.target.value)} disabled={resumes.length === 0}>
              {resumes.length === 0 ? <option value="">No analysed resume</option> : resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}
            </Select>
            <Select id="iv-role" label="Target role" value={role} onChange={e => setRole(e.target.value)}>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
            <Select id="iv-company" label="Lahore company (optional)" value={company} onChange={e => setCompany(e.target.value)}>
              <option value="">None: general role practice</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}{c.status === 'verified_lahore' ? '' : ' (not checked yet)'}</option>)}
            </Select>
            <Select id="iv-count" label="Main questions" value={count} onChange={e => setCount(Number(e.target.value))}>{[4, 5, 6, 8, 10].map(n => <option key={n} value={n}>{n}</option>)}</Select>
          </div>
          <p className="mt-2 text-xs text-ink-mute">{company ? 'Company practice uses only approved research for that company. Questions are still AI-written practice, never real company questions.' : 'General role practice: not specific to any company.'}</p>
          <fieldset className="mt-4">
            <legend className="text-sm font-medium">How will you answer?</legend>
            <label className="mt-1 flex items-center gap-2 text-sm"><input type="radio" name="mode" checked={mode === 'text'} onChange={() => setMode('text')} /> Typing</label>
            <label className="mt-1 flex items-center gap-2 text-sm"><input type="radio" name="mode" checked={mode === 'voice'} disabled={!support.recognition} onChange={() => setMode('voice')} /> Speaking (browser speech recognition){!support.recognition && <span className="text-xs text-ink-mute"> not supported in this browser</span>}</label>
          </fieldset>
          <label className="mt-4 flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1" checked={consent} onChange={e => setConsent(e.target.checked)} />
            <span>I have read the privacy notice and agree that my answers are sent to the AI provider and held to run this interview.</span>
          </label>
          <label className="mt-3 flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1" checked={keep} onChange={e => setKeep(e.target.checked)} />
            <span>Keep my transcript after the interview. Off means it is deleted after you get feedback, or after 24 hours.</span>
          </label>
          {error && <p role="alert" className="mt-3 text-sm text-bad">{error}</p>}
          <Button className="mt-4" disabled={!consent || !resumeId || !role || busy} onClick={start}>Start interview</Button>
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="font-semibold">Privacy notice</h2>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-ink-soft">
            <li>The interviewer is an AI. It can't see you and does not assess your face, voice, accent or appearance. It reads only the text of your answers.</li>
            <li>Your answers are sent to the AI provider (Groq) to write follow-ups and feedback.</li>
            <li>If you speak, some browsers send the audio to the browser vendor for recognition. Typing avoids this. You always see and can edit the text before it is sent.</li>
            <li>Questions are AI-written practice. They are not real questions from any company.</li>
            <li>You can delete a transcript or the whole interview at any time. Scores are preparation indicators, not hiring predictions.</li>
          </ul>
        </Card>
      </div>
      <h2 className="mb-2 mt-8 text-lg font-semibold">Your interviews</h2>
      {past.length === 0 ? <p className="text-sm text-ink-soft">No interviews yet.</p> : (
        <ul className="divide-y divide-line rounded-xl border border-line bg-surface" aria-label="Past interviews">
          {past.map(i => (
            <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
              <span><b>{i.role.title}</b>{i.company ? ` · ${i.company.name}` : ' · general'} · {new Date(i.started_at).toLocaleDateString()} · {i.answers_given} answers</span>
              <span className="flex items-center gap-2"><Badge tone={TONE[i.status]}>{i.status}</Badge>{i.evaluated && <Badge tone="brand">Feedback ready</Badge>}
                <Link className="font-semibold text-info underline" to={i.status === 'completed' ? `/app/interview/${i.id}/review` : `/app/interview/${i.id}`}>{i.status === 'completed' ? 'Review' : 'Open'}</Link></span>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
