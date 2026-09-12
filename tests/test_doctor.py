"""doctor 與 commit hook 的自檢：解析函式、受控詞彙、對本 repo 全跑無阻斷、hook 的放行／阻斷行為。"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "tools" / "doctor.py"
HOOK = ROOT / ".claude" / "hooks" / "pre_commit_check.py"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("anvil_doctor", DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[spec.name] = mod  # dataclass 解析型別註記時會查 sys.modules
    spec.loader.exec_module(mod)
    return mod


doctor = _load_doctor()


def test_parse_version():
    assert doctor.parse_version("v0.1.0") == (0, 1, 0)
    assert doctor.parse_version("[until: v1.2]") == (1, 2, 0)
    assert doctor.parse_version("nope") is None


def test_expiry_vocabulary():
    ok = ["[standing]", "[until: v0.2.0]", "[until: v1.0]", "[superseded-by: ../x.md]", "[retired: v0.1.0]"]
    bad = ["[active]", "[permanent]", "standing", "[until 0.2]", "[superseded-by:]"]
    assert all(doctor.EXPIRY_RE.match(s) for s in ok)
    assert not any(doctor.EXPIRY_RE.match(s) for s in bad)


def test_read_meta(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("# 標題\nStatus: active\nUpdated: 2026-09-12\nExpiry: [standing]\n\n內文 Status: 假的\n", encoding="utf-8")
    meta = doctor.read_meta(p)
    assert meta == {"Status": "active", "Updated": "2026-09-12", "Expiry": "[standing]"}


def test_doctor_on_this_repo_has_no_block():
    ctx = doctor.run(ROOT)
    blocks = [(c, m) for lvl, c, m in ctx.results if lvl == doctor.BLOCK]
    assert not blocks, f"doctor 阻斷：{blocks}"


def test_doctor_detects_expired_until(tmp_path):
    """[until: vX] 小於等於目前版本 → 阻斷。"""
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.3.0"\n[tool.anvil]\npackage = "pkg"\n', encoding="utf-8")
    (tmp_path / "docs" / "tasks").mkdir(parents=True)
    (tmp_path / "docs" / "tasks" / "2026-01-01-old.md").write_text(
        "# 舊任務\nStatus: active\nUpdated: 2026-01-01\nExpiry: [until: v0.2.0]\n", encoding="utf-8"
    )
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_metadata(ctx)
    assert any(lvl == doctor.BLOCK and "已到期" in m for lvl, _, m in ctx.results)


def test_doctor_limits_requires_evidence(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "limits.md").write_text(
        "# L\nStatus: active\nUpdated: 2026-09-12\nExpiry: [standing]\n\n"
        "| # | 首見 | 限制 | 處置 | 狀態 | 解除條件 | 解除證據 |\n|---|---|---|---|---|---|---|\n"
        "| L01 | v0.1.0 | x | accept | 已解除 | y | — |\n| L01 | v0.1.0 | dup | accept | 未解 | y | — |\n",
        encoding="utf-8",
    )
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_limits(ctx)
    msgs = [m for lvl, _, m in ctx.results if lvl == doctor.BLOCK]
    assert any("沒有解除證據" in m for m in msgs) and any("編號重複" in m for m in msgs)


def test_config_paths_are_respected(tmp_path):
    """[tool.anvil] 的 limits_file / tasks_dir / max_active_tasks 要真的被讀。"""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n'
        'limits_file = "docs/10_限制.md"\ntasks_dir = "work/tasks"\nmax_active_tasks = 2\n',
        encoding="utf-8",
    )
    (tmp_path / "work" / "tasks").mkdir(parents=True)
    for n in ("a", "b"):
        (tmp_path / "work" / "tasks" / f"2026-09-12-{n}.md").write_text(
            "# t\nStatus: active\nUpdated: 2026-09-12\nExpiry: [until: v0.2.0]\n", encoding="utf-8"
        )
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_limits(ctx)
    doctor.check_tasks(ctx)
    msgs = [(lvl, m) for lvl, _, m in ctx.results]
    assert any(lvl == doctor.WARN and "docs/10_限制.md" in m for lvl, m in msgs)
    assert any(lvl == doctor.OK and "active 任務單 2 份" in m for lvl, m in msgs)


def test_governed_globs_extend_metadata_check(tmp_path):
    """[[tool.anvil.governed]] 納管的檔案要進 metadata 檢查（缺欄位 → 阻斷）。"""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n'
        '[[tool.anvil.governed]]\nglob = "routes/**/PLAN.md"\nkind = "task"\n',
        encoding="utf-8",
    )
    (tmp_path / "routes" / "A" / "V1").mkdir(parents=True)
    (tmp_path / "routes" / "A" / "V1" / "PLAN.md").write_text("# 沒有中繼資料的規劃檔\n", encoding="utf-8")
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_metadata(ctx)
    assert any(lvl == doctor.BLOCK and "routes/A/V1/PLAN.md" in m for lvl, _, m in ctx.results)


def test_bootstrap_check(tmp_path):
    """樣板模式不吵；改名後 TEMPLATE_README 殘留與 README 佔位符要警告；README 連到已刪的檔要阻斷。"""
    def make(package: str, keep_template: bool, readme: str):
        for p in tmp_path.iterdir():
            p.unlink() if p.is_file() else None
        (tmp_path / "pyproject.toml").write_text(
            f'[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "{package}"\n', encoding="utf-8"
        )
        if keep_template:
            (tmp_path / "TEMPLATE_README.md").write_text("# t\n", encoding="utf-8")
        (tmp_path / "README.md").write_text(readme, encoding="utf-8")
        ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
        doctor.check_bootstrap(ctx)
        return [(lvl, m) for lvl, _, m in ctx.results]

    r = make("anvil", True, "# <專案名>\n")
    assert r[0][0] == doctor.OK
    r = make("mypkg", True, "# <專案名> — <一句話定位>\n<br>\n")
    assert any(lvl == doctor.WARN and "TEMPLATE_README.md" in m for lvl, m in r)
    assert any(lvl == doctor.WARN and "2 個佔位符" in m for lvl, m in r)
    r = make("mypkg", False, "> 以 [Anvil](TEMPLATE_README.md) 起始\n# Done\n")
    assert any(lvl == doctor.BLOCK for lvl, _ in r)
    r = make("mypkg", False, "# Done\n")
    assert r == [(doctor.OK, "樣板過渡已完成")]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8").stdout


def _init_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")


def test_coupled_blocks_when_require_missing(tmp_path):
    """改了 when 沒改 require → 阻斷；兩者都改 → 通過；staged 與 all 模式各自看對的集合。"""
    _init_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n'
        '[[tool.anvil.coupled]]\nwhen = "src/**/*.py"\nrequire = "CHANGELOG.md"\nreason = "改程式要記變更"\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# c\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    # 只改程式，未 stage：all 模式要擋，staged 模式看不到變更
    (tmp_path / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path), changes_mode="all")
    doctor.check_coupled(ctx)
    assert any(lvl == doctor.BLOCK and "CHANGELOG.md" in m and "改程式要記變更" in m for lvl, _, m in ctx.results)
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path), changes_mode="staged")
    doctor.check_coupled(ctx)
    assert ctx.results[-1][0] == doctor.OK and "沒有變更" in ctx.results[-1][2]
    # 兩者都改並 stage → 通過
    (tmp_path / "CHANGELOG.md").write_text("# c\n- 改了\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path), changes_mode="staged")
    doctor.check_coupled(ctx)
    assert ctx.results[-1][0] == doctor.OK


def test_ledgers_share_the_same_rules(tmp_path):
    """第二本帳（前綴 D）也要驗編號重複與解除證據。"""
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n'
        '[[tool.anvil.ledgers]]\nfile = "docs/debt.md"\nprefix = "D"\n',
        encoding="utf-8",
    )
    head = "# x\nStatus: active\nUpdated: 2026-09-12\nExpiry: [standing]\n\n| # | a | b | c | 狀態 | d | 證據 |\n|---|---|---|---|---|---|---|\n"
    (tmp_path / "docs" / "limits.md").write_text(head + "| L01 | v | x | accept | 未解 | y | — |\n", encoding="utf-8")
    (tmp_path / "docs" / "debt.md").write_text(head + "| D01 | v | x | accept | 已解除 | y | — |\n", encoding="utf-8")
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_limits(ctx)
    assert any(lvl == doctor.BLOCK and "docs/debt.md D01" in m for lvl, _, m in ctx.results)


def test_tasks_are_scanned_recursively(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n', encoding="utf-8")
    (tmp_path / "docs" / "tasks" / "v1").mkdir(parents=True)
    (tmp_path / "docs" / "tasks" / "v2").mkdir(parents=True)
    for sub in ("v1", "v2"):
        (tmp_path / "docs" / "tasks" / sub / "2026-09-12-x.md").write_text(
            "# t\nStatus: active\nUpdated: 2026-09-12\nExpiry: [until: v0.2.0]\n", encoding="utf-8"
        )
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_tasks(ctx)
    assert any(lvl == doctor.WARN and "2 份" in m for lvl, _, m in ctx.results)


def test_install_git_hooks(tmp_path):
    """乾跑不寫；--apply 寫入且含 doctor；重跑不產生備份；--uninstall --apply 移除。"""
    _init_repo(tmp_path)
    script = ROOT / "tools" / "install_git_hooks.py"
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    run = lambda *a: subprocess.run([sys.executable, str(script), "--root", str(tmp_path), *a],
                                    capture_output=True, text=True, encoding="utf-8")
    assert run().returncode == 0 and not hook.exists()
    assert run("--apply").returncode == 0 and "doctor.py" in hook.read_text(encoding="utf-8")
    assert run("--apply").returncode == 0 and not (tmp_path / ".git" / "hooks" / "pre-commit.bak").exists()
    assert run("--uninstall", "--apply").returncode == 0 and not hook.exists()


def test_milestone_routes_ignores_nesting_depth(tmp_path):
    """深度不同的路線都要被發現，且各自取自己的最大編號，不互相污染。"""
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\n', encoding="utf-8")
    for d in ("routes/A/Game/V1", "routes/A/Game/V7", "routes/B/V0", "routes/B/V5", "routes/C/_workshop", "routes/A/Game/V7/scripts/V9"):
        (tmp_path / d).mkdir(parents=True)
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    routes = ctx.milestone_routes("routes")
    assert routes["routes/A/Game"] == 7
    assert routes["routes/B"] == 5
    assert "routes/C" not in routes  # 沒有 V* 子目錄的不是路線
    assert routes["routes/A/Game/V7/scripts"] == 9  # 更深的巢狀也會被當成一條路線，由呼叫端用 pattern 或 base 收窄
    assert ctx.milestone_routes("nope") == {}


def test_links_scan_whole_repo_with_known_false_positive_patterns(tmp_path):
    """全庫掃描：一般檔斷連結阻斷；archive 內只警告；_templates、程式碼區塊、[[wiki]](註)、links-ignore 標記都跳過。"""
    _init_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.1.0"\n[tool.anvil]\npackage = "pkg"\nlinks_exclude = ["docs/vendor/**"]\n', encoding="utf-8"
    )
    for d in ("docs/archive", "docs/_templates", "docs/vendor", "docs/notes"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "docs" / "real.md").write_text("# r\n", encoding="utf-8")
    (tmp_path / "docs" / "notes" / "a.md").write_text(
        "見 [存在](../real.md) 與 [斷的](../nope.md)。\n"
        "記憶交叉引用 [[some-ref]](這是括號註解，不是連結)。\n"
        "```\n[程式碼裡的](../ghost.md)\n```\n行內 `[也是](../ghost2.md)` 略過。\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "archive" / "old.md").write_text("> ⛔ 已退役\n[搬家後斷了](../05.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "_templates" / "T.md").write_text("[V1](V1/) 示意\n", encoding="utf-8")
    (tmp_path / "docs" / "vendor" / "v.md").write_text("[外部](missing.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "ignored.md").write_text("<!-- anvil:links-ignore -->\n[x](missing.md)\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    ctx = doctor.Ctx(root=tmp_path, cfg=doctor.load_config(tmp_path))
    doctor.check_links(ctx)
    res = [(lvl, m) for lvl, _, m in ctx.results]
    assert [m for lvl, m in res if lvl == doctor.BLOCK] == ["docs/notes/a.md 連到不存在的 ../nope.md"]
    assert any(lvl == doctor.WARN and "docs/archive/old.md" in m and "退役" in m for lvl, m in res)
    assert not any("ghost" in m or "括號註解" in m or "V1/" in m or "vendor" in m or "ignored" in m for _, m in res)


def _run_hook(command: str, env_extra: dict | None = None, root: Path = ROOT) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root), **(env_extra or {})}
    env.pop("ANVIL_SKIP_DOCTOR", None) if not env_extra else None
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, encoding="utf-8", env=env
    )


def test_hook_ignores_non_commit():
    assert _run_hook("git status").returncode == 0


def test_hook_passes_when_doctor_clean():
    r = _run_hook('git commit -m "x"')
    assert r.returncode == 0, r.stderr


def test_hook_blocks_when_doctor_fails(tmp_path):
    """把一個壞掉的專案根餵給 hook（沒有 STATUS、沒有 CHANGELOG）→ exit 2。"""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "doctor.py").write_text(DOCTOR.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.0.1"\n', encoding="utf-8")
    r = _run_hook('git commit -m "x"', root=tmp_path)
    assert r.returncode == 2
    assert "阻斷" in r.stderr


def test_hook_escape_hatch(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "doctor.py").write_text(DOCTOR.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.0.1"\n', encoding="utf-8")
    r = _run_hook('git commit -m "x"', env_extra={"ANVIL_SKIP_DOCTOR": "1"}, root=tmp_path)
    assert r.returncode == 0 and "略過" in r.stderr
