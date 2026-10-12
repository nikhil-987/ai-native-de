import { useState } from "react";
import { LuActivity, LuCheck, LuRefreshCw, LuTriangleAlert } from "react-icons/lu";
import { getRunStatus } from "../lib/api.js";
import { LAYER_COLORS } from "../lib/sections.js";
import { Button, Card, CardTitle, Pill, STATUS_TONE, Spinner, cx } from "./ui.jsx";

export function RunsPanel({ flow }) {
  const [checked, setChecked] = useState({});

  async function check(run) {
    setChecked((c) => ({ ...c, [run.run_id]: { ...c[run.run_id], loading: true, error: null } }));
    try {
      const d = await getRunStatus(run);
      setChecked((c) => ({ ...c, [run.run_id]: { loading: false, status: d.status, error: d.error, end: d.end } }));
    } catch (e) {
      setChecked((c) => ({ ...c, [run.run_id]: { ...c[run.run_id], loading: false, error: e.message } }));
    }
  }

  const runs = flow.runs || [];

  return (
    <div className="mx-auto flex max-w-[1040px] flex-col gap-5">
      <div>
        <h2 className="mb-1 text-[22px] font-bold">Background Runs</h2>
        <p className="text-muted">Real-time status tracker for submitted Fabric notebook jobs, pipeline runs, and semantic model refreshes.</p>
      </div>

      {runs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center text-muted">
          <LuActivity className="mb-3 text-4xl text-muted/60" />
          <h3 className="mb-1 text-base font-bold text-ink">No Background Jobs Yet</h3>
          <p className="max-w-[480px] text-xs text-muted">
            When you run notebook stages (Bronze, Silver, Gold) or deploy orchestrator pipelines in the Studio, their execution status will appear here.
          </p>
        </Card>
      ) : (
        <div className="grid gap-3.5">
          {runs.map((r) => {
            const c = checked[r.run_id] || {};
            const status = c.status || r.status;
            const canCheck = r.workspace_id && r.item_id && r.run_id;
            return (
              <Card key={r.run_id || r.item} className={cx("flex flex-col gap-2 border-l-4", LAYER_COLORS[r.stage])}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="size-3 rounded-full bg-layer" />
                    <b className="text-base font-bold text-ink">{r.item || r.stage}</b>
                    <span className="rounded bg-code px-2 py-0.5 font-mono text-xs text-muted">Stage: {r.stage}</span>
                  </div>
                  {status && <Pill tone={STATUS_TONE[status] || "neutral"}>{status}</Pill>}
                </div>

                <div className="grid grid-cols-1 gap-2 border-t border-line pt-2 font-mono text-xs sm:grid-cols-3">
                  <div><span className="text-muted">Run ID:</span> <code className="text-ink">{r.run_id || "—"}</code></div>
                  <div><span className="text-muted">Kind:</span> <span className="text-ink">{r.kind || "job"}</span></div>
                  <div><span className="text-muted">Started:</span> <span className="text-ink">{r.started || "Recent"}</span></div>
                </div>

                <div className="mt-1 flex items-center justify-between border-t border-dashed border-line pt-2">
                  <div className="text-xs text-muted">
                    {r.duration ? `Duration: ${r.duration}` : "Job submitted to Fabric"}
                  </div>
                  {canCheck && (
                    <Button variant="ghost" size="xs" onClick={() => !c.loading && check(r)} disabled={c.loading}>
                      {c.loading ? <Spinner /> : <LuRefreshCw />} {c.loading ? "Checking status…" : "Check Status"}
                    </Button>
                  )}
                </div>
                {c.error && <div className="mt-1 text-xs text-bad">{c.error}</div>}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
