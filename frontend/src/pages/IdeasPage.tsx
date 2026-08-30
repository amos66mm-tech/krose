import { useQuery } from '@tanstack/react-query'
import { fetchIdeas } from '../api/client'
import { PriorityBadge } from '../components/Badge'
import { LoadingState } from '../components/States'

export default function IdeasPage() {
  const { data, isLoading } = useQuery({ queryKey: ['ideas'], queryFn: fetchIdeas })

  if (isLoading || !data) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-white">论坛内容增长点子</h2>
        <p className="text-sm text-slate-400">
          围绕「尼日利亚/加纳/喀麦隆礼品卡回收」这个核心业务，本工具持续采集的数据可以衍生出以下论坛内容与功能，用来提升卖家用户的粘性与信任。
        </p>
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {data.map((cat) => (
          <div key={cat.category} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <h3 className="mb-3 text-sm font-semibold text-emerald-300">{cat.category}</h3>
            <div className="flex flex-col gap-3">
              {cat.items.map((item) => (
                <div key={item.title} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-white">{item.title}</span>
                    <PriorityBadge priority={item.priority} />
                  </div>
                  <p className="text-xs text-slate-400">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
