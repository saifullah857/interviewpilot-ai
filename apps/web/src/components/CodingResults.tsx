import { Badge } from './ui'
import type { CodingSubmission } from '../lib/api'
import { show } from '../lib/text'

const TONE = { passed: 'ok', failed: 'bad', error: 'bad', timeout: 'warn', not_run: 'neutral' } as const
const LABEL = { passed: 'Passed', failed: 'Failed', error: 'Error', timeout: 'Timed out', not_run: 'Not run' } as const

export function CodingResults({ sub }: { sub: CodingSubmission }) {
  return (
    <div aria-label="Test results">
      {!sub.executed && <p role="status" className="mb-2 rounded-lg bg-warn-soft p-3 text-sm text-warn"><b>Nothing was run.</b> {sub.message}</p>}
      {sub.compile_error && <p role="alert" className="mb-2 rounded-lg bg-bad-soft p-3 font-mono text-xs text-bad">{sub.compile_error}</p>}
      <p className="mb-2 text-sm font-medium">
        {sub.kind === 'run' ? 'Visible tests' : 'Submission'}: {sub.executed ? `${sub.passed_count} of ${sub.total_count} passed` : `${sub.total_count} tests, none run`}
        {sub.executed && sub.runtime_ms !== null && <span className="ml-2 text-xs font-normal text-ink-mute">{sub.runtime_ms} ms total</span>}
      </p>
      <ul className="space-y-2">
        {sub.results.map(r => (
          <li key={r.id} className="rounded-lg border border-line p-2 text-xs">
            <div className="flex flex-wrap items-center gap-2"><b>{r.label}</b><Badge tone={TONE[r.status]}>{LABEL[r.status]}</Badge>{r.runtime_ms !== null && <span className="text-ink-mute">{r.runtime_ms} ms</span>}</div>
            {r.hidden ? <p className="mt-1 text-ink-mute">Inputs and expected values of hidden tests are not shown.</p> : (
              <dl className="mt-1 grid gap-0.5 font-mono">
                <div><dt className="inline text-ink-mute">input: </dt><dd className="inline">{show(r.args)}</dd></div>
                <div><dt className="inline text-ink-mute">expected: </dt><dd className="inline">{show(r.expected)}</dd></div>
                {r.actual != null && <div><dt className="inline text-ink-mute">your output: </dt><dd className="inline">{r.actual}</dd></div>}
                {r.error && <div className="text-bad"><dt className="inline">error: </dt><dd className="inline">{r.error}</dd></div>}
                {r.stdout && <div><dt className="inline text-ink-mute">printed: </dt><dd className="inline whitespace-pre-wrap">{r.stdout}</dd></div>}
              </dl>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
