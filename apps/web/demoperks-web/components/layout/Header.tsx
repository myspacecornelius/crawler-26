import Link from "next/link";
import { Gift } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 glass">
      <div className="mx-auto max-w-7xl flex items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
            <Gift className="h-4.5 w-4.5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">
            Demo<span className="text-brand-400">Offers</span>
          </span>
        </Link>

        <nav className="hidden sm:flex items-center gap-6 text-sm">
          <Link href="/offers" className="text-zinc-400 hover:text-white transition-colors">
            Browse
          </Link>
          <Link href="/dashboard" className="text-zinc-400 hover:text-white transition-colors">
            Dashboard
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/auth/login"
            className="text-sm text-zinc-400 hover:text-white transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/auth/signup"
            className="rounded-lg bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 text-sm font-medium transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </div>
    </header>
  );
}
