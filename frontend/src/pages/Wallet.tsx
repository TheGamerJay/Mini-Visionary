import { useEffect, useState } from "react";

export default function Wallet() {
  const [credits, setCredits] = useState<number>(0);
  const [receipts, setReceipts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("jwt_token");

  useEffect(() => {
    (async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      const res = await fetch("/api/payments/wallet", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const js = await res.json();
      if (js.ok) {
        setCredits(js.wallet?.credits ?? 0);
        setReceipts(js.receipts || []);
      }
      setLoading(false);
    })();
  }, [token]);

  async function viewReceipt(receiptId: number) {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    const url = `/api/payments/receipt/${receiptId}`;
    window.open(url, '_blank');
  }

  async function downloadReceipt(receiptId: number) {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    try {
      const response = await fetch(`/api/payments/receipt/${receiptId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const htmlContent = await response.text();
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt-${receiptId}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download receipt');
    }
  }

  async function emailReceipt(receiptId: number) {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    try {
      const response = await fetch("/api/payments/email-receipt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ receipt_id: receiptId })
      });

      const result = await response.json();
      if (result.ok) {
        alert("Receipt emailed successfully!");
      } else {
        alert(result.error || "Failed to email receipt");
      }
    } catch (error) {
      console.error('Email failed:', error);
      alert('Failed to email receipt');
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-black text-cyan-200 flex items-center justify-center">Loading wallet…</div>;
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-black text-cyan-200 flex items-center justify-center">
        Please <a className="text-cyan-300 px-2" href="/login">log in</a> to view your wallet.
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto p-6">
        <header className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" className="h-10 w-10 rounded-xl object-contain" />
            <h1 className="text-2xl font-semibold bg-gradient-to-r from-cyan-300 via-indigo-200 to-cyan-300 bg-clip-text text-transparent">
              Mini-Visionary — Wallet
            </h1>
          </div>
          <a href="/store" className="text-cyan-300 hover:text-cyan-200">Store</a>
        </header>

        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-6 mb-8">
          <div className="text-xl">Poster Credits: <span className="font-bold text-cyan-300">{credits}</span></div>
          <div className="text-sm text-indigo-300 mt-1">
            {Math.floor(credits / 10)} posters remaining • 10 credits = 1 poster
          </div>
        </div>

        <h2 className="mt-8 mb-3 text-xl font-semibold">Purchase History</h2>
        <div className="space-y-3">
          {receipts.length === 0 && <div className="text-cyan-200/70">No purchases yet.</div>}
          {receipts.map((r) => (
            <div key={r.id}
                 className="rounded-xl border border-cyan-500/20 bg-black/60 p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-medium">{r.sku.toUpperCase()} Pack — ${r.amount.toFixed(0)} {r.currency.toUpperCase()}</div>
                  <div className="text-xs text-cyan-200/70">{new Date(r.created_at).toLocaleString()}</div>
                </div>
                <div className="text-xs text-cyan-300">#{r.provider_id.substring(0, 12)}...</div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={() => viewReceipt(r.id)}
                  className="px-3 py-1 text-xs bg-cyan-600/20 border border-cyan-500/30 text-cyan-300 rounded hover:bg-cyan-600/30 transition-colors"
                >
                  View/Print
                </button>
                <button
                  onClick={() => downloadReceipt(r.id)}
                  className="px-3 py-1 text-xs bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 rounded hover:bg-indigo-600/30 transition-colors"
                >
                  Download
                </button>
                <button
                  onClick={() => emailReceipt(r.id)}
                  className="px-3 py-1 text-xs bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded hover:bg-purple-600/30 transition-colors"
                >
                  Email
                </button>
              </div>
            </div>
          ))}
        </div>

        {receipts.length === 0 && (
          <div className="mt-8 text-center">
            <p className="text-indigo-300 mb-4">Ready to start creating amazing posters?</p>
            <a
              href="/store"
              className="inline-block px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-600 hover:to-indigo-700 text-white font-semibold rounded-lg transition-all duration-200"
            >
              Get Poster Credits
            </a>
          </div>
        )}
      </div>
    </div>
  );
}