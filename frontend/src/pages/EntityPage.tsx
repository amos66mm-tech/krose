import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchEntity } from '../api/client'
import { Chip } from '../components/Badge'
import DocumentCard from '../components/DocumentCard'
import { LoadingState } from '../components/States'

export default function EntityPage() {
  const { id } = useParams()
  const entityId = Number(id)
  const { data, isLoading } = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => fetchEntity(entityId),
    enabled: Number.isFinite(entityId),
  })

  if (isLoading || !data) return <LoadingState />

  return (
    <div className="flex flex-col gap-6">
      <Link to="/entities" className="text-sm text-slate-400 hover:text-emerald-300">
        ← 全部实体
      </Link>
      <div>
        <div className="text-xs uppercase tracking-wide text-slate-500">{data.entity_type}</div>
        <h2 className="text-2xl font-semibold text-white">
          {data.name}
          {!data.is_seeded && <span className="ml-3 text-sm font-normal text-fuchsia-300">从原文中发现</span>}
        </h2>
        {data.description && <p className="mt-2 text-sm text-slate-300">{data.description}</p>}
        <p className="mt-1 text-xs text-slate-500">
          {data.mention_count} 次提及
          {data.country_code ? ` · ${data.country_code}` : ''}
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {data.aliases.map((a) => (
            <Chip key={a}>{a}</Chip>
          ))}
        </div>
      </div>

      {data.related_entities.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold text-white">常常一起出现</h3>
          <div className="flex flex-wrap gap-2">
            {data.related_entities.map((e) => (
              <Chip key={e.id} to={`/entities/${e.id}`}>
                {e.name}
              </Chip>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="mb-3 text-sm font-semibold text-white">提到它的原文</h3>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.documents.map((d) => (
            <DocumentCard key={d.id} doc={d} />
          ))}
        </div>
      </section>
    </div>
  )
}
