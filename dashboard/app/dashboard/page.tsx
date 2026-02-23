'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import StatsCard from '@/components/StatsCard';
import { listCampaigns, getCredits } from '@/lib/api';

interface Campaign {
  id: string;
  name: string;
  vertical: string;
  status: string;
  total_leads: number;
  total_emails: number;
  credits_used: number;
  created_at: string;
}

export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [credits, setCredits] = useState({ credits_remaining: 0, credits_monthly: 0, plan: 'starter' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listCampaigns(1).catch(() => ({ campaigns: [], total: 0 })),
      getCredits().catch(() => ({ credits_remaining: 0, credits_monthly: 0, plan: 'starter' })),
    ]).then(([campData, credData]) => {
      setCampaigns(campData.campaigns || []);
      setCredits(credData);
      setLoading(false);
    });
  }, []);

  const totalLeads = campaigns.reduce((sum, c) => sum + c.total_leads, 0);
  const totalEmails = campaigns.reduce((sum, c) => sum + c.total_emails, 0);
  const emailRate = totalLeads > 0 ? Math.round((totalEmails / totalLeads) * 100) : 0;
  const activeCampaigns = campaigns.filter((c) => c.status === 'running').length;

  const statusColor: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-emerald-100 text-emerald-700',
    failed: 'bg-red-100 text-red-700',
  };

  if (loading) {
    return <div className="animate-pulse text-gray-400 py-12 text-center">Loading dashboard...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Overview of your lead generation campaigns</p>
        </div>
        <Link
          href="/dashboard/campaigns/new"
          className="px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          + New Campaign
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatsCard label="Total Leads" value={totalLeads.toLocaleString()} icon="👥" />
        <StatsCard label="Emails Found" value={totalEmails.toLocaleString()} icon="📧" change={`${emailRate}% email rate`} changeType={emailRate > 50 ? 'positive' : 'neutral'} />
        <StatsCard label="Active Campaigns" value={activeCampaigns} icon="🚀" />
        <StatsCard label="Credits Remaining" value={credits.credits_remaining.toLocaleString()} icon="💳" change={`${credits.plan} plan`} />
      </div>

      {/* Recent Campaigns */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Recent Campaigns</h2>
          <Link href="/dashboard/campaigns" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
            View all →
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 font-medium text-gray-500">Campaign</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Vertical</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Leads</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Emails</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Credits</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {campaigns.slice(0, 5).map((c) => (
                <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <Link href={`/dashboard/campaigns/${c.id}`} className="font-medium text-gray-900 hover:text-brand-600">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-gray-600 capitalize">{c.vertical.replace('_', ' ')}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColor[c.status] || statusColor.pending}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{c.total_leads.toLocaleString()}</td>
                  <td className="px-6 py-4 text-gray-600">{c.total_emails.toLocaleString()}</td>
                  <td className="px-6 py-4 text-gray-600">{c.credits_used}</td>
                  <td className="px-6 py-4 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {campaigns.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-400">
                    No campaigns yet.{' '}
                    <Link href="/dashboard/campaigns/new" className="text-brand-600 hover:underline">
                      Create your first campaign
                    </Link>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
