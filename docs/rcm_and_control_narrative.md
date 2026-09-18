# RCM and Control Narrative

## RCM entry

| Attribute | Definition |
|---|---|
| Control ID | `ITGC-CM-01` |
| Risk | Unauthorized, untested, or untraceable production changes could compromise financial-system processing, security, or availability. |
| Objective | Production changes are authorized, tested, traceable to an immutable source commit and artifact, and deployed only through approved CI/CD pathways. |
| Activity | Daily automated full-population correlation of production deployments, CI/CD evidence, artifact provenance, and production control-plane changes; exceptions receive individual human-owned cases. |
| Frequency | Daily |
| Type | Automated detective ITGC with human corrective action |
| Nature | Full-population, two-direction reconciliation; no sampling |
| Evidence | Source manifest, validated extracts, assertion ledger, exception log, individual cases, workflow run, repository commit |
| Owner | Control owner in `config.yaml` |
| Systems | Fictional GitHub Actions, AWS, GitLab CI, Kubernetes, and OCI registries |

## Control activity

For each review window, the control obtains the complete population of
production deployments and the complete population of production cloud-side
mutations. It validates source provenance before processing. For every
deployment, it verifies timely independent approval, successful pre-deployment
testing, governed commit provenance, immutable artifact lineage, and a matching
cloud execution event. It then tests every cloud mutation in reverse to detect
changes with no CI/CD deployment. Exceptions are assigned stable IDs and routed
individually for human investigation, disposition, and closure approval.

## Assertion-to-evidence mapping

| Rule | Source evidence | Join | Failure condition |
|---|---|---|---|
| CM01 | Environment or merge approval | Deployment ID | Missing/rejected, self-approved, or after deployment |
| CM02 | Workflow check or pipeline test | Run ID | Missing, non-passing, or after deployment |
| CM03 | Commit and protection metadata | Commit SHA | Missing, unprotected, or signature unverified |
| CM04 | Registry/build provenance | Run ID + digest + commit SHA | Any mismatch or missing lineage |
| CM05 | CloudTrail/Kubernetes mutation | Run ID | Deployment has no cloud execution record |
| CM06 | Deployment population | Cloud event run ID | Cloud mutation has no in-scope deployment |

## IPE completeness and accuracy

Completeness is supported through API-query documentation, common period
boundaries, source row counts, unique keys, and two primary populations that are
reconciled in both directions. Accuracy is supported through explicit schemas,
SHA-256 checks, deterministic comparisons, named rules, and automated tests.
The evaluator fails closed before forming a control conclusion if a source does
not satisfy the manifest.

In production, the process owner must independently validate that each source
query covers every relevant repository, AWS account/region, Kubernetes cluster,
namespace, deployment method, and mutation event type. Hashing an incomplete
extract proves integrity, not completeness; query governance supplies the
complementary completeness assertion.

## Change management over this control

The evaluator is itself change-managed. `CODEOWNERS` marks configuration,
detection logic, integrity checks, and workflows for control-owner review.
Repository settings should require pull requests, passing CI, code-owner
approval, conversation resolution, and no force pushes to `main`. Version
history plus the retained commit SHA identifies what logic operated each run.

## Framework alignment

The design aligns conceptually with COSO Principle 11, COBIT BAI06 and DSS01,
NIST SP 800-53 CM-3/CM-5/CM-6/AU-12/CA-7, and ISO/IEC 27001:2022 controls 8.9,
8.25, 8.31, and 8.32. Organization-specific mapping and regulatory scoping must
be approved by the responsible compliance function.

## Seeded exceptions

The sample period contains seven expected findings so reviewers can observe the
end-to-end case contract:

- rejected GitHub/AWS approval;
- failed GitHub Actions test;
- GitHub/AWS artifact-digest mismatch;
- GitLab/Kubernetes self-approval;
- GitLab commit without protected-branch or verified-signature evidence;
- one out-of-band AWS IAM policy change; and
- one out-of-band Kubernetes ConfigMap change.

These make the monitoring workflow red by design. CI remains green because it
tests code health, not whether the fictional exception population is clean.

