'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import * as Dialog from '@radix-ui/react-dialog';
import { clsx } from 'clsx';
import {
  Search,
  LayoutDashboard,
  Rocket,
  Send,
  Link as LinkIcon,
  Building2,
  Briefcase,
  Settings,
  Plus,
  ArrowUpRight,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface PaletteItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  section: 'navigation' | 'actions';
}

const ITEMS: PaletteItem[] = [
  // Navigation
  { id: 'nav-overview', label: 'Overview', icon: LayoutDashboard, href: '/dashboard', section: 'navigation' },
  { id: 'nav-campaigns', label: 'Campaigns', icon: Rocket, href: '/dashboard/campaigns', section: 'navigation' },
  { id: 'nav-outreach', label: 'Outreach', icon: Send, href: '/dashboard/outreach', section: 'navigation' },
  { id: 'nav-crm', label: 'CRM', icon: LinkIcon, href: '/dashboard/crm', section: 'navigation' },
  { id: 'nav-verticals', label: 'Verticals', icon: Building2, href: '/dashboard/verticals', section: 'navigation' },
  { id: 'nav-portfolio', label: 'Portfolio', icon: Briefcase, href: '/dashboard/portfolio', section: 'navigation' },
  { id: 'nav-settings', label: 'Settings', icon: Settings, href: '/dashboard/settings', section: 'navigation' },
  // Quick actions
  { id: 'act-new-campaign', label: 'New Campaign', icon: Plus, href: '/dashboard/campaigns/new', section: 'actions' },
  { id: 'act-push-crm', label: 'Push to CRM', icon: ArrowUpRight, href: '/dashboard/crm', section: 'actions' },
];

const RECENT_KEY = 'command_palette_recent';
const MAX_RECENT = 5;

function getRecent(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
  } catch {
    return [];
  }
}

function addRecent(href: string) {
  const recent = getRecent().filter((r) => r !== href);
  recent.unshift(href);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Listen for custom event from sidebar search button
  useEffect(() => {
    function handler() {
      setOpen(true);
    }
    window.addEventListener('open-command-palette', handler);
    return () => window.removeEventListener('open-command-palette', handler);
  }, []);

  // Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Reset state when opening
  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const filtered = query
    ? ITEMS.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()))
    : ITEMS;

  const navItems = filtered.filter((i) => i.section === 'navigation');
  const actionItems = filtered.filter((i) => i.section === 'actions');

  // Build flat list for keyboard navigation
  const flatList: PaletteItem[] = [];
  if (navItems.length) flatList.push(...navItems);
  if (actionItems.length) flatList.push(...actionItems);

  // Also show recent when no query
  const recent = !query ? getRecent() : [];
  const recentItems = recent
    .map((href) => ITEMS.find((i) => i.href === href))
    .filter(Boolean) as PaletteItem[];

  const navigateTo = useCallback(
    (href: string) => {
      addRecent(href);
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const total = flatList.length;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % total);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 + total) % total);
    } else if (e.key === 'Enter' && flatList[activeIndex]) {
      e.preventDefault();
      navigateTo(flatList[activeIndex].href);
    }
  };

  // Reset active index when filtered list changes
  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
            <Search size={18} className="text-gray-400 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search pages and actions..."
              className="flex-1 text-sm text-gray-900 placeholder:text-gray-400 outline-none bg-transparent"
            />
            <kbd className="text-[10px] font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-400 border border-gray-200">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto py-2">
            {/* Recent section (only when no query) */}
            {recentItems.length > 0 && (
              <div className="mb-1">
                <p className="px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  Recent
                </p>
                {recentItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={'recent-' + item.id}
                      onClick={() => navigateTo(item.href)}
                      className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <Icon size={16} className="text-gray-400" />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Navigation section */}
            {navItems.length > 0 && (
              <div className="mb-1">
                <p className="px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  Navigation
                </p>
                {navItems.map((item, i) => {
                  const Icon = item.icon;
                  const idx = flatList.indexOf(item);
                  return (
                    <button
                      key={item.id}
                      onClick={() => navigateTo(item.href)}
                      onMouseEnter={() => setActiveIndex(idx)}
                      className={clsx(
                        'flex items-center gap-3 w-full px-4 py-2 text-sm transition-colors',
                        idx === activeIndex
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      )}
                    >
                      <Icon size={16} className={idx === activeIndex ? 'text-brand-500' : 'text-gray-400'} />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Actions section */}
            {actionItems.length > 0 && (
              <div className="mb-1">
                <p className="px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  Quick Actions
                </p>
                {actionItems.map((item) => {
                  const Icon = item.icon;
                  const idx = flatList.indexOf(item);
                  return (
                    <button
                      key={item.id}
                      onClick={() => navigateTo(item.href)}
                      onMouseEnter={() => setActiveIndex(idx)}
                      className={clsx(
                        'flex items-center gap-3 w-full px-4 py-2 text-sm transition-colors',
                        idx === activeIndex
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      )}
                    >
                      <Icon size={16} className={idx === activeIndex ? 'text-brand-500' : 'text-gray-400'} />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Empty state */}
            {flatList.length === 0 && (
              <div className="px-4 py-8 text-center text-sm text-gray-400">
                No results for &ldquo;{query}&rdquo;
              </div>
            )}
          </div>

          {/* Footer hints */}
          <div className="flex items-center gap-4 px-4 py-2 border-t border-gray-100 text-[11px] text-gray-400">
            <span className="flex items-center gap-1">
              <kbd className="font-mono bg-gray-100 px-1 py-0.5 rounded border border-gray-200">↑↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="font-mono bg-gray-100 px-1 py-0.5 rounded border border-gray-200">↵</kbd>
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="font-mono bg-gray-100 px-1 py-0.5 rounded border border-gray-200">esc</kbd>
              Close
            </span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
