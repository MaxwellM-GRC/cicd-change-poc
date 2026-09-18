"""Command-line entry point for the change-management control."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from .detection import evaluate
from .integrity import validate_sources
from .loaders import load_sources
from .models import ReviewResult
from .reporting import print_summary, write_cases, write_evidence, write_exceptions


ROOT = Path(__file__).resolve().parents[1]


def _run_id(config_path: Path, statuses) -> str:
    payload = {
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "sources": [(s.source_id, s.actual_sha256) for s in statuses],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"RUN-{digest[:16]}"


def run(config_path: Path, manifest_path: Path) -> tuple[ReviewResult, dict]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    statuses = validate_sources(config, ROOT, manifest_path)
    run_id = _run_id(config_path, statuses)
    if not all(status.ok for status in statuses):
        return ReviewResult(run_id, [], [], statuses, 0, 0, 0), config
    deployments, changes, evidence = load_sources(config, ROOT)
    findings, evaluations, matched = evaluate(config, deployments, changes, evidence)
    return ReviewResult(
        run_id, findings, evaluations, statuses,
        len(deployments), len(changes), matched,
    ), config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/source_manifest.json")
    parser.add_argument("--evidence-json", type=Path, default=ROOT / "output/control_evidence.json")
    parser.add_argument("--exceptions-csv", type=Path, default=ROOT / "output/exceptions.csv")
    parser.add_argument("--cases-dir", type=Path, default=ROOT / "output/cases")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)

    result, config = run(args.config, args.manifest)
    write_evidence(result, config, args.evidence_json)
    write_exceptions(result, args.exceptions_csv)
    if result.input_valid:
        write_cases(result, config, args.cases_dir)
    print_summary(result)
    if not result.input_valid:
        for source in result.source_status:
            if not source.ok:
                print(f"INVALID SOURCE {source.source_id}: {source.errors}")
        return 3
    if args.fail_on_findings and result.findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

