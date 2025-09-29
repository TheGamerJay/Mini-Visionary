import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState<string>("");
  const [adFree, setAdFree] = useState<boolean>(false);
  const [credits, setCredits] = useState<number>(0);
  const token = localStorage.getItem("jwt_token");

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    (async () => {
      try {
        const r = await fetch("/api/me", {
          headers: { Authorization: `Bearer ${token}` }
        });
        const js = await r.json();
        if (js?.ok) {
          setEmail(js.email || "");
          setAdFree(!!js.ad_free);
          setCredits(js.credits ?? 0);
        }
      } catch (error) {
        console.error("Failed to load user data:", error);
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  async function openPortal() {
    if (!token) return;

    try {
      const r = await fetch("/api/ads/portal", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const js = await r.json();
      if (js?.ok && js.url) {
        window.location.href = js.url;
      } else {
        alert(js.error || "Portal unavailable");
      }
    } catch (error) {
      console.error("Failed to open portal:", error);
      alert("Failed to open customer portal");
    }
  }

  async function goAdFree() {
    if (!token) return;

    try {
      const r = await fetch("/api/ads/checkout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const js = await r.json();
      if (js?.ok && js.url) {
        window.location.href = js.url;
      } else {
        alert(js.error || "Checkout unavailable");
      }
    } catch (error) {
      console.error("Failed to start checkout:", error);
      alert("Failed to start checkout");
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-black text-cyan-200 flex items-center justify-center">
        Please <Link className="text-cyan-300 px-2 underline" to="/login">log in</Link> to view settings.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-cyan-200 flex items-center justify-center">
        Loading…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-3xl mx-auto p-6">
        <header className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" className="h-10 w-10 rounded-xl object-contain" />
            <h1 className="text-2xl font-semibold bg-gradient-to-r from-cyan-300 via-indigo-200 to-cyan-300 bg-clip-text text-transparent">
              Mini-Visionary — Settings
            </h1>
          </div>
          <Link to="/store" className="text-cyan-300 hover:text-cyan-200">Store</Link>
        </header>

        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-5">
          <div className="text-sm text-cyan-200/80">Signed in as</div>
          <div className="text-lg font-semibold">{email || "—"}</div>

          <div className="mt-4 grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-cyan-500/25 bg-black/50 p-4">
              <div className="text-sm text-cyan-200/80 mb-1">Ad-Free Status</div>
              <div className={`text-lg font-semibold ${adFree ? "text-cyan-300" : "text-indigo-200"}`}>
                {adFree ? "Active — ads hidden" : "Not active"}
              </div>
              <div className="text-xs text-cyan-200/70 mt-1">
                {adFree ? "Manage or cancel your $5/mo ad-free subscription." : "Remove ads from chat and poster generation for $5/mo."}
              </div>

              {adFree ? (
                <button
                  onClick={openPortal}
                  className="mt-3 px-3 py-2 rounded-md border border-cyan-500/40 text-sm hover:bg-cyan-900/20 transition-colors"
                >
                  Manage Subscription
                </button>
              ) : (
                <button
                  onClick={goAdFree}
                  className="mt-3 px-3 py-2 rounded-md bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-sm font-semibold transition-all duration-200"
                >
                  Get Ad-Free — $5/mo
                </button>
              )}
            </div>

            <div className="rounded-xl border border-cyan-500/25 bg-black/50 p-4">
              <div className="text-sm text-cyan-200/80 mb-1">Credits</div>
              <div className="text-lg font-semibold text-cyan-300">{credits}</div>
              <div className="text-xs text-cyan-200/70 mt-1">
                ~ {Math.floor(credits / 10)} posters available (10 credits each)
              </div>
              <Link
                to="/store"
                className="mt-3 inline-block px-3 py-2 rounded-md bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-sm font-semibold transition-all duration-200"
              >
                Buy Credits
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-4 text-center">
          <Link
            to="/"
            className="text-cyan-400 hover:text-cyan-300 transition-colors duration-200"
          >
            Back to Home
          </Link>
        </div>

        <p className="mt-6 text-xs text-cyan-200/60 text-center">
          Need help with billing?{" "}
          <a href="mailto:support@minidreamposter.com" className="underline hover:text-cyan-200 transition-colors">
            Contact support
          </a>
        </p>
      </div>
    </div>
  );
}