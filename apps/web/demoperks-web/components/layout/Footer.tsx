import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-zinc-800/50 mt-auto">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-500">
          <p>&copy; {new Date().getFullYear()} Demo Offers. All rights reserved.</p>
          <div className="flex gap-6">
            <Link href="/offers" className="hover:text-zinc-300 transition-colors">
              Browse Offers
            </Link>
            <Link href="/dashboard" className="hover:text-zinc-300 transition-colors">
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
