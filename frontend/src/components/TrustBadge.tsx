interface TrustBadgeProps {
  score: number
}

function tierFor(score: number): { label: string; className: string } {
  if (score >= 70) return { label: 'Trusted', className: 'text-[var(--good)] border-[var(--good)]/40 bg-[var(--good)]/10' }
  if (score >= 40) return { label: 'Building', className: 'text-[var(--gold)] border-[var(--gold)]/40 bg-[var(--gold)]/10' }
  return { label: 'At risk', className: 'text-[var(--bad)] border-[var(--bad)]/40 bg-[var(--bad)]/10' }
}

export function TrustBadge({ score }: TrustBadgeProps) {
  const tier = tierFor(score)
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${tier.className}`}
      title="Laplace-smoothed on-time contribution ratio"
    >
      <span className="font-semibold">{score.toFixed(1)}</span>
      <span className="opacity-80">{tier.label}</span>
    </span>
  )
}
