"use client";

import { Search } from "lucide-react";

export function OfferFilters() {
  return (
    <div className="space-y-6">
      {/* Search */}
      <div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search offers…"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-colors"
          />
        </div>
      </div>

      {/* Category filter */}
      <div>
        <h3 className="text-sm font-medium text-zinc-300 mb-3">Category</h3>
        <div className="space-y-2">
          {["All", "Analytics", "Infrastructure", "Security", "DevTools", "Marketing"].map(
            (cat) => (
              <label key={cat} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-200 cursor-pointer">
                <input
                  type="radio"
                  name="category"
                  defaultChecked={cat === "All"}
                  className="accent-brand-500"
                />
                {cat}
              </label>
            )
          )}
        </div>
      </div>

      {/* Reward type filter */}
      <div>
        <h3 className="text-sm font-medium text-zinc-300 mb-3">Reward Type</h3>
        <div className="space-y-2">
          {["All", "Gift Card", "Cash", "Credit", "Discount", "Swag"].map(
            (type) => (
              <label key={type} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-200 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked={type === "All"}
                  className="accent-brand-500 rounded"
                />
                {type}
              </label>
            )
          )}
        </div>
      </div>

      {/* Region filter */}
      <div>
        <h3 className="text-sm font-medium text-zinc-300 mb-3">Region</h3>
        <select className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 focus:border-brand-500 outline-none">
          <option>All Regions</option>
          <option>US</option>
          <option>EU</option>
          <option>Global</option>
        </select>
      </div>
    </div>
  );
}
