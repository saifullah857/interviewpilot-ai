import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, EvidenceBadge, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type DiscoverDetail } from '../lib/api'
import type { EvidenceLabel } from '../lib/evidence'
import { StatusBadge } from './Companies'

const KINDS: [string, string][] = [['interview_format', 'How interviews are reported to work'], ['role_requirement', 'Role requirements'], ['tech_stack', 'Technology'], ['responsibility', 'What the role does']]
const date = (s: string) => new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

export default function CompanyDetail() {
  const { slug = '' } = useParams()
  const [c, setC] = useState<DiscoverDetail | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => api.discoverCompany(slug).then(d => { setC(d); setErr(null) }).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load this company.'))), [slug])
  useEffect(() => { setC(null); load() }, [load])

  const running = c?.latest_run?.status === 'running'
  useEffect(() => {
    if (!running) return
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [running, load])

  async function research(force = false) {
    setBusy(true); setNote('')
    try { await api.startCompanyResearch(slug, force); await load() } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not start research.') } finally { setBusy(false) }
  }

  if (err) return <ErrorState title={err.status === 404 ? 'Company not found' : undefined} action={<LinkButton to="/app/companies">Back to companies</LinkButton>}>{err.status === 404 ? 'The link may be wrong.' : err.message}</ErrorState>
  if (!c) return <Spinner label="Loading company" />
  const verified = c.status === 'verified_lahore'
  const run = c.latest_run
  const prep = `/app/assessment/setup?company=${c.slug}`
  return (
    <>
      <p className="mb-2 text-sm"><Link className="text-info underline" to="/app/companies">All companies</Link></p>
      <PageHeader title={c.name}
        intro={`${c.localities.length ? c.localities.join(', ') + ', Lahore. ' : ''}${c.description}`}
        actions={<div className="flex flex-wrap items-center gap-2"><StatusBadge status={c.status} label={c.status_label} />{c.auto_verified && <Badge tone="info" title="Confirmed by an automatic check of the company's own website, not by a person. Re-check before relying on it.">Automatic check</Badge>}{c.last_verified_at && <Badge tone={c.needs_recheck ? 'warn' : 'ok'}>{`checked ${date(c.last_verified_at)}`}</Badge>}</div>} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="font-semibold">Research agent</h2>
          <p className="mt-1 text-sm text-ink-soft">Searches the company's official website and public pages for a Lahore office, job requirements and reported interview formats. Everything it finds keeps its source link and label. It never invents questions, and results can be out of date.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button onClick={() => research(false)} disabled={busy || running}>{running ? 'Researching…' : run ? 'Show latest / research again' : 'Research this company'}</Button>
            {run && !running && <Button variant="secondary" onClick={() => research(true)} disabled={busy}>Force fresh research</Button>}
          </div>
          {running && <Spinner label="Searching the web and reading pages, this takes about a minute" />}
          {note && <p role="alert" className="mt-3 text-sm text-bad">{note}</p>}
          {run && !running && <p role="status" className={`mt-3 rounded-lg p-3 text-sm ${run.status === 'succeeded' ? 'bg-ok-soft text-ok' : 'bg-warn-soft text-warn'}`}>{(run.summary.message as string | undefined) ?? (run.status === 'failed' ? 'Research failed. Try again.' : 'Research finished.')}</p>}
          {run && !running && run.summary.website_discovered === true && <p className="mt-2 text-xs text-ink-mute">The company's website was found automatically from search results. Check the link before trusting it.</p>}
        </Card>
        <Card>
          <h2 className="mb-2 font-semibold">Details</h2>
          {c.locations.map(l => <p key={l.id} className="text-sm text-ink-soft">{l.locality}{l.address ? `, ${l.address}` : ''}, Lahore</p>)}
          {c.focus_areas.length > 0 && <p className="mt-2 text-xs text-ink-mute">Focus: {c.focus_areas.join(', ')}</p>}
          <div className="mt-3 flex flex-wrap gap-1.5">{c.tech_focus.map(f => <Badge key={f}>{f}</Badge>)}</div>
          {c.focus_note && <p className="mt-2 text-xs text-ink-mute">{c.focus_note}</p>}
          <div className="mt-3 space-y-1 text-sm">
            {c.website && <a className="block text-info underline" href={c.website} target="_blank" rel="noopener noreferrer">Website</a>}
            {c.careers_url && <a className="block text-info underline" href={c.careers_url} target="_blank" rel="noopener noreferrer">Careers page</a>}
          </div>
          <LinkButton to={prep} className="mt-5 w-full">Practise for this company</LinkButton>
          <p className="mt-2 text-xs text-ink-mute">{verified ? 'Questions use the research below where it applies to your role.' : 'Not confirmed yet, so practice will be general role preparation until research confirms the Lahore office.'}</p>
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="mb-1 font-semibold">What research found</h2>
          <p className="mb-3 text-xs text-ink-mute">Candidate reports may be out of date and are not official. Pages change, so check the links.</p>
          {c.requirements.length === 0 ? <p className="text-sm text-ink-soft">{verified ? 'No hiring information has been found yet.' : 'Nothing is shown until the Lahore office is confirmed.'}</p> : (
            KINDS.map(([kind, title]) => {
              const items = c.requirements.filter(r => r.kind === kind)
              return items.length === 0 ? null : (
                <section key={kind} className="mb-4"><h3 className="mb-2 text-sm font-semibold">{title}</h3>
                  <ul className="space-y-3">
                    {items.map(r => (
                      <li key={r.id} className="text-sm">
                        <p>{r.text}</p>
                        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                          {r.role_title && <Badge tone="brand">{r.role_title}</Badge>}
                          {r.years_experience !== null && <Badge>{r.years_experience}+ years</Badge>}
                          <Badge tone={r.scope === 'lahore' ? 'ok' : 'neutral'}>{r.scope === 'lahore' ? 'Lahore office' : r.scope === 'unspecified' ? 'Location not stated' : r.scope}</Badge>
                          {r.skills.map(s => <Badge key={s}>{s}</Badge>)}
                          <EvidenceBadge label={r.label as EvidenceLabel} />
                          <a className="text-xs text-info underline" href={r.source_url} target="_blank" rel="noopener noreferrer">{new URL(r.source_url).hostname}</a>
                          <span className="text-xs text-ink-mute">retrieved {date(r.retrieved_at)}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              )
            })
          )}
        </Card>
        <Card>
          <h2 className="mb-2 font-semibold">Sources</h2>
          {c.sources.length === 0 ? <p className="text-sm text-ink-soft">No sources yet.</p> : (
            <ul className="space-y-3">
              {c.sources.map(s => (
                <li key={s.id} className="text-xs text-ink-mute">
                  <EvidenceBadge label={s.label as EvidenceLabel} />
                  <a className="ml-1 text-info underline" href={s.url} target="_blank" rel="noopener noreferrer">{new URL(s.url).hostname}</a> · {date(s.retrieved_at)}{s.label !== s.stored_label && <span> (older than its freshness limit)</span>}
                  {s.excerpt && <span className="mt-1 block text-ink-soft">{s.excerpt}</span>}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  )
}
