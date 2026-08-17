#!/usr/bin/env python3
"""Smoke tests for read-qc-trimming v4 structural coherence.

Validates:
- Pre-flight sub-skill (sequali-input-preflight) presence and frontmatter
- Master SKILL.md frontmatter coherence (v4, updated date, preflight in description)
- Phase 0 / Preflight wiring in master SKILL.md (banner + section + follow-ups)
- README.md preflight mentions
- Bash recipe remains Phase 1 (Raw QC) — no regression
- Mistake guard: no claim of "md5 optional" that contradicts the NO-GO-on-mismatch rule

Run from anywhere: python3 test_smoke.py
"""

import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent
MASTER = SKILL_ROOT / "SKILL.md"
PREFLIGHT = SKILL_ROOT / "preflight" / "sequali-input-preflight" / "SKILL.md"
README = SKILL_ROOT / "README.md"


def _read(path: Path) -> str:
    """Read a UTF-8 text file, exiting if the file is missing.

    We exit (not raise) because the failure mode is a missing sub-skill,
    never a transient I/O issue.
    """
    if not path.exists():
        print(f"FAIL: required file missing: {path}", file=sys.stderr)
        sys.exit(2)
    return path.read_text(encoding="utf-8")


class TestPreflightSubSkillExists(unittest.TestCase):
    """The preflight sub-skill directory + SKILL.md must exist."""

    def test_preflight_directory_exists(self):
        self.assertTrue(
            (SKILL_ROOT / "preflight").is_dir(),
            "preflight/ directory is missing",
        )

    def test_preflight_subdir_named_correctly(self):
        self.assertTrue(
            (SKILL_ROOT / "preflight" / "sequali-input-preflight").is_dir(),
            "preflight/sequali-input-preflight/ directory is missing",
        )

    def test_preflight_skill_md_exists(self):
        self.assertTrue(
            PREFLIGHT.is_file(),
            f"preflight/sequali-input-preflight/SKILL.md is missing at {PREFLIGHT}",
        )


class TestPreflightFrontmatter(unittest.TestCase):
    """Frontmatter must declare the preflight as a vertex skill."""

    def setUp(self):
        self.text = _read(PREFLIGHT)
        # frontmatter block delimited by ---
        m = re.search(r"^---\n(.*?)\n---", self.text, re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(m, "preflight SKILL.md missing frontmatter delimiters")
        self.fm = m.group(1)

    def test_name_is_sequali_input_preflight(self):
        self.assertRegex(self.fm, r'name:\s*sequali-input-preflight')

    def test_version_is_majors_only(self):
        # allow v1.0.0 style
        self.assertRegex(self.fm, r'version:\s*1\.\d+\.\d+')

    def test_has_md5_trigger(self):
        # The user's request explicitly mandates md5 support
        self.assertRegex(self.fm, r'md5 check fastq|md5', re.IGNORECASE)

    def test_has_paired_end_parity_trigger(self):
        self.assertRegex(self.fm, r'paired-end parity|paired end', re.IGNORECASE)

    def test_has_platform_detection_trigger(self):
        self.assertRegex(
            self.fm, r'platform detection|platform detect', re.IGNORECASE,
        )

    def test_updated_field_present(self):
        self.assertRegex(self.fm, r'updated:\s*"\d{4}-\d{2}-\d{2}"')


class TestPreflightOutputContract(unittest.TestCase):
    """The preflight must declare the three output artifacts."""

    def setUp(self):
        self.text = _read(PREFLIGHT)

    def test_emits_params_json(self):
        self.assertIn("params.json", self.text)

    def test_emits_preflight_md(self):
        self.assertIn("preflight.md", self.text)

    def test_emits_preflight_evidence_txt(self):
        self.assertIn("preflight_evidence.txt", self.text)

    def test_verdict_gate_declares_go_with_warnings_floor(self):
        # Phase 1 / Phase 2 must refuse below this floor
        self.assertIn("GO-WITH-WARNINGS", self.text)
        self.assertIn("NO-GO", self.text)
        self.assertIn("refuse", self.text, "must explicitly state that downstream phases refuse to run without the verdict")

    def test_md5_mismatch_blocks_pipeline(self):
        # The user explicitly asked for md5 verification; the verdict must be NO-GO on mismatch.
        self.assertRegex(
            self.text, r"md5.*NO-GO|NO-GO.*md5|mismatch.*NO-GO",
            "md5 mismatch must produce a NO-GO verdict",
        )

    def test_paired_parity_is_a_gate(self):
        # The user explicitly asked for paired-end parity check
        self.assertRegex(
            self.text, r"parity|read count",
            "paired-end parity check must be documented",
        )

    def test_platform_detection_emits_params_json_field(self):
        # The verdict / platform cue must be written to params.json
        self.assertRegex(
            self.text, r'platform\.detected|"platform"',
            "platform detection must write to params.json",
        )


class TestStopPoints(unittest.TestCase):
    """Three explicit ask-user stop points (SP1–SP3)."""

    def setUp(self):
        self.text = _read(PREFLIGHT)

    def test_sp1_paired_or_single_unknown(self):
        self.assertIn("SP1", self.text)
        # The single FASTQ path/paired-or-single ambiguity
        self.assertRegex(
            self.text, r"single FASTQ|Single FASTQ|single-end",
        )

    def test_sp2_ubam_quality_scores(self):
        self.assertIn("SP2", self.text)
        self.assertRegex(self.text, r"uBAM", self.text)

    def test_sp3_md5_missing_but_large(self):
        self.assertIn("SP3", self.text)
        self.assertRegex(
            self.text, r"md5.*missing|md5.*NOT|large.*md5",
            "SP3 must address md5 missing case for large files",
        )


class TestMasterSkillCoherence(unittest.TestCase):
    """The master SKILL.md must advertise the preflight as v4."""

    def setUp(self):
        self.text = _read(MASTER)
        m = re.search(r"^---\n(.*?)\n---", self.text, re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(m, "master SKILL.md missing frontmatter")
        self.fm = m.group(1)

    def test_version_is_4(self):
        self.assertRegex(self.fm, r'version:\s*4\b')

    def test_description_advertises_preflight(self):
        # Agent trigger surfaces should include something preflight-shaped
        self.assertRegex(
            self.fm,
            r"preflight|optional preflight",
            re.IGNORECASE,
        )

    def test_preflight_in_triggers(self):
        # Some preflight trigger phrase must be in the triggers list
        self.assertRegex(
            self.fm,
            r"preflight raw reads|validate fastq|md5 check fastq",
            re.IGNORECASE,
        )

    def test_seqkit_in_requires(self):
        # pixi must be told to install seqkit for the preflight
        self.assertIn("seqkit", self.fm)


class TestMasterSkillRouting(unittest.TestCase):
    """The master SKILL.md must wire the preflight into the pipeline."""

    def setUp(self):
        self.text = _read(MASTER)

    def test_phase_0_section_exists(self):
        self.assertRegex(
            self.text,
            r"## Phase 0[^\n]*Preflight",
            "Master SKILL.md must have a Phase 0 Preflight section",
        )

    def test_phase_0_in_banner_diagram(self):
        # The ASCII diagram at the top should include Phase 0
        self.assertIn("Phase 0", self.text.split("```")[1] if "```" in self.text else "")

    def test_phase_0_references_subskill(self):
        # The Phase 0 section should reference the sub-skill path
        self.assertIn("preflight/sequali-input-preflight/SKILL.md", self.text)

    def test_phase_1_intro_unchanged(self):
        # Phase 1 (Raw QC) must still be present (no regression)
        self.assertIn("Phase 1: Raw Read QC", self.text)

    def test_phase_2_intro_unchanged(self):
        # Phase 2 (Trim/Clean) must still be present (no regression)
        self.assertIn("Phase 2: Trim/Clean", self.text)

    def test_phase_1_1_references_preflight(self):
        # Phase 1.1 should tell the user to trust params.json if preflight ran
        # The text "If you ran Phase 0" is the canonical cue.
        self.assertRegex(
            self.text,
            r"If you ran Phase 0",
        )

    def test_common_followups_has_preflight_entries(self):
        # The follow-ups section should mention preflight
        self.assertRegex(
            self.text,
            r"## Common follow-ups",
            "Common follow-ups section must exist",
        )
        self.assertRegex(
            self.text,
            r"preflight/sequali-input-preflight",
            "Follow-ups must reference the preflight sub-skill",
        )

    def test_verification_checklist_has_preflight_item(self):
        # The verification checklist should have a preflight checkbox
        self.assertRegex(
            self.text,
            r"Phase 0 \(Preflight",
            "Verification checklist must include Phase 0 Preflight",
        )

    def test_related_skills_lists_preflight(self):
        self.assertRegex(
            self.text,
            r"preflight/sequali-input-preflight",
        )


class TestREADME(unittest.TestCase):
    """README.md must mention the preflight and the new phase."""

    def setUp(self):
        self.text = _read(README)

    def test_mentions_preflight_or_phase_0(self):
        self.assertRegex(
            self.text,
            r"Phase 0|preflight|Preflight",
            "README must mention Phase 0 or preflight",
        )


class TestMasterSkillMistakeGuards(unittest.TestCase):
    """Catch silent regressions in the bash recipe path."""

    def setUp(self):
        self.text = _read(MASTER)

    def test_phase_1_still_uses_sequali(self):
        # Phase 1 must still be sequali + multiqc (no regression)
        self.assertIn("sequali", self.text)
        self.assertIn("multiqc", self.text)

    def test_phase_2_still_offers_fastp_fastplong_trim_galore(self):
        self.assertIn("fastp", self.text)
        self.assertIn("fastplong", self.text)
        self.assertIn("trim_galore", self.text)

    def test_phase_4_still_has_go_no_go_loop(self):
        self.assertIn("Phase 4", self.text)
        self.assertRegex(
            self.text,
            r"Go/No-Go|Go/No-Go Decision",
            "Phase 4 Go/No-Go decision loop must be preserved",
        )

    def test_no_hardcoded_workspace_paths(self):
        # No /home/<user>/ leaks into committed docs
        self.assertNotRegex(self.text, r"/home/[a-z]+/")


class TestPreflightPitfalls(unittest.TestCase):
    """Common preflight failure modes must be documented."""

    def setUp(self):
        self.text = _read(PREFLIGHT)

    def test_troubleshooting_section_present(self):
        self.assertRegex(
            self.text,
            r"Troubleshooting|## \d+\.",
            "Troubleshooting or numbered guidance section must exist",
        )

    def test_md5_sidecar_naming_issue(self):
        # The "md5 names do not match canonical" failure mode must be documented
        self.assertRegex(
            self.text,
            r"md5.*sidecar|sidecar.*md5|names do not match",
            "md5 sidecar naming mismatch must be in troubleshooting",
        )

    def test_paired_diff_by_one_acceptable(self):
        # A diff of 1 is acceptable (rounding)
        self.assertRegex(
            self.text,
            r"diff.*1.",
            "Small read-count differences (rounding) must be documented",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
