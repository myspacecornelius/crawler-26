'use client';

import { Globe, Mail, Rocket, Link2, Send } from 'lucide-react';
import { motion } from 'framer-motion';
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
  crawl_complete: <Globe className="w-4 h-4 text-brand-400 group-hover:text-brand-300 transition-colors" />,
  enrichment_complete: <Mail className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300 transition-colors" />,
  campaign_created: <Rocket className="w-4 h-4 text-brand-500 group-hover:text-brand-400 transition-colors" />,
  crm_push: <Link2 className="w-4 h-4 text-violet-400 group-hover:text-violet-300 transition-colors" />,
  outreach_launched: <Send className="w-4 h-4 text-amber-500 group-hover:text-amber-400 transition-colors" />,
};

const EVENT_BG: Record<EventType, string> = {
  crawl_complete: 'bg-brand-500/10 border-brand-500/20 group-hover:border-brand-500/50',
  enrichment_complete: 'bg-emerald-500/10 border-emerald-500/20 group-hover:border-emerald-500/50',
  campaign_created: 'bg-brand-500/20 border-brand-500/30 group-hover:border-brand-500/60 shadow-[0_0_10px_-2px_rgba(245,158,11,0.3)]',
  crm_push: 'bg-violet-500/10 border-violet-500/20 group-hover:border-violet-500/50',
  outreach_launched: 'bg-amber-500/10 border-amber-500/20 group-hover:border-amber-500/50',
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
  { id: '3', type: 'campaign_created', message: "Hive Node 'Q1 VC Outreach' established", timestamp: new Date(Date.now() - 24 * 60 * 60_000).toISOString() },
  { id: '4', type: 'crm_push', message: 'Pushed 150 leads to Hub node', timestamp: new Date(Date.now() - 48 * 60 * 60_000).toISOString() },
  { id: '5', type: 'outreach_launched', message: 'Swarm launched via Instantly', timestamp: new Date(Date.now() - 72 * 60 * 60_000).toISOString() },
];

export default function ActivityFeed({ events }: ActivityFeedProps) {
  const items = events ?? DEFAULT_EVENTS;

  return (
    <div className="glass-card hive-border rounded-xl p-6 relative overflow-hidden">
      {/* Background glow accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full blur-[50px] pointer-events-none" />

      <h3 className="font-semibold text-gray-100 mb-5 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulseGlow" />
        Hive Activity Log
      </h3>

      <div className="space-y-4 relative z-10">
        {items.map((ev, i) => (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            key={ev.id}
            className="flex items-start gap-4 group p-2 -mx-2 rounded-lg hover:bg-white/5 cursor-default transition-colors"
          >
            <div className={`flex-shrink-0 w-9 h-9 border rounded-[0.8rem] flex items-center justify-center transition-all duration-300 ${EVENT_BG[ev.type]}`}>
              {EVENT_ICON[ev.type]}
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
              <p className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">{ev.message}</p>
              <p className="text-xs font-mono text-gray-500 mt-1">{relativeTime(ev.timestamp)}</p>
            </div>
          </motion.div>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-6">Hive is dormant</p>
        )}
      </div>
    </div>
  );
}
