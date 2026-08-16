import { motion } from 'framer-motion'

export default function HeroStatCard({ label, value, unit, trend, icon: Icon }) {
  const trendUp = trend > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 240, damping: 22 }}
      className="relative h-full rounded-2xl p-6 flex flex-col justify-between overflow-hidden
                 border border-teal-500/20 dark:border-teal-400/20
                 bg-gradient-to-br from-teal-500/[0.07] via-transparent to-blue-500/[0.05]
                 dark:from-teal-400/[0.08] dark:via-transparent dark:to-blue-500/[0.06]
                 backdrop-blur-sm"
    >
      {/* ambient glow blob */}
      <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-teal-400/20 blur-3xl pointer-events-none" />

      <div className="relative flex items-start justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {label}
        </span>
        {Icon && (
          <span className="w-10 h-10 rounded-xl bg-teal-500/15 dark:bg-teal-400/15 text-teal-600 dark:text-teal-400
                            flex items-center justify-center shrink-0 shadow-lg shadow-teal-500/10">
            <Icon size={18} strokeWidth={2.2} />
          </span>
        )}
      </div>

      <div className="relative mt-6">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-5xl font-bold text-ink dark:text-slate-50 tracking-tight">
            {value}
          </span>
          {unit && <span className="font-mono text-sm text-slate-400">{unit}</span>}
        </div>
        {trend !== undefined && (
          <span className={`inline-block mt-3 font-mono text-[11px] px-2 py-1 rounded-full border
            ${trendUp
              ? 'text-amber-600 dark:text-signal border-amber-400/30 bg-amber-500/5'
              : 'text-teal-600 dark:text-teal-400 border-teal-400/30 bg-teal-500/5'}`}>
            {trendUp ? '▲' : '▼'} {Math.abs(trend)}% vs prev period
          </span>
        )}
      </div>
    </motion.div>
  )
}
