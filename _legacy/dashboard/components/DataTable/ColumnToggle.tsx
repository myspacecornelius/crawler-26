'use client';

import * as React from 'react';
import { Columns3 } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ColumnToggleProps {
  columns: { key: string; label: string; hidden?: boolean }[];
  visibleKeys: Set<string>;
  onChange: (visibleKeys: Set<string>) => void;
  tableId: string;
}

export default function ColumnToggle({ columns, visibleKeys, onChange, tableId }: ColumnToggleProps) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const stored = localStorage.getItem(`dt-cols-${tableId}`);
    if (stored) {
      try {
        const keys = JSON.parse(stored) as string[];
        onChange(new Set(keys));
      } catch { /* ignore */ }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableId]);

  React.useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const toggle = (key: string) => {
    const next = new Set(visibleKeys);
    if (next.has(key)) {
      if (next.size > 1) next.delete(key);
    } else {
      next.add(key);
    }
    localStorage.setItem(`dt-cols-${tableId}`, JSON.stringify([...next]));
    onChange(next);
  };

  const resetAll = () => {
    const all = new Set(columns.map((c) => c.key));
    localStorage.removeItem(`dt-cols-${tableId}`);
    onChange(all);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border transition-colors',
          open
            ? 'border-gray-400 bg-gray-100 text-gray-900'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        )}
      >
        <Columns3 className="h-4 w-4" />
        Columns
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 z-30 w-56 bg-white rounded-lg border border-gray-200 shadow-lg py-1">
          <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Toggle columns</span>
            <button onClick={resetAll} className="text-xs text-brand-600 hover:text-brand-700 font-medium">
              Reset
            </button>
          </div>
          {columns.map((col) => (
            <label
              key={col.key}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={visibleKeys.has(col.key)}
                onChange={() => toggle(col.key)}
                className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              {col.label}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
