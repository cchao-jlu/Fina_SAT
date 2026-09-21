from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_reference_artifacts(
    *,
    root: Path,
    artifacts: Sequence[Path],
    output_path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    root = Path(root).resolve()
    rows = []
    for artifact in sorted((Path(path).resolve() for path in artifacts), key=str):
        if not artifact.is_file():
            raise FileNotFoundError(artifact)
        rows.append(
            {
                "path": str(artifact.relative_to(root)),
                "size_bytes": artifact.stat().st_size,
                "sha256": sha256_file(artifact),
            }
        )
    payload = {**metadata, "artifacts": rows}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
