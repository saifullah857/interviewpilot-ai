import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import PromptText from '../components/PromptText'
import { Badge, Card, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type ScreeningResult as Result } from '../lib/api'

export default function ScreeningResult() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [r, setR] = useState<Result | null>(null)
  const [error, setError] = useState('')
  const [wrongOnly, setWrongOnly] = useState(false)
  useEffect(() => {
    api.screeningReview(id).then(setR).catch(e => {
      if (e instanceof ApiError && e.code === 'not_finished') nav(`/app/screening/${id}`, { replace: true })
      else setError(e instanceof ApiError ? e.message : 'Could not load the result.')
    })
  }, [id, nav])
  if (error) return <ErrorState>{error}</ErrorState>
  if (!r) return <Spinner label="Loading your result" />
  const sc = r.session.score ?? 0
  const items = r.review.filter(x => !wrongOnly || !x.correct)
  return (
    <>
      <PageHeader title="Screening result" intro={r.auto_submitted ? 'Time ran out, so the test was submitted automatically with the answers saved so far.' : 'Your test is finished.'} actions={<LinkButton to="/app/screening" variant="secondary">New test</LinkButton>} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card><p className="text-sm text-ink-soft">Score</p><p className="mt-1 font-display text-4xl font-bold">{sc}%</p><p className="text-sm text-ink-soft">{r.session.correct} of {r.session.total} correct</p></Card>
        <Card className="lg:col-span-2"><p className="text-sm text-ink-soft">Next step</p><p className="mt-1">{r.next_step.message}</p>
          {(r.next_step.weak_categories?.length ?? 0) > 0 && <p className="mt-2 text-sm">Practise: {r.next_step.weak_categories?.join(', ')}</p>}
          {(r.next_step.strong_categories?.length ?? 0) > 0 && <p className="mt-1 text-sm text-ink-soft">Strong: {r.next_step.strong_categories?.join(', ')}</p>}
          <div className="mt-3"><LinkButton to="/app/questions" variant="secondary">Study the question bank</LinkButton></div></Card>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card><h2 className="font-semibold">Score by topic</h2><div className="mt-2 h-56"><ResponsiveContainer><BarChart data={r.by_category} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} fontSize={11} /><YAxis type="category" dataKey="name" width={90} fontSize={11} /><Tooltip /><Bar dataKey="score" name="Correct %" fill="#2563eb" /></BarChart></ResponsiveContainer></div></Card>
        <Card><h2 className="font-semibold">Score by difficulty</h2><div className="mt-2 h-56"><ResponsiveContainer><BarChart data={r.by_difficulty}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Bar dataKey="score" name="Correct %" fill="#16a34a" /></BarChart></ResponsiveContainer></div></Card>
      </div>
      <div className="mt-6 flex items-center justify-between"><h2 className="text-lg font-semibold">Review your answers</h2>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={wrongOnly} onChange={e => setWrongOnly(e.target.checked)} /> Show only wrong or skipped</label></div>
      <div className="mt-2 space-y-3">
        {items.length === 0 && <p className="text-sm text-ink-soft">Nothing to show. Every answer was correct.</p>}
        {items.map(x => (
          <Card key={x.slug}>
            <div className="mb-2 flex flex-wrap gap-2"><Badge tone={x.correct ? 'ok' : 'bad'}>{x.correct ? 'Correct' : x.chosen === null ? 'Skipped' : 'Wrong'}</Badge><Badge>{x.category}</Badge><Badge>{x.difficulty}</Badge></div>
            <PromptText text={x.prompt} />
            <ul className="mt-3 space-y-1 text-sm">
              {x.options.map((o, k) => <li key={k} className={`rounded border p-2 font-mono whitespace-pre-wrap ${k === x.answer_index ? 'border-ok' : k === x.chosen ? 'border-bad' : 'border-line'}`}>{o}{k === x.answer_index && <b className="ml-2 font-sans">correct answer</b>}{k === x.chosen && k !== x.answer_index && <b className="ml-2 font-sans">your answer</b>}</li>)}
            </ul>
            <p className="mt-2 text-sm text-ink-soft">{x.explanation}</p>
          </Card>
        ))}
      </div>
      <p className="mt-4 text-xs text-ink-mute">{r.note}</p>
    </>
  )
}
