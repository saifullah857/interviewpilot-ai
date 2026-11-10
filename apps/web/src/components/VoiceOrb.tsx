import { Mic } from 'lucide-react'

export type OrbState = 'idle' | 'listening' | 'speaking' | 'thinking'
const BARS = [0.5, 0.9, 0.6, 1, 0.7, 0.95, 0.55, 0.8, 0.45]
const TEXT: Record<OrbState, string> = {
  idle: 'Waiting for your answer',
  listening: 'Listening: speak now, then check the text before sending',
  speaking: 'The interviewer is speaking',
  thinking: 'The interviewer is preparing the next question',
}

/** An abstract activity indicator, not a person and not an audio meter: it shows which state the interview is in.
 *  The animation stops under prefers-reduced-motion (see index.css); the text below always carries the same information. */
export function VoiceOrb({ state }: { state: OrbState }) {
  const active = state === 'listening' || state === 'speaking'
  return (
    <div className="flex flex-col items-center">
      <div className="relative my-6 flex h-40 w-40 items-center justify-center" aria-hidden data-state={state}>
        {(active || state === 'thinking') && <span className="orb-ring absolute inset-0 rounded-full bg-brand/40" />}
        <span className="relative flex h-28 w-28 items-center justify-center rounded-full bg-brand text-ink"><Mic size={36} /></span>
      </div>
      <div className="flex h-10 items-end gap-1" aria-hidden>
        {BARS.map((h, i) => <span key={i} className={active ? 'wave-bar w-1.5 rounded bg-brand' : 'w-1.5 rounded bg-slate-500'} style={{ height: `${h * 100}%`, animationDelay: `${i * 90}ms` }} />)}
      </div>
      <p className="mt-3 text-center text-sm text-slate-300" role="status">{TEXT[state]}</p>
    </div>
  )
}
