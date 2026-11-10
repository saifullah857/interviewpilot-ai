import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Field, PageHeader } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function Settings() {
  const { user, setUser } = useAuth()
  const nav = useNavigate()
  const [name, setName] = useState(user?.profile.display_name ?? '')
  const [msg, setMsg] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [pw, setPw] = useState('')
  const [delErr, setDelErr] = useState('')
  const [cur, setCur] = useState('')
  const [next, setNext] = useState('')
  const [again, setAgain] = useState('')
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null)

  async function saveProfile(e: FormEvent) {
    e.preventDefault()
    try { setUser(await api.updateProfile(name)); setMsg('Saved.') } catch (err) { setMsg(err instanceof ApiError ? err.message : 'Could not save.') }
  }
  async function toggleVoice(on: boolean) {
    if (!user) return
    try {
      const c = await api.updateConsents({ voice_transcript: on })
      setUser({ ...user, consents: c })
    } catch (err) { setMsg(err instanceof ApiError ? err.message : 'Could not update.') }
  }
  async function changePassword(e: FormEvent) {
    e.preventDefault()
    setPwMsg(null)
    if (next.length < 8) return setPwMsg({ ok: false, text: 'The new password must be at least 8 characters.' })
    if (next !== again) return setPwMsg({ ok: false, text: 'The two new passwords do not match.' })
    try {
      await api.changePassword(cur, next)
      setCur(''); setNext(''); setAgain('')
      setPwMsg({ ok: true, text: 'Password changed. Your other devices were signed out.' })
    } catch (err) { setPwMsg({ ok: false, text: err instanceof ApiError ? err.message : 'Could not change the password.' }) }
  }
  async function deleteAccount(e: FormEvent) {
    e.preventDefault()
    setDelErr('')
    try { await api.deleteAccount(pw); setUser(null); nav('/', { replace: true }) } catch (err) { setDelErr(err instanceof ApiError ? err.message : 'Could not delete.') }
  }

  return (
    <>
      <PageHeader title="Profile and settings" />
      <div className="grid max-w-3xl gap-4">
        <Card>
          <form onSubmit={saveProfile} className="space-y-4">
            <h2 className="font-semibold">Profile</h2>
            <p className="text-sm text-ink-soft">{user?.email}</p>
            <Field id="dn" label="Display name" value={name} maxLength={100} onChange={e => setName(e.target.value)} />
            <Button type="submit">Save changes</Button>
            {msg && <p role="status" className="text-sm text-ink-soft">{msg}</p>}
          </form>
        </Card>
        <Card>
          <form onSubmit={changePassword} className="space-y-4">
            <h2 className="font-semibold">Change password</h2>
            <Field id="pw-cur" type="password" label="Current password" value={cur} onChange={e => setCur(e.target.value)} autoComplete="current-password" />
            <Field id="pw-new" type="password" label="New password (at least 8 characters)" value={next} onChange={e => setNext(e.target.value)} autoComplete="new-password" maxLength={128} />
            <Field id="pw-again" type="password" label="Repeat the new password" value={again} onChange={e => setAgain(e.target.value)} autoComplete="new-password" maxLength={128} />
            <Button type="submit" disabled={!cur || !next || !again}>Change password</Button>
            {pwMsg && <p role={pwMsg.ok ? 'status' : 'alert'} className={pwMsg.ok ? 'text-sm text-ok' : 'text-sm text-bad'}>{pwMsg.text}</p>}
          </form>
        </Card>
        <Card>
          <h2 className="font-semibold">Privacy</h2>
          <label className="mt-3 flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1" checked={user?.consents.voice_transcript ?? false} onChange={e => toggleVoice(e.target.checked)} />
            <span>Save my voice interview transcripts. Off by default. You can turn this off at any time.</span>
          </label>
        </Card>
        <Card>
          <h2 className="font-semibold">Delete my account</h2>
          <p className="mt-1 text-sm text-ink-soft">This permanently removes your account and everything stored with it. It cannot be undone.</p>
          {!confirming ? <Button variant="danger" className="mt-3" onClick={() => setConfirming(true)}>Delete my account</Button> : (
            <form onSubmit={deleteAccount} className="mt-3 space-y-3">
              <Field id="del-pw" type="password" label="Confirm with your password" value={pw} onChange={e => setPw(e.target.value)} error={delErr} autoComplete="current-password" />
              <div className="flex gap-2"><Button type="submit" variant="danger" disabled={!pw}>Permanently delete</Button><Button type="button" variant="secondary" onClick={() => { setConfirming(false); setPw('') }}>Cancel</Button></div>
            </form>
          )}
        </Card>
      </div>
    </>
  )
}
