'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';

const nav = [
  { href: '/dashboard', label: 'Overview', icon: '📊' },
  { href: '/dashboard/campaigns', label: 'Campaigns', icon: '🚀' },
  { href: '/dashboard/outreach', label: 'Outreach', icon: '📨' },
  { href: '/dashboard/verticals', label: 'Verticals', icon: '🏢' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-gray-900 text-white flex flex-col">
      <div className="px-6 py-5 border-b border-gray-800">
        <h1 className="text-xl font-bold tracking-tight">
          <span className="text-brand-400">Lead</span>Factory
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">Multi-vertical lead gen</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-brand-600/20 text-brand-300'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-gray-800">
        <button
          onClick={() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }}
          className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
