# Read QC & Trimming Pipeline

End-to-end quality control and trimming for sequencing reads. **Sandwich pattern**: optional preflight → QC raw reads → trim/clean → QC trimmed reads → Go/No-Go decision.

```
Phase 0: Preflight      →  input audit + md5 + paired parity + platform detect  (optional)
Phase 1: Raw QC        →  sequali + multiqc
Phase 2: Trim/Clean     →  fastp / fastplong / trim_galore
Phase 3: Post-Trim QC   →  sequali + multiqc (again)
Phase 4: Go/No-Go       →  compare before vs after
       ├─ ALL PASS → GO: proceed to alignment
       ├─ FAIL → adjust params → return to Phase 2 (max 3 iterations)
       └─ Systemic batch FAIL → STOP: report to user
```

**Phase 0 (Preflight)** is an **opt-in sub-skill** at `preflight/sequali-input-preflight/`. Run it before Phase 1 when input provenance is unclear (e.g., newly downloaded FASTQs, paired-end R1/R2, or any startup where you want md5 verification + paired-end read count parity + automatic platform detection). Phase 0 emits `params.json` (machine contract) + `preflight.md` (human audit) + `preflight_evidence.txt` (raw evidence). Phase 1 / Phase 2 refuse to run without `preflight.md` verdict ≥ `GO-WITH-WARNINGS`. If you trust the inputs, skip Phase 0 and go straight to Phase 1.

## Why Merged?

Previously, read QC and trimming were separate skills, but they form an inseparable loop:
- QC identifies **what** to trim (adapters, quality decay, length)
- Trimming **fixes** those issues
- QC again **verifies** the fix worked (adapters ≈ 0%, quality restored, read loss < 10%)

Running QC only once (before or after trimming) is a common mistake. This merged skill enforces the correct sandwich pattern.

## Tools

| Tool | Purpose | Platform |
|------|---------|----------|
| `sequali` | QC metric generation | All platforms (short + long reads) |
| `multiqc` | Aggregate QC reporting | All platforms |
| `fastp` | Trimming & cleaning | Short reads (Illumina) |
| `fastplong` | Trimming & cleaning | Long reads (ONT, PacBio) |
| `trim_galore` | High-stringency adapter removal | Short reads (when fastp fails) |
| `seqkit` | **Preflight only** — paired-end read counting + average read length for platform detection | All platforms |

## Quick Start

```bash
# Phase 0 (optional): Preflight — input audit, md5, paired parity, platform detect
# See preflight/sequali-input-preflight/SKILL.md for full docs.
# Example: verify md5 + platform of raw reads
pixi run seqkit stat raw_R1.fastq.gz raw_R2.fastq.gz
md5sum -c raw_R1.fastq.gz.md5
# Emits: params.json (platform.detected + verdict) + preflight.md (audit) + preflight_evidence.txt

# Phase 1: Raw QC
sequali R1.fastq.gz R2.fastq.gz --outdir qc_raw/ --json qc_raw/sample.json
multiqc qc_raw/ -o qc_summary_raw/

# Phase 2: Trim (adjust parameters based on Phase 1 findings)
fastp -i R1.fq.gz -I R2.fq.gz \
      -o trimmed/R1_trimmed.fq.gz -O trimmed/R2_trimmed.fq.gz \
      --json trimmed/fastp.json -q 20 -l 15 --trim_poly_g

# Phase 3: Post-Trim QC (MANDATORY — do not skip)
sequali trimmed/R1_trimmed.fq.gz trimmed/R2_trimmed.fq.gz \
      --outdir qc_trimmed/ --json qc_trimmed/sample.json
multiqc qc_trimmed/ -o qc_summary_trimmed/

# Phase 4: Compare before vs after — check adapter content ≈ 0%, read loss < 10%
```

## Repository Layout

```
read-qc-trimming/
├── SKILL.md                            # Master orchestrator (router)
├── README.md                           # This file
├── .gitignore
└── preflight/
    └── sequali-input-preflight/
        └── SKILL.md                    # Phase 0 (optional, opt-in)
                                         #   - input audit + file size
                                         #   - md5 verification (if sidecars)
                                         #   - paired-end read count parity
                                         #   - platform auto-detection
                                         #   - emits params.json + preflight.md + preflight_evidence.txt
```

## Changelog

### v4 (2026-08-17) — Optional Phase 0 Preflight

- **New**: `preflight/sequali-input-preflight/` sub-skill (v1.0.0). Mirrors the bettamt-preflight pattern from `bacterial-genome-analysis`.
- **New**: `params.json` machine contract for Phase 1 / Phase 2 (platform detection, md5 status, paired parity).
- **New**: `preflight.md` human audit trail with `GO / GO-WITH-WARNINGS / NO-GO` verdict.
- **New**: 3 ask-user stop points (SP1–SP3): single FASTQ pairing, uBAM quality scores, large files missing md5.
- **New**: `seqkit` added to pixi dependencies (preflight only).
- **Test**: the battle-test sub-skill (`battle-test/read-qc-trimming-battle-test/SKILL.md`) enforces the preflight wiring and the no-regression rule on the bash recipe path. The standalone `test_smoke.py` was removed from the published bundle as a developer-convenience artifact.

### v3 (2026-08-14) — Phase 1 (Raw QC) + Phase 2 (Trim) + Phase 3 (Post-Trim QC) + Phase 4 (Go/No-Go loop)

- Original sandwich pattern. `fastplong` truncation note (no `--mask`/`--break`).

## Agent Compatibility

| Tool | Pi | Claude Code | Codex | Generic Bash |
|------|----|-------------|-------|-------------|
| `sequali` | ✅ bash | ✅ bash | ✅ bash | ✅ bash |
| `multiqc` | ✅ bash | ✅ bash | ✅ bash | ✅ bash |
| `fastp` | ✅ bash | ✅ bash | ✅ bash | ✅ bash |
| `fastplong` | ✅ bash | ✅ bash | ✅ bash | ✅ bash |
| `trim_galore` | ✅ bash | ✅ bash | ✅ bash | ✅ bash |

All tools are CLI-based and work identically across agents.

**To import into your agent, prompt it with:**

```
Import the skill from https://github.com/cheahhl814/read-qc-trimming
into your skills directory and adapt any agent-specific tool calls
to your native equivalents.
Then battle-test the import: run sequali on a test FASTQ file,
verify multiqc aggregation works, and confirm the Go/No-Go
decision criteria are clear and actionable.
```

## Replaces

This skill replaces and merges:
- `read-qc-analysis` (Phase 1 + Phase 3)
- `read-trimming-cleaning` (Phase 2)