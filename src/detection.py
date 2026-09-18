"""Full-population CI/CD evidence correlation and exception detection."""

from __future__ import annotations

from collections import defaultdict

from .models import CloudChange, Deployment, Finding


def _one(rows: list[dict], key: str, value: str) -> dict | None:
    return next((row for row in rows if row.get(key) == value), None)


def _finding(config: dict, rule: str, platform: str, object_type: str,
             object_id: str, deployment_id: str, detail: str) -> Finding:
    response = config["rules"][rule]
    return Finding(
        control_id=config["control"]["id"], rule=rule,
        severity=response["severity"], platform=platform,
        object_type=object_type, object_id=object_id,
        deployment_id=deployment_id, detail=detail,
        remediation=response["remediation"], lookback=response["lookback"],
        root_cause=response["root_cause"],
        closure_evidence=response["closure_evidence"],
    )


def evaluate(config: dict, deployments: list[Deployment], changes: list[CloudChange],
             evidence: dict) -> tuple[list[Finding], list[dict], int]:
    findings: list[Finding] = []
    evaluations: list[dict] = []
    changes_by_platform: dict[str, list[CloudChange]] = defaultdict(list)
    for change in changes:
        changes_by_platform[change.platform].append(change)

    deployment_runs = {(dep.platform, dep.run_id): dep for dep in deployments}
    matched_change_ids: set[str] = set()

    for dep in deployments:
        feeds = evidence[dep.platform]
        approval = _one(feeds["approvals"], "deployment_id", dep.deployment_id)
        approval_ok = bool(
            approval and approval["status"].lower() == "approved"
            and approval["requester"] != approval["approver"]
            and approval["approved_at"] <= dep.deployed_at
        )
        if not approval_ok:
            findings.append(_finding(
                config, "CM01_APPROVAL", dep.platform, "deployment", dep.deployment_id,
                dep.deployment_id,
                "No independent approved authorization completed before deployment."
            ))

        test = _one(feeds["tests"], "run_id", dep.run_id)
        test_ok = bool(test and test["status"].lower() == "passed"
                       and test["completed_at"] <= dep.deployed_at)
        if not test_ok:
            findings.append(_finding(
                config, "CM02_TESTING", dep.platform, "deployment", dep.deployment_id,
                dep.deployment_id, "Required tests were missing, failed, or completed after deployment."
            ))

        commit = _one(feeds["commits"], "commit_sha", dep.commit_sha)
        commit_ok = bool(commit and commit["protected_branch"].lower() == "true"
                         and commit["signature_verified"].lower() == "true")
        if not commit_ok:
            findings.append(_finding(
                config, "CM03_COMMIT", dep.platform, "deployment", dep.deployment_id,
                dep.deployment_id, "Commit is missing or lacks protected-branch and verified-signature evidence."
            ))

        artifact = _one(feeds["artifacts"], "run_id", dep.run_id)
        artifact_ok = bool(
            artifact and artifact["artifact_digest"] == dep.artifact_digest
            and artifact["built_from_commit"] == dep.commit_sha
        )
        if not artifact_ok:
            findings.append(_finding(
                config, "CM04_ARTIFACT", dep.platform, "deployment", dep.deployment_id,
                dep.deployment_id, "Deployed digest does not trace to the run artifact built from the deployed commit."
            ))

        matched = [c for c in changes_by_platform[dep.platform] if c.run_id == dep.run_id]
        trace_ok = bool(matched)
        if trace_ok:
            matched_change_ids.update(change.event_id for change in matched)
            if any(change.artifact_digest != dep.artifact_digest for change in matched):
                artifact_ok = False
                findings.append(_finding(
                    config, "CM04_ARTIFACT", dep.platform, "deployment", dep.deployment_id,
                    dep.deployment_id, "Control-plane digest differs from the deployment record."
                ))
        else:
            findings.append(_finding(
                config, "CM05_DEPLOYMENT_TRACE", dep.platform, "deployment", dep.deployment_id,
                dep.deployment_id, "No production control-plane audit event maps to the CI/CD run."
            ))

        evaluations.append({
            "platform": dep.platform, "deployment_id": dep.deployment_id,
            "run_id": dep.run_id, "commit_sha": dep.commit_sha,
            "artifact_digest": dep.artifact_digest,
            "evidence_refs": {
                "approval_id": approval["approval_id"] if approval else "",
                "test_run_id": test["run_id"] if test else "",
                "commit_sha": commit["commit_sha"] if commit else "",
                "artifact_id": artifact["artifact_id"] if artifact else "",
                "cloud_event_ids": [change.event_id for change in matched],
            },
            "assertions": {
                "approval": approval_ok, "testing": test_ok, "commit": commit_ok,
                "artifact": artifact_ok, "deployment_trace": trace_ok,
            },
            "result": "pass" if all((approval_ok, test_ok, commit_ok, artifact_ok, trace_ok)) else "exception",
        })

    for change in changes:
        if (change.platform, change.run_id) not in deployment_runs:
            findings.append(_finding(
                config, "CM06_OUT_OF_BAND", change.platform, "cloud_change", change.event_id,
                "", f"Production change {change.action} on {change.resource} by {change.actor} "
                "does not map to any in-scope CI/CD deployment."
            ))

    return findings, evaluations, len(matched_change_ids)


