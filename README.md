# Cloud CI/CD Change Management — Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cicd-change-poc/actions/workflows/ci.yml/badge.svg)

**Automated detection of production cloud changes that were not properly approved, tested, or traceable to the release pipeline that made them.**

Production changes move quickly. A deployment may look legitimate because it appears in GitHub Actions or GitLab CI, while a failed test, missing approval, or substituted software artifact is hidden in a separate record. At the same time, someone may make a direct AWS or Kubernetes change that never touches the pipeline at all.

This POC brings those records together. It checks the full set of fictional production deployments and cloud changes, then produces an audit-ready exception log and one follow-up case for each issue it finds.

> ⚠️ **Sanitized.** All names, people, repositories, cloud resources, account numbers, and source locations in this repository are fictional. No real employer, client, or production data is included.

---

## The problem it catches

The sample data includes two fictional release paths:

- **GitHub Actions → AWS** — release approvals, test results, source commits, image records, and AWS CloudTrail changes.
- **GitLab CI → Kubernetes** — merge approvals, pipeline tests, source commits, image records, and Kubernetes audit-log changes.

Reviewing each source on its own can make a change look clean. For example, a deployment record may exist even though the required test failed, or an AWS role may be changed directly from the console with no deployment record at all.

The sample deliberately includes fourteen issues, covering every control in the rule set:

- an unapproved pull request, rejected deployment approval, and self-approval;
- a failed test and a self-reviewed merge request;
- an unauthorized pipeline and deployment identity;
- an emergency release without retrospective review;
- an unreviewed pipeline-definition change and missing branch protection;
- a mismatch between the deployed software and the recorded build artifact;
- a rolled-back deployment without an incident record; and
- a direct cloud change with no corresponding release pipeline.

Only by connecting the release record to its approval, test, source, artifact, and cloud-side activity does the full picture emerge.

## What this control tests

| Control | Control description | Severity |
|---|---|---|
| CM-01 | Confirm every production deployment maps to an approved pull or merge request. | Critical |
| CM-02 | Confirm required independent review occurred before merge. | High |
| CM-03 | Confirm required CI checks passed for the deployed commit. | High |
| CM-04 | Confirm the deployed commit SHA matches the reviewed and approved SHA. | Critical |
| CM-05 | Confirm the deployment used an authorized pipeline rather than an unapproved manual path. | Critical |
| CM-06 | Confirm production deployment approval occurred before release, where required. | Critical |
| CM-07 | Confirm the developer did not solely approve and deploy their own change. | High |
| CM-08 | Confirm the deployment identity was authorized for production. | High |
| CM-09 | Confirm an emergency deployment received retrospective review timely. | High |
| CM-10 | Confirm pipeline or infrastructure-control definition changes received heightened review. | High |
| CM-11 | Confirm production cloud changes made outside the pipeline were detected. | Critical |
| CM-12 | Confirm artifact provenance links source commit, build, and deployed artifact. | Critical |
| CM-13 | Confirm branch and environment protections remain configured as required. | High |
| CM-14 | Confirm failed or rolled-back deployments have a linked incident or resolution record. | Medium |

## How it works

```text
GitHub / GitLab deployments ─┐
Approvals, tests, commits ───┤
Build-artifact records ──────┼─► validate inputs ─► connect evidence ─► report
AWS / Kubernetes changes ────┘                         every change       issues
```

- **Input validation** checks that every expected file is present, complete, and unchanged since it was collected. If a source is missing or altered, the review stops rather than reporting a misleading clean result.
- **Evidence matching** follows each deployment from approval through test, source code, built software, and its production cloud activity.
- **Reverse matching** starts with each AWS or Kubernetes production change and asks whether it can be traced back to a release pipeline.
- **Reporting** writes a simple exception log, a detailed run summary, and one human-owned case for every actionable finding.

Every run records where its data came from, the period reviewed, row counts, and a file fingerprint. This lets a reviewer see what was checked and re-perform the same review later.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the review and write evidence to output/
.venv/bin/python -m src.main

# Run the tests
.venv/bin/python -m pytest -q
```

## Sample output

```text
CLOUD CI/CD CHANGE-MANAGEMENT CONTROL
Production deployments evaluated: 6
Production cloud changes reviewed: 8
Population reconciled: True
Findings: 14 ({'critical': 6, 'high': 7, 'medium': 1})

[CRITICAL] CM-01 github_aws gha-aws-002
           Deployment does not map to an approved pull or merge request.
[HIGH]     CM-03 github_aws gha-aws-003
           Required CI checks were missing, failed, or completed after deployment.
[CRITICAL] CM-11 github_aws ct-9004
           Production change ... does not map to any in-scope CI/CD deployment.
```

The generated files are the evidence package:

```text
output/
  control_evidence.json   Detailed run summary, population counts, and source checks
  exceptions.csv          One straightforward row per finding
  cases/CM-*.md           One follow-up case per finding, with closure checklist
```

The review exits with `0` when it runs successfully. With `--fail-on-findings`, it exits with `2` when it detects exceptions. An input problem returns `3`, so a failed evidence check cannot be mistaken for a clean review.

## Continuous monitoring

This is designed to run repeatedly, not just once.

- **CI** (`ci.yml`) runs the test suite and a sample review on every change. It shows whether the POC itself is working correctly.
- **Change Control Monitor** (`control-monitor.yml`) runs every weekday, on demand, and after changes reach `main`. It saves the evidence first, opens or updates one GitHub Issue for each finding, then turns red when issues exist.
- **Exception Escalation** (`exception-escalation.yml`) flags open cases that pass the configured five-day response target.

A red Change Control Monitor run is expected with the included sample data: the sample is intentionally seeded with exceptions. The red status is the alert; the uploaded evidence and individual Issues show what needs attention.

Automation can identify and route an issue, but it cannot make a production change, approve a risk decision, or close a case. Those steps require a human owner.

## Repository map

```text
config.yaml                 Control rules, response guidance, and source mappings
data/                       Fictional GitHub, GitLab, AWS, and Kubernetes evidence
data/source_manifest.json   Source details, row counts, and file fingerprints
src/                        Input checks, evidence matching, detection, reporting
tests/                      Tests for rules, source checks, and output reconciliation
docs/                       Control narrative, evidence contract, production notes
```

## Control context

This POC supports a change-management IT general control: production changes should be approved, tested, traceable, and made through an authorized process. It is organized so a reviewer can inspect the source population, see how each test was performed, and follow an exception from detection through human resolution.

For detailed material, see [Evidence contract](docs/evidence_contract.md), [RCM and control narrative](docs/rcm_and_control_narrative.md), and [Production design](docs/production_design.md).

## Scope note

This is a focused proof of concept using static fictional files. A production implementation would collect evidence directly from the relevant GitHub, GitLab, AWS, Kubernetes, and artifact-registry services; retain it under the organization's evidence policy; and confirm population coverage for every in-scope environment.

MIT — see [LICENSE](LICENSE).
