import { Suspense, lazy, useCallback, useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, EvidenceBadge, LinkButton, Select, Spinner } from '../components/ui'
import { CodingResults } from '../components/CodingResults'
import { api, ApiError, type CodingSession as Session, type CodingSubmission, type RunnerStatus } from '../lib/api'
import { Paragraphs, renderInline, show } from '../lib/text'

const Editor = lazy(() => import('@monaco-editor/react'))  // large, so it loads only on this page
const fmt = (ms: number) => { const s = Math.max(0, Math.floor(ms / 1000)); return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` }
const SAVE: Record<string, string> = { saved: 'Draft saved', pending: 'Unsaved changes…', saving: 'Saving…', error: 'Could not save draft' }

export default function CodingSession() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [s, setS] = useState<Session | null>(null)
  const [runner, setRunner] = useState<RunnerStatus | null>(null)
  const [idx, setIdx] = useState(0)
  const [code, setCode] = useState<Record<string, string>>({})
  const [shown, setShown] = useState<Record<string, CodingSubmission | undefined>>({})
  const [busy, setBusy] = useState<'' | 'run' | 'submit' | 'finish'>('')
  const [save, setSave] = useState('saved')
  const [err, setErr] = useState('')
  const [note, setNote] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [now, setNow] = useState(Date.now())
  const offset = useRef(0)
  const timer = useRef<number | undefined>(undefined)
  const finishing = useRef(false)

  useEffect(() => {
    let live = true
    api.codingSession(id).then(x => {
      if (!live) return
      offset.current = Date.parse(x.server_now) - Date.now()
      setS(x)
      setCode(Object.fromEntries((x.problems ?? []).map(p => [p.slug, x.drafts[p.slug] ?? p.starter_code])))
      setShown(Object.fromEntries(x.progress.filter(p => p.last_submit).map(p => [p.problem, p.last_submit!])))
    }).catch(e => { if (live) setErr(e instanceof ApiError ? e.message : 'Could not load this session.') })
    api.codingRunner().then(r => { if (live) setRunner(r) }).catch(() => undefined)
    return () => { live = false }
  }, [id])

  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => { clearInterval(t); window.clearTimeout(timer.current) } }, [])

  const finish = useCallback(async () => {
    if (finishing.current) return
    finishing.current = true; setBusy('finish')
    try { await api.finishCoding(id); nav(`/app/coding/${id}/review`, { replace: true }) } catch (e) { finishing.current = false; setBusy(''); setErr(e instanceof ApiError ? e.message : 'Could not finish.') }
  }, [id, nav])

  const deadline = s ? Date.parse(s.deadline_at) : null
  const remaining = deadline === null ? null : deadline - (now + offset.current)
  useEffect(() => { if (remaining !== null && remaining <= 0 && s?.status === 'in_progress') void finish() }, [remaining, s?.status, finish])

  if (err && !s) return <ErrorState action={<LinkButton to="/app/coding">Back to coding practice</LinkButton>}>{err}</ErrorState>
  if (!s) return <Spinner label="Loading your session" />
  if (s.status === 'submitted') return <Navigate to={`/app/coding/${id}/review`} replace />
  const problems = s.problems ?? []
  const p = problems[idx]
  if (!p) return <ErrorState>This session has no problems.</ErrorState>
  const progress = s.progress.find(x => x.problem === p.slug)
  const sub = shown[p.slug]
  const low = remaining !== null && remaining < 5 * 60 * 1000

  function edit(value: string | undefined) {
    const v = value ?? ''
    setCode(c => ({ ...c, [p.slug]: v }))
    setSave('pending')
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(async () => {
      setSave('saving')
      try { await api.saveCodingDraft(id, p.slug, v); setSave('saved') } catch (e) {
        if (e instanceof ApiError && (e.code === 'time_expired' || e.code === 'not_in_progress')) nav(`/app/coding/${id}/review`, { replace: true }); else setSave('error')
      }
    }, 1500)
  }

  async function go(kind: 'run' | 'submit') {
    setBusy(kind); setNote('')
    window.clearTimeout(timer.current)
    try {
      const r = await (kind === 'run' ? api.runCode : api.submitCode)(id, p.slug, code[p.slug] ?? '')
      setShown(x => ({ ...x, [p.slug]: r })); setSave('saved')
      const fresh = await api.codingSession(id).catch(() => null)  // refresh counters
      if (fresh) setS(fresh)
    } catch (e) {
      if (e instanceof ApiError && (e.code === 'time_expired' || e.code === 'not_in_progress')) { nav(`/app/coding/${id}/review`, { replace: true }); return }
      setNote(e instanceof ApiError ? e.message : 'Something went wrong. Try again.')
    } finally { setBusy('') }
  }

  const unsubmitted = problems.filter(x => !s.progress.find(q => q.problem === x.slug)?.last_submit).map(x => x.title)
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Problems">
          {problems.map((x, n) => <button key={x.slug} role="tab" aria-selected={n === idx} onClick={() => setIdx(n)} className={`rounded-lg border px-3 py-1.5 text-sm ${n === idx ? 'border-brand bg-brand-soft font-semibold' : 'border-line bg-surface'}`}>{n + 1}. {x.title}</button>)}
        </div>
        <div className="flex items-center gap-3">
          <span role="status" className="text-xs text-ink-mute">{SAVE[save]}</span>
          <span role="timer" aria-live="off" aria-label="Time remaining" className={`rounded-lg px-3 py-1.5 font-mono text-lg font-semibold ${low ? 'bg-bad-soft text-bad' : 'bg-canvas'}`}>{remaining === null ? '--:--' : fmt(remaining)}</span>
        </div>
      </div>
      {runner && !runner.executes_code && <p role="status" className="mb-3 rounded-lg bg-warn-soft p-3 text-sm text-warn"><b>Code runner not connected.</b> {runner.message} Your code is saved but nothing is run or scored.</p>}
      {low && <p role="status" className="mb-3 text-sm text-bad">Less than five minutes left.</p>}
      {(s.plan?.company || s.plan?.resume || s.plan?.language_note) && (
        <div className="mb-3 rounded-lg border border-line bg-canvas p-3 text-sm">
          {s.plan?.company && <p><b>{s.plan.company.name} practice focus:</b> {s.plan.company.focus.join(', ')}. <span className="text-ink-mute">{s.plan.company.note}</span></p>}
          {s.plan?.resume && <p className="mt-1"><b>Matched to your resume:</b> {(s.plan.resume.focus ?? []).join(', ') || 'general skills'}{s.plan.resume.languages.length > 0 ? ` (languages: ${s.plan.resume.languages.join(', ')})` : ''}</p>}
          {s.plan?.language_note && <p className="mt-1 text-warn">{s.plan.language_note}</p>}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="max-h-[75vh] overflow-y-auto lg:col-span-2">
          <div className="flex flex-wrap items-center gap-2"><h1 className="text-xl font-bold">{p.title}</h1><Badge>{p.difficulty}</Badge>{(p.ds ?? []).filter(x => ['list', 'tuple', 'dict', 'set'].includes(x)).map(x => <Badge key={x} tone="info">{x}</Badge>)}<EvidenceBadge label="ai_generated_practice" /></div>
          {s.plan?.reasons?.[p.slug] && <p className="mt-2 text-xs text-ink-soft">Why this problem: {s.plan.reasons[p.slug]}</p>}
          <Paragraphs text={p.statement} />
          <h2 className="mt-4 text-sm font-semibold">Constraints</h2>
          <ul className="mt-1 list-disc pl-5 text-sm text-ink-soft">{p.constraints.map(c => <li key={c}>{renderInline(c)}</li>)}</ul>
          <h2 className="mt-4 text-sm font-semibold">Examples</h2>
          {p.examples.map((e, i) => (
            <div key={i} className="mt-2 rounded-lg bg-canvas p-2 text-xs">
              <p className="font-mono">input: {show(e.args)}</p><p className="font-mono">output: {show(e.output)}</p><p className="mt-1 text-ink-soft">{renderInline(e.explanation)}</p>
            </div>
          ))}
          <p className="mt-4 text-xs text-ink-mute">Run checks the {p.visible_tests.length} visible tests. Submit also checks {p.hidden_count} hidden tests, which show only pass or fail.</p>
        </Card>
        <div className="space-y-3 lg:col-span-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div className="w-40"><Select id="lang" label="Language" value="python" onChange={() => undefined}><option value="python">Python 3</option></Select></div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-ink-mute">{s.runs_left} runs left · {Math.max(0, 5 - (progress?.submits ?? 0))} submits left</span>
              <Button variant="secondary" onClick={() => go('run')} disabled={busy !== ''}>{busy === 'run' ? 'Running…' : 'Run'}</Button>
              <Button onClick={() => go('submit')} disabled={busy !== ''}>{busy === 'submit' ? 'Submitting…' : 'Submit'}</Button>
            </div>
          </div>
          <div className="overflow-hidden rounded-xl border border-line">
            <Suspense fallback={<Spinner label="Loading the code editor" />}>
              <Editor height="340px" language="python" value={code[p.slug] ?? ''} onChange={edit} options={{ minimap: { enabled: false }, fontSize: 14, tabSize: 4, ariaLabel: 'Python code editor', scrollBeyondLastLine: false }} />
            </Suspense>
          </div>
          {note && <p role="alert" className="text-sm text-bad">{note}</p>}
          <Card>{sub ? <CodingResults sub={sub} /> : <p className="text-sm text-ink-soft">Run your code to see results here.</p>}</Card>
          <div className="flex justify-between"><Link className="text-sm text-info underline" to="/app/coding">Leave (your session keeps running)</Link><Button variant="secondary" onClick={() => setConfirming(true)} disabled={busy !== ''}>Finish session</Button></div>
        </div>
      </div>

      {confirming && (
        <div role="dialog" aria-modal="true" aria-labelledby="fin-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="max-w-md">
            <h2 id="fin-title" className="text-lg font-semibold">Finish this session?</h2>
            <p className="mt-2 text-sm text-ink-soft">{unsubmitted.length === 0 ? 'You have submitted every problem.' : `Not submitted yet: ${unsubmitted.join(', ')}. They will count as not attempted.`} Solutions are shown after you finish, and you cannot submit again.</p>
            <div className="mt-4 flex gap-2"><Button onClick={finish} disabled={busy === 'finish'}>{busy === 'finish' ? 'Finishing…' : 'Finish now'}</Button><Button variant="secondary" onClick={() => setConfirming(false)}>Keep working</Button></div>
          </Card>
        </div>
      )}
    </div>
  )
}
