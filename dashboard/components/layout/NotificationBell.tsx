'use client';

import { useState } from 'react';
import { Bell } from 'lucide-react';
import { clsx } from 'clsx';

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
}

// Placeholder notifications — will be wired to real data later
const MOCK_NOTIFICATIONS: Notification[] = [
  { id: '1', title: 'Crawl completed', message: '2,832 leads extracted from VC vertical', time: '2m ago', read: false },
  { id: '2', title: 'Campaign sent', message: 'Outreach batch #12 delivered to 150 contacts', time: '1h ago', read: true },
];

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const unread = MOCK_NOTIFICATIONS.filter((n) => !n.read).length;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
        )}
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 z-40 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
              {unread > 0 && (
                <span className="text-xs text-brand-600 font-medium">{unread} new</span>
              )}
            </div>
            <div className="max-h-72 overflow-y-auto">
              {MOCK_NOTIFICATIONS.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-gray-400">No notifications</div>
              ) : (
                MOCK_NOTIFICATIONS.map((n) => (
                  <div
                    key={n.id}
                    className={clsx(
                      'px-4 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors',
                      !n.read && 'bg-brand-50/50'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-gray-900">{n.title}</p>
                      <span className="text-[11px] text-gray-400 whitespace-nowrap">{n.time}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
