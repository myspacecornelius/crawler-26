'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import * as Dialog from '@radix-ui/react-dialog';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Rocket,
  Send,
  Link as LinkIcon,
  Building2,
  Briefcase,
  Settings,
  X,
  LogOut,
} from 'lucide-react';
import { useSidebar } from '@/contexts/SidebarContext';
import type { LucideIcon } from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const nav: NavItem[] = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/campaigns', label: 'Campaigns', icon: Rocket },
  { href: '/dashboard/outreach', label: 'Outreach', icon: Send },
  { href: '/dashboard/crm', label: 'CRM', icon: LinkIcon },
  { href: '/dashboard/verticals', label: 'Verticals', icon: Building2 },
  { href: '/dashboard/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export default function MobileNav() {
  const { mobileOpen, setMobileOpen } = useSidebar();
  const pathname = usePathname();

  // Close on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname, setMobileOpen]);

  return (
    <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />
        <Dialog.Content className="fixed left-0 top-0 z-50 h-full w-72 bg-gray-900 text-white shadow-2xl data-[state=open]:animate-in data-[state=open]:slide-in-from-left data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-gray-800">
            <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-brand-400">Lead</span>Factory
              </h1>
            </Link>
            <Dialog.Close className="text-gray-500 hover:text-white transition-colors rounded-md p-1 hover:bg-gray-800">
              <X size={20} />
            </Dialog.Close>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {nav.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === '/dashboard'
                  ? pathname === '/dashboard'
                  : pathname === item.href || pathname?.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={clsx(
                    'relative flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-600/20 text-brand-300'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  )}
                >
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-brand-500" />
                  )}
                  <Icon size={20} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Sign out */}
          <div className="absolute bottom-0 left-0 right-0 px-3 pb-6 pt-2 border-t border-gray-800">
            <button
              onClick={() => {
                localStorage.removeItem('token');
                window.location.href = '/login';
              }}
              className="flex items-center gap-3 w-full text-left px-3 py-3 text-sm text-gray-500 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
            >
              <LogOut size={18} />
              Sign out
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
