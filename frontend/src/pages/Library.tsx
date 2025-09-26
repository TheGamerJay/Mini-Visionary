export default function Library() {
  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-cyan-100 mb-2">Your Poster Library</h1>
        <p className="text-cyan-200/70">View and manage all your created posters</p>
      </div>

      <div className="text-center py-12">
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