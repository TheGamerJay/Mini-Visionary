import AuthLogo from "./AuthLogo";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white relative overflow-hidden">
      {/* Enhanced background effects */}
      <div className="pointer-events-none absolute -top-60 -left-60 h-[40rem] w-[40rem] rounded-full bg-indigo-600/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-60 -right-60 h-[35rem] w-[35rem] rounded-full bg-purple-600/10 blur-3xl" />
      <div className="pointer-events-none absolute top-1/3 left-1/3 h-[20rem] w-[20rem] rounded-full bg-cyan-500/5 blur-3xl" />

      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="rounded-3xl border border-slate-700/50 bg-slate-900/90 shadow-2xl shadow-black/50 backdrop-blur-xl">
            <div className="p-8 sm:p-10">
              <div className="text-center mb-8">
                <AuthLogo />
                <p className="text-sm text-slate-400 mt-3 font-medium">
                  You Envision it, We Generate it.
                </p>
              </div>

              <div className="text-center mb-8">
                <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-3">
                  {title}
                </h1>
                {subtitle && (
                  <p className="text-slate-400 text-lg">
                    {subtitle}
                  </p>
                )}
              </div>

              <div>{children}</div>
            </div>
          </div>

          {/* footer */}
          <p className="mt-8 text-center text-xs text-slate-500">
            © {new Date().getFullYear()} Mini-Visionary. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}