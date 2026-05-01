import { useQuery } from '@tanstack/react-query'
import { Zap, ArrowUp, Clock } from 'lucide-react'
import { speedApi, dashboardApi } from '../api/endpoints'
import { useRealtimeStore } from '../stores/realtimeStore'
import AnimatedPage from '../components/ui/AnimatedPage'
import GlassCard from '../components/ui/GlassCard'
import { SkeletonCard } from '../components/ui/Skeleton'
import SummaryCard from '../components/dashboard/SummaryCard'
import SpeedGauge from '../components/dashboard/SpeedGauge'
import QuickTestButton from '../components/dashboard/QuickTestButton'
import TestProgressOverlay from '../components/dashboard/TestProgressOverlay'
import StatusIndicator from '../components/dashboard/StatusIndicator'
import HealthScoreRing from '../components/dashboard/HealthScoreRing'
import HealthTimelineChart from '../components/charts/HealthTimelineChart'
import { formatSpeed } from '../utils/formatters'

export default function DashboardPage() {
  const { data: latestSpeed, isLoading: loadingSpeed } = useQuery({
    queryKey: ['speed', 'latest'],
    queryFn: () => speedApi.latest().then((r) => r.data),
    refetchInterval: 10_000,
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['speed', 'stats', '24h'],
    queryFn: () => speedApi.stats('24h').then((r) => r.data),
    refetchInterval: 30_000,
  })

  const { data: healthScore, isLoading: loadingHealth } = useQuery({
    queryKey: ['dashboard', 'health-score'],
    queryFn: () => dashboardApi.healthScore('24h').then(r => r.data),
    refetchInterval: 30_000,
  })

  const { data: timeline } = useQuery({
    queryKey: ['dashboard', 'health-timeline'],
    queryFn: () => dashboardApi.healthTimeline(7).then(r => r.data),
    refetchInterval: 60_000,
  })

  const { lastResult } = useRealtimeStore((s) => s.testProgress)

  const displayDownload = lastResult?.download_mbps ?? latestSpeed?.download_mbps ?? null
  const displayUpload = lastResult?.upload_mbps ?? latestSpeed?.upload_mbps ?? null

  const networkStatus = (() => {
    if (!displayDownload) return 'unknown' as const
    if (displayDownload >= 50) return 'good' as const
    if (displayDownload >= 25) return 'fair' as const
    return 'poor' as const
  })()

  return (
    <AnimatedPage>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-display dark:text-gray-100 text-gray-900">Dashboard</h2>
          <StatusIndicator status={networkStatus} />
        </div>
        <QuickTestButton />
      </div>

      <TestProgressOverlay />

      {/* Health Score */}
      {loadingHealth ? (
        <SkeletonCard />
      ) : healthScore?.overall != null ? (
        <HealthScoreRing score={healthScore.overall} trend_pct={healthScore.trend_pct} breakdown={healthScore.breakdown} />
      ) : null}

      {/* Speed Gauges */}
      {loadingSpeed ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <GlassCard className="flex justify-center">
            <SpeedGauge label="Download" value={displayDownload} />
          </GlassCard>
          <GlassCard className="flex justify-center">
            <SpeedGauge label="Upload" value={displayUpload} />
          </GlassCard>
        </div>
      )}

      {/* Summary Cards */}
      {loadingStats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard label="Avg Download" value={formatSpeed(stats?.test_count ? stats.avg_download : null)} subtitle="Last 24 hours" icon={<Zap size={18} />} index={0} />
          <SummaryCard label="Avg Upload" value={formatSpeed(stats?.test_count ? stats.avg_upload : null)} subtitle="Last 24 hours" icon={<ArrowUp size={18} />} index={1} />
          <SummaryCard label="Max Download" value={formatSpeed(stats?.test_count ? stats.max_download : null)} subtitle="Last 24 hours" icon={<Zap size={18} />} index={2} />
          <SummaryCard label="Tests Run" value={stats?.test_count ? stats.test_count.toString() : '--'} subtitle="Last 24 hours" icon={<Clock size={18} />} index={3} />
        </div>
      )}

      {/* Health Timeline */}
      {timeline?.timeline && timeline.timeline.some(t => t.score !== null) && (
        <GlassCard>
          <h3 className="text-lg font-semibold mb-4 dark:text-gray-100 text-gray-900">Health Score (7 Days)</h3>
          <HealthTimelineChart data={timeline.timeline} />
        </GlassCard>
      )}
    </AnimatedPage>
  )
}
