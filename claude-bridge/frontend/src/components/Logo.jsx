import { useState } from "react";
import { cx } from "./ui.jsx";

// The ADROSONIC logo, served from frontend/public (copied into frontend/dist on build):
//   adrosonic-sidebar.png    - wide horizontal logo for sidenav
//   adrosonic-mark.png       - circular 3D sphere mark for avatars and AI icons
//   adrosonic-horizontal.png - alternate horizontal lockup
//   adrosonic-logo.png       - full stacked logo
const SOURCES = {
  sidenav: ["/adrosonic-sidebar.png", "/adrosonic-horizontal.png", "/adrosonic-logo.png"],
  horizontal: ["/adrosonic-sidebar.png", "/adrosonic-horizontal.png", "/adrosonic-logo.png"],
  logo: ["/adrosonic-sidebar.png", "/adrosonic-horizontal.png", "/adrosonic-logo.png"],
  mark: ["/adrosonic-mark.png", "/adrosonic-sidebar.png", "/adrosonic-logo.png"],
};

export function Logo({ variant = "horizontal", className, fallback = null }) {
  const sources = SOURCES[variant] || SOURCES.horizontal;
  const [i, setI] = useState(0);

  const defaultFallback = (
    <div className="flex items-center gap-2">
      <span className="font-extrabold uppercase tracking-wider text-white text-base">ADROSONIC</span>
    </div>
  );

  if (i >= sources.length) return fallback || defaultFallback;

  return (
    <img
      src={sources[i]}
      alt="ADROSONIC"
      draggable={false}
      onError={() => setI((n) => n + 1)}
      className={cx("block object-contain", className)}
    />
  );
}

// Square tile for avatars and empty states: the logo mark on a navy tile
export function LogoTile({ className }) {
  const [err, setErr] = useState(false);

  return (
    <span
      className={cx(
        "grid shrink-0 place-items-center overflow-hidden rounded-lg bg-[var(--brand-navy-900,#152337)] p-0.5 ring-1 ring-white/10 shadow-sm",
        className
      )}
    >
      <img
        src={err ? "/adrosonic-logo.png" : "/adrosonic-mark.png"}
        alt="ADROSONIC AI"
        draggable={false}
        onError={() => setErr(true)}
        className="size-full object-contain"
      />
    </span>
  );
}
