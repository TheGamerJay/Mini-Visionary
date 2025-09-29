import { Link } from "react-router-dom";

export default function CheckoutSuccess() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-green-400">Payment Success!</h1>
          <p className="text-cyan-200">
            Your poster credits have been added to your account.
          </p>
        </div>

        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-6">
          <div className="space-y-4">
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
                to="/wallet"
                className="block px-6 py-2 border border-indigo-400 text-indigo-300 font-medium rounded-lg hover:bg-indigo-900/20 transition-all duration-200"
              >
                View Wallet
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
  );
}