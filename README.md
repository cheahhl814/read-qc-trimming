# read-qc-trimming

[![Version](https://img.shields.io/badge/version-4-blue)](#-installation)
[![Type](https://img.shields.io/badge/type-agent%20skill-blueviolet)](#-installation)
[![Built with](https://img.shields.io/badge/built%20with-skill--forge-orange)](https://github.com/cheahhl814/bioinfo-skill-creator)

End-to-end read quality control and trimming pipeline. Optional preflight gate (sub-skill: preflight/sequali-input-preflight) validates raw reads (file presence, md5 if provided, paired-end parity, platform detection) before QC raw reads (sequali + multiqc), identify issues, trim/clean (fastp/fastplong/trim_galore), then QC trimmed reads to verify. Sandwich pattern: Preflight → QC → Trim → QC → Go/No-Go.

**Repository**: https://github.com/cheahhl814/read-qc-trimming

> [!NOTE]
> Current version: **v4** (updated 2026-08-17).

## Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Pipeline overview](#-pipeline-overview)
- [Tools](#-tools)
- [Update check](#-update-check)
- [Repository layout](#-repository-layout)
- [Hard guarantees](#-hard-guarantees)
- [Provenance](#-provenance)

## 🚀 Installation

This is an **agent skill**, not a user-facing library. The recommended install path is to let your AI agent import it.

**Option A — give your agent this prompt (recommended):**

```text
Install the read-qc-trimming skill from
https://github.com/cheahhl814/read-qc-trimming —
clone it into your agent's skills directory (the path your agent watches
for skills) and run `pixi install` from that directory. Then read the
skill's SKILL.md to understand its phases and the Input/Output contract
for each. Confirm when the environment is ready.
```

**Option B — manual install:**

```bash
git clone https://github.com/cheahhl814/read-qc-trimming.git
cd read-qc-trimming
pixi install
```

> [!TIP]
> `pixi install` resolves every pinned tool from `pixi.toml` (channels: conda-forge, bioconda) into an isolated `.pixi/` environment — no system-wide installs, no version conflicts with other skills.

## 💡 Usage

The skill is designed to be driven by an AI agent: the agent reads the master `SKILL.md`, detects the current phase from the filesystem state of your run directory, and routes to the right sub-skill.

### Natural-language prompts that trigger the skill

```text
quality control reads
trim reads
QC fastq
clean raw reads
sequali
```

### Manual phase execution

If you prefer to drive the phases yourself (or want to re-run a single phase):

```bash
# Set your run directory (all phase artifacts land here)
RUN_DIR=/path/to/run-dir

pixi run preflight   # Phase 0 (optional) — validate inputs, write preflight.md + params.json
pixi run qc-raw      # Phase 1 — sequali + multiqc on the raw reads
pixi run trim        # Phase 2 — fastp / fastplong / trim_galore
pixi run qc-trimmed  # Phase 3 — sequali + multiqc on the trimmed reads
pixi run go-no-go    # Phase 4 — compare before vs after, then GO / NO-GO
```

> [!NOTE]
> The phase tasks above are **phase markers, not runners** — the pipeline steps are agent instructions in `SKILL.md`, not scripts, so there is no `run.py` to call. The agent reads the phase section of `SKILL.md` and issues the real `sequali` / `fastp` / `multiqc` commands inside the activated environment. `pixi run update-check` is the one task that runs a real script.

> [!IMPORTANT]
> Each phase has an explicit **Inputs/Outputs contract** at the top of its sub-skill `SKILL.md`. If the upstream artifact is missing (e.g. you run `run` before `preflight` passed), the sub-skill refuses to proceed and tells you which phase to run first. Phases are gated on purpose — don't skip them.

## 🔬 Pipeline overview

The analysis follows a phased evidence chain. Each phase consumes the artifacts of the previous phase and gates progression with a Go/No-Go check.

| # | Phase | Goal | Sub-skill | Artifact produced |
|:--|:------|:-----|:----------|:------------------|
| **1** | **Preflight** | **v1.0.0 (new).** Pre-flight gate for the read-qc-trimming pipeline. Mirrors the `bettamt-preflight` pattern from [Betta | `preflight/` | `$RUN_DIR/preflight.md` |

> [!TIP]
> Read each sub-skill's `SKILL.md` for the full procedure, its ask-user stop points, and its signature library (stderr pattern → cause → fix).

## 🧰 Tools

All tools are resolved from conda-forge/bioconda via the pinned `pixi.toml`.

| Tool | Version | Role |
|:-----|:--------|:-----|
| `sequali` | `>=1.0.2,<2` | QC metric generation — all platforms (short + long reads) |
| `multiqc` | `>=1.35,<2` | Aggregate QC reporting — all platforms |
| `fastp` | `>=1.4.0,<2` | Trimming & cleaning — short reads (Illumina) |
| `fastplong` | `>=0.7.1,<0.8` | Trimming & cleaning — long reads (ONT, PacBio) |
| `trim-galore` | `>=2.3.0,<3` | High-stringency adapter removal — short reads (when fastp fails); **linux-64 only** (Bioconda has no osx build; the executable is `trim_galore`) |
| `seqkit` | `>=2.14.0,<3` | **Preflight only** — paired-end read counting + average read length for platform detection |

Tool usage is grounded in the offline `docs-corpus/` snapshots (version-matched `--help`/`man` captures, upstream repo docs, and web docs as fallback) — the agent reads these instead of guessing flags. Refresh them with `pixi run docs-corpus`; verify them with `pixi run docs-corpus-check`.

## 🔄 Update check

Every skill built with [skill-forge](https://github.com/cheahhl814/bioinfo-skill-creator) ships a self-update check that compares the deployed git SHA against this upstream repo via `git fetch` — no GitHub API call, no extra dependencies.

```bash
pixi run update-check
```

| Verdict | Exit | Meaning |
|:--------|:-----|:--------|
| `UP-TO-DATE` | 0 | Local HEAD matches origin/HEAD |
| `LOCAL-AHEAD` | 0 | Unpushed local commits; no action needed |
| `BEHIND-BY-N` | 1 | Upstream is N commits ahead → re-pull/re-sync from this repo |
| `OFFLINE` | 2 | `git fetch` failed; informational only |
| `NO-ORIGIN` | 2 | No `origin` remote configured; informational only |

## 📁 Repository layout

```text
read-qc-trimming/
├── SKILL.md                 # Master orchestrator (router — start here)
├── README.md                # This file
├── pixi.toml                # Pinned tool environment (pixi install)
├── params.json              # Render input — tool inventory + version (tracked)
├── docs-corpus/             # Offline snapshots of upstream tool docs
│   ├── .fingerprints        # md5 + capture date per source (regenerated)
│   ├── sequali/             #   cli-reference.md (verbatim --help) + github-readme.md
│   ├── multiqc/
│   ├── fastp/
│   ├── fastplong/
│   ├── trim_galore/
│   └── seqkit/
├── preflight/               # Phase 0 sub-skill (optional input gate)
│   └── sequali-input-preflight/SKILL.md
└── bin/
    ├── skill-update-check.py  # Self-update check (pixi run update-check)
    └── build-docs-corpus.py   # Regenerate docs-corpus/ (pixi run docs-corpus)
```

## 🔒 Hard guarantees

- **Filesystem evidence chain** — every phase emits the artifact the next phase consumes; the boundary between phases is the filesystem, not agent memory.
- **Docs-grounded tool usage** — tool flags come from `docs-corpus/`, never from the agent's memory.
- **Explicit stop points** — ambiguous decisions are surfaced to you as *Evidence + Recommend + Options*, not auto-picked.
- **Reproducible environments** — every tool is pinned in `pixi.toml` and resolved via pixi.

## 🚀 Nextflow runner

This skill does not currently ship a Nextflow runner. For cohort/HPC execution, wrap the `pixi run` tasks in a workflow scheduler of your choice.

## Provenance

Built with the [skill-forge](https://github.com/cheahhl814/bioinfo-skill-creator) meta-skill (v1.1.0), following the AiX-BIO skill convention (preflight → build → debug → battle-test evidence chain). Pattern adopted from:

- **BettaMt-agents** — https://github.com/cheahhl814/BettaMt-agents
- **bacterial-genome-analysis** — https://github.com/cheahhl814/bacterial-genome-analysis
- **amr-gene-screening** — https://github.com/cheahhl814/amr-gene-screening

## License

Released under the MIT License — see the license file in this repository for details.