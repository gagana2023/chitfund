import { useEffect, useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { TrustBadge } from '../components/TrustBadge'
import type { Cycle, JoinRequest, LedgerEntry, PoolDetail } from '../lib/types'

export function PoolDetailPage() {
  const { poolId } = useParams<{ poolId: string }>()
  const { user } = useAuth()
  const [pool, setPool] = useState<PoolDetail | null>(null)
  const [cycle, setCycle] = useState<Cycle | null>(null)
  const [ledger, setLedger] = useState<LedgerEntry[]>([])
  const [joinRequests, setJoinRequests] = useState<JoinRequest[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [bidAmount, setBidAmount] = useState('')
  const [copied, setCopied] = useState(false)

  function refresh() {
    if (!poolId) return
    Promise.all([
      api.get<PoolDetail>(`/pools/${poolId}`),
      api.get<Cycle>(`/pools/${poolId}/cycles/current`),
      api.get<LedgerEntry[]>(`/pools/${poolId}/ledger`),
    ])
      .then(([p, c, l]) => {
        setPool(p)
        setCycle(c)
        setLedger(l)
        const iAmHead = p.members.some((m) => m.user_id === user?.id && m.is_head)
        if (iAmHead) {
          api.get<JoinRequest[]>(`/pools/${poolId}/join-requests`).then(setJoinRequests)
        } else {
          setJoinRequests([])
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load pool'))
  }

  useEffect(refresh, [poolId])

  if (error) return <p className="text-sm text-[var(--bad)]">{error}</p>
  if (!pool || !cycle || !user) return <p className="text-sm text-[var(--text-dim)]">Loading…</p>

  const myMembership = pool.members.find((m) => m.user_id === user.id)
  const iHaveContributed = ledger.some(
    (e) => e.cycle_id === cycle.id && e.entry_type === 'contribution' && e.membership_id === myMembership?.membership_id,
  )

  async function runAction(action: () => Promise<unknown>) {
    setError(null)
    setBusy(true)
    try {
      await action()
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleBidSubmit(e: FormEvent) {
    e.preventDefault()
    await runAction(() => api.post(`/pools/${poolId}/bid`, { amount: Number(bidAmount) }))
    setBidAmount('')
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{pool.name}</h1>
          <p className="mt-1 text-sm text-[var(--text-dim)]">
            ₹{pool.contribution_amount} / cycle · cycle {pool.current_cycle_number} of {pool.member_cap} ·{' '}
            {pool.member_count}/{pool.member_cap} members
          </p>
        </div>
        {pool.status === 'active' && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(pool.invite_code)
              setCopied(true)
              setTimeout(() => setCopied(false), 1500)
            }}
            className="rounded-md border border-[var(--border)] px-3 py-1.5 font-mono text-sm text-[var(--text-dim)] transition hover:border-[var(--gold)]/50 hover:text-[var(--text)]"
          >
            {copied ? 'Copied!' : `Invite: ${pool.invite_code}`}
          </button>
        )}
      </div>

      {error && <p className="mb-4 text-sm text-[var(--bad)]">{error}</p>}

      {pool.status === 'completed' ? (
        <div className="mb-6 rounded-xl border border-[var(--gold)]/40 bg-[var(--gold-dim)] p-5 text-sm text-[var(--text)]">
          This pool has completed — every member has received a payout.
        </div>
      ) : (
        <div className="mb-6 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium text-[var(--text-dim)]">Cycle {cycle.cycle_number}</h2>
            <span className="rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-2.5 py-1 text-xs text-[var(--text-dim)]">
              {cycle.status.replace('_', ' ')}
            </span>
          </div>

          {cycle.status === 'collecting' && pool.member_count < pool.member_cap && (
            <p className="text-sm text-[var(--text-dim)]">
              Waiting for more members to join ({pool.member_count}/{pool.member_cap}) before this pool can start —
              share the invite code or approve join requests.
            </p>
          )}

          {cycle.status === 'collecting' && pool.member_count >= pool.member_cap && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-[var(--text-dim)]">
                {iHaveContributed
                  ? 'You have recorded your contribution this cycle.'
                  : 'Record your contribution to move this cycle toward bidding.'}
              </p>
              {!iHaveContributed && (
                <button
                  disabled={busy}
                  onClick={() => runAction(() => api.post(`/pools/${poolId}/contribute`, { on_time: true }))}
                  className="rounded-lg bg-[var(--gold)] px-4 py-2 text-sm font-medium text-[#191307] transition hover:brightness-110 disabled:opacity-50"
                >
                  Record contribution ₹{pool.contribution_amount}
                </button>
              )}
            </div>
          )}

          {cycle.status === 'bidding_open' && (
            <div>
              {myMembership?.has_won ? (
                <p className="text-sm text-[var(--text-dim)]">
                  You already won a payout in this pool — waiting on other members to bid.
                </p>
              ) : (
                <form onSubmit={handleBidSubmit} className="flex items-center gap-3">
                  <input
                    value={bidAmount}
                    onChange={(e) => setBidAmount(e.target.value)}
                    type="number"
                    min="0"
                    max={pool.contribution_amount * pool.member_count}
                    placeholder={`Bid amount (max ₹${pool.contribution_amount * pool.member_count})`}
                    className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]/60"
                  />
                  <button
                    type="submit"
                    disabled={!bidAmount || busy}
                    className="rounded-lg border border-[var(--gold)]/50 px-4 py-2 text-sm font-medium text-[var(--gold)] transition hover:bg-[var(--gold-dim)] disabled:opacity-50"
                  >
                    Submit bid
                  </button>
                </form>
              )}
              <p className="mt-3 text-xs text-[var(--text-dim)]">
                Lowest bid takes the payout at that amount; the discount splits as a dividend to everyone else.
              </p>
              <button
                disabled={busy}
                onClick={() => runAction(() => api.post(`/pools/${poolId}/cycles/current/resolve`, {}))}
                className="mt-3 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-dim)] transition hover:border-[var(--gold)]/50 hover:text-[var(--text)] disabled:opacity-50"
              >
                Resolve cycle now
              </button>
            </div>
          )}
        </div>
      )}

      {joinRequests.length > 0 && (
        <div className="mb-6 rounded-xl border border-[var(--gold)]/40 bg-[var(--gold-dim)] p-5">
          <h2 className="mb-3 text-sm font-medium text-[var(--text)]">Pending join requests</h2>
          <div className="grid gap-2">
            {joinRequests.map((r) => (
              <div key={r.id} className="flex items-center justify-between rounded-lg bg-[var(--surface)] px-4 py-2.5">
                <span className="text-sm text-[var(--text)]">{r.requester_name}</span>
                <div className="flex gap-2">
                  <button
                    disabled={busy}
                    onClick={() => runAction(() => api.post(`/pools/${poolId}/join-requests/${r.id}/approve`, {}))}
                    className="rounded-md bg-[var(--good)]/15 px-3 py-1 text-xs font-medium text-[var(--good)] transition hover:bg-[var(--good)]/25 disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    disabled={busy}
                    onClick={() => runAction(() => api.post(`/pools/${poolId}/join-requests/${r.id}/reject`, {}))}
                    className="rounded-md bg-[var(--bad)]/15 px-3 py-1 text-xs font-medium text-[var(--bad)] transition hover:bg-[var(--bad)]/25 disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mb-6">
        <h2 className="mb-3 text-sm font-medium text-[var(--text-dim)]">Members</h2>
        <div className="grid gap-2">
          {pool.members.map((m) => (
            <div
              key={m.membership_id}
              className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
            >
              <span className="text-sm text-[var(--text)]">
                {m.name}
                {m.user_id === user.id && <span className="text-[var(--text-dim)]"> (you)</span>}
                {m.is_head && (
                  <span className="ml-2 rounded-full border border-[var(--gold)]/40 bg-[var(--gold-dim)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[var(--gold)]">
                    Head
                  </span>
                )}
                {m.has_won && <span className="ml-2 text-xs text-[var(--gold)]">already won</span>}
              </span>
              <TrustBadge score={m.trust_score} />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium text-[var(--text-dim)]">Ledger</h2>
        {ledger.length === 0 ? (
          <p className="text-sm text-[var(--text-dim)]">No transactions yet.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <tbody>
                {ledger.map((e) => (
                  <tr key={e.id} className="border-b border-[var(--border)] last:border-0">
                    <td className="px-4 py-2.5 text-[var(--text)]">{e.member_name}</td>
                    <td className="px-4 py-2.5 capitalize text-[var(--text-dim)]">{e.entry_type}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[var(--text)]">₹{e.amount.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right text-xs text-[var(--text-dim)]">
                      {new Date(e.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
