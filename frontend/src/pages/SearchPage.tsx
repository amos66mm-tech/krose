import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchDocTypes, searchDocuments } from '../api/client'
import DocumentCard from '../components/DocumentCard'
import { EmptyState, LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

const STREAMS = [
  { key: '', label: '全部网' },
  { key: 'market_scan', label: '市场全景' },
  { key: 'community', label: '社区' },
  { key: 'news_risk', label: '风险/监管' },
  { key: 'competitor_discovery', label: '新平台' },
  { key: 'rates', label: '行情' },
  { key: 'platform_watch', label: '已知平台' },
  { key: 'custom', label: '自定义' },
]

export default function SearchPage() {
  const { countryCode } = useCountry()
  const [params, setParams] = useSearchParams()
  const [draft, setDraft] = useState(params.get('q') ?? '')
  const q = params.get('q') ?? ''
  const docType = params.get('doc_type') ?? ''
  const stream = params.get('stream') ?? ''
  const tag = params.get('tag') ?? ''

  const { data: docTypes } = useQuery({ queryKey: ['doc-types'], queryFn: fetchDocTypes })
  const { data, isLoading } = useQuery({
    queryKey: ['search', q, countryCode, docType, stream, tag],
    queryFn: () =>
      searchDocuments({
        q,
        countryCode,
        docType: docType || undefined,
        stream: stream || undefined,
        tag: tag || undefined,
        limit: 50,
      }),
  })

  const filters = useMemo(() => ({ q, docType, stream, tag }), [q, docType, stream, tag])

  const update = (patch: Record<string, string>) => {
    const next = new URLSearchParams(params)
    Object.entries(patch).forEach(([k, v]) => {
      if (v) next.set(k, v)
      else next.delete(k)
    })
    setParams(next)
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold text-white">检索情报库</h2>
        <p className="text-sm text-slate-400">
          搜「scam」「MoMo」「FlashCards」「延迟」「CBN」——系统不会替你决定什么重要，只把收进来的材料摊开。
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          update({ q: draft })
        }}
        className="flex gap-2"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="任意关键词，中英文都可以"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-white outline-none focus:border-emerald-500"
        />
        <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400">
          搜索
        </button>
      </form>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => update({ doc_type: '' })}
          className={`rounded-full px-3 py-1 text-xs ${!docType ? 'bg-emerald-500 text-slate-950' : 'border border-slate-700 text-slate-300'}`}
        >
          全部类型
        </button>
        {(docTypes ?? []).map((t) => (
          <button
            key={t.key}
            onClick={() => update({ doc_type: t.key })}
            className={`rounded-full px-3 py-1 text-xs ${docType === t.key ? 'bg-emerald-500 text-slate-950' : 'border border-slate-700 text-slate-300'}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {STREAMS.map((s) => (
          <button
            key={s.key || 'all'}
            onClick={() => update({ stream: s.key })}
            className={`rounded-full px-3 py-1 text-xs ${stream === s.key ? 'bg-sky-500 text-slate-950' : 'border border-slate-700 text-slate-300'}`}
          >
            {s.label}
          </button>
        ))}
      </div>
      {tag && (
        <p className="text-xs text-slate-400">
          当前标签 #{tag}{' '}
          <button className="text-emerald-400" onClick={() => update({ tag: '' })}>
            清除
          </button>
        </p>
      )}

      {isLoading ? (
        <LoadingState />
      ) : !data?.items.length ? (
        <EmptyState label={filters.q ? `没有命中「${filters.q}」` : '没有符合筛选的原文'} />
      ) : (
        <>
          <p className="text-xs text-slate-500">共 {data.total} 条</p>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {data.items.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
