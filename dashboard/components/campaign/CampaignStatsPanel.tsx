'use client';

import StatsCard from '@/components/StatsCard';
import { Users, Mail, ShieldCheck, Flame, BarChart3, RefreshCw } from 'lucide-react';

interface Stats {
  total_leads: number;
  with_email: number;
  email_rate: number;
  verified_emails: number;
  hot_leads: number;
  warm_leads: number;
  cool_leads: number;
  avg_score: number;
  top_funds: { fund: string; count: number }[];
}

interface Freshness {
  freshness_pct?: number;
  verified_last_7d?: number;
}

interface CampaignStatsPanelProps {
  stats: Stats;
  freshness?: Freshness | null;
}

export default function CampaignStatsPanel({ stats, freshness }: CampaignStatsPanelProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <StatsCard
        label="Total Leads"
        value={stats.total_leads}
        icon={<Users className="w-5 h-5" />}
      />
      <StatsCard
        label="With Email"
        value={stats.with_email}
        icon={<Mail className="w-5 h-5" />}
        change={`${stats.email_rate}% rate`}
        changeType={stats.email_rate > 50 ? 'positive' : 'neutral'}
      />
      <StatsCard
        label="Verified"
        value={stats.verified_emails}
        icon={<ShieldCheck className="w-5 h-5" />}
        change={`${stats.total_leads > 0 ? Math.round(stats.verified_emails / stats.total_leads * 100) : 0}% rate`}
        changeType={stats.verified_emails > 0 ? 'positive' : 'neutral'}
      />
      <StatsCard
        label="Avg Score"
        value={stats.avg_score}
        icon={<BarChart3 className="w-5 h-5" />}
      />
      <StatsCard
        label="HOT Leads"
        value={stats.hot_leads}
        icon={<Flame className="w-5 h-5" />}
        changeType="positive"
      />
      {freshness && (
        <StatsCard
          label="Data Freshness"
          value={`${freshness?.freshness_pct ?? 0}%`}
          icon={<RefreshCw className="w-5 h-5" />}
          change={`${freshness?.verified_last_7d ?? 0} verified this week`}
          changeType={(freshness?.freshness_pct ?? 0) > 70 ? 'positive' : 'neutral'}
        />
      )}
    </div>
  );
}
