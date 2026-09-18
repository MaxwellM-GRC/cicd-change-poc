"""Normalized records and RCM ready control result structures."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256


@dataclass(frozen=True)
class Deployment:
    platform: str
    deployment_id: str
    environment: str
    deployed_at: str
    commit_sha: str
    artifact_digest: str
    run_id: str
    actor: str


@dataclass(frozen=True)
class CloudChange:
    platform: str
    event_id: str
    changed_at: str
    resource: str
    action: str
    actor: str
    run_id: str
    artifact_digest: str


@dataclass(frozen=True)
class Finding:
    control_id: str
    rule: str
    severity: str
    platform: str
    object_type: str
    object_id: str
    deployment_id: str
    detail: str
    remediation: str
    lookback: str
    root_cause: str
    closure_evidence: str

    @property
    def finding_id(self) -> str:
        seed = "|".join(
            [self.control_id, self.rule, self.platform, self.object_type, self.object_id]
        )
        return f"CM-{sha256(seed.encode()).hexdigest()[:16]}"

    def as_dict(self) -> dict:
        return {"finding_id": self.finding_id, **asdict(self)}


@dataclass
class SourceStatus:
    source_id: str
    platform: str
    kind: str
    path: str
    source_uri: str = ""
    query: str = ""
    extracted_at: str = ""
    window_start: str = ""
    window_end: str = ""
    expected_rows: int = 0
    actual_rows: int = 0
    expected_sha256: str = ""
    actual_sha256: str = ""
    missing_columns: list[str] = field(default_factory=list)
    duplicate_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_columns and not self.duplicate_keys and not self.errors

    def as_dict(self) -> dict:
        result = asdict(self)
        result["ok"] = self.ok
        return result


@dataclass
class ReviewResult:
    run_id: str
    findings: list[Finding]
    evaluations: list[dict]
    source_status: list[SourceStatus]
    deployment_count: int
    cloud_change_count: int
    matched_cloud_changes: int

    @property
    def input_valid(self) -> bool:
        return all(source.ok for source in self.source_status)

    @property
    def population_reconciled(self) -> bool:
        evaluated_ids = {row["deployment_id"] for row in self.evaluations}
        return len(evaluated_ids) == self.deployment_count

