import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { fetchActivities, fetchPlatforms } from '../api/client'
import { ActivityBadge } from '../components/Badge'
import { EmptyState, LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

export default function ActivitiesPage() {
  const { countryCode } = useCountry()
  const { data: platforms } = useQuery({ queryKey: ['platforms', countryCode], queryFn: () => fetchPlatforms(countryCode) })
  const { data: activities, isLoading } = useQuery({
    queryKey: ['activities', countryCode],
    queryFn: () => fetchActivities(countryCode, 100),
    refetchInterval: 60_000,
  })

  const platformLookup = useMemo(() => new Map((platforms ?? []).map((p) => [p.id, p])), [platforms])

  if (isLoading) return <LoadingState />
  if (!activities?.length) return <EmptyState label="暂无活动/公告数据" />

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-white">活动情报</h2>
        <p className="text-sm text-slate-400">各平台的限时加价、新卡种上线、政策变化、系统维护等动态，帮助卖家抓住最佳出货窗口。</p>
      </div>
      <div className="flex flex-col gap-3">
        {activities.map((act) => {
          const platform = platformLookup.get(act.platform_id)
          return (
            <div key={act.id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{platform?.name ?? `平台 #${act.platform_id}`}</span>
                  <ActivityBadge type={act.activity_type} />
                </div>
                <span className="text-xs text-slate-500">
                  {act.published_at ? new Date(act.published_at).toLocaleString('zh-CN') : new Date(act.collected_at).toLocaleString('zh-CN')}
                </span>
              </div>
              <h3 className="text-sm font-medium text-slate-100">{act.title}</h3>
              {act.summary && <p className="mt-1 text-sm text-slate-400">{act.summary}</p>}
              {act.source_url && (
                <a href={act.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-400 hover:underline">
                  查看来源 →
                </a>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
