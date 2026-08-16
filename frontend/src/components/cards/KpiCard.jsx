import { motion } from 'framer-motion'

const ACCENT_STYLES = {
  teal:    { bar: 'bg-teal-500/50',    text: 'text-teal-600 dark:text-teal-400',    glow: 'hover:shadow-teal-500/10',    badge: 'bg-teal-500/10 text-teal-600 dark:text-teal-400' },
  blue:    { bar: 'bg-blue-500/50',    text: 'text-blue-600 dark:text-blue-400',    glow: 'hover:shadow-blue-500/10',    badge: 'bg-blue-500/10 text-blue-600 dark:text-blue-400' },
  violet:  { bar: 'bg-violet-500/50',  text: 'text-violet-600 dark:text-violet-400', glow: 'hover:shadow-violet-500/10',  badge: 'bg-violet-500/10 text-violet-600 dark:text-violet-400' },
  emerald: { bar: 'bg-emerald-500/50', text: 'text-emerald-600 dark:text-emerald-400', glow: 'hover:shadow-emerald-500/10', badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' },
  amber:   { bar: 'bg-amber-500/50',   text: 'text-amber-600 dark:text-signal',     glow: 'hover:shadow-amber-500/10',   badge: 'bg-amber-500/10 text-amber-600 dark:text-signal' },
  alert:   { bar: 'bg-rose-500/60',    text: 'text-rose-600 dark:text-rose-400',    glow: 'hover:shadow-rose-500/10',    badge: 'bg-rose-500/10 text-rose-600 dark:text-rose-400' },
  neutral: { bar: 'bg-navy/40',        text: 'text-ink dark:text-slate-200',        glow: 'hover:shadow-slate-500/10',   badge: 'bg-slate-500/10 text-ink dark:text-slate-200' },
}

export default function KpiCard({ label, value, unit, trend, accent = 'teal', icon: Icon }) {
  const style = ACCENT_STYLES[accent] || ACCENT_STYLES.teal
  const trendUp = trend > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 260, damping: 22 }}
      className={`bg-paper-raised dark:bg-panel border border-slate-200 dark:border-slate-800 rounded-xl p-5
                  flex flex-col gap-2 relative overflow-hidden shadow-none hover:shadow-xl ${style.glow}`}
    >
      <div className={`absolute top-0 left-0 w-full h-[3px] ${style.bar}`} />

      <div className="flex items-start justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
          {label}
        </span>
        {Icon && (
          <span className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${style.badge}`}>
            <Icon size={15} strokeWidth={2.2} />
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className={`font-display text-3xl font-semibold ${style.text}`}>{value}</span>
        {unit && <span className="font-mono text-xs text-slate-400">{unit}</span>}
      </div>

      {trend !== undefined && (
        <span className={`font-mono text-[10px] ${trendUp ? 'text-amber-600 dark:text-signal' : 'text-teal-600 dark:text-teal-400'}`}>
          {trendUp ? '▲' : '▼'} {Math.abs(trend)}% vs prev period
        </span>
      )}
    </motion.div>
  )
}
