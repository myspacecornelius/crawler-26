'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  listCampaigns,
  pushToCRM,
  getCRMStatus,
  getCRMFields,
  getDefaultFieldMapping,
} from '@/lib/api';

interface Campaign {
  id: string;
  name: string;
  vertical: string;
  status: string;
  total_leads: number;
}

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

const PUSH_STORAGE_KEY = 'leadfactory_crm_push_records';
const TIERS = ['HOT', 'WARM', 'COOL'] as const;

function loadPushRecords(): CRMPushRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(PUSH_STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function savePushRecords(records: CRMPushRecord[]) {
  localStorage.setItem(PUSH_STORAGE_KEY, JSON.stringify(records));
}

function getStoredCred(key: string): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem(key) || '';
}

function setStoredCred(key: string, value: string) {
  if (value) {
    localStorage.setItem(key, value);
  } else {
    localStorage.removeItem(key);
  }
}

export default function CRMPage() {
  // Provider credentials
  const [hubspotKey, setHubspotKey] = useState('');
  const [sfInstanceUrl, setSfInstanceUrl] = useState('');
  const [sfClientId, setSfClientId] = useState('');
  const [sfClientSecret, setSfClientSecret] = useState('');
  const [sfAccessToken, setSfAccessToken] = useState('');
  const [showSfAdvanced, setShowSfAdvanced] = useState(false);

  // Connection status
  const [hubspotConnected, setHubspotConnected] = useState(false);
  const [sfConnected, setSfConnected] = useState(false);
  const [hubspotTesting, setHubspotTesting] = useState(false);
  const [sfTesting, setSfTesting] = useState(false);
  const [hubspotError, setHubspotError] = useState('');
  const [sfError, setSfError] = useState('');

  // Push form
  const [selectedProvider, setSelectedProvider] = useState<'hubspot' | 'salesforce'>('hubspot');
  const [campaignId, setCampaignId] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [selectedTiers, setSelectedTiers] = useState<string[]>(['HOT', 'WARM']);
  const [testMode, setTestMode] = useState(false);
  const [showFieldMapping, setShowFieldMapping] = useState(false);
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});
  const [defaultMapping, setDefaultMapping] = useState<Record<string, string>>({});
  const [crmFields, setCrmFields] = useState<string[]>([]);
  const [customFields, setCustomFields] = useState<{ key: string; value: string }[]>([]);
  const [pushing, setPushing] = useState(false);
  const [pushError, setPushError] = useState('');
  const [pushResult, setPushResult] = useState<{ created: number; updated: number; failed: number } | null>(null);

  // Data
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [pushRecords, setPushRecords] = useState<CRMPushRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    setHubspotKey(getStoredCred('crm_hubspot_api_key'));
    setSfInstanceUrl(getStoredCred('crm_sf_instance_url'));
    setSfClientId(getStoredCred('crm_sf_client_id'));
    setSfClientSecret(getStoredCred('crm_sf_client_secret'));
    setSfAccessToken(getStoredCred('crm_sf_access_token'));
    setPushRecords(loadPushRecords());

    listCampaigns(1)
      .then((data) => setCampaigns(data.campaigns || []))
      .catch(() => setCampaigns([]))
      .finally(() => setLoading(false));
  }, []);

  // Load field mapping defaults + CRM fields when provider changes
  const loadFieldConfig = useCallback(async (provider: string) => {
    try {
      const [defaults, fields] = await Promise.all([
        getDefaultFieldMapping().catch(() => ({})),
        getCRMFields(provider, true).catch(() => ({ fields: [] })),
      ]);
      setDefaultMapping(defaults.mapping || defaults || {});
      setFieldMapping(defaults.mapping || defaults || {});
      const fieldList = Array.isArray(fields) ? fields : (fields.fields || []);
      setCrmFields(fieldList.map((f: string | { name: string }) => typeof f === 'string' ? f : f.name));
    } catch {
      setDefaultMapping({});
      setFieldMapping({});
      setCrmFields([]);
    }
  }, []);

  useEffect(() => {
    loadFieldConfig(selectedProvider);
  }, [selectedProvider, loadFieldConfig]);

  // Save credentials to localStorage on change
  const saveHubspotKey = (val: string) => {
    setHubspotKey(val);
    setStoredCred('crm_hubspot_api_key', val);
    setHubspotConnected(false);
  };

  const saveSfField = (key: string, val: string, setter: (v: string) => void) => {
    setter(val);
    setStoredCred(key, val);
    setSfConnected(false);
  };

  // Test connections
  const testHubspot = async () => {
    setHubspotTesting(true);
    setHubspotError('');
    try {
      await getCRMFields('hubspot', true);
      setHubspotConnected(true);
    } catch (err: unknown) {
      setHubspotError(err instanceof Error ? err.message : 'Connection failed');
      setHubspotConnected(false);
    }
    setHubspotTesting(false);
  };

  const testSalesforce = async () => {
    setSfTesting(true);
    setSfError('');
    try {
      await getCRMFields('salesforce', true);
      setSfConnected(true);
    } catch (err: unknown) {
      setSfError(err instanceof Error ? err.message : 'Connection failed');
      setSfConnected(false);
    }
    setSfTesting(false);
  };

  const handleTierToggle = (tier: string) => {
    setSelectedTiers((prev) =>
      prev.includes(tier) ? prev.filter((t) => t !== tier) : [...prev, tier]
    );
  };

  const addCustomField = () => {
    setCustomFields([...customFields, { key: '', value: '' }]);
  };

  const updateCustomField = (idx: number, field: 'key' | 'value', val: string) => {
    const updated = [...customFields];
    updated[idx][field] = val;
    setCustomFields(updated);
  };

  const removeCustomField = (idx: number) => {
    setCustomFields(customFields.filter((_, i) => i !== idx));
  };

  const handlePush = async () => {
    setPushError('');
    setPushResult(null);
    if (!campaignId) { setPushError('Select a source campaign'); return; }

    setPushing(true);
    try {
      const customFieldsObj: Record<string, string> = {};
      customFields.forEach((cf) => { if (cf.key) customFieldsObj[cf.key] = cf.value; });

      const payload: Parameters<typeof pushToCRM>[0] = {
        provider: selectedProvider,
        campaign_id: campaignId,
        test_mode: testMode,
        min_score: minScore > 0 ? minScore : undefined,
        tiers: selectedTiers.length > 0 ? selectedTiers : undefined,
        field_mapping: Object.keys(fieldMapping).length > 0 ? fieldMapping : undefined,
        custom_fields: Object.keys(customFieldsObj).length > 0 ? customFieldsObj : undefined,
      };

      if (selectedProvider === 'hubspot' && hubspotKey) {
        payload.api_key = hubspotKey;
      } else if (selectedProvider === 'salesforce') {
        if (sfAccessToken) payload.sf_access_token = sfAccessToken;
        if (sfInstanceUrl) payload.sf_instance_url = sfInstanceUrl;
        if (sfClientId) payload.sf_client_id = sfClientId;
        if (sfClientSecret) payload.sf_client_secret = sfClientSecret;
      }

      const result = await pushToCRM(payload);

      const campaign = campaigns.find((c) => c.id === campaignId);
      const record: CRMPushRecord = {
        provider: selectedProvider,
        campaign_id: campaignId,
        campaign_name: campaign?.name || campaignId,
        pushed_at: new Date().toISOString(),
        total: (result.created || 0) + (result.updated || 0) + (result.failed || 0),
        created: result.created || 0,
        updated: result.updated || 0,
        failed: result.failed || 0,
        crm_ids: result.crm_ids || [],
      };

      const updated = [record, ...pushRecords];
      savePushRecords(updated);
      setPushRecords(updated);
      setPushResult({ created: record.created, updated: record.updated, failed: record.failed });
    } catch (err: unknown) {
      setPushError(err instanceof Error ? err.message : 'Push failed');
    }
    setPushing(false);
  };

  const handleCheckStatus = async (record: CRMPushRecord) => {
    if (!record.crm_ids?.length) return;
    try {
      const result = await getCRMStatus({
        provider: record.provider,
        crm_ids: record.crm_ids,
        api_key: record.provider === 'hubspot' ? hubspotKey : undefined,
      });
      alert(JSON.stringify(result, null, 2));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Status check failed');
    }
  };

  if (loading) {
    return <div className="animate-pulse text-gray-400 py-12 text-center">Loading CRM...</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">CRM Integration</h1>
        <p className="text-sm text-gray-500 mt-1">Push leads to HubSpot or Salesforce</p>
      </div>

      {/* Section 1: Provider Setup */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* HubSpot Card */}
        <div className="bg-white rounded-xl border border-gray-200 border-l-4 border-l-orange-400 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🟠</span>
              <div>
                <h3 className="font-semibold text-gray-900">HubSpot</h3>
                <p className="text-xs text-gray-500">CRM & Marketing Platform</p>
              </div>
            </div>
            {hubspotConnected ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700">
                Connected ✓
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-500">
                Not connected
              </span>
            )}
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key (Private App Token)</label>
              <input
                type="password"
                value={hubspotKey}
                onChange={(e) => saveHubspotKey(e.target.value)}
                placeholder="pat-na1-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
            {hubspotError && (
              <div className="p-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">{hubspotError}</div>
            )}
            <button
              onClick={testHubspot}
              disabled={!hubspotKey || hubspotTesting}
              className="w-full px-3 py-2 text-sm font-medium rounded-lg border border-orange-300 text-orange-700 hover:bg-orange-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {hubspotTesting ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>

        {/* Salesforce Card */}
        <div className="bg-white rounded-xl border border-gray-200 border-l-4 border-l-blue-400 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔵</span>
              <div>
                <h3 className="font-semibold text-gray-900">Salesforce</h3>
                <p className="text-xs text-gray-500">Enterprise CRM</p>
              </div>
            </div>
            {sfConnected ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700">
                Connected ✓
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-500">
                Not connected
              </span>
            )}
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Instance URL</label>
              <input
                type="text"
                value={sfInstanceUrl}
                onChange={(e) => saveSfField('crm_sf_instance_url', e.target.value, setSfInstanceUrl)}
                placeholder="https://yourorg.my.salesforce.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
              <input
                type="password"
                value={sfAccessToken}
                onChange={(e) => saveSfField('crm_sf_access_token', e.target.value, setSfAccessToken)}
                placeholder="00D..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <button
              onClick={() => setShowSfAdvanced(!showSfAdvanced)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              {showSfAdvanced ? '▲ Hide OAuth credentials' : '▼ OAuth credentials (optional)'}
            </button>

            {showSfAdvanced && (
              <div className="space-y-3 pt-1">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
                  <input
                    type="text"
                    value={sfClientId}
                    onChange={(e) => saveSfField('crm_sf_client_id', e.target.value, setSfClientId)}
                    placeholder="3MVG9..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Secret</label>
                  <input
                    type="password"
                    value={sfClientSecret}
                    onChange={(e) => saveSfField('crm_sf_client_secret', e.target.value, setSfClientSecret)}
                    placeholder="Client secret..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {sfError && (
              <div className="p-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">{sfError}</div>
            )}
            <button
              onClick={testSalesforce}
              disabled={(!sfAccessToken && !sfClientId) || sfTesting}
              className="w-full px-3 py-2 text-sm font-medium rounded-lg border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sfTesting ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>
      </div>

      {/* Security Note */}
      <div className="mb-8 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
        ⚠️ Credentials are stored in your browser only. For production use, configure via environment variables on the server.
      </div>

      {/* Section 2: Push Leads */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-5">Push Leads to CRM</h2>

        {/* Provider Toggle */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
          <div className="flex gap-3">
            <button
              onClick={() => setSelectedProvider('hubspot')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                selectedProvider === 'hubspot'
                  ? 'bg-orange-100 text-orange-700 ring-1 ring-orange-300'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              🟠 HubSpot
            </button>
            <button
              onClick={() => setSelectedProvider('salesforce')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                selectedProvider === 'salesforce'
                  ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-300'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              🔵 Salesforce
            </button>
          </div>
        </div>

        {/* Source Campaign */}
        <div className="mb-5">
          <label htmlFor="crm-campaign" className="block text-sm font-medium text-gray-700 mb-2">Source Campaign</label>
          <select
            id="crm-campaign"
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
                {TIERS.map((tier) => (
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

        {/* Field Mapping */}
        <div className="mb-5">
          <button
            onClick={() => setShowFieldMapping(!showFieldMapping)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
          >
            <span>{showFieldMapping ? '▼' : '▶'}</span>
            Field Mapping
            <span className="text-xs text-gray-400 font-normal">({Object.keys(fieldMapping).length} fields)</span>
          </button>

          {showFieldMapping && (
            <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-4 py-2 font-medium text-gray-500 text-xs">LeadFactory Field</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500 text-xs">CRM Field</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {Object.entries(fieldMapping).map(([lfField, crmField]) => (
                    <tr key={lfField} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono text-xs text-gray-700">{lfField}</td>
                      <td className="px-4 py-2">
                        {crmFields.length > 0 ? (
                          <select
                            value={crmField}
                            onChange={(e) => setFieldMapping({ ...fieldMapping, [lfField]: e.target.value })}
                            aria-label={`CRM field mapping for ${lfField}`}
                            className="w-full px-2 py-1 border border-gray-200 rounded text-xs font-mono bg-white focus:ring-1 focus:ring-brand-500"
                          >
                            <option value="">— unmapped —</option>
                            {crmFields.map((f) => (
                              <option key={f} value={f}>{f}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            value={crmField}
                            onChange={(e) => setFieldMapping({ ...fieldMapping, [lfField]: e.target.value })}
                            placeholder="CRM field name"
                            aria-label={`CRM field mapping for ${lfField}`}
                            className="w-full px-2 py-1 border border-gray-200 rounded text-xs font-mono focus:ring-1 focus:ring-brand-500"
                          />
                        )}
                      </td>
                    </tr>
                  ))}
                  {Object.keys(fieldMapping).length === 0 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-4 text-center text-xs text-gray-400">
                        No field mapping loaded. Connect a provider and defaults will appear.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
              {Object.keys(defaultMapping).length > 0 && (
                <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
                  <button
                    onClick={() => setFieldMapping({ ...defaultMapping })}
                    className="text-xs text-brand-600 hover:text-brand-700 font-medium"
                  >
                    Reset to defaults
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Custom Fields */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">Custom Fields</label>
          {customFields.map((cf, idx) => (
            <div key={idx} className="flex gap-2 mb-2">
              <input
                type="text"
                value={cf.key}
                onChange={(e) => updateCustomField(idx, 'key', e.target.value)}
                placeholder="Field name"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
              <input
                type="text"
                value={cf.value}
                onChange={(e) => updateCustomField(idx, 'value', e.target.value)}
                placeholder="Value"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
              <button
                onClick={() => removeCustomField(idx)}
                className="px-3 py-2 text-sm text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
          ))}
          <button
            onClick={addCustomField}
            className="text-sm text-brand-600 hover:text-brand-700 font-medium"
          >
            + Add field
          </button>
        </div>

        {/* Test Mode Toggle */}
        <div className="mb-5">
          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative">
              <input
                type="checkbox"
                checked={testMode}
                onChange={(e) => setTestMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-brand-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-600"></div>
            </div>
            <span className="text-sm font-medium text-gray-700">Test Mode</span>
            {testMode && (
              <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700">
                Test mode — validates mapping without pushing
              </span>
            )}
          </label>
        </div>

        {/* Error / Success */}
        {pushError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {pushError}
          </div>
        )}
        {pushResult && (
          <div className={`mb-4 p-4 rounded-lg border text-sm ${
            pushResult.failed === 0
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : pushResult.created > 0 || pushResult.updated > 0
              ? 'bg-amber-50 border-amber-200 text-amber-700'
              : 'bg-red-50 border-red-200 text-red-600'
          }`}>
            <div className="font-medium mb-1">
              {pushResult.failed === 0 ? 'Push Successful' : pushResult.created > 0 || pushResult.updated > 0 ? 'Push Completed with Errors' : 'Push Failed'}
            </div>
            <div className="flex gap-6 text-xs">
              <span><strong>{pushResult.created}</strong> created</span>
              <span><strong>{pushResult.updated}</strong> updated</span>
              <span><strong>{pushResult.failed}</strong> failed</span>
            </div>
          </div>
        )}

        {/* Push Button */}
        <button
          onClick={handlePush}
          disabled={pushing || !campaignId}
          className="w-full px-4 py-3 bg-brand-600 text-white text-sm font-semibold rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pushing ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              Pushing leads...
            </span>
          ) : testMode ? 'Validate Mapping (Test Mode)' : 'Push to CRM'}
        </button>
      </div>

      {/* Section 3: Push History */}
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
              {pushRecords.map((rec, idx) => (
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
                  <td className="px-6 py-4 text-right">
                    {rec.crm_ids?.length > 0 && (
                      <button
                        onClick={() => handleCheckStatus(rec)}
                        className="text-xs font-medium text-brand-600 hover:text-brand-700"
                      >
                        Check Status
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {pushRecords.length === 0 && (
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
    </div>
  );
}
