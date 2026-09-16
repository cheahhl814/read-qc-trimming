---
name: "read-qc-trimming"
description: "End-to-end read quality control and trimming pipeline. Optional preflight gate (sub-skill: preflight/sequali-input-preflight) validates raw reads (file presence, md5 if provided, paired-end parity, platform detection) before QC raw reads (sequali + multiqc), identify issues, trim/clean (fastp/fastplong/trim_galore), then QC trimmed reads to verify. Sandwich pattern: Preflight → QC → Trim → QC → Go/No-Go."
version: 4
updated: "2026-08-17"
triggers:
  - "quality control reads"
  - "trim reads"
  - "QC fastq"
  - "clean raw reads"
  - "sequali"
  - "fastp"
  - "trim_galore"
  - "fastplong"
  - "read QC"
  - "read trimming"
  - "raw read quality"
  - "multiqc QC"
  - "sequencing quality check"
  - "adapter trimming"
  - "QC before alignment"
  - "preflight raw reads"
  - "validate fastq"
  - "md5 check fastq"
requires:
  - "sequali (conda: bioconda) — platform-agnostic QC metric generation"
  - "multiqc (conda: bioconda) — aggregate QC reporting"
  - "fastp (conda: bioconda) — short-read trimming"
  - "fastplong (conda: bioconda) — long-read trimming"
  - "trim_galore (conda: bioconda) — high-stringency short-read adapter removal"
  - "seqkit (conda: bioconda) — paired-read counting + stats (preflight only)"
  - "pixi (pixi install) — environment management"
---

# Read QC & Trimming Pipeline

End-to-end quality control and trimming for sequencing reads. Follows a **sandwich pattern**: QC raw reads → trim/clean → QC trimmed reads → Go/No-Go decision.

```
┌─────────────────────────────────────────────────────┐
│  Phase 0: Preflight (Optional)                      │
│  Validate: file presence, md5 if provided,         │
│  paired-end parity, platform detection             │
│  (sub-skill: preflight/sequali-input-preflight)    │
├─────────────────────────────────────────────────────┤
│  Phase 1: Raw QC      (sequali + multiqc)           │
│  Identify: adapter content, quality decay, length,  │
│  GC bias, overrepresented sequences                 │
├─────────────────────────────────────────────────────┤
│  Phase 2: Trim/Clean  (fastp / fastplong /           │
│                        trim_galore)                  │
│  Fix: remove adapters, quality-trim, length-filter, │
│  poly-G/A tail removal                              │
├─────────────────────────────────────────────────────┤
│  Phase 3: Post-Trim QC (sequali + multiqc)           │
│  Verify: adapters ≈0%, quality restored,            │
│  read loss <10%                                      │
├─────────────────────────────────────────────────────┤
│  Phase 4: Go/No-Go    (compare before vs after)      │
│  ┌── GO ──→ Proceed to alignment/assembly            │
│  │                                                    │
│  └── NO → Adjust parameters ──→ Return to Phase 2 ──┐│
│       (max 3 iterations, then STOP & report)       ││
│                                                     ││
│  Multiple systemic FAIL across batch?               ││
│  ──→ STOP: Library prep issue, report to user      ││
└─────────────────────────────────────────────────────┘
```

## When to Use

- Upon receipt of raw sequencing data (`.fastq`, `.fastq.gz`, `.uBAM`).
- Before alignment or assembly to reduce noise and improve mapping rates.
- To verify sequencing quality across a multi-sample batch.
- When a unified QC approach is needed for projects with both short and long reads.

## When to Run Phase 0 (Preflight)

Run the preflight sub-skill (`preflight/sequali-input-preflight/`) before Phase 1 if any of the following apply:

- **You just downloaded the data** and want to verify integrity (md5 checksum).
- **You have paired-end reads** and want to confirm R1 and R2 have matched read counts before `fastp` runs.
- **You're unsure of the platform** (Illumina / ONT / PacBio) and want auto-detection from extension + avg read length.
- **The files are large** (> 5 GB) and you want a fast preflight step that catches missing/empty files before sequali runs.
- **You're integrating with downstream skills** (e.g., `bacterial-genome-analysis`) that expect a `params.json` + `preflight.md` contract.

If you trust the inputs (e.g., a collaborator already validated them, or you're iterating on a known dataset), skip Phase 0 and go straight to Phase 1.

## Phase 0: Input Preflight (Optional)

Run the sub-skill at `preflight/sequali-input-preflight/`. It audits input files, validates md5 if provided, checks paired-end parity, and detects platform. Output: `params.json` (machine contract) + `preflight.md` (human audit) + `preflight_evidence.txt` (raw evidence).

**Pre-run confirmation gate**: before collecting any evidence, the sub-skill shows the user the list of files it will audit and asks for confirmation (yes / no / show all). This catches path errors and wrong-directory accidents before any work is done. The gate always fires — it is not conditional on evidence. See `preflight/sequali-input-preflight/SKILL.md` §0.0 for the message template and behavior.

**Verdict gate**: Phase 1 and Phase 2 refuse to run without `preflight.md` verdict ≥ `GO-WITH-WARNINGS`. If you skip Phase 0, the master skill does NOT block Phase 1 — the gate is opt-in via the sub-skill. Use the preflight whenever the input provenance is unclear or the data is from a new source.

**For full preflight documentation, see** [`preflight/sequali-input-preflight/SKILL.md`](preflight/sequali-input-preflight/SKILL.md). Summary of what it does:

1. **File presence + size** — refuses to proceed if any expected FASTQ is missing or empty.
2. **md5 verification** (if `.fastq.gz.md5` sidecar present) — refuses to proceed on checksum mismatch.
3. **Paired-end read count parity** — refuses to proceed if R1 and R2 read counts differ.
4. **Platform detection** — auto-detects Illumina / ONT / PacBio from extension + avg read length; writes `platform.detected` to `params.json`.
5. **Disk space** — refuses to proceed if < 10 GB free (Post-trim QC output can be ~5× input size).

The sub-skill has 3 ask-user stop points (SP1–SP3) that fire only on ambiguous evidence (single FASTQ with unclear pairing, uBAM with unknown quality scores, large files with no md5).

## Prerequisites

- **Environment**: This skill requires an active Pixi environment. Refer to [pixi-skill](https://github.com/cheahhl814/pixi-skill) for setup.

```bash
pixi init
pixi workspace channel add conda-forge bioconda
pixi add sequali multiqc fastp fastplong trim_galore seqkit
```

## Phase 1: Raw Read QC

### 1.1 Identify Read Platform

Determine read type from file metadata or user context to set correct quality thresholds. **If you ran Phase 0 (preflight), read `$RUN_DIR/params.json` `platform.detected` and trust it** — the preflight uses average read length from `seqkit stats` to disambiguate platforms automatically.

| Platform                   | Read Type     | Expected Read Length | Quality Profile                  |
| -------------------------- | ------------- | -------------------- | -------------------------------- |
| Illumina (NovaSeq/NextSeq) | Short, paired | 75-300 bp            | High Q30+, 3' poly-G tails       |
| Illumina (MiSeq)           | Short, paired | 150-300 bp           | High Q30+, no poly-G             |
| Oxford Nanopore            | Long, single  | 1-100+ kb            | Variable Q7-15, 5' quality decay |
| PacBio HiFi                | Long, single  | 10-25 kb             | High Q30+ (CCS)                  |
| PacBio CLR                 | Long, single  | 10-50 kb             | Low Q12-15                       |

### 1.2 Run Sequali

```bash
# Single-end or long-read:
sequali input.fastq.gz --outdir qc_raw/ --json qc_raw/sample.json -t 4

# Paired-end Illumina:
sequali R1.fastq.gz R2.fastq.gz --outdir qc_raw/ --json qc_raw/sample.json -t 4
```

### 1.3 Aggregate with MultiQC

```bash
# For comprehensive reporting (human + agent):
multiqc qc_raw/ -o qc_summary_raw/

# For data-only extraction (agent-only):
multiqc qc_raw/ --no-report --data-format json -o qc_summary_raw/
```

### 1.4 Interpret Raw QC Results

Read results in this priority order:

**Triage** (`qc_summary_raw/multiqc_data.json`):

- Multiple samples `FAIL` the same module → systematic library prep issue
- Single sample `FAIL` → sample-specific problem

**Per-Sample Deep Dive** (`qc_raw/<sample>.json`):

| Observation                                | Inference                         | Action                          |
| ------------------------------------------ | --------------------------------- | ------------------------------- |
| Per-base quality drops below Q20 at 3' end | Quality decay                     | Plan tail trimming (`-q 20`)    |
| Adapter content > 0%                       | Contamination                     | Plan adapter removal            |
| GC content deviates from expected          | Contamination or bias             | Flag as Warning                 |
| Read length variance is high (short reads) | Fragmented DNA or poor clustering | Plan length filtering (`-l 15`) |
| Overrepresented sequences > 1%             | Adapter/contaminant               | Identify and remove             |

**Record these findings** — they determine the Phase 2 parameters.

## Phase 2: Trim/Clean

### 2.1 Select Tool and Parameters

Based on Phase 1 findings and read platform:

| Data Type                        | Tool          | When to Use                                                           |
| -------------------------------- | ------------- | --------------------------------------------------------------------- |
| **Short-read (standard)**        | `fastp`       | Default choice — fast, auto adapter detection, integrated QC          |
| **Short-read (high stringency)** | `trim_galore` | When fastp fails to remove complex adapters or specific kit artifacts |
| **Long-read (ONT/PacBio)**       | `fastplong`   | Optimized for long-read error profiles and length distributions       |

### 2.2 Execute Trimming

#### fastp (Short Reads — Default)

```bash
# Paired-end with quality trimming
# Adjust parameters based on Phase 1 findings:
fastp -i R1.fq.gz -I R2.fq.gz \
      -o trimmed/R1_trimmed.fq.gz -O trimmed/R2_trimmed.fq.gz \
      --json trimmed/fastp.json --html trimmed/fastp.html \
      -q 20 -u 40 -l 15 \
      --trim_poly_g
```

**Parameter tuning based on Phase 1 findings:**

| Phase 1 Finding                     | Parameter          | Value                                     |
| ----------------------------------- | ------------------ | ----------------------------------------- |
| 3' quality decay below Q20          | `-q`               | 20 (or higher for stricter)               |
| Many short reads after quality trim | `-l`               | 15 (or 20 to be more aggressive)          |
| NovaSeq/NextSeq poly-G tails        | `--trim_poly_g`    | Always enable for these platforms         |
| Adapter detected (auto)             | fastp auto-detects | No explicit flag needed                   |
| Per-read low-quality bases > 40%    | `-u`               | 40 (allow 40% low-quality bases per read) |

#### fastplong (Long Reads)

```bash
# Long-read cleaning with cut-window quality trimming
fastplong -i input.fq.gz -o trimmed/output.fq.gz \
          -M 10 --cut_front --cut_tail \
          --trim_poly_x --poly_x_min_len 10 \
          --json trimmed/fastplong.json
```

**Parameter tuning:**

| Phase 1 Finding                  | Parameter       | Value                                                             |
| -------------------------------- | --------------- | ----------------------------------------------------------------- |
| Low-quality regions within reads | `-M` + `--cut_front`/`--cut_tail` | Cut-window mean-quality threshold (e.g. `-M 10`), trims from both ends. **Note:** fastplong has no `--mask`/`--break` flags — unlike some other long-read tools, it truncates low-quality windows rather than masking bases with `N`. Reads get shorter, not N-replaced. |
| Poly-A/G tails in cDNA data      | `--trim_poly_x` | Enable with `--poly_x_min_len 10`                                 |

#### trim_galore (High-Stringency Short Reads)

Use when `fastp` fails to remove adapters or for specific kit presets:

```bash
# High-stringency paired-end trimming
trim_galore --paired --quality 20 --length 20 \
            --nextera --output_dir trimmed/ \
            R1.fq.gz R2.fq.gz
```

**Kit presets:**

| Kit/Platform                  | Flag            | Notes                  |
| ----------------------------- | --------------- | ---------------------- |
| Nextera                       | `--nextera`     | Common for ATAC-seq    |
| Small RNA                     | `--small_rna`   | Retains short reads    |
| BGI/MGI                       | `--bgiseq`      | BGI-specific adapters  |
| TruSeq (default)              | (none)          | Auto-detected by fastp |
| 5' bias (e.g., degraded FFPE) | `--hardtrim5 N` | Remove first N bases   |

### 2.3 Record Trimming Stats

After trimming, review the tool's JSON report:

```bash
# fastp summary
python3 -c "
import json
data = json.load(open('trimmed/fastp.json'))
bf = data['filtering_result']['reads_before_filter']
af = data['filtering_result']['reads_after_filter']
pct = (1 - af/bf) * 100
print(f'Reads before: {bf:,}')
print(f'Reads after:  {af:,}')
print(f'Reads lost:  {pct:.1f}%')
"
```

**If read loss > 20%**: Trimming is too aggressive. Loosen `-q` or `-l` thresholds and re-run Phase 2.

## Phase 3: Post-Trim QC

**This step is mandatory.** Do not skip it.

Run the same QC pipeline on the trimmed reads:

```bash
# Re-run sequali on trimmed outputs
sequali trimmed/R1_trimmed.fq.gz trimmed/R2_trimmed.fq.gz \
      --outdir qc_trimmed/ --json qc_trimmed/sample.json -t 4

# Re-run multiqc
multiqc qc_trimmed/ -o qc_summary_trimmed/
```

## Phase 4: Go/No-Go Decision Loop

This is an **iterative loop**, not a one-time decision. If trimming criteria fail,
adjust parameters and re-run from Phase 2. Maximum 3 iterations before escalating.

```
Phase 4 Go/No-Go
  │
  ├─ ALL PASS ──→ GO: Proceed to alignment/assembly
  │
  ├─ Adapter FAIL ──→ Adjust: switch tool or specify adapter ──→ Phase 2
  │
  ├─ Quality FAIL ──→ Adjust: raise -q threshold ──→ Phase 2
  │
  ├─ Read loss > 20% ──→ Adjust: loosen -l or -q ──→ Phase 2
  │
  ├─ GC shift > 5% ──→ Adjust: check for over-trimming ──→ Phase 2
  │
  ├─ N50 drop > 20% ──→ Adjust: lower -M threshold or disable one of --cut_front/--cut_tail ──→ Phase 2
  │
  │
  ├─ After 3 iterations ──→ STOP: Flag as "requires manual review"
  │
  └─ Systemic batch FAIL ──→ STOP: Library prep issue, report to user
```

### 4.1 Compare Before vs After

```bash
# Compare MultiQC data before and after trimming
diff <(cat qc_summary_raw/multiqc_data.json | python3 -m json.tool) \
     <(cat qc_summary_trimmed/multiqc_data.json | python3 -m json.tool)
```

### 4.2 Go/No-Go Criteria

| Criterion                     | Pass Threshold          | Fail → Adjust                                               | Max Iterations |
| ----------------------------- | ----------------------- | ----------------------------------------------------------- | -------------- |
| Adapter content               | ≈ 0%                    | Switch tool (fastp→trim_galore) or specify adapter manually | 3              |
| Per-base quality              | Q20+ across full length | Increase `-q` threshold                                     | 3              |
| Read loss                     | < 10% total             | Loosen `-l` or `-q`; if > 20%, flag as degraded             | 3              |
| GC content shift              | < 5% change from raw    | Check for over-trimming or contamination removal            | 3              |
| N50 preservation (long reads) | > 80% of raw N50        | Lower `-M` threshold or disable one of `--cut_front`/`--cut_tail` (fastplong truncates, so aggressive cut-window settings shorten reads more than expected) | 3              |

### 4.3 Iteration Protocol

On each failed iteration:

1. **Identify** which criterion failed from Phase 3 QC
2. **Adjust** the corresponding trimming parameter (see table above)
3. **Re-run** Phase 2 with new parameters (overwrite previous trimmed output)
4. **Re-run** Phase 3 QC on the new trimmed output
5. **Re-evaluate** at Phase 4

After **3 iterations** without all criteria passing:

- **STOP** the pipeline
- Flag the sample as "requires manual review"
- Report all iteration results to the user
- Include the raw QC, all trimming attempts, and final post-trim QC

### 4.4 Output Summary

After a GO decision, the agent should produce:

```markdown
## Read QC & Trimming Summary

**Sample**: <sample_name>
**Platform**: <Illumina/ONT/PacBio>
**Pipeline**: sequali → <fastp/fastplong/trim_galore> → sequali

### Raw QC (Phase 1)
- Total reads: <N>
- Mean quality: <Q>
- Adapter content: <X>%
- GC content: <Y>%

### Trimming (Phase 2)
- Tool: <fastp/fastplong/trim_galore>
- Reads before: <N>
- Reads after: <M>
- Reads lost: <P>% (<N-M> reads)

### Post-Trim QC (Phase 3)
- Adapter content: ≈0%
- Mean quality: <Q>
- GC content: <Y>% (delta from raw: <d>%)

### Decision: GO ✓
### Iterations: <N> (if > 1, list parameter changes)
```

## Pitfalls

- **Over-trimming**: Setting `-l` (min length) too high in `fastp` can discard a huge percentage of a library, especially degraded samples. Always check Phase 3 read loss.
- **Wrong adapter preset**: Using `--nextera` in `trim_galore` for a TruSeq library will not remove adapters. Verify the kit used.
- **Long-read fragmentation**: `fastplong` has no `--mask`/`--break` flags (unlike some other long-read tools) — it always trims via cut-window (`-M` + `--cut_front`/`--cut_tail`), which truncates rather than N-masks. An aggressive `-M` threshold on raw Nanopore data can destroy too many reads; if N50 drops sharply, lower `-M` or trim only one end.
- **Poly-G tails on NovaSeq/NextSeq**: Always use `--trim_poly_g` for these platforms. Not enabling it will inflate adapter content in Phase 3.
- **uBAM handling**: When using uBAM files, ensure they contain quality scores; otherwise QC metrics will be empty.
- **Biological artifacts vs contamination**: High overrepresentation may be biological (e.g., specific motifs in a target gene). Flag as "Observation" not "Failure" unless it conflicts with the project goal.
- **File extensions**: Ensure files are properly named (`.fastq`, `.fastq.gz`). Unconventional extensions may require explicit pathing.
- **Skipping Phase 3**: Never skip post-trim QC. Unverified trimming is the #1 source of silent pipeline failures.

## Verification

- [ ] Phase 0 (Preflight, optional): `preflight/sequali-input-preflight/` ran — `params.json` + `preflight.md` written with verdict ≥ `GO-WITH-WARNINGS`, md5 verified (if sidecars present), paired-end parity confirmed, platform detected
- [ ] Phase 1 (Raw QC): `sequali` and `multiqc` ran successfully on raw reads
- [ ] Phase 2 (Trim): Trimming tool selected based on Phase 1 findings and platform
- [ ] Phase 3 (Post-Trim QC): `sequali` and `multiqc` ran successfully on trimmed reads
- [ ] Phase 4 (Go/No-Go): All criteria pass — adapter content ≈ 0%, quality restored, read loss < 10%
- [ ] If Phase 4 failed: iterations documented with parameter changes per attempt
- [ ] If 3+ iterations: flagged as "requires manual review" with full iteration history
- [ ] Output files match input count for paired-end data (R1 and R2 have same line counts)
- [ ] Summary report produced with before/after comparison

## Update Check

This skill ships a self-update check that compares the deployed `SKILL.md` (and the rest of the skill) against the upstream `github.com/cheahhl814/read-qc-trimming` repo via `git fetch` + SHA diff — no GitHub API call, no extra dependencies.

```bash
# From this skill's directory:
python3 bin/skill-update-check.py
# Or, for skills with pixi.toml:
pixi run update-check
# Verdict legend (exit code in parens):
#   UP-TO-DATE       (0)  local HEAD matches origin/HEAD
#   LOCAL-AHEAD      (0)  unpushed local commits; no action needed
#   BEHIND-BY-N      (1)  upstream is N commits ahead → rsync from @skills/read-qc-trimming/
#   OFFLINE          (2)  git fetch failed (no network / no credentials); informational
#   NO-ORIGIN        (2)  no `origin` remote configured; informational
```

When `BEHIND-BY-N`, the script prints the canonical fix (rsync from `@skills/read-qc-trimming/` to `~/.pi/agent/skills/read-qc-trimming/` per AGENTS.md §4a, then `diff -rq` to verify). When `OFFLINE`, the script still prints `local_sha` + deployed version so the user can compare by hand. The full implementation is in `bin/skill-update-check.py` (synced from the [bioinfo-skill-creator](https://github.com/cheahhl814/bioinfo-skill-creator) meta-skill v1.1.0+).

## Related Skills

- [preflight/sequali-input-preflight](preflight/sequali-input-preflight/SKILL.md) — **Optional preflight gate** (v1.0.0): validates file presence, md5 if provided, paired-end read count parity, and detects platform before Phase 1.
- [bacterial-genome-analysis/preflight/genome-input-preflight](https://github.com/cheahhl814/bacterial-genome-analysis/tree/master/preflight/genome-input-preflight) — Sister preflight for **cleaned** reads (runs after this skill, before assembly).
- [pixi-skill](https://github.com/cheahhl814/pixi-skill) — Environment setup and tool installation
- [read-mapping-alignment](../read-mapping-alignment/SKILL.md) — Next step after trimming: align reads to reference
- [nextflow-pipelines](../nextflow-pipelines/SKILL.md) — Automate this pipeline with Nextflow

## Common follow-ups

| User says | What to do |
| --- | --- |
| "Run preflight before QC" | Invoke `preflight/sequali-input-preflight/`. It audits input files, validates md5 if provided, checks paired-end parity, and detects platform. The output (`params.json` + `preflight.md`) gates Phase 1 — without a `GO` or `GO-WITH-WARNINGS` verdict, Phase 1 should refuse. |
| "Pre-flight confirmation gate is annoying, skip it" | Acceptable. The pre-run gate accepts a "trust me, just go" answer and records the bypass in `preflight_evidence.txt`. The gate is intended for catching wrong-directory/wrong-file accidents, not for blocking trust. |
| "I want to preflight a different directory" | HARD stop on the current gate. Re-run the sub-skill with the new path. The agent must not silently accept a different `$RUN_DIR` mid-run. |
| "md5 check failed" | HARD stop. Do not silently re-download. Ask the user to inspect the partial download / transfer. The preflight is read-only and must NOT delete files. |
| "R1 and R2 read counts differ" | HARD stop. This will crash `fastp` mid-run. Recommend re-extracting from the source FASTQ or re-downloading both files together. |
| "What platform is this?" | Read `$RUN_DIR/params.json` → `platform.detected`. If `ambiguous` (avg read length between 800 bp and 1.2 kb), ask the user to confirm. |
| "I trust the inputs, skip preflight" | Skip Phase 0, go straight to Phase 1. The preflight is opt-in by design — it does not block. |
| "Add md5 to an existing run" | Run preflight with the `.md5` sidecars in place. It overwrites the previous `params.json` + `preflight.md`. Phase 1 output is unchanged (sequali does not read md5). |