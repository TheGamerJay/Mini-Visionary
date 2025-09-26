import React, { useEffect, useMemo, useRef, useState } from "react";
import { Send, StopCircle, RotateCcw, Trash2, Settings2, ChevronDown, Copy, Loader2, User, Bot, Sparkles } from "lucide-react";
import AdSlot from "../components/AdSlot";

export type ChatMessage = { role: "user" | "assistant" | "system"; content: string; ts?: number };

const PRESETS: Record<string, { label: string; system: string; emoji: string }> = {
  friendly: { label: "Friendly Helper", emoji: "😊", system: "You are a warm, friendly, and helpful assistant for Mini-Visionary. Be concise, positive, and practical." },
  creative: { label: "Creative Brainstorm", emoji: "✨", system: "You are a wildly creative brainstorming partner. Generate vivid, original ideas and iterate quickly." },
  tutor:    { label: "Technical Tutor", emoji: "📘", system: "You are a patient technical tutor. Explain clearly, step-by-step, with short examples." },
  concise:  { label: "Concise Expert",  emoji: "🔧", system: "You are a brief, precise expert. Answer in the fewest words that fully solve the task." },
};

const MODELS = ["gpt-4o-mini","gpt-4.1-mini","gpt-4o","gpt-4.1"] as const;

export default function Chat() {
  const [preset, setPreset] = useState<keyof typeof PRESETS>("friendly");
  const [systemOpen, setSystemOpen] = useState(false);
  const [system, setSystem] = useState(PRESETS.friendly.system);
  const [temperature, setTemperature] = useState(0.7);
  const [model, setModel] = useState<(typeof MODELS)[number]>("gpt-4o-mini");
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: "assistant", content: "Hi! I'm your friendly helper. How can I assist today?", ts: Date.now() }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stopped, setStopped] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // ads / entitlement
  const [adFree, setAdFree] = useState(false);

  // attachments
  const [attachFile, setAttachFile] = useState<File | null>(null);
  const [attachUrl, setAttachUrl] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const jwt = useMemo(() => localStorage.getItem("jwt_token") || "", []);

  // load entitlement + hydrate chat per preset
  useEffect(() => {
    (async () => {
      try {
        if (!jwt) return;
        const r = await fetch("/api/me", { headers: { Authorization: `Bearer ${jwt}` } });
        const js = await r.json();
        if (js?.ok) setAdFree(!!js.ad_free);
      } catch {}
    })();
  }, [jwt]);

  useEffect(() => {
    const key = `mdp:chatmini:${preset}`;
    const saved = localStorage.getItem(key);
    if (saved) {
      const s = JSON.parse(saved);
      setMessages(s.messages || [{ role: "assistant", content: "Hi! I'm your friendly helper. How can I assist today?" }]);
      setSystem(s.system || PRESETS[preset].system);
      setTemperature(s.temperature ?? 0.7);
      setModel(s.model || "gpt-4o-mini");
    } else {
      setMessages([{ role: "assistant", content: "Hi! I'm your friendly helper. How can I assist today?" }]);
      setSystem(PRESETS[preset].system);
      setTemperature(0.7);
      setModel("gpt-4o-mini");
    }
  }, [preset]);

  useEffect(() => {
    const key = `mdp:chatmini:${preset}`;
    localStorage.setItem(key, JSON.stringify({ messages, system, temperature, model }));
  }, [messages, system, temperature, model, preset]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const presetList = useMemo(() => Object.entries(PRESETS).map(([k, v]) => ({ value: k, label: `${v.emoji} ${v.label}` })), []);

  function addMessage(m: ChatMessage) {
    setMessages((prev) => [...prev, { ...m, ts: Date.now() }]);
  }

  async function uploadReferenceToS3(file: File) {
    const ext = (file.name.split(".").pop() || "png").toLowerCase();
    const res = await fetch("/api/storage/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}) },
      body: JSON.stringify({ ext, contentType: file.type || "image/png" })
    });
    const js = await res.json();
    if (!js?.ok) throw new Error("presign failed");
    await fetch(js.uploadUrl, { method: "PUT", body: file, headers: { "Content-Type": file.type || "image/png" } });
    return js.publicUrl as string;
  }

  async function send() {
    if (!input.trim() && !attachUrl) return;
    if (loading) return;

    // /poster command → call generator and insert image bubble
    const posterCmd = input.trim().startsWith("/poster");
    if (posterCmd) {
      const prompt = input.trim().replace(/^\/poster\s*/i, "");
      addMessage({ role: "user", content: input.trim() || "(poster)" });
      setInput("");

      try {
        const res = await fetch("/api/poster/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json", ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}) },
          body: JSON.stringify({ prompt, style: "chat", size: "1200x1500" })
        });
        const js = await res.json();
        if (js?.ok && js.url) {
          addMessage({ role: "assistant", content: `Here you go!` });
          setMessages(prev => [...prev, { role: "assistant", content: `[image]${js.url}` }]);
        } else {
          addMessage({ role: "assistant", content: `⚠️ Generation failed: ${js?.error || "unknown error"}` });
        }
      } catch {
        addMessage({ role: "assistant", content: "⚠️ Network error while generating poster." });
      }
      return;
    }

    // Normal chat (may include reference image)
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
    addMessage(userMsg);
    setInput("");

    const userParts: any[] = [];
    if (userMsg.content) userParts.push({ type: "text", text: userMsg.content });
    if (attachUrl) userParts.push({ type: "image_url", image_url: attachUrl });

    const payload = {
      model,
      temperature,
      system,
      messages: [...messages, userMsg].map(({ role, content }) => ({ role, content })),
      parts: userParts, // backend consumes this for multimodal
    };

    abortRef.current = new AbortController();
    setLoading(true);
    setStopped(false);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abortRef.current.signal,
      });
      const js = await res.json();
      if (js?.ok && js.message) addMessage({ role: "assistant", content: js.message });
      else addMessage({ role: "assistant", content: `⚠️ Error: ${js?.error || "Unknown error"}` });
    } catch (e: any) {
      if (e.name === "AbortError") addMessage({ role: "assistant", content: "(stopped)" });
      else addMessage({ role: "assistant", content: "⚠️ Network error." });
    } finally {
      setLoading(false);
      abortRef.current = null;
      // one-turn reference
      setAttachFile(null);
      setAttachUrl(null);
    }
  }

  function stop() { setStopped(true); abortRef.current?.abort(); }
  function retryLast() {
    if (loading) return;
    const lastUser = [...messages].reverse().find(m => m.role === "user");
    if (lastUser) { setInput(lastUser.content); setTimeout(send, 0); }
  }
  function clearChat() { setMessages([{ role: "assistant", content: "Chat cleared. How can I help now?", ts: Date.now() }]); }
  function copyText(id: number, text: string) { navigator.clipboard.writeText(text).then(() => { setCopiedId(String(id)); setTimeout(()=>setCopiedId(null), 1100); }); }

  const assistantCountUpTo = (idx: number) => messages.slice(0, idx + 1).filter(m => m.role === "assistant").length;

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="pointer-events-none fixed -top-40 -left-40 h-96 w-96 rounded-full bg-cyan-600/20 blur-3xl" />
      <div className="pointer-events-none fixed -bottom-40 -right-40 h-[28rem] w-[28rem] rounded-full bg-indigo-700/25 blur-3xl" />

      <header className="sticky top-0 z-20 backdrop-blur bg-black/40 border-b border-cyan-500/15">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Mini-Visionary" className="h-9 w-9 rounded-xl" onError={(e: any) => e.currentTarget.style.display = 'none'} />
            <div>
              <div className="text-sm text-cyan-200/80">Mini-Visionary</div>
              <div className="text-xs text-cyan-200/60">ChatMini</div>
            </div>
          </div>
          {!adFree && (
            <button
              onClick={async () => {
                const t = localStorage.getItem("jwt_token");
                const r = await fetch("/api/ads/checkout", { method: "POST", headers: t ? { Authorization: `Bearer ${t}` } : {} });
                const js = await r.json();
                if (js?.ok && js.url) window.location.href = js.url;
                else alert("Checkout unavailable");
              }}
              className="px-3 py-2 rounded-md border border-cyan-500/40 text-sm hover:bg-cyan-900/20"
              title="Remove ads for $5/month"
            >Remove Ads — $5/mo</button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6 grid md:grid-cols-[280px_1fr] gap-6">
        {/* Sidebar */}
        <aside className="space-y-4">
          <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-4">
            <label className="block text-sm mb-1 text-cyan-200/80">Preset</label>
            <div className="relative">
              <select value={preset} onChange={(e) => setPreset(e.target.value as any)}
                className="w-full appearance-none p-3 pr-9 rounded-lg bg-black/60 border border-cyan-600 focus:ring-2 focus:ring-indigo-400 outline-none">
                {Object.entries(PRESETS).map(([k, v]) => <option key={k} value={k}>{v.emoji} {v.label}</option>)}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cyan-300 pointer-events-none" />
            </div>

            <div className="mt-4">
              <label className="block text-sm mb-1 text-cyan-200/80">Model</label>
              <select value={model} onChange={(e) => setModel(e.target.value as any)} className="w-full p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none">
                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>

            <div className="mt-4">
              <label className="block text-sm mb-1 text-cyan-200/80">Temperature: {temperature.toFixed(2)}</label>
              <input type="range" min={0} max={1} step={0.05} value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))} className="w-full" />
            </div>

            <details className="mt-4 rounded-lg border border-indigo-600/60 bg-black/40 p-3" open={systemOpen} onToggle={(e) => setSystemOpen((e.target as HTMLDetailsElement).open)}>
              <summary className="cursor-pointer select-none text-cyan-200/90 flex items-center gap-2"><Settings2 className="h-4 w-4" /> System Prompt</summary>
              <textarea value={system} onChange={(e) => setSystem(e.target.value)} className="mt-3 w-full h-28 p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none" />
              <div className="text-[11px] text-cyan-200/70 mt-1">Controls the assistant's behavior.</div>
            </details>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button onClick={retryLast} className="px-3 py-2 rounded-md border border-cyan-500/40 text-sm hover:bg-cyan-900/20 inline-flex items-center gap-2"><RotateCcw className="h-4 w-4" />Retry</button>
              <button onClick={clearChat} className="px-3 py-2 rounded-md border border-indigo-500/60 text-sm hover:bg-indigo-900/30 inline-flex items-center gap-2"><Trash2 className="h-4 w-4" />Clear</button>
            </div>
          </div>
        </aside>

        {/* Chat */}
        <section className="flex flex-col min-h-[70vh]">
          <div ref={scrollerRef} className="flex-1 rounded-2xl border border-cyan-500/25 bg-gradient-to-br from-indigo-950/70 via-black/80 to-cyan-950/70 p-4 overflow-y-auto">
            <div className="space-y-4">
              {messages.map((m, i) => (
                <React.Fragment key={i}>
                  <ChatBubble index={i} m={m} onCopy={(id, text) => navigator.clipboard.writeText(text)} />
                  {/* Ad every 2 assistant replies */}
                  {!adFree && m.role === "assistant" && (messages.slice(0, i + 1).filter(x => x.role === "assistant").length % 2 === 0) && (
                    <AdSlot slot="1234567890" className="my-3 border border-cyan-500/20 rounded-xl bg-black/40" />
                  )}
                </React.Fragment>
              ))}
              {loading && <div className="flex items-center gap-2 text-cyan-200/80 text-sm"><Loader2 className="h-4 w-4 animate-spin" /> Thinking…</div>}
            </div>
          </div>

          <form onSubmit={(e) => { e.preventDefault(); send(); }} className="mt-4 rounded-2xl border border-cyan-500/25 bg-black/50 p-3">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                {attachUrl && (
                  <div className="mb-2 text-[11px] text-cyan-200/80 flex items-center gap-2">
                    <img src={attachUrl} className="h-6 w-6 rounded object-cover border border-cyan-500/40" />
                    <span>Reference attached</span>
                    <button type="button" onClick={() => { setAttachFile(null); setAttachUrl(null); }} className="underline">remove</button>
                  </div>
                )}
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message… (try /poster neon skyline) • Shift+Enter = newline"
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                  className="w-full max-h-48 min-h-[48px] p-3 rounded-lg bg-black/60 border border-indigo-600 focus:ring-2 focus:ring-cyan-400 outline-none"
                />
                <div className="mt-2 flex items-center gap-3 text-[11px] text-cyan-200/70">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input type="file" accept="image/*" className="hidden"
                      onChange={async (e) => {
                        const f = e.target.files?.[0]; if (!f) return;
                        setAttachFile(f);
                        try { const url = await uploadReferenceToS3(f); setAttachUrl(url); }
                        catch { alert("Upload failed"); setAttachFile(null); }
                      }}
                    />
                    <span className="px-2 py-1 rounded-md border border-cyan-500/40 hover:bg-cyan-900/20">Attach image</span>
                  </label>
                  <span>• Use <b>/poster</b> to generate images</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={stop} disabled={!loading} title="Stop" className="p-2 rounded-lg border border-indigo-500/60 hover:bg-indigo-900/30 disabled:opacity-50"><StopCircle className="h-5 w-5" /></button>
                <button type="submit" disabled={loading || (!input.trim() && !attachUrl)} className="px-4 py-2 rounded-lg font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 disabled:opacity-60 inline-flex items-center gap-2"><Send className="h-4 w-4" /> Send</button>
              </div>
            </div>
            <div className="mt-2 text-[11px] text-cyan-200/70 flex items-center gap-2"><Sparkles className="h-3 w-3" /> Tip: presets change tone; edit System Prompt for custom behavior.</div>
          </form>
        </section>
      </main>

      <footer className="py-8 text-center text-xs text-cyan-200/60">© {new Date().getFullYear()} Mini-Visionary</footer>
    </div>
  );
}

function ChatBubble({ m, index, onCopy }: { m: ChatMessage; index: number; onCopy: (id: number, text: string) => void }) {
  const isUser = m.role === "user";
  const content = m.content.startsWith("[image]") ? (
    <img src={m.content.replace("[image]", "")} alt="image" className="mt-1 rounded-lg border border-cyan-500/30 max-w-full" />
  ) : m.content;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] rounded-2xl px-3 py-2 border ${isUser ? "bg-cyan-900/30 border-cyan-500/40" : "bg-black/50 border-indigo-600/40"}`}>
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-1 text-xs text-cyan-200/70">
            {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
            <span>{isUser ? "You" : "Assistant"}</span>
          </div>
          <button onClick={() => onCopy(index, typeof content === "string" ? content : m.content)} className="text-[10px] text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1"><Copy className="h-3 w-3" /> Copy</button>
        </div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed text-cyan-50">{content}</div>
      </div>
    </div>
  );
}