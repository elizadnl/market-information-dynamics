$ErrorActionPreference = "Stop"

$panel = "data/processed/public_pilot.csv"
if (-not (Test-Path $panel)) {
    Write-Host "No existing public panel found. Building it from public FRED + PortWatch sources..."
    python -m market_information_dynamics.cli public-pilot --start 2019-01-01 --out $panel
}

python -m market_information_dynamics.cli empirical-v2 `
    --panel $panel `
    --financial-config configs/universe_v1.yaml `
    --experiment-config configs/empirical_v2.yaml `
    --out artifacts/empirical_v2
