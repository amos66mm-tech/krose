import { Link } from 'react-router-dom'
import { Chip, DocTypeBadge, SentimentBadge } from './Badge'
import type { DocumentListItem } from '../types'

export default function DocumentCard({ doc }: { doc: DocumentListItem }) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 transition hover:border-emerald-500/40">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <DocTypeBadge type={doc.doc_type} />
        <SentimentBadge sentiment={doc.sentiment} />
        {doc.country_code && <span className="text-xs text-slate-500">{doc.country_code}</span>}
        {doc.is_demo && <span className="text-xs text-amber-400">演示语料</span>}
        <span className="text-xs text-slate-500">{doc.source_domain || 'unknown'}</span>
      </div>
      <Link to={`/documents/${doc.id}`} className="text-base font-semibold text-white hover:text-emerald-300">
        {doc.title}
      </Link>
      {doc.summary_zh && <p className="mt-2 text-sm leading-6 text-slate-300">{doc.summary_zh}</p>}
      {!doc.summary_zh && doc.snippet && <p className="mt-2 text-sm text-slate-400">{doc.snippet.slice(0, 220)}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {doc.entities.slice(0, 6).map((e) => (
          <Chip key={e.id} to={`/entities/${e.id}`}>
            {e.name}
          </Chip>
        ))}
        {doc.tags.slice(0, 4).map((t) => (
          <Chip key={t.id} to={`/search?tag=${encodeURIComponent(t.slug)}`}>
            #{t.name}
          </Chip>
        ))}
      </div>
    </article>
  )
}
