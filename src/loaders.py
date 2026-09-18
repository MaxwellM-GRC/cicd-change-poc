"""Load the normalized fictional CI/CD and cloud-audit fixtures."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .models import CloudChange, Deployment


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_sources(config: dict, root: Path) -> tuple[list[Deployment], list[CloudChange], dict]:
    deployments: list[Deployment] = []
    cloud_changes: list[CloudChange] = []
    evidence: dict = defaultdict(lambda: defaultdict(list))
    for source in config["sources"]:
        rows = _read(root / source["path"])
        platform, kind = source["platform"], source["kind"]
        if kind == "deployments":
            deployments.extend(
                Deployment(platform=platform, **row) for row in rows
                if row["environment"].lower() == "production"
            )
        elif kind == "cloud_changes":
            cloud_changes.extend(CloudChange(platform=platform, **row) for row in rows)
        else:
            evidence[platform][kind].extend(rows)
    return deployments, cloud_changes, evidence


