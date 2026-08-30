import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchEntities } from '../api/client'
import { LoadingState } from '../components/States'

const TYPES = [
  { key: '', label: '全部' },
  { key: 'platform', label: '平台' },
  { key: 'card_type', label: '卡种' },
  { key: 'payment_rail', label: '支付通道' },
  { key: 'place', label: '地点' },
  { key: 'org', label: '机构' },
  { key: 'topic', label: '主题' },
  { key: 'other', label: '其他' },
]

export default function EntitiesPage() {
  const [type, setType] = useState('')
  const [discoveredOnly, setDiscoveredOnly] = useState(false)
  const { data, isLoading } = useQuery({
    queryKey: ['entities', type, discoveredOnly],
    queryFn: () => fetchEntities({ entityType: type || undefined, discoveredOnly }),
  })

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold text-white">实体</h2>
        <p className="text-sm text-slate-400">
          平台、卡种、支付通道、地点、监管机构都会从原文里长出来。种子名单只是起点，真正有价值的往往是「发现」标记。
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {TYPES.map((t) => (
          <button
            key={t.key || 'all'}
            onClick={() => setType(t.key)}
            className={`rounded-full px-3 py-1 text-xs ${type === t.key ? 'bg-emerald-500 text-slate-950' : 'border border-slate-700 text-slate-300'}`}
          >
            {t.label}
          </button>
        ))}
        <button
          onClick={() => setDiscoveredOnly((v) => !v)}
          className={`rounded-full px-3 py-1 text-xs ${discoveredOnly ? 'bg-fuchsia-500 text-slate-950' : 'border border-slate-700 text-slate-300'}`}
        >
          只看新发现
        </button>
      </div>
      {isLoading ? (
        <LoadingState />
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {(data ?? []).map((e) => (
            <Link
              key={e.id}
              to={`/entities/${e.id}`}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 hover:border-emerald-500/40"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{e.name}</span>
                <span className="text-xs text-slate-500">{e.mention_count} 次提及</span>
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {e.entity_type}
                {e.country_code ? ` · ${e.country_code}` : ''}
                {!e.is_seeded && <span className="ml-2 text-fuchsia-300">发现</span>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
