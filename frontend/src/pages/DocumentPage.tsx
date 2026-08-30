import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchDocument } from '../api/client'
import { Chip, DocTypeBadge, SentimentBadge } from '../components/Badge'
import DocumentCard from '../components/DocumentCard'
import { LoadingState } from '../components/States'

export default function DocumentPage() {
  const { id } = useParams()
  const docId = Number(id)
  const { data, isLoading } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => fetchDocument(docId),
    enabled: Number.isFinite(docId),
  })

  if (isLoading || !data) return <LoadingState />

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <Link to="/search" className="text-sm text-slate-400 hover:text-emerald-300">
        ← 返回检索
      </Link>
      <div>
        <div className="mb-3 flex flex-wrap gap-2">
          <DocTypeBadge type={data.doc_type} />
          <SentimentBadge sentiment={data.sentiment} />
          {data.is_demo && <span className="text-xs text-amber-400">演示语料</span>}
        </div>
        <h2 className="text-2xl font-semibold text-white">{data.title}</h2>
        <p className="mt-2 text-sm text-slate-400">
          {data.source_domain} · {data.stream} · {data.country_code || '多市场'} · 命中 {data.hit_count} 次
        </p>
        {data.url && (
          <a href={data.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-sm text-emerald-400 hover:underline">
            打开原始链接
          </a>
        )}
      </div>

      {data.summary_zh && (
        <section className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-300">整理后的摘要</h3>
          <p className="text-sm leading-7 text-slate-200">{data.summary_zh}</p>
        </section>
      )}

      {data.facts?.length > 0 && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-2 text-sm font-semibold text-white">抽出的事实</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-slate-300">
            {data.facts.map((f, i) => (
              <li key={i}>
                <span className="text-slate-500">[{f.kind}]</span> {f.claim}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-wrap gap-2">
        {data.entities.map((e) => (
          <Chip key={e.id} to={`/entities/${e.id}`}>
            {e.name} · {e.entity_type}
          </Chip>
        ))}
        {data.tags.map((t) => (
          <Chip key={t.id} to={`/search?tag=${encodeURIComponent(t.slug)}`}>
            #{t.name}
          </Chip>
        ))}
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h3 className="mb-2 text-sm font-semibold text-white">原文</h3>
        <p className="whitespace-pre-wrap text-sm leading-7 text-slate-300">{data.full_text || data.snippet}</p>
        {data.query && <p className="mt-4 text-xs text-slate-500">捕获这条材料的查询：{data.query}</p>}
      </section>

      {data.related.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-white">相关原文（共享实体）</h3>
          <div className="grid grid-cols-1 gap-4">
            {data.related.map((d) => (
              <DocumentCard key={d.id} doc={d} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
