'use client';

import * as React from 'react';
import * as ToastPrimitives from '@radix-ui/react-toast';
import { X } from 'lucide-react';
import { cn } from '@/lib/cn';

/* ── Toast Context / Hook ─────────────────────────── */

type ToastVariant = 'default' | 'success' | 'error' | 'warning';

interface ToastEntry {
  id: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastContextValue {
  toasts: ToastEntry[];
  toast: (entry: Omit<ToastEntry, 'id'>) => void;
  dismiss: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a <Toaster />');
  return ctx;
}

/* ── Variant styles ───────────────────────────────── */

const variantStyles: Record<ToastVariant, string> = {
  default: 'border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]',
  success: 'border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/5 text-[hsl(var(--success))]',
  error: 'border-[hsl(var(--destructive))]/30 bg-[hsl(var(--destructive))]/5 text-[hsl(var(--destructive))]',
  warning: 'border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/5 text-[hsl(var(--warning))]',
};

/* ── Individual Toast ─────────────────────────────── */

function ToastItem({
  entry,
  onDismiss,
}: {
  entry: ToastEntry;
  onDismiss: (id: string) => void;
}) {
  return (
    <ToastPrimitives.Root
      className={cn(
        'group pointer-events-auto relative flex w-full items-center justify-between gap-4 overflow-hidden rounded-[var(--radius)] border p-4 shadow-lg transition-all',
        'data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)]',
        'data-[state=open]:animate-slideUp data-[state=closed]:animate-fadeOut',
        variantStyles[entry.variant ?? 'default']
      )}
      duration={entry.duration ?? 5000}
      onOpenChange={(open) => {
        if (!open) onDismiss(entry.id);
      }}
    >
      <div className="grid gap-1">
        {entry.title && (
          <ToastPrimitives.Title className="text-sm font-semibold">
            {entry.title}
          </ToastPrimitives.Title>
        )}
        {entry.description && (
          <ToastPrimitives.Description className="text-sm opacity-90">
            {entry.description}
          </ToastPrimitives.Description>
        )}
      </div>
      <ToastPrimitives.Close
        className="rounded-md p-1 opacity-0 transition-opacity hover:opacity-100 group-hover:opacity-70 focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </ToastPrimitives.Close>
    </ToastPrimitives.Root>
  );
}

/* ── Toaster Provider ─────────────────────────────── */

let toastCount = 0;

export function Toaster({ children }: { children?: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastEntry[]>([]);

  const toast = React.useCallback((entry: Omit<ToastEntry, 'id'>) => {
    const id = `toast-${++toastCount}`;
    setToasts((prev) => [...prev, { ...entry, id }]);
  }, []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const value = React.useMemo(() => ({ toasts, toast, dismiss }), [toasts, toast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      <ToastPrimitives.Provider swipeDirection="right">
        {children}
        {toasts.map((entry) => (
          <ToastItem key={entry.id} entry={entry} onDismiss={dismiss} />
        ))}
        <ToastPrimitives.Viewport className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]" />
      </ToastPrimitives.Provider>
    </ToastContext.Provider>
  );
}
Toaster.displayName = 'Toaster';

export default Toaster;
