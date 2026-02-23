'use client';

import { useState } from 'react';
import { CircleDot, Cloud, ChevronDown } from 'lucide-react';
import { getCRMFields } from '@/lib/api';

interface CRMProviderSetupProps {
  hubspotKey: string;
  onHubspotKeyChange: (val: string) => void;
  hubspotConnected: boolean;
  onHubspotConnected: (val: boolean) => void;
  sfInstanceUrl: string;
  onSfInstanceUrlChange: (val: string) => void;
  sfAccessToken: string;
  onSfAccessTokenChange: (val: string) => void;
  sfClientId: string;
  onSfClientIdChange: (val: string) => void;
  sfClientSecret: string;
  onSfClientSecretChange: (val: string) => void;
  sfConnected: boolean;
  onSfConnected: (val: boolean) => void;
}

export default function CRMProviderSetup({
  hubspotKey,
  onHubspotKeyChange,
  hubspotConnected,
  onHubspotConnected,
  sfInstanceUrl,
  onSfInstanceUrlChange,
  sfAccessToken,
  onSfAccessTokenChange,
  sfClientId,
  onSfClientIdChange,
  sfClientSecret,
  onSfClientSecretChange,
  sfConnected,
  onSfConnected,
}: CRMProviderSetupProps) {
  const [hubspotTesting, setHubspotTesting] = useState(false);
  const [hubspotError, setHubspotError] = useState('');
  const [sfTesting, setSfTesting] = useState(false);
  const [sfError, setSfError] = useState('');
  const [showSfAdvanced, setShowSfAdvanced] = useState(false);

  const testHubspot = async () => {
    setHubspotTesting(true);
    setHubspotError('');
    try {
      await getCRMFields('hubspot', true);
      onHubspotConnected(true);
    } catch (err: unknown) {
      setHubspotError(err instanceof Error ? err.message : 'Connection failed');
      onHubspotConnected(false);
    }
    setHubspotTesting(false);
  };

  const testSalesforce = async () => {
    setSfTesting(true);
    setSfError('');
    try {
      await getCRMFields('salesforce', true);
      onSfConnected(true);
    } catch (err: unknown) {
      setSfError(err instanceof Error ? err.message : 'Connection failed');
      onSfConnected(false);
    }
    setSfTesting(false);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* HubSpot Card */}
      <div className="bg-white rounded-xl border border-gray-200 border-l-4 border-l-orange-400 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center">
              <CircleDot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">HubSpot</h3>
              <p className="text-xs text-gray-500">CRM & Marketing Platform</p>
            </div>
          </div>
          {hubspotConnected ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Connected
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
              onChange={(e) => onHubspotKeyChange(e.target.value)}
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
            <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
              <Cloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Salesforce</h3>
              <p className="text-xs text-gray-500">Enterprise CRM</p>
            </div>
          </div>
          {sfConnected ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Connected
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
              onChange={(e) => onSfInstanceUrlChange(e.target.value)}
              placeholder="https://yourorg.my.salesforce.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
            <input
              type="password"
              value={sfAccessToken}
              onChange={(e) => onSfAccessTokenChange(e.target.value)}
              placeholder="00D..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="button"
            onClick={() => setShowSfAdvanced(!showSfAdvanced)}
            className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium"
          >
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showSfAdvanced ? 'rotate-180' : ''}`} />
            {showSfAdvanced ? 'Hide OAuth credentials' : 'OAuth credentials (optional)'}
          </button>

          {showSfAdvanced && (
            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
                <input
                  type="text"
                  value={sfClientId}
                  onChange={(e) => onSfClientIdChange(e.target.value)}
                  placeholder="3MVG9..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client Secret</label>
                <input
                  type="password"
                  value={sfClientSecret}
                  onChange={(e) => onSfClientSecretChange(e.target.value)}
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
  );
}
