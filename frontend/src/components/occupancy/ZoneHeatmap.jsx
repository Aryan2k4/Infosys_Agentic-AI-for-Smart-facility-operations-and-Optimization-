import Card from '../maintenance/Card'

function heatColor(pct) {
  if (pct >= 90) return 'bg-rose-500'
  if (pct >= 70) return 'bg-amber-400'
  if (pct >= 40) return 'bg-teal-400'
  if (pct >= 15) return 'bg-teal-200 dark:bg-teal-900'
  return 'bg-slate-100 dark:bg-slate-800'
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)

export default function ZoneHeatmap({ heatmap, zones, onSelect }) {
  const nameById = Object.fromEntries((zones || []).map(z => [z.zone_id, z.name]))

  return (
    <Card title="Occupancy Heatmap" badge="AVG UTILIZATION BY HOUR">
      <div className="overflow-x-auto">
        <div className="min-w-[640px]">
          <div className="grid gap-[3px] mb-1" style={{ gridTemplateColumns: '140px repeat(24, 1fr)' }}>
            <div />
            {HOURS.map(h => (
              <div key={h} className="text-center font-mono text-[8px] text-slate-400">
                {h % 3 === 0 ? h : ''}
              </div>
            ))}
          </div>
          {(heatmap || []).map(row => (
            <div key={row.zone_id} className="grid gap-[3px] mb-[3px] items-center" style={{ gridTemplateColumns: '140px repeat(24, 1fr)' }}>
              <div
                onClick={() => onSelect?.(row.zone_id)}
                className={`font-mono text-[10px] text-slate-500 truncate pr-2 ${onSelect ? 'cursor-pointer hover:text-teal-500 transition-colors' : ''}`}
              >
                {nameById[row.zone_id] || row.zone_id}
              </div>
              {row.hourly_avg_utilization_pct.map((pct, h) => (
                <div
                  key={h}
                  title={`${nameById[row.zone_id] || row.zone_id} · ${h}:00 · ${pct}%`}
                  className={`h-4 rounded-sm ${heatColor(pct)}`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-3 mt-3 font-mono text-[9px] text-slate-500">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-slate-100 dark:bg-slate-800" /> quiet</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-teal-200 dark:bg-teal-900" /> low</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-teal-400" /> moderate</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-amber-400" /> busy</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-rose-500" /> overcrowded</span>
      </div>
    </Card>
  )
}
