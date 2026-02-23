'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Mail, Send, Users, Eye, MessageSquare, ChevronDown } from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import ProviderCard from '@/components/outreach/ProviderCard';
import OutreachStatsChart from '@/components/outreach/OutreachStatsChart';
import CollapsibleSection from '@/components/ui/CollapsibleSection';
import { useToast } from '@/components/ui/Toast';
import { TableSkeleton } from '@/components/DataTable';
import EmptyState from '@/components/EmptyState';
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
  const { toast } = useToast();

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
      toast({ title: 'Failed to start', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
  };

  const handlePause = async (rec: OutreachRecord) => {
    try {
      await pauseOutreach(rec.provider, rec.provider_campaign_id, useSavedKey ? undefined : apiKey || undefined);
      fetchAllStats(records);
    } catch (err: unknown) {
      toast({ title: 'Failed to pause', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' });
    }
  };

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Outreach</h1>
            <p className="text-sm text-gray-500 mt-1">Launch and monitor email outreach campaigns</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <TableSkeleton columns={8} rows={3} />
        </div>
      </div>
    );
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
                <ProviderCard
                  key={p.id}
                  id={p.id}
                  label={p.label}
                  description={p.desc}
                  selected={provider === p.id}
                  onClick={() => setProvider(p.id)}
                />
              ))}
            </div>
          </div>

          {/* Source Campaign */}
          <div className="mb-5">
            <label htmlFor="source-campaign" className="block text-sm font-medium text-gray-700 mb-2">Source Campaign</label>
            <select
              id="source-campaign"
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
                  aria-label="Minimum Score"
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

      {/* Active Campaigns */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Active Campaigns
            {records.length > 0 && <span className="text-sm font-normal text-gray-400 ml-2">{records.length} campaigns</span>}
          </h2>
          {statsLoading && <span className="text-xs text-gray-400 animate-pulse">Fetching stats...</span>}
        </div>

        {records.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200">
            <EmptyState
              icon={<Mail className="h-12 w-12" />}
              title="No outreach campaigns yet"
              description="Launch one above to get started."
              action={{ label: 'Launch Campaign', onClick: () => setShowForm(true) }}
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {records.map((rec) => {
              const s = statsMap[rec.provider_campaign_id] || {};
              return (
                <Link
                  key={rec.provider_campaign_id}
                  href={`/dashboard/outreach/${rec.provider_campaign_id}?provider=${rec.provider}`}
                  className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-gray-300 transition-all group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors">
                        {rec.name}
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5 capitalize">{rec.provider} &middot; {new Date(rec.launched_at).toLocaleDateString()}</p>
                    </div>
                    <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full flex-shrink-0 ${
                      s.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                      s.status === 'paused' ? 'bg-amber-100 text-amber-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {s.status || 'unknown'}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <Send className="w-3.5 h-3.5 text-gray-400" />
                      </div>
                      <p className="text-sm font-semibold text-gray-900">{s.emails_sent?.toLocaleString() ?? '—'}</p>
                      <p className="text-[10px] text-gray-500">Sent</p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <Eye className="w-3.5 h-3.5 text-blue-400" />
                      </div>
                      <p className="text-sm font-semibold text-gray-900">
                        {s.open_rate != null ? `${s.open_rate}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-500">Open Rate</p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                      </div>
                      <p className="text-sm font-semibold text-gray-900">
                        {s.reply_rate != null ? `${s.reply_rate}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-500">Reply Rate</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {s.total_leads?.toLocaleString() ?? '—'} leads
                    </span>
                    <div className="flex gap-1">
                      {s.status !== 'active' && (
                        <button
                          onClick={(e) => { e.preventDefault(); handleStart(rec); }}
                          className="text-xs font-medium text-emerald-600 hover:text-emerald-700 px-2 py-0.5 rounded hover:bg-emerald-50"
                        >
                          Start
                        </button>
                      )}
                      {s.status === 'active' && (
                        <button
                          onClick={(e) => { e.preventDefault(); handlePause(rec); }}
                          className="text-xs font-medium text-amber-600 hover:text-amber-700 px-2 py-0.5 rounded hover:bg-amber-50"
                        >
                          Pause
                        </button>
                      )}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Performance Chart */}
      {records.length > 0 && (
        <OutreachStatsChart records={records} statsMap={statsMap} />
      )}
    </div>
  );
}
