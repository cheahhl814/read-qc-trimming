---
name: sequali-input-preflight
description: Validate raw read inputs (FASTQ + optional md5) for the read-qc-trimming pipeline and write a preflight.md audit trail + params.json platform contract. Computes evidence (file presence, file size, md5 checksum if provided, read count parity for paired-end, platform detection from extension and average read length) and emits a GO / GO-WITH-WARNINGS / NO-GO verdict. Always run before Phase 1 (Raw QC) and Phase 2 (Trim/Clean). Has 3 explicit ask-user stop points (SP1–SP3) that fire only when evidence is ambiguous. Triggers: "preflight raw reads", "validate fastq", "md5 check fastq", "paired-end parity", "platform detection raw reads", "read-qc-trimming preflight".
version: 1.0.0
updated: "2026-08-17"
triggers:
  - "preflight raw reads"
  - "validate fastq"
  - "md5 check fastq"
  - "paired-end parity"
  - "platform detection raw reads"
  - "read-qc-trimming preflight"
  - "audit raw reads"
  - "check fastq before QC"
  - "fastq integrity"
  - "verify read counts"
  - "fastq platform detect"
---

# Skill: sequali-input-preflight

> **v1.0.0 (new).** Pre-flight gate for the read-qc-trimming pipeline. Mirrors the `bettamt-preflight` pattern from [BettaMt-agents](https://github.com/cheahhl814/BettaMt-agents/blob/master/.agents/skills/bettamt-preflight/SKILL.md): gather inputs → compute evidence → write `params.json` (machine contract) + `preflight.md` (human audit). **Never** invokes `sequali` or any trimming tool. Phase 1 (Raw QC) and Phase 2 (Trim/Clean) refuse to run without `preflight.md` ≥ `GO-WITH-WARNINGS`.

## Audience

This skill serves two purposes:

- **AI Agents**: Triggered by phrases like *"preflight raw reads"* or *"validate my FASTQ"*. Must run all evidence collection steps, then write `params.json` + `preflight.md`.
- **Human Users**: Provides a transparent audit trail — every recommendation is cited back to a measured piece of evidence.

## When to Use This Skill

Use this skill if:

- You have **raw reads** (`.fastq`, `.fastq.gz`, `.fq.gz`, `.uBAM`) and want to know whether they are ready for `sequali` QC.
- You want to **verify md5 checksums** of downloads before QC (defends against partial downloads / transfer corruption).
- You want to **detect platform** (Illumina short / ONT long / PacBio long / unknown) before running `sequali` to pick the right Phase 2 tool.
- You want to **verify paired-end read count parity** before running `fastp` (mismatched counts cause `fastp` to fail mid-run).
- You want a **machine-readable `params.json`** that Phase 1 / Phase 2 can read without re-deriving platform decisions.
- You want a **human-readable `preflight.md`** documenting the audit trail (suitable for supplementary materials).

Do NOT use this skill if:

- You have **cleaned reads** — this skill is for raw reads. For cleaned reads, use `bacterial-genome-analysis/preflight/genome-input-preflight` instead.
- You want to QC immediately — this skill is the gate, not the QC itself.
- You are working with **already-trimmed** reads — they should bypass QC and go straight to assembly / mapping.

## 0.0 Pre-run Confirmation Gate

> **Always fire this gate before collecting any evidence.** It is the one place where the agent must wait for the user's explicit "proceed" before doing anything else. The format is **Evidence + Recommend + Options**.

Before the first evidence step (§1.1), the agent enumerates the files it would audit and asks the user to confirm. This catches path errors, wrong-directory accidents, and surprise-md5 decisions before any work is done.

**Trigger**: ALWAYS (this is not a conditional stop point — it is the entry gate).

**Evidence shown to the user** (read from the filesystem, do not invent):

```
$RUN_DIR: <path>
Files detected:
  - <file 1 name>  <size>  <md5 sidecar: yes/no>
  - <file 2 name>  <size>  <md5 sidecar: yes/no>
  - <file 3 name>  <size>  <md5 sidecar: yes/no>
  - (... any additional FASTQ / uBAM in $RUN_DIR that matches the canonical naming)
Files NOT detected (will be skipped unless you confirm a non-canonical path):
  - <file 1 name>  <size>  (not in the canonical raw_R1/R2/long naming)
```

**Recommended message** (the agent must format using this template):

> "I'll preflight the following files at `$RUN_DIR`:
> - `<file 1>` (4.2 GB, md5 sidecar present)
> - `<file 2>` (4.2 GB, no md5 sidecar)
> Do you want me to proceed?
> (A) Yes, run preflight now
> (B) No — let me point you at different files
> (C) Show me everything in `$RUN_DIR/` (in case I missed a file)"

**Behavior**:

| User choice | Action |
| --- | --- |
| A (Yes) | Proceed to §1.1 (evidence collection). |
| B (No) | HARD stop. Do not collect any evidence. Ask the user to re-run with correct paths. |
| C (Show all) | Enumerate every FASTQ / uBAM / uBAM.bai in `$RUN_DIR` (including non-canonical names), show sizes + md5 sidecar status, then re-ask the original confirmation question. |
| User types a custom path | HARD stop. Re-run this gate with the user-supplied path as the new `$RUN_DIR`. Do not silently accept. |
| User says "trust me, just go" | Acceptable. Record the user's bypass in `preflight_evidence.txt` as `=== 0.0 PRE-RUN CONFIRMATION === user bypassed pre-run confirmation gate at <timestamp>`. Proceed to §1.1. |

**Why this is not a stop point**: SP1–SP3 fire *during* evidence collection when the evidence is ambiguous. The pre-run confirmation fires *before* any evidence is collected — wrong directory, wrong file, or wrong intent. Different shape, different timing. Listed under §0.0 instead of §0.5 to keep the existing SP numbering stable.

**Tests must enforce**: the pre-run confirmation section must be present in the SKILL.md, and the master SKILL.md must reference it from the Phase 0 walkthrough.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path                                | Source        | Required? | Notes                                                                |
| ----------------------------------- | ------------- | --------- | -------------------------------------------------------------------- |
| `$RUN_DIR/raw_R1.fastq.gz`          | user / upload | conditional | Required for paired-end Illumina / hybrid                            |
| `$RUN_DIR/raw_R2.fastq.gz`          | user / upload | conditional | Required for paired-end Illumina / hybrid                            |
| `$RUN_DIR/raw_long.fastq.gz`        | user / upload | conditional | Required for ONT / PacBio / hybrid                                    |
| `$RUN_DIR/raw.fastq.gz`             | user / upload | conditional | Required for single-end short reads                                   |
| `$RUN_DIR/raw_R1.fastq.gz.md5`      | user / upload | optional  | md5 sidecar; if present, must match                                    |
| `$RUN_DIR/raw_R2.fastq.gz.md5`      | user / upload | optional  | md5 sidecar; if present, must match                                    |
| `$RUN_DIR/raw_long.fastq.gz.md5`    | user / upload | optional  | md5 sidecar; if present, must match                                    |
| `$RUN_DIR/raw.fastq.gz.md5`         | user / upload | optional  | md5 sidecar; if present, must match                                    |

**Naming convention**: the sub-skill accepts the canonical names above. If the user's files have different names, the agent must rename (or symlink) them into `$RUN_DIR/` before running preflight, or pass `--input_r1=/path/to/foo.fastq.gz` overrides (see §0.4).

### Outputs (produced)

| Path                              | Owner        | Format   | Notes                                                                            |
| --------------------------------- | ------------ | -------- | -------------------------------------------------------------------------------- |
| `$RUN_DIR/params.json`            | this skill   | JSON     | **Machine contract for Phase 1 / Phase 2.** Schema below.                          |
| `$RUN_DIR/preflight.md`           | this skill   | Markdown | **Human audit trail.** Verdict summary + evidence + recommendations.              |
| `$RUN_DIR/preflight_evidence.txt` | this skill   | text     | Raw evidence output (ls / md5sum / read counts) — kept for debugging.            |

### Where to write

- Use `$RUN_DIR` (env var) or the current working directory if `$RUN_DIR` is unset.
- Phase 1 (`sequali`) reads `$RUN_DIR/params.json` to choose the right invocation flags.
- Phase 1 also reads `$RUN_DIR/preflight.md` to verify the verdict gate.

### Verdict gate

Phase 1 (Raw QC) and Phase 2 (Trim/Clean) **refuse to run** unless `$RUN_DIR/preflight.md` overall verdict is `GO` or `GO-WITH-WARNINGS`. A `NO-GO` verdict stops the pipeline.

| Verdict               | Meaning                                                                  | Action                                  |
| --------------------- | ------------------------------------------------------------------------ | --------------------------------------- |
| `GO`                  | All checks passed (md5 present + matching, paired parity OK, platform detected) | Proceed to Phase 1 / Phase 2 directly |
| `GO-WITH-WARNINGS`    | No md5 supplied (merit warning, skipped check) OR platform detection ambiguous (long filename differences) | Proceed to Phase 1 / Phase 2; warn user |
| `NO-GO`               | md5 supplied but mismatched, OR paired read count mismatch, OR missing input, OR empty file | HARD stop. Fix the issue, re-run preflight. |

## 0.4 Param overrides

If the user's files are not at the canonical paths, the agent can pass overrides via `$RUN_DIR/params.json` `inputs` field, or by passing on the command line:

```bash
# Example: preflight reads at non-canonical paths
pixi run amr-preflight --input_r1=/data/sample/R1.fq.gz \
                       --input_r2=/data/sample/R2.fq.gz
```

(If a CLI wrapper is not present, the sub-skill reads the user-supplied paths from the in-session prompt and writes them into `params.json` `inputs.*` fields.)

## 0.5 Ask-User Stop Points

This sub-skill has **3 stop points** (SP1–SP3). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Single FASTQ, paired-or-single unknown

| Trigger                                           | Evidence check                                | Action                                                                                                                                                   |
| ------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One FASTQ at a non-canonical path, no R1/R2 suffix | Cannot infer pairing from filename alone       | Ask: "I see one FASTQ at `<path>`. Is this paired-end? (A) yes — point me at R2, (B) no — single-end, (C) this is long-read (ONT/PacBio), not short-read" |

**Auto-pick when**: filename has `R1`/`R2` (→ paired) or `_long` (→ long-read) or `cleaned_` prefix from upstream (→ trust upstream pairing).

### SP2 — uBAM with unknown quality scores

| Trigger                                  | Evidence check                                | Action                                                                                                                                                     |
| ---------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input is `.uBAM` (unaligned BAM)         | Cannot introspect quality scores without `samtools` | Ask: "Detected `.uBAM` input. Does it contain quality scores? (A) yes (Illumina 1.8+ Phred+33), (B) no (Illumina 1.3-1.7 Phred+64 or older), (C) abort and convert to FASTQ first" |

**Auto-pick when**: input is plain FASTQ (`.fq`, `.fq.gz`, `.fastq`, `.fastq.gz`). No ask.

### SP3 — md5 missing but download is large (recommend, not block)

| Trigger                                          | Evidence check                            | Action                                                                                                                                              |
| ------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Single file > 5 GB OR total FASTQ > 10 GB, no md5 present | Real value in verifying integrity | Recommend: "Files are large (X GB). Do you want to (A) provide md5 sidecars now and re-run preflight, (B) skip md5 and proceed with `GO-WITH-WARNINGS`, (C) abort" |

**Auto-pick when**: total FASTQ < 5 GB OR md5 sidecars are present. No ask (md5 missing is a soft warning, not a hard gate).

## 1. Evidence Collection

The agent runs these evidence steps in order. Each step writes one section to `preflight_evidence.txt`.

### 1.1 File presence

```bash
ls -la $RUN_DIR/raw* 2>&1 | tee -a preflight_evidence.txt
```

Failure: any expected canonical file missing from `params.json` `inputs` → `NO-GO`.

### 1.2 File size (sanity check, no empty files)

```bash
for f in $RUN_DIR/raw*.fastq.gz $RUN_DIR/raw*.fq.gz $RUN_DIR/raw*.fastq $RUN_DIR/raw*.uBAM; do
  [ -f "$f" ] && du -h "$f" 2>&1 | tee -a preflight_evidence.txt
done
```

Threshold: any FASTQ file < 1 KB → `NO-GO` (probably corrupt or truncated).

### 1.3 md5 verification (if sidecar present)

```bash
# Standard sidecar format: <md5>   <path>
cd $RUN_DIR
md5sum -c raw_R1.fastq.gz.md5 2>&1 | tee -a preflight_evidence.txt
md5sum -c raw_R2.fastq.gz.md5 2>&1 | tee -a preflight_evidence.txt
md5sum -c raw_long.fastq.gz.md5 2>&1 | tee -a preflight_evidence.txt
```

Failure: `md5sum -c` returns non-zero → `NO-GO`. The agent must NOT delete the file — let the user investigate.

### 1.4 Read count parity (paired-end)

Two approaches, in order of preference:

```bash
# Approach A: bgzip + index + seqkit (fast, accurate)
pixi run seqkit stat raw_R1.fastq.gz raw_R2.fastq.gz 2>&1 | tee -a preflight_evidence.txt

# Approach B: pure zcat + grep (slower, no external deps)
n_R1=$(zcat raw_R1.fastq.gz | grep -c '^@')
n_R2=$(zcat raw_R2.fastq.gz | grep -c '^@')
echo "R1: $n_R1 reads; R2: $n_R2 reads" | tee -a preflight_evidence.txt
```

If `$n_R1 != $n_R2` → `NO-GO`. The agent must not proceed to `fastp` with mismatched counts (`fastp` will error mid-run).

### 1.5 Platform detection

Read length from the first 1000 records (cheap):

```bash
pixi run seqkit stats -a raw_R1.fastq.gz 2>&1 | tee -a preflight_evidence.txt
```

| Avg read length | Avg read length | Platform inference                                    |
| --------------- | --------------- | ----------------------------------------------------- |
| < 1 kb          | any             | Short-read (Illumina / Element / BGI)                  |
| ≥ 1 kb and < 25 kb | any           | Long-read (ONT)                                       |
| ≥ 10 kb and < 25 kb | any           | Long-read (PacBio HiFi / CLR)                         |
| ≥ 25 kb        | any             | Long-read (ONT ultra-long / PacBio ultra-long)        |

If avg read length is ambiguous (between 800 bp and 1.2 kb), set `platform: "ambiguous"` in `params.json` and recommend `GO-WITH-WARNINGS`. Phase 1 will still run; the user can pick the correct trimmer in Phase 2.

### 1.6 (Optional) Disk space check

```bash
df -h $RUN_DIR 2>&1 | tee -a preflight_evidence.txt
```

If free < 10 GB → `NO-GO` (Phase 1 + Phase 2 + Phase 3 outputs will consume ~5× input size).

## 2. Output Format

### 2.1 `params.json` schema

```json
{
  "skill": "sequali-input-preflight",
  "version": "1.0.0",
  "run_id": "<UUID or timestamp>",
  "inputs": {
    "r1": "$RUN_DIR/raw_R1.fastq.gz",
    "r2": "$RUN_DIR/raw_R2.fastq.gz",
    "long": "$RUN_DIR/raw_long.fastq.gz",
    "single": "$RUN_DIR/raw.fastq.gz"
  },
  "md5": {
    "provided": true,
    "r1_ok": true,
    "r2_ok": true,
    "long_ok": true,
    "single_ok": null
  },
  "read_counts": {
    "r1": 12345678,
    "r2": 12345678,
    "long": null,
    "single": null,
    "parity_ok": true
  },
  "platform": {
    "detected": "illumina_short",
    "ambiguous": false,
    "avg_read_length_r1": 150,
    "avg_read_length_long": null
  },
  "disk_free_gb": 142,
  "verdict": "GO",
  "warnings": [],
  "evidence_file": "$RUN_DIR/preflight_evidence.txt",
  "timestamp": "2026-08-17T12:34:56Z"
}
```

**Platform values**: `illumina_short` | `illumina_long` (PacBio/ONT) | `ont` | `pacbio_hifi` | `pacbio_clr` | `ambiguous` | `unknown`.

### 2.2 `preflight.md` template

```markdown
# sequali-input-preflight — Audit Report

**Run ID**: <run_id>
**Timestamp**: <timestamp>
**Inputs**: <list of files with sizes>
**md5 verification**: PASS / FAIL / NOT-SUPPLIED
**Paired-end parity**: OK / MISMATCH / N/A
**Platform detected**: <platform> (avg read length: <N> bp)
**Disk free**: <X> GB

## Verdict: <GO | GO-WITH-WARNINGS | NO-GO>

## Evidence
<contents of preflight_evidence.txt, or a summary table>

## Warnings (if any)
- <warning 1>
- <warning 2>

## Recommendations
- Phase 1 (Raw QC): <which sequali flags to use>
- Phase 2 (Trim/Clean): <which tool to pick given the detected platform>
```

### 2.3 `preflight_evidence.txt` format

Plain text, one chunk per evidence step:

```
=== 1.1 FILE PRESENCE ===
-rw-r--r-- 1 user user  4.2G Aug 17 12:00 raw_R1.fastq.gz
-rw-r--r-- 1 user user  4.2G Aug 17 12:00 raw_R2.fastq.gz

=== 1.2 FILE SIZE ===
4.2G   raw_R1.fastq.gz
4.2G   raw_R2.fastq.gz

=== 1.3 MD5 VERIFICATION ===
raw_R1.fastq.gz: OK
raw_R2.fastq.gz: OK

=== 1.4 READ COUNT PARITY ===
file                 num_seqs  avg_len  min_len  max_len  sum_len
raw_R1.fastq.gz      12,345,678  150      150      150      1,851,851,700
raw_R2.fastq.gz      12,345,678  150      150      150      1,851,851,700
Parity: OK

=== 1.5 PLATFORM DETECTION ===
Avg read length: 150 bp → illumina_short

=== 1.6 DISK SPACE ===
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  358G  142G  72% /data
```

## 3. The audit chain (handoff to Phase 1)

Once `preflight.md` is written with verdict `GO` or `GO-WITH-WARNINGS`:

1. **Phase 1 (Raw QC)** reads `params.json` `platform.detected` to pick the right `sequali` flags.
2. **Phase 2 (Trim/Clean)** reads `params.json` `platform.detected` to pick the right tool (`fastp` for short reads, `fastplong` for long reads).
3. **Phase 3 (Post-Trim QC)** ignores `params.json` — purely re-runs `sequali`.
4. **Phase 4 (Go/No-Go)** compares Phase 1 vs Phase 3 outputs and decides.

If the verdict is `NO-GO`, the pipeline stops. The user must fix the issue (re-download, re-extract, fix paths) and re-run preflight.

## 4. Procedural guidelines

- **Never** invoke `sequali`, `fastp`, `fastplong`, or `trim_galore` from this sub-skill. Those belong to Phase 1 / Phase 2.
- **Never** modify the input files. The preflight is read-only.
- **Always** write `preflight_evidence.txt` even if every check passes — it is the audit trail.
- **Always** write `preflight.md` with a verdict line, even if the verdict is `NO-GO`.
- If `md5` is provided but the corresponding file is missing, treat as `NO-GO` (do not silently skip).
- If `params.json` already exists at `$RUN_DIR`, the agent must ask: re-run preflight (overwrite) or abort?

## 5. Troubleshooting signature library

| Symptom                                                       | Likely cause                          | Fix                                                                                  |
| ------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| `md5sum -c` returns "No such file or directory"               | md5 sidecar names do not match canonical | Rename sidecar to match the FASTQ filename (e.g. `raw_R1.fastq.gz.md5`).             |
| `seqkit stat` reports `num_seqs: 0`                           | Empty / corrupt FASTQ                | Re-download the file.                                                                 |
| R1 and R2 read counts differ by 1                             | `seqkit` rounding / last record       | Acceptable if diff ≤ 10. Re-run with explicit `head -n 4000000 \| wc -l` verification. |
| `df -h` reports < 10 GB free                                  | Disk full                            | Free space or move `$RUN_DIR` to a larger filesystem.                                 |
| Avg read length is 0                                          | FASTQ has no reads (corrupt)         | Re-download.                                                                          |
| `file raw_R1.fastq.gz` reports "ASCII text"                  | File is not gzip-compressed          | Re-gzip or rename to `.fastq` (uncompressed).                                          |
| Avg read length is exactly 150 or 300 every time              | Synthetic / subsampled demo data      | Proceed — preflight cannot distinguish demo data from real Illumina.                  |

## 6. Cross-references

- [bacterial-genome-analysis/preflight/genome-input-preflight](https://github.com/cheahhl814/bacterial-genome-analysis/tree/master/preflight/genome-input-preflight) — sister preflight for cleaned reads (the next step in the pipeline).
- [bettamt-preflight](https://github.com/cheahhl814/BettaMt-agents/blob/master/.agents/skills/bettamt-preflight/SKILL.md) — the canonical pattern this sub-skill mirrors.
- [pixi-env-mgmt](https://github.com/cheahhl814/pixi-env-mgmt) — environment setup (this sub-skill requires `seqkit` for read counting; everything else is `bash` + `md5sum`).
- [read-mapping-alignment](https://github.com/cheahhl814/read-mapping-alignment) — next step after `read-qc-trimming` finishes.

## 7. References

- **md5sum**: GNU coreutils >= 8.x
- **seqkit**: >= 2.x (for read counting + stats)
- **zcat / gunzip**: standard Unix (fallback when seqkit is unavailable)
- **samtools**: optional (only for uBAM quality score inspection in SP2)
