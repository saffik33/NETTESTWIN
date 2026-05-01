import { useQuery } from '@tanstack/react-query'
import { pingApi, dnsApi } from '../api/endpoints'
import { formatLatency, formatPercent } from '../utils/formatters'
import { formatDateTime } from '../utils/dateUtils'
import { getLatencyColor } from '../utils/constants'
import AnimatedPage from '../components/ui/AnimatedPage'
import GlassCard from '../components/ui/GlassCard'
import { SkeletonCard, SkeletonChart, SkeletonTable } from '../components/ui/Skeleton'
import SummaryCard from '../components/dashboard/SummaryCard'
import PingLineChart from '../components/charts/PingLineChart'

export default function NetworkHealthPage() {
  const { data: pingHistory, isLoading: loadingPing } = useQuery({
    queryKey: ['ping', 'history'],
    queryFn: () => pingApi.history(50).then((r) => r.data),
  })

  const { data: pingStats, isLoading: loadingStats } = useQuery({
    queryKey: ['ping', 'stats'],
    queryFn: () => pingApi.stats('24h').then((r) => r.data),
  })

  const { data: dnsLatest } = useQuery({
    queryKey: ['dns', 'latest'],
    queryFn: () => dnsApi.latest().then((r) => r.data),
  })

  return (
    <AnimatedPage>
      <h2 className="text-2xl font-bold tracking-display dark:text-gray-100 text-gray-900">Network Health</h2>

      {loadingStats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard label="Avg Latency" value={formatLatency(pingStats?.test_count ? pingStats.avg_latency : null)} subtitle="Last 24h" index={0} />
          <SummaryCard label="Avg Jitter" value={formatLatency(pingStats?.test_count ? pingStats.avg_jitter : null)} subtitle="Last 24h" index={1} />
          <SummaryCard label="Packet Loss" value={formatPercent(pingStats?.test_count ? pingStats.avg_packet_loss : null)} subtitle="Last 24h" index={2} />
          <SummaryCard label="Tests" value={pingStats?.test_count ? pingStats.test_count.toString() : '--'} subtitle="Last 24h" index={3} />
        </div>
      )}

      {loadingPing ? (
        <SkeletonChart />
      ) : (
        <GlassCard>
          <h3 className="text-lg font-semibold mb-4 dark:text-gray-100 text-gray-900">Latency & Jitter</h3>
          {pingHistory && pingHistory.length > 0 ? (
            <PingLineChart data={pingHistory} />
          ) : (
            <div className="h-64 flex items-center justify-center dark:text-gray-500 text-gray-400">No ping data yet</div>
          )}
        </GlassCard>
      )}

      {/* DNS Results */}
      <GlassCard>
        <h3 className="text-lg font-semibold mb-4 dark:text-gray-100 text-gray-900">DNS Resolution (Latest)</h3>
        {dnsLatest && dnsLatest.length > 0 ? (
          <div className="space-y-2">
            {dnsLatest.map((d, i) => (
              <div key={i} className="flex items-center justify-between py-2 dark:border-b dark:border-white/[0.04] border-b border-gray-100 last:border-0">
                <span className="dark:text-gray-300 text-gray-600">{d.target_domain}</span>
                <div className="flex items-center gap-4">
                  <span className="text-sm dark:text-gray-500 text-gray-400">{d.resolved_ip || '--'}</span>
                  <span className={`font-medium tabular-nums ${d.success ? getLatencyColor(d.resolution_time_ms) : 'text-red-400'}`}>
                    {d.success ? formatLatency(d.resolution_time_ms) : 'Failed'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="dark:text-gray-500 text-gray-400 text-center py-4">No DNS data yet</div>
        )}
      </GlassCard>

      {/* Ping History Table */}
      {loadingPing ? (
        <SkeletonTable />
      ) : (
        <GlassCard noPadding>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="glass-table-head">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-xs tracking-label dark:text-gray-500 text-gray-400">Time</th>
                  <th className="text-right px-4 py-3 font-medium text-xs tracking-label dark:text-gray-500 text-gray-400">Latency</th>
                  <th className="text-right px-4 py-3 font-medium text-xs tracking-label dark:text-gray-500 text-gray-400">Jitter</th>
                  <th className="text-right px-4 py-3 font-medium text-xs tracking-label dark:text-gray-500 text-gray-400">Loss</th>
                  <th className="text-left px-4 py-3 font-medium text-xs tracking-label dark:text-gray-500 text-gray-400">Target</th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-white/[0.04] divide-gray-100">
                {pingHistory?.map((row) => (
                  <tr key={row.id} className="glass-table-row transition-colors">
                    <td className="px-4 py-3 dark:text-gray-300 text-gray-600">{formatDateTime(row.timestamp)}</td>
                    <td className={`px-4 py-3 text-right font-medium tabular-nums ${getLatencyColor(row.avg_latency_ms)}`}>{formatLatency(row.avg_latency_ms)}</td>
                    <td className="px-4 py-3 text-right dark:text-gray-500 text-gray-400 tabular-nums">{formatLatency(row.jitter_ms)}</td>
                    <td className="px-4 py-3 text-right dark:text-gray-500 text-gray-400 tabular-nums">{formatPercent(row.packet_loss_pct)}</td>
                    <td className="px-4 py-3 dark:text-gray-500 text-gray-400">{row.target_host}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </AnimatedPage>
  )
}
