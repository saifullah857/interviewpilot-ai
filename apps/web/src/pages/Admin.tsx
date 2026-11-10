import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Badge, Button, Card, EmptyState, ErrorState, Field, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type AdminCompany, type AdminCompanyItem } from '../lib/api'
import { EvidenceBadge } from '../components/ui'
import type { EvidenceLabel } from '../lib/evidence'

const STATUS_TONE: Record<string, 'ok' | 'warn' | 'bad' | 'neutral' | 'info'> = { verified_lahore: 'ok', candidate: 'neutral', pending_review: 'info', stale: 'warn', rejected: 'bad' }
const RUN_TONE: Record<string, 'ok' | 'warn' | 'bad' | 'neutral' | 'info'> = { running: 'info', succeeded: 'ok', partial: 'warn', unavailable: 'warn', failed: 'bad' }
const WARNING_TEXT: Record<string, string> = {
  no_official_site: 'No official website is recorded, so no official pages were searched. Save the website above and run again.',
  ai_not_configured: "AI isn't configured on this server, so only sources were saved.",
  ai_unavailable: 'The AI service was unavailable, so some pages were not analysed.',
  ai_output_rejected: 'The AI returned output that failed our checks for some pages. Those pages produced no findings.',
  some_pages_not_fetched: 'Some official pages could not be fetched; search snippets were used instead.',
  fetch_failed_using_snippets: 'Fetching pages failed; search snippets were used instead.',
}
const today = () => new Date().toISOString().slice(0, 10)

function useAction() {
  const [msg, setMsg] = useState<{ ok: boolean; text: string; list?: string[] } | null>(null)
  const run = async (fn: () => Promise<unknown>, okText: string) => {
    try { await fn(); setMsg({ ok: true, text: okText }); return true } catch (e) {
      const list = e instanceof ApiError && Array.isArray(e.details) ? (e.details as unknown as string[]) : undefined
      setMsg({ ok: false, text: e instanceof ApiError ? e.message : 'Something went wrong.', list }); return false
    }
  }
  return { msg, run, clear: () => setMsg(null) }
}

export default function Admin() {
  const [list, setList] = useState<AdminCompanyItem[] | null>(null)
  const [status, setStatus] = useState('')
  const [sel, setSel] = useState<AdminCompany | null>(null)
  const [error, setError] = useState('')
  const [newName, setNewName] = useState('')
  const act = useAction()

  const load = useCallback(() => api.adminCompanies(status || undefined).then(setList).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load.')), [status])
  useEffect(() => { load() }, [load])
  const open = (id: string) => api.adminCompany(id).then(setSel).catch(() => setError('Could not open that company.'))
  const apply = async (fn: () => Promise<AdminCompany>, okText: string) => { if (await act.run(async () => setSel(await fn()), okText)) load() }

  if (error) return <ErrorState>{error}</ErrorState>
  if (!list) return <Spinner label="Loading companies" />
  return (
    <>
      <PageHeader title="Company review" intro="Verify a company's Lahore presence from official sources. Nothing is public until you verify it." />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <Select id="st" label="Status" value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All</option>
            {Object.keys(STATUS_TONE).map(s => <option key={s}>{s}</option>)}
          </Select>
          {list.length === 0 ? <div className="mt-3"><EmptyState title="No companies">Run <code>python -m app.cli import-seed</code> or add one below.</EmptyState></div> : (
            <ul className="mt-3 max-h-96 divide-y divide-line overflow-y-auto" aria-label="Companies to review">
              {list.map(c => (
                <li key={c.id}>
                  <button className={`flex w-full items-center justify-between gap-2 px-1 py-2 text-left text-sm hover:bg-canvas ${sel?.id === c.id ? 'font-semibold' : ''}`} onClick={() => open(c.id)}>
                    <span>{c.name}</span><Badge tone={STATUS_TONE[c.verification_status]}>{c.verification_status}</Badge>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <form className="mt-4 flex items-end gap-2" onSubmit={async (e: FormEvent) => { e.preventDefault(); if (newName.trim()) { await apply(() => api.adminCreateCompany({ name: newName.trim() }), 'Candidate added.'); setNewName('') } }}>
            <div className="flex-1"><Field id="new-company" label="Add a candidate" value={newName} onChange={e => setNewName(e.target.value)} /></div>
            <Button type="submit" variant="secondary">Add</Button>
          </form>
        </Card>
        <div className="space-y-4 lg:col-span-2">
          {act.msg && (
            <div role={act.msg.ok ? 'status' : 'alert'} className={`rounded-lg p-3 text-sm ${act.msg.ok ? 'bg-ok-soft text-ok' : 'bg-bad-soft text-bad'}`}>
              {act.msg.text}{act.msg.list && <ul className="mt-1 list-disc pl-5">{act.msg.list.map(x => <li key={x}>{x}</li>)}</ul>}
            </div>
          )}
          {sel ? <Detail key={sel.id} c={sel} apply={apply} run={act.run} reload={() => open(sel.id)} /> : <EmptyState title="Select a company">Pick one on the left to see its locations and sources.</EmptyState>}
        </div>
      </div>
    </>
  )
}

function Detail({ c, apply, run, reload }: { c: AdminCompany; apply: (fn: () => Promise<AdminCompany>, ok: string) => Promise<void>; run: (fn: () => Promise<unknown>, ok: string) => Promise<boolean>; reload: () => Promise<unknown> }) {
  const [info, setInfo] = useState({ website: c.website ?? '', careers_url: c.careers_url ?? '', description: c.description, tech: c.tech_focus.join(', ') })
  const [chosen, setChosen] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [loc, setLoc] = useState({ locality: '', address: '', is_lahore: true })
  const [src, setSrc] = useState({ url: '', source_type: 'official_website', label: 'official_verified', supports_lahore: true, excerpt: '', date: today() })
  const [force, setForce] = useState(false)
  const running = c.latest_run?.status === 'running'
  useEffect(() => {
    if (!running) return
    const t = setInterval(() => { reload() }, 3000)  // poll until the background run finishes
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, c.id])
  const toggle = (id: string) => setChosen(x => (x.includes(id) ? x.filter(i => i !== id) : [...x, id]))

  return (
    <>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-xl font-semibold">{c.name}</h2><Badge tone={STATUS_TONE[c.verification_status]}>{c.verification_status}</Badge></div>
        {c.last_verified_at && <p className="mt-1 text-xs text-ink-mute">Last verified {new Date(c.last_verified_at).toLocaleDateString()}</p>}
        <form className="mt-4 grid gap-2 sm:grid-cols-2" onSubmit={(e: FormEvent) => { e.preventDefault(); apply(() => api.adminUpdateCompany(c.id, { website: info.website || null, careers_url: info.careers_url || null, description: info.description, tech_focus: info.tech.split(',').map(t => t.trim()).filter(Boolean) }), 'Details saved.') }}>
          <Field id="co-website" label="Official website" type="url" value={info.website} onChange={e => setInfo({ ...info, website: e.target.value })} />
          <Field id="co-careers" label="Official careers page" type="url" value={info.careers_url} onChange={e => setInfo({ ...info, careers_url: e.target.value })} />
          <div className="sm:col-span-2"><Field id="co-desc" label="Short description (your own words)" maxLength={2000} value={info.description} onChange={e => setInfo({ ...info, description: e.target.value })} /></div>
          <Field id="co-tech" label="Technologies (comma separated)" value={info.tech} onChange={e => setInfo({ ...info, tech: e.target.value })} />
          <div className="flex items-end"><Button type="submit" variant="secondary">Save details</Button></div>
        </form>
        <h3 className="mt-4 text-sm font-semibold">Locations</h3>
        {c.locations.length === 0 ? <p className="text-sm text-ink-soft">None yet.</p> : <ul className="text-sm">{c.locations.map(l => <li key={l.id}>{l.locality}{l.address ? `, ${l.address}` : ''} {l.is_lahore ? <Badge tone="ok">Lahore</Badge> : <Badge>Not Lahore</Badge>}</li>)}</ul>}
        <form className="mt-3 grid gap-2 sm:grid-cols-4" onSubmit={(e: FormEvent) => { e.preventDefault(); apply(() => api.adminAddLocation(c.id, { locality: loc.locality, address: loc.address || undefined, is_lahore: loc.is_lahore }), 'Location added.'); setLoc({ ...loc, locality: '', address: '' }) }}>
          <Field id="loc-locality" label="Locality" value={loc.locality} onChange={e => setLoc({ ...loc, locality: e.target.value })} placeholder="e.g. Gulberg" />
          <Field id="loc-address" label="Address (as on the source)" value={loc.address} onChange={e => setLoc({ ...loc, address: e.target.value })} />
          <label className="flex items-end gap-2 pb-3 text-sm"><input type="checkbox" checked={loc.is_lahore} onChange={e => setLoc({ ...loc, is_lahore: e.target.checked })} /> In Lahore</label>
          <div className="flex items-end"><Button type="submit" variant="secondary" disabled={loc.locality.trim().length < 2}>Add location</Button></div>
        </form>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold">Sources (tick the ones that support your decision)</h3>
        {c.sources.length === 0 ? <p className="mt-1 text-sm text-ink-soft">No sources yet. Add the company's official contact or careers page below.</p> : (
          <ul className="mt-2 space-y-3">
            {c.sources.map(s => (
              <li key={s.id} className="flex gap-3 text-sm">
                <input type="checkbox" aria-label={`Use source ${s.url}`} checked={chosen.includes(s.id)} onChange={() => toggle(s.id)} className="mt-1" />
                <div>
                  <a className="break-all text-info underline" href={s.url} target="_blank" rel="noopener noreferrer">{s.url}</a>
                  <div className="mt-1 flex flex-wrap gap-1.5"><Badge tone="info">{s.source_type}</Badge><Badge tone={s.label === 'official_verified' ? 'ok' : 'neutral'}>{s.stored_label}</Badge>{s.supports_lahore && <Badge tone="ok">supports Lahore</Badge>}<Badge>{s.status}</Badge></div>
                  {s.excerpt && <p className="mt-1 text-ink-soft">{s.excerpt}</p>}
                  <div className="mt-1 flex gap-2">
                    <button className="text-xs text-info underline disabled:opacity-40" disabled={s.status === 'active'} onClick={() => apply(() => api.adminSetSource(c.id, s.id, 'active'), 'Source approved.')}>Approve source</button>
                    <button className="text-xs text-info underline disabled:opacity-40" disabled={s.status === 'rejected'} onClick={() => apply(() => api.adminSetSource(c.id, s.id, 'rejected'), 'Source rejected, along with findings that rely on it.')}>Reject source</button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
        <form className="mt-4 grid gap-2 sm:grid-cols-2" onSubmit={(e: FormEvent) => { e.preventDefault(); apply(() => api.adminAddSource(c.id, { url: src.url, source_type: src.source_type, label: src.label, supports_lahore: src.supports_lahore, excerpt: src.excerpt, retrieved_at: `${src.date}T00:00:00Z` }), 'Source added.'); setSrc({ ...src, url: '', excerpt: '' }) }}>
          <div className="sm:col-span-2"><Field id="src-url" label="Page URL (open it yourself first)" type="url" value={src.url} onChange={e => setSrc({ ...src, url: e.target.value })} /></div>
          <Select id="src-type" label="Source type" value={src.source_type} onChange={e => setSrc({ ...src, source_type: e.target.value })}>
            {['official_website', 'careers_page', 'job_posting', 'registry', 'candidate_report', 'other'].map(t => <option key={t}>{t}</option>)}
          </Select>
          <Select id="src-label" label="Label" value={src.label} onChange={e => setSrc({ ...src, label: e.target.value })}>
            {['official_verified', 'public_candidate_report', 'unverified_or_outdated'].map(t => <option key={t}>{t}</option>)}
          </Select>
          <div className="sm:col-span-2"><Field id="src-excerpt" label="What it shows (your own words, short)" maxLength={500} value={src.excerpt} onChange={e => setSrc({ ...src, excerpt: e.target.value })} /></div>
          <Field id="src-date" label="Date you checked it" type="date" value={src.date} onChange={e => setSrc({ ...src, date: e.target.value })} />
          <label className="flex items-end gap-2 pb-3 text-sm"><input type="checkbox" checked={src.supports_lahore} onChange={e => setSrc({ ...src, supports_lahore: e.target.checked })} /> Shows a Lahore office</label>
          <div><Button type="submit" variant="secondary" disabled={!src.url}>Add source</Button></div>
        </form>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold">Research (automated)</h3>
        {c.verification_status !== 'verified_lahore' ? <p className="mt-1 text-sm text-ink-soft">Research is available once the company is verified.</p> : (
          <>
            <p className="mt-1 text-xs text-ink-mute">Searches the web for official hiring pages and public reports, then proposes findings. Nothing is shown to users until you approve it. Each run uses a few search credits.</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <Button onClick={async () => { if (await run(async () => { await api.adminStartResearch(c.id, force) }, 'Research started.')) await reload() }} disabled={running}>{running ? 'Researching…' : 'Run research'}</Button>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={force} onChange={e => setForce(e.target.checked)} /> Refresh even if a recent run exists</label>
            </div>
            {c.latest_run && (
              <div className="mt-3 rounded-lg bg-canvas p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2"><Badge tone={RUN_TONE[c.latest_run.status]}>{c.latest_run.status}</Badge><span>{c.latest_run.summary.message ?? (running ? 'Working…' : '')}</span></div>
                {(c.latest_run.summary.warnings ?? []).length > 0 && <ul className="mt-2 list-disc pl-5 text-xs text-warn">{(c.latest_run.summary.warnings ?? []).map(w => <li key={w}>{WARNING_TEXT[w] ?? w}</li>)}</ul>}
                {(c.latest_run.summary.conflicts ?? []).length > 0 && <p className="mt-2 text-xs text-bad">Sources disagree: {(c.latest_run.summary.conflicts ?? []).map(x => `${x.role} (${x.years.join(' vs ')} years)`).join('; ')}. Check them before approving.</p>}
              </div>
            )}
          </>
        )}
        {c.findings.length > 0 && (
          <ul className="mt-4 space-y-4" aria-label="Research findings">
            {c.findings.map(f => (
              <li key={f.id} className="border-t border-line pt-3 text-sm">
                <p>{f.text}</p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  <Badge>{f.kind.replace('_', ' ')}</Badge>{f.role_title && <Badge tone="brand">{f.role_title}</Badge>}
                  {f.skills.map(s => <Badge key={s}>{s}</Badge>)}
                  <Badge tone={f.scope === 'lahore' ? 'ok' : 'warn'}>{f.scope === 'lahore' ? 'Mentions Lahore' : 'Location not stated'}</Badge>
                  <EvidenceBadge label={f.label as EvidenceLabel} /><Badge tone={f.status === 'active' ? 'ok' : f.status === 'rejected' ? 'bad' : 'neutral'}>{f.status}</Badge>
                </div>
                <a className="mt-1 block break-all text-xs text-info underline" href={f.source_url} target="_blank" rel="noopener noreferrer">{f.source_url}</a>
                <div className="mt-2 flex gap-2">
                  <Button variant="secondary" disabled={f.status === 'active'} onClick={() => apply(() => api.adminSetFinding(c.id, f.id, 'active'), 'Finding approved.')}>Approve</Button>
                  <Button variant="secondary" disabled={f.status === 'rejected'} onClick={() => apply(() => api.adminSetFinding(c.id, f.id, 'rejected'), 'Finding rejected.')}>Reject</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold">Decision</h3>
        <div className="mt-2"><label htmlFor="notes" className="mb-1 block text-sm font-medium">Review notes</label>
          <textarea id="notes" rows={3} maxLength={2000} value={notes} onChange={e => setNotes(e.target.value)} className="w-full rounded-lg border border-line px-3 py-2 text-sm" placeholder="What you checked and why" /></div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button onClick={() => apply(() => api.adminDecide(c.id, { decision: 'verified', evidence_ids: chosen, notes }), 'Verified. It now appears in the directory.')}>Verify as Lahore company</Button>
          <Button variant="danger" onClick={() => apply(() => api.adminDecide(c.id, { decision: 'rejected', evidence_ids: chosen, notes }), 'Rejected.')}>Reject</Button>
          {c.verification_status === 'verified_lahore' && <Button variant="secondary" onClick={() => apply(() => api.adminDecide(c.id, { decision: 'marked_stale', evidence_ids: [], notes }), 'Marked stale and hidden.')}>Mark stale</Button>}
        </div>
        {c.verifications.length > 0 && (
          <ul className="mt-4 space-y-1 border-t border-line pt-3 text-xs text-ink-soft">{c.verifications.map(v => <li key={v.id}>{new Date(v.created_at).toLocaleString()}: {v.decision}{v.notes ? ` (${v.notes})` : ''}</li>)}</ul>
        )}
      </Card>
    </>
  )
}
