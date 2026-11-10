import { LinkButton, Card, EvidenceBadge } from '../components/ui'
import { MapPin, ShieldCheck, Code2, Mic } from 'lucide-react'

const PLAN = [
  'Upload your resume',
  'Pick a role and a Lahore company',
  'Take a personalised assessment',
  'Solve coding challenges',
  'Talk through a voice interview',
  'Get your improvement plan',
]

export default function Landing() {
  return (
    <>
      <section className="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-2 lg:px-10 lg:py-20">
        <div>
          <h1 className="text-4xl font-extrabold leading-tight lg:text-6xl">Prepare for the interview you actually have in Lahore.</h1>
          <p className="mt-5 max-w-xl text-lg text-ink-soft">
            Practice for software houses and AI teams with a verified Lahore office. Every company fact shows its source, and every practice question says it was generated.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <LinkButton to="/signup">Create free account</LinkButton>
            <LinkButton to="/app/companies" variant="secondary">Browse Lahore companies</LinkButton>
          </div>
        </div>
        <Card className="border-brand/40 bg-brand-soft text-black">
          <h2 className="text-xl font-bold text-black">Your flight plan</h2>
          <ol className="mt-4 space-y-3">
            {PLAN.map((s, i) => (
              <li key={s} className="flex items-center gap-3 font-medium text-black">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-black">{i + 1}</span>
                <span className="text-black">{s}</span>
              </li>
            ))}
          </ol>
        </Card>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 lg:grid-cols-3 lg:px-10" aria-label="What makes it different">
        {[
          { icon: MapPin, t: 'Lahore only', d: 'Only companies with a verified Lahore presence are listed. No remote-only listings.' },
          { icon: ShieldCheck, t: 'Evidence you can check', d: 'Findings link to their source and carry a freshness date.' },
          { icon: Code2, t: 'Real code checks', d: 'Coding results come from test runs, never from an AI guess.' },
        ].map(({ icon: Icon, t, d }) => (
          <Card key={t}><Icon className="mb-2 text-brand-deep" aria-hidden /><h2 className="text-lg font-semibold">{t}</h2><p className="mt-1 text-sm text-ink-soft">{d}</p></Card>
        ))}
      </section>
      <section className="mx-auto mt-10 max-w-6xl px-4 lg:px-10">
        <Card>
          <h2 className="flex items-center gap-2 text-lg font-semibold"><Mic size={18} aria-hidden /> How we label what you see</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <EvidenceBadge label="official_verified" /><EvidenceBadge label="public_candidate_report" />
            <EvidenceBadge label="ai_generated_practice" /><EvidenceBadge label="unverified_or_outdated" />
          </div>
          <p className="mt-3 text-sm text-ink-soft">Scores are preparation indicators. They are not a prediction of whether you will be hired.</p>
        </Card>
      </section>
    </>
  )
}
