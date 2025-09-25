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
        navigate("/");
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
          <label className="flex items-center justify-between text-sm mb-1 text-cyan-200/80">
            <span>Password</span>
            <Link to="/forgot" className="text-cyan-300 hover:text-cyan-200">
              Forgot?
            </Link>
          </label>
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
          className="w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-indigo-200/80">
        Don't have an account?{" "}
        <Link to="/signup" className="text-cyan-300 hover:text-cyan-200 font-medium">
          Create account
        </Link>
      </div>
    </AuthLayout>
  );
}