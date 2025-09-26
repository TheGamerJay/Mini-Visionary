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
    <div className="min-h-screen" style={{
      background: `radial-gradient(1200px 800px at 25% -10%, #1a1030 0%, transparent 55%), linear-gradient(180deg, #0b0b11, #0f0f0f)`
    }}>
      {/* Top banner */}
      <div className="h-3 w-full bg-gradient-to-r from-purple-700 via-purple-500 to-blue-400 shadow-lg shadow-purple-500/35"></div>

      <div id="login-root" className="flex items-center justify-center min-h-screen px-4 pt-10 pb-16">
        <div className="login-card w-full max-w-[520px] mx-auto mt-10 px-6 py-7 rounded-2xl bg-gradient-to-b from-slate-800/85 to-slate-900/90 border border-purple-500/25 shadow-2xl shadow-black/45">

          <h2 className="login-title text-2xl font-extrabold text-white mb-1.5">Welcome back</h2>
          <p className="login-subtitle text-slate-400 mb-4.5">
            Sign in to continue. <span className="text-blue-400 font-semibold">You Envision it, We Generate it.</span>
          </p>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form grid gap-2.5">
            <label htmlFor="email" className="text-sm text-slate-300">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-3 rounded-xl border border-purple-500/35 bg-slate-800 text-white outline-none focus:border-purple-400 focus:shadow-lg focus:shadow-purple-500/14 transition-all"
              autoComplete="email"
              required
            />

            <label htmlFor="password" className="text-sm text-slate-300">Password</label>
            <div className="password-field relative flex items-center">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-3 pr-12 rounded-xl border border-purple-500/35 bg-slate-800 text-white outline-none focus:border-purple-400 focus:shadow-lg focus:shadow-purple-500/14 transition-all"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={togglePassword}
                className="password-toggle absolute right-1.5 grid place-items-center w-9 h-9 rounded-lg bg-slate-700 border border-purple-500/25 cursor-pointer hover:bg-slate-600 transition-colors"
                aria-label="Show password"
                aria-pressed={showPassword}
              >
                <span className={`${showPassword ? 'hidden' : 'inline'}`} aria-hidden="true">👁️</span>
                <span className={`${showPassword ? 'inline' : 'hidden'}`} aria-hidden="true">🙈</span>
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-3 py-2.5 px-3.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-orange-500 via-pink-500 to-cyan-400 bg-[length:200%_100%] text-slate-900 shadow-2xl shadow-black/45 hover:-translate-y-0.5 hover:brightness-105 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="auth-links flex gap-2.5 items-center justify-between mt-3">
            <Link
              to="/signup"
              className="btn-secondary inline-flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-gradient-to-b from-slate-700 to-slate-800 text-white border border-purple-500/35 hover:border-purple-500/60 transition-all duration-200 text-sm font-semibold"
            >
              Create account
            </Link>
            <Link
              to="/forgot"
              className="link-quiet text-slate-400 hover:text-white transition-colors text-sm"
            >
              Forgot password?
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom banner */}
      <div className="h-3 w-full bg-gradient-to-r from-purple-700 via-purple-500 to-blue-400 shadow-lg shadow-purple-500/35 mt-7"></div>
      <div className="login-footer text-center mt-4 mb-6 tracking-widest font-extrabold opacity-25 text-white text-sm">
        MINI VISIONARY
      </div>
    </div>
  );
}