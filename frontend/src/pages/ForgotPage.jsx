import React, { useState } from "react";
import { Link } from "react-router-dom";

const BRAND = {
  name: "Mini Visionary",
  slogan: "You Envision it, We Generate it.",
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
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Password Reset</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          Enter your email and we'll send a reset link or temp password.
        </p>

        {done ? (
          <div className="text-center space-y-4">
            <div className="text-3xl">📬</div>
            <p>Check your inbox for instructions to reset your password.</p>
            <Link to="/login" className="link-quiet">Back to sign in</Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="login-form">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={e=>setEmail(e.target.value)}
placeholder="Enter your email address"
              required
            />

            {error && <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm">{error}</div>}

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "Please wait…" : "Reset Password"}
            </button>
          </form>
        )}

        <div className="auth-links">
          <div className="text-sm text-center">
            <Link to="/login" className="link-quiet">Back to sign in</Link>
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