import csv
import json
from pathlib import Path

from src.main import ROOT, run
from src.reporting import write_cases, write_evidence, write_exceptions


def test_evidence_and_case_outputs_reconcile(tmp_path):
    result, config = run(ROOT / "config.yaml", ROOT / "data/source_manifest.json")
    evidence = tmp_path / "evidence.json"
    exceptions = tmp_path / "exceptions.csv"
    cases = tmp_path / "cases"
    write_evidence(result, config, evidence)
    write_exceptions(result, exceptions)
    write_cases(result, config, cases)

    payload = json.loads(evidence.read_text())
    rows = list(csv.DictReader(exceptions.open()))
    assert payload["input_valid"] is True
    assert payload["population_reconciled"] is True
    assert payload["population"]["production_deployments"] == 6
    assert payload["population"]["production_cloud_changes"] == 8
    assert len(payload["evaluations"]) == 6
    assert len(payload["findings"]) == len(rows) == 14
    assert len(list(cases.glob("CM-*.md"))) == 14
    assert all("human decision required" in p.read_text().lower() for p in cases.iterdir())


def test_run_id_is_reproducible_for_same_config_and_sources():
    first, _ = run(ROOT / "config.yaml", ROOT / "data/source_manifest.json")
    second, _ = run(ROOT / "config.yaml", ROOT / "data/source_manifest.json")
    assert first.run_id == second.run_id
