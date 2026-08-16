import { useEffect, useState, useCallback } from 'react'
import { securityService } from '../../services/securityService'
import SecurityKpiRow from '../../components/security/SecurityKpiRow'
import FlaggedEventsList from '../../components/security/FlaggedEventsList'
import SecurityAlertsList from '../../components/security/SecurityAlertsList'
import Card from '../../components/maintenance/Card'
import SectionHeader from '../../components/maintenance/SectionHeader'
import AgentTraceViewer from '../../components/agent/AgentTraceViewer'
import LiveIndicator from '../../components/ui/LiveIndicator'

const RISK_BADGE = {
  high: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  low: 'bg-teal-500/10 text-teal-400 border-teal-500/30',
}

export default function SecurityDashboardPage() {
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [investigation, setInvestigation] = useState(null)
  const [investigating, setInvestigating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    const [building, alertsData] = await Promise.all([
      securityService.getBuilding(),
      securityService.getAlerts(),
    ])
    setData(building)
    setAlerts(alertsData.alerts)
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
      const result = await securityService.getInvestigation()
      setInvestigation(result)
      const alertsData = await securityService.getAlerts()
      setAlerts(alertsData.alerts)
    } catch (err) {
      setError(err.message)
    } finally {
      setInvestigating(false)
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="font-mono text-xs text-slate-500 tracking-widest animate-pulse-line">SCANNING ACCESS LOGS…</span>
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
          <h1 className="font-display text-3xl md:text-4xl font-semibold text-ink dark:text-slate-100 tracking-tight">Security Intelligence</h1>
          <p className="font-mono text-xs text-slate-500 mt-2">
            {data.building_id} <span className="text-slate-300 dark:text-slate-700">·</span> anomaly-driven access monitoring
          </p>
        </div>
      </div>

      <div className="p-6 md:p-10 flex flex-col gap-10 max-w-[1400px]">
        <section className="flex flex-col gap-4">
          <SectionHeader title="Building Overview" subtitle="Access activity and anomaly detection across every monitored entry point" />
          <SecurityKpiRow building={data.building} confidence={data.model_confidence} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
            <FlaggedEventsList events={data.flagged_events} />
            <Card title="Access Points" badge={`${data.access_points?.length ?? 0} MONITORED`}>
              <div className="flex flex-col gap-2">
                {data.access_points?.map(ap => (
                  <div key={ap.access_point_id} className="flex items-center justify-between border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2.5">
                    <div>
                      <p className="text-sm text-ink dark:text-slate-200">{ap.name}</p>
                      <p className="font-mono text-[10px] text-slate-500">{ap.access_point_id}{ap.zone_id ? ` · ${ap.zone_id}` : ''}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full border text-[10px] font-mono ${RISK_BADGE[ap.risk_level] || ''}`}>
                      {ap.risk_level} risk
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <SectionHeader
            title="Agent Investigation"
            subtitle="The Security Agent weighs anomaly score against access-point risk and only opens alerts where the evidence is clear"
          />
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-4 items-start">
            <div className="bg-paper-raised dark:bg-panel border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col gap-3">
              <h3 className="font-display text-sm font-medium text-ink dark:text-slate-200">Run Deep Investigation</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Reviews flagged events, cross-references access-point risk level, and opens real alerts for the ones worth escalating.
              </p>
              <button
                onClick={runInvestigation}
                disabled={investigating}
                className="mt-1 font-mono text-xs tracking-wide px-4 py-2.5 rounded-lg border border-teal-500/50 dark:border-teal-400/40
                           text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-400/5 hover:bg-teal-100 dark:hover:bg-teal-400/10
                           disabled:opacity-40 disabled:cursor-not-allowed transition-colors self-start"
              >
                {investigating ? 'agent working…' : '▶ investigate access activity'}
              </button>
            </div>
            <AgentTraceViewer
              investigation={investigation}
              isLoading={investigating}
              title="Security Agent Trace"
              hint="Watch the agent weigh anomaly score against access-point risk before opening an alert."
            />
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <SectionHeader title="Alerts" subtitle="Anomaly-driven alerts, plus restricted-zone handoffs from the Occupancy Agent" />
          <SecurityAlertsList alerts={alerts} />
        </section>
      </div>
    </div>
  )
}
