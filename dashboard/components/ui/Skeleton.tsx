import * as React from 'react';
import { cn } from '@/lib/cn';

/* ── Base Skeleton ────────────────────────────────── */

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-[var(--radius)] bg-[hsl(var(--muted))]', className)}
      {...props}
    />
  );
}
Skeleton.displayName = 'Skeleton';

/* ── SkeletonText ─────────────────────────────────── */

function SkeletonText({
  lines = 3,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { lines?: number }) {
  return (
    <div className={cn('space-y-2', className)} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn('h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  );
}
SkeletonText.displayName = 'SkeletonText';

/* ── SkeletonCircle ───────────────────────────────── */

function SkeletonCircle({
  size = 40,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { size?: number }) {
  return (
    <Skeleton
      className={cn('shrink-0 rounded-full', className)}
      style={{ width: size, height: size }}
      {...props}
    />
  );
}
SkeletonCircle.displayName = 'SkeletonCircle';

/* ── SkeletonCard ─────────────────────────────────── */

function SkeletonCard({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-sm',
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-4">
        <SkeletonCircle size={48} />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="mt-4">
        <SkeletonText lines={3} />
      </div>
    </div>
  );
}
SkeletonCard.displayName = 'SkeletonCard';

export { Skeleton, SkeletonText, SkeletonCircle, SkeletonCard };
export default Skeleton;
