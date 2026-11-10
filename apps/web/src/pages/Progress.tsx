import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge, Card, EmptyState, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type Dashboard } from '../lib/api'

const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '')
const COMP: Record<string, string> = { technical_knowledge: 'Technical knowledge', coding_correctness: 'Coding', interview_performance: 'Interview' }

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return <Card><p className="text-sm text-ink-soft">{label}</p><p className="mt-1 font-display text-3xl font-bold">{value}</p>{hint && <p className="mt-1 text-xs text-ink-mute">{hint}</p>}</Card>
}

function Chart({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return <Card><h2 className="font-semibold">{title}</h2>{note && <p className="mb-2 text-xs text-ink-mute">{note}</p>}<div className="mt-2 h-64 w-full">{children}</div></Card>
}

export default function Progress() {
  const [d, setD] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api.dashboard().then(setD).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load your progress.')) }, [])

  if (error) return <ErrorState>{error}</ErrorState>
  if (!d) return <Spinner label="Loading your progress" />
  const s = d.summary
  if (s.coding_sessions === 0 && s.reports === 0 && s.screening_tests === 0) {
    return (<><PageHeader title="My progress" intro="Your scores over time, drawn from your own finished work." />
      <EmptyState title="Nothing to chart yet" action={<LinkButton to="/app/coding">Start a coding challenge</LinkButton>}>Finish a coding session, a screening test or an assessment and your progress graphs appear here automatically.</EmptyState></>)
  }
  const coding = d.coding.map((c, i) => ({ name: `#${i + 1} ${day(c.date)}`, score: c.score, solved: c.solved, problems: c.problems_count }))
  const trend = d.reports.map(r => ({ name: day(r.date), overall: r.overall, ...Object.fromEntries(Object.entries(r.components).map(([k, v]) => [COMP[k] ?? k, v])) }))
  const lines = ['Technical knowledge', 'Coding', 'Interview'].filter(k => trend.some(t => (t as Record<string, unknown>)[k] !== undefined))
  const COLORS = ['#2563eb', '#16a34a', '#d97706']
  return (
    <>
      <PageHeader title="My progress" intro="Everything here is calculated from your own finished sessions. Reports are saved automatically when you finish." actions={<LinkButton to="/app/results" variant="secondary">Open my reports</LinkButton>} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Kpi label="Coding sessions" value={String(s.coding_sessions)} />
        <Kpi label="Problems fully solved" value={`${s.problems_solved}`} hint={`of ${s.bank_size} in the bank`} />
        <Kpi label="Average coding score" value={s.average_coding_score === null ? '-' : `${s.average_coding_score}%`} hint={s.best_coding_score === null ? undefined : `Best ${s.best_coding_score}%`} />
        <Kpi label="Average screening score" value={s.average_screening_score === null ? '-' : `${s.average_screening_score}%`} hint={`${s.screening_tests} test${s.screening_tests === 1 ? '' : 's'}`} />
        <Kpi label="Latest overall score" value={s.latest_overall === null ? '-' : `${s.latest_overall}`} hint={`${s.reports} saved report${s.reports === 1 ? '' : 's'}`} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Chart title="Coding score per session" note="Share of tests passed in the problems you submitted. Sessions where nothing ran are left out.">
          <ResponsiveContainer><LineChart data={coding}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Line type="monotone" dataKey="score" name="Score %" stroke="#16a34a" strokeWidth={2} connectNulls /></LineChart></ResponsiveContainer>
        </Chart>
        <Chart title="Overall score trend" note="One point per saved report.">
          {trend.length === 0 ? <p className="p-6 text-sm text-ink-soft">No report yet. Finish a session to create one.</p> : (
            <ResponsiveContainer><LineChart data={trend}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Legend />
              <Line type="monotone" dataKey="overall" name="Overall" stroke="#111827" strokeWidth={3} connectNulls />
              {lines.map((k, i) => <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % 3]} strokeWidth={1.5} connectNulls />)}</LineChart></ResponsiveContainer>)}
        </Chart>
        <Chart title="Screening score per test" note="Correct answers in your timed MCQ and output tests.">
          {d.screening.length === 0 ? <p className="p-6 text-sm text-ink-soft">Take an online screening test to see this.</p> : (
            <ResponsiveContainer><LineChart data={d.screening.map((t, k) => ({ name: `#${k + 1} ${day(t.date)}`, score: t.score }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Line type="monotone" dataKey="score" name="Score %" stroke="#7c3aed" strokeWidth={2} connectNulls /></LineChart></ResponsiveContainer>)}
        </Chart>
        <Chart title="Screening strength by topic" note="Correct answers per topic across all your screening tests.">
          {d.screening_categories.length === 0 ? <p className="p-6 text-sm text-ink-soft">Take an online screening test to see this.</p> : (
            <ResponsiveContainer><BarChart data={d.screening_categories} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} fontSize={11} /><YAxis type="category" dataKey="name" width={90} fontSize={11} /><Tooltip /><Bar dataKey="score" name="Correct %" fill="#7c3aed" /></BarChart></ResponsiveContainer>)}
        </Chart>
        <Chart title="Strength by topic" note="Tests passed per topic across all your submissions.">
          {d.topics.length === 0 ? <p className="p-6 text-sm text-ink-soft">Submit a problem to see topics.</p> : (
            <ResponsiveContainer><BarChart data={d.topics} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" domain={[0, 100]} fontSize={11} /><YAxis type="category" dataKey="name" width={110} fontSize={11} /><Tooltip /><Bar dataKey="score" name="Pass rate %" fill="#2563eb" /></BarChart></ResponsiveContainer>)}
        </Chart>
        <Chart title="Data structures and difficulty" note="How you do with list, tuple, dict, set, loops and conditions.">
          {d.structures.length < 3 ? <p className="p-6 text-sm text-ink-soft">Submit a few more problems to draw this.</p> : (
            <ResponsiveContainer><RadarChart data={d.structures}><PolarGrid /><PolarAngleAxis dataKey="name" fontSize={11} /><PolarRadiusAxis domain={[0, 100]} fontSize={10} /><Radar dataKey="score" name="Pass rate %" stroke="#d97706" fill="#d97706" fillOpacity={0.35} /><Tooltip /></RadarChart></ResponsiveContainer>)}
        </Chart>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold">What to practise next</h2>
          {d.weak_topics.length === 0 ? <p className="mt-2 text-sm text-ink-soft">Not enough submissions yet to say which topic is weakest.</p> : (
            <ul className="mt-2 space-y-1 text-sm">{d.weak_topics.map(t => <li key={t.name} className="flex justify-between"><span>{t.name}</span><Badge tone="warn">{t.score}%</Badge></li>)}</ul>)}
          {d.strong_topics.length > 0 && <p className="mt-3 text-sm text-ink-soft">Strong: {d.strong_topics.map(t => `${t.name} (${t.score}%)`).join(', ')}</p>}
        </Card>
        <Card className="overflow-x-auto">
          <h2 className="mb-2 font-semibold">Coding sessions</h2>
          <table className="w-full text-left text-sm"><caption className="sr-only">Coding sessions</caption>
            <thead className="text-ink-mute"><tr><th className="py-1 font-medium">Date</th><th className="font-medium">Focus</th><th className="font-medium">Solved</th><th className="font-medium">Score</th></tr></thead>
            <tbody>{[...d.coding].reverse().slice(0, 8).map(c => (
              <tr key={c.id} className="border-t border-line"><td className="py-1"><Link className="text-info underline" to={`/app/coding/${c.id}/review`}>{day(c.date)}</Link></td><td>{c.company?.name ?? 'General'}</td><td>{c.solved}/{c.problems_count}</td><td>{c.score === null ? 'not run' : `${c.score}%`}</td></tr>))}</tbody></table>
        </Card>
      </div>
    </>
  )
}
