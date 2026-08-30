import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { NavLink, Outlet } from 'react-router-dom'
import { fetchAgentStatus, fetchCountries } from '../api/client'
import { useCountry } from '../context/CountryContext'

const NAV_ITEMS = [
  { to: '/', label: '总览', icon: '📊', end: true },
  { to: '/prices', label: '价格看板', icon: '💱' },
  { to: '/activities', label: '活动情报', icon: '📣' },
  { to: '/social', label: '社媒动态', icon: '💬' },
  { to: '/agent', label: 'Agent 探针', icon: '🤖' },
  { to: '/ideas', label: '论坛增长点子', icon: '💡' },
]

export default function Layout() {
  const { countryCode, setCountryCode } = useCountry()
  const { data: countries } = useQuery({ queryKey: ['countries'], queryFn: fetchCountries })
  const { data: agentStatus } = useQuery({
    queryKey: ['agent-status'],
    queryFn: fetchAgentStatus,
    refetchInterval: 60_000,
  })

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-900/60 px-4 py-6">
        <div className="mb-8 flex items-center gap-2 px-2">
          <span className="text-2xl">🎁</span>
          <div>
            <div className="text-lg font-semibold leading-tight">GiftRadar</div>
            <div className="text-xs text-slate-400">非洲礼品卡市场情报</div>
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
            <span
              className={clsx(
                'h-2 w-2 rounded-full',
                agentStatus?.live_mode ? 'bg-emerald-400' : 'bg-amber-400',
              )}
            />
            <span className="font-medium text-slate-200">
              {agentStatus?.live_mode ? '实时抓取模式' : '演示数据模式'}
            </span>
          </div>
          <p>
            {agentStatus?.live_mode
              ? `LLM: ${agentStatus.llm_model}`
              : '配置 EXA_API_KEY 与 LLM_API_KEY 后自动切换为真实抓取'}
          </p>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 py-4 backdrop-blur">
          <div>
            <h1 className="text-base font-semibold text-white">尼日利亚 · 加纳 · 喀麦隆 礼品卡市场看板</h1>
            <p className="text-xs text-slate-400">卖方视角比价 · 平台情报 · 论坛内容引擎</p>
          </div>
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
