import { useCallback, useEffect, useState, type ChangeEvent } from 'react'
import { UploadCloud } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type DiscoverCompany, type Fit, type FitGroup, type Recommendations, type ResumeItem } from '../lib/api'

const MAX_MB = 5
const OK_EXT = ['.pdf', '.docx']
const when = (s: string) => new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const msg = (e: unknown) => (e instanceof ApiError ? e.message : 'Something went wrong. Try again.')

function SourceBadge({ source }: { source: 'stated' | 'inferred' }) {
  return source === 'stated' ? <Badge tone="ok" title="Written in your resume">Stated</Badge> : <Badge tone="info" title="Concluded by the AI, not written in your resume">Inferred</Badge>
}

function Group({ title, g }: { title: string; g: FitGroup }) {
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="text-xs text-ink-mute">{Math.round(g.coverage_stated * 100)}% shown in your resume ({Math.round(g.coverage_with_inferred * 100)}% counting AI inferences)</p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {g.matched.map(m => <span key={m.skill} className="inline-flex items-center gap-1"><Badge tone="ok">{m.skill}</Badge><SourceBadge source={m.source} /></span>)}
        {g.missing.map(m => <Badge key={m} tone="warn" title="Not shown in your resume">Missing: {m}</Badge>)}
      </div>
    </div>
  )
}

export default function Resume() {
  const [list, setList] = useState<ResumeItem[] | null>(null)
  const [error, setError] = useState('')
  const [sel, setSel] = useState<string | null>(null)
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState('')
  const [confirmDel, setConfirmDel] = useState(false)
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [role, setRole] = useState('')
  const [fit, setFit] = useState<Fit | null>(null)
  const [rec, setRec] = useState<Recommendations | null>(null)
  const [recRole, setRecRole] = useState('')
  const [recErr, setRecErr] = useState('')
  const companies: DiscoverCompany[] = rec?.companies ?? []
  const [company, setCompany] = useState('')

  const load = useCallback(() => api.resumes().then(r => { setList(r); setSel(s => s ?? r[0]?.id ?? null) }).catch(e => setError(msg(e))), [])
  useEffect(() => { load(); api.roles().then(setRoles).catch(() => setRoles([])) }, [load])

  const current = list?.find(r => r.id === sel) ?? null
  useEffect(() => { setFit(null); setRole(''); setCompany(''); setConfirmDel(false); setRec(null); setRecRole('') }, [sel])
  const analysedId = current?.latest ? current.id : null
  const verKey = current?.latest?.id ?? ''
  useEffect(() => {
    if (!analysedId) return
    let live = true
    api.discoverRecommendations(analysedId, recRole || undefined).then(r => { if (live) { setRec(r); setRecErr('') } }).catch(e => { if (live) setRecErr(msg(e)) })
    return () => { live = false }
  }, [analysedId, recRole, verKey])

  async function onPick(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase()
    if (!OK_EXT.includes(ext)) return setNote({ ok: false, text: 'Choose a PDF or DOCX file.' })
    if (f.size > MAX_MB * 1024 * 1024) return setNote({ ok: false, text: `File is larger than ${MAX_MB} MB.` })
    setBusy('upload'); setNote(null)
    try {
      const r = await api.uploadResume(f)
      setNote({ ok: true, text: r.duplicate ? 'You already uploaded this file, so I opened the existing copy.' : 'Uploaded. Review the privacy note, then analyse it.' })
      await load(); setSel(r.id)
    } catch (err) { setNote({ ok: false, text: msg(err) }) } finally { setBusy('') }
  }

  async function analyse() {
    if (!current) return
    setBusy('analyse'); setNote(null); setFit(null)
    try { const r = await api.analyzeResume(current.id); setList(l => l?.map(x => (x.id === r.id ? r : x)) ?? l); setNote({ ok: true, text: 'Analysis saved.' }) }
    catch (err) { setNote({ ok: false, text: msg(err) }) } finally { setBusy('') }
  }

  async function remove() {
    if (!current) return
    try { await api.deleteResume(current.id); setSel(null); setConfirmDel(false); setNote({ ok: true, text: 'Resume deleted, including the stored file.' }); await load() }
    catch (err) { setNote({ ok: false, text: msg(err) }) }
  }

  async function compare(slug: string, companySlug: string) {
    setRole(slug); setCompany(companySlug); setFit(null)
    if (!slug || !current) return
    try { setFit(await api.resumeFit(current.id, slug, companySlug || undefined)) } catch (err) { setNote({ ok: false, text: msg(err) }) }
  }

  if (error) return <ErrorState>{error}</ErrorState>
  if (!list) return <Spinner label="Loading your resumes" />
  const v = current?.latest
  const p = v?.parsed

  return (
    <>
      <PageHeader title="Resume" intro="Upload a PDF or DOCX. We extract your skills, projects and experience, and keep what you wrote separate from what the AI infers." />
      <Card>
        <label htmlFor="resume" className="flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-line p-8 text-center hover:bg-canvas">
          <UploadCloud aria-hidden className="text-brand-deep" />
          <span className="font-medium">{busy === 'upload' ? 'Uploading…' : 'Choose a resume file'}</span>
          <span className="text-sm text-ink-mute">PDF or DOCX, text-based, up to {MAX_MB} MB</span>
        </label>
        <input id="resume" type="file" accept=".pdf,.docx" onChange={onPick} className="sr-only" disabled={busy !== ''} />
        <p className="mt-3 text-xs text-ink-mute">
          Privacy: when you press Analyse, the text of your resume is sent to Groq, our AI provider, with emails, phone numbers, links and ID numbers removed first. Don't upload anything you aren't comfortable sharing with that provider. You can delete a resume, and its stored file, at any time.
        </p>
        {note && <p role={note.ok ? 'status' : 'alert'} className={`mt-3 text-sm ${note.ok ? 'text-ok' : 'text-bad'}`}>{note.text}</p>}
      </Card>

      {list.length === 0 ? <div className="mt-4"><EmptyState title="No resumes yet">Upload one to get started.</EmptyState></div> : (
        <Card className="mt-4">
          <h2 className="mb-2 font-semibold">Your resumes</h2>
          <ul className="divide-y divide-line" aria-label="Your resumes">
            {list.map(r => (
              <li key={r.id}>
                <button onClick={() => setSel(r.id)} aria-current={r.id === sel} className={`flex w-full items-center justify-between gap-3 py-2 text-left text-sm ${r.id === sel ? 'font-semibold' : ''}`}>
                  <span>{r.filename}<span className="block text-xs font-normal text-ink-mute">{when(r.created_at)}, {r.pages} page{r.pages === 1 ? '' : 's'}</span></span>
                  <Badge tone={r.analyzed ? 'ok' : 'neutral'}>{r.analyzed ? 'Analysed' : 'Not analysed'}</Badge>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {current && (
        <Card className="mt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">{current.filename}</h2>
            <div className="flex gap-2">
              <Button onClick={analyse} disabled={busy !== ''}>{busy === 'analyse' ? 'Analysing…' : v ? 'Analyse again' : 'Analyse with AI'}</Button>
              {!confirmDel ? <Button variant="secondary" onClick={() => setConfirmDel(true)}>Delete</Button>
                : <><Button variant="danger" onClick={remove}>Yes, delete it</Button><Button variant="secondary" onClick={() => setConfirmDel(false)}>Cancel</Button></>}
            </div>
          </div>
          {busy === 'analyse' && <Spinner label="Analysing, this can take up to a minute" />}
          {(current.injection_signals.length > 0 || current.truncated || (v && (v.report.dropped_ungrounded > 0 || v.report.downgraded_to_inferred > 0))) && (
            <ul className="mt-3 list-disc space-y-1 rounded-lg bg-warn-soft p-3 pl-7 text-sm text-warn">
              {current.injection_signals.length > 0 && <li>Your resume contains text that looks like instructions to an AI. It was treated as ordinary text and ignored.</li>}
              {current.truncated && <li>Your resume was very long, so only the first part was analysed.</li>}
              {v && v.report.dropped_ungrounded > 0 && <li>{v.report.dropped_ungrounded} item(s) were removed because the AI could not point to matching text in your resume.</li>}
              {v && v.report.downgraded_to_inferred > 0 && <li>{v.report.downgraded_to_inferred} skill(s) were relabelled "Inferred" because they could not be matched to your text.</li>}
            </ul>
          )}
          {!p ? <p className="mt-3 text-sm text-ink-soft">Not analysed yet. Analysis uses the AI provider described above.</p> : (
            <div className="mt-4 space-y-5">
              <p className="text-xs text-ink-mute">Analysed {when(v!.created_at)} with {v!.provider} ({v!.model}). Extracted by AI and checked against your text; it can still contain mistakes.</p>
              <section><h3 className="mb-2 text-sm font-semibold">Skills</h3>
                {p.skills.length === 0 ? <p className="text-sm text-ink-soft">None found.</p> : <div className="flex flex-wrap gap-2">{p.skills.map(s => <span key={s.name} className="inline-flex items-center gap-1"><Badge>{s.name}</Badge><SourceBadge source={s.source} /></span>)}</div>}</section>
              {p.education.length > 0 && <section><h3 className="mb-2 text-sm font-semibold">Education</h3><ul className="space-y-1 text-sm">{p.education.map((e, i) => <li key={i}>{[e.degree, e.field].filter(Boolean).join(' in ')} {e.degree || e.field ? '· ' : ''}{e.institution}{e.period ? ` (${e.period})` : ''}</li>)}</ul></section>}
              {p.experience.length > 0 && <section><h3 className="mb-2 text-sm font-semibold">Experience</h3><ul className="space-y-2 text-sm">{p.experience.map((e, i) => <li key={i}><b>{e.title}</b>{e.organization ? `, ${e.organization}` : ''}{e.period ? ` (${e.period})` : ''}<span className="block text-ink-soft">{e.summary}</span></li>)}</ul></section>}
              {p.projects.length > 0 && <section><h3 className="mb-2 text-sm font-semibold">Projects</h3><ul className="space-y-2 text-sm">{p.projects.map((e, i) => <li key={i}><b>{e.name}</b><span className="block text-ink-soft">{e.description}</span></li>)}</ul></section>}
              {p.achievements.length > 0 && <section><h3 className="mb-2 text-sm font-semibold">Achievements</h3><ul className="list-disc pl-5 text-sm">{p.achievements.map((a, i) => <li key={i}>{a.text}{a.measurable && <> <Badge tone="ok">measurable</Badge></>}</li>)}</ul></section>}
              {p.inferences.length > 0 && (
                <section><h3 className="mb-1 text-sm font-semibold">AI conclusions</h3><p className="mb-2 text-xs text-ink-mute">These are not written in your resume. They are the AI's guesses from what is there.</p>
                  <ul className="space-y-1 text-sm">{p.inferences.map((x, i) => <li key={i}><SourceBadge source="inferred" /> {x.statement} <span className="text-ink-mute">(because: {x.basis}; confidence {x.confidence})</span></li>)}</ul></section>
              )}
              <section className="rounded-xl border border-brand/40 bg-brand-soft p-4 text-black">
                <h3 className="text-base font-semibold text-black">Best fit for your resume</h3>
                {recErr && <p role="alert" className="mt-2 text-sm text-bad">{recErr}</p>}
                {!rec && !recErr && <Spinner label="Finding roles and Lahore companies" />}
                {rec && (
                  <>
                    <p className="mt-1 text-sm">Pick the role you want. Companies are ranked by how their focus area and technologies match that role and your resume.</p>
                    <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Roles that fit your resume">
                      {rec.roles.slice(0, 6).map(r => (
                        <button key={r.slug} onClick={() => setRecRole(r.slug)} aria-pressed={rec.role.slug === r.slug}
                          className={`rounded-full border px-3 py-1.5 text-sm ${rec.role.slug === r.slug ? 'border-brand bg-brand font-semibold text-black' : 'border-line bg-surface text-black hover:bg-canvas'}`}>{r.title} · {r.score}%</button>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-black">Skills matching {rec.role.title}: {rec.role.matched.length ? rec.role.matched.join(', ') : 'none found yet'}. Still to show: {rec.role.missing.length ? rec.role.missing.join(', ') : 'nothing from the core list'}.</p>
                    <ul className="mt-3 grid gap-3 md:grid-cols-2" aria-label="Recommended Lahore companies">
                      {rec.companies.slice(0, 8).map(c => (
                        <li key={c.slug} className="rounded-lg border border-line bg-surface p-3 text-ink">
                          <div className="flex items-start justify-between gap-2">
                            <b>{c.name}</b>
                            <Badge tone="brand" title={c.match?.basis}>{c.match?.score ?? 0}% match</Badge>
                          </div>
                          <p className="mt-1 text-xs text-ink-mute">{c.status === 'verified_lahore' ? 'Lahore office confirmed' : 'Lahore candidate, not checked yet'} · {c.focus_areas.join(', ')}</p>
                          {c.match?.reasons.map(x => <p key={x} className="mt-1 text-xs text-ink-soft">{x}</p>)}
                          <div className="mt-2 flex flex-wrap gap-2">
                            <Link className="text-sm text-info underline" to={`/app/companies/${c.slug}`}>Research this company</Link>
                            <Link className="text-sm text-info underline" to={`/app/assessment/setup?company=${c.slug}&role=${rec.role.slug}&resume=${current!.id}`}>Practise for it</Link>
                          </div>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-2 text-xs text-black">{rec.companies[0]?.match?.basis}</p>
                  </>
                )}
              </section>
              <section className="border-t border-line pt-4">
                <h3 className="mb-2 text-sm font-semibold">Compare with a role</h3>
                <div className="grid max-w-2xl gap-3 sm:grid-cols-2">
                  <Select id="fit-role" label="Target role" value={role} onChange={e => compare(e.target.value, company)}><option value="">Choose a role</option>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</Select>
                  <Select id="fit-company" label="Lahore company (optional)" value={company} onChange={e => compare(role, e.target.value)}><option value="">General role preparation</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select>
                </div>
                {fit && (
                  <div className="mt-3 space-y-3">
                    <Group title="Core skills" g={fit.required} /><Group title="Nice to have" g={fit.preferred} />
                    {fit.notes.map(n => <p key={n} className="text-xs text-ink-soft">{n}</p>)}
                    <p className="text-xs text-ink-mute">{fit.catalog_note} {fit.disclaimer}</p>
                    {fit.company && (
                      <div className="rounded-lg border border-line p-3">
                        <h3 className="text-sm font-semibold">Compared with {fit.company.company.name}</h3>
                        {!fit.company.available ? <p className="mt-1 text-sm text-ink-soft">{fit.company.reason}</p> : (
                          <>
                            <p className="text-xs text-ink-mute">{Math.round((fit.company.coverage_stated ?? 0) * 100)}% of the weighted skills are shown in your resume ({Math.round((fit.company.coverage_with_inferred ?? 0) * 100)}% counting AI inferences), from {fit.company.evidence_count} approved source item(s).</p>
                            <ul className="mt-2 space-y-2 text-sm">
                              {fit.company.skills?.map(s => (
                                <li key={s.skill}>
                                  <span className="inline-flex flex-wrap items-center gap-1.5"><b>{s.skill}</b>{s.have ? <SourceBadge source={s.have} /> : <Badge tone="warn">Not in your resume</Badge>}<Badge title="How much the evidence counts">weight {s.weight}</Badge></span>
                                  <span className="block text-xs text-ink-mute">{s.reasons.join('; ')}. {s.sources.map(x => <a key={x.url} className="text-info underline" href={x.url} target="_blank" rel="noopener noreferrer">{new URL(x.url).hostname}</a>)}</span>
                                </li>
                              ))}
                            </ul>
                            {fit.company.notes?.map(n => <p key={n} className="mt-2 text-xs text-ink-soft">{n}</p>)}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </section>
            </div>
          )}
        </Card>
      )}
    </>
  )
}
