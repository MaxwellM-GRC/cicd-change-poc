# Cloud-Native CI/CD Change Management — Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cicd-change-poc/actions/workflows/ci.yml/badge.svg)

An RCM-ready automated control that tests the **complete population** of
production deployments and production control-plane changes across two
fictional paths:

- GitHub Actions → AWS (workflow approvals, checks, commits, ECR digests, and CloudTrail)
- GitLab CI → Kubernetes (merge approvals, pipeline tests, commits, OCI digests, and audit logs)

It proves each production deployment was independently approved, tested, tied
to a governed commit, and executed with the expected immutable artifact. It
also reverses the test: every cloud-side mutation must map back to CI/CD, which
surfaces console, CLI, or cluster-admin changes that bypassed the pipeline.

> **Sanitized:** Acme, all people, account IDs, resources, repositories, and
> source URIs are fictional. No employer, client, or production data appears here.

## What this control tests

| Rule | Assertion | Severity |
|---|---|---|
| `CM01_APPROVAL` | Independent approval completed before deployment | Critical |
| `CM02_TESTING` | Required tests passed before deployment | High |
| `CM03_COMMIT` | Commit is verified and on a protected branch | High |
| `CM04_ARTIFACT` | Deployed digest matches the artifact built from that commit and run | Critical |
| `CM05_DEPLOYMENT_TRACE` | CI/CD deployment has matching cloud execution evidence | High |
| `CM06_OUT_OF_BAND` | Cloud change maps back to an in-scope CI/CD deployment | Critical |

The fixtures deliberately include one rejected AWS approval, one failed test,
one artifact substitution, one GitLab self-approval, one ungoverned commit, and
two out-of-band cloud changes. These produce **7 stable, per-finding exception
cases** while two baseline deployments pass every assertion.

## Evidence flow

```text
GitHub/GitLab deployment population ─┐
approvals + tests + commits + images ├─ provenance validation ─ full-population join
CloudTrail/Kubernetes audit events ──┘                              │
                                                                    ├─ control_evidence.json
                                                                    ├─ exceptions.csv
                                                                    └─ one human-owned case/finding
```

Every input is declared in `data/source_manifest.json` with a source URI,
extraction query, timestamp, review window, row count, and SHA-256. A missing,
changed, incomplete, duplicated, or out-of-window source makes the run fail
closed with exit code `3`; the control does not claim a clean result from
untrusted evidence.

The output contract preserves:

- a deterministic run ID bound to the config and all source hashes;
- source provenance and input validation results;
- population counts for deployments and cloud changes;
- one assertion ledger row for every production deployment;
- evidence references for approval, test, commit, artifact, and cloud event;
- stable finding IDs and prescribed response fields; and
- one Markdown case per finding with human approval required for disposition and closure.

See [Evidence contract](docs/evidence_contract.md) and
[RCM and control narrative](docs/rcm_and_control_narrative.md).

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.main
```

Generated evidence is written to `output/` (gitignored):

```text
output/
  control_evidence.json   complete machine-readable run package
  exceptions.csv         one row per finding
  cases/CM-*.md           one independently trackable exception case per finding
```

Exit codes are `0` for a valid completed run, `2` when
`--fail-on-findings` is supplied and findings exist, and `3` when provenance or
input-integrity validation fails.

## Continuous monitoring

`control-monitor.yml` runs on a weekday schedule, on demand, and on changes to
`main`. It always uploads the evidence package before raising an alert. Each
finding is maintained as its own GitHub Issue using the stable finding ID; an
open issue receives observation comments, and a recurring closed issue is
reopened. The run then turns red when findings exist so notification is not
silently lost.

`exception-escalation.yml` ages open cases and flags those past the configured
five-day SLA. Automation can detect, route, recommend, and escalate. It cannot
roll back production, mutate resources, approve its own advice, or close an
exception. Those are explicit human decisions.

## Repository map

```text
config.yaml                 control, rule response, and source contract
data/source_manifest.json   source provenance and content hashes
data/github_aws/            fictional GitHub Actions/AWS evidence
data/gitlab_k8s/            fictional GitLab CI/Kubernetes evidence
data/cloudtrail/            complete fictional AWS production-change population
data/kubernetes/            complete fictional Kubernetes mutation population
src/integrity.py            fail-closed manifest/schema/count/hash checks
src/loaders.py              normalized source ingestion
src/detection.py            full-population correlation and CM01–CM06 rules
src/reporting.py            evidence package, exception log, individual cases
tests/                      provenance, rules, reconciliation, outputs, run IDs
docs/                       RCM, evidence contract, and production design
```

## Scope and reliance

This is a proof of concept, not a live AWS, GitHub, GitLab, or Kubernetes
integration. Production deployment requires authoritative API collectors,
immutable evidence retention, service-account hardening, organization-specific
approval semantics, and independent validation of the population queries.
Those boundaries are detailed in [Production design](docs/production_design.md).

MIT licensed.

