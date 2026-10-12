import { useState, useEffect, useCallback, useRef } from "react";

const STORAGE_KEY = "adrosonic_studio_notifications_v1";

const SEED_NOTIFICATIONS = [
  {
    id: "notif-seed-4",
    title: "Direct Lake Semantic Model Synced",
    message: "Direct Lake semantic model Customer_360_DirectLake successfully refreshed and synchronized with Gold Delta tables.",
    type: "semantic_model",
    status: "completed",
    item: "Customer_360_DirectLake",
    stage: "semantic_model",
    run_id: "run-dl-902",
    duration: "14s",
    timestamp: "3 minutes ago",
    read: false,
  },
  {
    id: "notif-seed-3",
    title: "Data Factory Orchestrator Deployed",
    message: "Pipeline Automobile_Claims_Orchestrator deployed with sequential activities (Bronze, Silver, Gold) and retry triggers.",
    type: "pipeline",
    status: "completed",
    item: "Automobile_Claims_Orchestrator",
    stage: "orchestrator",
    run_id: "run-pipe-412",
    duration: "18s",
    timestamp: "12 minutes ago",
    read: false,
  },
  {
    id: "notif-seed-2",
    title: "Silver PySpark Cleansing Completed",
    message: "Notebook Silver_Marine executed. Deduplication, regex cleaning, and business rules applied to 125,000 rows.",
    type: "notebook",
    status: "completed",
    item: "Silver_Marine",
    stage: "silver",
    run_id: "run-s05-77a",
    duration: "1m 12s",
    timestamp: "25 minutes ago",
    read: true,
  },
  {
    id: "notif-seed-1",
    title: "Bronze Notebook Ingestion Succeeded",
    message: "Notebook Bronze_Marine loaded raw files into Lakehouse Bronze delta table bronze_marine.",
    type: "notebook",
    status: "completed",
    item: "Bronze_Marine",
    stage: "bronze",
    run_id: "run-b05-12c",
    duration: "45s",
    timestamp: "40 minutes ago",
    read: true,
  },
];

export function useNotifications(flow) {
  const [notifications, setNotifications] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      // fallback
    }
    return SEED_NOTIFICATIONS;
  });

  const [activeToast, setActiveToast] = useState(null);
  const seenRuns = useRef(new Set());

  // Save to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } catch (e) {
      // ignore
    }
  }, [notifications]);

  const addNotification = useCallback((notif) => {
    const id = notif.id || `notif-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const newEntry = {
      id,
      timestamp: "Just now",
      read: false,
      ...notif,
    };
    setNotifications((prev) => [newEntry, ...prev.filter((n) => n.id !== id)]);
    setActiveToast(newEntry);
  }, []);

  // Monitor flow.runs for new execution events
  useEffect(() => {
    if (!flow?.runs || !Array.isArray(flow.runs)) return;

    for (const r of flow.runs) {
      const key = `${r.run_id || r.item}-${r.status}`;
      if (!seenRuns.current.has(key)) {
        seenRuns.current.add(key);

        // Determine type
        const type = r.stage === "orchestrator" ? "pipeline"
          : r.stage === "semantic_model" ? "semantic_model"
          : "notebook";

        const title = r.status === "completed"
          ? `${type === "pipeline" ? "Pipeline" : type === "semantic_model" ? "Semantic Model" : "Notebook"} Succeeded: ${r.item || r.stage}`
          : r.status === "failed"
          ? `${type === "pipeline" ? "Pipeline" : type === "semantic_model" ? "Semantic Model" : "Notebook"} Failed: ${r.item || r.stage}`
          : `${type === "pipeline" ? "Pipeline" : type === "semantic_model" ? "Semantic Model" : "Notebook"} Running: ${r.item || r.stage}`;

        const message = r.status === "completed"
          ? `Execution of ${r.item || r.stage} completed successfully in Fabric. Output Delta tables are updated.`
          : r.status === "failed"
          ? `Execution of ${r.item || r.stage} encountered an error. Check driver logs in Monitoring.`
          : `Execution of ${r.item || r.stage} was submitted to Microsoft Fabric Livy / Data Factory cluster.`;

        addNotification({
          title,
          message,
          type,
          status: r.status || "completed",
          item: r.item || r.stage,
          stage: r.stage,
          run_id: r.run_id,
          duration: r.duration || "45s",
        });
      }
    }
  }, [flow?.runs, addNotification]);

  const markAsRead = useCallback((id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const dismissToast = useCallback(() => {
    setActiveToast(null);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    notifications,
    unreadCount,
    activeToast,
    dismissToast,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
  };
}
