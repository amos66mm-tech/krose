interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  accent?: 'emerald' | 'sky' | 'amber' | 'rose'
}

const ACCENTS: Record<string, string> = {
  emerald: 'from-emerald-500/20 to-emerald-500/0 text-emerald-300',
  sky: 'from-sky-500/20 to-sky-500/0 text-sky-300',
  amber: 'from-amber-500/20 to-amber-500/0 text-amber-300',
  rose: 'from-rose-500/20 to-rose-500/0 text-rose-300',
}

export default function StatCard({ label, value, hint, accent = 'emerald' }: StatCardProps) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-gradient-to-br ${ACCENTS[accent]} bg-slate-900/60 p-4`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
  )
}
