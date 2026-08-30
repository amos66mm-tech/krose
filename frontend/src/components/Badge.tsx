import clsx from 'clsx'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

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
  mixed: '混合',
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

const DOC_TYPE_STYLES: Record<string, string> = {
  rate_list: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  promotion: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  complaint: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  scam_report: 'bg-rose-500/20 text-rose-200 border-rose-500/40',
  news: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  how_to: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  competitor: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30',
  policy: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  forum_thread: 'bg-slate-500/15 text-slate-200 border-slate-500/30',
  review: 'bg-teal-500/15 text-teal-300 border-teal-500/30',
  social: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  other: 'bg-slate-700/40 text-slate-300 border-slate-600/40',
}

const DOC_TYPE_LABEL: Record<string, string> = {
  rate_list: '报价',
  promotion: '活动',
  complaint: '投诉',
  scam_report: '诈骗/风险',
  news: '新闻',
  how_to: '教程',
  competitor: '新平台',
  policy: '监管',
  forum_thread: '论坛',
  review: '口碑',
  social: '社媒',
  other: '未分类',
}

export function DocTypeBadge({ type }: { type: string }) {
  return (
    <span className={clsx('rounded-full border px-2 py-0.5 text-xs font-medium', DOC_TYPE_STYLES[type] ?? DOC_TYPE_STYLES.other)}>
      {DOC_TYPE_LABEL[type] ?? type}
    </span>
  )
}

export function Chip({ children, to }: { children: ReactNode; to?: string }) {
  const className =
    'rounded-full border border-slate-700 bg-slate-800/80 px-2 py-0.5 text-xs text-slate-300 hover:border-emerald-500 hover:text-emerald-300'
  if (to) {
    return (
      <Link to={to} className={className}>
        {children}
      </Link>
    )
  }
  return <span className={className}>{children}</span>
}
