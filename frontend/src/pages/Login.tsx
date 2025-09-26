import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { useState } from "react";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, password: form.password }),
      });

      const data = await response.json();

      if (data.ok && data.token) {
        // Store JWT token
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

  return (
    <AuthLayout title="Welcome to Mini-Visionary" subtitle="Sign in to start creating amazing posters">
      <div className="space-y-4">
        {/* Quick Action Buttons */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <Link
            to="/signup"
            className="flex items-center justify-center p-4 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 transition-all duration-300 group border border-slate-600/30 hover:border-slate-500/50"
          >
            <span className="text-sm font-medium text-slate-200 group-hover:text-white">Create Account</span>
          </Link>

          <Link
            to="/forgot"
            className="flex items-center justify-center p-4 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 transition-all duration-300 group border border-slate-600/30 hover:border-slate-500/50"
          >
            <span className="text-sm font-medium text-slate-200 group-hover:text-white">Forgot Password</span>
          </Link>
        </div>

        {/* Login Form */}
        <form className="space-y-4" onSubmit={onSubmit}>
          {error && (
            <div className="bg-red-500/10 border border-red-400/30 text-red-300 px-4 py-3 rounded-xl text-sm backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                {error}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-200">Email Address</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full p-4 rounded-xl bg-slate-800/50 border border-slate-600/50 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20 outline-none placeholder-slate-400 text-white transition-all duration-200"
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-200">Password</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full p-4 rounded-xl bg-slate-800/50 border border-slate-600/50 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20 outline-none placeholder-slate-400 text-white transition-all duration-200"
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl font-semibold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-700 hover:to-indigo-600 text-white transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-[1.02] transform"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Signing in...
              </div>
            ) : "Sign In to Continue"}
          </button>
        </form>

        {/* Call to Action */}
        <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-slate-800/40 to-slate-700/40 text-center border border-slate-600/20 backdrop-blur-sm">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-white mb-2">New to Mini-Visionary?</h3>
            <p className="text-sm text-slate-300">Join thousands creating stunning AI-powered posters</p>
          </div>
          <Link
            to="/signup"
            className="inline-block px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-purple-500/30 hover:scale-105 transform"
          >
            Create Free Account
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}