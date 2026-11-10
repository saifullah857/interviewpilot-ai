import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge, Card, ErrorState, EvidenceBadge, LinkButton, PageHeader, Spinner } from '../components/ui'
import { Button } from '../components/ui'
import { api, ApiError, type Review } from '../lib/api'

export default function AssessmentReview() {
  const { id = '' } = useParams()
  const [r, setR] = useState<Review | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const nav = useNavigate()
  const [codingErr, setCodingErr] = useState('')
  useEffect(() => { api.reviewAssessment(id).then(setR).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load the review.'))) }, [id])
  async function startCoding() {
    setCodingErr('')
    try { const s = await api.createCodingSession({ assessment_id: id, count: 2 }); nav(`/app/coding/${s.id}`) } catch (e) {
      if (e instanceof ApiError && e.code === 'session_in_progress') { const sid = (e.details as unknown as { session_id?: string } | undefined)?.session_id; if (sid) { nav(`/app/coding/${sid}`); return } }
      setCodingErr(e instanceof ApiError ? e.message : 'Could not start the coding challenge.')
    }
  }
  if (err) return <ErrorState title={err.status === 409 ? 'Not submitted yet' : undefined} action={<LinkButton to={`/app/assessment/${id}`}>Back</LinkButton>}>{err.message}</ErrorState>
  if (!r) return <Spinner label="Loading your review" />
  const { result: s, assessment: a } = r
  return (
    <>
      <PageHeader title="Your results" intro={`${a.role.title}${a.mode === 'company' && a.company ? `, ${a.company.name}` : ', general role preparation'}`} />
      {a.auto_submitted && <p role="status" className="mb-4 rounded-lg bg-warn-soft p-3 text-sm text-warn">Time ran out, so your saved answers were submitted automatically.</p>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card><h2 className="text-sm text-ink-soft">Multiple choice</h2><p className="mt-1 text-3xl font-bold">{s.mcq_correct} / {s.mcq_total}</p><p className="text-xs text-ink-mute">{s.mcq_unanswered} left blank. Scored objectively.</p></Card>
        <Card><h2 className="text-sm text-ink-soft">Short answers</h2><p className="mt-1 text-3xl font-bold">{s.short_answered} / {s.short_total}</p><p className="text-xs text-ink-mute">answered. Not scored yet.</p></Card>
        <Card>
          <h2 className="mb-1 text-sm text-ink-soft">By topic</h2>
          <ul className="space-y-1 text-sm">{s.by_topic.map(t => <li key={t.topic} className="flex justify-between"><span>{t.topic}</span><span>{t.correct}/{t.total}</span></li>)}</ul>
        </Card>
      </div>
      <p className="mt-3 text-xs text-ink-mute">{s.note} Scores are preparation indicators, not predictions of being hired.</p>
      <ol className="mt-5 space-y-4">
        {r.questions.map(q => (
          <li key={q.id}>
            <Card>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge>Question {q.position}</Badge><EvidenceBadge label="ai_generated_practice" />
                {q.type === 'mcq' ? <Badge tone={q.is_correct ? 'ok' : 'bad'}>{q.is_correct ? 'Correct' : q.selected_index == null ? 'Left blank' : 'Incorrect'}</Badge> : <Badge tone="neutral">Not scored yet</Badge>}
                {q.informed_by.map(x => <a key={x.url} className="text-xs text-info underline" href={x.url} target="_blank" rel="noopener noreferrer">{new URL(x.url).hostname}</a>)}
              </div>
              <h3 className="font-semibold">{q.prompt}</h3>
              {q.type === 'mcq' ? (
                <ul className="mt-2 space-y-1 text-sm">
                  {q.options.map(o => (
                    <li key={o.index} className={o.index === q.correct_index ? 'font-semibold text-ok' : o.index === q.selected_index ? 'text-bad' : ''}>
                      {o.text} {o.index === q.correct_index && '(correct answer)'} {o.index === q.selected_index && o.index !== q.correct_index && '(your answer)'}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="mt-2 grid gap-3 text-sm md:grid-cols-2">
                  <div><h4 className="font-medium">Your answer</h4><p className="whitespace-pre-wrap text-ink-soft">{q.response_text ?? 'You left this blank.'}</p></div>
                  <div><h4 className="font-medium">A good answer covers</h4><ul className="list-disc pl-5 text-ink-soft">{q.reference_points.map(p => <li key={p}>{p}</li>)}</ul></div>
                </div>
              )}
              <p className="mt-2 text-sm text-ink-soft"><b>Why:</b> {q.explanation}</p>
            </Card>
          </li>
        ))}
      </ol>
      <div className="mt-5 flex flex-wrap gap-2"><Button onClick={startCoding}>Continue to the coding challenge</Button><LinkButton to="/app/assessment/setup" variant="secondary">Practise again</LinkButton><LinkButton to="/app/history" variant="secondary">History</LinkButton></div>
      {codingErr && <p role="alert" className="mt-2 text-sm text-bad">{codingErr}</p>}
      <p className="mt-3 text-xs text-ink-mute">The voice interview and full reports arrive in later phases.</p>
    </>
  )
}
