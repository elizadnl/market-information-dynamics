#!/usr/bin/env bash
set -euo pipefail

python -m pip install -e '.[dev]'
python scripts/build_native.py || echo 'Native build unavailable; using Python backend.'
python -m market_information_dynamics.cli public-research \
  --start 2019-01-01 \
  --financial-config configs/universe_v1.yaml \
  --portwatch-config configs/portwatch_v1.yaml \
  --experiment-config configs/empirical_v1.yaml \
  --data-out data/processed/public_pilot.csv \
  --out artifacts/empirical_v1

echo 'Done. Open artifacts/empirical_v1/RESULTS.md'
