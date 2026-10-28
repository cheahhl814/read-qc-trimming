# fastplong — CLI reference (verbatim `--help`)

Captured: 2026-10-28
Source: `fastplong --help`, executed inside this skill's pinned pixi environment.
Version: 0.7.1  (conda package: `fastplong`)
Upstream: https://github.com/OpenGene/fastplong

This file is the authoritative flag reference for this skill: it was captured from the exact binary the skill pins, so the flags below match the installed version.

```
usage: /home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/read-qc-trimming/.pixi/envs/default/bin/fastplong [options] ...
options:
-i, --in                                read input file name (string [=])
-o, --out                               read output file name (string [=])
--failed_out                        specify the file to store reads that cannot pass the filters. (string [=])
-z, --compression                       compression level for gzip output (1 ~ 9). 1 is fastest, 9 is smallest, default is 4. (int [=4])
--stdin                             input from STDIN.
--stdout                            stream passing-filters reads to STDOUT. This option will result in interleaved FASTQ output for paired-end output. Disabled by default.
--reads_to_process                  specify how many reads/pairs to be processed. Default 0 means process all reads. (int [=0])
--dont_overwrite                    don't overwrite existing files. Overwritting is allowed by default.
-V, --verbose                           output verbose log information (i.e. when every 1M reads are processed).
--ont_summary                       ONT sequencing_summary.txt file to add run-level QC charts to JSON/HTML reports. Can be used without FASTQ input for summary-only reporting. (string [=])
--target_bases                      approximately target this number of bases to output after filtering. This option reads the input twice and cannot be used with --sample_rate or output splitting. (long [=0])
--sample_rate                       randomly keep this fraction of reads after filtering (0.0~1.0). This option cannot be used with --target_bases. (double [=1])
--seed                              seed for reproducible output sampling. (unsigned long [=1])
--best_reads                        keep the best N reads by mean quality after filtering. This option reads the input twice and cannot be used with --best_bases. (long [=0])
--best_bases                        keep the best reads by mean quality until this many bases are selected after filtering. This option reads the input twice and cannot be used with --best_reads. (long [=0])
-A, --disable_adapter_trimming          adapter trimming is enabled by default. If this option is specified, adapter trimming is disabled
-s, --start_adapter                     the adapter sequence at read start (5'). (string [=auto])
-e, --end_adapter                       the adapter sequence at read end (3'). (string [=auto])
-a, --adapter_fasta                     specify a FASTA file to trim both read by all the sequences in this FASTA file (string [=])
-d, --distance_threshold                threshold of sequence-adapter-distance/adapter-length (0.0 ~ 1.0), greater value means more adapters detected (double [=0.25])
--trimming_extension                when an adapter is detected, extend the trimming to make cleaner trimming, default 10 means trimming 10 bases more (int [=10])
--disable_chimera_splitting         disable splitting reads by internal adapters/chimeric ligation signals.
--discard_chimeric_reads            discard reads containing internal adapters instead of splitting them into segments.
--chimera_min_segment_length        minimum segment length retained after splitting internal adapters, default: 20 (int [=20])
-f, --trim_front                        trimming how many bases in front for read, default is 0 (int [=0])
-t, --trim_tail                         trimming how many bases in tail for read, default is 0 (int [=0])
-x, --trim_poly_x                       enable polyX trimming in 3' ends.
--poly_x_min_len                    the minimum length to detect polyX in the read tail. 10 by default. (int [=10])
-5, --cut_front                         move a sliding window from front (5') to tail, drop the bases in the window if its mean quality < threshold, stop otherwise.
-3, --cut_tail                          move a sliding window from tail (3') to front, drop the bases in the window if its mean quality < threshold, stop otherwise.
-W, --cut_window_size                   the window size option shared by cut_front, cut_tail. Range: 1~1000, default: 4 (int [=4])
-M, --cut_mean_quality                  the mean quality requirement option shared by cut_front, cut_tail. Range: 1~36 default: 20 (Q20) (int [=20])
--cut_front_window_size             the window size option of cut_front, default to cut_window_size if not specified (int [=4])
--cut_front_mean_quality            the mean quality requirement option for cut_front, default to cut_mean_quality if not specified (int [=20])
--cut_tail_window_size              the window size option of cut_tail, default to cut_window_size if not specified (int [=4])
--cut_tail_mean_quality             the mean quality requirement option for cut_tail, default to cut_mean_quality if not specified (int [=20])
-N, --mask                              mask the low quality regions with N, these regions are detected by sliding window with mean quality < mask_mean_quality.
--mask_window_size                  the size of the sliding window to evaluate the mean quality for N masking(5~1000000), default: 50 (int [=50])
--mask_mean_quality                 the mean quality requirement for sliding window N masking (5~30), default: 10 (Q10) (int [=10])
-b, --break                             break the reads by discarding the low quality regions, these regions are detected by sliding window with mean quality < break_mean_quality.
--break_window_size                 the size of the sliding window to evaluate the mean quality for sliding window breaking(5~1000000), default: 100 (int [=100])
--break_mean_quality                the mean quality requirement for sliding window breaking (5~30), default: 10 (Q10) (int [=10])
--best_read_segment                 keep only the best high-quality continuous segment from each read. Low-quality regions are detected by sliding window.
--best_read_segment_window_size     the window size option of best-read-segment mode (5~1000000), default: 100 (int [=100])
--best_read_segment_mean_quality    the mean quality requirement for best-read-segment mode (5~30), default: 10 (Q10) (int [=10])
-Q, --disable_quality_filtering         quality filtering is enabled by default. If this option is specified, quality filtering is disabled
-q, --qualified_quality_phred           the quality value that a base is qualified. Default 15 means phred quality >=Q15 is qualified. (int [=15])
-u, --unqualified_percent_limit         how many percents of bases are allowed to be unqualified (0~100). Default 40 means 40% (int [=40])
--n_base_limit                      if number of N base is >n_base_limit, then this read is discarded (0~1000000). 0 means no N allowed, default 1000000 means no N limit (int [=1000000])
-n, --n_percent_limit                   if one read's N base percentage is >n_percent_limit, then this read is discarded (0~100). Default 10 means 10% (int [=10])
-m, --mean_qual                         if one read's mean_qual quality score <mean_qual, then this read is discarded. Default 0 means no requirement (int [=0])
-L, --disable_length_filtering          length filtering is enabled by default. If this option is specified, length filtering is disabled
-l, --length_required                   reads shorter than length_required will be discarded, default is 20. (int [=20])
--length_limit                      reads longer than length_limit will be discarded, default 0 means no limitation. (int [=0])
-y, --low_complexity_filter             enable low complexity filter. The complexity is defined as the percentage of base that is different from its next base (base[i] != base[i+1]).
-Y, --complexity_threshold              the threshold for low complexity filter (0~100). Default is 30, which means 30% complexity is required. (int [=30])
--min_gc                            the minimum GC content percentage allowed for each read (0~100). Default 0 means no minimum GC requirement. (double [=0])
--max_gc                            the maximum GC content percentage allowed for each read (0~100). Default 100 means no maximum GC requirement. (double [=100])
-j, --json                              the json format report file name (string [=fastplong.json])
-h, --html                              the html format report file name (string [=fastplong.html])
-R, --report_title                      should be quoted with ' or ", default is "fastplong report" (string [=fastplong report])
-w, --thread                            worker thread number, default is 3 (int [=3])
--split                             split output by limiting total split file number with this option (2~999), a sequential number prefix will be added to output name ( 0001.out.fq, 0002.out.fq...), disabled by default (int [=0])
--split_by_lines                    split output by limiting lines of each file with this option(>=1000), a sequential number prefix will be added to output name ( 0001.out.fq, 0002.out.fq...), disabled by default (long [=0])
--split_prefix_digits               the digits for the sequential number padding (1~10), default is 4, so the filename will be padded as 0001.xxx, 0 to disable padding (int [=4])
-?, --help                              print this message
```
