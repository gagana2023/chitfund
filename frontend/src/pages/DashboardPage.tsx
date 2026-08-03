import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import type { Pool, PoolPublic } from '../lib/types'

export function DashboardPage() {
  const [pools, setPools] = useState<Pool[] | null>(null)
  const [discoverable, setDiscoverable] = useState<PoolPublic[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activePanel, setActivePanel] = useState<'none' | 'create' | 'join'>('none')

  function refresh() {
    api
      .get<Pool[]>('/pools')
      .then(setPools)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load pools'))
    api
      .get<PoolPublic[]>('/pools/discover')
      .then(setDiscoverable)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load discoverable pools'))
  }

  useEffect(refresh, [])

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Your pools</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActivePanel(activePanel === 'join' ? 'none' : 'join')}
            className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-dim)] transition hover:border-[var(--gold)]/50 hover:text-[var(--text)]"
          >
            Join with code
          </button>
          <button
            onClick={() => setActivePanel(activePanel === 'create' ? 'none' : 'create')}
            className="rounded-md bg-[var(--gold)] px-3 py-1.5 text-sm font-medium text-[#191307] transition hover:brightness-110"
          >
            + New pool
          </button>
        </div>
      </div>

      {activePanel === 'create' && (
        <CreatePoolPanel
          onCreated={() => {
            setActivePanel('none')
            refresh()
          }}
        />
      )}
      {activePanel === 'join' && (
        <JoinPoolPanel
          onJoined={() => {
            setActivePanel('none')
            refresh()
          }}
        />
      )}

      {error && <p className="mb-4 text-sm text-[var(--bad)]">{error}</p>}

      {pools === null ? (
        <p className="text-sm text-[var(--text-dim)]">Loading…</p>
      ) : pools.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--border)] p-10 text-center text-sm text-[var(--text-dim)]">
          No pools yet. Create one, or join an existing pool with an invite code.
        </div>
      ) : (
        <div className="grid gap-3">
          {pools.map((pool) => (
            <Link
              key={pool.id}
              to={`/pools/${pool.id}`}
              className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 transition hover:border-[var(--gold)]/40"
            >
              <div>
                <p className="font-medium text-[var(--text)]">{pool.name}</p>
                <p className="mt-0.5 text-xs text-[var(--text-dim)]">
                  ₹{pool.contribution_amount} / cycle · {pool.member_count}/{pool.member_cap} members · cycle{' '}
                  {pool.current_cycle_number}
                </p>
              </div>
              <span
                className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                  pool.status === 'active'
                    ? 'border-[var(--good)]/40 bg-[var(--good)]/10 text-[var(--good)]'
                    : 'border-[var(--border)] bg-[var(--surface-raised)] text-[var(--text-dim)]'
                }`}
              >
                {pool.status}
              </span>
            </Link>
          ))}
        </div>
      )}

      <div className="mt-10">
        <h2 className="mb-3 text-sm font-medium text-[var(--text-dim)]">Discover pools</h2>
        {discoverable === null ? (
          <p className="text-sm text-[var(--text-dim)]">Loading…</p>
        ) : discoverable.length === 0 ? (
          <p className="text-sm text-[var(--text-dim)]">No public pools right now.</p>
        ) : (
          <div className="grid gap-2">
            {discoverable.map((pool) => (
              <div
                key={pool.id}
                className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">{pool.name}</p>
                  <p className="mt-0.5 text-xs text-[var(--text-dim)]">
                    run by {pool.head_name} · ₹{pool.contribution_amount} / cycle · {pool.member_count}/
                    {pool.member_cap} members
                  </p>
                </div>
                <RequestToJoinButton pool={pool} onRequested={refresh} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function RequestToJoinButton({ pool, onRequested }: { pool: PoolPublic; onRequested: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (pool.is_member) {
    return <span className="text-xs text-[var(--good)]">already a member</span>
  }
  if (pool.has_pending_request) {
    return <span className="text-xs text-[var(--gold)]">request pending</span>
  }

  async function handleClick() {
    setError(null)
    setSubmitting(true)
    try {
      await api.post(`/pools/${pool.id}/join-requests`, {})
      onRequested()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to request')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="text-right">
      <button
        onClick={handleClick}
        disabled={submitting}
        className="rounded-md border border-[var(--gold)]/50 px-3 py-1.5 text-xs font-medium text-[var(--gold)] transition hover:bg-[var(--gold-dim)] disabled:opacity-50"
      >
        {submitting ? 'Requesting…' : 'Request to join'}
      </button>
      {error && <p className="mt-1 text-xs text-[var(--bad)]">{error}</p>}
    </div>
  )
}

function CreatePoolPanel({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [cap, setCap] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/pools', {
        name: name.trim(),
        contribution_amount: Number(amount),
        member_cap: Number(cap),
      })
      onCreated()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create pool')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 grid gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:grid-cols-4"
    >
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Pool name"
        className="rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]/60 sm:col-span-2"
      />
      <input
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="Contribution ₹"
        type="number"
        min="1"
        className="rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]/60"
      />
      <input
        value={cap}
        onChange={(e) => setCap(e.target.value)}
        placeholder="Members"
        type="number"
        min="2"
        max="50"
        className="rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]/60"
      />
      {error && <p className="text-sm text-[var(--bad)] sm:col-span-4">{error}</p>}
      <button
        type="submit"
        disabled={!name.trim() || !amount || !cap || submitting}
        className="rounded-lg bg-[var(--gold)] px-4 py-2 text-sm font-medium text-[#191307] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50 sm:col-span-4"
      >
        {submitting ? 'Creating…' : 'Create pool'}
      </button>
    </form>
  )
}

function JoinPoolPanel({ onJoined }: { onJoined: () => void }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/pools/join', { invite_code: code.trim() })
      onJoined()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to join pool')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 flex gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
    >
      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Invite code"
        className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]/60"
      />
      {error && <p className="text-sm text-[var(--bad)]">{error}</p>}
      <button
        type="submit"
        disabled={!code.trim() || submitting}
        className="rounded-lg bg-[var(--gold)] px-4 py-2 text-sm font-medium text-[#191307] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? 'Joining…' : 'Join'}
      </button>
    </form>
  )
}
