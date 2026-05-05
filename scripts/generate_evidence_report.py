#!/usr/bin/env python3
"""Summarize machine-readable release-evidence artifacts for the technical exploration report."""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _parse_junit(path: Path) -> dict[str, int | str]:
    root = ET.parse(path).getroot()  # noqa: S314
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    if suite is None:
        return {"error": f"no testsuite in {path}"}
    return {
        "tests": int(suite.attrib.get("tests", "0")),
        "failures": int(suite.attrib.get("failures", "0")),
        "errors": int(suite.attrib.get("errors", "0")),
        "skipped": int(suite.attrib.get("skipped", "0")),
        "time_s": suite.attrib.get("time", ""),
        "timestamp": suite.attrib.get("timestamp", ""),
    }


def _parse_coverage_xml(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()  # noqa: S314
    line_rate = float(root.attrib.get("line-rate", "0"))
    branch_rate = float(root.attrib.get("branch-rate", "0"))
    lines_valid = int(root.attrib.get("lines-valid", "0"))
    lines_covered = int(root.attrib.get("lines-covered", "0"))
    return {
        "line_rate_pct": round(line_rate * 100.0, 2),
        "branch_rate_pct": round(branch_rate * 100.0, 2),
        "lines_covered": lines_covered,
        "lines_valid": lines_valid,
    }


def _parse_vendor_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    summaries = data.get("summaries")
    out: dict[str, Any] = {"runs": len(data.get("runs", []))}
    if isinstance(summaries, list):
        out["summaries"] = []
        for s in summaries:
            if not isinstance(s, dict):
                continue
            out["summaries"].append(
                {
                    "provider": s.get("provider"),
                    "median_ttfb_ms": s.get("median_ttfb_ms"),
                    "sample_count": s.get("sample_count"),
                },
            )
    return out


def _junit_lines(title: str, path: Path, root: Path) -> list[str]:
    if not path.is_file():
        return [f"*Missing `{path.relative_to(root)}`*", ""]
    j = _parse_junit(path)
    t, f, e, sk = j["tests"], j["failures"], j["errors"], j["skipped"]
    return [
        title,
        f"- tests: {t}, failures: {f}, errors: {e}, skipped: {sk}",
        f"- JUnit: `{path.relative_to(root)}`",
        "",
    ]


def _coverage_lines(path: Path, reps: Path, root: Path) -> list[str]:
    if not path.is_file():
        return [f"*Missing `{path.relative_to(root)}`*", ""]
    c = _parse_coverage_xml(path)
    rel_cov = path.relative_to(root)
    rel_rep = reps.relative_to(root)
    return [
        "### Coverage (`src/eleven_demo/`, integration excluded)",
        (
            f"- Line rate (cobertura): **{c['line_rate_pct']}%** "
            f"({c['lines_covered']}/{c['lines_valid']} lines)"
        ),
        f"- Branch rate: **{c['branch_rate_pct']}%**",
        f"- XML / HTML: `{rel_cov}`, `{rel_rep}/htmlcov/`",
        "",
    ]


def _vendor_lines(path: Path, root: Path) -> list[str]:
    vendor = _parse_vendor_json(path)
    head = ["### Vendor benchmark JSON"]
    if vendor is None:
        head.append(
            f"- `{path.relative_to(root)}` **not present** — run "
            "`uv run python scripts/tts_vendor_benchmark.py --n 5 ...` with "
            "`DEFAULT_PT_VOICE_ID` and `OPENAI_API_KEY` set.",
        )
        head.append("")
        return head
    head.append(f"- `{path.relative_to(root)}` — {vendor['runs']} runs recorded.")
    for s in vendor.get("summaries", []):
        med = s.get("median_ttfb_ms")
        med_s = "n/a" if isinstance(med, float) and math.isnan(med) else str(med)
        prov = s.get("provider")
        n = s.get("sample_count")
        head.append(f"  - **{prov}**: median TTFB ms ≈ {med_s}, n={n}")
    head.append("")
    return head


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print Markdown evidence summary (JUnit, coverage, vendor JSON) for docs.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root",
    )
    args = parser.parse_args()
    root: Path = args.root
    reps = root / "artifacts" / "reports"
    bench = root / "artifacts" / "benchmarks"

    lines: list[str] = ["## Evidence summary (generated)", ""]
    unit_xml = reps / "pytest.xml"
    int_xml = reps / "integration-pytest.xml"
    cov_xml = reps / "coverage.xml"
    vendor_json = bench / "tts-vendor-latest.json"
    pre_commit = reps / "pre-commit.txt"

    lines.extend(
        _junit_lines('### Unit tests (`pytest -m "not integration"`, xdist)', unit_xml, root),
    )
    lines.extend(_junit_lines("### Integration replay (`pytest -m integration`)", int_xml, root))
    lines.extend(_coverage_lines(cov_xml, reps, root))

    if pre_commit.is_file():
        lines.extend(["### Pre-commit", f"- Log: `{pre_commit.relative_to(root)}`", ""])
    else:
        lines.extend([f"*Missing `{pre_commit.relative_to(root)}`*", ""])

    lines.extend(_vendor_lines(vendor_json, root))
    sys.stdout.write("\n".join(lines))


if __name__ == "__main__":
    main()
