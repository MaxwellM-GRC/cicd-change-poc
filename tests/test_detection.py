from dataclasses import replace
from pathlib import Path

import yaml

from src.detection import evaluate
from src.loaders import load_sources


ROOT = Path(__file__).resolve().parents[1]


def _result():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    deployments, changes, evidence = load_sources(config, ROOT)
    return config, deployments, changes, evaluate(config, deployments, changes, evidence)


def _inputs():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    return (config, *load_sources(config, ROOT))


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


def test_review_must_precede_merge_not_merely_deployment():
    config, deployments, changes, evidence = _inputs()
    governance = next(row for row in evidence["github_aws"]["governance"] if row["deployment_id"] == "gha-aws-001")
    governance["reviewed_at"] = "2026-08-05T13:35:00Z"  # after merge, before deployment
    findings, _, _ = evaluate(config, deployments, changes, evidence)
    assert any(f.rule == "CM-02" and f.deployment_id == "gha-aws-001" for f in findings)


def test_cloud_change_requires_matching_run_digest_identity_and_time():
    config, deployments, changes, evidence = _inputs()
    tampered = [replace(change, actor="unapproved-console-user") if change.event_id == "ct-9001" else change for change in changes]
    findings, _, _ = evaluate(config, deployments, tampered, evidence)
    assert any(f.rule == "CM-11" and f.object_id == "ct-9001" for f in findings)
