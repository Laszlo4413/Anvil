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
