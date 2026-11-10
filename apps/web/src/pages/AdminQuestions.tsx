import { useCallback, useEffect, useState } from 'react'
import { Badge, Button, Card, EmptyState, ErrorState, Field, PageHeader, Select, Spinner } from '../components/ui'
import { api, ApiError, type AdminQuestion, type CompanyFocus } from '../lib/api'

const blank = (): Omit<AdminQuestion, 'id'> => ({ slug: '', kind: 'technical', category: '', difficulty: 'easy', roles: [], companies: [], topics: [], prompt: '', ideal_answer: '', key_points: [], follow_ups: [], options: [], answer_index: null, explanation: '', source_label: 'company_focused_practice', source_note: '', enabled: true })
const lines = (t: string) => t.split('\n').map(x => x.trim()).filter(Boolean)

export default function AdminQuestions() {
  const [roles, setRoles] = useState<{ slug: string; title: string }[]>([])
  const [companies, setCompanies] = useState<CompanyFocus[]>([])
  const [items, setItems] = useState<AdminQuestion[] | null>(null)
  const [total, setTotal] = useState(0)
  const [company, setCompany] = useState('')
  const [kind, setKind] = useState('')
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [form, setForm] = useState<(Omit<AdminQuestion, 'id'> & { editing?: boolean }) | null>(null)
  const [formError, setFormError] = useState('')

  const load = useCallback(() => {
    const p: Record<string, string> = {}
    if (company) p.company = company
    if (kind) p.kind = kind
    if (text.trim()) p.q = text.trim()
    api.adminQuestions(p).then(r => { setItems(r.items); setTotal(r.total); setError('') }).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load questions.'))
  }, [company, kind, text])
  useEffect(() => { api.roles().then(setRoles).catch(() => setRoles([])); api.codingCompanies().then(r => setCompanies(r.companies)).catch(() => setCompanies([])) }, [])
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [load])

  const toggle = (q: AdminQuestion) => api.adminUpdateQuestion(q.slug, { enabled: !q.enabled }).then(load).catch(e => setError(e instanceof ApiError ? e.message : 'Could not update.'))
  const remove = (q: AdminQuestion) => { if (window.confirm(`Delete ${q.slug}? This cannot be undone.`)) api.adminDeleteQuestion(q.slug).then(load).catch(e => setError(e instanceof ApiError ? e.message : 'Could not delete.')) }
  const save = async () => {
    if (!form) return
    setFormError('')
    const { editing, slug, ...rest } = form
    try {
      if (editing) await api.adminUpdateQuestion(slug, rest)
      else await api.adminCreateQuestion({ slug, ...rest })
      setForm(null); load()
    } catch (e) { setFormError(e instanceof ApiError ? (e.details ? JSON.stringify(e.details).slice(0, 300) : e.message) : 'Could not save.') }
  }
  const set = (patch: Partial<Omit<AdminQuestion, 'id'>>) => setForm(f => (f ? { ...f, ...patch } : f))
  const multi = (e: React.ChangeEvent<HTMLSelectElement>) => Array.from(e.target.selectedOptions).map(o => o.value)
  const mc = form && (form.kind === 'mcq' || form.kind === 'output')

  return (
    <>
      <PageHeader title="Manage questions" intro="Add, edit, disable or delete questions of the question bank. The same rules as the import apply." actions={<Button onClick={() => { setForm({ ...blank() }); setFormError('') }}>Add question</Button>} />
      {form && (
        <Card className="mb-4">
          <h2 className="font-semibold">{form.editing ? `Edit ${form.slug}` : 'New question'}</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Field id="aq-slug" label="Slug" value={form.slug} disabled={form.editing} onChange={e => set({ slug: e.target.value })} hint="Lowercase letters, digits and dashes, for example arbisoft-tech-30" />
            <Field id="aq-cat" label="Category" value={form.category} onChange={e => set({ category: e.target.value })} />
            <Select id="aq-kind" label="Type" value={form.kind} onChange={e => set({ kind: e.target.value })}><option value="technical">Technical</option><option value="scenario">Scenario</option><option value="mcq">MCQ</option><option value="output">Output</option></Select>
            <Select id="aq-diff" label="Difficulty" value={form.difficulty} onChange={e => set({ difficulty: e.target.value })}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></Select>
            <div><label htmlFor="aq-comp" className="mb-1 block text-sm font-medium">Companies (hold Ctrl to pick several)</label><select id="aq-comp" multiple className="h-32 w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.companies} onChange={e => set({ companies: multi(e) })}>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</select></div>
            <div><label htmlFor="aq-roles" className="mb-1 block text-sm font-medium">Roles</label><select id="aq-roles" multiple className="h-32 w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.roles} onChange={e => set({ roles: multi(e) })}>{roles.map(r => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></div>
          </div>
          <label htmlFor="aq-prompt" className="mb-1 mt-3 block text-sm font-medium">Question</label>
          <textarea id="aq-prompt" rows={3} className="w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.prompt} onChange={e => set({ prompt: e.target.value })} />
          {mc ? (
            <>
              <label htmlFor="aq-opts" className="mb-1 mt-3 block text-sm font-medium">Options (one per line, at least 3)</label>
              <textarea id="aq-opts" rows={4} className="w-full rounded-lg border border-line bg-surface p-2 font-mono text-sm" value={form.options.join('\n')} onChange={e => set({ options: lines(e.target.value) })} />
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <Field id="aq-ans" label="Correct option number" type="number" min={1} value={form.answer_index === null ? '' : form.answer_index + 1} onChange={e => set({ answer_index: e.target.value ? Number(e.target.value) - 1 : null })} />
                <Field id="aq-expl" label="Explanation" value={form.explanation} onChange={e => set({ explanation: e.target.value })} />
              </div>
            </>
          ) : (
            <>
              <label htmlFor="aq-ideal" className="mb-1 mt-3 block text-sm font-medium">Ideal answer</label>
              <textarea id="aq-ideal" rows={3} className="w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.ideal_answer} onChange={e => set({ ideal_answer: e.target.value })} />
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div><label htmlFor="aq-kp" className="mb-1 block text-sm font-medium">Key points (one per line, at least 2)</label><textarea id="aq-kp" rows={3} className="w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.key_points.join('\n')} onChange={e => set({ key_points: lines(e.target.value) })} /></div>
                <div><label htmlFor="aq-fu" className="mb-1 block text-sm font-medium">Follow-up questions (one per line)</label><textarea id="aq-fu" rows={3} className="w-full rounded-lg border border-line bg-surface p-2 text-sm" value={form.follow_ups.join('\n')} onChange={e => set({ follow_ups: lines(e.target.value) })} /></div>
              </div>
            </>
          )}
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Select id="aq-src" label="Source" value={form.source_label} onChange={e => set({ source_label: e.target.value })}><option value="company_focused_practice">Company-focused practice</option><option value="reported">Reported (needs a source note)</option><option value="verified">Verified (needs a source note)</option></Select>
            <Field id="aq-note" label="Source note" value={form.source_note} onChange={e => set({ source_note: e.target.value })} hint="Where the claim comes from. Required for reported and verified." />
          </div>
          {formError && <p role="alert" className="mt-3 text-sm text-bad">{formError}</p>}
          <div className="mt-3 flex gap-2"><Button onClick={save}>Save question</Button><Button variant="secondary" onClick={() => setForm(null)}>Cancel</Button></div>
        </Card>
      )}
      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <Select id="aqf-company" label="Company" value={company} onChange={e => setCompany(e.target.value)}><option value="">All</option>{companies.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select>
          <Select id="aqf-kind" label="Type" value={kind} onChange={e => setKind(e.target.value)}><option value="">Any</option><option value="technical">Technical</option><option value="scenario">Scenario</option><option value="mcq">MCQ</option><option value="output">Output</option></Select>
          <Field id="aqf-text" label="Search" value={text} onChange={e => setText(e.target.value)} />
        </div>
      </Card>
      {error && <ErrorState>{error}</ErrorState>}
      {!items && !error && <Spinner label="Loading questions" />}
      {items && items.length === 0 && <EmptyState title="No questions match">Change the filters or add a question.</EmptyState>}
      {items && items.length > 0 && <p className="mt-3 text-sm text-ink-soft">Showing {items.length} of {total}.</p>}
      <div className="mt-2 space-y-2">
        {(items ?? []).map(q => (
          <Card key={q.slug}>
            <div className="flex flex-wrap items-center gap-2"><code className="text-xs">{q.slug}</code><Badge>{q.kind}</Badge><Badge>{q.difficulty}</Badge><Badge tone="info">{q.source_label.replace(/_/g, ' ')}</Badge>{!q.enabled && <Badge tone="bad">disabled</Badge>}</div>
            <p className="mt-1 text-sm">{q.prompt.split('\n')[0].slice(0, 200)}</p>
            <div className="mt-2 flex gap-2">
              <Button variant="secondary" onClick={() => { setForm({ ...q, editing: true }); setFormError('') }}>Edit</Button>
              <Button variant="secondary" onClick={() => toggle(q)}>{q.enabled ? 'Disable' : 'Enable'}</Button>
              <Button variant="secondary" onClick={() => remove(q)}>Delete</Button>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
}
