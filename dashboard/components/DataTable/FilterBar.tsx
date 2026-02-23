'use client';

import * as React from 'react';
import { Filter, X } from 'lucide-react';
import { cn } from '@/lib/cn';

interface FilterBarProps {
  children: React.ReactNode;
  activeCount?: number;
  onClearAll?: () => void;
  className?: string;
}

export default function FilterBar({ children, activeCount = 0, onClearAll, className }: FilterBarProps) {
  const [open, setOpen] = React.useState(false);

  return (
    <div className={cn('', className)}>
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border transition-colors',
          open
            ? 'border-gray-400 bg-gray-100 text-gray-900'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        )}
      >
        <Filter className="h-4 w-4" />
        Filters
        {activeCount > 0 && (
          <span className="ml-1 inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold rounded-full bg-brand-600 text-white">
            {activeCount}
          </span>
        )}
      </button>

      {open && (
        <div className="mt-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {children}
          </div>
          {activeCount > 0 && onClearAll && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={onClearAll}
                className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X className="h-3 w-3" />
                Clear all filters
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
