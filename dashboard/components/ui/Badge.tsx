import * as React from 'react';
import { cn } from '@/lib/cn';

const badgeVariants = {
  variant: {
    default: 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]',
    success: 'bg-[hsl(var(--success))]/10 text-[hsl(var(--success))] border-[hsl(var(--success))]/20',
    warning: 'bg-[hsl(var(--warning))]/10 text-[hsl(var(--warning))] border-[hsl(var(--warning))]/20',
    destructive: 'bg-[hsl(var(--destructive))]/10 text-[hsl(var(--destructive))] border-[hsl(var(--destructive))]/20',
    outline: 'border-[hsl(var(--border))] text-[hsl(var(--foreground))]',
  },
  size: {
    sm: 'px-1.5 py-0.5 text-[10px]',
    default: 'px-2.5 py-0.5 text-xs',
  },
} as const;

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof badgeVariants.variant;
  size?: keyof typeof badgeVariants.size;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full border font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2',
          badgeVariants.variant[variant],
          badgeVariants.size[size],
          className
        )}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';

export { Badge };
export default Badge;
