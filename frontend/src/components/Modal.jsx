import React from "react";

export default function Modal({ open, title, message, onClose, action }) {
  if (!open) return null;
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,.5)",
      display: "grid", placeItems: "center", zIndex: 50
    }}>
      <div style={{
        width: "min(520px, 92vw)", background: "#0b0f19", color: "#fff",
        borderRadius: 14, padding: 20, boxShadow: "0 10px 30px rgba(0,0,0,.6)"
      }}>
        <h3 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>{title}</h3>
        <p style={{ marginTop: 10, lineHeight: 1.5, color: "#c7d2fe" }}>{message}</p>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
          {action}
          <button onClick={onClose} style={{
            padding: "10px 14px", borderRadius: 10, border: "1px solid #374151",
            background: "transparent", color: "#e5e7eb"
          }}>Close</button>
        </div>
      </div>
    </div>
  );
}