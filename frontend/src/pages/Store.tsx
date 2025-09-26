import { useEffect, useState } from "react";

type Item = {
  sku: "starter" | "standard" | "studio";
  name: string;
  desc: string;
  credits: number;
  price: number;
  currency: string;
};

export default function Store() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await fetch("/api/payments/products");
      const js = await res.json();
      setItems(js.items || []);
      setLoading(false);
    })();
  }, []);

  async function buy(sku: string) {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      alert("Please log in first.");
      return;
    }
    const res = await fetch("/api/payments/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        sku,
        success_url: `${window.location.origin}/checkout/success`,
        cancel_url: `${window.location.origin}/checkout/cancel`,
      }),
    });
    const js = await res.json();
    if (js.ok && js.url) window.location.href = js.url;
    else alert(js.error || "Checkout error");
  }

  if (loading) return <div className="min-h-screen bg-black text-cyan-200 flex items-center justify-center">Loading store…</div>;

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-5xl mx-auto p-6">
        <header className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" className="h-10 w-10 rounded-xl object-contain" />
            <h1 className="text-2xl font-semibold bg-gradient-to-r from-cyan-300 via-indigo-200 to-cyan-300 bg-clip-text text-transparent">
              Mini-Visionary — Store
            </h1>
          </div>
          <a href="/wallet" className="text-cyan-300 hover:text-cyan-200">Wallet</a>
        </header>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Ad-Free Subscription Tile */}
          <div className="rounded-2xl border border-purple-500/25 bg-gradient-to-br from-purple-950/70 via-black/80 to-indigo-950/70 p-6 shadow-[0_0_50px_-12px_rgba(168,85,247,0.25)] relative">
            <h2 className="text-xl font-bold text-purple-300">Remove Ads</h2>
            <p className="mt-1 text-purple-200/80">Ad-free experience across chat and poster generation.</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-purple-300">$5</span>
              <span className="text-base text-purple-300/70">/mo</span>
            </div>
            <div className="mt-2 text-purple-200/80">Clean, distraction-free interface</div>
            <div className="mt-1 text-xs text-purple-300">
              Cancel anytime
            </div>
            <button
              onClick={async () => {
                const token = localStorage.getItem("jwt_token");
                if (!token) {
                  alert("Please log in first.");
                  return;
                }
                const r = await fetch("/api/ads/checkout", {
                  method: "POST",
                  headers: { Authorization: `Bearer ${token}` }
                });
                const js = await r.json();
                if (js?.ok && js.url) window.location.href = js.url;
                else alert(js.error || "Checkout unavailable");
              }}
              className="mt-5 w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 transition"
            >
              Go Ad-Free
            </button>
          </div>

          {items.map((p, index) => (
            <div key={p.sku}
                 className={`rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-6 shadow-[0_0_50px_-12px_rgba(0,255,255,0.25)] relative ${
                   p.sku === 'standard' ? 'ring-2 ring-cyan-400/50 scale-105' : ''
                 }`}>
              {p.sku === 'standard' && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white text-xs font-semibold rounded-full">
                  Most Popular
                </div>
              )}

              <h2 className="text-xl font-bold">{p.name}</h2>
              <p className="mt-1 text-cyan-200/80">{p.desc}</p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold">${p.price.toFixed(0)}</span>
                <span className="text-xs text-cyan-300/70">{p.currency.toUpperCase()}</span>
              </div>
              <div className="mt-2 text-cyan-200/80">{p.credits} poster credits</div>
              <div className="mt-1 text-xs text-indigo-300">
                ${(p.price / p.credits).toFixed(2)} per credit
              </div>
              <button
                onClick={() => buy(p.sku)}
                className="mt-5 w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition"
              >
                Buy {p.name}
              </button>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center space-y-4">
          <p className="text-sm text-cyan-200/60">Secure payments via Stripe • 10 poster credits = 1 poster</p>
          <div className="text-xs text-indigo-300 max-w-2xl mx-auto">
            Credits never expire and can be used anytime. Each poster generation costs 10 credits.
            Failed generations are automatically refunded.
          </div>
        </div>
      </div>
    </div>
  );
}