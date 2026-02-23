'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listCampaigns, runCampaign, deleteCampaign } from '@/lib/api';

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
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

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
      load(page);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to run campaign');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete campaign "${name}" and all its leads?`)) return;
    try {
      await deleteCampaign(id);
      load(page);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

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

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 animate-pulse">Loading campaigns...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Name</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Vertical</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Leads</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Emails</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Created</th>
                  <th className="text-right px-6 py-3 font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {campaigns.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <Link href={`/dashboard/campaigns/${c.id}`} className="font-medium text-gray-900 hover:text-brand-600">
                        {c.name}
                      </Link>
                      {c.error_message && (
                        <p className="text-xs text-red-500 mt-0.5 truncate max-w-xs">{c.error_message}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-600 capitalize">{c.vertical.replace('_', ' ')}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColor[c.status] || statusColor.pending}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{c.total_leads.toLocaleString()}</td>
                    <td className="px-6 py-4 text-gray-600">{c.total_emails.toLocaleString()}</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right space-x-2">
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
                    </td>
                  </tr>
                ))}
                {campaigns.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-400">
                      No campaigns yet.{' '}
                      <Link href="/dashboard/campaigns/new" className="text-brand-600 hover:underline">Create one</Link>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {total > 20 && (
          <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200 bg-gray-50">
            <p className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 20)}</p>
            <div className="flex gap-1">
              <button onClick={() => load(page - 1)} disabled={page <= 1} className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40">Prev</button>
              <button onClick={() => load(page + 1)} disabled={page >= Math.ceil(total / 20)} className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
