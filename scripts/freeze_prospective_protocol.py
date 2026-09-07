from __future__ import annotations

import hashlib
import json
from pathlib import Path

FILES = [
    "configs/empirical_v3.yaml",
    "configs/empirical_v4.yaml",
    "src/market_information_dynamics/evaluation/candidate_overlay.py",
    "src/market_information_dynamics/evaluation/empirical_v4.py",
    "src/market_information_dynamics/online/fixed_share.py",
    "docs/prospective_protocol.md",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


root = Path(__file__).resolve().parents[1]
manifest = {
    "frozen_on": "2026-08-28",
    "prospective_start": "2026-09-01",
    "files": {name: sha256(root / name) for name in FILES},
}
output = root / "docs" / "prospective_manifest.json"
output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(output)
