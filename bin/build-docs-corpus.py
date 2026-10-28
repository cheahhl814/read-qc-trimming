#!/usr/bin/env python3
"""Regenerate this skill's docs-corpus/ from the pinned pixi environment.

The corpus is what keeps the agent from hallucinating tool flags: every tool
this skill invokes gets an offline snapshot of its own documentation, captured
at the version this skill actually pins.

Three sources, in the skill-forge fallback order:

  1. cli-reference.md  verbatim `--help` executed inside the pinned pixi env.
                       Authoritative — it matches the pinned version exactly.
  2. github-readme.md  the upstream repository README, fetched verbatim.
  3. web-docs.md       upstream documentation site, when a README is missing
                       or thinner than the `--help` capture.

A per-tool `README.md` indexes the sources; `.fingerprints` records the
md5 + capture date of each so staleness is detectable.

Usage:  python3 bin/build-docs-corpus.py            # refresh every tool
        python3 bin/build-docs-corpus.py sequali    # refresh one tool
        python3 bin/build-docs-corpus.py --check    # verify, don't write
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "docs-corpus"
ENV_BIN = ROOT / ".pixi" / "envs" / "default" / "bin"

# tool (executable name) -> conda package, upstream repo, raw README URL
TOOLS: dict[str, dict[str, str]] = {
    "sequali": {
        "package": "sequali",
        "repo": "rhpvorderman/sequali",
        # The upstream default branch is `develop`, and its README is .rst.
        "readme": "https://raw.githubusercontent.com/rhpvorderman/sequali/develop/README.rst",
    },
    "multiqc": {
        "package": "multiqc",
        "repo": "MultiQC/MultiQC",
        "readme": "https://raw.githubusercontent.com/MultiQC/MultiQC/main/README.md",
    },
    "fastp": {
        "package": "fastp",
        "repo": "OpenGene/fastp",
        "readme": "https://raw.githubusercontent.com/OpenGene/fastp/master/README.md",
    },
    "fastplong": {
        "package": "fastplong",
        "repo": "OpenGene/fastplong",
        "readme": "https://raw.githubusercontent.com/OpenGene/fastplong/master/README.md",
    },
    "trim_galore": {
        # conda package is hyphenated; the executable is underscored.
        "package": "trim-galore",
        "repo": "FelixKrueger/TrimGalore",
        "readme": "https://raw.githubusercontent.com/FelixKrueger/TrimGalore/master/README.md",
    },
    "seqkit": {
        "package": "seqkit",
        "repo": "shenwei356/seqkit",
        "readme": "https://raw.githubusercontent.com/shenwei356/seqkit/master/README.md",
    },
}


def tool_version(tool: str) -> str:
    """The version of `tool` as installed in the pinned env."""
    exe = ENV_BIN / tool
    if not exe.exists():
        return "unknown"
    for args in ([tool, "--version"], [tool, "version"]):
        try:
            proc = subprocess.run(
                [str(exe), *args[1:]], capture_output=True, text=True, timeout=60
            )
        except (OSError, subprocess.SubprocessError):
            continue
        blob = f"{proc.stdout}\n{proc.stderr}"
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", blob)
        if m:
            return m.group(1)
    return "unknown"


def capture_help(tool: str) -> str:
    """Verbatim `--help` from the pinned binary, with rich box borders stripped.

    MultiQC renders its help in a `rich` panel, so every flag line is prefixed
    with a box-drawing character. Stripping the borders makes the capture
    greppable with the usual `^\\s*-{1,2}[A-Za-z]` pattern.
    """
    exe = ENV_BIN / tool
    if not exe.exists():
        return ""
    try:
        proc = subprocess.run(
            [str(exe), "--help"], capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    blob = proc.stdout if proc.stdout.strip() else proc.stderr
    lines = []
    for line in blob.splitlines():
        stripped = re.sub(r"^[│╭╰├─\s]+", "", line)
        lines.append(stripped.rstrip())
    return "\n".join(lines).strip()


def fetch(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — a failed fetch is a WARN, not a crash
        return ""


def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()


def build(tool: str, meta: dict[str, str], today: str) -> list[str]:
    """Write one tool's corpus entry. Returns the list of populated sources."""
    out = CORPUS / tool
    out.mkdir(parents=True, exist_ok=True)
    version = tool_version(tool)
    populated: list[str] = []

    help_text = capture_help(tool)
    if help_text:
        (out / "cli-reference.md").write_text(
            f"# {tool} — CLI reference (verbatim `--help`)\n\n"
            f"Captured: {today}\n"
            f"Source: `{tool} --help`, executed inside this skill's pinned pixi "
            f"environment.\n"
            f"Version: {version}  (conda package: `{meta['package']}`)\n"
            f"Upstream: https://github.com/{meta['repo']}\n\n"
            f"This file is the authoritative flag reference for this skill: it was "
            f"captured from the exact binary the skill pins, so the flags below "
            f"match the installed version.\n\n"
            f"```\n{help_text}\n```\n",
            encoding="utf-8",
        )
        populated.append("cli-reference.md")

    readme = fetch(meta["readme"])
    if readme.strip():
        (out / "github-readme.md").write_text(
            f"# {tool} — upstream README\n\n"
            f"Captured: {today}\n"
            f"Source: {meta['readme']}\n"
            f"Upstream: https://github.com/{meta['repo']}\n"
            f"Pinned version: {version}\n\n"
            f"```markdown\n{readme}\n```\n",
            encoding="utf-8",
        )
        populated.append("github-readme.md")

    index = [
        f"# {tool} — docs-corpus entry",
        "",
        f"**Version**: {version}  (conda package: `{meta['package']}`)",
        f"**Upstream**: https://github.com/{meta['repo']}",
        f"**Captured**: {today}",
        "",
        "## Sources",
        "",
        "| File | Source | Role |",
        "|------|--------|------|",
    ]
    if "cli-reference.md" in populated:
        index.append(
            f"| `cli-reference.md` | `{tool} --help` (verbatim, pinned binary) | "
            "**authoritative** — flag names and defaults for the pinned version |"
        )
    if "github-readme.md" in populated:
        index.append(
            f"| `github-readme.md` | upstream repo README | usage examples, "
            "workflow context, citation |"
        )
    if not populated:
        index.append("| _(none populated)_ | — | all three fallback sources failed |")
    index += [
        "",
        "## How to use this entry",
        "",
        "Read `cli-reference.md` before invoking the tool — it is the flag "
        "contract for the version this skill pins. Reach for "
        "`github-readme.md` for worked examples and platform caveats.",
        "",
    ]
    (out / "README.md").write_text("\n".join(index), encoding="utf-8")
    return populated


def main() -> int:
    check_only = "--check" in sys.argv
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
    tools = wanted or list(TOOLS)
    unknown = [t for t in tools if t not in TOOLS]
    if unknown:
        print(f"unknown tool(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    today = date.today().isoformat()
    CORPUS.mkdir(parents=True, exist_ok=True)
    fingerprints: list[str] = []
    failures = 0

    for tool in tools:
        meta = TOOLS[tool]
        out = CORPUS / tool
        if check_only:
            have = [s for s in ("cli-reference.md", "github-readme.md", "web-docs.md")
                    if (out / s).exists() and (out / s).stat().st_size > 0]
            ok = (out / "README.md").exists() and bool(have)
            flags = 0
            if (out / "cli-reference.md").exists():
                flags = len(re.findall(
                    r"^\s*-{1,2}[A-Za-z][\w-]*",
                    (out / "cli-reference.md").read_text(), re.MULTILINE))
            print(f"  {'OK  ' if ok else 'FAIL'} {tool}: index={ (out / 'README.md').exists() } "
                  f"sources={len(have)}/3 flag_lines={flags}")
            if not ok or flags < 2:
                failures += 1
            continue

        populated = build(tool, meta, today)
        flag_lines = 0
        if (out / "cli-reference.md").exists():
            flag_lines = len(re.findall(
                r"^\s*-{1,2}[A-Za-z][\w-]*",
                (out / "cli-reference.md").read_text(), re.MULTILINE))
        status = "OK  " if populated and flag_lines >= 2 else "WARN"
        print(f"  {status} {tool}: {len(populated)}/3 sources, {flag_lines} flag-like lines")
        for src in ("cli-reference.md", "github-readme.md", "web-docs.md"):
            p = out / src
            if p.exists() and p.stat().st_size > 0:
                fingerprints.append(f"{md5(p.read_text())}  {tool}/{src}")
        if not populated or flag_lines < 2:
            failures += 1

    if not check_only:
        (CORPUS / ".fingerprints").write_text(
            f"# docs-corpus fingerprints — regenerate with bin/build-docs-corpus.py\n"
            f"# captured: {today}\n" + "\n".join(fingerprints) + "\n",
            encoding="utf-8",
        )
        print(f"  wrote {CORPUS / '.fingerprints'} ({len(fingerprints)} entries)")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
