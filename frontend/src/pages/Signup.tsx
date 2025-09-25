import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { useState } from "react";

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ display_name: "", email: "", password: "", confirmPassword: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          display_name: form.display_name
        }),
      });

      const data = await response.json();

      if (data.ok && data.token) {
        // Store JWT token
        localStorage.setItem('jwt_token', data.token);
        navigate("/");
      } else {
        setError(data.error || "Signup failed");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create Account" subtitle="Start creating amazing posters">
      <form className="space-y-4" onSubmit={onSubmit}>
        {error && (
          <div className="bg-red-900/50 border border-red-600/50 text-red-200 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm mb-1 text-cyan-200/80">Display Name</label>
          <input
            type="text"
            required
            value={form.display_name}
            onChange={(e) => setForm({ ...form, display_name: e.target.value })}
            className="w-full p-3 rounded-lg bg-black/60 border border-cyan-600 focus:ring-2 focus:ring-indigo-400 outline-none placeholder-cyan-200/50"
            placeholder="Your display name"
            autoComplete="name"
          />
        </div>

        <div>
          <label className="block text-sm mb-1 text-cyan-200/80">Email</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full p-3 rounded-lg bg-black/60 border border-cyan-600 focus:ring-2 focus:ring-indigo-400 outline-none placeholder-cyan-200/50"
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
            className="w-full p-3 rounded-lg bg-black/60 border border-cyan-600 focus:ring-2 focus:ring-indigo-400 outline-none placeholder-cyan-200/50"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            minLength={8}
          />
        </div>

        <div>
          <label className="block text-sm mb-1 text-cyan-200/80">Confirm Password</label>
          <input
            type="password"
            required
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            className="w-full p-3 rounded-lg bg-black/60 border border-cyan-600 focus:ring-2 focus:ring-indigo-400 outline-none placeholder-cyan-200/50"
            placeholder="Confirm your password"
            autoComplete="new-password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Creating…" : "Sign Up"}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-indigo-200/80">
        Already have an account?{" "}
        <Link to="/login" className="text-cyan-300 hover:text-cyan-200 font-medium">
          Log in
        </Link>
      </div>
    </AuthLayout>
  );
}