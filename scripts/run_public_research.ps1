$ErrorActionPreference = "Stop"

Write-Host "Installing Market Information Dynamics in editable mode..."
python -m pip install -e ".[dev]"

Write-Host "Attempting optional native C++ build..."
try {
    python scripts/build_native.py
} catch {
    Write-Warning "Native build unavailable; continuing with the tested Python backend."
}

Write-Host "Running public empirical v1..."
python -m market_information_dynamics.cli public-research `
    --start 2019-01-01 `
    --financial-config configs/universe_v1.yaml `
    --portwatch-config configs/portwatch_v1.yaml `
    --experiment-config configs/empirical_v1.yaml `
    --data-out data/processed/public_pilot.csv `
    --out artifacts/empirical_v1

Write-Host "Done. Open artifacts/empirical_v1/RESULTS.md"
