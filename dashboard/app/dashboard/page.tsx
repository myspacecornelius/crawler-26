'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Users, Mail, Rocket, CreditCard } from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import LeadsOverTimeChart from '@/components/charts/LeadsOverTimeChart';
import EmailStatusDonut from '@/components/charts/EmailStatusDonut';
import ActivityFeed from '@/components/ActivityFeed';
import QuickActions from '@/components/QuickActions';
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

/* ── Skeleton components ─────────────────────────────────── */

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden animate-pulse">
      <div className="h-1 bg-gray-200" />
      <div className="p-5 space-y-3">
        <div className="h-3 w-24 bg-gray-200 rounded" />
        <div className="h-7 w-16 bg-gray-200 rounded" />
        <div className="h-3 w-32 bg-gray-200 rounded" />
      </div>
      <div className="h-[30px] bg-gray-100" />
    </div>
  );
}

function SkeletonChart({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-5 animate-pulse ${className}`}>
      <div className="h-4 w-36 bg-gray-200 rounded mb-4" />
      <div className="h-[220px] bg-gray-100 rounded-lg" />
    </div>
  );
}

function SkeletonTable() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden animate-pulse">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="h-4 w-40 bg-gray-200 rounded" />
      </div>
      <div className="divide-y divide-gray-100">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="px-6 py-4 flex gap-6">
            <div className="h-3 w-32 bg-gray-200 rounded" />
            <div className="h-3 w-20 bg-gray-200 rounded" />
            <div className="h-3 w-16 bg-gray-200 rounded" />
            <div className="h-3 w-12 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Mock sparkline generators ───────────────────────────── */

function randomSparkline(len = 14, base = 50, variance = 30): number[] {
  return Array.from({ length: len }, () => base + Math.floor(Math.random() * variance));
}

/* ── Main page ───────────────────────────────────────────── */

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

  /* ── Skeleton loading state ────────────────────────────── */

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2 animate-pulse">
            <div className="h-6 w-48 bg-gray-200 rounded" />
            <div className="h-4 w-72 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <SkeletonChart className="lg:col-span-2" />
          <SkeletonChart />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonTable />
          <SkeletonChart />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-sm text-gray-500 mt-1">Here&apos;s what&apos;s happening with your lead generation</p>
        </div>
        <Link
          href="/dashboard/campaigns/new"
          className="px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          + New Campaign
        </Link>
      </div>

      {/* ── Quick Actions ───────────────────────────────── */}
      <QuickActions />

      {/* ── Stats Grid ──────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          label="Total Leads"
          value={totalLeads}
          icon={<Users className="w-5 h-5" />}
          change={campaigns.length > 0 ? `${campaigns.length} campaigns` : undefined}
          changeType="positive"
          sparklineData={randomSparkline(14, 40, 60)}
        />
        <StatsCard
          label="Emails Found"
          value={totalEmails}
          icon={<Mail className="w-5 h-5" />}
          change={`${emailRate}% email rate`}
          changeType={emailRate > 50 ? 'positive' : 'neutral'}
          sparklineData={randomSparkline(14, 30, 50)}
        />
        <StatsCard
          label="Active Campaigns"
          value={activeCampaigns}
          icon={<Rocket className="w-5 h-5" />}
          changeType="neutral"
        />
        <StatsCard
          label="Credits Remaining"
          value={credits.credits_remaining}
          icon={<CreditCard className="w-5 h-5" />}
          change={`${credits.plan} plan`}
          changeType="neutral"
          sparklineData={randomSparkline(14, 200, 100)}
        />
      </div>

      {/* ── Charts row ──────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <LeadsOverTimeChart />
        </div>
        <EmailStatusDonut />
      </div>

      {/* ── Bottom row: Campaigns + Activity Feed ───────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Campaigns */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Recent Campaigns</h3>
            <Link href="/dashboard/campaigns" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Campaign</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Leads</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {campaigns.slice(0, 5).map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3">
                      <Link href={`/dashboard/campaigns/${c.id}`} className="font-medium text-gray-900 hover:text-brand-600">
                        {c.name}
                      </Link>
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColor[c.status] || statusColor.pending}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-600">{c.total_leads.toLocaleString()}</td>
                    <td className="px-6 py-3 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
                {campaigns.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-gray-400">
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

        {/* Activity Feed */}
        <ActivityFeed />
      </div>
    </div>
  );
}
