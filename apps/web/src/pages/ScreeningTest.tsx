import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import PromptText from '../components/PromptText'
import { Badge, Button, Card, ErrorState, Spinner } from '../components/ui'
import { api, ApiError, type ScreeningSession } from '../lib/api'

const fmt = (ms: number) => { const s = Math.max(0, Math.floor(ms / 1000)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` }

export default function ScreeningTest() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [s, setS] = useState<ScreeningSession | null>(null)
  const [i, setI] = useState(0)
  const [error, setError] = useState('')
  const [now, setNow] = useState(Date.now())
  const [busy, setBusy] = useState(false)
  const offset = useRef(0)

  const apply = useCallback((x: ScreeningSession) => {
    offset.current = Date.parse(x.server_now) - Date.now()
    if (x.status === 'submitted') { nav(`/app/screening/${x.id}/result`, { replace: true }); return }
    setS(x)
  }, [nav])
  useEffect(() => { api.screeningSession(id).then(apply).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load the test.')) }, [id, apply])
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t) }, [])

  const remaining = s ? Date.parse(s.deadline_at) - (now + offset.current) : null
  useEffect(() => { if (remaining !== null && remaining <= 0) api.screeningSession(id).then(apply).catch(() => undefined) }, [remaining, id, apply])

  if (error && !s) return <ErrorState>{error}</ErrorState>
  if (!s) return <Spinner label="Loading the test" />
  const q = s.questions[i]
  const chosen = s.answers[q.slug]
  const choose = (c: number) => {
    setS({ ...s, answers: { ...s.answers, [q.slug]: c } })  // show it immediately; the server copy is saved right after
    api.screeningAnswer(id, q.slug, c).then(setS).catch(e => setError(e instanceof ApiError ? e.message : 'Could not save your answer.'))
  }
  const finish = async () => {
    const left = s.total - Object.keys(s.answers).length
    if (left > 0 && !window.confirm(`${left} question${left === 1 ? ' is' : 's are'} unanswered and will count as wrong. Submit now?`)) return
    setBusy(true)
    try { await api.screeningSubmit(id); nav(`/app/screening/${id}/result`) } catch (e) { setError(e instanceof ApiError ? e.message : 'Could not submit.'); setBusy(false) }
  }
  const low = remaining !== null && remaining < 120000

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Question {i + 1} of {s.total}</h1>
        <span role="timer" aria-live="off" className={`font-mono text-lg ${low ? 'text-bad' : ''}`}>{remaining === null ? '' : fmt(remaining)}</span>
      </div>
      {low && <p role="status" className="mb-2 text-sm text-bad">Less than two minutes left.</p>}
      {error && <p role="alert" className="mb-2 text-sm text-bad">{error}</p>}
      <div className="grid gap-4 lg:grid-cols-[1fr_16rem]">
        <Card>
          <div className="mb-2 flex flex-wrap gap-2"><Badge>{q.difficulty}</Badge><Badge>{q.category}</Badge><Badge tone="info">{q.kind === 'output' ? 'output' : 'multiple choice'}</Badge></div>
          <PromptText text={q.prompt} />
          <fieldset className="mt-4 space-y-2">
            <legend className="sr-only">Choose one answer</legend>
            {q.options.map((o, k) => (
              <label key={k} className={`flex cursor-pointer items-start gap-2 rounded-lg border p-3 text-sm ${chosen === k ? 'border-info bg-canvas' : 'border-line'}`}>
                <input type="radio" name={`q-${q.slug}`} checked={chosen === k} onChange={() => choose(k)} className="mt-1" />
                <span className="font-mono whitespace-pre-wrap">{o}</span>
              </label>
            ))}
          </fieldset>
          <div className="mt-4 flex flex-wrap justify-between gap-2">
            <Button variant="secondary" disabled={i === 0} onClick={() => setI(i - 1)}>Previous</Button>
            {i < s.total - 1 ? <Button onClick={() => setI(i + 1)}>Next</Button> : <Button disabled={busy} onClick={finish}>Submit test</Button>}
          </div>
        </Card>
        <Card>
          <p className="mb-2 text-sm font-medium">{Object.keys(s.answers).length} of {s.total} answered</p>
          <div className="flex flex-wrap gap-1">
            {s.questions.map((x, k) => <button key={x.slug} aria-label={`Question ${k + 1}${s.answers[x.slug] !== undefined ? ', answered' : ''}`} onClick={() => setI(k)} className={`h-8 w-8 rounded text-xs ${k === i ? 'ring-2 ring-info' : ''} ${s.answers[x.slug] !== undefined ? 'bg-info text-white' : 'border border-line'}`}>{k + 1}</button>)}
          </div>
          <Button variant="secondary" className="mt-4 w-full" disabled={busy} onClick={finish}>Submit test</Button>
        </Card>
      </div>
    </>
  )
}
