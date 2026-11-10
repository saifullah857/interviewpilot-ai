import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, Card, EmptyState, ErrorState, LinkButton, PageHeader, Spinner } from '../components/ui'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, ApiError, type Assessment, type ReportSummary } from '../lib/api'

const TONE: Record<string, 'ok' | 'info' | 'warn' | 'bad' | 'neutral'> = { submitted: 'ok', in_progress: 'info', ready: 'neutral', generating: 'info', failed: 'bad' }
const LABEL: Record<string, string> = { submitted: 'Completed', in_progress: 'In progress', ready: 'Not started', generating: 'Being written', failed: 'Failed' }

export default function History() {
  const [rows, setRows] = useState<Assessment[] | null>(null)
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState<string | null>(null)
  const load = () => api.assessments().then(setRows).catch(e => setError(e instanceof ApiError ? e.message : 'Could not load your history.'))
  useEffect(() => { load(); api.reports().then(setReports).catch(() => setReports([])) }, [])

  async function remove(id: string) { try { await api.deleteAssessment(id); setConfirm(null); await load() } catch (e) { setError(e instanceof ApiError ? e.message : 'Could not delete.') } }

  if (error) return <ErrorState>{error}</ErrorState>
  if (!rows) return <Spinner label="Loading your history" />
  return (
    <>
      <PageHeader title="Assessment history" />
      {rows.length === 0 ? <EmptyState title="No assessments yet" action={<LinkButton to="/app/assessment/setup">Start practising</LinkButton>}>Your practice sessions will be listed here.</EmptyState> : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Past assessments</caption>
            <thead className="border-b border-line text-ink-mute"><tr><th className="p-3 font-medium">Date</th><th className="p-3 font-medium">Target</th><th className="p-3 font-medium">Status</th><th className="p-3 font-medium">Multiple choice</th><th className="p-3 font-medium"><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>{rows.map(r => (
              <tr key={r.id} className="border-b border-line last:border-0">
                <td className="p-3">{new Date(r.created_at).toLocaleDateString('en-GB')}</td>
                <td className="p-3"><Link className="text-info underline" to={`/app/assessment/${r.id}`}>{r.role.title}</Link><span className="block text-xs text-ink-mute">{r.mode === 'company' && r.company ? r.company.name : 'General role preparation'}</span></td>
                <td className="p-3"><Badge tone={TONE[r.status]}>{LABEL[r.status]}</Badge></td>
                <td className="p-3">{r.score ? `${r.score.mcq_correct} / ${r.score.mcq_total}` : 'n/a'}</td>
                <td className="p-3 text-right">{confirm === r.id ? <><Button variant="danger" onClick={() => remove(r.id)}>Yes, delete</Button> <Button variant="secondary" onClick={() => setConfirm(null)}>Cancel</Button></> : <button className="text-xs text-info underline" onClick={() => setConfirm(r.id)}>Delete</button>}</td>
              </tr>))}</tbody>
          </table>
        </Card>
      )}
      <h2 className="mb-2 mt-8 text-lg font-semibold">Saved reports</h2>
      {reports.length === 0 ? <p className="text-sm text-ink-soft">No report yet. One is saved automatically when you finish a coding session, submit an assessment or get interview feedback.</p> : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h3 className="text-sm font-semibold">Overall score of each report</h3>
            <div className="mt-2 h-56"><ResponsiveContainer><BarChart data={[...reports].reverse().map(r => ({ name: new Date(r.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }), overall: r.overall }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 100]} fontSize={11} /><Tooltip /><Bar dataKey="overall" name="Overall" fill="#2563eb" /></BarChart></ResponsiveContainer></div>
          </Card>
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm"><caption className="sr-only">Saved reports</caption>
              <thead className="border-b border-line text-ink-mute"><tr><th className="p-3 font-medium">Date</th><th className="p-3 font-medium">Role</th><th className="p-3 font-medium">Overall</th><th className="p-3"></th></tr></thead>
              <tbody>{reports.map(r => (
                <tr key={r.id} className="border-b border-line last:border-0"><td className="p-3">{new Date(r.created_at).toLocaleDateString('en-GB')}</td><td className="p-3">{r.role.title} {r.auto && <Badge tone="info">auto</Badge>}</td><td className="p-3">{r.overall ?? '-'}</td><td className="p-3 text-right"><Link className="text-info underline" to={`/app/results/${r.id}`}>Open</Link></td></tr>))}</tbody>
            </table>
          </Card>
        </div>
      )}
    </>
  )
}
