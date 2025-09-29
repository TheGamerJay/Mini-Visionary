import { Link } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { useState } from "react";

export default function Forgot() {
  const [emailSent, setEmailSent] = useState(false);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/forgot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.ok) {
        setEmailSent(true);
      } else {
        setError(data.error || "Failed to send reset email");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Reset Password" subtitle={emailSent ? "Check your email" : "We'll email you a secure link"}>
      {emailSent ? (
        <div className="rounded-lg border border-cyan-500/30 bg-black/50 p-4 text-sm text-cyan-100">
          We sent a reset link to <span className="font-medium text-cyan-300">{email}</span>.
          <div className="mt-4 flex gap-2">
            <Link to="/login" className="px-4 py-2 rounded-md bg-cyan-600/80 hover:bg-cyan-500 transition font-medium">
              Back to Login
            </Link>
            <button
              onClick={() => setEmailSent(false)}
              className="px-4 py-2 rounded-md border border-indigo-500/60 hover:bg-indigo-900/30 transition font-medium"
            >
              Send again
            </button>
          </div>
        </div>
      ) : (
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none placeholder-cyan-200/50"
              placeholder="Email"
              autoComplete="email"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Sending…" : "Send Reset Link"}
          </button>
        </form>
      )}

      <div className="mt-6 text-center text-sm text-indigo-200/80">
        Remembered it?{" "}
        <Link to="/login" className="text-cyan-300 hover:text-cyan-200 font-medium">
          Back to Login
        </Link>
      </div>
    </AuthLayout>
  );
}