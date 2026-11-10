import { useEffect, useState } from 'react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type BankQuestion, type BankReveal, type BankStats } from '../lib/api'

const TONE: Record<string, 'ok' | 'warn' | 'bad'> = { easy: 'ok', medium: 'warn', hard: 'bad' }
const SOURCE: Record<string, string> = { verified: 'Verified', reported: 'Reported', company_focused_practice: 'Company-focused practice' }

export default function QuestionBank() {
  const [stats, setStats] = useState<BankStats | null>(null)
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [kind, setKind] = useState('')
  const [text, setText] = useState('')
  const [items, setItems] = useState<BankQuestion[] | null>(null)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [open, setOpen] = useState<Record<string, BankReveal>>({})

  useEffect(() => {
    api.bankStats().then(setStats).catch(() => setStats(null))
    api.roles().then(setRoles).catch(() => setRoles([]))
  }, [])
  useEffect(() => {
    setItems(null)
    const p: Record<string, string> = {}
    if (company) p.company = company
    if (role) p.role = role
    if (difficulty) p.difficulty = difficulty
    if (kind) p.kind = kind
    if (text.trim()) p.q = text.trim()
    const t = setTimeout(() => api.bankQuestions(p).then(r => { setItems(r.items); setTotal(r.total); setError('') }).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load questions.')), 250)
    return () => clearTimeout(t)
  }, [company, role, difficulty, kind, text])

  const reveal = (slug: string) => api.bankReveal(slug).then(r => setOpen(o => ({ ...o, [slug]: r }))).catch(() => setError('Could not load the answer.'))

  return (
    <>
      <PageHeader title="Question bank" intro="Practice questions for each software house. Think through your own answer first, then open the ideal answer." />
      <p className="mb-4 rounded-lg border border-line bg-canvas p-3 text-sm text-ink-soft">Every question here is <b>company-focused practice</b>: written for the company's technology focus. They are not the company's real interview questions, and nothing here says what a company will ask you.</p>
      <Card>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Select id="qb-company" label="Company" value={company} onChange={e => setCompany(e.target.value)}><option value="">All companies</option>{(stats?.companies ?? []).map(c => <option key={c.slug} value={c.slug}>{c.name} ({c.total})</option>)}</Select>
          <Select id="qb-role" label="Role" value={role} onChange={e => setRole(e.target.value)}><option value="">All roles</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
          <Select id="qb-diff" label="Difficulty" value={difficulty} onChange={e => setDifficulty(e.target.value)}><option value="">Any</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></Select>
          <Select id="qb-kind" label="Type" value={kind} onChange={e => setKind(e.target.value)}><option value="">Any</option><option value="technical">Technical</option><option value="scenario">Scenario</option><option value="mcq">MCQ</option><option value="output">Output</option></Select>
          <div><label htmlFor="qb-text" className="mb-1 block text-sm font-medium">Search</label><input id="qb-text" className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm" value={text} onChange={e => setText(e.target.value)} placeholder="e.g. RAG, SQL, deadlock" /></div>
        </div>
      </Card>
      {error && <ErrorState>{error}</ErrorState>}
      {!items && !error && <Spinner label="Loading questions" />}
      {items && items.length === 0 && <EmptyState title="No questions match">Try another company, role or search word. Only some companies have questions so far.</EmptyState>}
      {items && items.length > 0 && <p className="mt-4 text-sm text-ink-soft">Showing {items.length} of {total} questions.</p>}
      <div className="mt-2 space-y-3">
        {(items ?? []).map(q => {
          const r = open[q.slug]
          return (
            <Card key={q.slug}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={TONE[q.difficulty]}>{q.difficulty}</Badge><Badge>{q.category}</Badge><Badge>{q.kind}</Badge>
                <Badge tone="info" title={q.source_title}>{SOURCE[q.source_label] ?? q.source_label}</Badge>
              </div>
              <p className="mt-2 font-medium">{q.prompt}</p>
              {q.options.length > 0 && <ol className="mt-2 list-decimal pl-5 text-sm">{q.options.map(o => <li key={o}>{o}</li>)}</ol>}
              {!r ? <Button variant="secondary" className="mt-3" onClick={() => reveal(q.slug)}>Show ideal answer</Button> : (
                <div className="mt-3 rounded-lg bg-canvas p-3 text-sm">
                  {r.ideal_answer && <p>{r.ideal_answer}</p>}
                  {r.answer_index !== null && <p><b>Correct option:</b> {r.answer_index + 1}. {r.explanation}</p>}
                  {r.key_points.length > 0 && <><p className="mt-2 font-medium">Key points to cover</p><ul className="list-disc pl-5">{r.key_points.map(k => <li key={k}>{k}</li>)}</ul></>}
                  {r.follow_ups.length > 0 && <><p className="mt-2 font-medium">Possible follow-up</p><ul className="list-disc pl-5">{r.follow_ups.map(k => <li key={k}>{k}</li>)}</ul></>}
                </div>
              )}
            </Card>
          )
        })}
      </div>
    </>
  )
}
