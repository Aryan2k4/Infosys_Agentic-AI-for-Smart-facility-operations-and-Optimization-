export default function Card({ title, badge, className = '', children }) {
  return (
    <div className={`bg-paper-raised dark:bg-panel border border-slate-200 dark:border-slate-800 rounded-xl p-5 ${className}`}>
      {(title || badge) && (
        <div className="flex items-center justify-between mb-4 gap-2">
          {title && <h3 className="font-display text-sm font-medium text-ink dark:text-slate-200">{title}</h3>}
          {badge && <span className="font-mono text-[10px] tracking-widest text-slate-500 shrink-0">{badge}</span>}
        </div>
      )}
      {children}
    </div>
  )
}
