import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { ApiError } from '../lib/api'

export function LoginPage() {
  const [name, setName] = useState('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(name.trim(), pin.trim())
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-[var(--bg)] px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--text)]">Chitfund</h1>
          <p className="mt-1 text-sm text-[var(--text-dim)]">Rotating savings circles, with a trust score attached.</p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-lg shadow-black/20"
        >
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-[var(--text-dim)]">
            Your name
          </label>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Priya"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2.5 text-[var(--text)] outline-none transition focus:border-[var(--gold)]/60"
          />

          <label className="mb-1.5 mt-4 block text-xs font-medium uppercase tracking-wide text-[var(--text-dim)]">
            PIN
          </label>
          <input
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="Pick any PIN — remember it"
            type="password"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2.5 text-[var(--text)] outline-none transition focus:border-[var(--gold)]/60"
          />

          {error && <p className="mt-2 text-sm text-[var(--bad)]">{error}</p>}
          <button
            type="submit"
            disabled={!name.trim() || pin.trim().length < 3 || submitting}
            className="mt-4 w-full rounded-lg bg-[var(--gold)] px-4 py-2.5 font-medium text-[#191307] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? 'Entering…' : 'Enter'}
          </button>
        </form>
      </div>
    </div>
  )
}
