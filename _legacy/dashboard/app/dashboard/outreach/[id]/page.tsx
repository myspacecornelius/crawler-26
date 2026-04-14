'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import StatsCard from '@/components/StatsCard';
import { useToast } from '@/components/ui/Toast';
import { getOutreachStats, startOutreach, pauseOutreach } from '@/lib/api';

interface OutreachStatsData {
  total_leads?: number;
  emails_sent?: number;
  opens?: number;
  open_rate?: number;
  replies?: number;
  reply_rate?: number;
  bounces?: number;
  clicks?: number;
  status?: string;
}

export default function OutreachDetailPage() {
  const { toast } = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const provider = searchParams.get('provider') || 'instantly';

  const [stats, setStats] = useState<OutreachStatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getOutreachStats(provider, id);
      setStats(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadStats();
  }, [provider, id]);

  const handleStart = async () => {
    setActionLoading(true);
    try {
      await startOutreach(provider, id);
      await loadStats();
    } catch (err: unknown) {
      toast({ title: 'Failed to start', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
    setActionLoading(false);
  };

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await pauseOutreach(provider, id);
      await loadStats();
    } catch (err: unknown) {
      toast({ title: 'Failed to pause', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
    setActionLoading(false);
  };

  // Find name from localStorage
  let campaignName = id;
  if (typeof window !== 'undefined') {
    try {
      const records = JSON.parse(localStorage.getItem('leadfactory_outreach_records') || '[]');
      const match = records.find((r: { provider_campaign_id: string }) => r.provider_campaign_id === id);
      if (match) campaignName = match.name;
    } catch { /* ignore */ }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link href="/dashboard/outreach" className="text-sm text-gray-400 hover:text-gray-600">Outreach</Link>
            <span className="text-gray-300">/</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{campaignName}</h1>
          <div className="flex items-center gap-3 mt-2">
            {stats?.status && (
              <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${
                stats.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                stats.status === 'paused' ? 'bg-amber-100 text-amber-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {stats.status}
              </span>
            )}
            <span className="text-sm text-gray-500 capitalize">{provider}</span>
            <span className="text-sm text-gray-400">ID: {id}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {stats?.status !== 'active' && (
            <button
              onClick={handleStart}
              disabled={actionLoading}
              className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              {actionLoading ? '...' : 'Start'}
            </button>
          )}
          {stats?.status === 'active' && (
            <button
              onClick={handlePause}
              disabled={actionLoading}
              className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
            >
              {actionLoading ? '...' : 'Pause'}
            </button>
          )}
        </div>
      </div>

      {/* Loading / Error */}
      {loading && (
        <div className="animate-pulse text-gray-400 py-12 text-center">Loading stats...</div>
      )}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 mb-8">
          {error}
        </div>
      )}

      {/* Stats Grid */}
      {stats && !loading && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          <StatsCard label="Total Leads" value={stats.total_leads ?? 0} icon="👥" />
          <StatsCard label="Emails Sent" value={stats.emails_sent ?? 0} icon="📤" />
          <StatsCard
            label="Opens"
            value={stats.opens ?? 0}
            icon="👁️"
            change={stats.open_rate != null ? `${stats.open_rate}% rate` : undefined}
            changeType={stats.open_rate != null && stats.open_rate > 20 ? 'positive' : 'neutral'}
          />
          <StatsCard
            label="Replies"
            value={stats.replies ?? 0}
            icon="💬"
            change={stats.reply_rate != null ? `${stats.reply_rate}% rate` : undefined}
            changeType={stats.reply_rate != null && stats.reply_rate > 5 ? 'positive' : 'neutral'}
          />
          <StatsCard label="Bounces" value={stats.bounces ?? 0} icon="⚠️" />
          <StatsCard label="Clicks" value={stats.clicks ?? 0} icon="🔗" />
        </div>
      )}

      {/* Back link */}
      <Link href="/dashboard/outreach" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
        ← Back to Outreach
      </Link>
    </div>
  );
}
