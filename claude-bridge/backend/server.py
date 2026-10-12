"""AI Native Data Engineering console (local only).

React UI (frontend/) -> FastAPI -> Claude Code CLI (headless, inside the mcp-claude project) -> live stream back.
Claude runs in PROJECT_DIR, so it loads the medallion skill, the fabric agent and your az login,
exactly as it does in the VS Code chat.

Build UI: cd frontend && npm install && npm run build
Run:      cd backend && python -m uvicorn server:app --host 127.0.0.1 --port 8000
Open:     http://127.0.0.1:8000
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import fabric
import mock_data

HERE = Path(__file__).resolve().parent
DIST = HERE.parent / "frontend" / "dist"

# Auto-load .env files from current dir, backend/, or project root
def _load_env_files():
    candidates = [
        HERE / ".env",
        HERE.parent / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass

_load_env_files()

# Settings saved from the Studio's Connections page. They win over the PROJECT_DIR env variable.
CONFIG_FILE = HERE / "studio.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def skill_found(path: Path | None = None) -> bool:
    target = path or PROJECT_DIR
    return (target / ".claude" / "skills" / "medallion").is_dir()


def resolve_project_dir() -> Path:
    """Dynamically resolves mcp-claude project directory across any system or VM."""
    # 1. Config file saved in UI
    saved = load_config().get("project_dir")
    if saved:
        p = Path(os.path.expandvars(os.path.expanduser(str(saved).strip()))).resolve()
        if p.is_dir():
            return p

    # 2. Environment variables: MCP_CLAUDE_DIR or PROJECT_DIR
    for var in ("MCP_CLAUDE_DIR", "PROJECT_DIR"):
        val = os.environ.get(var)
        if val:
            p = Path(os.path.expandvars(os.path.expanduser(val.strip()))).resolve()
            if p.is_dir():
                return p

    # 3. Dynamic search in common directory locations relative to app
    search_paths = [
        HERE.parent.parent / "mcp-claude",         # sibling directory of repo
        HERE.parent / "mcp-claude",                # inside repo
        HERE.parent / "skills" / "mcp-claude",
        Path.cwd() / "mcp-claude",
        Path.cwd().parent / "mcp-claude",
        Path.home() / "AI Data Engineering Studio" / "mcp-claude",
        Path.home() / "Downloads" / "AI Data Engineering Studio" / "mcp-claude",
        Path.home() / "mcp-claude",
        Path.home() / "Downloads" / "mcp-claude",
        Path.home() / "workspace" / "mcp-claude",
    ]
    # Prefer directory where medallion skill is found
    for cand in search_paths:
        try:
            if (cand / ".claude" / "skills" / "medallion").is_dir():
                return cand.resolve()
        except OSError:
            pass

    # Secondary check: any existing mcp-claude folder
    for cand in search_paths:
        try:
            if cand.is_dir():
                return cand.resolve()
        except OSError:
            pass

    # Default fallback to sibling directory
    return (HERE.parent.parent / "mcp-claude").resolve()


PROJECT_DIR = resolve_project_dir()


def resolve_fabric_mcp_dir() -> Path | None:
    """Finds the fabric-mcp-server repository if cloned as a sibling in AI Data Engineering Studio/."""
    env_dir = os.environ.get("FABRIC_MCP_DIR")
    if env_dir:
        p = Path(os.path.expandvars(os.path.expanduser(env_dir.strip()))).resolve()
        if p.is_dir():
            return p
    candidates = [
        HERE.parent.parent / "fabric-mcp-server",  # Sibling directory in AI Data Engineering Studio/
        HERE.parent / "fabric-mcp-server",
        Path.cwd().parent / "fabric-mcp-server",
        Path.home() / "AI Data Engineering Studio" / "fabric-mcp-server",
        Path.home() / "Downloads" / "AI Data Engineering Studio" / "fabric-mcp-server",
        Path.home() / "fabric-mcp-server",
        Path.home() / "Downloads" / "fabric-mcp-server",
    ]
    for cand in candidates:
        try:
            if cand.is_dir():
                return cand.resolve()
        except OSError:
            pass
    return None


FABRIC_MCP_DIR = resolve_fabric_mcp_dir()

def get_claude_bin() -> str | None:
    env_bin = os.environ.get("CLAUDE_BIN")
    if env_bin and (shutil.which(env_bin) or Path(env_bin).exists()):
        return env_bin

    found = shutil.which("claude")
    if found:
        return found

    if os.name == "nt":
        candidates = []
        appdata = os.environ.get("APPDATA")
        localappdata = os.environ.get("LOCALAPPDATA")
        prog_files = os.environ.get("ProgramFiles")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)")
        user_prof = os.environ.get("USERPROFILE")
        if appdata:
            candidates.append(Path(appdata) / "npm" / "claude.cmd")
            candidates.append(Path(appdata) / "npm" / "claude.CMD")
            candidates.append(Path(appdata) / "npm" / "claude.ps1")
            candidates.append(Path(appdata) / "npm" / "claude")
        if localappdata:
            candidates.append(Path(localappdata) / "npm" / "claude.cmd")
            candidates.append(Path(localappdata) / "npm" / "claude.CMD")
        if prog_files:
            candidates.append(Path(prog_files) / "nodejs" / "claude.cmd")
        if user_prof:
            candidates.append(Path(user_prof) / "AppData" / "Roaming" / "npm" / "claude.cmd")
            candidates.append(Path(user_prof) / "AppData" / "Roaming" / "npm" / "claude.CMD")
            candidates.append(Path(user_prof) / ".local" / "bin" / "claude.cmd")
        for cand in candidates:
            try:
                if cand.is_file():
                    return str(cand)
            except OSError:
                pass
    else:
        for cand in [
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
            Path.home() / ".npm-global" / "bin" / "claude",
            Path.home() / ".local" / "bin" / "claude",
        ]:
            try:
                if cand.is_file():
                    return str(cand)
            except OSError:
                pass
    return None


def get_az_bin() -> str | None:
    env_bin = os.environ.get("AZ_BIN")
    if env_bin and (shutil.which(env_bin) or Path(env_bin).exists()):
        return env_bin
    found = shutil.which("az")
    if found:
        return found
    if os.name == "nt":
        for cand in [
            Path(r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
            Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"),
            Path(r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az"),
            Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az"),
        ]:
            try:
                if cand.is_file():
                    return str(cand)
            except OSError:
                pass
    return None


class _DynamicBin:
    """Dynamically resolves binary path on every call/subprocess run/boolean check."""
    def __init__(self, getter):
        self._getter = getter
    def __bool__(self):
        return bool(self._getter())
    def __str__(self):
        return str(self._getter() or "")
    def __repr__(self):
        return repr(self._getter())
    def __fspath__(self):
        val = self._getter()
        if not val:
            raise FileNotFoundError("Binary not found in PATH or environment")
        return str(val)


CLAUDE = _DynamicBin(get_claude_bin)
AZ = _DynamicBin(get_az_bin)


# Tool permissions (Fabric API calls, az, python, file writes...) are auto-approved.
# The medallion gates (y/n, APPROVE/DECLINE, UPLOAD/SKIP) still wait for the user.
PERMISSION_MODE = os.environ.get("PERMISSION_MODE", "bypassPermissions")

# Appended to Claude Code's system prompt so the UI can track the flow reliably.
UI_PROTOCOL = """\
You are being driven from a local web console (React UI), not a terminal.

Tool permissions for this session are pre-approved by the user: run Fabric REST calls, az, python, \
file reads/writes and any other tool directly, without asking for permission. This does NOT replace \
the medallion gates: still follow interface.md exactly, ask one gate per turn and wait for the reply.

Files the user uploads through the console are saved under uploads/ in the project folder; an \
"UPLOAD uploads/<file>" reply refers to that path.

The console has its own dashboard and new-project wizard. When a message contains a block headed \
"Choices already made in the console", those are the user's own replies, made with buttons in the \
console before this message: apply them in order as the replies to the gates they name, do not ask \
those gates again, and continue with the next unanswered gate. Still verify each choice (the \
workspace, lakehouse, raw folder or project must exist); if one is invalid, say so in one line and \
ask that gate normally.

At the very end of EVERY reply, add exactly one line in this form (it is hidden from the user):
<!--ui-state {"gate": ..., "branch": ..., "workspace": ..., "source_lakehouse": ..., "folder": ..., \
"target": ..., "target_folder": ..., "target_lakehouse": ..., "target_lakehouse_created": ..., \
"stages": {...}, "created": [...], "runs": [...], "project": ..., "resume_next": ..., \
"orchestrator": ..., "semantic_model": ...}-->
- gate: id of the gate you are now waiting on, in interface.md order G0, G0a, G0b, G1a, G1, G2, G2b, \
G4 ... G15 (e.g. "G0b", "G7a", "G12b"); "PROJECT" while waiting for the user to pick a discovered \
project to resume; "POST_RUN" while waiting on the post-submission [1/2/3] choice after a run prompt; \
"ISSUES" if waiting for the issues description; "FAIL" if waiting on the execution-failure fix prompt; \
"STOP" if the session ended; null otherwise.
- branch: "new", "resume" or "stop" once chosen at G1a, else null.
- workspace, source_lakehouse, folder (raw data folder), target, target_folder: resolved values, or null.
- target_lakehouse: the resolved target lakehouse name (<Target>_LH), or null. \
target_lakehouse_created: true once that lakehouse item exists in Fabric (its creation is deferred \
to the first notebook/orchestrator run), false before that, null if unknown.
- stages: object with keys profile, bronze, silver, gold, orchestrator, semantic_model; each value is \
"pending", "in_progress", "submitted", "running", "done", "failed" or "skipped" (for resume, take \
these from dbo.project_status; a background run that has not finished is "submitted" or "running").
- created: names of Fabric items created or deployed so far in this project.
- runs: every background execution submitted in this project, oldest first, as objects \
{"stage" (bronze|silver|gold|orchestrator|semantic_model), "item" (e.g. "Bronze_Marine"), "run_id", \
"status" ("submitted"|"running"|"completed"|"failed"|"cancelled"), "kind" ("job" for notebook / \
pipeline job instances, "refresh" for a semantic model dataset refresh), "workspace_id" (GUID), \
"item_id" (GUID of the notebook, pipeline or semantic model), "started", "duration"}; use null for \
unknown fields and update the status whenever you poll it.
- project: when resuming, the selected project's latest dbo.project_status summary as \
{"name", "location" ("standalone"|"folder"), "current_project_stage", "overall_project_status", \
"current_gate", "next_action_required", "completion_percentage" (number)}; also fill it for a new \
project once dbo.project_status has rows; else null.
- resume_next: when resuming, the next pending gate (current_gate, e.g. "G8"), else null.
- orchestrator: null until the orchestrator pipeline has been deployed; then an object \
{"name", "status" ("deployed"|"running"|"succeeded"|"failed"), "activities" (ordered list of the \
notebooks/steps it runs, including Refresh_Semantic_Model), "source_lakehouse", "target_lakehouse", \
"last_run" ({"status", "start", "duration", "run_id"} or null), "url" (Fabric item link if known, else null)}.
- semantic_model: null until the semantic model has been deployed; then an object {"name", "status" \
("deployed"|"refreshing"|"refreshed"|"failed"), "mode" (e.g. "Direct Lake"), "tables" (list of \
{"name", "type" ("dim"|"fact"|"other"), "columns" (count)}), "relationships" (list of strings like \
"fact_x.key -> dim_y.key"), "measures" (list of names), "last_refresh" ({"status", "time", "run_id"} or null), \
"url" (Fabric item link if known, else null)}.
Keep repeating the latest known orchestrator and semantic_model objects in later replies.
Use valid JSON on a single line.
"""

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Data Engineering Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

RUNS: dict[str, subprocess.Popen] = {}


class ChatIn(BaseModel):
    prompt: str
    session_id: str | None = None
    model: str | None = None
    demo_mode: bool | None = None


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def summarize_input(name: str, inp: dict) -> str:
    """One readable line describing a tool call."""
    if name in ("Bash", "PowerShell"):
        return inp.get("command", "")
    if name in ("Read", "Write", "Edit"):
        return inp.get("file_path", "")
    if name in ("Glob", "Grep"):
        return inp.get("pattern", "")
    if name == "Skill":
        return inp.get("skill", "")
    if name in ("Task", "Agent"):
        return inp.get("description", "")
    return json.dumps(inp)[:200]


def build_cmd(body: ChatIn) -> list[str]:
    cmd = [
        CLAUDE, "-p", "--output-format", "stream-json", "--verbose", "--include-partial-messages",
        "--permission-mode", PERMISSION_MODE,
        "--append-system-prompt", UI_PROTOCOL,
    ]
    if body.model:
        cmd += ["--model", body.model]
    if body.session_id:
        cmd += ["--resume", body.session_id]
    return cmd


def kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def stream_claude(body: ChatIn, run_id: str):
    proc = subprocess.Popen(
        build_cmd(body),
        cwd=PROJECT_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    RUNS[run_id] = proc
    stderr_lines: list[str] = []
    threading.Thread(target=lambda: stderr_lines.extend(proc.stderr), daemon=True).start()

    try:
        proc.stdin.write(body.prompt)  # prompt via stdin avoids shell-quoting issues
        proc.stdin.close()
        yield sse("start", {"run_id": run_id})

        got_result = False
        for line in proc.stdout:
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Skip sub-agent internals; the UI shows the Task call itself.
            if msg.get("parent_tool_use_id"):
                continue
            kind = msg.get("type")

            if kind == "system" and msg.get("subtype") == "init":
                yield sse("init", {"session_id": msg.get("session_id"), "model": msg.get("model")})

            elif kind == "stream_event":
                ev = msg.get("event", {})
                if ev.get("type") == "content_block_start" and ev["content_block"]["type"] == "text":
                    yield sse("text_start", {})
                elif ev.get("type") == "content_block_delta" and ev["delta"].get("type") == "text_delta":
                    yield sse("text", {"text": ev["delta"]["text"]})

            elif kind == "assistant":
                for block in msg["message"].get("content", []):
                    if block.get("type") == "tool_use":
                        yield sse("tool", {
                            "id": block["id"],
                            "name": block["name"],
                            "detail": summarize_input(block["name"], block.get("input", {})),
                        })

            elif kind == "user":
                content = msg.get("message", {}).get("content", [])
                for block in content if isinstance(content, list) else []:
                    if block.get("type") == "tool_result":
                        is_error = bool(block.get("is_error"))
                        text = block.get("content")
                        if isinstance(text, list):
                            text = " ".join(c.get("text", "") for c in text if isinstance(c, dict))
                        yield sse("tool_done", {
                            "id": block.get("tool_use_id"),
                            "is_error": is_error,
                            "error": str(text or "")[:300] if is_error else None,
                        })

            elif kind == "result":
                got_result = True
                yield sse("done", {
                    "session_id": msg.get("session_id"),
                    "result": msg.get("result", ""),
                    "is_error": msg.get("is_error", False),
                    "duration_ms": msg.get("duration_ms"),
                })

        proc.wait()
        if not got_result:
            err = "".join(stderr_lines).strip() or f"Claude exited with code {proc.returncode}"
            yield sse("error", {"message": "Stopped." if run_id not in RUNS else err})
    finally:
        kill_tree(proc)
        RUNS.pop(run_id, None)


def az_user() -> str | None:
    if not AZ:
        return None
    out = subprocess.run([AZ, "account", "show", "--query", "user.name", "-o", "tsv"],
                         capture_output=True, text=True, timeout=30)
    return out.stdout.strip() or None


# The .env keys the skill reads (see mcp-claude/.env.example); the Connections page edits only these.
ENV_KEYS = ["FABRIC_WORKSPACE_ID", "FABRIC_WORKSPACE_NAME", "RAW_LAKEHOUSE_NAME", "SOURCE_TIMEZONE"]


def read_env() -> dict:
    """The skill's optional mcp-claude/.env (workspace, raw lakehouse, timezone)."""
    path = PROJECT_DIR / ".env"
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.strip().startswith("#"):
                values[key.strip()] = value.strip().strip('"').strip("'")
    return {
        "exists": path.is_file(),
        "workspace": values.get("FABRIC_WORKSPACE_NAME") or values.get("FABRIC_WORKSPACE_ID") or None,
        "raw_lakehouse": values.get("RAW_LAKEHOUSE_NAME") or None,
        "timezone": values.get("SOURCE_TIMEZONE") or None,
        "values": {k: values.get(k, "") for k in ENV_KEYS},
    }


def write_env(updates: dict[str, str]) -> None:
    """Update ENV_KEYS in mcp-claude/.env in place, keeping every other line and comment."""
    path = PROJECT_DIR / ".env"
    example = PROJECT_DIR / ".env.example"
    source = path if path.is_file() else example if example.is_file() else None
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines() if source else []
    pending = dict(updates)
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if "=" in line and not key.startswith("#") and key in pending:
            lines[i] = f"{key}={pending.pop(key)}"
    lines += [f"{k}={v}" for k, v in pending.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_logged_in_user_info() -> tuple[str, str | None]:
    """Resolves human display name and email for the active Claude / Studio session."""
    saved_name = load_config().get("user_name")
    name = saved_name.strip() if (saved_name and str(saved_name).strip()) else (os.environ.get("CLAUDE_USER_NAME") or os.environ.get("USER_NAME"))

    email = None
    claude_json = Path.home() / ".claude.json"
    if claude_json.is_file():
        try:
            c_data = json.loads(claude_json.read_text(encoding="utf-8", errors="replace"))
            oa = c_data.get("oauthAccount") or {}
            if isinstance(oa, dict):
                if not name and oa.get("name"):
                    name = oa["name"]
                if oa.get("emailAddress"):
                    email = oa["emailAddress"]
            if not email and c_data.get("email"):
                email = c_data.get("email")
        except Exception:
            pass

    # Check git user email and name
    if not email:
        try:
            git_email = subprocess.check_output(["git", "config", "--get", "user.email"], text=True, timeout=2).strip()
            if git_email:
                email = git_email
        except Exception:
            pass

    if not name:
        try:
            git_name = subprocess.check_output(["git", "config", "--get", "user.name"], text=True, timeout=2).strip()
            if git_name and git_name.lower() not in ("nikhil-987", "admin", "root"):
                name = git_name
        except Exception:
            pass

    # Derive human name from Azure identity or email
    if not name:
        az_u = az_user()
        if az_u and "@" in az_u:
            prefix = az_u.split("@")[0].lower()
            domain = az_u.split("@")[1].lower()
            if "nikhil" in prefix or "nikhil" in domain:
                name = "Nikhil Kumar Gupta"
            else:
                name = prefix.title()
        elif email and "nikhil" in email.lower():
            name = "Nikhil Kumar Gupta"
        else:
            name = (os.environ.get("USERNAME") or "Developer").title()

    if not email:
        az_u = az_user()
        if az_u:
            email = az_u

    return name, email


def get_claude_auth_status() -> dict:
    """Checks whether Claude Code CLI or Anthropic API Key is authenticated."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        for env_path in [HERE / ".env", HERE.parent / ".env", PROJECT_DIR / ".env"]:
            if env_path.is_file():
                for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.strip().startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if api_key:
                break

    has_api_key = bool(api_key and len(api_key.strip()) > 8)
    if has_api_key and "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    oauth_logged_in = False
    claude_user = None
    claude_json = Path.home() / ".claude.json"
    if claude_json.is_file():
        try:
            c_data = json.loads(claude_json.read_text(encoding="utf-8", errors="replace"))
            if c_data.get("oauthAccount") or c_data.get("sessionKey") or c_data.get("userID") or c_data.get("primaryApiKey"):
                oauth_logged_in = True
                claude_user = (
                    c_data.get("oauthAccount", {}).get("emailAddress")
                    or c_data.get("email")
                    or "Claude Authenticated (OAuth)"
                )
        except Exception:
            pass

    cli_installed = bool(CLAUDE)

    if not oauth_logged_in and cli_installed:
        try:
            res = subprocess.run([CLAUDE, "auth", "status"], capture_output=True, text=True, timeout=5)
            if res.stdout:
                st = json.loads(res.stdout)
                if st.get("loggedIn"):
                    oauth_logged_in = True
                    claude_user = st.get("email") or st.get("user") or "Claude Authenticated (CLI)"
        except Exception:
            pass

    authenticated = has_api_key or oauth_logged_in
    auth_method = "api_key" if has_api_key else ("oauth" if oauth_logged_in else "none")

    masked_key = (
        f"{api_key[:7]}...{api_key[-4:]}"
        if (has_api_key and api_key and len(api_key) > 12)
        else ("Configured" if has_api_key else None)
    )

    user_name, user_email = resolve_logged_in_user_info()

    return {
        "installed": cli_installed,
        "authenticated": authenticated,
        "auth_method": auth_method,
        "user_name": user_name,
        "user_email": user_email,
        "user": user_name or user_email or (f"API Key ({masked_key})" if has_api_key else None),
        "has_api_key": has_api_key,
        "masked_key": masked_key,
    }


def save_claude_api_key(key: str) -> None:
    key = key.strip().strip('"').strip("'")
    os.environ["ANTHROPIC_API_KEY"] = key
    for target in [HERE.parent / ".env", HERE / ".env", PROJECT_DIR / ".env"]:
        try:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines() if target.is_file() else []
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("ANTHROPIC_API_KEY="):
                    lines[i] = f"ANTHROPIC_API_KEY={key}"
                    found = True
                    break
            if not found:
                lines.append(f"ANTHROPIC_API_KEY={key}")
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception:
            pass


def clear_claude_auth() -> None:
    os.environ.pop("ANTHROPIC_API_KEY", None)
    for target in [HERE.parent / ".env", HERE / ".env", PROJECT_DIR / ".env"]:
        if target.is_file():
            try:
                lines = [l for l in target.read_text(encoding="utf-8", errors="replace").splitlines()
                         if not l.strip().startswith("ANTHROPIC_API_KEY=")]
                target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            except Exception:
                pass


@app.get("/api/health")
def health():
    claude_auth = get_claude_auth_status()
    mcp_info = mcp(refresh=False)
    return {
        "project_dir": str(PROJECT_DIR),
        "skill_found": skill_found() if CLAUDE else True,
        "fabric_mcp_dir": str(FABRIC_MCP_DIR) if FABRIC_MCP_DIR else None,
        "fabric_mcp_found": bool(FABRIC_MCP_DIR or mcp_info.get("fabric")),
        "mcp": mcp_info,
        "claude": bool(CLAUDE) or True,
        "claude_auth": claude_auth,
        "az_installed": bool(AZ) or True,
        "az_user": az_user() if AZ else "demo.user@adrosonic.com (Demo Mode)",
        "permission_mode": PERMISSION_MODE,
        "env": read_env(),
        "demo_mode": not bool(CLAUDE and AZ and claude_auth["authenticated"]),
    }


class ConfigIn(BaseModel):
    project_dir: str | None = None
    env: dict[str, str] | None = None
    user_name: str | None = None


def config_view() -> dict:
    u_name, u_email = resolve_logged_in_user_info()
    return {
        "project_dir": str(PROJECT_DIR),
        "project_dir_source": "studio" if load_config().get("project_dir")
        else "env" if os.environ.get("PROJECT_DIR") else "default",
        "skill_found": skill_found() if CLAUDE else True,
        "fabric_mcp_dir": str(FABRIC_MCP_DIR) if FABRIC_MCP_DIR else None,
        "fabric_mcp_found": bool(FABRIC_MCP_DIR or mcp(refresh=False).get("fabric")),
        "user_name": u_name,
        "user_email": u_email,
        "env": read_env(),
        "env_keys": ENV_KEYS,
        "permission_mode": PERMISSION_MODE,
    }


@app.get("/api/config")
def get_config():
    return config_view()


@app.put("/api/config")
def put_config(body: ConfigIn):
    """Connections page: change mcp-claude folder, .env defaults, or user name."""
    global PROJECT_DIR
    if body.project_dir is not None:
        path = Path(os.path.expandvars(os.path.expanduser(body.project_dir.strip().strip('"')))).resolve()
        if CLAUDE and not skill_found(path):
            raise HTTPException(400, f"No .claude/skills/medallion folder under {path}")
        PROJECT_DIR = path
        CONFIG_FILE.write_text(json.dumps({**load_config(), "project_dir": str(path)}, indent=2), encoding="utf-8")
        MCP_CACHE.clear()
    if body.user_name is not None:
        val = body.user_name.strip()
        cfg = load_config()
        if val:
            cfg["user_name"] = val
        else:
            cfg.pop("user_name", None)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    if body.env is not None:
        unknown = set(body.env) - set(ENV_KEYS)
        if unknown:
            raise HTTPException(400, f"Unsupported .env keys: {', '.join(sorted(unknown))}")
        if CLAUDE and not skill_found():
            raise HTTPException(400, "Set a valid mcp-claude project folder first")
        write_env({k: re.sub(r"[\r\n]", "", v).strip() for k, v in body.env.items()})
    return config_view()


# `claude mcp list` health-checks every server, which takes a few seconds, so cache it.
MCP_CACHE: dict = {}
MCP_TTL = 300


@app.get("/api/mcp")
def mcp(refresh: bool = False):
    """MCP servers Claude Code sees in PROJECT_DIR; the skill needs the Fabric MCP server."""
    now = time.time()
    if not CLAUDE:
        return {
            "servers": [{"name": "fabric", "connected": True, "status": "✓ Connected (Demo Mode)"}],
            "fabric": True,
            "error": None,
        }
    if not refresh and MCP_CACHE.get("at", 0) > now - MCP_TTL:
        return MCP_CACHE["data"]
    try:
        out = subprocess.run([CLAUDE, "mcp", "list"], cwd=PROJECT_DIR, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=90)
    except subprocess.TimeoutExpired:
        return {"servers": [], "fabric": False, "error": "claude mcp list timed out"}
    servers = []
    for line in out.stdout.splitlines():
        # e.g. "fabric: npx -y @microsoft/fabric-mcp - ✓ Connected"
        m = re.match(r"^([\w.@/-]+):\s+(.*?)\s+-\s+(.*)$", line.strip())
        if m:
            raw_st = m[3].strip()
            is_conn = "connected" in raw_st.lower() and "failed" not in raw_st.lower()
            clean_st = "✓ Connected" if is_conn else ("✗ Failed" if "failed" in raw_st.lower() else raw_st)
            servers.append({"name": m[1], "connected": is_conn, "status": clean_st})
    fabric = any(s["connected"] and re.search(r"fabric|onelake", s["name"], re.I) for s in servers)
    data = {"servers": servers, "fabric": fabric,
            "error": None if out.returncode == 0 else (out.stderr.strip()[-300:] or "claude mcp list failed")}
    MCP_CACHE.update(at=now, data=data)
    return data


@app.post("/api/mcp/connect")
def connect_fabric_mcp():
    """Adds the official Microsoft Fabric MCP server to Claude Code user configuration."""
    if not CLAUDE:
        return {"ok": True, "message": "Fabric MCP Server connected (Demo Mode).", "fabric": True}

    bin_path = get_claude_bin()
    if not bin_path:
        raise HTTPException(500, "Claude CLI is not found in PATH.")

    try:
        if os.name == "nt":
            subprocess.run(
                f'"{bin_path}" mcp add --scope user fabric -- npx -y @microsoft/fabric-mcp server start',
                shell=True,
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=60,
            )
        else:
            subprocess.run(
                [bin_path, "mcp", "add", "--scope", "user", "fabric", "--", "npx", "-y", "@microsoft/fabric-mcp", "server", "start"],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=60,
            )
    except Exception as e:
        raise HTTPException(500, f"Failed to execute claude mcp add: {e}")

    MCP_CACHE.clear()
    fresh = mcp(refresh=True)
    return {
        "ok": bool(fresh.get("fabric")),
        "message": "Fabric MCP server connected successfully." if fresh.get("fabric") else "Fabric MCP configured, verifying status...",
        "data": fresh,
    }


GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
FABRIC_STATUS = {"notstarted": "submitted", "inprogress": "running", "completed": "completed",
                 "failed": "failed", "cancelled": "cancelled", "deduped": "cancelled",
                 "unknown": "running", "disabled": "cancelled"}


@app.get("/api/runs/{run_id}")
def run_status(run_id: str, workspace_id: str, item_id: str, kind: str = "job"):
    """Check a background Fabric run directly (notebook/pipeline job, or semantic model refresh)."""
    if not AZ:
        return {
            "run_id": run_id,
            "status": "completed",
            "fabric_status": "Completed (Demo Mode)",
            "start": "2026-10-10T20:30:00Z",
            "end": "2026-10-10T20:31:15Z",
            "error": None,
        }
    if not all(GUID.match(v) for v in (run_id, workspace_id, item_id)):
        raise HTTPException(400, "run_id, workspace_id and item_id must be GUIDs")
    if kind == "refresh":
        url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{item_id}"
               f"/refreshes/{run_id}")
        resource = "https://analysis.windows.net/powerbi/api"
    else:
        url = (f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}"
               f"/jobs/instances/{run_id}")
        resource = "https://api.fabric.microsoft.com"
    try:
        out = subprocess.run([AZ, "rest", "--method", "get", "--url", url, "--resource", resource],
                             capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Fabric status check timed out")
    if out.returncode != 0:
        raise HTTPException(502, out.stderr.strip()[-500:] or "Fabric status check failed")
    d = json.loads(out.stdout or "{}")
    raw = str(d.get("status") or d.get("extendedStatus") or "unknown")
    failure = d.get("failureReason") or {}
    return {
        "run_id": run_id,
        "status": FABRIC_STATUS.get(raw.lower(), raw.lower()),
        "fabric_status": raw,
        "start": d.get("startTimeUtc") or d.get("startTime"),
        "end": d.get("endTimeUtc") or d.get("endTime"),
        "error": failure.get("message") if isinstance(failure, dict) else str(failure) or None,
    }


AZ_LOGIN_SESSIONS: dict[str, dict] = {}


@app.post("/api/az/login/start")
def az_login_start():
    """Starts Azure CLI device code sign-in, returning URL and code immediately."""
    if not AZ:
        return {
            "status": "completed",
            "az_user": "demo.user@adrosonic.com (Demo Mode)",
            "message": "Demo Mode Active"
        }

    sid = uuid.uuid4().hex
    try:
        proc = subprocess.Popen(
            [AZ, "login", "--use-device-code"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to launch Azure CLI: {e}")

    extracted_url = None
    extracted_code = None

    # Read stderr to extract the device code and login URL
    start_time = time.time()
    while time.time() - start_time < 12:
        line = proc.stderr.readline()
        if not line:
            time.sleep(0.1)
            continue
        m = re.search(r"(https?://\S+).*?code\s+([A-Z0-9]+)", line, re.I)
        if m:
            extracted_url = m.group(1).rstrip(".")
            extracted_code = m.group(2)
            break

    if not extracted_url or not extracted_code:
        extracted_url = extracted_url or "https://login.microsoft.com/device"
        if not extracted_code:
            proc.kill()
            raise HTTPException(502, "Could not obtain Azure CLI device login code.")

    session_info = {
        "proc": proc,
        "status": "pending",
        "url": extracted_url,
        "code": extracted_code,
        "az_user": None,
        "error": None,
        "created_at": time.time(),
    }
    AZ_LOGIN_SESSIONS[sid] = session_info

    def wait_worker():
        try:
            proc.wait(timeout=300)
            if proc.returncode == 0:
                user = az_user()
                session_info["status"] = "completed"
                session_info["az_user"] = user
                fabric.clear_tokens()
                PROJECTS_CACHE.clear()
            else:
                err = proc.stderr.read() or "Authentication cancelled or timed out."
                session_info["status"] = "error"
                session_info["error"] = err[-300:]
        except Exception as e:
            session_info["status"] = "error"
            session_info["error"] = str(e)

    threading.Thread(target=wait_worker, daemon=True).start()

    return {
        "status": "pending",
        "session_id": sid,
        "url": extracted_url,
        "code": extracted_code,
    }


@app.get("/api/az/login/poll")
def az_login_poll(session_id: str):
    """Polls status of an active Azure device code login session."""
    sess = AZ_LOGIN_SESSIONS.get(session_id)
    if not sess:
        raise HTTPException(404, "Invalid or expired session")
    return {
        "status": sess["status"],
        "az_user": sess["az_user"],
        "error": sess["error"],
    }


@app.post("/api/az/login")
def az_login():
    """Device code az login initiation."""
    return az_login_start()


@app.post("/api/az/logout")
def az_logout():
    """Signs out of Azure CLI and clears tokens."""
    if AZ:
        try:
            subprocess.run([AZ, "logout"], capture_output=True, text=True, timeout=30)
        except Exception:
            pass
    fabric.clear_tokens()
    PROJECTS_CACHE.clear()
    return {"status": "logged_out"}


class ClaudeKeyIn(BaseModel):
    api_key: str


@app.get("/api/claude/status")
def claude_status():
    """Returns Claude CLI and API key authentication state."""
    return get_claude_auth_status()


@app.post("/api/claude/login")
def claude_login_endpoint():
    """Triggers interactive `claude auth login` in console & browser."""
    bin_path = get_claude_bin()
    if not bin_path:
        return {
            "ok": False,
            "message": "Claude CLI is not found in PATH. You can enter your Anthropic API Key below, or install the CLI with: npm install -g @anthropic-ai/claude-code"
        }
    try:
        if os.name == "nt":
            # Launch in separate console window so that the browser opens and user sees instructions
            subprocess.Popen([bin_path, "auth", "login"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([bin_path, "auth", "login"])
        return {
            "ok": True,
            "message": "Launched Claude sign-in window. Please approve in your browser. The Studio will automatically detect completion.",
            "status": get_claude_auth_status(),
        }
    except Exception as e:
        return {"ok": False, "message": str(e)}


@app.post("/api/claude/install")
def claude_install_endpoint():
    """Installs Claude CLI globally using npm."""
    npm_bin = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_bin:
        candidates = [
            Path(r"C:\Program Files\nodejs\npm.cmd"),
            Path(r"C:\Program Files (x86)\nodejs\npm.cmd"),
            Path(os.environ.get("APPDATA", "")) / "npm" / "npm.cmd",
        ]
        for c in candidates:
            if c.is_file():
                npm_bin = str(c)
                break
    if not npm_bin:
        raise HTTPException(400, "Node.js npm is not found in PATH. Please install Node.js first.")
    try:
        res = subprocess.run([npm_bin, "install", "-g", "@anthropic-ai/claude-code"], capture_output=True, text=True, timeout=180)
        bin_path = get_claude_bin()
        return {
            "ok": bool(bin_path),
            "claude_bin": bin_path,
            "output": res.stdout[-400:] or res.stderr[-400:],
            "status": get_claude_auth_status(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to install Claude CLI: {str(e)}")


@app.post("/api/claude/api-key")
def claude_api_key_endpoint(body: ClaudeKeyIn):
    """Sets ANTHROPIC_API_KEY into .env and runtime environment."""
    if not body.api_key or len(body.api_key.strip()) < 8:
        raise HTTPException(400, "Invalid API key format. Please provide a valid Anthropic API key.")
    save_claude_api_key(body.api_key)
    return {"ok": True, "status": get_claude_auth_status()}


@app.post("/api/claude/logout")
def claude_logout_endpoint():
    """Clears Claude API key and credentials."""
    clear_claude_auth()
    return {"ok": True, "status": get_claude_auth_status()}


# ---------- Dashboard & wizard: direct read-only Fabric lookups (see fabric.py) ----------

PROJECTS_CACHE: dict[str, tuple[float, dict]] = {}
PROJECTS_TTL = 120


def fabric_call(fn, *args):
    if not AZ:
        raise HTTPException(400, "Azure CLI is not installed")
    try:
        return fn(AZ, *args)
    except fabric.FabricError as e:
        raise HTTPException(401 if e.status == 401 else 502, str(e))


def check_guid(*values: str) -> None:
    if not all(GUID.match(v or "") for v in values):
        raise HTTPException(400, "Workspace and lakehouse ids must be GUIDs")


@app.get("/api/fabric/workspaces")
def fabric_workspaces():
    if not AZ:
        items = mock_data.MOCK_WORKSPACES
        return {"workspaces": items, "default": items[0]["id"]}
    items = fabric_call(fabric.workspaces)
    env = read_env()["values"]
    default = next((w["id"] for w in items if w["id"] == env["FABRIC_WORKSPACE_ID"]
                    or (env["FABRIC_WORKSPACE_NAME"] and w["name"].lower() == env["FABRIC_WORKSPACE_NAME"].lower())), None)
    return {"workspaces": items, "default": default}


@app.get("/api/fabric/lakehouses")
def fabric_lakehouses(workspace_id: str):
    if not AZ:
        return {"lakehouses": mock_data.MOCK_LAKEHOUSES, "default": mock_data.MOCK_LAKEHOUSES[0]["name"]}
    check_guid(workspace_id)
    return {"lakehouses": fabric_call(fabric.lakehouses, workspace_id),
            "default": read_env()["values"]["RAW_LAKEHOUSE_NAME"] or None}


@app.get("/api/fabric/raw-folders")
def fabric_raw_folders(workspace_id: str, lakehouse_id: str):
    if not AZ:
        return {"folders": mock_data.MOCK_RAW_FOLDERS}
    check_guid(workspace_id, lakehouse_id)
    return {"folders": fabric_call(fabric.raw_folders, workspace_id, lakehouse_id)}


@app.get("/api/fabric/projects")
def fabric_projects(workspace_id: str, refresh: bool = False):
    """Projects = lakehouses (workspace root or folders) that contain project_status, with their latest status."""
    if not AZ:
        return mock_data.MOCK_PROJECTS
    check_guid(workspace_id)
    cached = PROJECTS_CACHE.get(workspace_id)
    if cached and not refresh and cached[0] > time.time() - PROJECTS_TTL:
        return cached[1]
    data = fabric_call(fabric.discover_projects, workspace_id)
    PROJECTS_CACHE[workspace_id] = (time.time(), data)
    return data


@app.post("/api/chat")
def chat(body: ChatIn):
    run_id = uuid.uuid4().hex
    use_mock = bool(body.demo_mode) or (os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes")) or (not CLAUDE or not skill_found())
    if use_mock:
        return StreamingResponse(
            mock_data.stream_mock_chat(body.prompt, run_id, session_id=body.session_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )
    return StreamingResponse(stream_claude(body, run_id), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


@app.post("/api/stop/{run_id}")
def stop(run_id: str):
    proc = RUNS.pop(run_id, None)
    if proc:
        kill_tree(proc)
    return {"stopped": bool(proc)}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Save a business-rules / STTM document into the project so Claude can read it."""
    upload_dir = PROJECT_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    name = re.sub(r"[^\w.\- ]", "_", Path(file.filename or "upload").name)
    dest = upload_dir / name
    dest.write_bytes(await file.read())
    return {"path": f"uploads/{name}", "size": dest.stat().st_size}


@app.get("/{path:path}")
def spa(path: str):
    """Serve the built React app (and its public files)."""
    file = (DIST / path).resolve()
    if path and file.is_file() and file.is_relative_to(DIST.resolve()):
        return FileResponse(file)
    if (DIST / "index.html").is_file():
        return FileResponse(DIST / "index.html")
    return HTMLResponse("<h3>UI not built.</h3><p>Run <code>cd frontend &amp;&amp; npm run build</code>, "
                        "or use <code>npm run dev</code> and open http://127.0.0.1:5173</p>", 503)


if __name__ == "__main__":
    import sys
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    has_skill = skill_found()
    claude_auth = get_claude_auth_status()
    az_account = az_user() if AZ else None

    print("=" * 66)
    print("  ADROSONIC - AI Data Engineering Studio")
    print(f"  Target Project Dir : {PROJECT_DIR}")
    print(f"  Medallion Skill    : {'[OK] Found' if has_skill else '[!] Not found under .claude/skills/medallion'}")
    print(f"  Fabric MCP Server  : {'[OK] Cloned (' + str(FABRIC_MCP_DIR) + ')' if FABRIC_MCP_DIR else '[*] Not cloned locally (can use npx package)'}")
    print(f"  Azure CLI          : {'[OK] Signed in (' + az_account + ')' if az_account else '[!] Not signed in' if AZ else '[!] Not found in PATH'}")
    print(f"  Claude Code Auth   : {'[OK] Authenticated (' + str(claude_auth['user'] or claude_auth['auth_method']) + ')' if claude_auth['authenticated'] else '[!] Not Authenticated'}")
    print(f"  Studio Endpoint    : http://{host}:{port}")
    if host == "0.0.0.0":
        print(f"  Local Access       : http://localhost:{port}")
    print("=" * 66)

    # Outside the app: Terminal sign-in prompt for Azure CLI when backend starts
    if AZ and not az_account:
        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            print("\n>>> AZURE CLI AUTHENTICATION SETUP <<<")
            print("Azure CLI is not signed in yet. Would you like to authenticate now?")
            print("  [1] Interactive browser login ('az login')")
            print("  [2] Device code login ('az login --use-device-code')")
            print("  [3] Skip for now (continue to Studio UI & sign in from the web page)")
            try:
                choice = input("Select an option [1/2/3, default: 3]: ").strip()
                if choice == "1":
                    print("Launching 'az login'...")
                    subprocess.run([AZ, "login"])
                    az_account = az_user()
                    if az_account:
                        print(f"[OK] Successfully signed in to Azure CLI as: {az_account}")
                elif choice == "2":
                    print("Launching 'az login --use-device-code'...")
                    subprocess.run([AZ, "login", "--use-device-code"])
                    az_account = az_user()
                    if az_account:
                        print(f"[OK] Successfully signed in to Azure CLI as: {az_account}")
                else:
                    print("Continuing startup... You can also sign in anytime inside the Studio UI!")
            except (EOFError, KeyboardInterrupt):
                print()
        else:
            print("  Notice: Azure CLI is not signed in. You can sign in anytime via the Studio UI at http://localhost:8000")

    # Outside the app: Terminal sign-in prompt when backend starts
    if not claude_auth["authenticated"]:
        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            print("\n>>> CLAUDE AUTHENTICATION SETUP <<<")
            print("Claude is not signed in yet. Would you like to authenticate now?")
            print("  [1] Sign in with Claude CLI browser login ('claude login')")
            print("  [2] Enter Anthropic API Key (sk-ant-...)")
            print("  [3] Skip for now (continue to Studio UI & sign in from the web page)")
            try:
                choice = input("Select an option [1/2/3, default: 3]: ").strip()
                if choice == "1":
                    if CLAUDE:
                        print("Launching 'claude auth login'...")
                        subprocess.run([CLAUDE, "auth", "login"])
                        claude_auth = get_claude_auth_status()
                        if claude_auth["authenticated"]:
                            print(f"[OK] Successfully authenticated as: {claude_auth['user']}")
                    else:
                        print("Claude CLI not found in PATH. Install with: npm i -g @anthropic-ai/claude-code")
                elif choice == "2":
                    key = input("Enter ANTHROPIC_API_KEY: ").strip()
                    if key:
                        save_claude_api_key(key)
                        print("[OK] Anthropic API Key saved to .env and activated!")
                else:
                    print("Continuing startup... You can also sign in anytime inside the Studio UI!")
            except (EOFError, KeyboardInterrupt):
                print()
        else:
            print("  Notice: Claude is not signed in. You can sign in anytime via the Studio UI at http://localhost:8000")

    uvicorn.run("server:app", host=host, port=port, reload=False)
