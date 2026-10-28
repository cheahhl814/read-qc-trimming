#!/usr/bin/env python3
"""Structural smoke tests for the read-qc-trimming skill.

Encodes the domain-specific battle-test checks (skill-forge battle-test
sub-skill §2-§5) as an executable gate, so the skill's conformance is
reproducible rather than a one-time manual review:

  #2  contract wiring      — the Phase 0 sub-skill has an Inputs/Outputs contract
  #3  signature library    — every sub-skill has a signature library with >= 3 rows
  #4  docs-corpus          — every tool in pixi.toml has a populated corpus entry
  #5  pixi parse           — the manifest parses and pins the tools it promises

The domain-agnostic checks (#1 frontmatter, #6 git hygiene, #9/#10 update-check
wiring, #11 README hygiene) are implemented by skill-forge's own linter:

    python3 <skill-forge>/bin/skill-lint.py .

Usage:  python3 bin/skill-smoke.py
        pixi run test-smoke
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not cond else ""))


def tool_inventory() -> list[dict]:
    params = ROOT / "params.json"
    if not params.exists():
        return []
    import json

    try:
        return json.loads(params.read_text()).get("tool_inventory", [])
    except Exception:  # noqa: BLE001
        return []


def manifest() -> str:
    p = ROOT / "pixi.toml"
    return p.read_text() if p.exists() else ""


def main() -> int:
    print("== #2 Contract wiring ==")
    for sub in sorted(ROOT.glob("*/SKILL.md")) + sorted(ROOT.glob("*/*/SKILL.md")):
        text = sub.read_text()
        rel = sub.relative_to(ROOT)
        has_contract = bool(re.search(r"^##\s.*Inputs\s*/\s*Outputs", text, re.MULTILINE | re.IGNORECASE))
        check(f"{rel} declares an Inputs/Outputs contract", has_contract)

    print("== #3 Signature-library completeness ==")
    for sub in sorted(ROOT.glob("*/SKILL.md")) + sorted(ROOT.glob("*/*/SKILL.md")):
        text = sub.read_text()
        rel = sub.relative_to(ROOT)
        rows = re.findall(
            r"^## Troubleshooting — Signature library$(.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        count = len(re.findall(r"^\| `", rows[0], re.MULTILINE)) if rows else 0
        check(f"{rel} signature library has >= 3 entries", count >= 3, f"found {count}")

    print("== #4 Docs-corpus freshness ==")
    corpus = ROOT / "docs-corpus"
    check("docs-corpus/ exists", corpus.is_dir())
    check("docs-corpus/.fingerprints exists", (corpus / ".fingerprints").is_file())
    for tool in tool_inventory():
        name = tool.get("name", "")
        d = corpus / name
        index = d / "README.md"
        sources = [s for s in ("cli-reference.md", "github-readme.md", "web-docs.md")
                   if (d / s).is_file() and (d / s).stat().st_size > 0]
        check(f"docs-corpus/{name}/README.md exists", index.is_file())
        check(f"docs-corpus/{name} has >= 1 populated source", bool(sources),
              "all three fallback sources missing/empty")
        cli = d / "cli-reference.md"
        if cli.is_file():
            flags = len(re.findall(r"^\s*-{1,2}[A-Za-z][\w-]*", cli.read_text(), re.MULTILINE))
            check(f"docs-corpus/{name}/cli-reference.md has >= 2 flag-like lines", flags >= 2,
                  f"found {flags}")

    print("== #5 Pixi manifest ==")
    toml = manifest()
    check("pixi.toml exists", bool(toml))
    check("pixi.toml uses the [workspace] table (not the deprecated [project])",
          "[workspace]" in toml and "[project]" not in toml)
    check("pixi.toml declares exclude-newer (bounds the re-solve when the lock is gitignored)",
          "exclude-newer" in toml)
    check("pixi.toml wires the update-check task", "update-check" in toml)
    for tool in tool_inventory():
        name = tool.get("name", "")
        pkg = name.replace("_", "-")
        check(f"pixi.toml pins {name}", re.search(rf"^\s*{re.escape(pkg)}\s*=", toml, re.MULTILINE) is not None,
              f"no dependency entry for {name} (conda package {pkg})")
    # The manifest must actually parse.
    try:
        proc = subprocess.run(["pixi", "lock", "--dry-run"], cwd=ROOT,
                              capture_output=True, text=True, timeout=900)
        check("pixi lock --dry-run succeeds", proc.returncode == 0,
              (proc.stderr or proc.stdout).strip().splitlines()[-1] if (proc.stderr or proc.stdout).strip() else "")
    except FileNotFoundError:
        check("pixi is on PATH", False, "pixi not found")
    except subprocess.TimeoutExpired:
        check("pixi lock --dry-run succeeds", False, "timed out")

    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
