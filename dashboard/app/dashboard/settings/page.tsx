'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useToast } from '@/components/ui/Toast';
import { getProfile, getCredits, createCheckout, getBillingPortal, getBillingHistory } from '@/lib/api';

export default function SettingsPage() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [credits, setCredits] = useState<any>(null);
  const [history, setHistory] = useState<any>(null);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getProfile().catch(() => null),
      getCredits().catch(() => null),
      getBillingHistory().catch(() => null),
    ]).then(([u, c, h]) => {
      setUser(u);
      setCredits(c);
      setHistory(h);
    });
  }, []);

  const plans = [
    { slug: 'starter', name: 'Starter', price: '$0/mo', credits: 500, features: ['500 credits/month', '1 vertical', 'CSV export'] },
    { slug: 'pro', name: 'Pro', price: '$49/mo', credits: 5000, features: ['5,000 credits/month', 'All verticals', 'CSV + API export', 'Email verification'] },
    { slug: 'scale', name: 'Scale', price: '$149/mo', credits: 25000, features: ['25,000 credits/month', 'All verticals', 'Priority crawling', 'Outreach integration', 'Dedicated support'] },
    { slug: 'enterprise', name: 'Enterprise', price: 'Custom', credits: -1, features: ['Unlimited credits', 'Custom verticals', 'White-label', 'SLA guarantee', 'Dedicated infrastructure'] },
  ];

  const creditPacks = [
    { slug: '1k', name: '1,000 Credits', price: '$19' },
    { slug: '5k', name: '5,000 Credits', price: '$79' },
    { slug: '10k', name: '10,000 Credits', price: '$129' },
  ];

  const handleUpgrade = async (planSlug: string) => {
    if (planSlug === 'enterprise') {
      window.location.href = 'mailto:sales@leadfactory.io?subject=Enterprise%20Plan%20Inquiry';
      return;
    }
    setLoading(planSlug);
    try {
      const { checkout_url } = await createCheckout(planSlug);
      window.location.href = checkout_url;
    } catch (e: any) {
      toast({ title: 'Checkout failed', description: e.message || 'Failed to start checkout', variant: 'error' });
    } finally {
      setLoading(null);
    }
  };

  const handleBuyCredits = async (packSlug: string) => {
    setLoading(`pack-${packSlug}`);
    try {
      const { checkout_url } = await createCheckout(undefined, packSlug);
      window.location.href = checkout_url;
    } catch (e: any) {
      toast({ title: 'Checkout failed', description: e.message || 'Failed to start checkout', variant: 'error' });
    } finally {
      setLoading(null);
    }
  };

  const handleManageSubscription = async () => {
    setLoading('portal');
    try {
      const { portal_url } = await getBillingPortal();
      window.location.href = portal_url;
    } catch (e: any) {
      toast({ title: 'Portal error', description: e.message || 'Failed to open billing portal', variant: 'error' });
    } finally {
      setLoading(null);
    }
  };

  const formatReason = (reason: string) => {
    const map: Record<string, string> = {
      monthly_refill: 'Monthly refill',
      subscription_cancelled: 'Subscription cancelled',
    };
    if (map[reason]) return map[reason];
    if (reason.startsWith('purchase:')) return `Purchased ${reason.split(':')[1]}`;
    if (reason.startsWith('plan_upgrade:')) return `Upgraded to ${reason.split(':')[1]}`;
    if (reason === 'campaign_run') return 'Campaign run';
    return reason;
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Settings</h1>
      <p className="text-sm text-gray-500 mb-8">Manage your account and subscription</p>

      {/* Account Info */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account</h2>
        {user && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Name</p>
              <p className="font-medium text-gray-900">{user.name}</p>
            </div>
            <div>
              <p className="text-gray-500">Email</p>
              <p className="font-medium text-gray-900">{user.email}</p>
            </div>
            <div>
              <p className="text-gray-500">Company</p>
              <p className="font-medium text-gray-900">{user.company || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500">Member since</p>
              <p className="font-medium text-gray-900">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        )}
      </div>

      {/* Credits */}
      {credits && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Credits</h2>
            {credits.plan !== 'starter' && (
              <button
                onClick={handleManageSubscription}
                disabled={loading === 'portal'}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
              >
                {loading === 'portal' ? 'Loading...' : 'Manage Subscription'}
              </button>
            )}
          </div>
          <div className="flex items-end gap-2 mb-3">
            <span className="text-3xl font-bold text-gray-900">{credits.credits_remaining.toLocaleString()}</span>
            <span className="text-gray-500 mb-1">/ {credits.credits_monthly.toLocaleString()} monthly</span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-blue-500 rounded-full transition-all"
              style={{ width: `${Math.min((credits.credits_remaining / credits.credits_monthly) * 100, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500">Credits refill monthly on your billing date. 1 credit = 1 lead with verified email.</p>
        </div>
      )}

      {/* Credit Packs */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Buy Credit Packs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {creditPacks.map((pack) => (
            <div key={pack.slug} className="border border-gray-200 rounded-lg p-4 flex flex-col items-center">
              <p className="font-semibold text-gray-900">{pack.name}</p>
              <p className="text-2xl font-bold text-gray-900 my-2">{pack.price}</p>
              <button
                onClick={() => handleBuyCredits(pack.slug)}
                disabled={loading === `pack-${pack.slug}`}
                className="w-full mt-2 px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {loading === `pack-${pack.slug}` ? 'Loading...' : 'Buy Now'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Plans */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {plans.map((plan) => {
            const isActive = credits?.plan?.toLowerCase() === plan.slug;
            return (
              <div
                key={plan.name}
                className={`rounded-xl border-2 p-5 transition-all ${
                  isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                  {isActive && (
                    <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">Current</span>
                  )}
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-4">{plan.price}</p>
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="text-sm text-gray-600 flex items-center gap-2">
                      <span className="text-emerald-500 text-xs">&#10003;</span>
                      {f}
                    </li>
                  ))}
                </ul>
                {!isActive && (
                  <button
                    onClick={() => handleUpgrade(plan.slug)}
                    disabled={loading === plan.slug}
                    className="w-full mt-4 px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    {loading === plan.slug
                      ? 'Loading...'
                      : plan.slug === 'enterprise'
                        ? 'Contact Sales'
                        : 'Upgrade'}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Credit History */}
      {history && history.transactions && history.transactions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Credit History</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Description</th>
                  <th className="pb-2 font-medium text-right">Amount</th>
                  <th className="pb-2 font-medium text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                {history.transactions.map((tx: any) => (
                  <tr key={tx.id} className="border-b border-gray-50">
                    <td className="py-2 text-gray-600">{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td className="py-2 text-gray-900">{formatReason(tx.reason)}</td>
                    <td className={`py-2 text-right font-medium ${tx.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {tx.amount >= 0 ? '+' : ''}{tx.amount.toLocaleString()}
                    </td>
                    <td className="py-2 text-right text-gray-600">{tx.balance_after.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Legal Links */}
      <div className="border-t border-gray-200 pt-6 flex gap-6 text-sm text-gray-500">
        <Link href="/terms" className="hover:text-gray-700">Terms of Service</Link>
        <Link href="/privacy" className="hover:text-gray-700">Privacy Policy</Link>
      </div>
    </div>
  );
}
