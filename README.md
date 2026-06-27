# Read QC & Trimming Pipeline

End-to-end quality control and trimming for sequencing reads. **Sandwich pattern**: QC raw reads → trim/clean → QC trimmed reads → Go/No-Go decision.

```
Phase 1: Raw QC        →  sequali + multiqc
Phase 2: Trim/Clean     →  fastp / fastplong / trim_galore
Phase 3: Post-Trim QC   →  sequali + multiqc (again)
Phase 4: Go/No-Go       →  compare before vs after
```

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

## Quick Start

```bash
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