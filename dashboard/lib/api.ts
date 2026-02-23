const API_BASE = '/api';

async function fetchAPI(path: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Auth
export async function register(email: string, password: string, name: string, company: string) {
  const data = await fetchAPI('/users/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name, company }),
  });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const data = await fetchAPI('/users/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function getProfile() {
  return fetchAPI('/users/me');
}

export async function getCredits() {
  return fetchAPI('/users/credits');
}

// Campaigns
export async function createCampaign(name: string, vertical: string, config: Record<string, unknown> = {}) {
  return fetchAPI('/campaigns', {
    method: 'POST',
    body: JSON.stringify({ name, vertical, config }),
  });
}

export async function listCampaigns(page = 1, status?: string) {
  const params = new URLSearchParams({ page: String(page) });
  if (status) params.set('status', status);
  return fetchAPI(`/campaigns?${params}`);
}

export async function getCampaign(id: string) {
  return fetchAPI(`/campaigns/${id}`);
}

export async function runCampaign(id: string) {
  return fetchAPI(`/campaigns/${id}/run`, { method: 'POST' });
}

export async function deleteCampaign(id: string) {
  return fetchAPI(`/campaigns/${id}`, { method: 'DELETE' });
}

// Leads
export async function listLeads(campaignId: string, params: Record<string, string> = {}) {
  const searchParams = new URLSearchParams(params);
  return fetchAPI(`/leads/campaign/${campaignId}?${searchParams}`);
}

export async function getLeadStats(campaignId: string) {
  return fetchAPI(`/leads/campaign/${campaignId}/stats`);
}

export async function getFreshness(campaignId: string) {
  return fetchAPI(`/leads/campaign/${campaignId}/freshness`);
}

export function getExportUrl(campaignId: string, tier?: string) {
  const params = new URLSearchParams();
  if (tier) params.set('tier', tier);
  return `${API_BASE}/leads/campaign/${campaignId}/export?${params}`;
}

// Verticals
export async function listVerticals() {
  return fetchAPI('/verticals');
}

export async function getVertical(slug: string) {
  return fetchAPI(`/verticals/${slug}`);
}

// Billing
export async function createCheckout(plan?: string, creditPack?: string) {
  return fetchAPI('/billing/checkout', {
    method: 'POST',
    body: JSON.stringify({ plan, credit_pack: creditPack }),
  });
}

export async function getBillingPortal() {
  return fetchAPI('/billing/portal');
}

export async function getBillingHistory(page = 1) {
  return fetchAPI(`/billing/history?page=${page}`);
}

export async function getBillingPlans() {
  return fetchAPI('/billing/plans');
}

// CSV Import
export async function importCSV(campaignId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const res = await fetch(`${API_BASE}/campaigns/${campaignId}/import`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) throw new Error('Import failed');
  return res.json();
}

// Opt-out
export async function optOutLead(leadId: string) {
  return fetchAPI(`/leads/${leadId}/optout`, { method: 'POST' });
}

// Outreach
export async function launchOutreach(data: {
  name: string;
  provider: string;
  campaign_id: string;
  from_email?: string;
  from_name?: string;
  min_score?: number;
  tiers?: string[];
  api_key?: string;
  custom_vars?: Record<string, string>;
}) {
  return fetchAPI('/outreach/launch', { method: 'POST', body: JSON.stringify(data) });
}

export async function startOutreach(provider: string, providerCampaignId: string, apiKey?: string) {
  return fetchAPI('/outreach/start', {
    method: 'POST',
    body: JSON.stringify({ provider, provider_campaign_id: providerCampaignId, api_key: apiKey }),
  });
}

export async function pauseOutreach(provider: string, providerCampaignId: string, apiKey?: string) {
  return fetchAPI('/outreach/pause', {
    method: 'POST',
    body: JSON.stringify({ provider, provider_campaign_id: providerCampaignId, api_key: apiKey }),
  });
}

export async function getOutreachStats(provider: string, providerCampaignId: string) {
  return fetchAPI(`/outreach/stats/${provider}/${providerCampaignId}`);
}

export async function listOutreachTemplates() {
  return fetchAPI('/outreach/templates');
}

// Portfolio
export async function getFundPortfolio(fund: string, params: Record<string, string> = {}) {
  const searchParams = new URLSearchParams(params);
  return fetchAPI(`/funds/${encodeURIComponent(fund)}/portfolio?${searchParams}`);
}

// CRM
export async function pushToCRM(data: {
  provider: string;
  campaign_id: string;
  test_mode?: boolean;
  min_score?: number;
  tiers?: string[];
  field_mapping?: Record<string, string>;
  custom_fields?: Record<string, string>;
  api_key?: string;
  sf_client_id?: string;
  sf_client_secret?: string;
  sf_instance_url?: string;
  sf_access_token?: string;
}) {
  return fetchAPI('/crm/push', { method: 'POST', body: JSON.stringify(data) });
}

export async function getCRMStatus(data: {
  provider: string;
  crm_ids: string[];
  test_mode?: boolean;
  api_key?: string;
}) {
  return fetchAPI('/crm/status', { method: 'POST', body: JSON.stringify(data) });
}

export async function getCRMFields(provider: string, testMode = true) {
  return fetchAPI(`/crm/fields/${provider}?test_mode=${testMode}`);
}

export async function getDefaultFieldMapping() {
  return fetchAPI('/crm/field-mapping/defaults');
}
