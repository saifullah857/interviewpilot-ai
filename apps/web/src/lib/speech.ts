/** Browser speech helpers. Everything here is optional: when the browser lacks support, the interview uses typing instead.
 *  Some browsers send recognised audio to the browser vendor; the interview screens say so. */

interface RecognitionResult { isFinal: boolean; 0: { transcript: string } }
interface RecognitionEvent { results: ArrayLike<RecognitionResult> }
interface Recognition {
  lang: string; continuous: boolean; interimResults: boolean
  onresult: ((e: RecognitionEvent) => void) | null
  onerror: ((e: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void; stop(): void; abort(): void
}
type RecognitionCtor = new () => Recognition
type Win = { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor }

const ctor = (): RecognitionCtor | undefined => (typeof window === 'undefined' ? undefined : (window as unknown as Win).SpeechRecognition ?? (window as unknown as Win).webkitSpeechRecognition)

export const speechSupport = () => ({
  recognition: !!ctor(),
  synthesis: typeof window !== 'undefined' && 'speechSynthesis' in window && typeof SpeechSynthesisUtterance !== 'undefined',
})

export type SpeechProblem = 'denied' | 'network' | 'no_speech' | 'other'

export interface Recognizer { start(): void; stop(): void }

/** Returns null when speech recognition is unsupported. The recognised text is only handed to the caller, never sent anywhere by this code. */
export function createRecognizer(h: { onText: (text: string, final: boolean) => void; onProblem: (p: SpeechProblem) => void; onEnd: () => void }): Recognizer | null {
  const C = ctor()
  if (!C) return null
  const r = new C()
  r.lang = typeof navigator !== 'undefined' && navigator.language ? navigator.language : 'en-US'
  r.continuous = false
  r.interimResults = true
  r.onresult = e => {
    const list = Array.from(e.results)
    h.onText(list.map(x => x[0].transcript).join(' ').trim(), list.length > 0 && list[list.length - 1].isFinal)
  }
  r.onerror = e => {
    if (e.error === 'aborted') return
    h.onProblem(e.error === 'not-allowed' || e.error === 'service-not-allowed' || e.error === 'audio-capture' ? 'denied' : e.error === 'network' ? 'network' : e.error === 'no-speech' ? 'no_speech' : 'other')
  }
  r.onend = () => h.onEnd()
  return { start: () => r.start(), stop: () => r.stop() }
}

export function speak(text: string, onEnd: () => void): boolean {
  if (!speechSupport().synthesis) return false
  try {
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.onend = onEnd
    u.onerror = onEnd
    window.speechSynthesis.speak(u)
    return true
  } catch { return false }
}

export function cancelSpeech() {
  try { if (speechSupport().synthesis) window.speechSynthesis.cancel() } catch { /* nothing to cancel */ }
}
