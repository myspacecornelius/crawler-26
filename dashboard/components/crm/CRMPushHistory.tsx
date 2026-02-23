'use client';

import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import { getCRMStatus } from '@/lib/api';

interface CRMPushRecord {
  provider: string;
  campaign_id: string;
  campaign_name: string;
  pushed_at: string;
  total: number;
  created: number;
  updated: number;
  failed: number;
  crm_ids: string[];
}

interface CRMPushHistoryProps {
  records: CRMPushRecord[];
  hubspotKey: string;
  onSyncAgain: (record: CRMPushRecord) => void;
}

export default function CRMPushHistory({ records, hubspotKey, onSyncAgain }: CRMPushHistoryProps) {
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [statusData, setStatusData] = useState<unknown>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState('');

  const handleCheckStatus = async (record: CRMPushRecord) => {
    if (!record.crm_ids?.length) return;
    setStatusLoading(true);
    setStatusError('');
    setStatusData(null);
    setStatusDialogOpen(true);
    try {
      const result = await getCRMStatus({
        provider: record.provider,
        crm_ids: record.crm_ids,
        api_key: record.provider === 'hubspot' ? hubspotKey : undefined,
      });
      setStatusData(result);
    } catch (err: unknown) {
      setStatusError(err instanceof Error ? err.message : 'Status check failed');
    }
    setStatusLoading(false);
  };

  return (
    <>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Push History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 font-medium text-gray-500">Date</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Campaign</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Provider</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Total</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Created</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Updated</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Failed</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                <th className="text-right px-6 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {records.map((rec, idx) => (
                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-gray-600 whitespace-nowrap">
                    {new Date(rec.pushed_at).toLocaleDateString()}{' '}
                    <span className="text-xs text-gray-400">{new Date(rec.pushed_at).toLocaleTimeString()}</span>
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">{rec.campaign_name}</td>
                  <td className="px-6 py-4 text-gray-600 capitalize">{rec.provider}</td>
                  <td className="px-6 py-4 text-gray-600">{rec.total}</td>
                  <td className="px-6 py-4 text-emerald-600 font-medium">{rec.created}</td>
                  <td className="px-6 py-4 text-blue-600 font-medium">{rec.updated}</td>
                  <td className="px-6 py-4 text-red-600 font-medium">{rec.failed}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${
                      rec.failed === 0
                        ? 'bg-emerald-100 text-emerald-700'
                        : rec.created > 0 || rec.updated > 0
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {rec.failed === 0 ? 'Success' : rec.created > 0 || rec.updated > 0 ? 'Partial' : 'Failed'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {rec.crm_ids?.length > 0 && (
                      <button
                        onClick={() => handleCheckStatus(rec)}
                        className="text-xs font-medium text-brand-600 hover:text-brand-700"
                      >
                        Check Status
                      </button>
                    )}
                    <button
                      onClick={() => onSyncAgain(rec)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-700"
                      title="Sync again"
                    >
                      <RefreshCw className="w-3 h-3" />
                      Sync Again
                    </button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-gray-400">
                    No CRM pushes yet. Configure a provider above and push your first leads.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Dialog — replaces alert() */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>CRM Push Status</DialogTitle>
            <DialogDescription>Detailed status of the pushed records</DialogDescription>
          </DialogHeader>
          {statusLoading ? (
            <div className="py-6 text-center text-gray-400 animate-pulse">Loading status...</div>
          ) : statusError ? (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{statusError}</div>
          ) : statusData ? (
            <pre className="max-h-80 overflow-auto text-xs bg-gray-50 border border-gray-200 rounded-lg p-4 font-mono text-gray-700">
              {JSON.stringify(statusData, null, 2)}
            </pre>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}
