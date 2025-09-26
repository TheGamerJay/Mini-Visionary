import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token");
    }
  }, [token]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      setError("Invalid reset token");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });

      const data = await response.json();

      if (data.ok) {
        setSuccess(true);
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate("/login");
        }, 3000);
      } else {
        if (data.error === "token_expired") {
          setError("Reset link has expired. Please request a new password reset.");
        } else if (data.error === "invalid_token") {
          setError("Invalid reset link. Please request a new password reset.");
        } else {
          setError(data.error || "Failed to reset password");
        }
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <AuthLayout title="Invalid Link" subtitle="This reset link is not valid">
        <div className="text-center space-y-4">
          <div className="bg-red-900/50 border border-red-600/50 text-red-200 px-4 py-3 rounded-lg text-sm">
            This password reset link is invalid or has expired.
          </div>
          <Link
            to="/forgot"
            className="block px-6 py-2 bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition text-white font-medium rounded-lg"
          >
            Request New Reset Link
          </Link>
          <Link
            to="/login"
            className="block text-cyan-300 hover:text-cyan-200 transition-colors duration-200"
          >
            Back to Login
          </Link>
        </div>
      </AuthLayout>
    );
  }

  if (success) {
    return (
      <AuthLayout title="Password Reset!" subtitle="Your password has been successfully updated">
        <div className="text-center space-y-4">

          <div className="bg-green-900/50 border border-green-600/50 text-green-200 px-4 py-3 rounded-lg text-sm">
            Your password has been successfully reset. You can now log in with your new password.
          </div>

          <p className="text-indigo-300">
            Redirecting to login page in a few seconds...
          </p>

          <Link
            to="/login"
            className="block px-6 py-2 bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition text-white font-medium rounded-lg"
          >
            Continue to Login
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Set New Password" subtitle="Choose a strong password for your account">
      <form className="space-y-4" onSubmit={onSubmit}>
        {error && (
          <div className="bg-red-900/50 border border-red-600/50 text-red-200 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm mb-1 text-cyan-200/80">New Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none placeholder-cyan-200/50"
            placeholder="At least 8 characters"
            minLength={8}
          />
        </div>

        <div>
          <label className="block text-sm mb-1 text-cyan-200/80">Confirm Password</label>
          <input
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none placeholder-cyan-200/50"
            placeholder="Confirm your new password"
            minLength={8}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Updating Password…" : "Update Password"}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-indigo-200/80">
        Remember your password?{" "}
        <Link to="/login" className="text-cyan-300 hover:text-cyan-200 font-medium">
          Back to Login
        </Link>
      </div>
    </AuthLayout>
  );
}