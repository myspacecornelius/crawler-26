'use client';

import Link from 'next/link';
import { Plus, Globe, Link2, Download } from 'lucide-react';
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
      label: 'New Campaign',
      description: 'Create a lead gen campaign',
      icon: <Plus className="w-5 h-5" />,
      href: '/dashboard/campaigns/new',
    },
    {
      label: 'Run Deep Crawl',
      description: 'Extract contacts from funds',
      icon: <Globe className="w-5 h-5" />,
      onClick: onRunCrawl,
    },
    {
      label: 'Push to CRM',
      description: 'Sync leads to HubSpot / SF',
      icon: <Link2 className="w-5 h-5" />,
      href: '/dashboard/crm',
    },
    {
      label: 'Export CSV',
      description: 'Download leads as CSV',
      icon: <Download className="w-5 h-5" />,
      onClick: onExportCsv,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {actions.map((a) => {
        const inner = (
          <div className="flex flex-col items-center text-center gap-2 p-4 rounded-xl border border-gray-200 bg-white hover:border-brand-300 hover:shadow-md transition-all cursor-pointer group">
            <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center group-hover:bg-brand-100 transition-colors">
              {a.icon}
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">{a.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{a.description}</p>
            </div>
          </div>
        );

        if (a.href) {
          return (
            <Link key={a.label} href={a.href}>
              {inner}
            </Link>
          );
        }
        return (
          <button key={a.label} onClick={a.onClick} className="text-left">
            {inner}
          </button>
        );
      })}
    </div>
  );
}
