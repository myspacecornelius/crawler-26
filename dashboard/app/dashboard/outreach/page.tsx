'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import StatsCard from '@/components/StatsCard';
import {
  listCampaigns,
  launchOutreach,
  startOutreach,
  pauseOutreach,
  getOutreachStats,
  listOutreachTemplates,
} from '@/lib/api';

interface OutreachRecord {
  provider: string;
  provider_campaign_id: string;
  name: string;
  source_campaign_id: string;
  launched_at: string;
}

interface Campaign {
  id: string;
  name: string;
  vertical: string;
  status: string;
  total_leads: number;
}

interface TemplateStep {
  step: number;
  subject: string;
  body: string;
  delay_days?: number;
}

interface Template {
  name: string;
  vertical: string;
  steps: TemplateStep[];
}

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

const STORAGE_KEY = 'leadfactory_outreach_records';

function loadRecords(): OutreachRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveRecords(records: OutreachRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

const providers = [
  { id: 'instantly', label: 'Instantly', desc: 'High-volume cold email with auto-warmup' },
  { id: 'smartlead', label: 'SmartLead', desc: 'Multi-inbox rotation & AI sequences' },
];

const tiers = ['HOT', 'WARM', 'COOL'] as const;

export default function OutreachPage() {
  // Launch form state
  const [showForm, setShowForm] = useState(false);
  const [provider, setProvider] = useState('instantly');
  const [campaignId, setCampaignId] = useState('');
  const [campaignName, setCampaignName] = useState('');
  const [fromEmail, setFromEmail] = useState('');
  const [fromName, setFromName] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [selectedTiers, setSelectedTiers] = useState<string[]>(['HOT', 'WARM']);
  const [apiKey, setApiKey] = useState('');
  const [useSavedKey, setUseSavedKey] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState('');
  const [launchSuccess, setLaunchSuccess] = useState('');

  // Data
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [expandedTemplate, setExpandedTemplate] = useState<string | null>(null);
  const [records, setRecords] = useState<OutreachRecord[]>([]);
  const [statsMap, setStatsMap] = useState<Record<string, OutreachStatsData>>({});
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(false);

  // Load source campaigns and templates
  useEffect(() => {
    Promise.all([
      listCampaigns(1).catch(() => ({ campaigns: [], total: 0 })),
      listOutreachTemplates().catch(() => []),
    ]).then(([campData, tmpl]) => {
      setCampaigns(campData.campaigns || []);
      setTemplates(Array.isArray(tmpl) ? tmpl : []);
      const recs = loadRecords();
      setRecords(recs);
      if (recs.length === 0) setShowForm(true);
      setLoading(false);
    });
  }, []);

  // Fetch stats for all stored outreach records
  const fetchAllStats = useCallback(async (recs: OutreachRecord[]) => {
    if (recs.length === 0) return;
    setStatsLoading(true);
    const map: Record<string, OutreachStatsData> = {};
    await Promise.all(
      recs.map(async (r) => {
        try {
          const s = await getOutreachStats(r.provider, r.provider_campaign_id);
          map[r.provider_campaign_id] = s;
        } catch {
          map[r.provider_campaign_id] = {};
        }
      })
    );
    setStatsMap(map);
    setStatsLoading(false);
  }, []);

  useEffect(() => {
    if (!loading && records.length > 0) {
      fetchAllStats(records);
    }
  }, [loading, records, fetchAllStats]);

  const handleTierToggle = (tier: string) => {
    setSelectedTiers((prev) =>
      prev.includes(tier) ? prev.filter((t) => t !== tier) : [...prev, tier]
    );
  };

  const handleLaunch = async () => {
    setLaunchError('');
    setLaunchSuccess('');
    if (!campaignId) { setLaunchError('Select a source campaign'); return; }
    if (!campaignName.trim()) { setLaunchError('Enter a campaign name'); return; }
    if (!apiKey && !useSavedKey) { setLaunchError('Provide a provider API key or use a saved key'); return; }

    setLaunching(true);
    try {
      const result = await launchOutreach({
        name: campaignName,
        provider,
        campaign_id: campaignId,
        from_email: fromEmail || undefined,
        from_name: fromName || undefined,
        min_score: minScore > 0 ? minScore : undefined,
        tiers: selectedTiers.length > 0 ? selectedTiers : undefined,
        api_key: useSavedKey ? undefined : apiKey,
      });

      const newRecord: OutreachRecord = {
        provider,
        provider_campaign_id: result.provider_campaign_id || result.id || campaignName,
        name: campaignName,
        source_campaign_id: campaignId,
        launched_at: new Date().toISOString(),
      };
      const updated = [newRecord, ...records];
      saveRecords(updated);
      setRecords(updated);

      setLaunchSuccess(`Campaign launched! Provider ID: ${newRecord.provider_campaign_id}`);
      setCampaignName('');
      setFromEmail('');
      setFromName('');
      setApiKey('');
      setMinScore(0);
      setSelectedTiers(['HOT', 'WARM']);

      fetchAllStats(updated);
    } catch (err: unknown) {
      setLaunchError(err instanceof Error ? err.message : 'Failed to launch campaign');
    }
    setLaunching(false);
  };

  const handleStart = async (rec: OutreachRecord) => {
    try {
      await startOutreach(rec.provider, rec.provider_campaign_id, useSavedKey ? undefined : apiKey || undefined);
      fetchAllStats(records);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to start');
    }
  };

  const handlePause = async (rec: OutreachRecord) => {
    try {
      await pauseOutreach(rec.provider, rec.provider_campaign_id, useSavedKey ? undefined : apiKey || undefined);
      fetchAllStats(records);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to pause');
    }
  };

  if (loading) {
    return <div className="animate-pulse text-gray-400 py-12 text-center">Loading outreach...</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Outreach</h1>
          <p className="text-sm text-gray-500 mt-1">Launch and monitor email outreach campaigns</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          {showForm ? 'Hide Form' : '+ Launch Campaign'}
        </button>
      </div>

      {/* Launch Form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-5">Launch Outreach Campaign</h2>

          {/* Provider Selector */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
            <div className="grid grid-cols-2 gap-3">
              {providers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    provider === p.id
                      ? 'border-brand-500 bg-brand-50 ring-1 ring-brand-500'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{p.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Source Campaign */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">Source Campaign</label>
            <select
              value={campaignId}
              onChange={(e) => setCampaignId(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white"
            >
              <option value="">Select a campaign...</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.total_leads} leads ({c.status})
                </option>
              ))}
            </select>
          </div>

          {/* Campaign Name */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">Campaign Name</label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="e.g. VC Outreach — March 2026"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          {/* From Email & Name */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">From Email</label>
              <input
                type="email"
                value={fromEmail}
                onChange={(e) => setFromEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">From Name</label>
              <input
                type="text"
                value={fromName}
                onChange={(e) => setFromName(e.target.value)}
                placeholder="Your Name"
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
          </div>

          {/* Targeting */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">Targeting</label>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600">Minimum Score</span>
                  <span className="text-sm font-medium text-gray-900">{minScore}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-full accent-brand-600"
                />
              </div>
              <div>
                <span className="text-sm text-gray-600 block mb-2">Tiers</span>
                <div className="flex gap-2">
                  {tiers.map((tier) => (
                    <button
                      key={tier}
                      onClick={() => handleTierToggle(tier)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                        selectedTiers.includes(tier)
                          ? tier === 'HOT'
                            ? 'bg-red-100 text-red-700 ring-1 ring-red-300'
                            : tier === 'WARM'
                            ? 'bg-amber-100 text-amber-700 ring-1 ring-amber-300'
                            : 'bg-blue-100 text-blue-700 ring-1 ring-blue-300'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {tier}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* API Key */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">Provider API Key</label>
            <div className="flex items-center gap-3 mb-2">
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useSavedKey}
                  onChange={(e) => setUseSavedKey(e.target.checked)}
                  className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                Use saved key from settings
              </label>
            </div>
            {!useSavedKey && (
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste your API key..."
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            )}
          </div>

          {/* Template Preview */}
          {templates.length > 0 && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Email Sequence Templates</label>
              <div className="space-y-2">
                {templates.map((t) => (
                  <div key={t.name} className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setExpandedTemplate(expandedTemplate === t.name ? null : t.name)}
                      className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 transition-colors"
                    >
                      <span>{t.name} <span className="text-gray-400 font-normal">({t.steps.length} steps)</span></span>
                      <span className="text-gray-400">{expandedTemplate === t.name ? '▲' : '▼'}</span>
                    </button>
                    {expandedTemplate === t.name && (
                      <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 space-y-3">
                        {t.steps.map((step) => (
                          <div key={step.step} className="text-sm">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-brand-100 text-brand-700 text-xs font-bold">
                                {step.step}
                              </span>
                              <span className="font-medium text-gray-900">{step.subject}</span>
                              {step.delay_days != null && step.delay_days > 0 && (
                                <span className="text-xs text-gray-400">+{step.delay_days}d</span>
                              )}
                            </div>
                            <p className="text-gray-500 text-xs ml-7 line-clamp-2">{step.body}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error / Success */}
          {launchError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {launchError}
            </div>
          )}
          {launchSuccess && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700">
              {launchSuccess}
            </div>
          )}

          {/* Launch Button */}
          <button
            onClick={handleLaunch}
            disabled={launching}
            className="w-full px-4 py-3 bg-brand-600 text-white text-sm font-semibold rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {launching ? 'Launching...' : 'Launch Outreach Campaign'}
          </button>
        </div>
      )}

      {/* Active Campaigns Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Active Campaigns</h2>
          {statsLoading && <span className="text-xs text-gray-400 animate-pulse">Fetching stats...</span>}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Provider</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Leads</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Sent</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Opens</th>
                <th className="text-left px-6 py-3 font-medium text-gray-500">Replies</th>
                <th className="text-right px-6 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {records.map((rec) => {
                const s = statsMap[rec.provider_campaign_id] || {};
                return (
                  <tr key={rec.provider_campaign_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <Link
                        href={`/dashboard/outreach/${rec.provider_campaign_id}?provider=${rec.provider}`}
                        className="font-medium text-gray-900 hover:text-brand-600"
                      >
                        {rec.name}
                      </Link>
                      <p className="text-xs text-gray-400 mt-0.5">{new Date(rec.launched_at).toLocaleDateString()}</p>
                    </td>
                    <td className="px-6 py-4 text-gray-600 capitalize">{rec.provider}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${
                        s.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                        s.status === 'paused' ? 'bg-amber-100 text-amber-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {s.status || 'unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{s.total_leads?.toLocaleString() ?? '—'}</td>
                    <td className="px-6 py-4 text-gray-600">{s.emails_sent?.toLocaleString() ?? '—'}</td>
                    <td className="px-6 py-4 text-gray-600">
                      {s.opens != null ? s.opens.toLocaleString() : '—'}
                      {s.open_rate != null && <span className="text-xs text-gray-400 ml-1">({s.open_rate}%)</span>}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {s.replies != null ? s.replies.toLocaleString() : '—'}
                      {s.reply_rate != null && <span className="text-xs text-gray-400 ml-1">({s.reply_rate}%)</span>}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {s.status !== 'active' && (
                        <button onClick={() => handleStart(rec)} className="text-xs font-medium text-emerald-600 hover:text-emerald-700">
                          Start
                        </button>
                      )}
                      {s.status === 'active' && (
                        <button onClick={() => handlePause(rec)} className="text-xs font-medium text-amber-600 hover:text-amber-700">
                          Pause
                        </button>
                      )}
                      <Link
                        href={`/dashboard/outreach/${rec.provider_campaign_id}?provider=${rec.provider}`}
                        className="text-xs font-medium text-gray-500 hover:text-gray-700"
                      >
                        Stats
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {records.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-400">
                    No outreach campaigns yet. Launch one above to get started.
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
