import React, { useState } from "react";
import { Link } from "react-router-dom";

const BRAND = {
  name: "Mini Visionary",
  slogan: "You Envision it, We Generate It",
};

async function apiForgot(payload) {
  const response = await fetch("/api/auth/forgot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

export default function ForgotPage() {
  const [email, setEmail]   = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone]       = useState(false);
  const [error, setError]     = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      await apiForgot({ email });
      setDone(true);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <Link to="/login" className="inline-flex items-center gap-3">
            <img src="/static/logo.png" alt="logo" className="h-10 w-10 rounded" onError={(e)=>{e.currentTarget.style.display='none';}} />
            <div className="text-left">
              <h1 className="text-2xl font-extrabold drop-shadow">{BRAND.name}</h1>
              <p className="text-sm text-slate-300">{BRAND.slogan}</p>
            </div>
          </Link>
        </div>

        <div className="bg-slate-900/70 backdrop-blur rounded-2xl shadow-2xl ring-1 ring-white/10 p-6">
          <h2 className="text-2xl font-extrabold text-center mb-1">Password Reset</h2>
          <p className="text-center text-slate-300 mb-4">Enter your email and we'll send a reset link or temp password.</p>

          {done ? (
            <div className="text-center space-y-4">
              <div className="text-3xl">📬</div>
              <p>Check your inbox for instructions to reset your password.</p>
              <Link to="/login" className="text-indigo-300 hover:text-indigo-200">Back to sign in</Link>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-3">
              <label className="block">
                <span className="block text-sm font-medium mb-1">Email</span>
                <input type="email" autoComplete="email"
                       className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 focus:border-indigo-400 outline-none transition shadow-inner"
                       value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" required />
              </label>

              {error && <p className="text-rose-300 text-sm">{error}</p>}

              <button type="submit" disabled={loading}
                className="w-full mt-2 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-cyan-400 hover:from-pink-400 hover:to-cyan-300 text-slate-900 font-semibold shadow-lg disabled:opacity-60">
                {loading ? "Please wait…" : "Reset Password"}
              </button>

              <div className="text-sm mt-3 text-center">
                <Link to="/login" className="text-indigo-300 hover:text-indigo-200">Back to sign in</Link>
              </div>
            </form>
          )}
        </div>

        <footer className="mt-6 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} {BRAND.name}
        </footer>
      </div>
    </div>
  );
}