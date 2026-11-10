import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type Assessment } from '../lib/api'

export default function AssessmentPage() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [a, setA] = useState<Assessment | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')

  const generating = a?.status === 'generating'
  useEffect(() => {
    let live = true
    const load = () => api.assessment(id).then(x => { if (live) setA(x) }).catch(e => { if (live) setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load this assessment.')) })
    load()
    if (!generating && a) return () => { live = false }  // already finished: no polling
    const t = setInterval(load, 2500)  // poll only while the assessment is being written
    return () => { live = false; clearInterval(t) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, generating])

  if (err) return <ErrorState title={err.status === 404 ? 'Assessment not found' : undefined} action={<LinkButton to="/app/assessment/setup">Back to setup</LinkButton>}>{err.status === 404 ? 'It may have been deleted.' : err.message}</ErrorState>
  if (!a) return <Spinner label="Loading" />
  if (a.status === 'in_progress') return <Navigate to={`/app/assessment/${a.id}/take`} replace />
  if (a.status === 'submitted') return <Navigate to={`/app/assessment/${a.id}/review`} replace />

  async function cancel() {
    setBusy(true)
    try { await api.deleteAssessment(id); nav('/app/assessment/setup') } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not cancel.'); setBusy(false) }
  }

  async function start() {
    setBusy(true); setNote('')
    try { await api.startAssessment(id); nav(`/app/assessment/${id}/take`) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not start.'); setBusy(false) }
  }

  return (
    <>
      <PageHeader title={a.status === 'generating' ? 'Writing your assessment' : a.status === 'failed' ? 'Assessment not created' : 'Before you start'} />
      {a.status === 'generating' && <Card className="max-w-xl"><Spinner label="Writing and checking your questions, this can take a minute" /><div className="flex flex-wrap items-center gap-3 px-6 pb-4"><p className="text-xs text-ink-mute">You can leave this page; it will be in your history when ready. If the AI is busy, built-in practice questions fill the gap.</p><Button variant="secondary" onClick={cancel} disabled={busy}>Cancel and start over</Button></div></Card>}
      {a.status === 'failed' && <ErrorState action={<LinkButton to="/app/assessment/setup">Try again</LinkButton>}>{a.message ?? 'Something went wrong.'} You can try again right away.</ErrorState>}
      {a.status === 'ready' && (
        <Card className="max-w-2xl">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">{a.role.title}</Badge>
            {a.mode === 'company' && a.company ? <Badge tone="ok">Company-informed: {a.company.name}</Badge> : <Badge>General role preparation</Badge>}
            <Badge>{a.question_count} questions</Badge><Badge>{a.duration_minutes} minutes</Badge>
          </div>
          {a.notice && <p role="status" className="mt-3 rounded-lg bg-warn-soft p-3 text-sm text-warn">{a.notice}</p>}
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ink-soft">
            <li>The timer starts when you press Start and cannot be paused. If it runs out, your saved answers are submitted automatically.</li>
            <li>Your answers are saved as you go. Multiple-choice answers are scored when you submit; short answers are not scored yet.</li>
            <li>Every question is AI-generated practice. {a.mode === 'company' ? 'Some are inspired by approved sources about the company, which are linked on the question. They are not real questions asked by the company.' : 'None are real questions from any company.'}</li>
            <li>Your score is a preparation indicator, not a prediction of being hired. Browsers cannot reliably prevent outside help, so we do not claim to; practise honestly for useful feedback.</li>
          </ul>
          {a.generation.dropped > 0 && <p className="mt-3 text-xs text-ink-mute">{a.generation.dropped} draft question(s) were discarded by our automatic checks.</p>}
          {note && <p role="alert" className="mt-3 text-sm text-bad">{note}</p>}
          <div className="mt-5 flex gap-2"><Button onClick={start} disabled={busy}>{busy ? 'Starting…' : 'Start now'}</Button><LinkButton to="/app/history" variant="secondary">Not now</LinkButton></div>
        </Card>
      )}
      <p className="mt-4 text-sm"><Link className="text-info underline" to="/app/assessment/setup">Set up another</Link></p>
    </>
  )
}
