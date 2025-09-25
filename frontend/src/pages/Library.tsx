export default function Library() {
  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-cyan-100 mb-2">Your Poster Library</h1>
        <p className="text-cyan-200/70">View and manage all your created posters</p>
      </div>

      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-indigo-100 mb-2">No Posters Yet</h3>
        <p className="text-indigo-300 mb-6">Start creating your first AI-powered poster</p>
        <button
          onClick={() => window.location.href = '/create'}
          className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-cyan-600 hover:to-indigo-700 transition-all duration-200"
        >
          Create First Poster
        </button>
      </div>
    </div>
  );
}