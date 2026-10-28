# sequali — CLI reference (verbatim `--help`)

Captured: 2026-10-28
Source: `sequali --help`, executed inside this skill's pinned pixi environment.
Version: 1.0.2  (conda package: `sequali`)
Upstream: https://github.com/rhpvorderman/sequali

This file is the authoritative flag reference for this skill: it was captured from the exact binary the skill pins, so the flags below match the installed version.

```
usage: sequali [-h] [--json JSON] [--html HTML] [--outdir OUTDIR]
[--images-zip ZIP] [--adapter-file ADAPTER_FILE]
[--overrepresentation-threshold-fraction FRACTION]
[--overrepresentation-min-threshold THRESHOLD]
[--overrepresentation-max-threshold THRESHOLD]
[--overrepresentation-max-unique-fragments N]
[--overrepresentation-fragment-length LENGTH]
[--overrepresentation-sample-every DIVISOR]
[--overrepresentation-bases-from-start BP]
[--overrepresentation-bases-from-end BP]
[--duplication-max-stored-fingerprints N]
[--fingerprint-front-length LENGTH]
[--fingerprint-back-length LENGTH]
[--fingerprint-front-offset LENGTH]
[--fingerprint-back-offset LENGTH] [-t THREADS] [--version]
INPUT [INPUT_REVERSE]

Create a quality metrics report for sequencing data.

positional arguments:
INPUT                 Input FASTQ or uBAM file. The format is autodetected
and compressed formats are supported.
INPUT_REVERSE         Second FASTQ file for Illumina paired-end reads.

options:
-h, --help            show this help message and exit
--json JSON           JSON output file. default: '<input>.json'.
--html HTML           HTML output file. default: '<input>.html'.
--outdir, --dir OUTDIR
Output directory for the report files. default:
current working directory.
--images-zip ZIP      If supplied, will create a zip file with the images at
the supplied location.
--adapter-file ADAPTER_FILE
File with adapters to search for. See default file for
formatting. Default:
/home/cheahhl814/claude_workspace/bioinformatics/AIx-
BIO/skills/read-qc-
trimming/.pixi/envs/default/lib/python3.13/site-
packages/sequali/adapters/adapter_list.tsv.
--overrepresentation-threshold-fraction FRACTION
At what fraction a sequence is determined to be
overrepresented. The threshold is calculated as
fraction times the number of sampled sequences.
Default: 0.001 (1 in 1,000).
--overrepresentation-min-threshold THRESHOLD
The minimum amount of occurrences for a sequence to be
considered overrepresented, regardless of the bound
set by the threshold fraction. Useful for smaller
files. Default: 100.
--overrepresentation-max-threshold THRESHOLD
The amount of occurrences for a sequence to be
considered overrepresented, regardless of the bound
set by the threshold fraction. Useful for very large
files. Default: unlimited.
--overrepresentation-max-unique-fragments N
The maximum amount of unique fragments to store.
Larger amounts increase the sensitivity of finding
overrepresented sequences at the cost of increasing
memory usage. Default: 5,000,000.
--overrepresentation-fragment-length LENGTH
The length of the fragments to sample. The maximum is
31. Default: 21.
--overrepresentation-sample-every DIVISOR
How often a read should be sampled. More samples leads
to better precision, lower speed, and also towards
more bias towards the beginning of the file as the
fragment store gets filled up with more sequences from
the beginning. Default: 1 in 8.
--overrepresentation-bases-from-start BP
The minimum amount of bases sampled from the start of
the read. There might be slight overshoot depending on
the fragment length. Set to a negative value to sample
the entire read. Default: 100
--overrepresentation-bases-from-end BP
The minimum amount of bases sampled from the end of
the read. There might be slight overshoot depending on
the fragment length. Set to a negative value to sample
the entire read. Default: 100
--duplication-max-stored-fingerprints N
Determines how many fingerprints are maximally stored
to estimate the duplication rate. More fingerprints
leads to a more accurate estimate, but also more
memory usage. Default: 1,000,000.
--fingerprint-front-length LENGTH
Set the number of bases to be taken for the
deduplication fingerprint from the front of the
sequence. Default: 8.
--fingerprint-back-length LENGTH
Set the number of bases to be taken for the
deduplication fingerprint from the back of the
sequence. Default: 8.
--fingerprint-front-offset LENGTH
Set the offset for the front part of the deduplication
fingerprint. Useful for avoiding adapter sequences.
Default: 64 for single end, 0 for paired sequences.
--fingerprint-back-offset LENGTH
Set the offset for the back part of the deduplication
fingerprint. Useful for avoiding adapter sequences.
Default: 64 for single end, 0 for paired sequences.
-t, --threads THREADS
Number of threads to use. If greater than one an
additional thread for gzip decompression will be used.
Default: 2.
--version             show program's version number and exit
```
