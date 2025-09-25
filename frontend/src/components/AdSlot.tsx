import { useEffect, useRef } from "react";

declare global {
  interface Window {
    adsbygoogle?: any[];
  }
}

interface AdSlotProps {
  slot: string;
  format?: string;
  responsive?: boolean;
  className?: string;
  hidden?: boolean;
}

export default function AdSlot({
  slot,
  format = "auto",
  responsive = true,
  className = "",
  hidden = false
}: AdSlotProps) {
  const ref = useRef<HTMLModElement>(null);

  useEffect(() => {
    if (!hidden) {
      try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } catch (error) {
        console.warn("AdSense failed to load:", error);
      }
    }
  }, [hidden]);

  if (hidden) return null;

  return (
    <ins
      className={`adsbygoogle block ${className}`}
      style={{ display: "block" }}
      data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
      data-ad-slot={slot}
      data-ad-format={format}
      {...(responsive ? { "data-full-width-responsive": "true" } : {})}
      ref={ref as any}
    />
  );
}