import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchIntelOverview, searchDocuments } from '../api/client'
import DocumentCard from '../components/DocumentCard'
import StatCard from '../components/StatCard'
import { EmptyState, LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

export default function InboxPage() {
  const { countryCode } = useCountry()
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['intel-overview', countryCode],
    queryFn: () => fetchIntelOverview(countryCode),
  })
  const { data: latest, isLoading: loadingDocs } = useQuery({
    queryKey: ['intel-latest', countryCode],
    queryFn: () => searchDocuments({ countryCode, limit: 12 }),
  })

  if (loadingOverview || !overview) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-white">情报库</h2>
        <p className="text-sm text-slate-400">
          先把公开材料尽量收进来、整理成原文 + 实体 + 主题。你不必事先知道要什么——搜索和浏览会让需要的数据自己浮出来。
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="原文篇数" value={overview.total_documents} hint="全部归档，不只是抽出来的字段" accent="emerald" />
        <StatCard label="24h 新入库" value={overview.documents_24h} accent="sky" />
        <StatCard label="实体" value={overview.total_entities} hint={`其中新发现 ${overview.discovered_entities}`} accent="amber" />
        <StatCard label="正在撒的网" value={overview.watch_count} hint={overview.live_mode ? '真实搜索' : '演示语料'} accent="rose" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">按材料类型</h3>
            <Link to="/search" className="text-xs text-emerald-400 hover:underline">
              进入检索
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {overview.doc_type_counts.map((row) => (
              <Link
                key={row.key}
                to={`/search?doc_type=${encodeURIComponent(row.key)}`}
                className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 hover:border-emerald-500"
              >
                {row.label}
                <span className="ml-2 text-slate-500">{row.count}</span>
              </Link>
            ))}
            {overview.doc_type_counts.length === 0 && <p className="text-sm text-slate-500">还没有原文</p>}
          </div>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">新发现的实体</h3>
          <div className="flex flex-col gap-2">
            {overview.emerging_entities.length === 0 && (
              <p className="text-sm text-slate-500">最近没有种子名单之外的新名字。继续撒网就会出现。</p>
            )}
            {overview.emerging_entities.map((e) => (
              <Link key={e.id} to={`/entities/${e.id}`} className="flex items-center justify-between text-sm hover:text-emerald-300">
                <span>
                  {e.name}
                  <span className="ml-2 text-xs text-slate-500">{e.entity_type}</span>
                </span>
                <span className="text-xs text-slate-500">{e.mention_count} 次</span>
              </Link>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">被提到最多的实体</h3>
          <div className="flex flex-col divide-y divide-slate-800">
            {overview.top_entities.map((e) => (
              <Link key={e.id} to={`/entities/${e.id}`} className="flex items-center justify-between py-2 text-sm hover:text-emerald-300">
                <span className="text-slate-200">
                  {e.name}
                  {!e.is_seeded && <span className="ml-2 text-xs text-fuchsia-300">发现</span>}
                </span>
                <span className="text-slate-500">{e.mention_count}</span>
              </Link>
            ))}
          </div>
        </section>
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">主题标签</h3>
          <div className="flex flex-wrap gap-2">
            {overview.tag_counts.map((t) => (
              <Link
                key={t.key}
                to={`/search?tag=${encodeURIComponent(t.key)}`}
                className="rounded-full border border-slate-700 px-3 py-1 text-sm text-slate-300 hover:border-emerald-500"
              >
                #{t.label} {t.count}
              </Link>
            ))}
          </div>
        </section>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">最新入库的原文</h3>
          <Link to="/search" className="text-xs text-emerald-400 hover:underline">
            查看全部
          </Link>
        </div>
        {loadingDocs ? (
          <LoadingState />
        ) : !latest?.items.length ? (
          <EmptyState label="情报库还是空的。去「采集」页撒网，或确认演示语料已写入。" />
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {latest.items.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
