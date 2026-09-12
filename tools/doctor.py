"""doctor — Anvil 專案的文件新鮮度與協作紀律檢查。

## 為什麼需要這支
規則寫在 AGENTS.md 裡不會自己被遵守。樣板誕生前盤點的兩個既有專案給了正反兩面的證據：
一個專案裡唯二沒被任何工具盯著的兩份索引文件正好是落後最久的；另一個專案有完整的文件生命週期腳本，
卻沒掛到任何強制點，全靠代理人記得跑。
這支的存在理由是把「文件要不要更新」從「靠記得」變成「一個會失敗的檢查」，
並由 .claude/hooks/pre_commit_check.py 在每次 git commit 前呼叫。

## 檢查什麼
 1. version   版本三處一致（pyproject / <package>/__init__.py / 最新 git tag）+ CHANGELOG 有該版本段
 2. status    STATUS.md 的 Version 等於 pyproject；Updated 落後最近 commit 超過 N 天則警告
 3. agents    AGENTS.md 存在且不超過行數上限；CLAUDE.md 含 @AGENTS.md
 4. links     README.md / AGENTS.md / STATUS.md 內的相對連結都指到存在的路徑
 5. metadata  治理文件（STATUS、docs/limits.md、decisions、tasks、archive）都有 Status/Updated/Expiry，
              詞彙在受控範圍內，[until: vX.Y] 到期者列出，[superseded-by:] 目標存在
 6. tasks     同時 Status: active 的任務單不超過一份；檔名以 YYYY-MM-DD- 開頭
 7. archive   docs/archive 內每檔首行是「> ⛔ 已退役」標記
 8. limits    docs/limits.md 編號不重複；標「已解除」的條目附證據
 9. adr       docs/decisions 編號從 0001 連續；每份的「選項」節至少列兩項（含被拒選項）
10. tools     tools/ 內腳本 docstring 含四段（為什麼需要／檢查什麼或做什麼／安全／退出碼）
11. gitignore .gitignore 涵蓋敏感檔樣式；git 追蹤清單內沒有敏感檔
12. ext       載入 tools/doctor_ext/*.py 的 run(ctx)，讓延伸層加自己的檢查
13. bootstrap 專案已從樣板改名後：TEMPLATE_README.md 應已刪除、README.md 不應殘留中文佔位符；
              樣板模式（package 仍是 anvil）不檢查

## 安全設計
只讀不寫。不改任何檔案、不打網路；外部程式只呼叫 git 的唯讀子命令。沒有 git 或沒有 tag 時降級為警告，
不阻斷。不因為「還有未解除的限制」而失敗——limits 檢查只驗結構（編號、證據），不驗內容。

## 退出碼
0 = 沒有阻斷項（可能有警告）；1 = 有阻斷項。
用法：python tools/doctor.py [--quick] [--root <專案根>] [--list]
  --quick  跳過 links 與 ext（給 commit hook 用）
  --list   只列出檢查名稱
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import fnmatch
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

BLOCK, WARN, OK = "BLOCK", "WARN", "OK"
SYMBOL = {BLOCK: "✗", WARN: "⚠", OK: "✓"}

VERSION_RE = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?")
EXPIRY_RE = re.compile(
    r"^\[(?:standing|until: v?\d+\.\d+(?:\.\d+)?|superseded-by: [^\]]+|retired: v?\d+\.\d+(?:\.\d+)?)\]$"
)
META_KEYS = ("Status", "Version", "Created", "Updated", "Expiry")
STATUS_VOCAB = {
    "general": {"active", "retired"},
    "task": {"draft", "active", "done", "dropped"},
    "adr": {"proposed", "accepted", "rejected", "superseded"},
}
DEFAULT_CFG = {
    "package": "anvil",
    "docs_dir": "docs",
    "status_file": "STATUS.md",
    "limits_file": "docs/limits.md",       # 既有專案可指向自己的限制總帳，不必改名
    "tasks_dir": "docs/tasks",
    "decisions_dir": "docs/decisions",
    "archive_dir": "docs/archive",
    "max_active_tasks": 1,
    "governed": [],                        # 額外納管的文件：[{"glob": "...", "kind": "task|adr|general"}]
    "status_stale_days": 14,
    "agents_max_lines": 150,
    "sensitive_globs": [".env", ".env.*", "credentials.json", "token.json", "cookie.txt", "*.db", "*.sqlite"],
}


@dataclass
class Ctx:
    """傳給每項檢查（含延伸層 run(ctx)）的上下文。"""

    root: Path
    cfg: dict
    quick: bool = False
    results: list[tuple[str, str, str]] = field(default_factory=list)  # (level, check, message)

    def add(self, level: str, check: str, message: str) -> None:
        self.results.append((level, check, message))

    @property
    def docs(self) -> Path:
        return self.root / self.cfg["docs_dir"]

    def git(self, *args: str) -> str | None:
        """唯讀 git 呼叫；沒有 git 或不是 repo 回 None。"""
        try:
            out = subprocess.run(
                ["git", *args], cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
        except FileNotFoundError:
            return None
        if out.returncode != 0:
            return None
        return out.stdout.strip()


# ── 共用解析 ──────────────────────────────────────────────────────────


def load_config(root: Path) -> dict:
    """讀 pyproject.toml 的 [project].version 與 [tool.anvil]；沒有 tomllib 就退回簡易解析。"""
    cfg = dict(DEFAULT_CFG)
    cfg["pyproject_version"] = None
    py = root / "pyproject.toml"
    if not py.exists():
        return cfg
    text = py.read_text(encoding="utf-8")
    data = None
    try:
        import tomllib  # Python 3.11+

        data = tomllib.loads(text)
    except ModuleNotFoundError:
        try:
            import tomli  # type: ignore

            data = tomli.loads(text)
        except ModuleNotFoundError:
            data = None
    if data is not None:
        cfg["pyproject_version"] = (data.get("project") or {}).get("version")
        cfg.update((data.get("tool") or {}).get("anvil") or {})
        return cfg
    # 簡易退路：只抓需要的幾個 key
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.M)
    cfg["pyproject_version"] = m.group(1) if m else None
    sec = re.search(r"^\[tool\.anvil\](.*?)(?=^\[|\Z)", text, re.M | re.S)
    if sec:
        for key, val in re.findall(r'^\s*(\w+)\s*=\s*(".*?"|\d+|\[.*?\])\s*(?:#.*)?$', sec.group(1), re.M):
            if val.startswith('"'):
                cfg[key] = val.strip('"')
            elif val.startswith("["):
                cfg[key] = re.findall(r'"([^"]*)"', val)
            else:
                cfg[key] = int(val)
    return cfg


def parse_version(s: str | None) -> tuple[int, int, int] | None:
    if not s:
        return None
    m = VERSION_RE.search(s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)


def read_meta(path: Path, max_lines: int = 15) -> dict[str, str]:
    """讀檔案開頭的 `Key: value` 中繼資料行。"""
    meta: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:max_lines]
    except (OSError, UnicodeDecodeError):
        return meta
    for line in lines:
        m = re.match(r"^(Status|Version|Created|Updated|Expiry):\s*(.+?)\s*$", line)
        if m:
            meta.setdefault(m.group(1), m.group(2))
    return meta


def rel(ctx: Ctx, p: Path) -> str:
    try:
        return p.relative_to(ctx.root).as_posix()
    except ValueError:
        return p.as_posix()


def latest_tag_version(ctx: Ctx) -> tuple[str | None, tuple[int, int, int] | None]:
    out = ctx.git("tag", "--list", "v*")
    if not out:
        return None, None
    best_name, best_ver = None, None
    for name in out.splitlines():
        v = parse_version(name)
        if v and (best_ver is None or v > best_ver):
            best_name, best_ver = name, v
    return best_name, best_ver


def current_version(ctx: Ctx) -> tuple[int, int, int] | None:
    return parse_version(ctx.cfg.get("pyproject_version"))


# ── 各項檢查 ──────────────────────────────────────────────────────────


def check_version(ctx: Ctx) -> None:
    name = "version"
    pv = ctx.cfg.get("pyproject_version")
    if not pv:
        ctx.add(BLOCK, name, "pyproject.toml 沒有 [project].version")
        return
    init = ctx.root / ctx.cfg["package"] / "__init__.py"
    if not init.exists():
        ctx.add(BLOCK, name, f"找不到 {rel(ctx, init)}（[tool.anvil].package 設對了嗎？）")
    else:
        m = re.search(r'^__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"), re.M)
        iv = m.group(1) if m else None
        if iv != pv:
            ctx.add(BLOCK, name, f"__version__={iv!r} 與 pyproject version={pv!r} 不一致")
    tag_name, tag_ver = latest_tag_version(ctx)
    if tag_ver is None:
        ctx.add(WARN, name, "尚無 v* tag（首次收關時打 tag 即可）")
    elif tag_ver != parse_version(pv):
        ctx.add(WARN, name, f"最新 tag {tag_name} 與 pyproject {pv} 不同（開發中正常；收關時要一致）")
    ch = ctx.root / "CHANGELOG.md"
    if not ch.exists():
        ctx.add(BLOCK, name, "沒有 CHANGELOG.md")
    elif f"## [{pv}]" not in ch.read_text(encoding="utf-8"):
        ctx.add(BLOCK, name, f"CHANGELOG.md 沒有 `## [{pv}]` 段")
    if not any(lvl != OK and c == name for lvl, c, _ in ctx.results):
        ctx.add(OK, name, f"版本 {pv} 三處一致，CHANGELOG 有該段")


def check_status(ctx: Ctx) -> None:
    name = "status"
    sf = ctx.root / ctx.cfg["status_file"]
    if not sf.exists():
        ctx.add(BLOCK, name, f"沒有 {ctx.cfg['status_file']}")
        return
    meta = read_meta(sf)
    pv = ctx.cfg.get("pyproject_version")
    if meta.get("Version") != pv:
        ctx.add(BLOCK, name, f"STATUS Version={meta.get('Version')!r} 與 pyproject {pv!r} 不一致")
    upd = meta.get("Updated")
    try:
        upd_date = dt.date.fromisoformat(upd) if upd else None
    except ValueError:
        upd_date = None
    if upd_date is None:
        ctx.add(BLOCK, name, "STATUS Updated 缺少或不是 YYYY-MM-DD")
    else:
        last = ctx.git("log", "-1", "--format=%cs")
        try:
            last_date = dt.date.fromisoformat(last) if last else None
        except ValueError:
            last_date = None
        if last_date:
            lag = (last_date - upd_date).days
            if lag > int(ctx.cfg["status_stale_days"]):
                ctx.add(WARN, name, f"STATUS Updated={upd} 落後最近 commit {last} 共 {lag} 天")
    if not any(lvl != OK and c == name for lvl, c, _ in ctx.results):
        ctx.add(OK, name, f"STATUS 版本一致，Updated={upd}")


def check_agents(ctx: Ctx) -> None:
    name = "agents"
    ag = ctx.root / "AGENTS.md"
    if not ag.exists():
        ctx.add(BLOCK, name, "沒有 AGENTS.md")
        return
    n = len(ag.read_text(encoding="utf-8").splitlines())
    limit = int(ctx.cfg["agents_max_lines"])
    if n > limit:
        ctx.add(WARN, name, f"AGENTS.md {n} 行，超過上限 {limit}；先問每一行「刪掉會出錯嗎」")
    cl = ctx.root / "CLAUDE.md"
    if cl.exists() and "@AGENTS.md" not in cl.read_text(encoding="utf-8"):
        ctx.add(WARN, name, "CLAUDE.md 沒有 `@AGENTS.md`，Claude Code 讀不到主規範")
    if not any(lvl != OK and c == name for lvl, c, _ in ctx.results):
        ctx.add(OK, name, f"AGENTS.md {n} 行，CLAUDE.md 有 import")


LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def check_links(ctx: Ctx) -> None:
    name = "links"
    bad = 0
    for fname in ("README.md", "AGENTS.md", ctx.cfg["status_file"]):
        f = ctx.root / fname
        if not f.exists():
            continue
        for target in LINK_RE.findall(f.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:") or "<" in target:
                continue
            if not (f.parent / target).exists():
                bad += 1
                ctx.add(BLOCK, name, f"{fname} 連到不存在的 {target}")
    if not bad:
        ctx.add(OK, name, "README / AGENTS / STATUS 的相對連結都存在")


def governed_files(ctx: Ctx) -> list[tuple[Path, str]]:
    """回傳 (檔案, 類別)。類別決定 Status 詞彙。"""
    out: list[tuple[Path, str]] = []
    sf = ctx.root / ctx.cfg["status_file"]
    if sf.exists():
        out.append((sf, "general"))
    lim = ctx.root / ctx.cfg["limits_file"]
    if lim.exists():
        out.append((lim, "general"))
    for key, kind in (("decisions_dir", "adr"), ("tasks_dir", "task"), ("archive_dir", "general")):
        d = ctx.root / ctx.cfg[key]
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                if p.name.lower() == "readme.md":
                    continue
                out.append((p, kind))
    # 延伸點：[[tool.anvil.governed]] glob="..." kind="task|adr|general"，讓專案把自己的文件納入同一套檢查
    seen = {p for p, _ in out}
    for entry in ctx.cfg.get("governed") or []:
        glob, kind = entry.get("glob"), entry.get("kind", "general")
        if not glob or kind not in STATUS_VOCAB:
            continue
        for p in sorted(ctx.root.glob(glob)):
            if p.is_file() and p not in seen and p.name.lower() != "readme.md":
                out.append((p, kind))
                seen.add(p)
    return out


def check_metadata(ctx: Ctx) -> None:
    name = "metadata"
    cur = current_version(ctx)
    problems = 0
    for path, kind in governed_files(ctx):
        r = rel(ctx, path)
        meta = read_meta(path)
        missing = [k for k in ("Status", "Updated", "Expiry") if k not in meta]
        if missing:
            problems += 1
            ctx.add(BLOCK, name, f"{r} 缺 {'/'.join(missing)}")
            continue
        status = meta["Status"].split()[0].lower()
        if status not in STATUS_VOCAB[kind]:
            problems += 1
            ctx.add(BLOCK, name, f"{r} Status={meta['Status']!r} 不在 {sorted(STATUS_VOCAB[kind])}")
        exp = meta["Expiry"]
        if not EXPIRY_RE.match(exp):
            problems += 1
            ctx.add(BLOCK, name, f"{r} Expiry={exp!r} 不在受控詞彙（[standing]／[until: vX.Y]／[superseded-by: 路徑]／[retired: vX.Y]）")
            continue
        try:
            dt.date.fromisoformat(meta["Updated"])
        except ValueError:
            problems += 1
            ctx.add(BLOCK, name, f"{r} Updated={meta['Updated']!r} 不是 YYYY-MM-DD")
        if exp.startswith("[until:"):
            until = parse_version(exp)
            if cur and until and until <= cur:
                problems += 1
                ctx.add(BLOCK, name, f"{r} 已到期（Expiry {exp}，目前版本 v{'.'.join(map(str, cur))}）：結案、延期或退役")
            if status in ("done", "dropped", "retired", "superseded", "rejected"):
                problems += 1
                ctx.add(WARN, name, f"{r} Status={status} 但 Expiry 還是 {exp}，應改成 [retired: vX.Y]")
        elif exp.startswith("[superseded-by:"):
            target = exp[len("[superseded-by:") : -1].strip()
            if not (path.parent / target).exists():
                problems += 1
                ctx.add(BLOCK, name, f"{r} 的 superseded-by 目標不存在：{target}")
        elif exp == "[standing]" and status in ("retired", "superseded"):
            problems += 1
            ctx.add(WARN, name, f"{r} Status={status} 卻是 [standing]，應改 [superseded-by:] 或 [retired:]")
        if kind == "general" and path.parent.name == "archive" and status != "retired":
            problems += 1
            ctx.add(WARN, name, f"{r} 在 archive/ 但 Status={status}，應為 retired")
    if not problems:
        ctx.add(OK, name, f"{len(governed_files(ctx))} 份治理文件的中繼資料合規，無到期項")


def check_tasks(ctx: Ctx) -> None:
    name = "tasks"
    d = ctx.root / ctx.cfg["tasks_dir"]
    max_active = int(ctx.cfg["max_active_tasks"])
    if not d.is_dir():
        ctx.add(WARN, name, f"沒有 {ctx.cfg['tasks_dir']}/")
        return
    active: list[str] = []
    bad_name = 0
    for p in sorted(d.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}-", p.name):
            bad_name += 1
            ctx.add(WARN, name, f"{rel(ctx, p)} 檔名不是 YYYY-MM-DD- 開頭")
        if read_meta(p).get("Status", "").split()[:1] == ["active"]:
            active.append(p.name)
    if len(active) > max_active:
        ctx.add(WARN, name, f"同時 active 的任務單有 {len(active)} 份：{', '.join(active)}（上限 {max_active}）")
    if len(active) <= max_active and not bad_name:
        ctx.add(OK, name, f"active 任務單 {len(active)} 份")


def check_archive(ctx: Ctx) -> None:
    name = "archive"
    d = ctx.root / ctx.cfg["archive_dir"]
    if not d.is_dir():
        ctx.add(OK, name, "沒有 archive/（尚無退役文件）")
        return
    bad = 0
    for p in sorted(d.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        first = next((ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()), "")
        if not first.startswith("> ⛔"):
            bad += 1
            ctx.add(WARN, name, f"{rel(ctx, p)} 首行沒有「> ⛔ 已退役」標記")
    if not bad:
        ctx.add(OK, name, "archive 內文件都有退役標記")


def check_limits(ctx: Ctx) -> None:
    name = "limits"
    f = ctx.root / ctx.cfg["limits_file"]
    if not f.exists():
        ctx.add(WARN, name, f"沒有 {ctx.cfg['limits_file']}")
        return
    seen: set[str] = set()
    problems = 0
    rows = 0
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or not re.fullmatch(r"L\d+", cells[0]):
            continue
        rows += 1
        lid = cells[0]
        if lid in seen:
            problems += 1
            ctx.add(BLOCK, name, f"limits.md 編號重複：{lid}")
        seen.add(lid)
        if len(cells) >= 7 and "已解除" in cells[4] and cells[6] in ("", "—", "-"):
            problems += 1
            ctx.add(BLOCK, name, f"limits.md {lid} 標已解除但沒有解除證據")
    if not problems:
        ctx.add(OK, name, f"limits.md {rows} 條，編號不重複，已解除者皆附證據")


def check_adr(ctx: Ctx) -> None:
    name = "adr"
    d = ctx.root / ctx.cfg["decisions_dir"]
    if not d.is_dir():
        ctx.add(WARN, name, "沒有 docs/decisions/")
        return
    nums: list[int] = []
    problems = 0
    for p in sorted(d.glob("*.md")):
        m = re.match(r"^(\d{4})-", p.name)
        if not m:
            if p.name.lower() != "readme.md":
                problems += 1
                ctx.add(WARN, name, f"{rel(ctx, p)} 檔名不是 NNNN- 開頭")
            continue
        nums.append(int(m.group(1)))
        text = p.read_text(encoding="utf-8")
        sec = re.search(r"^## 選項.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
        items = re.findall(r"^\s*(?:\d+\.|[-*]|\|)\s*\S", sec.group(1), re.M) if sec else []
        if len(items) < 2:
            problems += 1
            ctx.add(WARN, name, f"{rel(ctx, p)} 的「選項」節少於兩項（被拒選項也要記）")
    if nums and nums != list(range(1, len(nums) + 1)):
        problems += 1
        ctx.add(WARN, name, f"ADR 編號不連續：{nums}")
    if not problems:
        ctx.add(OK, name, f"{len(nums)} 份 ADR 編號連續，選項節齊全")


def check_tools(ctx: Ctx) -> None:
    name = "tools"
    d = ctx.root / "tools"
    if not d.is_dir():
        ctx.add(OK, name, "沒有 tools/")
        return
    problems = 0
    files = [p for p in list(d.glob("*.py")) + list((d / "doctor_ext").glob("*.py")) if p.name != "__init__.py"]
    for p in files:
        try:
            doc = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or ""
        except SyntaxError as e:
            problems += 1
            ctx.add(BLOCK, name, f"{rel(ctx, p)} 語法錯誤：{e}")
            continue
        need = ["為什麼需要", "安全", "退出碼"]
        missing = [k for k in need if k not in doc]
        if "檢查什麼" not in doc and "做什麼" not in doc:
            missing.append("檢查什麼／做什麼")
        if missing:
            problems += 1
            ctx.add(WARN, name, f"{rel(ctx, p)} docstring 缺：{'、'.join(missing)}")
    if not problems:
        ctx.add(OK, name, f"{len(files)} 支腳本的 docstring 四段齊全")


def check_gitignore(ctx: Ctx) -> None:
    name = "gitignore"
    gi = ctx.root / ".gitignore"
    globs: list[str] = list(ctx.cfg["sensitive_globs"])
    if not gi.exists():
        ctx.add(BLOCK, name, "沒有 .gitignore")
        return
    lines = {ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()}
    missing = [g for g in globs if g not in lines]
    if missing:
        ctx.add(WARN, name, f".gitignore 沒有列：{', '.join(missing)}")
    tracked = ctx.git("ls-files")
    leaked = []
    if tracked is not None:
        for f in tracked.splitlines():
            base = f.rsplit("/", 1)[-1]
            if base.endswith(".example"):
                continue
            if any(fnmatch.fnmatch(base, g) for g in globs):
                leaked.append(f)
    for f in leaked:
        ctx.add(BLOCK, name, f"敏感檔已被 git 追蹤：{f}")
    if not missing and not leaked:
        ctx.add(OK, name, "敏感檔樣式都在 .gitignore，git 追蹤清單乾淨")


def check_ext(ctx: Ctx) -> None:
    name = "ext"
    d = ctx.root / "tools" / "doctor_ext"
    mods = [p for p in sorted(d.glob("*.py")) if not p.name.startswith("_")] if d.is_dir() else []
    if not mods:
        ctx.add(OK, name, "沒有延伸層檢查")
        return
    for p in mods:
        try:
            spec = importlib.util.spec_from_file_location(f"doctor_ext_{p.stem}", p)
            assert spec and spec.loader
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod  # 延伸層若用 dataclass 需要先註冊
            spec.loader.exec_module(mod)
            run = getattr(mod, "run", None)
            if run is None:
                ctx.add(WARN, name, f"{rel(ctx, p)} 沒有 run(ctx)")
                continue
            extra = run(ctx) or []
            for item in extra:
                lvl, msg = item[0], item[-1]
                ctx.add(lvl, f"ext:{p.stem}", msg)
        except Exception as e:  # 延伸層壞掉不該擋住基礎檢查
            ctx.add(WARN, name, f"{rel(ctx, p)} 執行失敗：{e}")


PLACEHOLDER_RE = re.compile(r"<[^<>\n]*[一-鿿][^<>\n]*>")  # 尖括號內含中文 = 佔位符；HTML 標籤是純 ASCII 不會命中
TEMPLATE_PACKAGE = "anvil"
TEMPLATE_README = "TEMPLATE_README.md"


def check_bootstrap(ctx: Ctx) -> None:
    """專案是否已完成從樣板到正式專案的過渡。"""
    name = "bootstrap"
    if ctx.cfg["package"] == TEMPLATE_PACKAGE:
        ctx.add(OK, name, "樣板模式（package 仍是 anvil），不檢查過渡狀態")
        return
    problems = 0
    if (ctx.root / TEMPLATE_README).exists():
        problems += 1
        ctx.add(WARN, name, f"專案已改名，{TEMPLATE_README} 可以刪除了（樣板說明對正式專案沒有用）")
    readme = ctx.root / "README.md"
    if readme.exists():
        hits = PLACEHOLDER_RE.findall(readme.read_text(encoding="utf-8"))
        if hits:
            problems += 1
            sample = "、".join(h if len(h) <= 24 else h[:24] + "…>" for h in hits[:3]) + ("…" if len(hits) > 3 else "")
            ctx.add(WARN, name, f"README.md 還有 {len(hits)} 個佔位符：{sample}")
        if TEMPLATE_README in readme.read_text(encoding="utf-8") and not (ctx.root / TEMPLATE_README).exists():
            problems += 1
            ctx.add(BLOCK, name, f"README.md 仍連到已刪除的 {TEMPLATE_README}，刪掉開頭那行提示")
    if not problems:
        ctx.add(OK, name, "樣板過渡已完成")


CHECKS = [
    ("version", check_version, False),
    ("status", check_status, False),
    ("agents", check_agents, False),
    ("links", check_links, True),  # True = --quick 時跳過
    ("metadata", check_metadata, False),
    ("tasks", check_tasks, False),
    ("archive", check_archive, False),
    ("limits", check_limits, False),
    ("adr", check_adr, False),
    ("tools", check_tools, False),
    ("gitignore", check_gitignore, False),
    ("bootstrap", check_bootstrap, False),
    ("ext", check_ext, True),
]


# ── 主程式 ────────────────────────────────────────────────────────────


def run(root: Path, quick: bool = False) -> Ctx:
    ctx = Ctx(root=root, cfg=load_config(root), quick=quick)
    for _, fn, skip_on_quick in CHECKS:
        if quick and skip_on_quick:
            continue
        fn(ctx)
    return ctx


def report(ctx: Ctx) -> int:
    counts = {BLOCK: 0, WARN: 0, OK: 0}
    for lvl, check, msg in ctx.results:
        counts[lvl] += 1
        print(f"{SYMBOL[lvl]} [{check}] {msg}")
    print(f"\n結果：阻斷={counts[BLOCK]} 警告={counts[WARN]} 通過={counts[OK]}")
    if counts[BLOCK]:
        print("★ 先解決阻斷項再繼續。")
        return 1
    print("無阻斷項，可繼續。" if counts[WARN] else "→ 全綠")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 管線預設 cp950
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Anvil doctor：文件新鮮度與協作紀律檢查（只讀）")
    ap.add_argument("--quick", action="store_true", help="跳過 links 與 ext（commit hook 用）")
    ap.add_argument("--root", default=None, help="專案根目錄（預設：本檔的上上層）")
    ap.add_argument("--list", action="store_true", help="只列檢查名稱")
    args = ap.parse_args(argv)
    if args.list:
        for name, _, skip in CHECKS:
            print(f"{name}{'  (--quick 跳過)' if skip else ''}")
        return 0
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    return report(run(root, quick=args.quick))


if __name__ == "__main__":
    sys.exit(main())
