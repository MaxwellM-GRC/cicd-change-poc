"""Full-population evaluation of the 14 cloud change-management controls."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .models import CloudChange, Deployment, Finding


def _one(rows: list[dict], key: str, value: str) -> dict | None:
    return next((row for row in rows if row.get(key) == value), None)


def _yes(value: str | None) -> bool:
    return (value or "").lower() == "true"


def _time(value: str) -> datetime:
    """Parse the canonical UTC timestamps used by collectors and fixtures."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _finding(config: dict, rule: str, platform: str, object_type: str,
             object_id: str, deployment_id: str, detail: str) -> Finding:
    control = config["rules"][rule]
    response = config["rule_responses"][rule]
    return Finding(
        control_id=config["control"]["id"], rule=rule,
        severity=control["severity"], platform=platform, object_type=object_type,
        object_id=object_id, deployment_id=deployment_id, detail=detail,
        remediation=response["remediation"], lookback=response["lookback"],
        root_cause=response["root_cause"], closure_evidence=response["closure_evidence"],
    )


def _record(findings, config, rule, dep, condition, detail):
    if not condition:
        findings.append(_finding(config, rule, dep.platform, "deployment", dep.deployment_id,
                                 dep.deployment_id, detail))


def evaluate(config: dict, deployments: list[Deployment], changes: list[CloudChange],
             evidence: dict) -> tuple[list[Finding], list[dict], int]:
    """Evaluate each deployment, then reconcile every cloud change back to CI/CD."""
    findings: list[Finding] = []
    evaluations: list[dict] = []
    by_platform_changes: dict[str, list[CloudChange]] = defaultdict(list)
    for change in changes:
        by_platform_changes[change.platform].append(change)
    deployment_runs = {(dep.platform, dep.run_id): dep for dep in deployments}
    matched_change_ids: set[str] = set()

    for dep in deployments:
        feeds = evidence[dep.platform]
        governance = _one(feeds["governance"], "deployment_id", dep.deployment_id)
        approval = _one(feeds["approvals"], "deployment_id", dep.deployment_id)
        test = _one(feeds["tests"], "run_id", dep.run_id)
        artifact = _one(feeds["artifacts"], "run_id", dep.run_id)
        reconciliation_window = timedelta(
            minutes=config["control_parameters"]["cloud_reconciliation_window_minutes"]
        )
        deployment_time = _time(dep.deployed_at)
        matched = [
            item for item in by_platform_changes[dep.platform]
            if governance
            and item.run_id == dep.run_id
            and item.artifact_digest == dep.artifact_digest
            and item.actor == governance["deployment_identity"]
        ]

        pr_ok = bool(governance and governance["pr_id"] and governance["pr_status"] == "merged"
                     and governance["merged_at"])
        review_ok = bool(governance and governance["review_status"] == "approved"
                         and governance["reviewer"] != governance["author"]
                         and governance["reviewed_at"] <= governance["merged_at"])
        test_ok = bool(test and test["status"] == "passed" and test["completed_at"] <= dep.deployed_at)
        sha_ok = bool(governance and governance["merged_sha"] == dep.commit_sha)
        pipeline_ok = bool(governance and _yes(governance["pipeline_authorized"]))
        approval_ok = bool(approval and approval["status"] == "approved"
                           and approval["approved_at"] <= dep.deployed_at)
        separation_ok = bool(approval and governance
                             and approval["approver"] not in {governance["author"], governance["deploy_initiator"]})
        identity_ok = bool(governance and governance["deployment_identity"] and _yes(governance["identity_authorized"]))
        emergency_ok = bool(governance and (
            not _yes(governance["is_emergency"])
            or (governance["retrospective_review_at"]
                and deployment_time <= _time(governance["retrospective_review_at"])
                <= deployment_time + timedelta(hours=config["control_parameters"]["emergency_review_sla_hours"])
            )
        ))
        artifact_ok = bool(artifact and artifact["artifact_digest"] == dep.artifact_digest
                           and artifact["built_from_commit"] == dep.commit_sha)
        matched = [item for item in matched if abs(_time(item.changed_at) - deployment_time) <= reconciliation_window]
        outcome_ok = bool(governance and (
            governance["outcome"] not in {"failed", "rolled_back"} or governance["incident_id"]
        ))

        _record(findings, config, "CM-01", dep, pr_ok, "Deployment does not map to an approved pull or merge request.")
        _record(findings, config, "CM-02", dep, review_ok, "Required independent review is missing, self-reviewed, or not timely.")
        _record(findings, config, "CM-03", dep, test_ok, "Required CI checks were missing, failed, or completed after deployment.")
        _record(findings, config, "CM-04", dep, sha_ok, "Deployed commit SHA does not match the reviewed and approved SHA.")
        _record(findings, config, "CM-05", dep, pipeline_ok, "Deployment did not use an authorized production pipeline.")
        _record(findings, config, "CM-06", dep, approval_ok, "Required production approval was missing, rejected, or late.")
        _record(findings, config, "CM-07", dep, separation_ok, "Developer solely approved their own change.")
        _record(findings, config, "CM-08", dep, identity_ok, "Deployment identity is missing or unauthorized for production.")
        _record(findings, config, "CM-09", dep, emergency_ok, "Emergency deployment lacks a timely retrospective review.")
        _record(findings, config, "CM-12", dep, artifact_ok, "Artifact provenance does not link deployed artifact to the source commit and build.")
        _record(findings, config, "CM-14", dep, outcome_ok, "Failed or rolled-back deployment has no linked incident or resolution record.")

        evaluations.append({
            "platform": dep.platform, "deployment_id": dep.deployment_id, "run_id": dep.run_id,
            "commit_sha": dep.commit_sha, "artifact_digest": dep.artifact_digest,
            "evidence_refs": {"pr_id": governance["pr_id"] if governance else "",
                              "approval_id": approval["approval_id"] if approval else "",
                              "test_run_id": test["run_id"] if test else "",
                              "artifact_id": artifact["artifact_id"] if artifact else "",
                              "cloud_event_ids": [item.event_id for item in matched]},
            "assertions": {"CM-01": pr_ok, "CM-02": review_ok, "CM-03": test_ok,
                           "CM-04": sha_ok, "CM-05": pipeline_ok, "CM-06": approval_ok,
                           "CM-07": separation_ok, "CM-08": identity_ok, "CM-09": emergency_ok,
                           "CM-12": artifact_ok, "CM-14": outcome_ok},
            "result": "pass" if all((pr_ok, review_ok, test_ok, sha_ok, pipeline_ok, approval_ok,
                                        separation_ok, identity_ok, emergency_ok, artifact_ok, outcome_ok)) else "exception",
        })
        matched_change_ids.update(item.event_id for item in matched)

    for item in evidence["shared"]["control_definition_changes"]:
        if not _yes(item["heightened_review"]):
            findings.append(_finding(config, "CM-10", item["platform"], "control_definition", item["change_id"], "",
                                     f"Change to {item['target']} lacks heightened review evidence."))
    for item in evidence["shared"]["protection_settings"]:
        if not (_yes(item["branch_protection"]) and _yes(item["environment_protection"])):
            findings.append(_finding(config, "CM-13", item["platform"], "protection_setting", item["setting_id"], "",
                                     "Required branch or environment protection is not configured."))
    for change in changes:
        deployment = deployment_runs.get((change.platform, change.run_id))
        authorized = bool(
            deployment
            and change.artifact_digest == deployment.artifact_digest
            and abs(_time(change.changed_at) - _time(deployment.deployed_at))
            <= timedelta(minutes=config["control_parameters"]["cloud_reconciliation_window_minutes"])
            and (governance := _one(evidence[change.platform]["governance"], "deployment_id", deployment.deployment_id))
            and change.actor == governance["deployment_identity"]
        )
        if not authorized:
            findings.append(_finding(config, "CM-11", change.platform, "cloud_change", change.event_id, "",
                                     f"Production change {change.action} on {change.resource} by {change.actor} does not map to CI/CD."))
    return findings, evaluations, len(matched_change_ids)
