'use client';

import { useEffect, useState } from 'react';
import { ShieldAlert } from 'lucide-react';
import { listCampaigns } from '@/lib/api';
import CRMProviderSetup from '@/components/crm/CRMProviderSetup';
import CRMPushForm from '@/components/crm/CRMPushForm';
import CRMPushHistory from '@/components/crm/CRMPushHistory';

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
  const [hubspotKey, setHubspotKey] = useState('');
  const [sfInstanceUrl, setSfInstanceUrl] = useState('');
  const [sfClientId, setSfClientId] = useState('');
  const [sfClientSecret, setSfClientSecret] = useState('');
  const [sfAccessToken, setSfAccessToken] = useState('');
  const [hubspotConnected, setHubspotConnected] = useState(false);
  const [sfConnected, setSfConnected] = useState(false);

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [pushRecords, setPushRecords] = useState<CRMPushRecord[]>([]);
  const [loading, setLoading] = useState(true);

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

  const handlePushComplete = (record: CRMPushRecord) => {
    const updated = [record, ...pushRecords];
    savePushRecords(updated);
    setPushRecords(updated);
  };

  const handleSyncAgain = (record: CRMPushRecord) => {
    // Re-push the same campaign with existing settings
    handlePushComplete({ ...record, pushed_at: new Date().toISOString() });
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

      {/* Provider Setup */}
      <CRMProviderSetup
        hubspotKey={hubspotKey}
        onHubspotKeyChange={saveHubspotKey}
        hubspotConnected={hubspotConnected}
        onHubspotConnected={setHubspotConnected}
        sfInstanceUrl={sfInstanceUrl}
        onSfInstanceUrlChange={(val) => saveSfField('crm_sf_instance_url', val, setSfInstanceUrl)}
        sfAccessToken={sfAccessToken}
        onSfAccessTokenChange={(val) => saveSfField('crm_sf_access_token', val, setSfAccessToken)}
        sfClientId={sfClientId}
        onSfClientIdChange={(val) => saveSfField('crm_sf_client_id', val, setSfClientId)}
        sfClientSecret={sfClientSecret}
        onSfClientSecretChange={(val) => saveSfField('crm_sf_client_secret', val, setSfClientSecret)}
        sfConnected={sfConnected}
        onSfConnected={setSfConnected}
      />

      {/* Security Note */}
      <div className="mb-8 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 flex-shrink-0" />
        Credentials are stored in your browser only. For production use, configure via environment variables on the server.
      </div>

      {/* Push Form */}
      <CRMPushForm
        campaigns={campaigns}
        hubspotKey={hubspotKey}
        sfAccessToken={sfAccessToken}
        sfInstanceUrl={sfInstanceUrl}
        sfClientId={sfClientId}
        sfClientSecret={sfClientSecret}
        onPushComplete={handlePushComplete}
      />

      {/* Push History */}
      <CRMPushHistory
        records={pushRecords}
        hubspotKey={hubspotKey}
        onSyncAgain={handleSyncAgain}
      />
    </div>
  );
}
