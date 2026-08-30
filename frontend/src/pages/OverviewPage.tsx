import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchDashboardSummary, triggerCollection } from '../api/client'
import StatCard from '../components/StatCard'
import { LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

export default function OverviewPage() {
  const { countryCode } = useCountry()
  const queryClient = useQueryClient()
  const [running, setRunning] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-summary', countryCode],
    queryFn: () => fetchDashboardSummary(countryCode),
    refetchInterval: 30_000,
  })

  const handleRefresh = async () => {
    setRunning(true)
    try {
      await triggerCollection('all', countryCode)
      await queryClient.invalidateQueries()
    } finally {
      setRunning(false)
    }
  }

  if (isLoading || !data) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">市场总览</h2>
          <p className="text-sm text-slate-400">
            覆盖 {data.total_countries} 个国家 · {data.total_platforms} 个礼品卡交易平台
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={running}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {running ? '采集中…' : '🔄 立即触发一次采集'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="24h 价格数据点" value={data.total_price_points_24h} accent="sky" />
        <StatCard label="24h 新出现价格" value={data.new_price_points_24h} hint="首次被发现的报价" accent="emerald" />
        <StatCard label="7天活动/加价" value={data.active_promotions_7d} accent="amber" />
        <StatCard label="7天社媒动态" value={data.social_posts_7d} accent="rose" />
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Agent 运行状态</h3>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              data.live_mode ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'
            }`}
          >
            {data.live_mode ? '实时抓取模式（Exa + LLM）' : '演示数据模式（未配置 API Key）'}
          </span>
        </div>
        {data.last_run ? (
          <p className="text-xs text-slate-400">
            最近一次采集：[{data.last_run.scope}] {data.last_run.status} · 处理 {data.last_run.targets_processed} 个目标 ·
            新增 {data.last_run.records_created} 条记录 · {new Date(data.last_run.started_at).toLocaleString('zh-CN')}
          </p>
        ) : (
          <p className="text-xs text-slate-500">尚未运行过采集任务</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">💰 各卡种当前最佳回收价</h3>
          <div className="flex flex-col divide-y divide-slate-800">
            {data.best_rate_per_card_type.length === 0 && (
              <p className="py-6 text-center text-sm text-slate-500">暂无数据，试试点击右上角立即采集</p>
            )}
            {data.best_rate_per_card_type.map((row) => (
              <div key={row.gift_card_type} className="flex items-center justify-between py-2.5 text-sm">
                <span className="flex items-center gap-2 text-slate-200">
                  <span>{row.icon}</span>
                  {row.gift_card_type}
                </span>
                <span className="text-right">
                  <span className="font-semibold text-emerald-300">{row.rate_percent.toFixed(2)}%</span>
                  <span className="ml-2 text-xs text-slate-400">{row.platform}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">📈 近期波动最大的报价</h3>
          <div className="flex flex-col divide-y divide-slate-800">
            {data.biggest_movers.length === 0 && (
              <p className="py-6 text-center text-sm text-slate-500">暂无明显波动（可能是首次采集，还没有历史对比）</p>
            )}
            {data.biggest_movers.map((row, idx) => (
              <div key={idx} className="flex items-center justify-between py-2.5 text-sm">
                <span className="text-slate-200">
                  {row.platform} · {row.gift_card_type}
                </span>
                <span
                  className={`font-semibold ${row.change_percent >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}
                >
                  {row.change_percent >= 0 ? '▲' : '▼'} {Math.abs(row.change_percent).toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
