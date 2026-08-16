import { useEffect, useState, useCallback } from 'react'
import { occupancyService } from '../../services/occupancyService'
import OccupancyKpiRow from '../../components/occupancy/OccupancyKpiRow'
import ZoneHeatmap from '../../components/occupancy/ZoneHeatmap'
import ZoneTable from '../../components/occupancy/ZoneTable'
import OccupancyAlertsList from '../../components/occupancy/OccupancyAlertsList'
import ZoneDetailPanel from '../../components/occupancy/ZoneDetailPanel'
import SectionHeader from '../../components/maintenance/SectionHeader'
import AgentTraceViewer from '../../components/agent/AgentTraceViewer'
import LiveIndicator from '../../components/ui/LiveIndicator'

export default function OccupancyDashboardPage() {
  const [data, setData] = useState(null)
  const [selectedZoneId, setSelectedZoneId] = useState(null)
  const [investigation, setInvestigation] = useState(null)
  const [investigating, setInvestigating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    const result = await occupancyService.getBuilding()
    setData(result)
    setLastUpdated(new Date())
  }, [])

  const refreshNow = useCallback(async () => {
    setRefreshing(true)
    try { await load() } catch (err) { setError(err.message) } finally { setRefreshing(false) }
  }, [load])

  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        setLoading(true)
        await load()
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    init()
    return () => { cancelled = true }
  }, [load])

  const runInvestigation = useCallback(async () => {
    setInvestigating(true)
    setInvestigation(null)
    try {
      const result = await occupancyService.getInvestigation()
      setInvestigation(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setInvestigating(false)
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="font-mono text-xs text-slate-500 tracking-widest animate-pulse-line">SCANNING BUILDING ZONES…</span>
      </div>
    )
  }

  if (error) {
    return <div className="p-6 text-red-500 dark:text-red-400 text-sm font-mono">connection failed: {error}</div>
  }

  return (
    <div className="min-h-screen animate-fade-in">
      <div className="border-b border-slate-200 dark:border-slate-800/80 px-6 md:px-10 py-6 flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="mb-2"><LiveIndicator lastUpdated={lastUpdated} isRefreshing={refreshing} onRefresh={refreshNow} /></div>
          <h1 className="font-display text-3xl md:text-4xl font-semibold text-ink dark:text-slate-100 tracking-tight">Occupancy Intelligence</h1>
          <p className="font-mono text-xs text-slate-500 mt-2">
            {data.building_id} <span className="text-slate-300 dark:text-slate-700">·</span> ML-driven space utilization monitoring
          </p>
        </div>
      </div>

      <div className="p-6 md:p-10 flex flex-col gap-10 max-w-[1400px]">
        <section className="flex flex-col gap-4">
          <SectionHeader title="Building Overview" subtitle="Live headcount and utilization across every monitored zone" />
          <OccupancyKpiRow building={data.building} confidence={data.model_confidence} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
            <ZoneHeatmap heatmap={data.heatmap} zones={data.zones} onSelect={setSelectedZoneId} />
            <ZoneTable zones={data.zones} onSelect={setSelectedZoneId} selectedZoneId={selectedZoneId} />
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <SectionHeader
            title="Agent Investigation"
            subtitle="The Occupancy Agent decides for itself which zones warrant a closer look — including flagging restricted-zone occupancy to Security"
          />
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-4 items-start">
            <div className="bg-paper-raised dark:bg-panel border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col gap-3">
              <h3 className="font-display text-sm font-medium text-ink dark:text-slate-200">Run Deep Investigation</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Checks building-wide occupancy, drills into overcrowded and restricted zones, and hands off to Security when warranted.
              </p>
              <button
                onClick={runInvestigation}
                disabled={investigating}
                className="mt-1 font-mono text-xs tracking-wide px-4 py-2.5 rounded-lg border border-teal-500/50 dark:border-teal-400/40
                           text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-400/5 hover:bg-teal-100 dark:hover:bg-teal-400/10
                           disabled:opacity-40 disabled:cursor-not-allowed transition-colors self-start"
              >
                {investigating ? 'agent working…' : '▶ investigate occupancy'}
              </button>
            </div>
            <AgentTraceViewer
              investigation={investigation}
              isLoading={investigating}
              title="Occupancy Agent Trace"
              hint="Watch the agent decide whether restricted-zone occupancy warrants a Security handoff."
            />
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <SectionHeader title="Alerts" subtitle="Overcrowding, low-utilization space signals, and restricted-zone security handoffs" />
          <OccupancyAlertsList alerts={data.top_alerts} />
        </section>
      </div>

      <ZoneDetailPanel zoneId={selectedZoneId} onClose={() => setSelectedZoneId(null)} />
    </div>
  )
}
