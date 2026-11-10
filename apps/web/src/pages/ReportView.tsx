import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Badge, Button, Card, ErrorState, EvidenceBadge, LinkButton, PageHeader, Spinner } from '../components/ui'
import { api, ApiError, type Report, type ReportComponent } from '../lib/api'
import type { EvidenceLabel } from '../lib/evidence'

const SEV = { high: 'bad', medium: 'warn', low: 'neutral' } as const
const STATUS_TEXT: Record<string, string> = { missing: 'Missing', not_run: 'Not run', not_scored: 'Not scored' }

function Row({ c }: { c: ReportComponent }) {
  return (
    <li className="border-b border-line py-3 last:border-0">
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="font-medium">{c.name}</span>
        {c.value !== null ? <span className="font-semibold">{c.value} / 100</span> : <Badge tone="warn">{STATUS_TEXT[c.status]}</Badge>}
      </div>
      {c.value !== null && <div role="progressbar" aria-label={c.name} aria-valuenow={c.value} aria-valuemin={0} aria-valuemax={100} className="mt-1 h-2 rounded-full bg-canvas"><div className="h-2 rounded-full bg-brand" style={{ width: `${c.value}%` }} /></div>}
      <p className="mt-1 text-sm text-ink-soft">{c.reason}</p>
      {c.low_evidence && c.value !== null && <p className="mt-1"><Badge tone="warn">Limited evidence</Badge></p>}
      <details className="mt-1 text-xs text-ink-mute"><summary>How this is scored</summary><p className="mt-1">{c.how}</p></details>
    </li>
  )
}

export default function ReportView() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const [r, setR] = useState<Report | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirm, setConfirm] = useState(false)
  useEffect(() => { api.report(id).then(setR).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load the report.'))) }, [id])

  async function plan(h: 7 | 30) {
    setBusy(true); setNote('')
    try { setR(await api.reportRoadmap(id, h)) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not change the plan.') } finally { setBusy(false) }
  }
  async function remove() {
    setBusy(true)
    try { await api.deleteReport(id); nav('/app/results') } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not delete.'); setBusy(false) }
  }

  if (err) return <ErrorState title={err.status === 404 ? 'Report not found' : undefined} action={<LinkButton to="/app/results">Back to results</LinkButton>}>{err.message}</ErrorState>
  if (!r) return <Spinner label="Loading the report" />
  const measured = r.components.filter(c => c.kind === 'objective')
  const judged = r.components.filter(c => c.kind === 'subjective')
  return (
    <>
      <PageHeader title="Report" intro={`${r.role.title}${r.company ? ` · ${r.company.name}` : ' · general role preparation'} · ${new Date(r.created_at).toLocaleDateString('en-GB')} · rubric ${r.rubric_version}`}
        actions={<EvidenceBadge label="ai_generated_practice" />} />
      {note && <p role="alert" className="mb-3 text-sm text-bad">{note}</p>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="text-sm text-ink-soft">Overall preparation indicator</h2>
          <p className="mt-1 text-3xl font-bold">{r.overall.value === null ? 'No score yet' : `${r.overall.value} / 100`}</p>
          <p className="mt-1 text-sm text-ink-soft">{r.overall.note}</p>
          {r.overall.value !== null && <p className="mt-2 flex flex-wrap gap-1"><Badge tone="neutral">{r.overall.subjective_share}% AI judgement</Badge>{r.overall.limited && <Badge tone="warn">Limited evidence</Badge>}</p>}
          <details className="mt-2 text-xs text-ink-mute"><summary>How the overall number works</summary><p className="mt-1">{r.overall.how}</p></details>
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="font-semibold">What is missing</h2>
          {r.overall.missing.length === 0 ? <p className="mt-2 text-sm text-ink-soft">Nothing that carries weight in the overall indicator.</p> : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{r.overall.missing.map(m => <li key={m.key}><b>{m.name}</b>: {m.reason}</li>)}</ul>
          )}
          {r.notes.length > 0 && <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ink-soft">{r.notes.map(n => <li key={n}>{n}</li>)}</ul>}
        </Card>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card><h2 className="font-semibold">Measured results</h2><p className="text-xs text-ink-mute">Computed from stored answers, test counts and your resume. No AI is involved in these numbers.</p><ul className="mt-2" aria-label="Measured results">{measured.map(c => <Row key={c.key} c={c} />)}</ul></Card>
        <Card><h2 className="font-semibold">AI judgement</h2><p className="text-xs text-ink-mute">An AI's opinion of the text of your interview answers. Subjective.</p><ul className="mt-2" aria-label="AI judgement">{judged.map(c => <Row key={c.key} c={c} />)}</ul></Card>
      </div>
      {r.previous && (
        <Card className="mt-4">
          <h2 className="font-semibold">Compared with your previous report ({new Date(r.previous.created_at).toLocaleDateString('en-GB')})</h2>
          <p className="mt-1 text-sm">Overall: {r.previous.overall_before ?? 'n/a'} to {r.previous.overall_after ?? 'n/a'}{r.previous.overall_delta !== null && ` (${r.previous.overall_delta >= 0 ? '+' : ''}${r.previous.overall_delta})`}</p>
          <ul className="mt-1 text-sm text-ink-soft">{r.previous.components.map(c => <li key={c.key}>{r.components.find(x => x.key === c.key)?.name}: {c.before} to {c.after} ({c.delta >= 0 ? '+' : ''}{c.delta})</li>)}</ul>
          <p className="mt-1 text-xs text-ink-mute">{r.previous.note}</p>
        </Card>
      )}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Skill gaps</h2>
          {r.gaps.length === 0 ? <p className="mt-2 text-sm text-ink-soft">No gaps were found in the results you included.</p> : (
            <ul className="mt-2 space-y-3 text-sm">{r.gaps.map(g => (
              <li key={g.label}>
                <span className="flex items-center justify-between gap-2"><b>{g.label}</b><span className="flex gap-1"><Badge tone={SEV[g.severity]}>{g.severity}</Badge><Badge tone="neutral">{g.kind === 'objective' ? 'measured' : g.kind === 'subjective' ? 'AI judgement' : 'both'}</Badge></span></span>
                <ul className="mt-1 list-disc pl-5 text-ink-soft">{g.evidence.map((e, i) => <li key={i}>{e.detail}</li>)}</ul>
              </li>))}</ul>
          )}
        </Card>
        <Card>
          <h2 className="font-semibold">Strengths</h2>
          {r.strengths.length === 0 ? <p className="mt-2 text-sm text-ink-soft">No clear strengths yet from the results included.</p> : (
            <ul className="mt-2 space-y-2 text-sm">{r.strengths.map(s => <li key={`${s.source}-${s.label}`}><b>{s.label}</b> <span className="text-ink-soft">({s.evidence})</span></li>)}</ul>
          )}
        </Card>
      </div>
      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold">{r.roadmap.horizon}-day improvement plan</h2>
          <div className="flex gap-2">
            <Button variant={r.roadmap.horizon === 7 ? 'primary' : 'secondary'} disabled={busy || r.roadmap.horizon === 7} onClick={() => plan(7)}>7 days</Button>
            <Button variant={r.roadmap.horizon === 30 ? 'primary' : 'secondary'} disabled={busy || r.roadmap.horizon === 30} onClick={() => plan(30)}>30 days</Button>
          </div>
        </div>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-mute"><Badge tone={r.roadmap.source === 'ai' ? 'info' : 'neutral'}>{r.roadmap.source === 'ai' ? 'Written by AI, checked' : 'Built-in plan'}</Badge>{r.roadmap.note}</p>
        <ol className="mt-3 space-y-3 text-sm" aria-label="Improvement plan">{r.roadmap.items.map(it => (
          <li key={it.when}><span className="font-semibold">{it.when}: {it.focus}</span> <span className="text-ink-mute">(about {it.minutes} min)</span>
            <ul className="mt-1 list-disc pl-5 text-ink-soft">{it.tasks.map(t => <li key={t}>{t}</li>)}</ul></li>))}</ol>
      </Card>
      {r.practice_questions.length > 0 && (
        <Card className="mt-4"><h2 className="font-semibold">Suggested practice</h2><ul className="mt-2 space-y-2 text-sm" aria-label="Practice suggestions">{r.practice_questions.map((p, i) => (
          <li key={i} className="flex flex-wrap items-start gap-2"><EvidenceBadge label={p.label as EvidenceLabel} /><span>{p.type === 'coding' ? `Coding: ${p.title}` : p.prompt}{p.topic && <span className="text-ink-mute"> ({p.topic})</span>}</span></li>))}</ul></Card>
      )}
      {r.mode === 'company' && (
        <Card className="mt-4">
          <h2 className="font-semibold">Company research behind this report</h2>
          {r.sources.length === 0 ? <p className="mt-2 text-sm text-ink-soft">No approved evidence matches this role.</p> : (
            <ul className="mt-2 space-y-2 text-sm">{r.sources.map(s => <li key={s.url}><a className="text-info underline" href={s.url} target="_blank" rel="noreferrer">{s.url}</a> <EvidenceBadge label={s.label as EvidenceLabel} /><span className="block text-ink-soft">{s.text}</span></li>)}</ul>
          )}
        </Card>
      )}
      <p className="mt-4 text-xs text-ink-mute">{r.disclaimer}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {confirm ? <Button variant="danger" onClick={remove} disabled={busy}>Yes, delete this report</Button> : <Button variant="secondary" onClick={() => setConfirm(true)}>Delete report</Button>}
        <LinkButton to="/app/results" variant="ghost">Back to results</LinkButton>
      </div>
    </>
  )
}
