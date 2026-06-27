---
name: "read-qc-trimming"
description: "End-to-end read quality control and trimming pipeline. QC raw reads (sequali + multiqc), identify issues, trim/clean (fastp/fastplong/trim_galore), then QC trimmed reads to verify. Sandwich pattern: QC → Trim → QC → Go/No-Go."
version: 1
created: "2026-06-27"
updated: "2026-06-27"
requires:
  - "sequali (conda: bioconda) — platform-agnostic QC metric generation"
  - "multiqc (conda: bioconda) — aggregate QC reporting"
  - "fastp (conda: bioconda) — short-read trimming"
  - "fastplong (conda: bioconda) — long-read trimming"
  - "trim_galore (conda: bioconda) — high-stringency short-read adapter removal"
  - "pixi (pixi install) — environment management"
---

# Read QC & Trimming Pipeline

End-to-end quality control and trimming for sequencing reads. Follows a **sandwich pattern**: QC raw reads → trim/clean → QC trimmed reads → Go/No-Go decision.

```
┌─────────────────────────────────────────────────────┐
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
│  Decision: proceed to alignment/assembly, or        │
│  re-trim with adjusted parameters                   │
└─────────────────────────────────────────────────────┘
```

## When to Use

- Upon receipt of raw sequencing data (`.fastq`, `.fastq.gz`, `.uBAM`).
- Before alignment or assembly to reduce noise and improve mapping rates.
- To verify sequencing quality across a multi-sample batch.
- When a unified QC approach is needed for projects with both short and long reads.

## Prerequisites

- **Environment**: This skill requires an active Pixi environment. Refer to [pixi-env-mgmt](../pixi-env-mgmt/SKILL.md) for setup.

```bash
pixi init
pixi workspace channel add conda-forge bioconda
pixi add sequali multiqc fastp fastplong trim_galore
```

## Phase 1: Raw Read QC

### 1.1 Identify Read Platform

Determine read type from file metadata or user context to set correct quality thresholds:

| Platform | Read Type | Expected Read Length | Quality Profile |
|----------|-----------|---------------------|-----------------|
| Illumina (NovaSeq/NextSeq) | Short, paired | 75-300 bp | High Q30+, 3' poly-G tails |
| Illumina (MiSeq) | Short, paired | 150-300 bp | High Q30+, no poly-G |
| Oxford Nanopore | Long, single | 1-100+ kb | Variable Q7-15, 5' quality decay |
| PacBio HiFi | Long, single | 10-25 kb | High Q30+ (CCS) |
| PacBio CLR | Long, single | 10-50 kb | Low Q12-15 |

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

| Observation | Inference | Action |
|-------------|-----------|--------|
| Per-base quality drops below Q20 at 3' end | Quality decay | Plan tail trimming (`-q 20`) |
| Adapter content > 0% | Contamination | Plan adapter removal |
| GC content deviates from expected | Contamination or bias | Flag as Warning |
| Read length variance is high (short reads) | Fragmented DNA or poor clustering | Plan length filtering (`-l 15`) |
| Overrepresented sequences > 1% | Adapter/contaminant | Identify and remove |

**Record these findings** — they determine the Phase 2 parameters.

## Phase 2: Trim/Clean

### 2.1 Select Tool and Parameters

Based on Phase 1 findings and read platform:

| Data Type | Tool | When to Use |
|-----------|------|------------|
| **Short-read (standard)** | `fastp` | Default choice — fast, auto adapter detection, integrated QC |
| **Short-read (high stringency)** | `trim_galore` | When fastp fails to remove complex adapters or specific kit artifacts |
| **Long-read (ONT/PacBio)** | `fastplong` | Optimized for long-read error profiles and length distributions |

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

| Phase 1 Finding | Parameter | Value |
|-----------------|-----------|-------|
| 3' quality decay below Q20 | `-q` | 20 (or higher for stricter) |
| Many short reads after quality trim | `-l` | 15 (or 20 to be more aggressive) |
| NovaSeq/NextSeq poly-G tails | `--trim_poly_g` | Always enable for these platforms |
| Adapter detected (auto) | fastp auto-detects | No explicit flag needed |
| Per-read low-quality bases > 40% | `-u` | 40 (allow 40% low-quality bases per read) |

#### fastplong (Long Reads)

```bash
# Long-read cleaning with quality masking
fastplong -i input.fq.gz -o trimmed/output.fq.gz \
          --mask --mask_mean_quality 10 \
          --trim_poly_x --poly_x_min_len 10 \
          --json trimmed/fastplong.json
```

**Parameter tuning:**

| Phase 1 Finding | Parameter | Value |
|-----------------|-----------|-------|
| Low-quality regions within reads | `--mask` | Replaces with N (preserves length) |
| Entire reads are low quality | `--break` | Discards read (aggressive — use only if `--mask` is insufficient) |
| Poly-A/G tails in cDNA data | `--trim_poly_x` | Enable with `--poly_x_min_len 10` |

#### trim_galore (High-Stringency Short Reads)

Use when `fastp` fails to remove adapters or for specific kit presets:

```bash
# High-stringency paired-end trimming
trim_galore --paired --quality 20 --length 20 \
            --nextera --output_dir trimmed/ \
            R1.fq.gz R2.fq.gz
```

**Kit presets:**

| Kit/Platform | Flag | Notes |
|-------------|------|-------|
| Nextera | `--nextera` | Common for ATAC-seq |
| Small RNA | `--small_rna` | Retains short reads |
| BGI/MGI | `--bgiseq` | BGI-specific adapters |
| TruSeq (default) | (none) | Auto-detected by fastp |
| 5' bias (e.g., degraded FFPE) | `--hardtrim5 N` | Remove first N bases |

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

## Phase 4: Go/No-Go Decision

### 4.1 Compare Before vs After

```bash
# Compare MultiQC data before and after trimming
diff <(cat qc_summary_raw/multiqc_data.json | python3 -m json.tool) \
     <(cat qc_summary_trimmed/multiqc_data.json | python3 -m json.tool)
```

### 4.2 Go/No-Go Criteria

| Criterion | Pass Threshold | Action if Fail |
|-----------|---------------|----------------|
| Adapter content | ≈ 0% | Switch tool (fastp → trim_galore) or specify adapter manually |
| Per-base quality | Q20+ across full length | Increase `-q` threshold and re-trim |
| Read loss | < 10% total | Acceptable loss; if > 20%, loosen parameters |
| GC content shift | < 5% change from raw | If > 5%, check for over-trimming or contamination removal |
| N50 preservation (long reads) | > 80% of raw N50 | Switch from `--break` to `--mask` |

### 4.3 Decision Matrix

```
All criteria PASS → GO: Proceed to alignment/assembly
                      Output: trimmed/*.fq.gz + qc_trimmed/multiqc_data.json

Adapter content FAIL → Re-trim with different tool or manual adapter flag

Quality still FAIL   → Re-trim with stricter -q threshold
                      or flag sample as "requires manual review"

Read loss > 20%      → Loosen -l or -q parameters
                      or flag as "degraded sample"

Multiple systemic
FAIL across batch     → STOP: Library prep issue
                      Report to user before proceeding
```

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
```

## Pitfalls

- **Over-trimming**: Setting `-l` (min length) too high in `fastp` can discard a huge percentage of a library, especially degraded samples. Always check Phase 3 read loss.
- **Wrong adapter preset**: Using `--nextera` in `trim_galore` for a TruSeq library will not remove adapters. Verify the kit used.
- **Long-read fragmentation**: Using `--break` in `fastplong` on raw Nanopore data often destroys too many reads. `--mask` is generally safer for assembly.
- **Poly-G tails on NovaSeq/NextSeq**: Always use `--trim_poly_g` for these platforms. Not enabling it will inflate adapter content in Phase 3.
- **uBAM handling**: When using uBAM files, ensure they contain quality scores; otherwise QC metrics will be empty.
- **Biological artifacts vs contamination**: High overrepresentation may be biological (e.g., specific motifs in a target gene). Flag as "Observation" not "Failure" unless it conflicts with the project goal.
- **File extensions**: Ensure files are properly named (`.fastq`, `.fastq.gz`). Unconventional extensions may require explicit pathing.
- **Skipping Phase 3**: Never skip post-trim QC. Unverified trimming is the #1 source of silent pipeline failures.

## Verification

- [ ] Phase 1 (Raw QC): `sequali` and `multiqc` ran successfully on raw reads
- [ ] Phase 2 (Trim): Trimming tool selected based on Phase 1 findings and platform
- [ ] Phase 3 (Post-Trim QC): `sequali` and `multiqc` ran successfully on trimmed reads
- [ ] Phase 4 (Go/No-Go): All criteria pass — adapter content ≈ 0%, quality restored, read loss < 10%
- [ ] Output files match input count for paired-end data (R1 and R2 have same line counts)
- [ ] Summary report produced with before/after comparison

## Related Skills

- [pixi-env-mgmt](../pixi-env-mgmt/SKILL.md) — Environment setup and tool installation
- [read-mapping-alignment](../read-mapping-alignment/SKILL.md) — Next step after trimming: align reads to reference
- [nextflow-pipelines](../nextflow-pipelines/SKILL.md) — Automate this pipeline with Nextflow