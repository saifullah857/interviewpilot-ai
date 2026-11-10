import { Link } from 'react-router-dom'
import type { ButtonHTMLAttributes, ReactNode, InputHTMLAttributes, SelectHTMLAttributes } from 'react'
import { AlertTriangle, CircleSlash, FlaskConical, Inbox } from 'lucide-react'
import { EVIDENCE_META, type EvidenceLabel } from '../lib/evidence'

export const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(' ')

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
const variants: Record<Variant, string> = {
  primary: 'bg-brand text-ink hover:bg-[#f27a2f] font-semibold',
  secondary: 'bg-surface text-ink border border-line hover:bg-canvas font-medium',
  ghost: 'text-ink-soft hover:bg-canvas font-medium',
  danger: 'bg-bad text-black hover:opacity-90 font-semibold',
}
const base = 'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50'

export function Button({ variant = 'primary', className, ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={cx(base, variants[variant], className)} {...p} />
}
export function LinkButton({ to, variant = 'primary', className, children }: { to: string; variant?: Variant; className?: string; children: ReactNode }) {
  return <Link to={to} className={cx(base, variants[variant], className)}>{children}</Link>
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cx('rounded-xl border border-line bg-surface p-5 shadow-lift', className)}>{children}</section>
}

const tones = {
  ok: 'bg-ok-soft text-ok', info: 'bg-info-soft text-info', warn: 'bg-warn-soft text-warn',
  bad: 'bg-bad-soft text-bad', neutral: 'bg-canvas text-ink-soft border border-line', brand: 'bg-brand-soft text-brand-deep',
}
export function Badge({ tone = 'neutral', children, title }: { tone?: keyof typeof tones; children: ReactNode; title?: string }) {
  return <span title={title} className={cx('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium', tones[tone])}>{children}</span>
}

export function EvidenceBadge({ label }: { label: EvidenceLabel }) {
  const m = EVIDENCE_META[label]
  return <Badge tone={m.tone} title={m.hint}>{m.text}</Badge>
}

/** Marks any content that is not live-verified. Required on all Phase 1 sample data. */
export function SampleBadge({ children = 'Sample data, not verified' }: { children?: ReactNode }) {
  return <Badge tone="warn"><FlaskConical size={12} aria-hidden /> {children}</Badge>
}

export function PageHeader({ title, intro, actions }: { title: string; intro?: string; actions?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold">{title}</h1>
        {intro && <p className="mt-1 text-ink-soft">{intro}</p>}
      </div>
      {actions}
    </header>
  )
}

export function Field({ label, hint, error, id, ...p }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string; id: string }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <input id={id} aria-invalid={!!error} aria-describedby={error ? `${id}-err` : hint ? `${id}-hint` : undefined}
        className={cx('w-full rounded-lg border bg-surface px-3 py-2.5 text-sm', error ? 'border-bad' : 'border-line')} {...p} />
      {hint && !error && <p id={`${id}-hint`} className="mt-1 text-xs text-ink-mute">{hint}</p>}
      {error && <p id={`${id}-err`} role="alert" className="mt-1 text-xs text-bad">{error}</p>}
    </div>
  )
}

export function Select({ label, id, children, ...p }: SelectHTMLAttributes<HTMLSelectElement> & { label: string; id: string }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <select id={id} className="w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm" {...p}>{children}</select>
    </div>
  )
}

export function Meter({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span>{label}</span><span className="font-semibold">{value}</span></div>
      <div role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} className="h-2 rounded-full bg-canvas">
        <div className="h-2 rounded-full bg-brand" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 p-6 text-ink-soft">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-line border-t-brand" aria-hidden />
      {label}…
    </div>
  )
}

function StateBox({ icon, title, children, action }: { icon: ReactNode; title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mx-auto max-w-md rounded-xl border border-dashed border-line bg-surface p-8 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-canvas text-ink-soft" aria-hidden>{icon}</div>
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-ink-soft">{children}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
export const EmptyState = (p: { title: string; children: ReactNode; action?: ReactNode }) => <StateBox icon={<Inbox size={20} />} {...p} />
export const ErrorState = (p: { title?: string; children: ReactNode; action?: ReactNode }) => <StateBox icon={<AlertTriangle size={20} />} title={p.title ?? 'Something went wrong'} {...p} />
export const UnavailableState = (p: { title?: string; children: ReactNode; action?: ReactNode }) => <StateBox icon={<CircleSlash size={20} />} title={p.title ?? 'Not available yet'} {...p} />
