from pathlib import Path

import yaml

from src.detection import evaluate
from src.loaders import load_sources


ROOT = Path(__file__).resolve().parents[1]


def _result():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    deployments, changes, evidence = load_sources(config, ROOT)
    return config, deployments, changes, evaluate(config, deployments, changes, evidence)


def test_full_production_population_is_evaluated():
    _, deployments, changes, (findings, evaluations, matched) = _result()
    assert len(deployments) == 6
    assert len(changes) == 8
    assert len(evaluations) == 6
    assert {row["deployment_id"] for row in evaluations} == {d.deployment_id for d in deployments}
    assert matched == 7


def test_seeded_exception_contract():
    _, _, _, (findings, _, _) = _result()
    rules = [finding.rule for finding in findings]
    assert len(findings) == 14
    assert set(rules) == {f"CM-{number:02d}" for number in range(1, 15)}
    assert rules.count("CM-11") == 1
    assert len({finding.finding_id for finding in findings}) == len(findings)


def test_happy_path_deployments_pass_all_assertions():
    _, _, _, (_, evaluations, _) = _result()
    passing = {row["deployment_id"] for row in evaluations if row["result"] == "pass"}
    assert passing == {"gha-aws-001", "gl-k8s-001"}
