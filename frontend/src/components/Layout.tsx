import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { FormEvent, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { fetchAgentStatus, fetchCountries } from '../api/client'
import { useCountry } from '../context/CountryContext'

const NAV_ITEMS = [
  { to: '/', label: '情报库', icon: '🗂️', end: true },
  { to: '/search', label: '检索', icon: '🔎', end: false },
  { to: '/entities', label: '实体', icon: '🧩', end: false },
  { to: '/topics', label: '主题', icon: '🏷️', end: false },
  { to: '/prices', label: '价格看板', icon: '💱', end: false },
  { to: '/collect', label: '采集', icon: '🛰️', end: false },
]

export default function Layout() {
  const navigate = useNavigate()
  const { countryCode, setCountryCode } = useCountry()
  const [q, setQ] = useState('')
  const { data: countries } = useQuery({ queryKey: ['countries'], queryFn: fetchCountries })
  const { data: agentStatus } = useQuery({
    queryKey: ['agent-status'],
    queryFn: fetchAgentStatus,
    refetchInterval: 60_000,
  })

  const onSearch = (e: FormEvent) => {
    e.preventDefault()
    const query = q.trim()
    navigate(query ? `/search?q=${encodeURIComponent(query)}` : '/search')
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-900/60 px-4 py-6">
        <div className="mb-8 flex items-center gap-2 px-2">
          <span className="text-2xl">📡</span>
          <div>
            <div className="text-lg font-semibold leading-tight">GiftRadar</div>
            <div className="text-xs text-slate-400">先收集，再发现</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-300'
                    : 'text-slate-300 hover:bg-slate-800/70 hover:text-white',
                )
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/80 p-3 text-xs text-slate-400">
          <div className="mb-1 flex items-center gap-2">
            <span className={clsx('h-2 w-2 rounded-full', agentStatus?.can_collect ? 'bg-emerald-400' : 'bg-amber-400')} />
            <span className="font-medium text-slate-200">
              {agentStatus?.can_collect ? '真实采集' : '演示情报库'}
            </span>
          </div>
          <p>
            {agentStatus?.can_collect
              ? `库内 ${agentStatus.document_count} 篇原文 · ${agentStatus.watch_count} 张网`
              : '没有 Exa Key 时用多样化演示语料，让你先把检索和实体用起来'}
          </p>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/80 px-6 py-4 backdrop-blur">
          <form onSubmit={onSearch} className="flex min-w-[240px] flex-1 items-center gap-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="在情报库里找：诈骗、MoMo、新平台、延迟…"
              className="w-full max-w-xl rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
            />
            <button className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-emerald-500">
              搜
            </button>
          </form>
          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 p-1">
            <button
              onClick={() => setCountryCode(undefined)}
              className={clsx(
                'rounded-full px-3 py-1.5 text-sm transition-colors',
                !countryCode ? 'bg-emerald-500 text-slate-950 font-semibold' : 'text-slate-300 hover:text-white',
              )}
            >
              全部
            </button>
            {countries?.map((c) => (
              <button
                key={c.code}
                onClick={() => setCountryCode(c.code)}
                className={clsx(
                  'rounded-full px-3 py-1.5 text-sm transition-colors',
                  countryCode === c.code
                    ? 'bg-emerald-500 text-slate-950 font-semibold'
                    : 'text-slate-300 hover:text-white',
                )}
              >
                {c.flag_emoji} {c.name_zh}
              </button>
            ))}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
