'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/cn';

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  badge?: string;
  children: React.ReactNode;
  className?: string;
}

export default function CollapsibleSection({
  title,
  defaultOpen = false,
  badge,
  children,
  className,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | undefined>(defaultOpen ? undefined : 0);

  useEffect(() => {
    if (!contentRef.current) return;
    if (open) {
      setHeight(contentRef.current.scrollHeight);
      const timer = setTimeout(() => setHeight(undefined), 200);
      return () => clearTimeout(timer);
    } else {
      setHeight(contentRef.current.scrollHeight);
      requestAnimationFrame(() => setHeight(0));
    }
  }, [open]);

  return (
    <div className={cn('border border-gray-200 rounded-xl overflow-hidden', className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span>{title}</span>
          {badge && (
            <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-gray-100 text-gray-500">
              {badge}
            </span>
          )}
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>
      <div
        ref={contentRef}
        style={{ height: height !== undefined ? `${height}px` : 'auto' }}
        className="transition-[height] duration-200 ease-in-out overflow-hidden"
      >
        <div className="px-5 pb-4">{children}</div>
        
      </div>
    </div>
  );
}
