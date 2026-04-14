import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "accent" | "success" | "outline";
  className?: string;
}

const variants = {
  default: "bg-zinc-800 text-zinc-300",
  accent: "bg-brand-600/15 text-brand-300 border border-brand-500/20",
  success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
  outline: "border border-zinc-700 text-zinc-400",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
