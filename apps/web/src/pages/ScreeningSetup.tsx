import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Badge, Button, Card, PageHeader, Select } from '../components/ui'
import { api, ApiError, type CompanyFocus, type ScreeningSummary } from '../lib/api'

export default function ScreeningSetup() {
  const nav = useNavigate()
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [companies, setCompanies] = useState<CompanyFocus[]>([])
  const [past, setPast] = useState<ScreeningSummary[]>([])
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [level, setLevel] = useState('mixed')
  const [count, setCount] = useState('20')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.roles().then(setRoles).catch(() => setRoles([]))
    api.codingCompanies().then(r => setCompanies(r.companies)).catch(() => setCompanies([]))
    api.screeningSessions().then(setPast).catch(() => setPast([]))
  }, [])

  const start = async () => {
    setBusy(true); setError('')
    try {
      const s = await api.createScreening({ role, level, count: Number(count), ...(company ? { company } : {}) })
      nav(`/app/screening/${s.id}`)
    } catch (e) {
      const active = e instanceof ApiError && e.code === 'active_session'
      setError(active ? 'You already have a test in progress. Open it from the list on the right.' : e instanceof ApiError ? e.message : 'Could not start the test.')
      if (active) api.screeningSessions().then(setPast).catch(() => undefined)
    } finally { setBusy(false) }
  }

  return (
    <>
      <PageHeader title="Online screening" intro="A timed test of multiple-choice and output questions, like the first screening round of many software houses. It is scored by fixed rules, not by AI." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Start a test</h2>
          <div className="mt-3 space-y-3">
            <Select id="sc-role" label="Role" value={role} onChange={e => setRole(e.target.value)}><option value="">Choose a role</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
            <Select id="sc-company" label="Software house (optional)" value={company} onChange={e => setCompany(e.target.value)}><option value="">Any / general</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select>
            <Select id="sc-level" label="Difficulty" value={level} onChange={e => setLevel(e.target.value)}><option value="mixed">Mixed</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></Select>
            <Select id="sc-count" label="Number of questions" value={count} onChange={e => setCount(e.target.value)}>{['10', '20', '30', '40'].map(n => <option key={n} value={n}>{n} (about {Math.round(Number(n) * 1.5)} minutes)</option>)}</Select>
          </div>
          <Button className="mt-4 w-full" disabled={!role || busy} onClick={start}>Start test</Button>
          {error && <p role="alert" className="mt-2 text-sm text-bad">{error}</p>}
          <p className="mt-3 text-xs text-ink-mute">Questions are company-focused practice, not the company's real questions. A score here is a preparation indicator, not a hiring prediction.</p>
        </Card>
        <Card>
          <h2 className="mb-2 font-semibold">Your tests</h2>
          {past.length === 0 ? <p className="text-sm text-ink-soft">No tests yet.</p> : (
            <ul className="divide-y divide-line text-sm">
              {past.map(s => (
                <li key={s.id} className="flex items-center justify-between gap-2 py-2">
                  <span>{s.company?.name ?? 'General'} · {s.level}<span className="block text-xs text-ink-mute">{s.submitted_at ? new Date(s.submitted_at).toLocaleDateString('en-GB') : 'in progress'}</span></span>
                  {s.status === 'submitted' ? <Link className="text-info underline" to={`/app/screening/${s.id}/result`}><Badge tone={(s.score ?? 0) >= 70 ? 'ok' : (s.score ?? 0) >= 40 ? 'warn' : 'bad'}>{s.score}%</Badge></Link> : <Link className="text-info underline" to={`/app/screening/${s.id}`}>Continue</Link>}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  )
}
