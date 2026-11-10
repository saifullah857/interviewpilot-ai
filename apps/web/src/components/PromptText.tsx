/** Shows a question prompt. Text between ``` fences is shown as code, everything else as paragraphs. */
export default function PromptText({ text }: { text: string }) {
  const parts = text.split(/```[a-z]*\n?/)
  return (
    <div className="space-y-2">
      {parts.map((part, i) => {
        const t = part.replace(/\n+$/, '')
        if (!t.trim()) return null
        return i % 2 === 1
          ? <pre key={i} className="overflow-x-auto rounded-lg bg-canvas p-3 font-mono text-sm">{t}</pre>
          : <p key={i} className="whitespace-pre-line">{t.trim()}</p>
      })}
    </div>
  )
}
