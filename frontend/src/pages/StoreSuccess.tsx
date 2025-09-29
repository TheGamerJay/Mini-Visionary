import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

export default function StoreSuccess() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [sessionData, setSessionData] = useState<any>(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");

    if (!sessionId) {
      setStatus("error");
      return;
    }

    const verifyPayment = async () => {
      try {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
          setStatus("error");
          return;
        }

        const response = await fetch(`/api/payments/session/${sessionId}`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });

        const data = await response.json();

        if (data.ok && data.status === "paid") {
          setSessionData(data);
          setStatus("success");
        } else {
          setStatus("error");
        }
      } catch (error) {
        console.error("Payment verification error:", error);
        setStatus("error");
      }
    };

    verifyPayment();
  }, [searchParams]);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-cyan-200">Verifying your payment...</p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full text-center space-y-6">
          <h1 className="text-2xl font-bold text-red-400">Payment Error</h1>
          <p className="text-indigo-300">
            We couldn't verify your payment. Please check your account or contact support if you were charged.
          </p>
          <div className="space-y-3">
            <Link
              to="/store"
              className="block px-6 py-2 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-medium rounded-lg hover:from-cyan-600 hover:to-indigo-700 transition-all duration-200"
            >
              Try Again
            </Link>
            <Link
              to="/"
              className="block text-cyan-400 hover:text-cyan-300 transition-colors duration-200"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-green-400">Payment Success!</h1>
          <p className="text-indigo-300">
            Your credits have been added to your account.
          </p>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-indigo-900 rounded-2xl p-6 border border-indigo-600/30">
          <div className="space-y-4">
            <div className="text-cyan-200">
              <div className="text-sm opacity-75">Payment Email</div>
              <div className="font-medium">{sessionData?.customer_email || "Confirmed"}</div>
            </div>

            <div className="pt-4 border-t border-indigo-600/30">
              <p className="text-sm text-indigo-300 mb-4">
                Ready to create amazing posters? Your credits are waiting!
              </p>

              <div className="space-y-3">
                <Link
                  to="/create"
                  className="block px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-cyan-600 hover:to-indigo-700 transition-all duration-200"
                >
                  Start Creating Posters
                </Link>

                <Link
                  to="/gallery"
                  className="block px-6 py-2 border border-indigo-400 text-indigo-300 font-medium rounded-lg hover:bg-indigo-900/20 transition-all duration-200"
                >
                  View Gallery
                </Link>

                <Link
                  to="/"
                  className="block text-cyan-400 hover:text-cyan-300 transition-colors duration-200"
                >
                  Back to Home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}