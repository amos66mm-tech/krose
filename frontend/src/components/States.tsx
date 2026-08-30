export function LoadingState({ label = '加载中…' }: { label?: string }) {
  return <div className="flex items-center justify-center py-16 text-sm text-slate-400">{label}</div>
}

export function EmptyState({ label = '暂无数据' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-800 py-16 text-sm text-slate-500">
      <span className="text-2xl">🗂️</span>
      {label}
    </div>
  )
}
