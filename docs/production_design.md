# Production Design and Limitations

## Collector boundary

Replace CSV fixtures with least-privilege collectors that write immutable raw
responses and a manifest. GitHub and GitLab collectors should enumerate every
in-scope project and production environment. AWS collection should cover every
in-scope account and region and preserve CloudTrail event IDs. Kubernetes audit
collection should cover every production cluster and namespace, including
controller-driven mutations. Registry evidence should use immutable digest and
attestation APIs rather than mutable tags.

Collectors and the evaluator should run under different identities. Neither
should hold production write permission. Store evidence in a write-once bucket
with retention, encryption, access logging, and legal-hold behavior aligned to
the audit policy.

## Completeness controls

Production design should add:

- an authoritative inventory of repositories, accounts, regions, clusters, and namespaces;
- count reconciliation to source-native totals or independently generated reports;
- pagination and throttling checks with explicit failure on partial API responses;
- clock normalization and late-arriving-event handling;
- explicit allowlists for mutation types and service/controller identities;
- collector health, extract freshness, and zero-row plausibility alerts; and
- cross-account and cross-cluster duplicate detection.

## Organization-specific semantics

Approval rules often vary by risk class, emergency status, service, or change
type. Required tests may be a policy set rather than one aggregate conclusion.
Commit verification might use signed commits, protected tags, merge-train
evidence, or SLSA attestations. Adapt `config.yaml` and the evidence model only
through the repository's governed change process.

Emergency changes should not be silently excluded. Identify them in the
complete population and test their distinct authorization, retrospective
review, and time bound follow up requirements.

## Remediation safety

Detection does not authorize action. A production implementation may create a
ticket, notify an owner, and propose a rollback or policy correction. A human
with appropriate authority must evaluate business impact, approve the action,
and approve case closure. Automated production mutation is intentionally out of
scope for this repository.

## Known POC limitations

- Static fictional CSVs stand in for APIs and audit stores.
- ISO timestamp strings are directly comparable because every fixture uses UTC
  and the same canonical format; production should parse timezone-aware values.
- One aggregate test result represents the required test policy.
- The POC reconciles cloud activity using run ID, artifact digest, deployment
  identity, and a configured time window; production should additionally use
  signed deployment attestations and resource-specific correlation.
- GitHub repository settings such as branch protection are operational setup,
  not enforceable from source files alone.
