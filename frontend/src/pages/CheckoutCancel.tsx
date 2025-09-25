import { Link } from "react-router-dom";

export default function CheckoutCancel() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-16 h-16 bg-yellow-900/50 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.19 2.5 1.732 2.5z" />
          </svg>
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-yellow-400">Payment Cancelled</h1>
          <p className="text-cyan-200">
            Your payment was cancelled. No charges were made to your account.
          </p>
        </div>

        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-6">
          <div className="space-y-4">
            <p className="text-sm text-indigo-300 mb-4">
              Still want to get poster credits? You can try again anytime.
            </p>

            <div className="space-y-3">
              <Link
                to="/store"
                className="block px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-cyan-600 hover:to-indigo-700 transition-all duration-200"
              >
                Back to Store
              </Link>

              <Link
                to="/wallet"
                className="block px-6 py-2 border border-indigo-400 text-indigo-300 font-medium rounded-lg hover:bg-indigo-900/20 transition-all duration-200"
              >
                View Current Balance
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