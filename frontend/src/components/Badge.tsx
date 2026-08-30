import clsx from 'clsx'

const ACTIVITY_STYLES: Record<string, string> = {
  promotion: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  announcement: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  policy: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  outage: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
}

const ACTIVITY_LABEL: Record<string, string> = {
  promotion: '活动/加价',
  announcement: '公告/更新',
  policy: '政策变化',
  outage: '维护/故障',
}

export function ActivityBadge({ type }: { type: string }) {
  return (
    <span className={clsx('rounded-full border px-2 py-0.5 text-xs font-medium', ACTIVITY_STYLES[type] ?? ACTIVITY_STYLES.announcement)}>
      {ACTIVITY_LABEL[type] ?? type}
    </span>
  )
}

const SENTIMENT_STYLES: Record<string, string> = {
  positive: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  neutral: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
  negative: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
}

const SENTIMENT_LABEL: Record<string, string> = {
  positive: '正面',
  neutral: '中性',
  negative: '负面',
}

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  return (
    <span className={clsx('rounded-full border px-2 py-0.5 text-xs font-medium', SENTIMENT_STYLES[sentiment] ?? SENTIMENT_STYLES.neutral)}>
      {SENTIMENT_LABEL[sentiment] ?? sentiment}
    </span>
  )
}

const NETWORK_ICON: Record<string, string> = {
  twitter: '𝕏',
  facebook: 'f',
  instagram: '📷',
  telegram: '✈️',
}

export function NetworkBadge({ network }: { network: string }) {
  return (
    <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
      {NETWORK_ICON[network] ?? '🌐'} {network}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  const styles: Record<string, string> = {
    P0: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    P1: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    P2: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  }
  return (
    <span className={clsx('rounded-full border px-2 py-0.5 text-xs font-semibold', styles[priority] ?? styles.P2)}>
      {priority}
    </span>
  )
}
