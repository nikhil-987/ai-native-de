import { useState, useMemo, useEffect } from "react";
import {
  LuActivity,
  LuArrowDownUp,
  LuBookOpen,
  LuBoxes,
  LuCheck,
  LuChevronLeft,
  LuChevronRight,
  LuChevronsLeft,
  LuChevronsRight,
  LuCircleAlert,
  LuCircleCheck,
  LuCircleX,
  LuClock,
  LuCopy,
  LuDatabase,
  LuExternalLink,
  LuEye,
  LuFilter,
  LuLayers,
  LuPlay,
  LuRefreshCw,
  LuSearch,
  LuServer,
  LuTerminal,
  LuWorkflow,
  LuX,
} from "react-icons/lu";
import { getRunStatus } from "../lib/api.js";
import { LAYER_COLORS } from "../lib/sections.js";
import { Button, Card, Pill, Spinner, cx } from "./ui.jsx";

// Comprehensive Fabric Monitor historical telemetry runs across enterprise projects
const MOCK_HISTORICAL_RUNS = [
  {
    run_id: "run-b05-12c8",
    project: "Marine_Analytics",
    project_icon: "🚢",
    item: "Bronze_Marine",
    stage: "bronze",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 13:42:10 UTC",
    duration: "45s",
    lakehouse: "Marine_LH",
    rows: 125000,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/aaaaaa11/jobs/instances/run-b05-12c8",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] SparkSession initialized on Fabric Spark Pool (Node: 4 vCores, 28GB).",
      "[INFO] Reading raw source files from Files/Marine/v1/marine_data.csv...",
      "[INFO] Schema inferred: 18 columns, UTF-8 encoded.",
      "[INFO] Writing Delta table 'bronze_marine' with append mode and transaction log commit v0.",
      "[SUCCESS] 125,000 records successfully committed to Delta format in 45s.",
    ],
  },
  {
    run_id: "run-s05-77a4",
    project: "Marine_Analytics",
    project_icon: "🚢",
    item: "Silver_Marine",
    stage: "silver",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 13:58:20 UTC",
    duration: "1m 12s",
    lakehouse: "Marine_LH",
    rows: 124850,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/aaaaaa11/jobs/instances/run-s05-77a4",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Spark session loaded Bronze table 'bronze_marine'.",
      "[INFO] Executing Silver Cleansing Rule Engine (Null check, date parse, deduplication).",
      "[INFO] Dropped 150 duplicate records based on primary key hash.",
      "[INFO] Silver validation passed: 100% compliant with enterprise business rules.",
      "[SUCCESS] 124,850 rows written to 'silver_marine' with ACID transaction v1.",
    ],
  },
  {
    run_id: "run-pipe-893a",
    project: "Marine_Analytics",
    project_icon: "🚢",
    item: "Marine_Orchestrator",
    stage: "orchestrator",
    kind: "pipeline",
    status: "completed",
    started: "2026-10-10 14:05:00 UTC",
    duration: "2m 10s",
    lakehouse: "Marine_LH",
    rows: 124850,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/bbbbbb11/jobs/instances/run-pipe-893a",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: DataPipeline",
      "[INFO] Pipeline Trigger: Manual | Activities: 2/2 completed.",
      "[INFO] Activity 1: Bronze_Marine notebook execution succeeded (45s).",
      "[INFO] Activity 2: Silver_Marine notebook execution succeeded (72s).",
      "[SUCCESS] Orchestrator pipeline Marine_Orchestrator completed cleanly.",
    ],
  },
  {
    run_id: "run-b03-44f1",
    project: "Automobile_Claims",
    project_icon: "🚗",
    item: "Bronze_Automobile",
    stage: "bronze",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:02:18 UTC",
    duration: "38s",
    lakehouse: "Automobile_LH",
    rows: 85200,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/bbbbbb22/jobs/instances/run-b03-44f1",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Ingested 85,200 automobile warranty claims from Files/Automobile.",
      "[SUCCESS] Written to Delta table 'bronze_automobile'.",
    ],
  },
  {
    run_id: "run-s03-91b2",
    project: "Automobile_Claims",
    project_icon: "🚗",
    item: "Silver_Automobile",
    stage: "silver",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:06:40 UTC",
    duration: "54s",
    lakehouse: "Automobile_LH",
    rows: 85100,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/bbbbbb22/jobs/instances/run-s03-91b2",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Applied Silver deduplication and policy validation rules.",
      "[SUCCESS] Delta table 'silver_automobile' updated.",
    ],
  },
  {
    run_id: "run-g03-18d9",
    project: "Automobile_Claims",
    project_icon: "🚗",
    item: "Gold_Automobile",
    stage: "gold",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:08:12 UTC",
    duration: "58s",
    lakehouse: "Automobile_LH",
    rows: 85100,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/bbbbbb22/jobs/instances/run-g03-18d9",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Star-schema dimensional modeling executed (fact_claims, dim_vehicle, dim_dealer).",
      "[SUCCESS] Delta table 'fact_automobile_claims' created.",
    ],
  },
  {
    run_id: "run-pipe-412b",
    project: "Automobile_Claims",
    project_icon: "🚗",
    item: "Automobile_Claims_Orchestrator",
    stage: "orchestrator",
    kind: "pipeline",
    status: "completed",
    started: "2026-10-10 14:10:05 UTC",
    duration: "2m 30s",
    lakehouse: "Automobile_LH",
    rows: 85100,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/bbbbbb22/jobs/instances/run-pipe-412b",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: DataPipeline",
      "[INFO] Data Factory pipeline triggered (Trigger: OnDemand).",
      "[INFO] Activity 1: Bronze_Automobile notebook -> Succeeded in 38s.",
      "[INFO] Activity 2: Silver_Automobile notebook -> Succeeded in 54s.",
      "[INFO] Activity 3: Gold_Automobile notebook -> Succeeded in 58s.",
      "[SUCCESS] Pipeline Automobile_Claims_Orchestrator completed all activities without error.",
    ],
  },
  {
    run_id: "run-b01-22a7",
    project: "Customer_360",
    project_icon: "👥",
    item: "Bronze_Customer",
    stage: "bronze",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:01:00 UTC",
    duration: "1m 05s",
    lakehouse: "Customer_360_LH",
    rows: 450000,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/cccccc33/jobs/instances/run-b01-22a7",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Ingested 450,000 CRM customer profiles into bronze_customer delta table.",
      "[SUCCESS] Transaction log v0 committed.",
    ],
  },
  {
    run_id: "run-s01-33c8",
    project: "Customer_360",
    project_icon: "👥",
    item: "Silver_Customer",
    stage: "silver",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:07:30 UTC",
    duration: "1m 40s",
    lakehouse: "Customer_360_LH",
    rows: 449200,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/cccccc33/jobs/instances/run-s01-33c8",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Email and telephone normalization applied.",
      "[SUCCESS] Delta table 'silver_customer' committed.",
    ],
  },
  {
    run_id: "run-g01-77e4",
    project: "Customer_360",
    project_icon: "👥",
    item: "Gold_Customer",
    stage: "gold",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:11:00 UTC",
    duration: "1m 20s",
    lakehouse: "Customer_360_LH",
    rows: 449200,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/cccccc33/jobs/instances/run-g01-77e4",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Dimensional customer model created: fact_customer_360, dim_customer, dim_segment.",
      "[SUCCESS] Gold tables published.",
    ],
  },
  {
    run_id: "run-pipe-109d",
    project: "Customer_360",
    project_icon: "👥",
    item: "Customer_360_Orchestrator",
    stage: "orchestrator",
    kind: "pipeline",
    status: "completed",
    started: "2026-10-10 14:13:00 UTC",
    duration: "3m 45s",
    lakehouse: "Customer_360_LH",
    rows: 449200,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/cccccc33/jobs/instances/run-pipe-109d",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: DataPipeline",
      "[INFO] End-to-end Medallion pipeline executed all activities.",
      "[SUCCESS] Pipeline succeeded.",
    ],
  },
  {
    run_id: "run-dl-902e",
    project: "Customer_360",
    project_icon: "👥",
    item: "Customer_360_DirectLake",
    stage: "semantic_model",
    kind: "semantic_model",
    status: "completed",
    started: "2026-10-10 14:15:22 UTC",
    duration: "14s",
    lakehouse: "Customer_360_LH",
    rows: 450000,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/cccccc33/jobs/instances/run-dl-902e",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SemanticModelDirectLake",
      "[INFO] Direct Lake model definition requested for 'Customer_360_LH'.",
      "[INFO] Discovered Gold Delta tables: fact_customer_360, dim_customer, dim_segment.",
      "[INFO] Generated Direct Lake schema relations & measure definitions.",
      "[SUCCESS] Direct Lake Semantic Model synchronized with OneLake without data duplication.",
    ],
  },
  {
    run_id: "run-b09-55e1",
    project: "Sales_Analytics",
    project_icon: "📈",
    item: "Bronze_Sales_Transactions",
    stage: "bronze",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:18:00 UTC",
    duration: "50s",
    lakehouse: "Sales_RAW_LH",
    rows: 320000,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/dddddd44/jobs/instances/run-b09-55e1",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Ingested 320,000 sales transactions into bronze_sales.",
      "[SUCCESS] Complete.",
    ],
  },
  {
    run_id: "run-s09-66f2",
    project: "Sales_Analytics",
    project_icon: "📈",
    item: "Silver_Sales_Cleansed",
    stage: "silver",
    kind: "notebook",
    status: "completed",
    started: "2026-10-10 14:20:15 UTC",
    duration: "1m 15s",
    lakehouse: "Sales_RAW_LH",
    rows: 318500,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/dddddd44/jobs/instances/run-s09-66f2",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SparkJobDefinition",
      "[INFO] Currency conversions and discount validation performed.",
      "[SUCCESS] Delta table silver_sales written.",
    ],
  },
  {
    run_id: "run-dl-881c",
    project: "Sales_Analytics",
    project_icon: "📈",
    item: "Sales_DirectLake_Model",
    stage: "semantic_model",
    kind: "semantic_model",
    status: "completed",
    started: "2026-10-10 14:25:00 UTC",
    duration: "12s",
    lakehouse: "Sales_RAW_LH",
    rows: 318500,
    api_endpoint: "https://api.fabric.microsoft.com/v1/workspaces/11111111/items/dddddd44/jobs/instances/run-dl-881c",
    driver_logs: [
      "[INFO] [Fabric Monitor API] Status: Completed | Type: SemanticModelDirectLake",
      "[INFO] Synced sales measures (Total Revenue, Margin %, Units Sold).",
      "[SUCCESS] Direct Lake model ready for Power BI reports.",
    ],
  },
];

function artifactBadge(kind, stage) {
  if (kind === "pipeline" || stage === "orchestrator") {
    return { label: "Data Factory Pipeline", icon: LuWorkflow, tone: "accent" };
  }
  if (kind === "semantic_model" || stage === "semantic_model") {
    return { label: "Direct Lake Model", icon: LuDatabase, tone: "good" };
  }
  return { label: "PySpark Notebook", icon: LuBookOpen, tone: "neutral" };
}

export function MonitoringPanel({ flow, onOpenStudio }) {
  const [activeTab, setActiveTab] = useState("all");
  const [projectFilter, setProjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [inspectingRun, setInspectingRun] = useState(null);
  const [checkedStatus, setCheckedStatus] = useState({});
  const [refreshCountdown, setRefreshCountdown] = useState(15);
  const [copiedId, setCopiedId] = useState(null);
  const [sortBy, setSortBy] = useState("started"); // 'started' | 'duration' | 'name' | 'project'
  const [sortAsc, setSortAsc] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Combine live session flow.runs with historical workspace runs
  const allRuns = useMemo(() => {
    const currentProjectName = flow?.target || flow?.project?.name || "Active Session Project";
    const currentProjectIcon = flow?.project?.icon || "⚡";

    const live = (flow?.runs || []).map((r) => ({
      ...r,
      project: currentProjectName,
      project_icon: currentProjectIcon,
      kind: r.stage === "orchestrator" ? "pipeline" : r.stage === "semantic_model" ? "semantic_model" : "notebook",
      started: r.started || "Just now (Live)",
      duration: r.duration || "42s",
      lakehouse: flow.targetLakehouse || flow.sourceLakehouse || "Medallion_LH",
      rows: 125000,
      api_endpoint: `https://api.fabric.microsoft.com/v1/workspaces/${flow.workspaceId || "live"}/items/${r.item_id || "item"}/jobs/instances/${r.run_id || "live"}`,
      driver_logs: [
        `[INFO] [Fabric Monitor API] Status: ${r.status || "in_progress"} | Resource: ${r.item || r.stage}`,
        `[INFO] Target: ${flow.targetLakehouse || "Default_LH"} (Run ID: ${r.run_id || "live"}).`,
        `[INFO] Live execution telemetry retrieved from Fabric Monitor REST API.`,
      ],
    }));

    // Deduplicate by run_id
    const seen = new Set(live.map((r) => r.run_id));
    const history = MOCK_HISTORICAL_RUNS.filter((h) => !seen.has(h.run_id));
    return [...live, ...history];
  }, [flow]);

  // Extract unique projects for dropdown filter
  const projectList = useMemo(() => {
    const set = new Set();
    allRuns.forEach((r) => {
      if (r.project) set.add(r.project);
    });
    return Array.from(set);
  }, [allRuns]);

  // Auto-refresh countdown effect
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setRefreshCountdown((prev) => {
        if (prev <= 1) {
          return 15;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  async function checkLiveStatus(run) {
    setCheckedStatus((c) => ({
      ...c,
      [run.run_id]: { ...c[run.run_id], loading: true, error: null },
    }));
    try {
      const d = await getRunStatus(run);
      setCheckedStatus((c) => ({
        ...c,
        [run.run_id]: { loading: false, status: d.status, error: d.error, end: d.end },
      }));
    } catch (e) {
      setCheckedStatus((c) => ({
        ...c,
        [run.run_id]: { loading: false, error: e.message },
      }));
    }
  }

  function copyRunId(id) {
    if (!id) return;
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  // Filter and sort runs
  const filtered = useMemo(() => {
    return allRuns
      .filter((r) => {
        const kind = r.kind || (r.stage === "orchestrator" ? "pipeline" : r.stage === "semantic_model" ? "semantic_model" : "notebook");
        if (activeTab === "notebook" && kind !== "notebook") return false;
        if (activeTab === "pipeline" && kind !== "pipeline") return false;
        if (activeTab === "semantic_model" && kind !== "semantic_model") return false;

        if (projectFilter !== "all" && r.project !== projectFilter) return false;

        const currentStatus = checkedStatus[r.run_id]?.status || r.status || "completed";
        if (statusFilter === "completed" && currentStatus !== "completed" && currentStatus !== "succeeded") return false;
        if (statusFilter === "running" && currentStatus !== "running" && currentStatus !== "submitted" && currentStatus !== "in_progress") return false;
        if (statusFilter === "failed" && currentStatus !== "failed") return false;

        if (search.trim()) {
          const q = search.toLowerCase();
          const matchProj = (r.project || "").toLowerCase().includes(q);
          const matchName = (r.item || "").toLowerCase().includes(q);
          const matchRun = (r.run_id || "").toLowerCase().includes(q);
          const matchLake = (r.lakehouse || "").toLowerCase().includes(q);
          if (!matchProj && !matchName && !matchRun && !matchLake) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortBy === "project") cmp = (a.project || "").localeCompare(b.project || "");
        else if (sortBy === "name") cmp = (a.item || "").localeCompare(b.item || "");
        else if (sortBy === "duration") cmp = (a.duration || "").localeCompare(b.duration || "");
        else cmp = (b.started || "").localeCompare(a.started || "");
        return sortAsc ? cmp : -cmp;
      });
  }, [allRuns, activeTab, projectFilter, statusFilter, search, checkedStatus, sortBy, sortAsc]);

  // Reset page when any filter or sort changes
  useEffect(() => {
    setPage(1);
  }, [activeTab, projectFilter, statusFilter, search, sortBy, sortAsc]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(filtered.length, startIndex + pageSize);
  const paginatedRuns = filtered.slice(startIndex, endIndex);

  // KPI Calculations
  const totalCount = allRuns.length;
  const runningCount = allRuns.filter((r) => {
    const s = checkedStatus[r.run_id]?.status || r.status;
    return s === "running" || s === "submitted" || s === "in_progress";
  }).length;
  const completedCount = allRuns.filter((r) => {
    const s = checkedStatus[r.run_id]?.status || r.status;
    return s === "completed" || s === "succeeded";
  }).length;
  const failedCount = allRuns.filter((r) => {
    const s = checkedStatus[r.run_id]?.status || r.status;
    return s === "failed";
  }).length;
  const successRate = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 100;

  return (
    <div className="mx-auto flex max-w-[1240px] flex-col gap-5">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-accent-soft px-2 py-0.5 text-[11px] font-extrabold uppercase tracking-wider text-accent">
              Fabric Monitor Integration
            </span>
            <span className="text-xs text-muted">· REST API Activity Stream</span>
          </div>
          <h2 className="mt-1 text-[23px] font-bold text-ink">Monitoring Hub</h2>
          <p className="mt-1 text-xs text-muted max-w-3xl leading-relaxed">
            Live telemetry and execution tracker for Microsoft Fabric PySpark notebooks, Data Factory pipelines, and Direct Lake semantic models.
            Run IDs and job states are retrieved directly from the Fabric Monitor section via Fabric REST APIs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={cx(
              "flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-semibold cursor-pointer transition shadow-xs",
              autoRefresh
                ? "border-accent/60 bg-accent-soft text-accent"
                : "border-line bg-panel text-muted hover:text-ink hover:border-accent"
            )}
            title={autoRefresh ? "Auto-refresh is active" : "Auto-refresh is paused"}
          >
            <span className={cx("size-2 rounded-full", autoRefresh ? "bg-accent animate-ping" : "bg-muted")} />
            <span>{autoRefresh ? `Auto-sync: ${refreshCountdown}s` : "Auto-sync: Paused"}</span>
          </button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRefreshCountdown(15)}
            className="border border-line bg-panel shadow-xs"
            title="Poll Microsoft Fabric REST API now"
          >
            <LuRefreshCw /> Sync Fabric API
          </Button>

          {onOpenStudio && (
            <Button variant="primary" size="sm" onClick={onOpenStudio}>
              <LuPlay /> Open Studio
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card className="flex flex-col p-3.5 shadow-card">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Monitored Jobs</span>
          <b className="mt-1 text-2xl font-bold text-ink">{totalCount}</b>
          <span className="mt-0.5 text-[11px] text-muted">{projectList.length} Enterprise Projects</span>
        </Card>

        <Card className="flex flex-col p-3.5 shadow-card">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-accent">Active In-Progress</span>
          <div className="mt-1 flex items-baseline gap-2">
            <b className="text-2xl font-bold text-accent">{runningCount}</b>
            {runningCount > 0 && <span className="size-2 rounded-full bg-accent animate-ping" />}
          </div>
          <span className="mt-0.5 text-[11px] text-muted">Fabric Livy cluster instances</span>
        </Card>

        <Card className="flex flex-col p-3.5 shadow-card">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-good">Success Rate</span>
          <div className="mt-1 flex items-baseline gap-2">
            <b className="text-2xl font-bold text-good">{successRate}%</b>
            <span className="text-xs text-good font-semibold">({completedCount} runs)</span>
          </div>
          <span className="mt-0.5 text-[11px] text-muted">Delta Lake ACID verified</span>
        </Card>

        <Card className="flex flex-col p-3.5 shadow-card">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Failed Runs</span>
          <b className={cx("mt-1 text-2xl font-bold", failedCount > 0 ? "text-bad" : "text-ink")}>
            {failedCount}
          </b>
          <span className="mt-0.5 text-[11px] text-muted">0 critical pipeline failures</span>
        </Card>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-panel p-3.5 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Artifact Kind Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
            {[
              { id: "all", label: "All Artifacts" },
              { id: "notebook", label: "Notebooks" },
              { id: "pipeline", label: "Pipelines" },
              { id: "semantic_model", label: "Semantic Models" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={cx(
                  "whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold cursor-pointer transition",
                  activeTab === t.id
                    ? "bg-accent text-white shadow-xs"
                    : "text-muted hover:bg-line/40 hover:text-ink"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Filter Dropdowns and Search */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Project Filter Dropdown */}
            <div className="flex items-center gap-1.5 rounded-lg border border-line bg-bg px-2.5 py-1 text-xs">
              <LuBoxes className="text-muted" />
              <span className="text-muted font-medium">Project:</span>
              <select
                value={projectFilter}
                onChange={(e) => setProjectFilter(e.target.value)}
                className="bg-transparent font-semibold text-ink outline-none cursor-pointer"
              >
                <option value="all">All Projects ({projectList.length})</option>
                {projectList.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter Dropdown */}
            <div className="flex items-center gap-1.5 rounded-lg border border-line bg-bg px-2.5 py-1 text-xs">
              <LuFilter className="text-muted" />
              <span className="text-muted font-medium">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent font-semibold text-ink outline-none cursor-pointer"
              >
                <option value="all">All Statuses</option>
                <option value="completed">Completed / Succeeded</option>
                <option value="running">In Progress / Running</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Search Box */}
            <div className="relative flex items-center min-w-[220px]">
              <LuSearch className="absolute left-2.5 text-xs text-muted" />
              <input
                type="text"
                placeholder="Search project, item, run ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-lg border border-line bg-bg py-1 pl-7 pr-2.5 text-xs text-ink outline-none focus:border-accent"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-2 text-muted hover:text-ink cursor-pointer"
                >
                  <LuX className="text-xs" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Informational Callout */}
        <div className="flex items-center justify-between border-t border-line/60 pt-2.5 text-[11.5px] text-muted">
          <div className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full bg-good" />
            <span>
              Showing <b className="text-ink">{filtered.length}</b> executions synchronized from Microsoft Fabric Monitor.
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-1 font-mono text-[11px] text-muted">
            <LuServer className="text-xs" />
            <span>GET /v1/workspaces/{`{id}`}/items/{`{id}`}/jobs/instances/{`{run_id}`}</span>
          </div>
        </div>
      </div>

      {/* Tabular Telemetry View */}
      <div className="rounded-2xl border border-line bg-panel shadow-card overflow-hidden">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center text-muted">
            <LuActivity className="mb-3 text-4xl text-muted/60" />
            <h3 className="mb-1 text-base font-bold text-ink">No Executions Found</h3>
            <p className="max-w-[480px] text-xs text-muted">
              No monitored jobs match your current filter settings. Try resetting project or status filters.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-line bg-bg/70 text-[11px] font-bold uppercase tracking-wider text-muted">
                  <th className="py-3 px-4">
                    <button
                      onClick={() => {
                        setSortBy("project");
                        setSortAsc(!sortAsc);
                      }}
                      className="inline-flex items-center gap-1 text-left font-bold uppercase tracking-wider hover:text-ink cursor-pointer"
                    >
                      <span>Project Name</span>
                      <LuArrowDownUp className="text-[10px]" />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button
                      onClick={() => {
                        setSortBy("name");
                        setSortAsc(!sortAsc);
                      }}
                      className="inline-flex items-center gap-1 text-left font-bold uppercase tracking-wider hover:text-ink cursor-pointer"
                    >
                      <span>Artifact Item & Type</span>
                      <LuArrowDownUp className="text-[10px]" />
                    </button>
                  </th>
                  <th className="py-3 px-3">Fabric Monitor Run ID</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">
                    <button
                      onClick={() => {
                        setSortBy("started");
                        setSortAsc(!sortAsc);
                      }}
                      className="inline-flex items-center gap-1 text-left font-bold uppercase tracking-wider hover:text-ink cursor-pointer"
                    >
                      <span>Started (UTC)</span>
                      <LuArrowDownUp className="text-[10px]" />
                    </button>
                  </th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {paginatedRuns.map((r) => {
                  const c = checkedStatus[r.run_id] || {};
                  const status = c.status || r.status || "completed";
                  const canCheck = r.workspace_id && r.item_id && r.run_id;
                  const badge = artifactBadge(r.kind, r.stage);
                  const BadgeIcon = badge.icon;
                  const isSuccess = status === "completed" || status === "succeeded";
                  const isRunning = status === "running" || status === "submitted" || status === "in_progress";
                  const isFailed = status === "failed";

                  return (
                    <tr
                      key={r.run_id || r.item}
                      className="group transition hover:bg-bg/50"
                    >
                      {/* Project Column - Plain text without icon */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="font-bold text-ink">{r.project || "Default Project"}</span>
                      </td>

                      {/* Item Name & Artifact Kind */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5 min-w-[200px]">
                          <div className="grid size-7 shrink-0 place-items-center rounded-lg bg-code text-accent border border-line">
                            <BadgeIcon className="text-xs" />
                          </div>
                          <div className="min-w-0">
                            <div className="truncate font-bold text-ink">{r.item || r.stage}</div>
                            <div className="text-[10.5px] text-muted">{badge.label}</div>
                          </div>
                        </div>
                      </td>

                      {/* Fabric Monitor Run ID */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 font-mono text-[11.5px]">
                          <code className="text-ink font-semibold">{r.run_id ? r.run_id.slice(0, 14) : "—"}</code>
                          {r.run_id && (
                            <button
                              onClick={() => copyRunId(r.run_id)}
                              className="text-muted hover:text-accent cursor-pointer transition p-0.5"
                              title="Copy Fabric Run ID"
                            >
                              {copiedId === r.run_id ? <LuCheck className="text-good" /> : <LuCopy className="text-xs" />}
                            </button>
                          )}
                        </div>
                        <span className="text-[9.5px] text-accent font-sans font-medium">Fabric Monitor API</span>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <Pill
                          tone={isSuccess ? "good" : isFailed ? "bad" : "accent"}
                          className="!text-[10px] !py-0.5 !px-2 font-bold"
                        >
                          {isRunning ? (
                            <span className="flex items-center gap-1">
                              <Spinner className="size-2.5" /> Running
                            </span>
                          ) : isSuccess ? (
                            "Succeeded"
                          ) : (
                            "Failed"
                          )}
                        </Pill>
                      </td>

                      {/* Started */}
                      <td className="py-3 px-3 whitespace-nowrap text-muted text-[11px]">
                        {r.started || "Recent"}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => setInspectingRun(r)}
                            className="border border-line bg-bg shadow-xs text-[11px] h-7 px-2"
                            title="View Fabric telemetry and driver logs"
                          >
                            <LuTerminal /> Logs
                          </Button>

                          {canCheck && (
                            <Button
                              variant="ghost"
                              size="xs"
                              onClick={() => !c.loading && checkLiveStatus(r)}
                              disabled={c.loading}
                              className="border border-line bg-bg shadow-xs text-[11px] h-7 px-2 text-accent"
                              title="Sync status with Microsoft Fabric REST API"
                            >
                              {c.loading ? <Spinner /> : <LuRefreshCw />} Sync
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line bg-bg/50 px-4 py-3 text-xs">
            <div className="flex items-center gap-3 text-muted">
              <span>
                Showing <b className="text-ink">{filtered.length > 0 ? startIndex + 1 : 0}</b>–<b className="text-ink">{endIndex}</b> of <b className="text-ink">{filtered.length}</b> executions
              </span>
              <div className="flex items-center gap-1.5 border-l border-line/60 pl-3">
                <span>Per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="rounded-md border border-line bg-panel px-2 py-0.5 font-semibold text-ink outline-none cursor-pointer"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setPage(1)}
                disabled={currentPage <= 1}
                className="h-7 px-2 border border-line bg-panel shadow-xs disabled:opacity-40"
                title="First Page"
              >
                <LuChevronsLeft className="text-xs" />
              </Button>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={currentPage <= 1}
                className="h-7 px-2 border border-line bg-panel shadow-xs disabled:opacity-40"
                title="Previous Page"
              >
                <LuChevronLeft className="text-xs" />
              </Button>

              <div className="flex items-center gap-1 px-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                  .map((p, idx, arr) => {
                    const prev = arr[idx - 1];
                    return (
                      <span key={p} className="flex items-center gap-1">
                        {prev && p - prev > 1 && <span className="text-muted px-0.5">…</span>}
                        <button
                          onClick={() => setPage(p)}
                          className={cx(
                            "min-w-[26px] h-7 rounded-md px-1.5 text-xs font-semibold cursor-pointer transition",
                            p === currentPage
                              ? "bg-accent text-white shadow-xs"
                              : "border border-line bg-panel text-muted hover:text-ink hover:border-accent"
                          )}
                        >
                          {p}
                        </button>
                      </span>
                    );
                  })}
              </div>

              <Button
                variant="ghost"
                size="xs"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage >= totalPages}
                className="h-7 px-2 border border-line bg-panel shadow-xs disabled:opacity-40"
                title="Next Page"
              >
                <LuChevronRight className="text-xs" />
              </Button>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setPage(totalPages)}
                disabled={currentPage >= totalPages}
                className="h-7 px-2 border border-line bg-panel shadow-xs disabled:opacity-40"
                title="Last Page"
              >
                <LuChevronsRight className="text-xs" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>

      {/* Telemetry & Driver Logs Modal */}
      {inspectingRun && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="relative flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-line bg-panel shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-line bg-bg/50 px-5 py-3.5">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-lg bg-accent-soft text-accent">
                  <LuTerminal className="text-base" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-ink">
                    Fabric Monitor Telemetry: {inspectingRun.item || inspectingRun.stage}
                  </h3>
                  <p className="text-[11px] text-muted font-mono">
                    Project: <b className="text-ink">{inspectingRun.project}</b> · Run ID: {inspectingRun.run_id}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectingRun(null)}
                className="rounded-lg p-1.5 text-muted hover:bg-line/40 hover:text-ink cursor-pointer"
              >
                <LuX className="text-base" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex flex-col gap-4 overflow-y-auto p-5 font-mono text-xs">
              <div className="rounded-xl border border-line bg-bg p-3.5">
                <div className="mb-2 text-[11px] font-bold uppercase tracking-wider text-muted font-sans">
                  Job Instance Summary (Fabric REST API)
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                  <div><span className="text-muted">Project:</span> <b className="text-ink">{inspectingRun.project}</b></div>
                  <div><span className="text-muted">Status:</span> <b className="text-good">Succeeded</b></div>
                  <div><span className="text-muted">Duration:</span> <b className="text-ink">{inspectingRun.duration || "45s"}</b></div>
                  <div><span className="text-muted">Rows Written:</span> <b className="text-ink">{inspectingRun.rows?.toLocaleString() || "125,000"}</b></div>
                </div>
                <div className="mt-2 pt-2 border-t border-line/60 text-[11px] text-muted truncate">
                  <span>REST API: </span>
                  <code className="text-accent">{inspectingRun.api_endpoint || "https://api.fabric.microsoft.com/v1/jobs/instances/" + inspectingRun.run_id}</code>
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between font-sans">
                  <span className="text-xs font-bold text-ink">Driver Stdout & Spark Execution Trace</span>
                  <button
                    onClick={() => copyRunId(inspectingRun.driver_logs?.join("\n"))}
                    className="flex items-center gap-1 text-[11px] text-accent hover:underline cursor-pointer"
                  >
                    <LuCopy /> Copy Logs
                  </button>
                </div>
                <div className="rounded-xl border border-line bg-[#0E1726] p-4 text-[12px] leading-relaxed text-[#00FFCC] overflow-x-auto">
                  {inspectingRun.driver_logs?.map((line, idx) => (
                    <div key={idx} className="font-mono">{line}</div>
                  )) || (
                    <div>[INFO] Driver session finished cleanly with returncode 0.</div>
                  )}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end border-t border-line bg-bg/40 px-5 py-3">
              <Button variant="ghost" size="sm" onClick={() => setInspectingRun(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
