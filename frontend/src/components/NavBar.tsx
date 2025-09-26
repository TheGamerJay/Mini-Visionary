import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

type Me = { id:number; email:string; display_name?:string; avatar_url?:string } | null;

async function getMe(): Promise<Me> {
  try { const r = await fetch("/api/auth/whoami",{credentials:"include"}); return r.ok? r.json():null; }
  catch { return null; }
}
async function post(url:string, body?:any) {
  const r = await fetch(url,{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined});
  return r.ok;
}

export default function NavBar(){
  const [me,setMe]=useState<Me>(null);
  const [open,setOpen]=useState(false);
  const navigate = useNavigate();

  useEffect(()=>{ getMe().then(setMe); },[]);
  async function logout(){
    if(await post("/api/auth/logout")){ setMe(null); navigate("/login"); }
  }
  const A = ({to,label}:{to:string;label:string})=>(
    <Link to={to} className="px-4 py-2 rounded-lg hover:bg-gradient-to-r hover:from-indigo-600/20 hover:to-cyan-600/20 text-sm font-medium text-slate-200 hover:text-white transition-all duration-200 border border-transparent hover:border-indigo-400/30">{label}</Link>
  );
  const avatar = (me?.display_name?.[0]||me?.email?.[0]||"U").toUpperCase();

  return (
    <header className="fixed top-0 w-full border-b border-indigo-500/20 bg-slate-900/95 backdrop-blur-md shadow-lg z-50">
      <div className="mx-auto max-w-7xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to={me ? "/home" : "/"} className="flex items-center gap-2">
            <img
              src="/logo.png"
              alt="Mini-Visionary Logo"
              className="h-9 w-9 rounded-2xl object-contain"
            />
            <span className="font-semibold text-cyan-100">Mini-Visionary</span>
          </Link>
          <nav className="hidden md:flex items-center gap-1 ml-6">
            <A to="/home" label="Home" />
            <A to="/chat" label="Chat" />
            <A to="/create" label="Create" />
            <A to="/store" label="Store" />
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {!me ? (
            <div className="hidden sm:flex items-center gap-1">
              <A to="/login" label="Log in" />
              <Link to="/signup" className="px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 text-white text-sm font-medium hover:from-indigo-700 hover:to-cyan-700 transition-all duration-200 shadow-lg hover:scale-105">Sign up</Link>
            </div>
          ) : (
            <>
              <A to="/wallet" label="Wallet" />
              <div className="relative">
                <button onClick={()=>setOpen(v=>!v)} className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 grid place-items-center overflow-hidden">
                  {me?.avatar_url ? <img src={me.avatar_url} className="h-full w-full object-cover" /> : <span className="text-sm font-semibold text-white">{avatar}</span>}
                </button>
                {open && (
                  <div className="absolute right-0 mt-2 w-48 rounded-2xl border border-indigo-700 bg-slate-800 shadow-lg p-1">
                    <Link to="/profile" className="block px-3 py-2 rounded-xl hover:bg-indigo-700/30 text-sm font-medium text-cyan-200 hover:text-cyan-100">Profile</Link>
                    <Link to="/settings" className="block px-3 py-2 rounded-xl hover:bg-indigo-700/30 text-sm font-medium text-cyan-200 hover:text-cyan-100">Settings</Link>
                    <button onClick={logout} className="w-full text-left px-3 py-2 rounded-xl hover:bg-red-700/30 text-sm font-medium text-cyan-200 hover:text-red-300">Logout</button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}