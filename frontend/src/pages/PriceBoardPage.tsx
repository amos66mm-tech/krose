import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { fetchGiftCardTypes, fetchPlatforms, fetchPriceBoard } from '../api/client'
import PriceTrendModal from '../components/PriceTrendModal'
import { EmptyState, LoadingState } from '../components/States'
import { useCountry } from '../context/CountryContext'
import type { PriceBoardCell } from '../types'

export default function PriceBoardPage() {
  const { countryCode } = useCountry()
  const [selectedCell, setSelectedCell] = useState<PriceBoardCell | null>(null)

  const { data: platforms, isLoading: loadingPlatforms } = useQuery({
    queryKey: ['platforms', countryCode],
    queryFn: () => fetchPlatforms(countryCode),
  })
  const { data: cardTypes, isLoading: loadingCards } = useQuery({
    queryKey: ['gift-card-types'],
    queryFn: fetchGiftCardTypes,
  })
  const { data: board, isLoading: loadingBoard } = useQuery({
    queryKey: ['price-board', countryCode],
    queryFn: () => fetchPriceBoard(countryCode),
    refetchInterval: 30_000,
  })

  const cellMap = useMemo(() => {
    const map = new Map<string, PriceBoardCell>()
    board?.forEach((cell) => map.set(`${cell.platform_id}:${cell.gift_card_type_id}`, cell))
    return map
  }, [board])

  if (loadingPlatforms || loadingCards || loadingBoard) return <LoadingState />
  if (!platforms?.length || !cardTypes?.length) return <EmptyState label="没有找到平台或卡种，请先在后端种子数据里添加" />

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-white">价格看板</h2>
        <p className="text-sm text-slate-400">
          按平台 × 礼品卡种类矩阵展示最新回收价（相对卡面值的百分比）。绿色徽标代表相比上次上涨，红色代表下跌，点击任意格子查看历史趋势。
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80">
            <tr>
              <th className="sticky left-0 z-10 bg-slate-900/80 px-4 py-3 text-left font-semibold text-slate-300">
                平台
              </th>
              {cardTypes.map((card) => (
                <th key={card.id} className="px-4 py-3 text-center font-semibold text-slate-300 whitespace-nowrap">
                  {card.icon} {card.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {platforms.map((platform) => (
              <tr key={platform.id} className="hover:bg-slate-900/40">
                <td className="sticky left-0 z-10 bg-slate-950 px-4 py-3 font-medium text-white whitespace-nowrap">
                  {platform.name}
                  <div className="text-xs font-normal text-slate-500">{platform.notes.slice(0, 24)}</div>
                </td>
                {cardTypes.map((card) => {
                  const cell = cellMap.get(`${platform.id}:${card.id}`)
                  if (!cell) {
                    return (
                      <td key={card.id} className="px-4 py-3 text-center text-slate-600">
                        —
                      </td>
                    )
                  }
                  const changeColor =
                    cell.change_percent > 0
                      ? 'text-emerald-400'
                      : cell.change_percent < 0
                        ? 'text-rose-400'
                        : 'text-slate-500'
                  return (
                    <td
                      key={card.id}
                      onClick={() => setSelectedCell(cell)}
                      className="cursor-pointer px-4 py-3 text-center transition hover:bg-emerald-500/10"
                    >
                      <div className="font-semibold text-white">{cell.rate_percent.toFixed(1)}%</div>
                      <div className={`text-xs ${changeColor}`}>
                        {cell.is_new ? '🆕 新报价' : cell.change_percent !== 0 ? `${cell.change_percent > 0 ? '▲' : '▼'} ${Math.abs(cell.change_percent).toFixed(1)}%` : '持平'}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedCell && (
        <PriceTrendModal
          platformId={selectedCell.platform_id}
          platformName={selectedCell.platform_name}
          giftCardTypeId={selectedCell.gift_card_type_id}
          giftCardTypeName={selectedCell.gift_card_type_name}
          onClose={() => setSelectedCell(null)}
        />
      )}
    </div>
  )
}
