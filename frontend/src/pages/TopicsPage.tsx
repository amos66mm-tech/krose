import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchTags } from '../api/client'
import { LoadingState } from '../components/States'

export default function TopicsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['tags'], queryFn: fetchTags })

  if (isLoading) return <LoadingState />

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold text-white">主题</h2>
        <p className="text-sm text-slate-400">从原文里打上的标签。点进去看这个主题下所有材料。</p>
      </div>
      <div className="flex flex-wrap gap-3">
        {(data ?? [])
          .filter((t) => t.document_count > 0)
          .map((t) => (
            <Link
              key={t.id}
              to={`/search?tag=${encodeURIComponent(t.slug)}`}
              className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 hover:border-emerald-500/40"
            >
              <div className="text-sm font-medium text-white">#{t.name}</div>
              <div className="text-xs text-slate-500">
                {t.category} · {t.document_count} 篇
              </div>
            </Link>
          ))}
      </div>
    </div>
  )
}
