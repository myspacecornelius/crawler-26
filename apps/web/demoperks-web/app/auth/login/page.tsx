import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Log In — Demo Offers",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-6 animate-fade-in">
      <div className="glass rounded-2xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-2">Welcome back</h1>
        <p className="text-zinc-400 text-center text-sm mb-8">
          Log in to your Demo Offers account
        </p>

        <form className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">
              Email
            </label>
            <input
              type="email"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">
              Password
            </label>
            <input
              type="password"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-brand-600 hover:bg-brand-500 text-white py-2.5 font-semibold transition-colors"
          >
            Log In
          </button>
        </form>

        <p className="text-center text-sm text-zinc-400 mt-6">
          Don&apos;t have an account?{" "}
          <Link
            href="/auth/signup"
            className="text-brand-400 hover:text-brand-300 font-medium"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
