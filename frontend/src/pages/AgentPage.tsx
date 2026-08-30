import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { deleteWatch, fetchAgentStatus, fetchRuns, fetchWatches, patchWatch, runCustomCollect, triggerCollection } from '../api/client'
import { LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

const SCOPES = [
  { key: 'intel', label: '全量宽网（推荐）' },
  { key: 'market_scan', label: '市场全景' },
  { key: 'community', label: '社区/论坛' },
  { key: 'news_risk', label: '风险/监管' },
  { key: 'competitor_discovery', label: '新平台发现' },
  { key: 'rates', label: '行情材料' },
  { key: 'platform_watch', label: '已知平台' },
]

export default function AgentPage() {
  const { countryCode } = useCountry()
  const queryClient = useQueryClient()
  const [customQuery, setCustomQuery] = useState('')
  const [customLabel, setCustomLabel] = useState('自定义监控')
  const [customMessage, setCustomMessage] = useState<string | null>(null)

  const { data: status, isLoading: loadingStatus } = useQuery({
    queryKey: ['agent-status'],
    queryFn: fetchAgentStatus,
  })
  const { data: watches } = useQuery({ queryKey: ['watches'], queryFn: fetchWatches })
  const { data: runs, isLoading: loadingRuns } = useQuery({
    queryKey: ['runs'],
    queryFn: () => fetchRuns(20),
    refetchInterval: 15_000,
  })

  const collectMutation = useMutation({
    mutationFn: (scope: string) => triggerCollection(scope, countryCode),
    onSuccess: () => queryClient.invalidateQueries(),
  })

  const customMutation = useMutation({
    mutationFn: () => runCustomCollect(customQuery, customLabel, countryCode),
    onSuccess: (data: { detail?: string; documents?: unknown[]; mode?: string }) => {
      setCustomMessage(
        data.mode === 'demo'
          ? data.detail || '已保存这张网。配置 Exa Key 之后才会真正去搜。'
          : `已入库 ${(data.documents || []).length} 条原文`,
      )
      queryClient.invalidateQueries()
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCustomMessage(detail ?? '请求失败')
    },
  })

  if (loadingStatus || !status) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-white">采集与监控网</h2>
        <p className="text-sm text-slate-400">
          不知道要什么情报时，就多撒几张网。命中的网页会整篇进情报库，而不是只留下一个预先规定好的字段。
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">能力</h3>
          <ul className="flex flex-col gap-2 text-sm">
            <li className="flex items-center justify-between">
              <span className="text-slate-400">Exa 搜索（收原文）</span>
              <span className={status.has_exa ? 'text-emerald-400' : 'text-amber-400'}>
                {status.has_exa ? '已配置' : '未配置'}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">LLM 整理（可选）</span>
              <span className={status.has_llm ? 'text-emerald-400' : 'text-amber-400'}>
                {status.has_llm ? status.llm_model : '仅启发式整理'}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">情报库原文</span>
              <span className="text-slate-200">{status.document_count}</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-400">活跃的网</span>
              <span className="text-slate-200">{status.watch_count}</span>
            </li>
          </ul>
          {!status.can_collect && (
            <p className="mt-3 rounded-lg bg-amber-500/10 p-3 text-xs text-amber-300">
              当前用演示语料填充情报库，方便你先体验「搜索 / 实体 / 主题」。配置 <code>EXA_API_KEY</code> 后，采集会把真实网页归档进来，演示文档不会混进真实库。
            </p>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">立刻采集</h3>
          <div className="flex flex-col gap-2">
            {SCOPES.map((s) => (
              <button
                key={s.key}
                onClick={() => collectMutation.mutate(s.key)}
                disabled={collectMutation.isPending}
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-left text-sm text-slate-200 hover:border-emerald-500 disabled:opacity-50"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="mb-1 text-sm font-semibold text-white">再加一张网</h3>
        <p className="mb-3 text-xs text-slate-400">
          输入任何你突然想到的问题，例如「Kenya gift card buyer」或「Prestmit BVN complaint」。默认会保存下来，以后定时采集也会跑。
        </p>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            value={customLabel}
            onChange={(e) => setCustomLabel(e.target.value)}
            placeholder="这张网叫什么"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500 md:w-48"
          />
          <input
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="搜索词"
            className="w-full flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
          />
          <button
            onClick={() => customMutation.mutate()}
            disabled={!customQuery || customMutation.isPending}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {customMutation.isPending ? '撒网中…' : '保存并探测'}
          </button>
        </div>
        {customMessage && <p className="mt-3 text-sm text-emerald-300">{customMessage}</p>}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">当前所有的网</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500">
                <th className="py-2 pr-4">名称</th>
                <th className="py-2 pr-4">查询</th>
                <th className="py-2 pr-4">类型</th>
                <th className="py-2 pr-4">国家</th>
                <th className="py-2 pr-4">状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {(watches ?? []).map((w) => (
                <tr key={w.id} className="text-slate-300">
                  <td className="py-2 pr-4">
                    {w.label}
                    {w.is_system && <span className="ml-2 text-xs text-slate-500">系统</span>}
                  </td>
                  <td className="max-w-sm py-2 pr-4 text-xs text-slate-400">{w.query}</td>
                  <td className="py-2 pr-4">{w.stream}</td>
                  <td className="py-2 pr-4">{w.country_code || '—'}</td>
                  <td className="py-2 pr-4">
                    <button
                      onClick={() => patchWatch(w.id, !w.is_active).then(() => queryClient.invalidateQueries({ queryKey: ['watches'] }))}
                      className={w.is_active ? 'text-emerald-400' : 'text-slate-500'}
                    >
                      {w.is_active ? '开' : '关'}
                    </button>
                    {!w.is_system && (
                      <button
                        onClick={() => deleteWatch(w.id).then(() => queryClient.invalidateQueries({ queryKey: ['watches'] }))}
                        className="ml-3 text-xs text-rose-400"
                      >
                        删除
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">采集记录</h3>
        {loadingRuns ? (
          <LoadingState />
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500">
                <th className="py-2 pr-4">范围</th>
                <th className="py-2 pr-4">模式</th>
                <th className="py-2 pr-4">状态</th>
                <th className="py-2 pr-4">网数</th>
                <th className="py-2 pr-4">新原文</th>
                <th className="py-2 pr-4">时间</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {(runs ?? []).map((r) => (
                <tr key={r.id} className="text-slate-300">
                  <td className="py-2 pr-4">{r.scope}</td>
                  <td className="py-2 pr-4">{r.mode}</td>
                  <td className="py-2 pr-4">{r.status}</td>
                  <td className="py-2 pr-4">{r.targets_processed}</td>
                  <td className="py-2 pr-4">{r.records_created}</td>
                  <td className="py-2 pr-4 text-xs text-slate-500">{new Date(r.started_at).toLocaleString('zh-CN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
