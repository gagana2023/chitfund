import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from '../lib/auth'

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-svh bg-[var(--bg)] text-[var(--text)]">
      <header className="border-b border-[var(--border)]">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="text-lg font-semibold tracking-tight">Chitfund</span>
            <span className="text-xs text-[var(--text-dim)]">rotating savings, done right</span>
          </Link>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-[var(--text-dim)]">
                signed in as <span className="text-[var(--text)]">{user.name}</span>
              </span>
              <button
                onClick={logout}
                className="rounded-md border border-[var(--border)] px-3 py-1.5 text-[var(--text-dim)] transition hover:border-[var(--gold)]/50 hover:text-[var(--text)]"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
    </div>
  )
}
