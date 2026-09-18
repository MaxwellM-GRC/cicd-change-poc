# Control Evidence Contract

## Purpose

The evidence package is designed to support design evaluation, operating
effectiveness testing, re-performance, and exception follow-up for control
`ITGC-CM-01`. A reviewer should be able to answer four questions without
reconstructing the run from console output:

1. What complete populations were evaluated?
2. Where did every source originate, and was it changed after extraction?
3. Which evidence supports every assertion for every deployment?
4. Who must decide and approve the response to each exception?

## Inputs

`config.yaml` enumerates every required source and its schema. The retained
`data/source_manifest.json` provides, per extract:

| Field | Contract |
|---|---|
| `source_id` | Must exactly match one configured source |
| `source_uri` | Identifies the fictional source API or audit store |
| `query` | States how the complete population or evidence subset was selected |
| `extracted_at` | Records when extraction completed |
| `window_start` / `window_end` | Must equal the configured control period |
| `row_count` | Must reconcile to the retained CSV |
| `sha256` | Must match the retained bytes exactly |

The input gate also requires every mapped column, nonblank and unique source
primary keys, no unmanifested source, and no configured source omitted from the
manifest. Any failure stops evaluation.

## Populations and joins

The primary populations are all production deployment records from GitHub and
GitLab plus all production mutation events from CloudTrail and Kubernetes audit
logs. Approval, test, commit, and artifact sources are supporting evidence.

The forward join begins with each deployment and records a pass/fail result for
all deployment-specific assertions. Merge review must precede merge, and an
emergency retrospective review must fall inside the configured response window.
The reverse join begins with each cloud change and verifies its pipeline run,
artifact digest, authorized deployment identity, and proximity to the deployment
time. This two-direction design detects both incomplete deployment evidence and
changes made outside CI/CD.

## Outputs

`control_evidence.json` is the canonical run package:

- `schema_version`, deterministic `run_id`, generation timestamp;
- control metadata, review window, and remediation policy;
- source status with expected/actual counts and hashes;
- primary-population reconciliation counts;
- complete deployment assertion ledger with source-record references; and
- complete finding objects with response guidance.

`exceptions.csv` is a flat, auditor-friendly extract. `cases/CM-*.md` creates
one case per stable finding ID. The ID is derived from control, rule, platform,
object type, and object ID; it intentionally excludes run time and narrative so
the same unresolved condition is maintained across runs.

## Re-performance

The deterministic run ID hashes the control configuration and all retained
source hashes. Identical inputs and parameters produce the same ID and findings.
The output generation timestamp is informational and is not part of the ID.
Retain the repository commit SHA alongside the generated artifacts to identify
the exact code version used.

## Human decision boundary

Rule guidance is advisory and is tailored to the control that raised the case.
Every case requires a named human to approve the
rollback, redeployment, risk acceptance, or other disposition and to approve
closure evidence. The configured policy explicitly prohibits automatic
rollback, production mutation, and automatic closure.
