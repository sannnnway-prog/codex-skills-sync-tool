#!/usr/bin/env python3
"""
Local button panel for syncing Codex skills with GitHub via GitHub CLI.

It intentionally uses only Python's standard library plus the `gh` executable,
so the same folder can be shared with Windows and macOS teammates.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse


OWNER = "sannnnway-prog"
DEFAULT_BRANCH = "main"

SKILL_ROOT = Path(os.environ.get("CODEX_SKILLS_DIR", Path.home() / ".codex" / "skills")).expanduser()
STATE_DIR = Path(os.environ.get("CODEX_SKILL_SYNC_STATE", Path.home() / ".codex" / "skill-sync")).expanduser()
STATE_FILE = STATE_DIR / "state.json"
BACKUP_DIR = STATE_DIR / "backups"
LOG_FILE = STATE_DIR / "sync.log"

GROUPS = {
    "seo": {
        "label": "SEO 优化 Skills",
        "repo": "seo-optimization-skills",
        "description": "关键词、SERP、内外链、技术 SEO、结构化数据、排名、报告、预警等。",
        "skills": [
            "alert-manager",
            "backlink-analyzer",
            "competitor-analysis",
            "content-gap-analysis",
            "content-quality-auditor",
            "domain-authority-auditor",
            "entity-optimizer",
            "geo-content-optimizer",
            "internal-linking-optimizer",
            "keyword-research",
            "memory-management",
            "meta-tags-optimizer",
            "on-page-seo-auditor",
            "performance-reporter",
            "rank-tracker",
            "schema-markup-generator",
            "serp-analysis",
            "technical-seo-checker",
        ],
    },
    "blog": {
        "label": "Blog 创作 Skills",
        "repo": "blog-creation-skills",
        "description": "SEO 文章写作、旧文刷新、文章协作优化、WordPress 发布格式。",
        "skills": [
            "article-optimization-collab",
            "content-refresher",
            "seo-content-writer",
            "wordpress-blog-format",
        ],
    },
    "factory": {
        "label": "SEO 页面工厂 Skills",
        "repo": "seo-page-factory",
        "description": "页面工厂主流程及图片、视频、设计、GlobalGPT、飞书等配套工作流。",
        "skills": [
            "feature-page-factory",
            "agnes-video",
            "ai-product-workflow",
            "ark-seedream-image",
            "awesome-design-md",
            "figma-create-design-system-rules",
            "globalgpt",
            "globalgpt-coding",
            "globalgpt-image",
            "globalgpt-video",
            "gpt-image",
            "lark-mcp",
            "openai-next-image",
        ],
    },
}


APP_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Skills 同步面板</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #687180;
      --line: #d9dee7;
      --accent: #0d7c66;
      --accent-2: #2f5fbd;
      --warn: #a15c00;
      --bad: #b3261e;
      --shadow: 0 8px 24px rgba(29, 35, 43, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 22px 28px 14px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .sub {
      margin-top: 8px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }
    main {
      display: grid;
      grid-template-columns: minmax(260px, 360px) 1fr;
      gap: 18px;
      padding: 18px;
      max-width: 1180px;
      margin: 0 auto;
    }
    section, aside {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    aside {
      padding: 14px;
      align-self: start;
    }
    .group {
      display: grid;
      grid-template-columns: 24px 1fr;
      gap: 10px;
      padding: 12px;
      border-radius: 7px;
      border: 1px solid transparent;
      cursor: pointer;
    }
    .group + .group { margin-top: 8px; }
    .group:hover, .group.active {
      border-color: #b9c6d8;
      background: #f8fafc;
    }
    .group input { margin-top: 3px; }
    .group strong { display: block; font-size: 15px; }
    .group span { display: block; color: var(--muted); font-size: 12px; line-height: 1.45; margin-top: 4px; }
    .workspace {
      padding: 16px;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--line);
    }
    button {
      border: 1px solid #b8c2d0;
      background: #fff;
      color: var(--text);
      padding: 10px 13px;
      border-radius: 7px;
      font-size: 14px;
      cursor: pointer;
    }
    button.primary { background: var(--accent); color: white; border-color: var(--accent); }
    button.secondary { background: var(--accent-2); color: white; border-color: var(--accent-2); }
    button:disabled { opacity: .55; cursor: wait; }
    .status-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(160px, 1fr));
      gap: 10px;
      margin-top: 14px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 82px;
    }
    .metric b { display: block; font-size: 13px; color: var(--muted); font-weight: 600; }
    .metric span { display: block; margin-top: 8px; font-size: 18px; font-weight: 700; word-break: break-word; }
    .log {
      margin-top: 14px;
      border: 1px solid #cfd7e3;
      border-radius: 8px;
      background: #101418;
      color: #e6edf3;
      min-height: 360px;
      max-height: 520px;
      overflow: auto;
      padding: 13px;
      font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }
    .hint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
      margin-top: 12px;
    }
    .ok { color: var(--accent); }
    .warn { color: var(--warn); }
    .bad { color: var(--bad); }
    @media (max-width: 820px) {
      main { grid-template-columns: 1fr; }
      .status-grid { grid-template-columns: 1fr; }
      header { padding: 18px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Codex Skills 同步面板</h1>
    <div class="sub">选择要同步的项目，点击按钮即可在 GitHub 和本地 Codex Skills 之间同步。上传前会检查远端是否被别人更新过；下载前会备份本地目录。</div>
  </header>
  <main>
    <aside>
      <label class="group active" data-group="all">
        <input type="radio" name="group" value="all" checked>
        <div><strong>全部项目</strong><span>依次同步 SEO 优化、Blog 创作、SEO 页面工厂。</span></div>
      </label>
      <div id="groups"></div>
      <div class="hint">本面板需要电脑已登录 GitHub CLI：<code>gh auth login</code>。日常使用不需要手写命令。</div>
    </aside>
    <section class="workspace">
      <div class="toolbar">
        <button class="primary" id="pull">从 GitHub 更新到本地</button>
        <button class="secondary" id="push">把本地上传到 GitHub</button>
        <button id="status">状态检查</button>
      </div>
      <div class="status-grid">
        <div class="metric"><b>GitHub 登录</b><span id="auth">检查中</span></div>
        <div class="metric"><b>本地 Skills 目录</b><span id="root">检查中</span></div>
        <div class="metric"><b>当前选择</b><span id="selected">全部项目</span></div>
      </div>
      <div class="log" id="log">面板已打开。先点“状态检查”，确认 GitHub 登录和本地目录正常。</div>
      <div class="hint">如上传时提示远端冲突，说明同事已经更新过相关 skill。先点“从 GitHub 更新到本地”，面板会自动备份你本地旧版本，再按团队约定合并内容。</div>
    </section>
  </main>
<script>
const logEl = document.getElementById('log');
const authEl = document.getElementById('auth');
const rootEl = document.getElementById('root');
const selectedEl = document.getElementById('selected');
const groupsEl = document.getElementById('groups');
let busy = false;
let groupLabels = { all: '全部项目' };

function appendLog(text) {
  const now = new Date().toLocaleTimeString();
  logEl.textContent += `\n[${now}] ${text}`;
  logEl.scrollTop = logEl.scrollHeight;
}

function selectedGroup() {
  return document.querySelector('input[name="group"]:checked').value;
}

function setBusy(next) {
  busy = next;
  for (const btn of document.querySelectorAll('button')) btn.disabled = next;
}

async function api(path, body) {
  const options = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
  const res = await fetch(path, options);
  const data = await res.json();
  if (!res.ok || data.ok === false) throw new Error(data.error || JSON.stringify(data));
  return data;
}

async function loadStatus() {
  setBusy(true);
  try {
    const data = await api('/api/status');
    authEl.textContent = data.authenticated ? '已登录' : '未登录';
    authEl.className = data.authenticated ? 'ok' : 'bad';
    rootEl.textContent = data.skill_root;
    groupsEl.innerHTML = '';
    groupLabels = { all: '全部项目' };
    for (const group of data.groups) {
      groupLabels[group.key] = group.label;
      const label = document.createElement('label');
      label.className = 'group';
      label.dataset.group = group.key;
      label.innerHTML = `<input type="radio" name="group" value="${group.key}"><div><strong>${group.label}</strong><span>${group.repo} · 本地 ${group.local_count}/${group.total_count} 个 skill</span></div>`;
      groupsEl.appendChild(label);
    }
    bindGroups();
    appendLog(data.summary);
  } catch (err) {
    appendLog(`状态检查失败：${err.message}`);
  } finally {
    setBusy(false);
  }
}

function bindGroups() {
  for (const label of document.querySelectorAll('.group')) {
    label.addEventListener('click', () => {
      setTimeout(() => {
        for (const item of document.querySelectorAll('.group')) item.classList.remove('active');
        label.classList.add('active');
        selectedEl.textContent = groupLabels[selectedGroup()] || selectedGroup();
      }, 0);
    });
  }
}

async function runAction(action) {
  const group = selectedGroup();
  setBusy(true);
  appendLog(`${action === 'pull' ? '开始从 GitHub 更新到本地' : '开始上传本地到 GitHub'}：${groupLabels[group] || group}`);
  try {
    const data = await api(`/api/${action}`, { group });
    appendLog(data.log.join('\n'));
  } catch (err) {
    appendLog(`操作失败：${err.message}`);
  } finally {
    setBusy(false);
    await loadStatus();
  }
}

document.getElementById('status').addEventListener('click', loadStatus);
document.getElementById('pull').addEventListener('click', () => runAction('pull'));
document.getElementById('push').addEventListener('click', () => runAction('push'));
bindGroups();
loadStatus();
</script>
</body>
</html>
"""


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def log_line(message: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"[{dt.datetime.now().isoformat(timespec='seconds')}] {message}\n")


def run_gh(args: list[str], input_data: dict | None = None) -> dict | list | str:
    cmd = ["gh", *args]
    stdin = None
    if input_data is not None:
        stdin = json.dumps(input_data, ensure_ascii=False).encode("utf-8")
    try:
        proc = subprocess.run(
            cmd,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("找不到 GitHub CLI，请先安装 gh：https://cli.github.com/") from exc
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(stderr.strip() or stdout.strip() or f"gh exited with {proc.returncode}")
    text = stdout.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def gh_endpoint(repo: str, suffix: str) -> str:
    return f"repos/{OWNER}/{repo}/{suffix}"


def content_endpoint(repo: str, path: str) -> str:
    encoded = "/".join(quote(part, safe="") for part in path.split("/"))
    return gh_endpoint(repo, f"contents/{encoded}")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"files": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def state_key(group_key: str, path: str) -> str:
    return f"{group_key}:{path}"


def selected_groups(group_key: str) -> list[tuple[str, dict]]:
    if group_key == "all":
        return list(GROUPS.items())
    if group_key not in GROUPS:
        raise RuntimeError(f"未知项目：{group_key}")
    return [(group_key, GROUPS[group_key])]


def local_files_for_group(group: dict) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for skill in group["skills"]:
        skill_dir = SKILL_ROOT / skill
        if not skill_dir.exists():
            continue
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if should_skip_file(file_path):
                continue
            rel = file_path.relative_to(SKILL_ROOT).as_posix()
            result[rel] = file_path
    return result


def should_skip_file(path: Path) -> bool:
    parts = set(path.parts)
    ignored = {"__pycache__", ".git", ".venv", "node_modules", ".DS_Store"}
    if parts & ignored:
        return True
    lowered = path.name.lower()
    if lowered in {".env", ".env.local", ".env.production"}:
        return True
    if lowered.endswith((".pyc", ".pyo", ".log", ".tmp")):
        return True
    return False


def remote_tree(repo: str) -> dict[str, dict]:
    data = run_gh(["api", gh_endpoint(repo, f"git/trees/{DEFAULT_BRANCH}?recursive=1")])
    tree = {}
    for item in data.get("tree", []):
        if item.get("type") == "blob":
            tree[item["path"]] = item
    return tree


def remote_skill_files(repo: str, group: dict) -> dict[str, dict]:
    tree = remote_tree(repo)
    prefixes = tuple(f"{skill}/" for skill in group["skills"])
    return {path: item for path, item in tree.items() if path.startswith(prefixes)}


def get_remote_content(repo: str, path: str) -> tuple[bytes, str | None]:
    data = run_gh(["api", content_endpoint(repo, path)])
    if not isinstance(data, dict) or data.get("type") != "file":
        raise RuntimeError(f"远端文件不可读取：{repo}/{path}")
    content = data.get("content", "")
    raw = base64.b64decode(content.encode("ascii"))
    return raw, data.get("sha")


def put_remote_content(repo: str, path: str, raw: bytes, message: str, sha: str | None = None) -> str | None:
    payload = {
        "message": message,
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": DEFAULT_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    data = run_gh(["api", "--method", "PUT", content_endpoint(repo, path), "--input", "-"], payload)
    if isinstance(data, dict):
        return data.get("content", {}).get("sha")
    return None


def delete_remote_content(repo: str, path: str, sha: str, message: str) -> None:
    payload = {"message": message, "sha": sha, "branch": DEFAULT_BRANCH}
    run_gh(["api", "--method", "DELETE", content_endpoint(repo, path), "--input", "-"], payload)


def backup_skill_dir(skill: str, log: list[str]) -> None:
    src = SKILL_ROOT / skill
    if not src.exists():
        return
    dst = BACKUP_DIR / now_stamp() / skill
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    log.append(f"已备份本地 {skill} 到 {dst}")


def write_local_file(rel_path: str, raw: bytes) -> None:
    dest = SKILL_ROOT / Path(rel_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)


def pull_group(group_key: str, group: dict, state: dict, log: list[str]) -> None:
    repo = group["repo"]
    log.append(f"读取 GitHub：{OWNER}/{repo}")
    files = remote_skill_files(repo, group)
    if not files:
        log.append(f"远端没有找到 {group['label']} 的 skill 文件。")
        return
    for skill in group["skills"]:
        if any(path.startswith(f"{skill}/") for path in files):
            backup_skill_dir(skill, log)
            skill_path = SKILL_ROOT / skill
            if skill_path.exists():
                shutil.rmtree(skill_path)
    for rel_path in sorted(files):
        raw, sha = get_remote_content(repo, rel_path)
        write_local_file(rel_path, raw)
        if sha:
            state["files"][state_key(group_key, rel_path)] = {"sha": sha, "pulled_at": dt.datetime.now().isoformat()}
    log.append(f"已从 GitHub 更新 {len(files)} 个文件到 {SKILL_ROOT}")


def push_group(group_key: str, group: dict, state: dict, log: list[str]) -> None:
    repo = group["repo"]
    local_files = local_files_for_group(group)
    if not local_files:
        log.append(f"本地没有找到 {group['label']} 的 skill 文件。")
        return
    remote_files = remote_skill_files(repo, group)
    conflicts: list[str] = []
    for rel_path, remote_item in remote_files.items():
        key = state_key(group_key, rel_path)
        last_sha = state["files"].get(key, {}).get("sha")
        remote_sha = remote_item.get("sha")
        if last_sha and remote_sha and last_sha != remote_sha and rel_path in local_files:
            local_hash = hashlib.sha1(local_files[rel_path].read_bytes()).hexdigest()
            if local_hash != remote_sha:
                conflicts.append(rel_path)
    if conflicts:
        preview = "\n".join(f"- {path}" for path in conflicts[:20])
        raise RuntimeError(
            "GitHub 上已有同事更新过这些文件，已停止上传以避免覆盖。\n"
            "请先点“从 GitHub 更新到本地”，面板会备份你的本地版本。\n"
            f"{preview}"
        )
    uploaded = 0
    skipped = 0
    for rel_path, src in sorted(local_files.items()):
        raw = src.read_bytes()
        remote_sha = remote_files.get(rel_path, {}).get("sha")
        remote_raw = None
        if remote_sha:
            try:
                remote_raw, _ = get_remote_content(repo, rel_path)
            except RuntimeError:
                remote_raw = None
        if remote_raw == raw:
            skipped += 1
            if remote_sha:
                state["files"][state_key(group_key, rel_path)] = {"sha": remote_sha, "pushed_at": dt.datetime.now().isoformat()}
            continue
        message = f"Sync {group['label']} from local Codex"
        new_sha = put_remote_content(repo, rel_path, raw, message, remote_sha)
        if new_sha:
            state["files"][state_key(group_key, rel_path)] = {"sha": new_sha, "pushed_at": dt.datetime.now().isoformat()}
        uploaded += 1
    log.append(f"已上传 {uploaded} 个文件，跳过未变化文件 {skipped} 个：{OWNER}/{repo}")


def do_status() -> dict:
    authenticated = False
    auth_summary = ""
    try:
        auth_summary = str(run_gh(["auth", "status"]))
        authenticated = True
    except RuntimeError as exc:
        auth_summary = str(exc)
    groups = []
    for key, group in GROUPS.items():
        local_count = sum(1 for skill in group["skills"] if (SKILL_ROOT / skill / "SKILL.md").exists())
        groups.append({
            "key": key,
            "label": group["label"],
            "repo": f"{OWNER}/{group['repo']}",
            "local_count": local_count,
            "total_count": len(group["skills"]),
        })
    return {
        "ok": True,
        "authenticated": authenticated,
        "auth_summary": auth_summary,
        "skill_root": str(SKILL_ROOT),
        "groups": groups,
        "summary": f"状态检查完成：GitHub CLI {'已登录' if authenticated else '未登录'}，本地目录 {SKILL_ROOT}",
    }


def do_pull(group_key: str) -> dict:
    state = load_state()
    log: list[str] = []
    for key, group in selected_groups(group_key):
        pull_group(key, group, state, log)
    save_state(state)
    for line in log:
        log_line(line)
    return {"ok": True, "log": log}


def do_push(group_key: str) -> dict:
    state = load_state()
    log: list[str] = []
    for key, group in selected_groups(group_key):
        push_group(key, group, state, log)
    save_state(state)
    for line in log:
        log_line(line)
    return {"ok": True, "log": log}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/" or path == "/index.html":
                raw = APP_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            elif path == "/api/status":
                self._json(200, do_status())
            else:
                self._json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(body or "{}")
            group = payload.get("group", "all")
            if path == "/api/pull":
                self._json(200, do_pull(group))
            elif path == "/api/push":
                self._json(200, do_push(group))
            else:
                self._json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args: object) -> None:
        log_line(fmt % args)


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("CODEX_SKILL_SYNC_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Codex Skills 同步面板已启动：{url}")
    print("关闭这个窗口即可停止面板。")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
