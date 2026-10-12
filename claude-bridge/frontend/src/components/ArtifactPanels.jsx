import { LuArrowRight, LuExternalLink, LuSquareFunction, LuGitMerge, LuNetwork, LuTable2, LuWorkflow } from "react-icons/lu";
import { STAGES, gateLabel } from "../lib/flow.js";
import { Button, Card, CardTitle, Pill, STATUS_TONE, cx } from "./ui.jsx";

// Latest background run Claude reported for a stage (from ui-state "runs" or the submit message).
const latestRun = (flow, stage) => [...flow.runs].reverse().find((r) => r.stage === stage) || null;

function StatusPill({ status }) {
  if (!status) return null;
  return <Pill tone={STATUS_TONE[status] || "neutral"}>{status}</Pill>;
}

const KV = ({ k, children, title }) => (
  <div className="flex justify-between gap-2.5 border-b border-line py-1.5 text-[13.5px] last:border-b-0">
    <span className="text-muted">{k}</span><b className="break-all text-right font-medium" title={title}>{children}</b>
  </div>
);

// Shown in a tab before the item exists: where it gets built and how far the flow is.
function NotCreated({ title, stageKey, layer, icon: Icon, expectedName, flow, onGoToChat }) {
  const stage = STAGES.find((s) => s.key === stageKey);
  const current = stage.gates.includes(flow.gate);
  return (
    <Card className={cx("mx-auto flex max-w-[640px] flex-col items-center gap-3 px-6 py-9 text-center", layer)}>
      <span className="grid size-14 place-items-center rounded-2xl bg-layer-soft text-3xl text-layer"><Icon /></span>
      <h2 className="text-xl font-bold">{title} not created yet</h2>
      <p className="text-muted">
        {current
          ? <>The flow is currently at <b className="text-ink">{gateLabel(flow.gate)}</b>. Complete this step in the Studio to deploy it.</>
          : <>It is built during this stage, after earlier layers are completed.</>}
      </p>
      {expectedName && <p className="text-muted">It will be named <code>{expectedName}</code>.</p>}
      <div className="flex flex-wrap justify-center gap-1.5">
        {stage.gates.map((g) => (
          <span key={g} title={gateLabel(g)}
            className={cx("rounded-full border px-2.5 py-1 text-xs",
              g === flow.gate ? "border-transparent bg-layer text-on-color" : flow.visited.includes(g) ? "border-transparent bg-good-soft text-good" : "border-line bg-code text-muted")}>
            {gateLabel(g)}
          </span>
        ))}
      </div>
      <Button variant="primary" onClick={onGoToChat}>Go to Studio <LuArrowRight /></Button>
    </Card>
  );
}

function Header({ icon: Icon, title, item, flow }) {
  return (
    <Card className="flex flex-wrap items-center gap-4 border-l-[5px] border-l-layer">
      <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-layer-soft text-2xl text-layer"><Icon /></span>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-layer">{title}</div>
        <h2 className="break-words text-xl font-bold">{item.name}</h2>
        <div className="text-xs text-muted">
          {flow.workspace && <>Workspace {flow.workspace}</>}
          {flow.targetLakehouse && <> · {flow.targetLakehouse}</>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <StatusPill status={item.status} />
        {item.url && <Button variant="ghost" size="sm" onClick={() => window.open(item.url, "_blank", "noopener")}>Open in Fabric <LuExternalLink /></Button>}
      </div>
    </Card>
  );
}

export function OrchestratorPanel({ flow, onGoToChat }) {
  const item = flow.orchestrator;
  if (!item) {
    return (
      <NotCreated title="Orchestrator pipeline" stageKey="orchestrator" layer="orch" icon={LuWorkflow} flow={flow} onGoToChat={onGoToChat}
        expectedName={flow.target ? `${flow.target}_Medallion_Orchestrator` : null} />
    );
  }
  const activities = item.activities?.length
    ? item.activities
    : flow.target ? [`Bronze_${flow.target}`, `Silver_${flow.target}`, `Gold_${flow.target}`, "Refresh_Semantic_Model"] : [];
  const layerOf = (a) => (/^bronze/i.test(a) ? "bronze" : /^silver/i.test(a) ? "silver" : /^gold/i.test(a) ? "gold" : /semantic/i.test(a) ? "semantic" : "orch");
  const bgRun = latestRun(flow, "orchestrator");
  const run = item.last_run || (bgRun && { status: bgRun.status, start: bgRun.started, duration: bgRun.duration, run_id: bgRun.run_id });
  return (
    <div className="orch mx-auto flex max-w-[1040px] flex-col gap-4">
      <Header icon={LuWorkflow} title="Orchestrator pipeline" item={item} flow={flow} />

      <Card>
        <CardTitle icon={LuWorkflow}>Pipeline activities</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          {activities.map((a, i) => (
            <div key={a} className="flex items-center gap-2">
              <div className={cx("flex items-center gap-2 rounded-xl border-[1.5px] border-layer bg-layer-soft px-3 py-2", layerOf(a))}>
                <span className="grid size-6 place-items-center rounded-full bg-layer text-xs font-bold text-on-color">{i + 1}</span>
                <span className="font-semibold">{a}</span>
              </div>
              {i < activities.length - 1 && <LuArrowRight className="text-muted" />}
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardTitle>Lakehouses</CardTitle>
          <KV k="Source">{item.source_lakehouse || flow.sourceLakehouse || "—"}</KV>
          <KV k="Target">{item.target_lakehouse || flow.targetLakehouse || "—"}</KV>
        </Card>
        <Card>
          <CardTitle>Last run</CardTitle>
          {run ? (
            <>
              <KV k="Status"><StatusPill status={run.status} /></KV>
              <KV k="Started">{run.start || "—"}</KV>
              <KV k="Duration">{run.duration || "—"}</KV>
              <KV k="Run ID" title={run.run_id || ""}><code>{run.run_id || "—"}</code></KV>
            </>
          ) : <p className="text-muted">Not run yet. The flow offers a background execution upon deployment (or skip).</p>}
        </Card>
      </div>
    </div>
  );
}

export function SemanticModelPanel({ flow, onGoToChat }) {
  const item = flow.semanticModel;
  if (!item) {
    return (
      <NotCreated title="Semantic model" stageKey="semantic_model" layer="semantic" icon={LuNetwork} flow={flow} onGoToChat={onGoToChat}
        expectedName={flow.target ? `${flow.target}_Gold_Model` : null} />
    );
  }
  const tables = item.tables || [];
  const facts = tables.filter((t) => t.type === "fact");
  const dims = tables.filter((t) => t.type === "dim");
  const others = tables.filter((t) => t.type !== "fact" && t.type !== "dim");
  const bgRun = latestRun(flow, "semantic_model");
  const refresh = item.last_refresh || (bgRun && { status: bgRun.status, time: bgRun.started, run_id: bgRun.run_id });

  const TableList = ({ title, rows }) => rows.length > 0 && (
    <div className="mb-3 last:mb-0">
      <div className="mb-1 text-[13px] font-semibold">{title} <span className="text-muted">({rows.length})</span></div>
      <ul className="grid gap-1">
        {rows.map((t) => (
          <li key={t.name} className="text-[13px]"><code>{t.name}</code>{t.columns != null && <span className="text-muted"> · {t.columns} cols</span>}</li>
        ))}
      </ul>
    </div>
  );

  const stats = [
    ["Fact tables", facts.length, LuTable2], ["Dimensions", dims.length, LuTable2],
    ["Relationships", item.relationships?.length || 0, LuGitMerge], ["Measures", item.measures?.length || 0, LuSquareFunction],
  ];

  return (
    <div className="semantic mx-auto flex max-w-[1040px] flex-col gap-4">
      <Header icon={LuNetwork} title={`Semantic model${item.mode ? ` · ${item.mode}` : ""}`} item={item} flow={flow} />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {stats.map(([label, n, Icon]) => (
          <Card key={label} className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-layer-soft text-xl text-layer"><Icon /></span>
            <div><b className="block text-2xl font-extrabold leading-none">{n}</b><span className="text-xs text-muted">{label}</span></div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardTitle icon={LuTable2}>Tables</CardTitle>
          {tables.length ? (
            <>
              <TableList title="Facts" rows={facts} />
              <TableList title="Dimensions" rows={dims} />
              <TableList title="Other" rows={others} />
            </>
          ) : <p className="text-muted">Table details will appear once Claude reports them.</p>}
        </Card>
        <Card>
          <CardTitle icon={LuGitMerge}>Relationships</CardTitle>
          {item.relationships?.length
            ? <ul className="grid gap-1">{item.relationships.map((r) => <li key={r} className="text-[13px]"><code>{r}</code></li>)}</ul>
            : <p className="text-muted">None reported yet.</p>}
          <CardTitle icon={LuSquareFunction} className="mt-4">Measures</CardTitle>
          {item.measures?.length
            ? <div className="flex flex-wrap gap-1.5">{item.measures.map((m) => <span key={m} className="rounded-md bg-layer-soft px-2 py-0.5 text-xs font-medium text-layer">{m}</span>)}</div>
            : <p className="text-muted">None reported yet.</p>}
        </Card>
      </div>

      <Card>
        <CardTitle>Last refresh</CardTitle>
        {refresh ? (
          <>
            <KV k={<StatusPill status={refresh.status} />}>{refresh.time || ""}</KV>
            {refresh.run_id && <KV k="Run ID" title={refresh.run_id}><code>{refresh.run_id}</code></KV>}
          </>
        ) : <p className="text-muted">Not refreshed yet. The flow offers a background refresh upon deployment (or skip).</p>}
      </Card>
    </div>
  );
}
