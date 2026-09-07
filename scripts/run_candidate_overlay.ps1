$ErrorActionPreference = "Stop"
python -m market_information_dynamics.cli empirical-v3 `
  --panel data/processed/public_pilot.csv `
  --financial-config configs/universe_v1.yaml `
  --experiment-config configs/empirical_v3.yaml `
  --out artifacts/empirical_v3
