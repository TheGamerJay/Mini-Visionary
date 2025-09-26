import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const BRAND = {
  name: "Mini Visionary",
  slogan: "You Envision it, We Generate It",
};

async function apiRegister(payload) {
  // TODO: replace with your real API endpoint
  // return fetch("/api/auth/register", { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(payload) })
  //   .then(r => { if(!r.ok) throw new Error("Registration failed"); return r.json(); });

  // Mock for UI
  await new Promise(r => setTimeout(r, 700));
  return { ok: true };
}

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree]       = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const nav = useNavigate();

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!agree) { setError("Please accept Terms & Privacy"); return; }
    setLoading(true); setError("");
    try {
      await apiRegister({ displayName, username, email, password });
      nav("/login");
    } catch (err) {
      setError(err.message || "Registration failed");
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
          <h2 className="text-2xl font-extrabold text-center mb-1">Create your account</h2>
          <p className="text-center text-slate-300 mb-4">Join Mini Visionary and start creating posters with AI.</p>

          <form onSubmit={onSubmit} className="space-y-3">
            <label className="block">
              <span className="block text-sm font-medium mb-1">Display name</span>
              <input className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 focus:border-indigo-400 outline-none transition shadow-inner"
                     value={displayName} onChange={e=>setDisplayName(e.target.value)} placeholder="Jay" required />
            </label>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Username</span>
              <input className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 focus:border-indigo-400 outline-none transition shadow-inner"
                     value={username} onChange={e=>setUsername(e.target.value)} placeholder="minivisionary_jay" required />
            </label>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Email</span>
              <input type="email" autoComplete="email"
                     className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 focus:border-indigo-400 outline-none transition shadow-inner"
                     value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" required />
            </label>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Password</span>
              <input type="password" autoComplete="new-password"
                     className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 focus:border-indigo-400 outline-none transition shadow-inner"
                     value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters" required />
            </label>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="accent-indigo-500" checked={agree} onChange={e=>setAgree(e.target.checked)} />
              I agree to the <a className="underline decoration-dotted" href="#" onClick={(e)=>e.preventDefault()}>Terms of Service</a> and <a className="underline decoration-dotted" href="#" onClick={(e)=>e.preventDefault()}>Privacy Policy</a>.
            </label>

            {error && <p className="text-rose-300 text-sm">{error}</p>}

            <button type="submit" disabled={loading}
              className="w-full mt-2 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-cyan-400 hover:from-pink-400 hover:to-cyan-300 text-slate-900 font-semibold shadow-lg disabled:opacity-60">
              {loading ? "Please wait…" : "Create account"}
            </button>

            <div className="text-sm mt-3 text-center">
              Already have an account? <Link to="/login" className="text-indigo-300 hover:text-indigo-200">Sign in</Link>
            </div>
          </form>
        </div>

        <footer className="mt-6 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} {BRAND.name}
        </footer>
      </div>
    </div>
  );
}