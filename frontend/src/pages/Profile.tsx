import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Poster = { id: number; shared_url?: string; description?: string; tags?: string; created_at: string };

type UserProfile = {
  id: number;
  email: string;
  display_name?: string;
  credits: number;
  avatar_url?: string;
  plan?: string;
  posters_created: number;
  credits_spent: number;
  member_since: string;
};

export default function Profile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [posters, setPosters] = useState<Poster[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'library' | 'settings'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    const headers = { Authorization: `Bearer ${token}` };

    Promise.all([
      fetch("/api/me", { headers }).then(r => r.json()),
      fetch("/api/profile/library", { headers }).then(r => r.json())
    ]).then(([profileData, postersData]) => {
      if (profileData?.ok) {
        setProfile({
          ...profileData.user,
          posters_created: postersData?.length || 0,
          credits_spent: profileData.user?.credits_spent || 0,
          member_since: profileData.user?.member_since || profileData.user?.created_at || new Date().toISOString(),
          plan: profileData.user?.plan || "free"
        });
      }
      if (Array.isArray(postersData)) {
        setPosters(postersData);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-3xl p-8">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center text-3xl font-bold">
            {profile?.display_name?.[0] || profile?.email[0] || 'U'}
          </div>
          <div>
            <h1 className="text-3xl font-bold">{profile?.display_name || 'User'}</h1>
            <p className="text-blue-100">{profile?.email}</p>
            <div className="flex items-center space-x-4 mt-2">
              <div className="bg-white/20 px-3 py-1 rounded-full text-sm">
                {profile?.credits || 0} credits
              </div>
              <div className="bg-white/20 px-3 py-1 rounded-full text-sm capitalize">
                {profile?.plan || 'free'} plan
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'library', label: 'My Library', icon: '🎨' },
            { id: 'settings', label: 'Settings', icon: '⚙️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl border shadow-sm">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Posters Created</p>
                  <p className="text-2xl font-semibold text-gray-900">{profile?.posters_created || 0}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border shadow-sm">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Credits Remaining</p>
                  <p className="text-2xl font-semibold text-gray-900">{profile?.credits || 0}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border shadow-sm">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Member Since</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {new Date(profile?.member_since || Date.now()).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-50 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                to="/create"
                className="flex items-center p-4 bg-white rounded-xl border hover:shadow-md transition-all duration-200"
              >
                <div>
                  <h3 className="font-semibold text-gray-900">Create New Poster</h3>
                  <p className="text-sm text-gray-600">Generate a new AI poster</p>
                </div>
              </Link>

              <Link
                to="/store"
                className="flex items-center p-4 bg-white rounded-xl border hover:shadow-md transition-all duration-200"
              >
                <div>
                  <h3 className="font-semibold text-gray-900">Buy Credits</h3>
                  <p className="text-sm text-gray-600">Get more poster credits</p>
                </div>
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'library' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">My Poster Library</h2>
            <Link
              to="/create"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create New Poster
            </Link>
          </div>

          {posters.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No posters yet</h3>
              <p className="text-gray-600 mb-6">Create your first AI-powered poster to get started!</p>
              <Link
                to="/create"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Your First Poster
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {posters.map(poster => (
                <div key={poster.id} className="bg-white rounded-2xl border shadow-sm overflow-hidden hover:shadow-md transition-all duration-200">
                  {poster.shared_url && (
                    <div className="aspect-[3/4] bg-gray-100">
                      <img
                        src={poster.shared_url}
                        alt={poster.description || 'Poster'}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 line-clamp-2">
                      {poster.description || 'Untitled Poster'}
                    </h3>
                    {poster.tags && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">{poster.tags}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      {new Date(poster.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Settings</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={profile?.email || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  value={profile?.display_name || ''}
                  placeholder="Enter your display name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Save Changes
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl border p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Privacy & Security</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">Make posters private by default</h3>
                  <p className="text-sm text-gray-600">New posters will be private to your account</p>
                </div>
                <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">Email notifications</h3>
                  <p className="text-sm text-gray-600">Receive emails about your poster generations</p>
                </div>
                <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-red-900 mb-4">Danger Zone</h2>
            <p className="text-red-700 mb-4">
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
            <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
              Delete Account
            </button>
          </div>
        </div>
      )}
    </div>
  );
}