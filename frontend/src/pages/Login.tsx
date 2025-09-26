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
    <AuthLayout title="Welcome Back" subtitle="Sign in to continue">
      <div className="space-y-4">
        {/* Quick Action Buttons */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Link
            to="/signup"
            className="flex flex-col items-center p-3 rounded-xl bg-gradient-to-br from-cyan-900/40 to-indigo-900/40 border border-cyan-500/30 hover:border-cyan-400/50 transition-all duration-200 group"
          >
            <span className="text-sm text-cyan-200">Create Account</span>
          </Link>

          <Link
            to="/forgot"
            className="flex flex-col items-center p-3 rounded-xl bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border border-indigo-500/30 hover:border-indigo-400/50 transition-all duration-200 group"
          >
            <span className="text-sm text-indigo-200">Forgot Password</span>
          </Link>

          <button
            type="button"
            onClick={() => navigate("/")}
            className="flex flex-col items-center p-3 rounded-xl bg-gradient-to-br from-purple-900/40 to-cyan-900/40 border border-purple-500/30 hover:border-purple-400/50 transition-all duration-200 group"
          >
            <span className="text-sm text-purple-200">Home</span>
          </button>
        </div>

        {/* Login Form */}
        <form className="space-y-4" onSubmit={onSubmit}>
          {error && (
            <div className="bg-red-900/50 border border-red-600/50 text-red-200 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm mb-1 text-cyan-200/80">Email</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none placeholder-cyan-200/50"
              placeholder="Email"
              autoComplete="email"
            />
          </div>

          <div>
            <label className="block text-sm mb-1 text-cyan-200/80">Password</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none placeholder-cyan-200/50"
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/25"
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        {/* Call to Action */}
        <div className="mt-8 p-4 rounded-xl bg-gradient-to-r from-indigo-900/30 to-cyan-900/30 text-center">
          <p className="text-sm text-slate-300 mb-3">Ready to create stunning posters?</p>
          <Link
            to="/signup"
            className="inline-block px-6 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-medium rounded-lg hover:from-cyan-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:scale-105"
          >
            Create Account
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}