"""Direct, read-only Fabric / OneLake lookups for the dashboard and the new-project wizard.

No Claude involved: the backend calls the Fabric REST API and OneLake (ADLS Gen2 API) with the
signed-in Azure CLI user's token, so listing lakehouses or counting projects takes seconds.
A project is a lakehouse - at the workspace root or inside a workspace folder - that contains the
skill's control table project_status (Tables/dbo/project_status, or Tables/project_status).
Its rows are read with the `deltalake` package when it is installed.
"""
import json
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal

FABRIC_API = "https://api.fabric.microsoft.com/v1"
FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
STORAGE_RESOURCE = "https://storage.azure.com"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"

STAGE_KEYS = ["bronze", "silver", "gold", "orchestrator", "semantic_model"]
ROW_STATUS = {"COMPLETED": "done", "FAILED": "failed", "CANCELLED": "failed", "RUNNING": "running",
              "SUBMITTED": "submitted", "SKIPPED": "skipped"}


class FabricError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


# ---------- auth ----------

_tokens: dict[str, tuple[str, float]] = {}
_lock = threading.Lock()


def token(az: str, resource: str) -> str:
    with _lock:
        cached = _tokens.get(resource)
        if cached and cached[1] > time.time() + 120:
            return cached[0]
    out = subprocess.run([az, "account", "get-access-token", "--resource", resource, "-o", "json"],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise FabricError(out.stderr.strip()[-400:] or "Not signed in to Azure CLI (run az login)", 401)
    d = json.loads(out.stdout)
    try:
        expires = float(d.get("expires_on") or 0)
    except (TypeError, ValueError):
        expires = 0
    with _lock:
        _tokens[resource] = (d["accessToken"], expires or time.time() + 1800)
    return d["accessToken"]


def clear_tokens() -> None:
    with _lock:
        _tokens.clear()


def _get(url: str, tok: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise FabricError(f"{e.code} {e.reason}: {detail}", e.code) from None
    except urllib.error.URLError as e:
        raise FabricError(f"Cannot reach {urllib.parse.urlparse(url).netloc}: {e.reason}") from None


# ---------- Fabric REST ----------

def _list(az: str, path: str) -> list[dict]:
    url, items = f"{FABRIC_API}{path}", []
    while url:
        d = _get(url, token(az, FABRIC_RESOURCE))
        items += d.get("value", [])
        url = d.get("continuationUri")
    return items


def workspaces(az: str) -> list[dict]:
    return [{"id": w["id"], "name": w["displayName"], "type": w.get("type")} for w in _list(az, "/workspaces")]


def folder_paths(az: str, ws: str) -> dict[str, str]:
    """folderId -> "Parent/Child" path. Empty if the workspace has no folders (or the API is unavailable)."""
    try:
        items = _list(az, f"/workspaces/{ws}/folders")
    except FabricError as e:
        if e.status in (400, 403, 404):
            return {}
        raise
    by_id = {f["id"]: f for f in items}

    def path(fid):
        parts, seen = [], set()
        while fid in by_id and fid not in seen:
            seen.add(fid)
            parts.append(by_id[fid]["displayName"])
            fid = by_id[fid].get("parentFolderId")
        return "/".join(reversed(parts))

    return {fid: path(fid) for fid in by_id}


def lakehouses(az: str, ws: str) -> list[dict]:
    folders = folder_paths(az, ws)
    items = _list(az, f"/workspaces/{ws}/items?type=Lakehouse")
    return sorted(
        ({"id": i["id"], "name": i["displayName"], "folder": folders.get(i.get("folderId") or "")} for i in items),
        key=lambda x: ((x["folder"] or "").lower(), x["name"].lower()),
    )


# ---------- OneLake ----------

def list_paths(az: str, ws: str, directory: str) -> list[dict]:
    q = urllib.parse.urlencode({"resource": "filesystem", "recursive": "false", "directory": directory})
    try:
        d = _get(f"{ONELAKE}/{ws}?{q}", token(az, STORAGE_RESOURCE), {"x-ms-version": "2023-11-03"})
    except FabricError as e:
        if e.status == 404:
            return []
        raise
    return d.get("paths", [])


def _dirs(paths: list[dict]) -> list[str]:
    return [p["name"].rstrip("/").rsplit("/", 1)[-1] for p in paths if str(p.get("isDirectory")).lower() == "true"]


def raw_folders(az: str, ws: str, lakehouse_id: str) -> list[dict]:
    """Top-level folders under Files/ of the source lakehouse (each one is a candidate dataset)."""
    names = [n for n in _dirs(list_paths(az, ws, f"{lakehouse_id}/Files")) if not n.startswith("_")]
    return [{"name": n} for n in sorted(names, key=str.lower)]


def status_table_path(az: str, ws: str, lakehouse_id: str) -> str | None:
    for parent in ("Tables/dbo", "Tables"):
        if "project_status" in _dirs(list_paths(az, ws, f"{lakehouse_id}/{parent}")):
            return f"{parent}/project_status"
    return None


def _plain(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def deltalake_available() -> bool:
    try:
        import deltalake  # noqa: F401
        return True
    except ImportError:
        return False


def read_rows(az: str, ws: str, lakehouse_id: str, rel: str) -> list[dict] | None:
    """All rows of project_status, or None when the deltalake package is not installed."""
    try:
        from deltalake import DeltaTable
    except ImportError:
        return None
    table = DeltaTable(
        f"abfss://{ws}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/{rel}",
        storage_options={"bearer_token": token(az, STORAGE_RESOURCE), "use_fabric_endpoint": "true"},
    )
    return [{k: _plain(v) for k, v in row.items()} for row in table.to_pyarrow_table().to_pylist()]


# ---------- projects ----------

def _when(row: dict) -> str:
    return str(row.get("updated_at") or row.get("started_at") or "")


def summarize(lh: dict, rows: list[dict] | None, error: str | None) -> dict:
    folder_name = lh["folder"].rsplit("/", 1)[-1] if lh["folder"] else None
    base = {
        "lakehouse_id": lh["id"], "lakehouse": lh["name"], "folder": lh["folder"],
        "location": "folder" if lh["folder"] else "standalone",
        "name": folder_name or lh["name"], "stages": {}, "error": error,
    }
    if rows is None:
        return {**base, "bucket": "unknown", "readable": False}
    rows = sorted(rows, key=_when)
    latest = rows[-1] if rows else {}
    stages = {}
    for r in rows:
        key = str(r.get("stage") or "").lower()
        if key in STAGE_KEYS:
            stages[key] = ROW_STATUS.get(str(r.get("status") or "").upper(), "in_progress")
    overall = str(latest.get("overall_project_status") or "").upper() or None
    pct = latest.get("completion_percentage")
    bucket = ("completed" if overall == "COMPLETED" or pct == 100
              else "failed" if overall == "FAILED" else "in_progress")
    return {
        **base, "readable": True, "bucket": bucket, "stages": stages,
        "name": latest.get("project_name") or base["name"],
        "overall_status": overall, "current_stage": latest.get("current_project_stage"),
        "current_gate": latest.get("current_gate"), "next_action": latest.get("next_action_required"),
        "completion": pct, "updated_at": _when(latest) or None, "row_count": len(rows),
    }


def discover_projects(az: str, ws: str) -> dict:
    lhs = lakehouses(az, ws)

    def check(lh):
        try:
            rel = status_table_path(az, ws, lh["id"])
        except FabricError:
            return None
        if not rel:
            return None
        try:
            return lh, read_rows(az, ws, lh["id"], rel), None
        except Exception as e:  # unreadable table: still a project, status unknown
            return lh, None, str(e)[:300]

    with ThreadPoolExecutor(max_workers=8) as pool:
        found = [r for r in pool.map(check, lhs) if r]

    projects = [summarize(lh, rows, err) for lh, rows, err in found]
    projects.sort(key=lambda p: p.get("updated_at") or "", reverse=True)

    activity = []
    for lh, rows, _ in found:
        name = next((p["name"] for p in projects if p["lakehouse_id"] == lh["id"]), lh["name"])
        for r in rows or []:
            activity.append({
                "project": name, "stage": r.get("stage"), "artifact": r.get("artifact_name"),
                "status": r.get("status"), "when": _when(r) or None, "duration_seconds": r.get("duration_seconds"),
                "records_processed": r.get("records_processed"), "error": r.get("error_message"),
                "run_id": r.get("run_id"),
            })
    activity.sort(key=lambda a: a["when"] or "", reverse=True)

    count = lambda b: sum(p["bucket"] == b for p in projects)
    return {
        "workspace_id": ws,
        "projects": projects,
        "activity": activity[:15],
        "counts": {
            "total": len(projects),
            "completed": count("completed"),
            "in_progress": count("in_progress") + count("failed"),
            "failed": count("failed"),
            "unknown": count("unknown"),
        },
        "lakehouses_scanned": len(lhs),
        "status_reader": deltalake_available(),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
