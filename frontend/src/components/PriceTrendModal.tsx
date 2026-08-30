import { useQuery } from '@tanstack/react-query'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fetchPriceHistory } from '../api/client'
import { LoadingState } from './States'

interface Props {
  platformId: number
  platformName: string
  giftCardTypeId: number
  giftCardTypeName: string
  onClose: () => void
}

export default function PriceTrendModal({ platformId, platformName, giftCardTypeId, giftCardTypeName, onClose }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['price-history', platformId, giftCardTypeId],
    queryFn: () => fetchPriceHistory(platformId, giftCardTypeId, 30),
  })

  const chartData = (data ?? []).map((q) => ({
    time: new Date(q.collected_at).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit' }),
    rate: q.rate_percent,
  }))

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-xl border border-slate-800 bg-slate-900 p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">
            {platformName} · {giftCardTypeName} 回收价趋势（近30天）
          </h3>
          <button onClick={onClose} className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-800 hover:text-white">
            ✕
          </button>
        </div>
        {isLoading ? (
          <LoadingState />
        ) : chartData.length < 2 ? (
          <p className="py-10 text-center text-sm text-slate-500">历史数据点还太少，多运行几次采集后即可看到趋势曲线</p>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  domain={['dataMin - 2', 'dataMax + 2']}
                  unit="%"
                />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', fontSize: 12 }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="rate" stroke="#34d399" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
