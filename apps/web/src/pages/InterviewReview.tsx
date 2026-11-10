import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type InterviewReview as Review } from '../lib/api'

export default function InterviewReview() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [r, setR] = useState<Review | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState('')
  const [confirm, setConfirm] = useState<'' | 'transcript' | 'interview'>('')
  useEffect(() => { api.interviewReview(id).then(setR).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load the interview.'))) }, [id])

  async function evaluate() {
    setBusy('eval'); setNote('')
    try { setR(await api.evaluateInterview(id)) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not get feedback.') } finally { setBusy('') }
  }
  async function dropTranscript() {
    setBusy('del'); setConfirm('')
    try { const iv = await api.deleteInterviewTranscript(id); setR(x => (x ? { ...x, interview: iv } : x)) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not delete.') } finally { setBusy('') }
  }
  async function dropAll() {
    setBusy('del')
    try { await api.deleteInterview(id); nav('/app/interview') } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not delete.'); setBusy('') }
  }

  if (err) return <ErrorState title={err.status === 404 ? 'Interview not found' : undefined} action={<LinkButton to="/app/interview">Back to interviews</LinkButton>}>{err.message}</ErrorState>
  if (!r) return <Spinner label="Loading the review" />
  const { interview: iv, evaluation: ev } = r
  const answerText = (n: number) => iv.turns?.find(t => t.position === n)?.text
  return (
    <>
      <PageHeader title="Interview feedback" intro={`${iv.role.title}${iv.company ? ` · ${iv.company.name}` : ' · general role practice'} · ${iv.answers_given} answers`} actions={<Badge tone="warn">AI-written practice questions</Badge>} />
      {iv.status === 'active' && <p role="status" className="mb-4 rounded-lg bg-info-soft p-3 text-sm text-info">This interview is still active. <a className="font-semibold underline" href={`/app/interview/${id}`}>Return to the room</a></p>}
      {note && <p role="alert" className="mb-3 text-sm text-bad">{note}</p>}
      {!ev ? (
        <Card className="max-w-2xl">
          <h2 className="font-semibold">Feedback on your answers</h2>
          <p className="mt-2 text-sm text-ink-soft">The AI reads the text of your answers and scores four criteria. This is a subjective judgement, kept separate from any objective result such as coding test results.</p>
          {iv.answers_given === 0 && <p className="mt-2 text-sm text-warn">No answers were given, so there is nothing to evaluate.</p>}
          {!iv.transcript_available && <p className="mt-2 text-sm text-warn">The transcript has been removed, so feedback can no longer be created.</p>}
          <Button className="mt-4" onClick={evaluate} disabled={busy !== '' || iv.status === 'active' || iv.answers_given === 0 || !iv.transcript_available}>Get feedback on my answers</Button>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card>
              <h2 className="text-sm text-ink-soft">Interview preparation indicator</h2>
              <p className="mt-1 text-3xl font-bold">{ev.indicator === null ? 'n/a' : `${ev.indicator} / 100`}</p>
              <p className="mt-1 flex flex-wrap gap-1"><Badge tone="warn">AI judgement, subjective</Badge><Badge tone={ev.evidence_level === 'limited' ? 'bad' : 'neutral'}>{ev.evidence_level === 'limited' ? 'Limited evidence' : `${ev.answers_scored} answers scored`}</Badge></p>
            </Card>
            <Card className="lg:col-span-2"><h2 className="font-semibold">Read this first</h2><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-soft">{ev.caveats.map(c => <li key={c}>{c}</li>)}</ul></Card>
          </div>
          <Card>
            <h2 className="font-semibold">Criteria (rubric {ev.rubric_version}, scored 0 to 4)</h2>
            <ul className="mt-3 space-y-4">
              {ev.criteria.map(c => (
                <li key={c.key}>
                  <div className="flex items-center justify-between text-sm"><span className="font-medium">{c.name}</span><span className="font-semibold">{c.score} / {c.max}</span></div>
                  <div role="progressbar" aria-label={c.name} aria-valuenow={c.score} aria-valuemin={0} aria-valuemax={c.max} className="mt-1 h-2 rounded-full bg-canvas"><div className="h-2 rounded-full bg-brand" style={{ width: `${(c.score / c.max) * 100}%` }} /></div>
                  <p className="mt-1 text-sm text-ink-soft">{c.rationale}</p>
                  <p className="mt-1 text-xs text-ink-mute">{c.low_evidence ? <Badge tone="warn">Cites no specific answer</Badge> : <>Based on answer{c.evidence_turns.length > 1 ? 's' : ''} at turn {c.evidence_turns.join(', ')}.</>}</p>
                  {c.evidence_turns.map(n => answerText(n) && <details key={n} className="mt-1 text-xs text-ink-soft"><summary>Show your answer (turn {n})</summary><p className="mt-1 rounded bg-canvas p-2">{answerText(n)}</p></details>)}
                </li>
              ))}
            </ul>
          </Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card><h2 className="font-semibold">Strengths</h2><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{ev.strengths.map(s => <li key={s}>{s}</li>)}</ul></Card>
            <Card><h2 className="font-semibold">To improve</h2><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{ev.improvements.map(s => <li key={s}>{s}</li>)}</ul></Card>
          </div>
          {ev.per_answer.length > 0 && (
            <Card><h2 className="font-semibold">Notes on individual answers</h2>
              <ul className="mt-2 space-y-3 text-sm">{ev.per_answer.map(p => <li key={p.turn}><p className="text-ink-mute">Question: {p.question}</p><p>{p.note}</p>{p.stronger_answer_hint && <p className="text-ink-soft">A stronger answer could: {p.stronger_answer_hint}</p>}</li>)}</ul></Card>
          )}
          <p className="text-xs text-ink-mute">Created {new Date(ev.created_at).toLocaleString()} by {ev.provider} ({ev.model}). {ev.injection_signals.length > 0 && 'Some answers contained text that looked like instructions to an AI; it was ignored.'}</p>
        </div>
      )}
      <Card className="mt-6">
        <h2 className="font-semibold">Transcript and data</h2>
        {iv.transcript_available && iv.turns ? (
          <ul className="mt-2 max-h-72 space-y-2 overflow-y-auto text-sm" aria-label="Transcript">{iv.turns.map(t => <li key={t.id}><span className="font-semibold">{t.speaker === 'interviewer' ? 'Interviewer' : 'You'}: </span>{t.text}</li>)}</ul>
        ) : <p className="mt-2 text-sm text-ink-soft">{iv.save_transcript ? 'The transcript was deleted.' : 'The transcript was not kept, as you chose. Scores and notes remain.'}</p>}
        <div className="mt-3 flex flex-wrap gap-2">
          {iv.transcript_available && iv.status !== 'active' && (confirm === 'transcript'
            ? <Button variant="danger" onClick={dropTranscript} disabled={busy !== ''}>Yes, delete the transcript</Button>
            : <Button variant="secondary" onClick={() => setConfirm('transcript')}>Delete transcript</Button>)}
          {confirm === 'interview'
            ? <Button variant="danger" onClick={dropAll} disabled={busy !== ''}>Yes, delete this interview</Button>
            : <Button variant="secondary" onClick={() => setConfirm('interview')}>Delete this interview</Button>}
          <LinkButton to="/app/interview" variant="ghost">Back to interviews</LinkButton>
        </div>
      </Card>
    </>
  )
}
