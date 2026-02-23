'use client';

import { Globe, Mail, Rocket, Link2, Send } from 'lucide-react';
import type { ReactNode } from 'react';

type EventType = 'crawl_complete' | 'enrichment_complete' | 'campaign_created' | 'crm_push' | 'outreach_launched';

interface ActivityEvent {
  id: string;
  type: EventType;
  message: string;
  timestamp: string; // ISO string
}

interface ActivityFeedProps {
  events?: ActivityEvent[];
}

const EVENT_ICON: Record<EventType, ReactNode> = {
  crawl_complete: <Globe className="w-4 h-4 text-blue-500" />,
  enrichment_complete: <Mail className="w-4 h-4 text-emerald-500" />,
  campaign_created: <Rocket className="w-4 h-4 text-brand-600" />,
  crm_push: <Link2 className="w-4 h-4 text-violet-500" />,
  outreach_launched: <Send className="w-4 h-4 text-amber-500" />,
};

const EVENT_BG: Record<EventType, string> = {
  crawl_complete: 'bg-blue-50',
  enrichment_complete: 'bg-emerald-50',
  campaign_created: 'bg-brand-50',
  crm_push: 'bg-violet-50',
  outreach_launched: 'bg-amber-50',
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return 'Yesterday';
  return `${days}d ago`;
}

const DEFAULT_EVENTS: ActivityEvent[] = [
  { id: '1', type: 'crawl_complete', message: 'Deep crawl completed: 5,205 contacts extracted', timestamp: new Date(Date.now() - 2 * 60 * 60_000).toISOString() },
  { id: '2', type: 'enrichment_complete', message: 'Enrichment: 4,990 emails generated', timestamp: new Date(Date.now() - 5 * 60 * 60_000).toISOString() },
  { id: '3', type: 'campaign_created', message: "Campaign 'Q1 VC Outreach' created", timestamp: new Date(Date.now() - 24 * 60 * 60_000).toISOString() },
  { id: '4', type: 'crm_push', message: 'Pushed 150 leads to HubSpot', timestamp: new Date(Date.now() - 48 * 60 * 60_000).toISOString() },
  { id: '5', type: 'outreach_launched', message: 'Outreach campaign launched via Instantly', timestamp: new Date(Date.now() - 72 * 60 * 60_000).toISOString() },
];

export default function ActivityFeed({ events }: ActivityFeedProps) {
  const items = events ?? DEFAULT_EVENTS;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Recent Activity</h3>
      <div className="space-y-3">
        {items.map((ev) => (
          <div key={ev.id} className="flex items-start gap-3">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${EVENT_BG[ev.type]}`}>
              {EVENT_ICON[ev.type]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-700 leading-snug">{ev.message}</p>
              <p className="text-xs text-gray-400 mt-0.5">{relativeTime(ev.timestamp)}</p>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-4">No recent activity</p>
        )}
      </div>
    </div>
  );
}
