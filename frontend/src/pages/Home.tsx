import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-8 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <img
              src="/logo.png"
              alt="Mini-Visionary Logo"
              className="h-24 w-auto object-contain"
            />
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-cyan-400 via-indigo-500 to-purple-600 bg-clip-text text-transparent">
            Mini-Visionary
          </h1>
          <p className="text-2xl md:text-3xl text-cyan-300 mt-4 font-semibold">
            You Envision it, We Generate it.
          </p>
          <p className="text-xl md:text-2xl text-cyan-200 mt-6 leading-relaxed">
            Transform your imagination into stunning movie-style posters with AI
          </p>
          <p className="text-lg text-indigo-300 max-w-2xl mx-auto">
            From fantasy epics to sci-fi adventures, create professional posters in seconds.
            Just describe your vision and watch it come to life.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/create"
            className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-cyan-600 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-cyan-500/25"
          >
            Start Creating
          </Link>
          <Link
            to="/gallery"
            className="px-8 py-3 border border-indigo-400 text-indigo-300 font-semibold rounded-lg hover:bg-indigo-900/20 transition-all duration-200"
          >
            View Gallery
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-800 to-indigo-900 border border-indigo-600/30">
          <h3 className="text-xl font-semibold text-cyan-100 mb-2">AI-Powered Generation</h3>
          <p className="text-indigo-300">
            Advanced AI creates stunning, unique posters from your text descriptions in seconds.
          </p>
        </div>

        <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-800 to-indigo-900 border border-indigo-600/30">
          <h3 className="text-xl font-semibold text-cyan-100 mb-2">Multiple Styles</h3>
          <p className="text-indigo-300">
            Fantasy, sci-fi, horror, romance, action, anime - create in any genre you love.
          </p>
        </div>

        <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-800 to-indigo-900 border border-indigo-600/30">
          <h3 className="text-xl font-semibold text-cyan-100 mb-2">Personal Library</h3>
          <p className="text-indigo-300">
            Save, organize, and manage all your creations in your private poster library.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-gradient-to-br from-slate-900 to-indigo-950 rounded-3xl p-8 md:p-12 border border-indigo-800/30">
        <h2 className="text-3xl font-bold text-center text-cyan-100 mb-8">How It Works</h2>
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
      <section className="text-center bg-gradient-to-r from-cyan-600 via-indigo-700 to-purple-800 text-white rounded-3xl p-8 md:p-12 border border-indigo-500/30 shadow-2xl shadow-cyan-500/10">
        <h2 className="text-3xl font-bold mb-4 text-cyan-100">Ready to Create Your First Poster?</h2>
        <p className="text-xl opacity-90 mb-8 max-w-2xl mx-auto text-indigo-200">
          Join thousands of creators who've brought their stories to life with AI-powered poster generation.
        </p>
        <Link
          to="/create"
          className="inline-block px-8 py-3 bg-gradient-to-r from-cyan-400 to-indigo-500 text-black font-semibold rounded-lg hover:from-cyan-300 hover:to-indigo-400 transition-all duration-200 shadow-lg hover:shadow-cyan-400/25"
        >
          Start Creating Now
        </Link>
      </section>
    </div>
  );
}