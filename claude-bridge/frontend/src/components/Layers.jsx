import { LAYER_COLORS, LAYER_SHORT } from "../lib/sections.js";
import { cx } from "./ui.jsx";

// Bronze / Silver / Gold / Orchestrator / Semantic chips, each in its layer colour, styled by status.
const LAYERS = ["bronze", "silver", "gold", "orchestrator", "semantic_model"];

const CHIP_STATE = {
  done: "border-layer bg-layer text-on-color",
  in_progress: "border-layer bg-layer-soft text-layer animate-glow",
  submitted: "border-layer bg-layer-soft text-layer animate-glow",
  running: "border-layer bg-layer-soft text-layer animate-glow",
  skipped: "border-dashed border-layer text-layer opacity-80",
  failed: "border-bad bg-bad-soft text-bad",
  pending: "border-layer text-layer opacity-50",
};

export function LayerChips({ stages, className }) {
  return (
    <div className={cx("flex flex-wrap gap-1.5", className)}>
      {LAYERS.map((k) => {
        const st = stages?.[k] || "pending";
        return (
          <span key={k} title={`${LAYER_SHORT[k]}: ${st.replace("_", " ")}`}
            className={cx("rounded-full border-[1.5px] px-2.5 py-0.5 text-[11px] font-bold tracking-wide", LAYER_COLORS[k], CHIP_STATE[st] || CHIP_STATE.pending)}>
            {LAYER_SHORT[k]}
          </span>
        );
      })}
    </div>
  );
}

export function ProgressBar({ pct, className }) {
  const v = Math.max(0, Math.min(100, Number(pct) || 0));
  return (
    <div className={cx("h-1.5 overflow-hidden rounded-full bg-code", className)} role="progressbar" aria-valuenow={v} aria-valuemin={0} aria-valuemax={100}>
      <i className="block h-full rounded-full bg-[linear-gradient(90deg,var(--bronze),var(--silver),var(--gold))] transition-[width] duration-500" style={{ width: `${v}%` }} />
    </div>
  );
}
