import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const BRAND = {
  name: "Mini Visionary",
  slogan: "You Envision it, We Generate it.",
};

async function apiRegister(payload) {
  const response = await fetch("/api/auth/signup", {
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
  const [showPassword, setShowPassword] = useState(false);
  const [agree, setAgree]       = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const nav = useNavigate();

  const togglePassword = () => {
    setShowPassword(!showPassword);
  };

  const handleAgreementChange = (e) => {
    if (e.target.checked) {
      const confirmed = window.confirm(
        "By checking this box, you acknowledge that you have read, understood, and agree to be bound by Mini Visionary's Terms of Service and Privacy Policy. This agreement will govern your use of our services."
      );
      if (confirmed) {
        setAgree(true);
      } else {
        e.target.checked = false;
      }
    } else {
      setAgree(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!agree) { setError("Please accept Terms & Privacy"); return; }
    setLoading(true); setError("");
    try {
      await apiRegister({ display_name: displayName, email, password });
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
placeholder="Enter your display name"
            required
          />

          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={e=>setUsername(e.target.value)}
placeholder="Choose a username"
            required
          />

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

          <label htmlFor="password">Password</label>
          <div className="password-field">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={password}
              onChange={e=>setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
            />
            <div className="password-toggle" onClick={togglePassword}>
              {showPassword ? (
                <span>🙈</span>
              ) : (
                <span>👁️</span>
              )}
            </div>
          </div>

          {error && <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm">{error}</div>}

          <div className="mb-4">
            <div className="flex justify-center mb-2">
              <input
                type="checkbox"
                className="accent-indigo-500 w-4 h-4"
                checked={agree}
                onChange={handleAgreementChange}
              />
            </div>
            <div className="text-sm text-center leading-relaxed">
              I agree to the <Link to="/terms-of-service" className="text-indigo-300 hover:text-indigo-200 underline decoration-dotted">Terms of Service</Link> and <Link to="/privacy-policy" className="text-indigo-300 hover:text-indigo-200 underline decoration-dotted">Privacy Policy</Link>
            </div>
          </div>

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