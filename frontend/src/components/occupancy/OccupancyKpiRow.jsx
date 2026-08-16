import { LayoutGrid, UsersRound, Gauge, AlertTriangle, Target } from 'lucide-react'
import KpiCard from '../cards/KpiCard'

export default function OccupancyKpiRow({ building, confidence }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
      <KpiCard label="Zones Monitored" value={building.zones_monitored} accent="blue" icon={LayoutGrid} />
      <KpiCard label="Total Headcount" value={building.total_headcount} unit={`/ ${building.total_capacity ?? '—'}`} accent="emerald" icon={UsersRound} />
      <KpiCard label="Avg Utilization" value={building.avg_utilization_pct} unit="%" accent="teal" icon={Gauge} />
      <KpiCard label="Overcrowded Zones" value={building.overcrowded_zones} accent="alert" icon={AlertTriangle} />
      {confidence?.available && (
        <KpiCard
          label="Detection Accuracy"
          value={`${Math.round(confidence.held_out_accuracy * 100)}%`}
          unit={confidence.model_used?.replace(/_/g, ' ')}
          accent="violet"
          icon={Target}
        />
      )}
    </div>
  )
}
