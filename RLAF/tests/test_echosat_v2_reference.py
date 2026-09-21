import json
from pathlib import Path

from src.echosat.reference import freeze_reference_artifacts, sha256_file


def test_sha256_file_is_content_stable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("echo-sat\n", encoding="utf-8")
    first = sha256_file(artifact)
    second = sha256_file(artifact)
    artifact.write_text("echo-sat changed\n", encoding="utf-8")
    changed = sha256_file(artifact)

    assert first == second
    assert first == "460b49d57c8dd4faacb81e1d670016578617e26c6076c4aa245e79458165138c"
    assert changed != first


def test_freeze_reference_artifacts_records_relative_paths_and_hashes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    checkpoint = root / "runs" / "model.pt"
    manifest = root / "runs" / "manifest.csv"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    manifest.write_text("base_instance_id\nbase-a\n", encoding="utf-8")

    output = root / "runs" / "analysis" / "echosat_v2_reference" / "reference.json"
    payload = freeze_reference_artifacts(
        root=root,
        artifacts=[checkpoint, manifest],
        output_path=output,
        metadata={"reference_checkpoint": "v1.2-iter15"},
    )

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert payload == saved
    assert saved["reference_checkpoint"] == "v1.2-iter15"
    assert [row["path"] for row in saved["artifacts"]] == [
        "runs/manifest.csv",
        "runs/model.pt",
    ]
    assert [row["size_bytes"] for row in saved["artifacts"]] == [24, 10]
    assert all(len(row["sha256"]) == 64 for row in saved["artifacts"])
