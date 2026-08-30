import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchAgentStatus, fetchRuns, runCustomWatch, triggerCollection } from '../api/client'
import { LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'
import type { CustomWatchResult } from '../types'

const SCOPES: { key: 'all' | 'price' | 'activity' | 'social'; label: string }[] = [
  { key: 'all', label: '全部（价格+活动+社媒）' },
  { key: 'price', label: '仅价格' },
  { key: 'activity', label: '仅活动/公告' },
  { key: 'social', label: '仅社媒' },
]

export default function AgentPage() {
  const { countryCode } = useCountry()
  const queryClient = useQueryClient()
  const [customQuery, setCustomQuery] = useState('')
  const [customLabel, setCustomLabel] = useState('自定义监控目标')
  const [customResults, setCustomResults] = useState<CustomWatchResult[] | null>(null)
  const [customError, setCustomError] = useState<string | null>(null)

  const { data: status, isLoading: loadingStatus } = useQuery({
    queryKey: ['agent-status'],
    queryFn: fetchAgentStatus,
  })
  const { data: runs, isLoading: loadingRuns } = useQuery({
    queryKey: ['runs'],
    queryFn: () => fetchRuns(20),
    refetchInterval: 15_000,
  })

  const collectMutation = useMutation({
    mutationFn: (scope: 'all' | 'price' | 'activity' | 'social') => triggerCollection(scope, countryCode),
    onSuccess: () => queryClient.invalidateQueries(),
  })

  const customMutation = useMutation({
    mutationFn: () => runCustomWatch(customQuery, customLabel),
    onSuccess: (data) => {
      setCustomResults(data)
      setCustomError(null)
    },
    onError: (err: any) => {
      setCustomError(err?.response?.data?.detail ?? '请求失败')
      setCustomResults(null)
    },
  })

  if (loadingStatus || !status) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-white">Agent 探针控制台</h2>
        <p className="text-sm text-slate-400">
          管理采集 Agent：查看 Key 配置状态、手动触发采集、以及体验「万物皆可爬」的即时探针接口。
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">🔑 API 配置状态</h3>
          <ul className="flex flex-col gap-2 text-sm">
            <li className="flex items-center justify-between">
              <span className="text-slate-400">Exa 搜索 API</span>
              <span className={status.has_exa ? 'text-emerald-400' : 'text-amber-400'}>
                {status.has_exa ? '✅ 已配置' : '⚠️ 未配置 (EXA_API_KEY)'}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">LLM（OpenAI 协议）</span>
              <span className={status.has_llm ? 'text-emerald-400' : 'text-amber-400'}>
                {status.has_llm ? `✅ ${status.llm_model}` : '⚠️ 未配置 (LLM_API_KEY)'}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">LLM Base URL</span>
              <span className="text-slate-300">{status.llm_base_url}</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">定时采集</span>
              <span className="text-slate-300">
                {status.scheduler_enabled ? `每 ${status.collection_interval_minutes} 分钟` : '已关闭'}
              </span>
            </li>
          </ul>
          {!status.live_mode && (
            <p className="mt-3 rounded-lg bg-amber-500/10 p-3 text-xs text-amber-300">
              当前处于演示模式：所有价格/活动/社媒数据均为算法模拟生成（带 [DEMO] 标记）。
              在 Cursor Dashboard → Secrets 中配置 <code>EXA_API_KEY</code> 与 <code>LLM_API_KEY</code>（遵循 OpenAI 协议，
              可指向 OpenAI 官方或任意兼容供应商）后，下一次采集会自动切换为真实抓取。
            </p>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">▶️ 手动触发采集</h3>
          <div className="flex flex-col gap-2">
            {SCOPES.map((s) => (
              <button
                key={s.key}
                onClick={() => collectMutation.mutate(s.key)}
                disabled={collectMutation.isPending}
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-left text-sm text-slate-200 transition hover:border-emerald-500 hover:text-emerald-300 disabled:opacity-50"
              >
                {s.label}
              </button>
            ))}
          </div>
          {collectMutation.isSuccess && (
            <p className="mt-2 text-xs text-emerald-400">✅ 采集完成，数据已刷新</p>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="mb-1 text-sm font-semibold text-white">🕷️ 万物探针（自定义即时抓取）</h3>
        <p className="mb-3 text-xs text-slate-400">
          输入任意关键词，Agent 会用 Exa 搜索最新网页，再用 LLM 做结构化摘要提取——这是为论坛未来扩展预留的通用入口
          （例如监控竞品动态、汇率新闻、行业监管消息等）。需要先配置好 API Key。
        </p>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            value={customLabel}
            onChange={(e) => setCustomLabel(e.target.value)}
            placeholder="标签，例如：竞品动态"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500 md:w-48"
          />
          <input
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="搜索关键词，例如：Nigeria gift card market news this week"
            className="w-full flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
          />
          <button
            onClick={() => customMutation.mutate()}
            disabled={!customQuery || customMutation.isPending}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {customMutation.isPending ? '探测中…' : '探测'}
          </button>
        </div>
        {customError && <p className="mt-3 text-sm text-amber-300">{customError}</p>}
        {customResults && (
          <div className="mt-4 flex flex-col gap-3">
            {customResults.map((r, idx) => (
              <div key={idx} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                <a href={r.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-emerald-300 hover:underline">
                  {r.title || r.url}
                </a>
                {r.extraction?.found ? (
                  <div className="mt-1 text-sm text-slate-300">
                    <p className="font-medium">{r.extraction.headline}</p>
                    <p className="text-slate-400">{r.extraction.summary}</p>
                    {r.extraction.key_facts?.length > 0 && (
                      <ul className="mt-1 list-inside list-disc text-xs text-slate-500">
                        {r.extraction.key_facts.map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
                  <p className="mt-1 text-xs text-slate-500">LLM 未能从该网页中抽取到明确信息</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">🗒️ 最近采集记录</h3>
        {loadingRuns ? (
          <LoadingState />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500">
                  <th className="py-2 pr-4">范围</th>
                  <th className="py-2 pr-4">模式</th>
                  <th className="py-2 pr-4">状态</th>
                  <th className="py-2 pr-4">目标数</th>
                  <th className="py-2 pr-4">新增记录</th>
                  <th className="py-2 pr-4">开始时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {(runs ?? []).map((r) => (
                  <tr key={r.id} className="text-slate-300">
                    <td className="py-2 pr-4">{r.scope}</td>
                    <td className="py-2 pr-4">{r.mode === 'live' ? '🟢 live' : '🟡 mock'}</td>
                    <td className="py-2 pr-4">
                      {r.status === 'success' ? '✅' : r.status === 'failed' ? '❌' : '⏳'} {r.status}
                    </td>
                    <td className="py-2 pr-4">{r.targets_processed}</td>
                    <td className="py-2 pr-4">{r.records_created}</td>
                    <td className="py-2 pr-4 text-xs text-slate-500">{new Date(r.started_at).toLocaleString('zh-CN')}</td>
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
