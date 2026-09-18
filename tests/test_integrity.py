import json
from pathlib import Path

import yaml

from src.integrity import validate_sources


ROOT = Path(__file__).resolve().parents[1]


def test_all_fictional_sources_match_retained_manifest():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    statuses = validate_sources(config, ROOT, ROOT / "data/source_manifest.json")
    assert len(statuses) == len(config["sources"])
    assert all(source.ok for source in statuses)
    assert sum(s.actual_rows for s in statuses if s.kind == "deployments") == 6
    assert sum(s.actual_rows for s in statuses if s.kind == "cloud_changes") == 8


def test_tampered_source_fails_closed(tmp_path):
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    config["sources"] = [dict(config["sources"][0])]
    fixture = tmp_path / "deployments.csv"
    fixture.write_text((ROOT / config["sources"][0]["path"]).read_text() + "tampered")
    config["sources"][0]["path"] = fixture.name
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
    manifest["sources"] = [manifest["sources"][0]]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    statuses = validate_sources(config, tmp_path, manifest_path)
    assert not statuses[0].ok
    assert "manifest SHA-256 does not match source" in statuses[0].errors


