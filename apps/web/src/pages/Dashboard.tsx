import { useEffect, useState } from 'react'
import { Card, PageHeader, LinkButton, Badge } from '../components/ui'
import { api, type Assessment, type MatchRow, type ReportSummary, type ResumeItem } from '../lib/api'

export default function Dashboard() {
  const [resumes, setResumes] = useState<ResumeItem[] | null>(null)
  useEffect(() => { api.resumes().then(setResumes).catch(() => setResumes([])) }, [])
  const [recent, setRecent] = useState<Assessment[] | null>(null)
  useEffect(() => { api.assessments().then(a => setRecent(a.slice(0, 3))).catch(() => setRecent([])) }, [])
  const [reports, setReports] = useState<ReportSummary[] | null>(null)
  const [gaps, setGaps] = useState<{ label: string; severity: string }[] | null>(null)
  useEffect(() => {
    api.reports().then(r => { setReports(r); if (r[0]) api.report(r[0].id).then(x => setGaps(x.gaps)).catch(() => setGaps([])); else setGaps([]) }).catch(() => { setReports([]); setGaps([]) })
  }, [])
  const [topRoles, setTopRoles] = useState<MatchRow[]>([])
  const [topCompanies, setTopCompanies] = useState<MatchRow[]>([])
  useEffect(() => {
    api.readinessRoles({}).then(r => {
      const best = r.items.filter(x => x.value !== null).slice(0, 3)
      setTopRoles(best)
      if (best[0]?.role) api.readinessCompanies({ role: best[0].role.slug }).then(c => setTopCompanies(c.items.filter(x => x.value !== null).slice(0, 3))).catch(() => setTopCompanies([]))
    }).catch(() => setTopRoles([]))
  }, [])
  const latest = resumes?.[0]
  const next = !latest ? { text: 'Upload a resume to unlock a personalised assessment.', to: '/app/resume', cta: 'Upload resume' }
    : !latest.analyzed ? { text: 'Analyse your resume so questions can match your projects.', to: '/app/resume', cta: 'Open resume' }
    : recent && recent.length === 0 ? { text: 'Start your first practice assessment.', to: '/app/assessment/setup', cta: 'Start practising' }
    : reports && reports.length === 0 ? { text: 'Create a report from your finished work to see gaps and a plan.', to: '/app/results', cta: 'Create a report' }
    : { text: 'Practise your top gap, then create a new report to see your progress.', to: '/app/results', cta: 'Open results' }
  return (
    <>
      <PageHeader title="Dashboard" intro="Your preparation at a glance." />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card><h2 className="font-semibold">Resume analysis</h2><p className="mt-1 text-sm text-ink-soft">{!latest ? 'No resume uploaded yet.' : latest.analyzed ? `${latest.filename} is analysed.` : `${latest.filename} is uploaded but not analysed yet.`}</p><LinkButton to="/app/resume" className="mt-3">{latest ? 'Open resume' : 'Upload resume'}</LinkButton></Card>
        <Card><h2 className="font-semibold">Target</h2><p className="mt-1 text-sm text-ink-soft">No target selected yet. Choose a role and, optionally, a verified Lahore company.</p><LinkButton to="/app/assessment/setup" variant="secondary" className="mt-3">Choose target</LinkButton></Card>
        <Card><h2 className="font-semibold">Next action</h2><p className="mt-1 text-sm text-ink-soft">{next.text}</p><LinkButton to={next.to} variant="secondary" className="mt-3">{next.cta}</LinkButton></Card>
        {topRoles.length > 0 && (
          <Card className="lg:col-span-3">
            <h2 className="font-semibold">Recommended for you</h2>
            <p className="mt-1 text-xs text-ink-mute">From your resume and your results, as a preparation estimate (not a hiring probability).</p>
            <div className="mt-2 grid gap-4 sm:grid-cols-2">
              <div><p className="text-sm font-medium">Roles</p><ul className="mt-1 text-sm">{topRoles.map(r => <li key={r.role?.slug}>{r.role?.title}: {r.value}% <span className="text-xs text-ink-mute">({r.label})</span></li>)}</ul></div>
              <div><p className="text-sm font-medium">Companies for {topRoles[0].role?.title}</p><ul className="mt-1 text-sm">{topCompanies.map(c => <li key={c.company?.slug}>{c.company?.name}: {c.value}%</li>)}</ul></div>
            </div>
            <LinkButton to="/app/readiness" variant="secondary" className="mt-3">Open company readiness</LinkButton>
          </Card>
        )}
        <Card className="lg:col-span-2">
          <h2 className="mb-3 font-semibold">Recent results</h2>
          {!recent ? <p className="text-sm text-ink-soft">Loading…</p> : recent.length === 0 ? <p className="text-sm text-ink-soft">No assessments yet. <LinkButton to="/app/assessment/setup" variant="secondary" className="ml-2">Start practising</LinkButton></p> : (
            <ul className="divide-y divide-line">
              {recent.map(h => (
                <li key={h.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <span>{h.role.title}, {h.mode === 'company' && h.company ? h.company.name : 'general role preparation'}<span className="block text-xs text-ink-mute">{new Date(h.created_at).toLocaleDateString('en-GB')}{h.score ? ` · ${h.score.mcq_correct}/${h.score.mcq_total} multiple choice` : ''}</span></span>
                  <Badge tone={h.status === 'submitted' ? 'ok' : 'neutral'}>{h.status === 'submitted' ? 'Completed' : h.status.replace('_', ' ')}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <h2 className="mb-3 font-semibold">Skill gaps</h2>
          {!gaps ? <p className="text-sm text-ink-soft">Loading…</p> : gaps.length === 0 ? <p className="text-sm text-ink-soft">{reports && reports.length > 0 ? 'No gaps in your latest report.' : 'Gaps appear here after you create a report.'}</p> : (
            <ul className="space-y-2 text-sm">{gaps.slice(0, 5).map(g => <li key={g.label} className="flex justify-between gap-2"><span>{g.label}</span><Badge tone={g.severity === 'high' ? 'bad' : g.severity === 'medium' ? 'warn' : 'neutral'}>{g.severity}</Badge></li>)}</ul>
          )}
        </Card>
      </div>
    </>
  )
}
