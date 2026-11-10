import type { ReactNode } from 'react'

/** Renders plain text with `code` spans as React nodes. It never injects HTML, so problem text cannot run anything. */
export function renderInline(text: string): ReactNode[] {
  return text.split(/(`[^`]+`)/g).map((part, i) => (part.startsWith('`') && part.endsWith('`') && part.length > 2
    ? <code key={i} className="rounded bg-canvas px-1 py-0.5 font-mono text-[0.85em]">{part.slice(1, -1)}</code>
    : <span key={i}>{part}</span>))
}

export function Paragraphs({ text }: { text: string }) {
  return <>{text.split(/\n\s*\n/).map((p, i) => <p key={i} className="mt-2 text-sm text-ink-soft">{renderInline(p)}</p>)}</>
}

export const show = (v: unknown) => { const s = JSON.stringify(v); return s.length > 160 ? `${s.slice(0, 160)}…` : s }
