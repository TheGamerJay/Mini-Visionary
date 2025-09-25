// Drop your logo in /public/logo.png OR pass a different src prop.
export default function AuthLogo({ src = "/logo.png", title = "Mini-Visionary" }) {
  return (
    <div className="flex items-center gap-3">
      <img
        src={src}
        alt={`${title} logo`}
        className="h-10 w-10 rounded-xl ring-1 ring-cyan-400/40 object-contain"
        onError={(e) => { e.currentTarget.style.display = "none"; }}
      />
      <span className="text-lg tracking-wide font-semibold bg-gradient-to-r from-cyan-300 via-cyan-100 to-indigo-300 bg-clip-text text-transparent">
        {title}
      </span>
    </div>
  );
}