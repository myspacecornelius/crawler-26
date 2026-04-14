'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight } from 'lucide-react';

const LABEL_MAP: Record<string, string> = {
  dashboard: 'Overview',
  campaigns: 'Campaigns',
  outreach: 'Outreach',
  crm: 'CRM',
  verticals: 'Verticals',
  portfolio: 'Portfolio',
  settings: 'Settings',
  new: 'New Campaign',
  billing: 'Billing',
};

function toLabel(segment: string): string {
  return LABEL_MAP[segment] || segment.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  if (!pathname) return null;

  const segments = pathname.split('/').filter(Boolean);

  // Build crumb list: [{ label, href }]
  const crumbs = segments.map((seg, i) => ({
    label: toLabel(seg),
    href: '/' + segments.slice(0, i + 1).join('/'),
  }));

  // Don't show breadcrumbs if we're at root /dashboard
  if (crumbs.length <= 1) return null;

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm">
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1;
        return (
          <span key={crumb.href} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={14} className="text-gray-400 shrink-0" />}
            {isLast ? (
              <span className="text-gray-900 font-medium">{crumb.label}</span>
            ) : (
              <Link href={crumb.href} className="text-gray-500 hover:text-gray-700 transition-colors">
                {crumb.label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
