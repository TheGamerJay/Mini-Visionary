import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <section className="text-center space-y-8 py-16">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-white via-cyan-200 to-indigo-300 bg-clip-text text-transparent leading-tight">
            Welcome Back!
          </h1>
          <p className="text-2xl md:text-3xl text-slate-300 mt-6 font-light tracking-wide">
            Ready to create amazing posters?
          </p>
          <p className="text-xl md:text-2xl text-slate-400 mt-8 leading-relaxed max-w-4xl mx-auto">
            Your creative workspace is ready. Explore tools, browse the gallery, or start your next masterpiece.
          </p>
        </div>

        <div className="flex justify-center mt-12">
          <Link
            to="/store"
            className="px-10 py-4 bg-gradient-to-r from-indigo-600 to-cyan-600 text-white font-medium rounded-xl hover:from-indigo-700 hover:to-cyan-700 transition-all duration-300 shadow-xl hover:shadow-indigo-500/30 hover:scale-105 transform"
          >
            Explore Gallery
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid md:grid-cols-3 gap-8 mt-24">
        <div className="text-center p-8 rounded-2xl bg-slate-800/30 backdrop-blur-sm transition-all duration-300 hover:scale-105 group">
          <h3 className="text-xl font-semibold text-white mb-4">AI-Powered Generation</h3>
          <p className="text-slate-400 leading-relaxed">
            Advanced AI creates stunning, unique posters from your text descriptions in seconds with professional quality.
          </p>
        </div>

        <div className="text-center p-8 rounded-2xl bg-slate-800/30 backdrop-blur-sm transition-all duration-300 hover:scale-105 group">
          <h3 className="text-xl font-semibold text-white mb-4">Multiple Styles</h3>
          <p className="text-slate-400 leading-relaxed">
            Fantasy, sci-fi, horror, romance, action, anime - create in any genre with cinema-quality results.
          </p>
        </div>

        <div className="text-center p-8 rounded-2xl bg-slate-800/30 backdrop-blur-sm transition-all duration-300 hover:scale-105 group">
          <h3 className="text-xl font-semibold text-white mb-4">Personal Library</h3>
          <p className="text-slate-400 leading-relaxed">
            Save, organize, and manage all your creations in your private poster library with easy sharing.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-slate-800/20 backdrop-blur-sm rounded-3xl p-12 md:p-16 mt-24">
        <h2 className="text-4xl font-bold text-center text-white mb-12">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-indigo-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4 shadow-lg shadow-cyan-500/25">
              1
            </div>
            <h3 className="text-lg font-semibold mb-2 text-cyan-100">Describe Your Vision</h3>
            <p className="text-indigo-300">
              Write a description of your dream poster. Be as creative and detailed as you want.
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4 shadow-lg shadow-indigo-500/25">
              2
            </div>
            <h3 className="text-lg font-semibold mb-2 text-cyan-100">AI Creates Magic</h3>
            <p className="text-indigo-300">
              Our AI analyzes your prompt and generates a professional movie-style poster.
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-cyan-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4 shadow-lg shadow-purple-500/25">
              3
            </div>
            <h3 className="text-lg font-semibold mb-2 text-cyan-100">Save & Share</h3>
            <p className="text-indigo-300">
              Add titles, customize details, and save to your library. Ready to download or share!
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="text-center bg-gradient-to-r from-indigo-600 via-purple-700 to-cyan-700 text-white rounded-3xl p-12 md:p-16 shadow-2xl shadow-indigo-500/20 mt-24">
        <h2 className="text-4xl font-bold mb-6 text-white">Ready to Create Your First Poster?</h2>
        <p className="text-xl mb-10 max-w-3xl mx-auto text-slate-200 leading-relaxed">
          Join thousands of creators who've brought their stories to life with our professional AI-powered poster generation platform.
        </p>
        <Link
          to="/create"
          className="inline-block px-12 py-4 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-slate-100 transition-all duration-300 shadow-xl hover:shadow-2xl hover:scale-105 transform"
        >
          Start Creating Now
        </Link>
      </section>
    </div>
  );
}