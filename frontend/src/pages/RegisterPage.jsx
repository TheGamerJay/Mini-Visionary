import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const BRAND = {
  name: "Mini Visionary",
  slogan: "You Envision it, We Generate it.",
};

async function apiRegister(payload) {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Registration failed");
  }

  return data;
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
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Create your account</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          Join Mini Visionary and start creating posters with AI.
        </p>

        <form onSubmit={onSubmit} className="login-form">
          <label htmlFor="displayName">Display name</label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={e=>setDisplayName(e.target.value)}
            placeholder="Jay"
            required
          />

          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={e=>setUsername(e.target.value)}
            placeholder="minivisionary_jay"
            required
          />

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={e=>setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={e=>setPassword(e.target.value)}
            placeholder="At least 8 characters"
            required
          />

          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" className="accent-indigo-500 mt-0.5 flex-shrink-0" checked={agree} onChange={e=>setAgree(e.target.checked)} />
            <span>
              I agree to the{" "}
              <a className="text-indigo-300 hover:text-indigo-200 underline decoration-dotted" href="#" onClick={(e)=>e.preventDefault()}>
                Terms of Service
              </a>{" "}
              and{" "}
              <a className="text-indigo-300 hover:text-indigo-200 underline decoration-dotted" href="#" onClick={(e)=>e.preventDefault()}>
                Privacy Policy
              </a>
              .
            </span>
          </label>

          {error && <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm">{error}</div>}

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Please wait…" : "Create account"}
          </button>
        </form>

        <div className="auth-links">
          <div className="text-sm text-center">
            Already have an account? <Link to="/login" className="link-quiet">Sign in</Link>
          </div>
        </div>
      </div>

      <div className="site-banner bottom"></div>
      <div className="login-footer">
        <div className="login-tagline">You Envision it, We Generate it.</div>
      </div>
    </div>
  );
}