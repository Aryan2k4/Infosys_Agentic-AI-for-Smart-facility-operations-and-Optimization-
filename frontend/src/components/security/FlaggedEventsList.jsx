import Card from '../maintenance/Card'

const RISK_STYLE = {
  high: 'border-l-rose-500',
  medium: 'border-l-amber-500',
  low: 'border-l-teal-500',
}

function scoreColor(score) {
  if (score >= 0.75) return 'text-rose-500'
  if (score >= 0.6) return 'text-amber-500'
  return 'text-slate-400'
}

export default function FlaggedEventsList({ events }) {
  return (
    <Card title="Flagged Events" badge="ANOMALY DETECTOR">
      {!events?.length && (
        <div className="text-xs text-slate-500 font-mono py-8 text-center">no flagged events</div>
      )}
      <div className="flex flex-col gap-2 max-h-[420px] overflow-y-auto pr-1">
        {events?.map((ev) => (
          <div key={ev.event_id} className={`border border-slate-200 dark:border-slate-800 border-l-4 ${RISK_STYLE[ev.risk_level] || ''} rounded-lg px-3 py-2.5`}>
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm text-ink dark:text-slate-200">
                  {ev.employee_id} <span className="text-slate-400">·</span> {ev.access_point_id}
                </p>
                <p className="font-mono text-[10px] text-slate-500 mt-0.5">
                  {new Date(ev.timestamp).toLocaleString()} · {ev.access_granted ? 'granted' : 'DENIED'} · risk: {ev.risk_level}
                </p>
              </div>
              <span className={`shrink-0 font-mono text-xs font-medium ${scoreColor(ev.anomaly_score)}`}>
                {ev.anomaly_score.toFixed(2)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
