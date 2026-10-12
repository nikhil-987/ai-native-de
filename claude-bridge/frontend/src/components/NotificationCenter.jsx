import { useState, useRef, useEffect } from "react";
import {
  LuBell,
  LuBellRing,
  LuBookOpen,
  LuCheck,
  LuCheckCheck,
  LuCircleAlert,
  LuCircleCheck,
  LuCircleX,
  LuDatabase,
  LuExternalLink,
  LuFilter,
  LuTrash2,
  LuWorkflow,
  LuX,
} from "react-icons/lu";
import { Button, IconButton, Pill, cx } from "./ui.jsx";

function artifactIcon(type) {
  if (type === "pipeline") return LuWorkflow;
  if (type === "semantic_model") return LuDatabase;
  return LuBookOpen;
}

function statusBadge(status) {
  if (status === "completed" || status === "succeeded") {
    return { tone: "good", icon: LuCircleCheck, label: "Succeeded" };
  }
  if (status === "failed") {
    return { tone: "bad", icon: LuCircleX, label: "Failed" };
  }
  return { tone: "accent", icon: LuCircleAlert, label: "In Progress" };
}

export function NotificationCenter({
  notifications = [],
  unreadCount = 0,
  onMarkAsRead,
  onMarkAllAsRead,
  onRemove,
  onClearAll,
  onNavigateToMonitoring,
}) {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("all");
  const panelRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const filtered = notifications.filter((n) => {
    if (filter === "unread") return !n.read;
    if (filter === "notebook") return n.type === "notebook";
    if (filter === "pipeline") return n.type === "pipeline";
    if (filter === "semantic_model") return n.type === "semantic_model";
    return true;
  });

  return (
    <div className="relative inline-block" ref={panelRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={cx(
          "relative flex size-8 items-center justify-center rounded-lg border transition shadow-xs cursor-pointer",
          open
            ? "border-accent bg-accent-soft text-accent"
            : "border-line bg-panel text-muted hover:border-accent hover:text-ink"
        )}
        aria-label="Execution notifications"
        title={unreadCount > 0 ? `${unreadCount} unread execution notifications` : "Execution notifications"}
      >
        {unreadCount > 0 ? (
          <LuBellRing className="text-base text-accent animate-pulse" />
        ) : (
          <LuBell className="text-base" />
        )}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex min-w-[17px] h-[17px] items-center justify-center rounded-full bg-accent px-1 text-[10px] font-bold text-white shadow-xs">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className="absolute right-0 top-full mt-2 z-50 w-[min(420px,94vw)] rounded-2xl border border-line bg-panel shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-line bg-bg/50 px-4 py-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-ink">Execution Notifications</h3>
              {unreadCount > 0 && (
                <span className="rounded-full bg-accent/20 px-2 py-0.5 text-[11px] font-bold text-accent">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={onMarkAllAsRead}
                  title="Mark all as read"
                  className="text-[11px] h-7 px-2 text-accent hover:bg-accent-soft"
                >
                  <LuCheckCheck /> Read All
                </Button>
              )}
              {notifications.length > 0 && (
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={onClearAll}
                  title="Clear all notifications"
                  className="text-[11px] h-7 px-2 text-muted hover:text-bad hover:bg-bad-soft"
                >
                  <LuTrash2 /> Clear
                </Button>
              )}
              <IconButton
                size="xs"
                onClick={() => setOpen(false)}
                aria-label="Close notifications"
                className="size-7"
              >
                <LuX />
              </IconButton>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 overflow-x-auto border-b border-line bg-bg/30 px-3 py-2 text-xs no-scrollbar">
            {[
              { id: "all", label: "All" },
              { id: "unread", label: `Unread (${unreadCount})` },
              { id: "notebook", label: "Notebooks" },
              { id: "pipeline", label: "Pipelines" },
              { id: "semantic_model", label: "Semantic Models" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={cx(
                  "whitespace-nowrap rounded-md px-2.5 py-1 text-[11.5px] font-medium transition cursor-pointer",
                  filter === f.id
                    ? "bg-accent text-white shadow-xs"
                    : "text-muted hover:bg-line/40 hover:text-ink"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Notification List */}
          <div className="max-h-[380px] overflow-y-auto overscroll-contain divide-y divide-line/60">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-center text-muted">
                <LuBell className="mb-2 text-3xl opacity-40" />
                <p className="text-xs font-semibold text-ink">No notifications in this view</p>
                <p className="mt-0.5 text-[11px] text-muted">
                  Fabric notebook, pipeline, and semantic model execution events will be logged here.
                </p>
              </div>
            ) : (
              filtered.map((n) => {
                const Icon = artifactIcon(n.type);
                const badge = statusBadge(n.status);
                const BadgeIcon = badge.icon;

                return (
                  <div
                    key={n.id}
                    onClick={() => onMarkAsRead(n.id)}
                    className={cx(
                      "group relative flex items-start gap-3 p-3.5 transition cursor-pointer",
                      n.read ? "bg-panel hover:bg-bg/60 opacity-80" : "bg-accent-soft/20 hover:bg-accent-soft/35"
                    )}
                  >
                    {/* Status / Artifact Icon */}
                    <div className="relative mt-0.5 shrink-0">
                      <div className="grid size-8 place-items-center rounded-lg bg-code text-ink border border-line">
                        <Icon className="text-sm text-accent" />
                      </div>
                      <BadgeIcon
                        className={cx(
                          "absolute -bottom-1 -right-1 size-3.5 rounded-full bg-panel p-0.5",
                          badge.tone === "good" ? "text-good" : badge.tone === "bad" ? "text-bad" : "text-accent"
                        )}
                      />
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-1">
                        <h4 className={cx("text-xs leading-snug font-bold", n.read ? "text-ink" : "text-ink")}>
                          {n.title}
                        </h4>
                        <span className="shrink-0 text-[10.5px] text-muted whitespace-nowrap">
                          {n.timestamp}
                        </span>
                      </div>

                      <p className="mt-1 text-[11.5px] text-muted leading-relaxed line-clamp-2">
                        {n.message}
                      </p>

                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px]">
                        {n.item && (
                          <span className="rounded bg-code px-1.5 py-0.5 font-mono text-[10.5px] text-ink">
                            {n.item}
                          </span>
                        )}
                        {n.duration && (
                          <span className="text-muted">⏱ {n.duration}</span>
                        )}
                        <Pill tone={badge.tone} className="!text-[9px] !py-0 !px-1.5">
                          {badge.label}
                        </Pill>
                        {onNavigateToMonitoring && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onMarkAsRead(n.id);
                              setOpen(false);
                              onNavigateToMonitoring();
                            }}
                            className="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                          >
                            <span>Monitor</span>
                            <LuExternalLink className="text-[10px]" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Delete button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(n.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-muted hover:text-bad transition cursor-pointer"
                      title="Remove notification"
                    >
                      <LuX className="text-xs" />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && onNavigateToMonitoring && (
            <div className="border-t border-line bg-bg/40 p-2.5 text-center">
              <button
                onClick={() => {
                  setOpen(false);
                  onNavigateToMonitoring();
                }}
                className="w-full text-center text-xs font-semibold text-accent hover:underline cursor-pointer"
              >
                Open Full Monitoring Dashboard →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function NotificationToast({ toast, onDismiss, onNavigateToMonitoring }) {
  if (!toast) return null;

  const Icon = artifactIcon(toast.type);
  const badge = statusBadge(toast.status);

  return (
    <div className="fixed bottom-5 right-5 z-50 flex max-w-sm items-start gap-3 rounded-2xl border border-line bg-panel p-3.5 shadow-2xl animate-in slide-in-from-bottom-5 duration-200">
      <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
        <Icon className="text-lg" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <b className="truncate text-xs font-bold text-ink">{toast.title}</b>
          <button
            onClick={onDismiss}
            className="text-muted hover:text-ink cursor-pointer"
            aria-label="Dismiss toast"
          >
            <LuX className="text-xs" />
          </button>
        </div>
        <p className="mt-1 text-[11.5px] text-muted line-clamp-2 leading-snug">
          {toast.message}
        </p>
        <div className="mt-2 flex items-center justify-between">
          <Pill tone={badge.tone} className="!text-[9.5px]">
            {badge.label}
          </Pill>
          {onNavigateToMonitoring && (
            <button
              onClick={() => {
                onDismiss();
                onNavigateToMonitoring();
              }}
              className="text-xs font-semibold text-accent hover:underline cursor-pointer"
            >
              View in Monitoring →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
