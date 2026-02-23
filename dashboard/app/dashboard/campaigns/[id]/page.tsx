'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ChevronDown } from 'lucide-react';
import CampaignStatsPanel from '@/components/campaign/CampaignStatsPanel';
import LeadScoreDistribution from '@/components/campaign/LeadScoreDistribution';
import EmailStatusDonut from '@/components/charts/EmailStatusDonut';
import LeadTable from '@/components/LeadTable';
import { useToast } from '@/components/ui/Toast';
import { getCampaign, runCampaign, getLeadStats, getFreshness, listLeads, getExportUrl } from '@/lib/api';

interface Campaign {
  id: string;
  name: string;
  vertical: string;
  status: string;
  total_leads: number;
  total_emails: number;
  credits_used: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

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

export default function CampaignDetailPage() {
  const { toast } = useToast();
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [leadsTotal, setLeadsTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [freshness, setFreshness] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadLeads = useCallback(async (p: number, f: Record<string, string> = {}) => {
    try {
      const data = await listLeads(id, { page: String(p), per_page: '50', ...f });
      setLeads(data.leads);
      setLeadsTotal(data.total);
      setPage(p);
    } catch { /* ignore */ }
  }, [id]);

  useEffect(() => {
    Promise.all([
      getCampaign(id),
      getLeadStats(id).catch(() => null),
      getFreshness(id).catch(() => null),
    ]).then(([c, s, f]) => {
      setCampaign(c);
      setStats(s);
      setFreshness(f);
      setLoading(false);
    }).catch(() => router.push('/dashboard/campaigns'));

    loadLeads(1);
  }, [id, router, loadLeads]);

  const handleRun = async () => {
    try {
      const updated = await runCampaign(id);
      setCampaign(updated);
    } catch (err: unknown) {
      toast({ title: 'Failed to run campaign', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
  };

  if (loading || !campaign) {
    return <div className="animate-pulse text-gray-400 py-12 text-center">Loading campaign...</div>;
  }

  const statusColor: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-emerald-100 text-emerald-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link href="/dashboard/campaigns" className="text-sm text-gray-400 hover:text-gray-600">Campaigns</Link>
            <span className="text-gray-300">/</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColor[campaign.status]}`}>
              {campaign.status}
            </span>
            <span className="text-sm text-gray-500 capitalize">{campaign.vertical.replace('_', ' ')}</span>
            <span className="text-sm text-gray-400">Created {new Date(campaign.created_at).toLocaleDateString()}</span>
          </div>
          {campaign.error_message && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {campaign.error_message}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {campaign.status === 'pending' && (
            <button onClick={handleRun} className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors">
              Run Campaign
            </button>
          )}
          {campaign.status === 'completed' && campaign.total_leads > 0 && (
            <a
              href={getExportUrl(id)}
              className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
            >
              Export CSV
            </a>
          )}
        </div>
      </div>

      {/* Stats Panel */}
      {stats && <CampaignStatsPanel stats={stats} freshness={freshness} />}

      {/* Charts Row */}
      {stats && leads.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <LeadScoreDistribution leads={leads} />
          <EmailStatusDonut
            data={[
              { name: 'Verified', value: stats.verified_emails, color: '#10b981' },
              { name: 'With Email', value: Math.max(stats.with_email - stats.verified_emails, 0), color: '#f59e0b' },
              { name: 'No Email', value: Math.max(stats.total_leads - stats.with_email, 0), color: '#9ca3af' },
            ]}
          />
        </div>
      )}

      {/* Top Funds */}
      {stats && stats.top_funds.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-8">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Top Funds by Lead Count</h3>
          <div className="flex flex-wrap gap-2">
            {stats.top_funds.map((f) => (
              <span key={f.fund} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-full text-xs font-medium text-gray-700">
                {f.fund}
                <span className="text-gray-400">{f.count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Leads Table */}
      {campaign.total_leads > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Leads</h2>
            <div className="flex gap-2">
              {['HOT', 'WARM', 'COOL'].map((tier) => (
                <a
                  key={tier}
                  href={getExportUrl(id, tier)}
                  className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600 font-medium"
                >
                  Export {tier}
                </a>
              ))}
            </div>
          </div>
          <LeadTable
            leads={leads}
            total={leadsTotal}
            page={page}
            perPage={50}
            onPageChange={(p) => loadLeads(p, filters)}
            onFilterChange={(f) => { setFilters(f); loadLeads(1, f); }}
          />
        </div>
      )}
    </div>
  );
}
