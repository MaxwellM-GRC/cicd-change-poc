# RCM and Control Narrative

## RCM entry

| Attribute | Definition |
|---|---|
| Control ID | `ITGC-CM-01` |
| Risk | Unauthorized, untested, or untraceable production changes could compromise financial-system processing, security, or availability. |
| Objective | Production changes are authorized, tested, traceable to an immutable source commit and artifact, and deployed only through approved CI/CD pathways. |
| Activity | Daily automated full population correlation of production deployments, CI/CD evidence, artifact provenance, and production control plane changes; exceptions receive individual human owned cases. |
| Frequency | Daily |
| Type | Automated detective ITGC with human corrective action |
| Nature | Full population, two-direction reconciliation; no sampling |
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
| CM-01 | Pull or merge request evidence | Deployment ID | No approved pull or merge request |
| CM-02 | Merge review evidence | Pull or merge request ID | No timely independent review |
| CM-03 | Workflow or pipeline test | Run ID | Missing, non-passing, or late test |
| CM-04 | Approved merge SHA | Deployment ID + commit SHA | Deployed SHA differs from approved SHA |
| CM-05 | Authorized pipeline record | Deployment ID | Unapproved pipeline or manual path |
| CM-06 | Production environment approval | Deployment ID | Missing, rejected, or late approval |
| CM-07 | Author and approver evidence | Deployment ID | Developer approved their own change |
| CM-08 | Deployment identity authorization | Deployment ID | Identity is unauthorized for production |
| CM-09 | Emergency-change review | Deployment ID | No timely retrospective review |
| CM-10 | Pipeline/control-definition change record | Change ID | No heightened review evidence |
| CM-11 | CloudTrail/Kubernetes audit event | Cloud event run ID | Cloud mutation has no in-scope deployment |
| CM-12 | Registry/build provenance | Run ID + digest + commit SHA | Any missing or mismatched lineage |
| CM-13 | Branch/environment protection snapshot | Platform | Required protection is disabled |
| CM-14 | Deployment outcome and incident record | Deployment ID | Failed or rolled-back change lacks resolution |

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
detection logic, integrity checks, and workflows for control owner review.
Repository settings should require pull requests, passing CI, code-owner
approval, conversation resolution, and no force pushes to `main`. Version
history plus the retained commit SHA identifies what logic operated each run.

## Framework alignment

The design aligns conceptually with COSO Principle 11, COBIT BAI06 and DSS01,
NIST SP 800-53 CM-3/CM-5/CM-6/AU-12/CA-7, and ISO/IEC 27001:2022 controls 8.9,
8.25, 8.31, and 8.32. Organization-specific mapping and regulatory scoping must
be approved by the responsible compliance function.

## Seeded exceptions

The sample period contains fourteen expected findings so reviewers can observe
the end-to-end case contract across every control:

- unapproved pull request, mismatched approved SHA, and rejected AWS approval;
- failed CI test, emergency deployment without retrospective review, artifact mismatch, and unresolved rollback;
- unauthorized GitLab pipeline, self-approval, self-review, and unauthorized deployment identity;
- pipeline-definition change without heightened review and missing protection; and
- one out-of-band AWS IAM policy change.

These make the monitoring workflow red by design. CI remains green because it
tests code health, not whether the fictional exception population is clean.
