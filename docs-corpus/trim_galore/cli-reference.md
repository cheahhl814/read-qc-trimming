# trim_galore — CLI reference (verbatim `--help`)

Captured: 2026-10-28
Source: `trim_galore --help`, executed inside this skill's pinned pixi environment.
Version: 2.3.0  (conda package: `trim-galore`)
Upstream: https://github.com/FelixKrueger/TrimGalore

This file is the authoritative flag reference for this skill: it was captured from the exact binary the skill pins, so the flags below match the installed version.

```
Trim Galore: A fast, single-pass NGS adapter and quality trimmer.

Drop-in replacement for Trim Galore, rewritten in Rust. Matches v0.6.x outputs for the core feature set and extends it with poly-G / generic poly-A auto-trimming and other additions. Compatible with MultiQC and existing pipelines.

Usage: trim_galore [OPTIONS] <INPUT>...

Arguments:
<INPUT>...
Input FASTQ file(s). For paired-end, provide two files

Options:
-q, --quality <QUALITY>
Quality trimming cutoff (Phred score). Bases below this are trimmed from 3' end

[default: 20]

-a, --adapter <ADAPTER>
Adapter sequence for trimming. Auto-detected if not specified. Supports A{N} shorthand for repeated single bases (e.g., -a A{10} → AAAAAAAAAA). For multiple adapters, repeat -a (e.g., -a SEQ1 -a SEQ2) or use "file:adapters.fa"

--adapter2 <ADAPTER2>
Optional adapter sequence for Read 2 (paired-end only). Auto-set by --small_rna and --bgiseq presets. Supports A{N} shorthand for repeated single bases (e.g., -a2 T{150} → 150 T's). For multiple adapters, repeat -a2 (e.g., -a2 SEQ1 -a2 SEQ2) or use "file:adapters.fa"

--illumina
Use Illumina universal adapter (AGATCGGAAGAGC). Also the auto-detect fallback

--nextera
Use Nextera transposase adapter (CTGTCTCTTATA)

--small_rna
Use Illumina Small RNA adapter (TGGAATTCTCGG). Also lowers --length default to 18 and sets --adapter2 (GATCGTCGGACT, Illumina small RNA 5')

--stranded_illumina
Use Illumina Stranded mRNA adapter (ACTGTCTCTTATA). Not covered by auto-detection — must be set explicitly

--bgiseq
Use BGI/DNBSEQ adapter. Sets --adapter2 for Read 2. Also probed by auto-detection

--paired
Paired-end mode. Accepts an even number of input files as consecutive R1/R2 pairs (e.g. --paired R1.fq.gz R2.fq.gz, or a glob matching multiple samples)

-e, --error_rate <ERROR_RATE>
Maximum allowed error rate for adapter matching (0-1)

[default: 0.1]

--stringency <STRINGENCY>
Minimum overlap with adapter sequence required to trim (stringency)

[default: 1]

--length <LENGTH>
Minimum required sequence length after trimming. Default: 20 (18 for smallRNA adapter). In paired-end mode, both reads must pass; see --retain_unpaired to keep single survivors

--max_length <MAX_LENGTH>
Maximum allowed sequence length (discard reads longer than this). Typically only useful for smallRNA-seq to remove non-small-RNA reads

--max_n <MAX_N>
Maximum number of N bases allowed in a read. Integer: absolute count. Decimal (0-1): fraction of read length. In paired-end mode, either read over the limit removes the whole pair

--trim-n
Trim N bases from both ends of reads. Suppressed under --rrbs (matches Perl v0.6.x)

--clip_R1 <CLIP_R1>
Remove N bases from the 5' end of Read 1. Useful for removing 5' quality-bias regions

--clip_R2 <CLIP_R2>
Remove N bases from the 5' end of Read 2 (paired-end only). For paired-end bisulfite-seq, the end-repair step can introduce methylation bias; see Bismark User Guide

--three_prime_clip_R1 <THREE_PRIME_CLIP_R1>
Remove N bases from the 3' end of Read 1, after adapter/quality trimming

--three_prime_clip_R2 <THREE_PRIME_CLIP_R2>
Remove N bases from the 3' end of Read 2 (paired-end only), after adapter/quality trimming

--nextseq <NEXTSEQ>
NextSeq/NovaSeq 2-colour quality trimming. Trailing high-quality G bases are treated as no-signal artifacts and quality-trimmed. The value is the quality cutoff (replaces -q). Mutually exclusive with --quality

--phred64
Use Phred+64 quality encoding (Illumina 1.5). Default is Phred+33

--phred33
Use Phred+33 quality encoding (default, Sanger/Illumina 1.8+)

-o, --output_dir <OUTPUT_DIR>
Output directory for trimmed files. Created if it doesn't exist

--basename <BASENAME>
Custom basename for output files (replaces input filename stem). Only valid for a single file (single-end) or a single pair (paired-end)

--dont_gzip
Do not gzip-compress output files. Forces plain output regardless of input compression. By default, output compression mirrors the input (plain → plain, .gz → .gz; matches Perl v0.6.x behaviour)

--clumpify
Reorder reads in the gzip output so reads sharing a canonical 16-mer minimizer land adjacent, letting gzip's dictionary find longer redundant runs. Typical saving: 16–55% on short-read FASTQ. Records are byte-identical — only their order on disk changes. Pair lockstep is preserved.

Requires `--cores >= 2` and gzip output. Intended for short-read FASTQ; long-read inputs (ONT, PacBio) are unlikely to compress better. Combine with `--compression <N>` to trade speed against output size, and `--memory <N>` to grow the per-gzip-member sort run.

--compression <COMPRESSION>
Gzip compression level for output FASTQ (1–9). Default: 1 (fast, 75% larger files). Pass `--compression 6` for the gzip(1) default or `--compression 9` for archival use. Most useful in combination with `--clumpify`, where reordering plus a higher level compounds for substantially smaller output

[default: 1]

--memory <MEMORY>
Total memory budget for Trim Galore (e.g. `1G`, `512M`, `8G`). Currently used only by `--clumpify` for bin buffer sizing — bigger budget → bigger gzip members → better compression, up to a limit roughly equal to the uncompressed input size. Default: `1G`. Resolved bin layout and predicted peak RSS are printed at startup when `--clumpify` is set

[default: 1G]

--no_report_file
Suppress the trimming report

--preserve-tags <PRESERVE_TAGS>
Comma-separated list of BAM tags (e.g. "CB,UB,RX") to append to the FASTQ header on uBAM input. Tab-separated, samtools `-T`-compatible. Each tag must be a 2-char SAM tag name (`[A-Za-z][A-Za-z0-9]`). Ignored for FASTQ input. The `ALL` keyword is reserved for a future release and rejected in v1. See PLAN §3.2.5

--output-format <OUTPUT_FORMAT>
Output container format. Default `fastq` keeps existing behaviour (input-compression-mirroring FASTQ); `ubam` emits unaligned BAM with aux tags propagated from uBAM inputs (when `--preserve-tags` is set). uBAM output is always single-threaded in v1; see the rejection rules in `Cli::validate` for incompatible combinations. See `plans/06252026_pluggable-io-formats/phase1-trimgalore-formats/PLAN.md`

Possible values:
- fastq: FASTQ output, mirroring input compression (default)
- ubam:  Unaligned BAM output. Always single-threaded in v1; --clumpify, --passthrough, --clock, --implicon, --demux are rejected at validation

[default: fastq]

--retain_unpaired
Retain unpaired reads when the mate is too short (paired-end only). Cutoff via --length_1 / --length_2 (default 35 each)

-r, --length_1 <LENGTH_1>
Minimum length for unpaired Read 1 (with --retain_unpaired)

[default: 35]

--length_2 <LENGTH_2>
Minimum length for unpaired Read 2 (with --retain_unpaired)

[default: 35]

--passthrough <PASSTHROUGH>
Pass a third FASTQ file through unchanged but keep it in lockstep with R1/R2. Use case: 10X Multiome / scATAC libraries where the cell-barcode (I1/I2) read must stay aligned to the trimmed R1/R2. Records dropped by length/quality/N filters are also dropped from the passthrough output. The passthrough file is never trimmed or adapter-scanned.

Requires --paired with exactly one R1/R2 pair. Incompatible with --retain_unpaired, --clumpify, and all specialty modes (--clock, --implicon, --hardtrim5/3, --demux).

Note: legacy headers like @read/1, @read/2, @read/3 sync correctly. If your files use unusual header conventions and the sync check fires unexpectedly, please file an issue with a sample header line. If --fastqc is enabled the passthrough FastQC report will look poor (cell-barcode reads are intentionally uniformly-structured) — that's expected, not a defect. On a mid-stream reader error (truncated or desynced passthrough), partial output files may remain on disk — re-run after fixing the input.

--rename
Add clipped sequences to read IDs for --clip_R1/R2, --three_prime_clip_R1/R2, and --hardtrim5/3. Appends :clip5:SEQ and/or :clip3:SEQ to the read ID (each half only when that side was clipped). Useful for UMI handling

--consider_already_trimmed <CONSIDER_ALREADY_TRIMMED>
If auto-detected adapter count is at or below this threshold, skip adapter trimming (only quality trimming proceeds). Incompatible with explicit adapter presets

--rrbs
RRBS mode for MspI-digested samples. Removes 2bp end-repair artifacts at MspI cut sites after adapter trimming. In paired-end directional mode, automatically sets --clip_R2 2 unless the user provides their own value. Do not use with Tecan Ovation RRBS kits — those use a diversity-trimming step instead

--non_directional
Non-directional RRBS libraries. Reads starting with CAA or CGA get 2bp trimmed from the 5' end. Requires --rrbs. Unlike directional --rrbs, does not auto-set --clip_R2 2 in paired-end mode

--fastqc
Run FastQC on the trimmed output files (built in via the bundled fastqc-rust library; no external Java or FastQC binary needed). Produces FastQC 0.12.1-compatible *_fastqc.html / *_fastqc.zip artifacts

--fastqc_args <FASTQC_ARGS>
Additional arguments to pass to FastQC. Implies --fastqc. Common flags are translated to the bundled engine: --nogroup, --expgroup, --quiet, --svg, --nano, --nofilter, --casava, -t/--threads, -o/--outdir. Unrecognised flags emit a warning and are ignored

-j, --cores <CORES>
Number of worker threads for parallel processing (default: 1). At --cores 1 the worker-pool is bypassed (single thread, ~5 MB RAM). From --cores 2 upward, an N+4 thread model applies: N workers + 2 decompressors + 1 batcher + 1 writer. Wall-clock speedup is near-linear up to --cores 8 for paired-end runs; beyond that, gzip-output I/O on the storage layer typically becomes binding before workers run out of useful per-read work, so additional cores help progressively less

[default: 1]

--poly_a
Trim poly-A tails from the 3' end of Read 1 (and single-end reads), and poly-T heads from the 5' end of Read 2. Runs after adapter trimming, so poly-A tails hidden behind adapters are also removed

--poly_g
Trim poly-G tails from the 3' end of Read 1 (and single-end reads), and poly-C heads from the 5' end of Read 2. Useful for data from 2-colour instruments (NovaSeq, NextSeq) where no-signal bases are called as high-quality G. By default, poly-G trimming is auto-detected from the data. Use this flag to force-enable it. This is independent from --nextseq (quality-based G-trimming)

--no_poly_g
Disable poly-G auto-detection and trimming

-n, --times <TIMES>
Number of adapter trimming rounds per read. With multiple adapters, this allows removing more than one adapter from the same read. Default: 1. Typical multi-adapter usage: -n 3

[default: 1]

--discard_untrimmed
Discard reads that did not contain an adapter sequence. Only reads where at least one adapter match was found are written to output. For paired-end, the pair is discarded if neither read had an adapter

--hardtrim5 <HARDTRIM5>
Hard-trim to keep only the first N bases from the 5' end. Bypasses adapter/quality trimming entirely. Output filenames end in .<N>bp_5prime.fq(.gz)

--hardtrim3 <HARDTRIM3>
Hard-trim to keep only the last N bases from the 3' end. Bypasses adapter/quality trimming entirely. Output filenames end in .<N>bp_3prime.fq(.gz)

--clock
Epigenetic Clock mode (paired-end only). Extracts 8bp UMI + 4bp fixed sequence (CAGT) from both reads, appends to read IDs, and clips R1 at position 13, R2 at position 15. Bypasses normal trimming

--implicon[=<IMPLICON>]
Transfer the first N bases from Read 2 as a UMI barcode to both read IDs, then clip R2 by N bases. Paired-end only. Bypasses normal trimming (IMPLICON preprocessing). Default UMI length: 8 (used when --implicon is given without a value)

--demux <DEMUX>
Demultiplex reads after trimming based on 3' inline barcodes. Takes a barcode file (TSV: sample_name\tbarcode_sequence). Barcode is removed from the read and appended to the read ID. Single-end only

-h, --help
Print help (see a summary with '-h')

-V, --version
Print version
```
