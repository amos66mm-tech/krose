import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { fetchPlatforms, fetchSocialPosts } from '../api/client'
import { NetworkBadge, SentimentBadge } from '../components/Badge'
import { EmptyState, LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'

export default function SocialPage() {
  const { countryCode } = useCountry()
  const { data: platforms } = useQuery({ queryKey: ['platforms', countryCode], queryFn: () => fetchPlatforms(countryCode) })
  const { data: posts, isLoading } = useQuery({
    queryKey: ['social', countryCode],
    queryFn: () => fetchSocialPosts(countryCode, 100),
    refetchInterval: 60_000,
  })

  const platformLookup = useMemo(() => new Map((platforms ?? []).map((p) => [p.id, p])), [platforms])

  if (isLoading) return <LoadingState />
  if (!posts?.length) return <EmptyState label="暂无社交媒体动态" />

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-white">社媒动态</h2>
        <p className="text-sm text-slate-400">聚合各平台在 Twitter/Facebook/Instagram/Telegram 上的最新动态与舆情倾向。</p>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {posts.map((post) => {
          const platform = platformLookup.get(post.platform_id)
          return (
            <div key={post.id} className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold text-white">{platform?.name ?? `平台 #${post.platform_id}`}</span>
                <NetworkBadge network={post.network} />
              </div>
              <p className="flex-1 text-sm text-slate-300">{post.content}</p>
              <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                <span>{post.author}</span>
                <SentimentBadge sentiment={post.sentiment} />
              </div>
              <div className="mt-1 flex items-center justify-between text-xs text-slate-600">
                <span>{post.published_at ? new Date(post.published_at).toLocaleString('zh-CN') : ''}</span>
                <span>互动热度 {post.engagement_score.toFixed(0)}</span>
              </div>
              {post.url && (
                <a href={post.url} target="_blank" rel="noreferrer" className="mt-2 text-xs text-emerald-400 hover:underline">
                  查看原文 →
                </a>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
