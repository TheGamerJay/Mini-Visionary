import React, { useState, useEffect } from "react";
import PosterStyleGallery from "../components/PosterStyleGallery";
import Modal from "../components/Modal";
import AdSlot from "../components/AdSlot";

export default function CreatePoster() {
  const API_BASE = import.meta.env.VITE_API_BASE || "";
  const [style, setStyle] = useState("fantasy");
  const [prompt, setPrompt] = useState("");
  const [file, setFile] = useState(null);
  const [imgUrl, setImgUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [credits, setCredits] = useState(null);
  const [adFree, setAdFree] = useState(false);
  const [showAd, setShowAd] = useState(false);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalMsg, setModalMsg] = useState("");
  const openModal = (title, message) => {
    setModalTitle(title);
    setModalMsg(message);
    setModalOpen(true);
  };

  useEffect(() => {
    // Fetch credits and ad-free status
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    // Get user info and ad-free status
    fetch(`${API_BASE}/api/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => {
        if (d?.ok) {
          setCredits(d.credits ?? 0);
          setAdFree(!!d.ad_free);
        }
      })
      .catch(() => {});
  }, []);

  const onGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setImgUrl("");

    const token = localStorage.getItem("jwt_token");
    if (!token) {
      setLoading(false);
      openModal("Authentication Required", "Please log in to generate posters.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/poster/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: prompt,
          style: style
        })
      });
      const data = await res.json();
      setLoading(false);

      if (res.status === 402 || data?.error === "insufficient_credits") {
        openModal("You need more credits",
          "Each poster costs 10 credits. Visit the store to buy a pack or subscribe.");
        return;
      }

      if (!data.ok) {
        // Show backend-provided reason (e.g., safety policy)
        openModal("We couldn't generate that",
          data.error || "The request was blocked by safety filters. Your credits have been refunded.");
        return;
      }

      setImgUrl(data.url);
      setShowAd(true); // Show ad after successful generation

      // Refresh credits
      fetch(`${API_BASE}/api/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(d => {
          if (d?.ok) setCredits(d.credits ?? 0);
        });
    } catch (err) {
      setLoading(false);
      openModal("Something went wrong", "Network or server error. Please try again.");
    }
  };

  return (
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Create Your Poster</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          If you can dream it, we can poster it.
        </p>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", justifyContent: "center", marginBottom: "20px" }}>
          {!adFree && (
            <button
              onClick={async () => {
                const token = localStorage.getItem("jwt_token");
                const r = await fetch("/api/ads/checkout", {
                  method: "POST",
                  headers: token ? { Authorization: `Bearer ${token}` } : {}
                });
                const js = await r.json();
                if (js?.ok && js.url) window.location.href = js.url;
                else alert("Checkout unavailable");
              }}
              className="btn-secondary"
              style={{ fontSize: "12px", padding: "6px 12px" }}
            >
              Remove Ads — $5/mo
            </button>
          )}
          <div style={{
            background: "rgba(6, 182, 212, 0.1)",
            border: "1px solid rgba(99, 102, 241, 0.3)",
            borderRadius: "20px",
            padding: "8px 16px",
            color: "#06b6d4",
            fontWeight: "600"
          }}>
            Credits: <strong>{credits ?? "…"}</strong>
          </div>
        </div>

      <form onSubmit={onGenerate} className="login-form" style={{ gap: 20 }}>
        <div>
          <label htmlFor="style">Choose a Poster Style</label>
          <PosterStyleGallery
            onSelect={(val) => setStyle(val)}
            selectedStyle={style}
          />
          <p style={{
            marginTop: "12px",
            fontSize: "0.9rem",
            color: "#a1a1aa"
          }}>
            Selected Style: <strong style={{ color: "#06b6d4" }}>{style}</strong>
          </p>
        </div>

        <label htmlFor="prompt">Description (optional if you upload an image)</label>
        <textarea
          id="prompt"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., a cosmic demi-human standing in star-lit ruins, cinematic lighting"
          style={{ resize: "vertical" }}
        />

        <label htmlFor="file">Upload Image (optional)</label>
        <input
          id="file"
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <button
          type="submit"
          disabled={loading || credits < 10}
          className={loading || credits < 10 ? "" : "btn-primary"}
          style={loading || credits < 10 ? {
            padding: "14px 20px",
            borderRadius: 12,
            border: "1px solid rgba(153, 153, 153, 0.3)",
            background: "rgba(153, 153, 153, 0.3)",
            color: "#666",
            fontWeight: 700,
            fontSize: "1.1rem",
            cursor: "not-allowed",
            width: "100%"
          } : {}}
          title="Costs 10 credits per generate"
        >
          {loading ? "Generating…" :
           credits < 10 ? "Need More Credits" :
           "Generate (10 credits)"}
        </button>

        {credits !== null && credits < 10 && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/35 text-red-200 rounded-xl text-sm text-center">
            You need at least 10 credits to generate a poster.
            <a href="/store" style={{ color: "#3b82f6", marginLeft: "8px" }}>
              Buy credits →
            </a>
          </div>
        )}
      </form>

      {imgUrl && (
        <div style={{
          marginTop: 32,
          background: "rgba(255, 255, 255, 0.02)",
          padding: "24px",
          borderRadius: "16px",
          border: "1px solid rgba(255, 255, 255, 0.1)"
        }}>
          <h3 style={{
            marginTop: 0,
            color: "#0ea5e9",
            marginBottom: "16px"
          }}>
            ✨ Your Generated Poster
          </h3>
          <img
            src={imgUrl}
            alt="Generated poster"
            style={{
              width: "100%",
              maxWidth: "600px",
              height: "auto",
              borderRadius: 12,
              border: "1px solid rgba(255, 255, 255, 0.1)"
            }}
          />

          {/* Ad after successful generation */}
          {!adFree && showAd && (
            <div style={{ marginTop: "16px" }}>
              <AdSlot
                slot="1234567890"
                className="border border-cyan-500/20 rounded-xl bg-black/40 p-3"
              />
            </div>
          )}
        </div>
      )}
      </div>

      <div className="site-banner bottom"></div>
      <div className="login-footer">
        <div className="login-tagline">You Envision it, We Generate it.</div>
      </div>

      {/* Modal */}
      <Modal
        open={modalOpen}
        title={modalTitle}
        message={modalMsg}
        onClose={() => setModalOpen(false)}
        action={(
          <a href="/store" style={{
            display: modalTitle.includes("credits") ? "inline-block" : "none",
            padding: "10px 14px", borderRadius: 10, background: "#22c55e", color: "#0b0f19",
            textDecoration: "none", fontWeight: 800
          }}>
            Get Credits
          </a>
        )}
      />
    </div>
  );
}