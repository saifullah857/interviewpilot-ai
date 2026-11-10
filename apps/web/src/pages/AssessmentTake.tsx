import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, EvidenceBadge, LinkButton, Spinner } from '../components/ui'
import { api, ApiError, type Assessment, type Question } from '../lib/api'

type Draft = { selected_index?: number | null; response_text?: string }
type SaveState = 'saved' | 'pending' | 'saving' | 'error'
const SAVE_TEXT: Record<SaveState, string> = { saved: 'All answers saved', pending: 'Unsaved changes…', saving: 'Saving…', error: 'Could not save. Retrying…' }
const fmt = (ms: number) => { const s = Math.max(0, Math.floor(ms / 1000)); return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` }

export default function AssessmentTake() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [a, setA] = useState<Assessment | null>(null)
  const [err, setErr] = useState('')
  const [i, setI] = useState(0)
  const [answers, setAnswers] = useState<Record<string, Draft>>({})
  const [save, setSave] = useState<SaveState>('saved')
  const [confirming, setConfirming] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [now, setNow] = useState(Date.now())
  const offset = useRef(0)
  const dirty = useRef(new Set<string>())
  const latest = useRef(answers)
  const debounce = useRef<number | undefined>(undefined)
  const submitted = useRef(false)
  latest.current = answers

  useEffect(() => {
    let live = true
    api.assessment(id).then(x => {
      if (!live) return
      offset.current = Date.parse(x.server_now) - Date.now()  // follow the server's clock, not the laptop's
      setA(x)
      setAnswers(Object.fromEntries((x.answers ?? []).map(s => [s.question_id, { selected_index: s.selected_index, response_text: s.response_text ?? '' }])))
    }).catch(e => { if (live) setErr(e instanceof ApiError ? e.message : 'Could not load this assessment.') })
    return () => { live = false }
  }, [id])

  const flush = useCallback(async () => {
    const ids = [...dirty.current]
    if (ids.length === 0) return true
    dirty.current.clear()
    setSave('saving')
    try {
      await api.saveAnswers(id, ids.map(q => ({ question_id: q, selected_index: latest.current[q]?.selected_index ?? null, response_text: latest.current[q]?.response_text ?? null })))
      setSave(dirty.current.size ? 'pending' : 'saved')
      return true
    } catch (e) {
      ids.forEach(q => dirty.current.add(q))
      if (e instanceof ApiError && (e.code === 'time_expired' || e.code === 'not_in_progress')) { nav(`/app/assessment/${id}/review`, { replace: true }); return false }
      setSave('error')
      return false
    }
  }, [id, nav])

  function change(qid: string, patch: Draft) {
    setAnswers(prev => ({ ...prev, [qid]: { ...prev[qid], ...patch } }))
    dirty.current.add(qid)
    setSave('pending')
    window.clearTimeout(debounce.current)
    debounce.current = window.setTimeout(() => { void flush() }, 800)
  }

  const submit = useCallback(async () => {
    if (submitted.current) return
    submitted.current = true
    setSubmitting(true)
    await flush()
    try { await api.submitAssessment(id); nav(`/app/assessment/${id}/review`, { replace: true }) }
    catch (e) { submitted.current = false; setSubmitting(false); setErr(e instanceof ApiError ? e.message : 'Could not submit.') }
  }, [flush, id, nav])

  useEffect(() => {
    const t = setInterval(() => { setNow(Date.now()); if (dirty.current.size) void flush() }, 1000)  // clock tick + retry of any unsaved answers
    return () => { clearInterval(t); window.clearTimeout(debounce.current) }
  }, [flush])

  const deadline = a?.deadline_at ? Date.parse(a.deadline_at) : null
  const remaining = deadline === null ? null : deadline - (now + offset.current)
  useEffect(() => { if (remaining !== null && remaining <= 0 && a?.status === 'in_progress') void submit() }, [remaining, a?.status, submit])

  const qs: Question[] = useMemo(() => a?.questions ?? [], [a])
  if (err) return <ErrorState action={<LinkButton to="/app/history">Back to history</LinkButton>}>{err}</ErrorState>
  if (!a) return <Spinner label="Loading your test" />
  if (a.status === 'ready') return <Navigate to={`/app/assessment/${a.id}`} replace />
  if (a.status === 'submitted') return <Navigate to={`/app/assessment/${a.id}/review`} replace />
  if (a.status !== 'in_progress' || qs.length === 0) return <Navigate to={`/app/assessment/${a.id}`} replace />

  const q = qs[i]
  const d = answers[q.id] ?? {}
  const answered = (x: Question) => { const v = answers[x.id]; return x.type === 'mcq' ? v?.selected_index != null : !!v?.response_text?.trim() }
  const unanswered = qs.filter(x => !answered(x)).length
  const low = remaining !== null && remaining < 5 * 60 * 1000

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-2xl font-bold">{a.role.title}{a.mode === 'company' && a.company ? `, ${a.company.name}` : ''}</h1><p className="text-sm text-ink-soft">Question {i + 1} of {qs.length}</p></div>
        <div className="flex items-center gap-3">
          <span role="status" className="text-xs text-ink-mute">{SAVE_TEXT[save]}</span>
          <span role="timer" aria-live="off" aria-label="Time remaining" className={`rounded-lg px-3 py-1.5 font-mono text-lg font-semibold ${low ? 'bg-bad-soft text-bad' : 'bg-canvas'}`}>{remaining === null ? '--:--' : fmt(remaining)}</span>
        </div>
      </div>
      {low && <p role="status" className="mb-3 text-sm text-bad">Less than five minutes left.</p>}

      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="lg:col-span-3">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <EvidenceBadge label="ai_generated_practice" /><Badge>{q.difficulty}</Badge><Badge>{q.topic}</Badge>
            {q.category === 'company_informed' && <Badge tone="info">Inspired by approved sources</Badge>}
          </div>
          {q.informed_by.length > 0 && (
            <p className="mb-3 rounded-lg bg-canvas p-2 text-xs text-ink-soft">
              Informed by: {q.informed_by.map(r => <a key={r.url} className="mr-2 text-info underline" href={r.url} target="_blank" rel="noopener noreferrer">{new URL(r.url).hostname}</a>)}
              This is a practice question. It is not a question the company asked.
            </p>
          )}
          {q.type === 'mcq' ? (
            <fieldset>
              <legend className="text-lg font-semibold">{q.prompt}</legend>
              <div className="mt-4 space-y-2">
                {q.options.map(o => (
                  <label key={o.index} className="flex cursor-pointer items-start gap-3 rounded-lg border border-line p-3 text-sm has-[:checked]:border-brand has-[:checked]:bg-brand-soft">
                    <input type="radio" className="mt-0.5" name={q.id} checked={d.selected_index === o.index} onChange={() => change(q.id, { selected_index: o.index })} /> {o.text}
                  </label>
                ))}
              </div>
              {d.selected_index != null && <button className="mt-2 text-xs text-info underline" onClick={() => change(q.id, { selected_index: null })}>Clear my answer</button>}
            </fieldset>
          ) : (
            <div>
              <label htmlFor={`a-${q.id}`} className="text-lg font-semibold">{q.prompt}</label>
              <textarea id={`a-${q.id}`} rows={8} maxLength={4000} value={d.response_text ?? ''} onChange={e => change(q.id, { response_text: e.target.value })} className="mt-3 w-full rounded-lg border border-line p-3 text-sm" placeholder="Write your answer in your own words" />
              <p className="text-right text-xs text-ink-mute">{(d.response_text ?? '').length} / 4000 · not scored yet</p>
            </div>
          )}
          <div className="mt-5 flex justify-between">
            <Button variant="secondary" disabled={i === 0} onClick={() => setI(i - 1)}>Previous</Button>
            {i < qs.length - 1 ? <Button onClick={() => setI(i + 1)}>Next question</Button> : <Button onClick={() => setConfirming(true)}>Review and submit</Button>}
          </div>
        </Card>
        <Card>
          <h2 className="mb-2 text-sm font-semibold">Questions</h2>
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Question navigator">
            {qs.map((x, n) => (
              <button key={x.id} onClick={() => setI(n)} aria-label={`Question ${n + 1}${answered(x) ? ', answered' : ', not answered'}`} aria-current={n === i}
                className={`h-8 w-8 rounded-md border text-xs ${n === i ? 'border-ink' : 'border-line'} ${answered(x) ? 'bg-brand-soft' : 'bg-surface'}`}>{n + 1}</button>
            ))}
          </div>
          <Button className="mt-4 w-full" variant="secondary" onClick={() => setConfirming(true)}>Submit</Button>
          <p className="mt-3 text-xs text-ink-mute">Scores are preparation indicators, not predictions of being hired. <Link className="text-info underline" to="/app/history">History</Link></p>
        </Card>
      </div>

      {confirming && (
        <div role="dialog" aria-modal="true" aria-labelledby="submit-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="max-w-md">
            <h2 id="submit-title" className="text-lg font-semibold">Submit your assessment?</h2>
            <p className="mt-2 text-sm text-ink-soft">{unanswered === 0 ? 'You have answered every question.' : `${unanswered} question(s) are not answered and will count as blank.`} You cannot change answers after submitting.</p>
            <div className="mt-4 flex gap-2"><Button onClick={submit} disabled={submitting}>{submitting ? 'Submitting…' : 'Submit now'}</Button><Button variant="secondary" onClick={() => setConfirming(false)} disabled={submitting}>Keep working</Button></div>
          </Card>
        </div>
      )}
    </div>
  )
}
