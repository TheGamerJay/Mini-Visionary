import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (data.ok && data.token) {
        localStorage.setItem('jwt_token', data.token);
        navigate("/dashboard");
      } else {
        setError(data.error || "Login failed");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const togglePassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Welcome back</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          Sign in to continue Your Vision.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            autoComplete="email"
            required
          />

          <label htmlFor="password">Password</label>
          <div className="password-field">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
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

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/register" className="btn-secondary">
            Create account
          </Link>
          <Link to="/forgot-password" className="link-quiet">
            Forgot password?
          </Link>
        </div>
      </div>

      <div className="site-banner bottom"></div>
      <div className="login-footer">
        <div className="login-tagline">You Envision it, We Generate it.</div>
      </div>
    </div>
  );
}