import AuthLogo from "./AuthLogo";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* soft radial glows */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-cyan-600/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-[28rem] w-[28rem] rounded-full bg-indigo-700/25 blur-3xl" />

      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 shadow-[0_0_50px_-12px_rgba(0,255,255,0.35)] backdrop-blur-xl">
            <div className="p-7 sm:p-8">
              <div className="flex items-center justify-between mb-4">
                <AuthLogo />
                <span className="text-xs text-cyan-300/70">v1.0</span>
              </div>
              <p className="text-center text-sm text-cyan-300/80 mb-6 italic">
                You Envision it, We Generate it.
              </p>

              <h1 className="text-2xl sm:text-3xl font-bold text-center bg-gradient-to-r from-cyan-300 via-indigo-200 to-cyan-300 bg-clip-text text-transparent">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-2 text-center text-sm text-cyan-200/70">
                  {subtitle}
                </p>
              )}

              <div className="mt-6">{children}</div>
            </div>
          </div>

          {/* footer */}
          <p className="mt-6 text-center text-xs text-cyan-200/60">
            © {new Date().getFullYear()} Mini-Visionary. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}