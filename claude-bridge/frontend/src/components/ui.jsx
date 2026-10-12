import { LuLoaderCircle } from "react-icons/lu";

// Shared building blocks aligned with ADROSONIC AI Data Engineering Studio Branding Specification v1.0.

export const cx = (...classes) => classes.filter(Boolean).join(" ");

export function Spinner({ className }) {
  return <LuLoaderCircle aria-hidden className={cx("shrink-0 animate-spin", className)} />;
}

const BUTTON_BASE =
  "inline-flex cursor-pointer select-none items-center justify-center gap-2 font-medium transition " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brand-cyan-300,#00CCFF)] disabled:cursor-default disabled:opacity-45";

const BUTTON_VARIANT = {
  primary: "bg-[var(--brand-blue-600,#144074)] text-white shadow-sm hover:brightness-110 active:brightness-95 disabled:hover:brightness-100",
  ghost: "border border-line bg-transparent text-ink hover:bg-code",
  subtle: "bg-code text-ink hover:bg-line/70",
  danger: "bg-[var(--status-failed,#D64545)] text-white hover:brightness-110",
  good: "bg-[var(--status-success,#1FAE5C)] text-white hover:brightness-110",
  nav: "border border-nav-line bg-transparent text-nav-ink hover:bg-[var(--brand-navy-800,#1A2C47)]",
  link: "bg-transparent p-0 text-[var(--brand-blue-400,#2D79A6)] underline-offset-2 hover:underline",
};

const BUTTON_SIZE = {
  xs: "rounded-md px-2 py-0.5 text-xs",
  sm: "rounded-lg px-3 py-1.5 text-xs",
  md: "rounded-lg px-4 py-2 text-sm",
  lg: "rounded-xl px-7 py-3 text-base",
};

export function Button({ variant = "subtle", size = "md", className, type = "button", ...props }) {
  return <button type={type} className={cx(BUTTON_BASE, BUTTON_VARIANT[variant], variant !== "link" && BUTTON_SIZE[size], className)} {...props} />;
}

export function IconButton({ className, type = "button", ...props }) {
  return (
    <button type={type}
      className={cx("grid size-9 shrink-0 cursor-pointer place-items-center rounded-lg text-lg text-ink transition hover:bg-code disabled:opacity-45 focus-visible:outline-2 focus-visible:outline-[var(--brand-cyan-300,#00CCFF)]", className)}
      {...props} />
  );
}

// Cards use ~8px corner radius (rounded-lg) and neutral-200 border (#E8E8E8) as per Spec section 6.2
export function Card({ as: Tag = "section", className, ...props }) {
  return <Tag className={cx("min-w-0 rounded-lg border border-line bg-panel p-4 shadow-card", className)} {...props} />;
}

export function CardTitle({ icon: Icon, className, children }) {
  return (
    <h3 className={cx("mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted", className)}>
      {Icon && <Icon className="text-sm" />}{children}
    </h3>
  );
}

// Status Tones per Branding Specification Section 4
export const TONES = {
  good: "bg-[#e4f7ed] text-[var(--status-success,#1FAE5C)] dark:bg-[#10332c] dark:text-[var(--brand-teal-400,#23E3BA)]",
  bad: "bg-[#fceaea] text-[var(--status-failed,#D64545)] dark:bg-[#381a1f] dark:text-[#ff7676]",
  info: "bg-[#e8f3f9] text-[var(--brand-blue-400,#2D79A6)] dark:bg-[#162f45] dark:text-[var(--brand-blue-400,#2D79A6)]",
  warn: "bg-[#e6f8f8] text-[var(--brand-teal-600,#03B7B7)] dark:bg-[#133338] dark:text-[var(--brand-teal-600,#03B7B7)]",
  neutral: "bg-code text-[var(--status-draft,#8A8F98)]",
  pending: "border border-[var(--status-pending,#B8BCC4)] bg-transparent text-[var(--status-draft,#8A8F98)]",
  layer: "bg-layer-soft text-layer",
};

export function Pill({ tone = "neutral", className, children, title }) {
  return (
    <span title={title}
      className={cx("inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide", TONES[tone], className)}>
      {children}
    </span>
  );
}

// Run / item status → pill tone mapping per Spec Section 4
export const STATUS_TONE = {
  deployed: "info", running: "info", refreshing: "info", submitted: "info", in_progress: "info",
  ready_to_deploy: "warn",
  succeeded: "good", refreshed: "good", completed: "good", done: "good", generated: "good",
  failed: "bad", cancelled: "bad",
  skipped: "neutral", pending: "pending", draft: "neutral",
};

export function StatusDot({ state }) {
  const color = state === "on" ? "bg-good ring-good/20" : state === "off" ? "bg-bad ring-bad/20" : state === "wait" ? "bg-nav-mark ring-transparent animate-blink" : "bg-nav-muted/50 ring-transparent";
  return <span className={cx("size-2 shrink-0 rounded-full ring-[3px]", color)} />;
}

export function Alert({ tone = "bad", className, children }) {
  return <div className={cx("rounded-lg px-3 py-2 text-[13px]", TONES[tone], className)}>{children}</div>;
}

export function Field({ label, hint, children }) {
  return (
    <label className="flex flex-col gap-1 text-[12.5px] text-muted font-medium">
      <span className="flex flex-wrap items-baseline gap-x-2">{label}{hint && <code className="text-[11px] text-muted/80">{hint}</code>}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full min-w-0 rounded-lg border border-line bg-bg px-3 py-2 text-[13.5px] text-ink outline-none transition placeholder:text-muted/70 focus:border-[var(--brand-blue-400,#2D79A6)] focus:ring-2 focus:ring-[var(--brand-blue-400,#2D79A6)]/20 disabled:opacity-60";
