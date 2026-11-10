import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { CodingResults } from '../components/CodingResults'
import { api, ApiError, type CodingFeedback, type CodingReview as Review } from '../lib/api'
import { Paragraphs } from '../lib/text'

export default function CodingReview() {
  const { id = '' } = useParams()
  const [r, setR] = useState<Review | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [fb, setFb] = useState<Record<string, CodingFeedback>>({})
  const [busy, setBusy] = useState('')
  const [note, setNote] = useState('')
  useEffect(() => { api.codingReview(id).then(setR).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load the review.'))) }, [id])

  async function feedback(submissionId: string) {
    setBusy(submissionId); setNote('')
    try { const f = await api.codingFeedback(submissionId); setFb(x => ({ ...x, [submissionId]: f })) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not get feedback.') } finally { setBusy('') }
  }

  if (err) return <ErrorState title={err.status === 409 ? 'Not finished yet' : undefined} action={<LinkButton to={`/app/coding/${id}`}>Back to the session</LinkButton>}>{err.message}</ErrorState>
  if (!r) return <Spinner label="Loading your results" />
  const s = r.summary
  return (
    <>
      <PageHeader title="Coding results" intro={r.session.auto_submitted ? 'Time ran out, so the session was finished automatically.' : 'Your session is finished.'} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card><h2 className="text-sm text-ink-soft">Problems solved</h2><p className="mt-1 text-3xl font-bold">{s.executed ? `${s.solved} / ${s.problems}` : 'n/a'}</p></Card>
        <Card><h2 className="text-sm text-ink-soft">Tests passed (objective)</h2><p className="mt-1 text-3xl font-bold">{s.executed && s.tests_passed !== null ? `${s.tests_passed} / ${s.tests_total}` : 'Not run'}</p></Card>
        <Card><p className="text-xs text-ink-mute">{s.note} Scores are preparation indicators, not predictions of being hired.</p></Card>
      </div>
      <Card className="mt-4">
        <p className="text-sm"><b>{s.executed && s.tests_total ? `Coding score: ${Math.round(((s.tests_passed ?? 0) / s.tests_total) * 100)}%.` : 'Nothing was run, so there is no score.'}</b> Your report was saved automatically in your history.</p>
        <div className="mt-2 flex flex-wrap gap-2"><LinkButton to="/app/progress" variant="secondary">See my progress graphs</LinkButton><LinkButton to="/app/results" variant="secondary">Open my reports</LinkButton></div>
      </Card>
      {note && <p role="alert" className="mt-3 text-sm text-bad">{note}</p>}
      <div className="mt-5 space-y-5">
        {r.problems.map(p => (
          <Card key={p.problem.slug}>
            <div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-semibold">{p.problem.title}</h2>
              <Badge tone={p.solved ? 'ok' : p.submission?.executed ? 'bad' : 'neutral'}>{p.solved ? 'Solved' : p.submission ? (p.submission.executed ? 'Not solved' : 'Not run') : 'Not submitted'}</Badge>
              <span className="text-xs text-ink-mute">{p.runs} runs · {p.submits} submits</span></div>
            <div className="mt-3 grid gap-4 lg:grid-cols-2">
              <div><h3 className="mb-1 text-sm font-semibold">Your code</h3><pre className="max-h-72 overflow-auto rounded-lg bg-canvas p-3 text-xs">{p.final_code}</pre></div>
              <div>{p.submission ? <CodingResults sub={p.submission} /> : <p className="text-sm text-ink-soft">You did not submit this problem.</p>}</div>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div><h3 className="mb-1 text-sm font-semibold">Approach and complexity</h3><Paragraphs text={p.approach} /><p className="mt-2 text-xs text-ink-mute">Time {p.complexity.time}, space {p.complexity.space}</p></div>
              <div><h3 className="mb-1 text-sm font-semibold">Reference solution</h3><pre className="max-h-60 overflow-auto rounded-lg bg-canvas p-3 text-xs">{p.reference_solution}</pre></div>
            </div>
            {p.submission && (
              <div className="mt-4 border-t border-line pt-3">
                {(fb[p.submission.id] ?? p.submission.feedback) ? (() => { const f = (fb[p.submission.id] ?? p.submission.feedback)!; return (
                  <div><h3 className="text-sm font-semibold">AI commentary <Badge tone="warn">Subjective</Badge></h3>
                    <p className="text-xs text-ink-mute">{f.note}</p>
                    <p className="mt-2 text-sm"><b>Complexity:</b> {f.complexity}</p>
                    {f.strengths.length > 0 && <><h4 className="mt-2 text-sm font-medium">Strengths</h4><ul className="list-disc pl-5 text-sm text-ink-soft">{f.strengths.map(x => <li key={x}>{x}</li>)}</ul></>}
                    {f.improvements.length > 0 && <><h4 className="mt-2 text-sm font-medium">To improve</h4><ul className="list-disc pl-5 text-sm text-ink-soft">{f.improvements.map(x => <li key={x}>{x}</li>)}</ul></>}
                    {f.readability && <p className="mt-2 text-sm text-ink-soft">{f.readability}</p>}
                  </div>) })() : <Button variant="secondary" disabled={busy === p.submission.id} onClick={() => feedback(p.submission!.id)}>{busy === p.submission.id ? 'Asking the AI…' : 'Get AI feedback on this solution'}</Button>}
              </div>
            )}
          </Card>
        ))}
      </div>
      <div className="mt-5 flex gap-2"><LinkButton to="/app/coding">Practise more</LinkButton><LinkButton to="/app/history" variant="secondary">History</LinkButton></div>
    </>
  )
}
