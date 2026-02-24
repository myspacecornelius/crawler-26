'use client';

import Link from 'next/link';
import { Plus, Globe, Link2, Download } from 'lucide-react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface QuickAction {
  label: string;
  description: string;
  icon: ReactNode;
  href?: string;
  onClick?: () => void;
}

interface QuickActionsProps {
  onExportCsv?: () => void;
  onRunCrawl?: () => void;
}

export default function QuickActions({ onExportCsv, onRunCrawl }: QuickActionsProps) {
  const actions: QuickAction[] = [
    {
      label: 'New Core',
      description: 'Establish a new colony',
      icon: <Plus className="w-5 h-5" />,
      href: '/dashboard/campaigns/new',
    },
    {
      label: 'Deep Scrape Flow',
      description: 'Extract leads from the hive',
      icon: <Globe className="w-5 h-5" />,
      onClick: onRunCrawl,
    },
    {
      label: 'Sync Hub',
      description: 'Connect internal CRM nodes',
      icon: <Link2 className="w-5 h-5" />,
      href: '/dashboard/crm',
    },
    {
      label: 'Extract Cell',
      description: 'Download CSV nectar',
      icon: <Download className="w-5 h-5" />,
      onClick: onExportCsv,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {actions.map((a, i) => {
        const inner = (
          <motion.div
            whileHover={{ y: -4, scale: 1.02 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="flex flex-col items-center text-center gap-2 p-5 rounded-[1.5rem] glass-card hive-border cursor-pointer group"
          >
            <motion.div
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-500 border border-brand-500/20 flex items-center justify-center group-hover:bg-brand-500 group-hover:text-black group-hover:shadow-[0_0_20px_-3px_rgba(245,158,11,0.6)] transition-all duration-300"
            >
              {a.icon}
            </motion.div>
            <div>
              <p className="text-sm font-semibold text-gray-100 group-hover:text-brand-400 transition-colors">{a.label}</p>
              <p className="text-xs text-gray-500 mt-1">{a.description}</p>
            </div>
          </motion.div>
        );

        if (a.href) {
          return (
            <Link key={a.label} href={a.href}>
              {inner}
            </Link>
          );
        }
        return (
          <button key={a.label} onClick={a.onClick} className="text-left w-full">
            {inner}
          </button>
        );
      })}
    </div>
  );
}
