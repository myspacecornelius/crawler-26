'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Megaphone, LayoutGrid, List, Users, Mail, Calendar } from 'lucide-react';
import { DataTable } from '@/components/DataTable';
import { useToast } from '@/components/ui/Toast';
import { listCampaigns, runCampaign, deleteCampaign } from '@/lib/api';
import type { Column } from '@/components/DataTable';

interface Campaign {
  id: string;
  name: string;
  vertical: string;
  status: string;
  total_leads: number;
  total_emails: number;
  credits_used: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

const statusColor: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700 animate-pulse',
  completed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
};

export default function CampaignsPage() {
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<string | undefined>();
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [view, setView] = useState<'table' | 'cards'>('table');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const STATUS_TABS = ['all', 'running', 'completed', 'pending', 'failed'] as const;

  const load = async (p = 1) => {
    setLoading(true);
    try {
      const data = await listCampaigns(p);
      setCampaigns(data.campaigns);
      setTotal(data.total);
      setPage(p);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleRun = async (id: string) => {
    try {
      await runCampaign(id);
      toast({ title: 'Campaign started', variant: 'success' });
      load(page);
    } catch (err: unknown) {
      toast({ title: 'Failed to run campaign', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete campaign "${name}" and all its leads?`)) return;
    try {
      await deleteCampaign(id);
      toast({ title: 'Campaign deleted', variant: 'success' });
      load(page);
    } catch (err: unknown) {
      toast({ title: 'Failed to delete', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
  };

  const handleSort = (key: string, direction: 'asc' | 'desc') => {
    setSortKey(key);
    setSortDir(direction);
  };

  const filteredCampaigns = statusFilter === 'all'
    ? campaigns
    : campaigns.filter((c) => c.status === statusFilter);

  const sortedCampaigns = sortKey
    ? [...filteredCampaigns].sort((a, b) => {
        const aVal = (a as unknown as Record<string, unknown>)[sortKey];
        const bVal = (b as unknown as Record<string, unknown>)[sortKey];
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
        }
        const aStr = String(aVal ?? '');
        const bStr = String(bVal ?? '');
        return sortDir === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
      })
    : filteredCampaigns;

  const columns: Column<Campaign>[] = [
    {
      key: 'name',
      label: 'Name',
      sortable: true,
      render: (c) => (
        <div>
          <Link href={`/dashboard/campaigns/${c.id}`} className="font-medium text-gray-900 hover:text-brand-600">
            {c.name}
          </Link>
          {c.error_message && (
            <p className="text-xs text-red-500 mt-0.5 truncate max-w-xs">{c.error_message}</p>
          )}
        </div>
      ),
    },
    {
      key: 'vertical',
      label: 'Vertical',
      sortable: true,
      render: (c) => <span className="text-gray-600 capitalize">{c.vertical.replace('_', ' ')}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (c) => (
        <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColor[c.status] || statusColor.pending}`}>
          {c.status}
        </span>
      ),
    },
    {
      key: 'total_leads',
      label: 'Leads',
      sortable: true,
      render: (c) => <span className="text-gray-600">{c.total_leads.toLocaleString()}</span>,
    },
    {
      key: 'total_emails',
      label: 'Emails',
      sortable: true,
      render: (c) => <span className="text-gray-600">{c.total_emails.toLocaleString()}</span>,
    },
    {
      key: 'created_at',
      label: 'Created',
      sortable: true,
      render: (c) => <span className="text-gray-500">{new Date(c.created_at).toLocaleDateString()}</span>,
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (c) => (
        <div className="text-right space-x-2">
          {c.status === 'pending' && (
            <button onClick={() => handleRun(c.id)} className="text-xs font-medium text-brand-600 hover:text-brand-700">
              Run
            </button>
          )}
          <Link href={`/dashboard/campaigns/${c.id}`} className="text-xs font-medium text-gray-500 hover:text-gray-700">
            View
          </Link>
          {c.status !== 'running' && (
            <button onClick={() => handleDelete(c.id, c.name)} className="text-xs font-medium text-red-500 hover:text-red-700">
              Delete
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="text-sm text-gray-500 mt-1">{total} total campaigns</p>
        </div>
        <Link
          href="/dashboard/campaigns/new"
          className="px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          + New Campaign
        </Link>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${
                statusFilter === tab
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
              {tab !== 'all' && (
                <span className="ml-1 text-gray-400">
                  {campaigns.filter((c) => c.status === tab).length}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
          <button
            onClick={() => setView('table')}
            className={`p-1.5 rounded-md transition-colors ${view === 'table' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
            title="Table view"
          >
            <List className="w-4 h-4" />
          </button>
          <button
            onClick={() => setView('cards')}
            className={`p-1.5 rounded-md transition-colors ${view === 'cards' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
            title="Card view"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Card View */}
      {view === 'cards' ? (
        sortedCampaigns.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <Megaphone className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-base font-semibold text-gray-900 mb-1">No campaigns found</h3>
            <p className="text-sm text-gray-500 mb-4">Try a different filter or create a new campaign.</p>
            <Link
              href="/dashboard/campaigns/new"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors"
            >
              Create Campaign
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedCampaigns.map((c) => (
              <Link
                key={c.id}
                href={`/dashboard/campaigns/${c.id}`}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-gray-300 transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors truncate pr-2">
                    {c.name}
                  </h3>
                  <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full flex-shrink-0 ${statusColor[c.status] || statusColor.pending}`}>
                    {c.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 capitalize mb-4">{c.vertical.replace('_', ' ')}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5" />
                    {c.total_leads.toLocaleString()} leads
                  </span>
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5" />
                    {c.total_emails.toLocaleString()} emails
                  </span>
                </div>
                {/* Mini progress bar */}
                <div className="mt-3">
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-brand-500 rounded-full transition-all campaign-progress-fill"
                      style={{ '--progress-width': `${c.total_leads > 0 ? Math.min((c.total_emails / c.total_leads) * 100, 100) : 0}%` } as React.CSSProperties}
                    />
                  </div>
                  <div className="flex items-center justify-between mt-1.5">
                    <span className="text-[10px] text-gray-400">{c.total_leads > 0 ? Math.round((c.total_emails / c.total_leads) * 100) : 0}% email rate</span>
                    <span className="flex items-center gap-1 text-[10px] text-gray-400">
                      <Calendar className="w-3 h-3" />
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                {c.error_message && (
                  <p className="text-xs text-red-500 mt-2 truncate">{c.error_message}</p>
                )}
              </Link>
            ))}
          </div>
        )
      ) : (

      <DataTable<Campaign>
        columns={columns}
        data={sortedCampaigns}
        total={total}
        page={page}
        perPage={20}
        loading={loading}
        onPageChange={(p) => load(p)}
        onSort={handleSort}
        sortKey={sortKey}
        sortDirection={sortDir}
        rowKey={(c) => c.id}
        emptyMessage="No campaigns yet"
        emptyDescription="Create your first campaign to start discovering leads."
        emptyIcon={<Megaphone className="h-12 w-12" />}
        emptyAction={{ label: 'Create Campaign', href: '/dashboard/campaigns/new' }}
      />

      )}
    </div>
  );
}
