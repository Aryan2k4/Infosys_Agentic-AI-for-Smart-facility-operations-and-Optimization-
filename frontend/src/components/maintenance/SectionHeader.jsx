export default function SectionHeader({ title, subtitle, badge }) {
  return (
    <div className="flex items-end justify-between flex-wrap gap-2 mb-1">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink dark:text-slate-100 tracking-tight">
          {title}
        </h2>
        {subtitle && (
          <p className="font-mono text-[11px] text-slate-500 mt-0.5">{subtitle}</p>
        )}
      </div>
      {badge && (
        <span className="font-mono text-[9px] tracking-widest px-2 py-1 rounded-full border border-slate-200 dark:border-slate-800 text-slate-500">
          {badge}
        </span>
      )}
    </div>
  )
}
