import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Button, Card, Field } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'

function AuthForm({ mode }: { mode: 'login' | 'signup' }) {
  const nav = useNavigate()
  const loc = useLocation()
  const { user, loading, setUser } = useAuth()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)
  const signup = mode === 'signup'

  if (!loading && user) return <Navigate to="/app" replace />

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const email = String(d.get('email') ?? '').trim()
    const password = String(d.get('password') ?? '')
    const name = String(d.get('name') ?? '').trim()
    const next: Record<string, string> = {}
    if (!/^\S+@\S+\.\S+$/.test(email)) next.email = 'Enter a valid email address.'
    if (password.length < 8) next.password = 'Use at least 8 characters.'
    setErrors(next)
    setFormError('')
    if (Object.keys(next).length) return
    setBusy(true)
    try {
      const me = signup ? await api.signup(email, password, name) : await api.login(email, password)
      setUser(me)
      nav((loc.state as { from?: string } | null)?.from ?? '/app', { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'validation_error' && err.details) {
        setErrors(Object.fromEntries(err.details.map(x => [x.field, x.message])))
      } else {
        setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <Card>
        <h1 className="text-2xl font-bold">{signup ? 'Create your account' : 'Log in'}</h1>
        <form onSubmit={onSubmit} noValidate className="mt-5 space-y-4">
          {formError && <p role="alert" className="rounded-lg bg-bad-soft p-3 text-sm text-bad">{formError}</p>}
          {signup && <Field id="name" name="name" label="Full name" autoComplete="name" />}
          <Field id="email" name="email" type="email" label="Email" autoComplete="email" error={errors.email} />
          <Field id="password" name="password" type="password" label="Password" autoComplete={signup ? 'new-password' : 'current-password'} hint={signup ? 'At least 8 characters.' : undefined} error={errors.password} />
          <Button type="submit" className="w-full" disabled={busy}>{busy ? 'Please wait…' : signup ? 'Create account' : 'Log in'}</Button>
        </form>
        <p className="mt-4 text-sm text-ink-soft">
          {signup ? <>Already registered? <Link className="text-info underline" to="/login">Log in</Link></> : <>New here? <Link className="text-info underline" to="/signup">Create an account</Link></>}
        </p>
      </Card>
    </div>
  )
}
export const Login = () => <AuthForm mode="login" />
export const Signup = () => <AuthForm mode="signup" />
