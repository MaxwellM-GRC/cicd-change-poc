"""Produce reproducible RCM-ready evidence and per-finding case files."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .models import ReviewResult


EXCEPTION_COLUMNS = [
    "run_id", "finding_id", "control_id", "rule", "severity", "platform",
    "object_type", "object_id", "deployment_id", "detail", "remediation",
    "lookback", "root_cause", "closure_evidence",
]


def build_payload(result: ReviewResult, config: dict) -> dict:
    counts = Counter(f.severity for f in result.findings)
    return {
        "schema_version": "1.0",
        "run_id": result.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "control": config["control"],
        "review_window": config["review_window"],
        "remediation_policy": config["remediation"],
        "input_valid": result.input_valid,
        "population_reconciled": result.population_reconciled,
        "population": {
            "production_deployments": result.deployment_count,
            "production_cloud_changes": result.cloud_change_count,
            "cloud_changes_matched_to_cicd": result.matched_cloud_changes,
            "cloud_changes_out_of_band": result.cloud_change_count - result.matched_cloud_changes,
            "deployments_evaluated": len(result.evaluations),
        },
        "source_provenance": [source.as_dict() for source in result.source_status],
        "counts_by_severity": dict(sorted(counts.items())),
        "evaluations": result.evaluations,
        "findings": [finding.as_dict() for finding in result.findings],
    }


def write_evidence(result: ReviewResult, config: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_payload(result, config), indent=2) + "\n", encoding="utf-8")


def write_exceptions(result: ReviewResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXCEPTION_COLUMNS)
        writer.writeheader()
        for finding in result.findings:
            writer.writerow({"run_id": result.run_id, **finding.as_dict()})


def write_cases(result: ReviewResult, config: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for finding in result.findings:
        text = f"""# Change-management exception {finding.finding_id}

- **Run ID:** `{result.run_id}`
- **Control:** `{finding.control_id}`
- **Rule:** `{finding.rule}`
- **Severity:** {finding.severity}
- **Platform:** {finding.platform}
- **Object:** {finding.object_type} `{finding.object_id}`
- **Deployment:** `{finding.deployment_id or 'not applicable'}`
- **Status:** Open — human decision required

## Detection detail

{finding.detail}

## Required response

- [ ] Remediation decision approved by an authorized human: {finding.remediation}
- [ ] Lookback completed: {finding.lookback}
- [ ] Root cause documented: {finding.root_cause}
- [ ] Closure evidence attached: {finding.closure_evidence}
- [ ] Control owner approved closure: {config['control']['owner']}

Automation may detect, route, and recommend. It must not mutate production,
approve its own recommendation, or close this case.
"""
        (directory / f"{finding.finding_id}.md").write_text(text, encoding="utf-8")


def print_summary(result: ReviewResult) -> None:
    counts = Counter(f.severity for f in result.findings)
    print("CLOUD CI/CD CHANGE-MANAGEMENT CONTROL")
    print(f"Run ID: {result.run_id}")
    print(f"Input provenance valid: {result.input_valid}")
    print(f"Production deployments evaluated: {result.deployment_count}")
    print(f"Production cloud changes reviewed: {result.cloud_change_count}")
    print(f"Population reconciled: {result.population_reconciled}")
    print(f"Findings: {len(result.findings)} ({dict(sorted(counts.items()))})")
    for finding in result.findings:
        print(f"[{finding.severity.upper()}] {finding.rule} {finding.platform} "
              f"{finding.object_id}: {finding.detail}")


