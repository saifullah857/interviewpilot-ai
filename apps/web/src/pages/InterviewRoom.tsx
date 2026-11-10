import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Mic, MicOff, Send, SkipForward, Volume2, VolumeX } from 'lucide-react'
import { Badge, Button, Card, ErrorState, EvidenceBadge, LinkButton, PageHeader, Spinner } from '../components/ui'
import { VoiceOrb, type OrbState } from '../components/VoiceOrb'
import { api, ApiError, type Interview, type InterviewEventKind } from '../lib/api'
import { cancelSpeech, createRecognizer, speak, speechSupport, type Recognizer, type SpeechProblem } from '../lib/speech'
import type { EvidenceLabel } from '../lib/evidence'

export default function InterviewRoom() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const support = speechSupport()
  const [iv, setIv] = useState<Interview | null>(null)
  const [err, setErr] = useState<ApiError | null>(null)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState<'' | 'send' | 'end' | 'resume'>('')
  const [note, setNote] = useState('')
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [aloud, setAloud] = useState(support.synthesis)
  const rec = useRef<Recognizer | null>(null)
  const viaSpeech = useRef(false)
  const base = useRef('')
  const spoken = useRef('')
  const reported = useRef(false)

  const report = useCallback(async (kind: InterviewEventKind) => {
    try { setIv(await api.interviewEvent(id, kind)) } catch { /* the text fallback works either way */ }
  }, [id])

  useEffect(() => { api.interview(id).then(setIv).catch(e => setErr(e instanceof ApiError ? e : new ApiError(0, 'error', 'Could not load the interview.'))) }, [id])
  useEffect(() => () => { cancelSpeech(); rec.current?.stop() }, [])

  const voiceWanted = iv?.input_mode === 'voice'
  useEffect(() => {
    if (iv && iv.status === 'active' && iv.input_mode === 'voice' && !support.recognition && !reported.current) { reported.current = true; void report('speech_unsupported') }
  }, [iv, support.recognition, report])

  const last = iv?.turns?.filter(t => t.speaker === 'interviewer').at(-1)
  useEffect(() => {
    if (!aloud || !last || iv?.status !== 'active' || !iv.awaiting_answer || spoken.current === last.id) return
    spoken.current = last.id
    setSpeaking(speak(last.text, () => setSpeaking(false)))
  }, [aloud, last, iv])

  function problem(p: SpeechProblem) {
    setListening(false)
    if (p === 'denied') { setNote('Microphone access was blocked or no microphone was found. You can keep going by typing.'); void report('mic_denied') }
    else if (p === 'network') { setNote('Speech recognition lost its connection. You can keep going by typing.'); void report('speech_error') }
    else if (p === 'no_speech') setNote("I didn't hear anything. Try again, or type your answer.")
    else { setNote('Speech recognition failed. You can keep going by typing.'); void report('speech_error') }
  }
  function toggleMic() {
    if (listening) { rec.current?.stop(); return }
    cancelSpeech(); setSpeaking(false); setNote('')
    rec.current ??= createRecognizer({
      onText: t => { viaSpeech.current = true; setText(base.current ? `${base.current} ${t}` : t) },
      onProblem: problem,
      onEnd: () => setListening(false),
    })
    if (!rec.current) { setNote('This browser does not support speech recognition. Please type.'); void report('speech_unsupported'); return }
    base.current = text.trim(); setListening(true)
    try { rec.current.start() } catch { setListening(false) }
  }

  async function send(skip = false) {
    if (!iv) return
    setBusy('send'); setNote(''); cancelSpeech(); setSpeaking(false); rec.current?.stop()
    try {
      setIv(await api.answerInterview(id, skip ? { skip: true } : { text, source: viaSpeech.current ? 'speech' : 'typed' }))
      setText(''); viaSpeech.current = false
    } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not send your answer. It is still in the box; try again.') }
    finally { setBusy('') }
  }
  async function finish() {
    setBusy('end'); cancelSpeech(); rec.current?.stop()
    try { await api.endInterview(id); nav(`/app/interview/${id}/review`) } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not end the interview.'); setBusy('') }
  }
  async function resume() {
    setBusy('resume')
    try { setIv(await api.resumeInterview(id)); setNote('') } catch (e) { setNote(e instanceof ApiError ? e.message : 'Could not resume.') } finally { setBusy('') }
  }

  if (err) return <ErrorState title={err.status === 404 ? 'Interview not found' : undefined} action={<LinkButton to="/app/interview">Back to interviews</LinkButton>}>{err.message}</ErrorState>
  if (!iv) return <Spinner label="Loading the interview" />
  const orb: OrbState = busy === 'send' ? 'thinking' : listening ? 'listening' : speaking ? 'speaking' : 'idle'
  const active = iv.status === 'active'
  const turns = iv.turns ?? []
  return (
    <>
      <PageHeader title="Interview room" intro={`${iv.role.title}${iv.company ? ` · ${iv.company.name}` : ' · general role practice'}`}
        actions={<div className="flex gap-2"><EvidenceBadge label={iv.label as EvidenceLabel} /><Badge tone="neutral">Question {Math.min(Math.max(iv.questions_asked, 1), iv.question_target)} of {iv.question_target}</Badge></div>} />
      {iv.status === 'interrupted' && (
        <p role="status" className="mb-4 rounded-lg bg-warn-soft p-3 text-sm text-warn">This interview was interrupted after {iv.idle_minutes} minutes without activity.{' '}
          <button className="font-semibold underline" onClick={resume} disabled={busy === 'resume'}>Resume</button>{iv.answers_given > 0 && <> or <a className="font-semibold underline" href={`/app/interview/${id}/review`}>get feedback on what you answered</a></>}.</p>
      )}
      {iv.status === 'completed' && <p role="status" className="mb-4 rounded-lg bg-ok-soft p-3 text-sm text-ok">The interview is complete. <a className="font-semibold underline" href={`/app/interview/${id}/review`}>See your feedback</a></p>}
      {iv.events.some(e => e.kind === 'mic_denied' || e.kind === 'speech_unsupported' || e.kind === 'speech_error') && voiceWanted === false && <p className="mb-4 text-sm text-ink-soft">Switched to typing because speech input isn't available.</p>}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="bg-deck text-white lg:col-span-2">
          <VoiceOrb state={orb} />
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {voiceWanted && support.recognition && (
              <Button variant="secondary" aria-pressed={listening} onClick={toggleMic} disabled={!active || busy !== ''}>{listening ? <MicOff size={16} /> : <Mic size={16} />} {listening ? 'Stop listening' : 'Speak my answer'}</Button>
            )}
            {support.synthesis && <Button variant="secondary" aria-pressed={aloud} onClick={() => { if (aloud) { cancelSpeech(); setSpeaking(false) } setAloud(!aloud) }}>{aloud ? <Volume2 size={16} /> : <VolumeX size={16} />} {aloud ? 'Reading questions aloud' : 'Read questions aloud'}</Button>}
            {active && <Button variant="secondary" onClick={finish} disabled={busy !== ''}>End interview</Button>}
          </div>
          <p className="mt-4 text-center text-xs text-slate-400">The animation shows the interview's state, not your audio. The AI can't see you and reads only the text of your answers.</p>
        </Card>
        <Card className="lg:col-span-3">
          <h2 className="mb-2 font-semibold">Transcript</h2>
          {turns.length === 0 ? <p className="text-sm text-ink-soft">The transcript was removed.</p> : (
            <ul className="max-h-80 space-y-3 overflow-y-auto" aria-live="polite" aria-label="Transcript">
              {turns.map(t => (
                <li key={t.id} className="text-sm">
                  <span className="font-semibold">{t.speaker === 'interviewer' ? 'Interviewer' : 'You'}: </span>{t.text}
                  <span className="ml-2 inline-flex flex-wrap gap-1 align-middle">
                    {t.kind === 'follow_up' && <Badge tone="neutral">Follow-up</Badge>}
                    {t.source === 'fallback' && <Badge tone="warn" title="The AI was unavailable or its question was rejected by our checks, so a built-in practice question was used.">Built-in question</Badge>}
                    {t.informed_by.map(r => <a key={r.n} href={r.url} target="_blank" rel="noreferrer"><EvidenceBadge label={r.label as EvidenceLabel} /></a>)}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {active && iv.awaiting_answer && (
            <div className="mt-4">
              <label htmlFor="ans" className="mb-1 block text-sm font-medium">Your answer {viaSpeech.current && <span className="font-normal text-ink-mute">(from speech: check it before sending)</span>}</label>
              <textarea id="ans" rows={4} maxLength={4000} value={text} onChange={e => { setText(e.target.value); if (!e.target.value) viaSpeech.current = false }} disabled={busy !== ''}
                className="w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm" />
              <div className="mt-2 flex flex-wrap gap-2">
                <Button onClick={() => send(false)} disabled={busy !== '' || !text.trim()}><Send size={16} /> Send answer</Button>
                <Button variant="secondary" onClick={() => send(true)} disabled={busy !== ''}><SkipForward size={16} /> Skip question</Button>
              </div>
            </div>
          )}
          {note && <p role="alert" className="mt-3 text-sm text-bad">{note}</p>}
        </Card>
      </div>
      <p className="mt-4 text-xs text-ink-mute">{iv.notice}</p>
    </>
  )
}
