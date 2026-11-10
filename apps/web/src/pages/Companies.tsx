import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Card, EmptyState, ErrorState, Field, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type DiscoverCompany } from '../lib/api'

const FAMILIES: [string, string][] = [['', 'All focus areas'], ['web', 'Web'], ['frontend', 'Frontend'], ['backend', 'Backend'], ['mobile', 'Mobile'], ['ai-ml', 'AI / ML'], ['data', 'Data']]

export function StatusBadge({ status, label }: { status: DiscoverCompany['status']; label: string }) {
  return <Badge tone={status === 'verified_lahore' ? 'ok' : status === 'stale' ? 'warn' : 'neutral'}>{label}</Badge>
}

export default function Companies() {
  const [q, setQ] = useState('')
  const [fam, setFam] = useState('')
  const [items, setItems] = useState<DiscoverCompany[] | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let live = true
    const t = setTimeout(() => {
      api.discoverCompanies(q.trim(), fam)
        .then(d => { if (live) { setItems(d.items); setError('') } })
        .catch(e => { if (live) setError(e instanceof ApiError ? e.message : 'Could not load companies.') })
    }, 250)
    return () => { live = false; clearTimeout(t) }
  }, [q, fam, attempt])

  return (
    <>
      <PageHeader title="Lahore software houses and startups"
        intro="Open a company and press “Research this company”. The agent looks for a Lahore office on the company's own website and for public hiring and interview information. Companies marked “not checked yet” are Lahore candidates until that research confirms them." />
      <div className="mb-5 grid gap-3 sm:grid-cols-2">
        <Field id="search" label="Search by name or technology" value={q} onChange={e => setQ(e.target.value)} placeholder="e.g. React" />
        <Select id="fam" label="Focus area" value={fam} onChange={e => setFam(e.target.value)}>{FAMILIES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</Select>
      </div>
      {error ? <ErrorState action={<button className="text-sm text-info underline" onClick={() => setAttempt(a => a + 1)}>Try again</button>}>{error}</ErrorState>
        : !items ? <Spinner label="Loading companies" />
        : items.length === 0 ? <EmptyState title="No companies match" action={<button className="text-sm text-info underline" onClick={() => { setQ(''); setFam('') }}>Clear filters</button>}>Try a different search. If the list is empty, run <code>python -m app.cli import-seed</code> in apps\api.</EmptyState>
        : (
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-label="Companies">
            {items.map(c => (
              <li key={c.slug}>
                <Card className="h-full">
                  <h2 className="font-semibold"><Link className="underline-offset-2 hover:underline" to={`/app/companies/${c.slug}`}>{c.name}</Link></h2>
                  <div className="mt-1"><StatusBadge status={c.status} label={c.status_label} /></div>
                  {c.localities.length > 0 && <p className="mt-2 text-sm text-ink-soft">{c.localities.join(', ')}, Lahore</p>}
                  <div className="mt-3 flex flex-wrap gap-1.5">{c.tech_focus.map(f => <Badge key={f}>{f}</Badge>)}</div>
                  {c.status !== 'verified_lahore' && <p className="mt-2 text-xs text-ink-mute">Technology tags are rough notes until researched.</p>}
                </Card>
              </li>
            ))}
          </ul>
        )}
    </>
  )
}
