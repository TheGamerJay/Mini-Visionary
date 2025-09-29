import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AdSlot from "../components/AdSlot";

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Fetch user data
    fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok && data.user) {
        setUser(data.user);
      } else {
        localStorage.removeItem('jwt_token');
        navigate('/login');
      }
    })
    .catch(() => {
      localStorage.removeItem('jwt_token');
      navigate('/login');
    });
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    navigate('/login');
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-cyan-200">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Background Glow */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-cyan-600/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-[28rem] w-[28rem] rounded-full bg-indigo-700/15 blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Link
            to="/"
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
          >
            <img
              src="/logo.png"
              alt="Mini-Visionary Logo"
              className="h-10 w-auto object-contain"
            />
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent">
              Mini-Visionary
            </span>
          </Link>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-cyan-200">Welcome back,</p>
              <p className="font-semibold text-white">{user.display_name}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center text-sm font-semibold">
              {user.display_name?.[0]?.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Credits & Ad-Free Status Display */}
        <div className="mb-8 flex flex-wrap gap-4">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-900/40 to-indigo-900/40 border border-cyan-500/30">
            <div className="w-4 h-4 rounded-full bg-gradient-to-r from-yellow-400 to-amber-500"></div>
            <span className="text-sm text-cyan-200">Credits:</span>
            <span className="font-bold text-white">{user.credits}</span>
          </div>

          <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full border ${
            user.ad_free
              ? 'bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-green-500/30'
              : 'bg-gradient-to-r from-orange-900/40 to-red-900/40 border-orange-500/30'
          }`}>
            <div className={`w-4 h-4 rounded-full ${
              user.ad_free ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-orange-400 to-red-500'
            }`}></div>
            <span className="text-sm text-cyan-200">
              {user.ad_free ? 'Ad-Free Active' : 'Free Version'}
            </span>
            {!user.ad_free && (
              <Link
                to="/store"
                className="text-xs text-orange-300 hover:text-orange-200 underline"
              >
                Upgrade
              </Link>
            )}
          </div>
        </div>

        {/* Main Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Create Poster */}
          <Link
            to="/create"
            className="group p-6 rounded-2xl bg-gradient-to-br from-cyan-900/30 to-indigo-900/30 border border-cyan-500/30 hover:border-cyan-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-cyan-100 mb-1">Create Poster</h3>
                <p className="text-sm text-cyan-200/70">Generate AI-powered movie posters</p>
              </div>
            </div>
          </Link>

          {/* Library */}
          <Link
            to="/library"
            className="group p-6 rounded-2xl bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-indigo-500/30 hover:border-indigo-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-indigo-100 mb-1">Library</h3>
                <p className="text-sm text-indigo-200/70">View your saved posters</p>
              </div>
            </div>
          </Link>

          {/* Wallet */}
          <Link
            to="/wallet"
            className="group p-6 rounded-2xl bg-gradient-to-br from-purple-900/30 to-cyan-900/30 border border-purple-500/30 hover:border-purple-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-purple-100 mb-1">Wallet</h3>
                <p className="text-sm text-purple-200/70">Manage credits & billing</p>
              </div>
            </div>
          </Link>

          {/* Store */}
          <Link
            to="/store"
            className="group p-6 rounded-2xl bg-gradient-to-br from-emerald-900/30 to-cyan-900/30 border border-emerald-500/30 hover:border-emerald-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-emerald-100 mb-1">Store</h3>
                <p className="text-sm text-emerald-200/70">Buy credits & bundles</p>
              </div>
            </div>
          </Link>

          {/* Chat */}
          <Link
            to="/chat"
            className="group p-6 rounded-2xl bg-gradient-to-br from-rose-900/30 to-indigo-900/30 border border-rose-500/30 hover:border-rose-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-rose-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-rose-100 mb-1">AI Chat</h3>
                <p className="text-sm text-rose-200/70">Get creative assistance</p>
              </div>
            </div>
          </Link>

          {/* Profile */}
          <Link
            to="/profile"
            className="group p-6 rounded-2xl bg-gradient-to-br from-amber-900/30 to-orange-900/30 border border-amber-500/30 hover:border-amber-400/50 transition-all duration-200 hover:shadow-lg hover:shadow-amber-500/10"
          >
            <div>
              <div>
                <h3 className="font-semibold text-amber-100 mb-1">Profile</h3>
                <p className="text-sm text-amber-200/70">Account settings</p>
              </div>
            </div>
          </Link>
        </div>

        {/* AdSense Ad Slot - Only show for non ad-free users */}
        {!user.ad_free && (
          <div className="mb-8">
            <AdSlot
              slot="1234567890"
              className="mx-auto max-w-lg border border-cyan-500/20 rounded-xl bg-black/40 p-4"
            />
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            to="/settings"
            className="px-6 py-3 rounded-xl bg-slate-900/50 border border-slate-600/50 text-slate-300 hover:text-white hover:border-slate-500/70 transition-all duration-200"
          >
            Settings
          </Link>
          <Link
            to="/privacy"
            className="px-6 py-3 rounded-xl bg-slate-900/50 border border-slate-600/50 text-slate-300 hover:text-white hover:border-slate-500/70 transition-all duration-200"
          >
            Privacy
          </Link>
          <Link
            to="/terms"
            className="px-6 py-3 rounded-xl bg-slate-900/50 border border-slate-600/50 text-slate-300 hover:text-white hover:border-slate-500/70 transition-all duration-200"
          >
            Terms
          </Link>
          <button
            onClick={handleLogout}
            className="px-6 py-3 rounded-xl bg-red-900/50 border border-red-600/50 text-red-300 hover:text-white hover:border-red-500/70 transition-all duration-200"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}