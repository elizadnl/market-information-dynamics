# Windows quick start — v0.6

Run these commands from the repository root.

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

If `data/processed/public_pilot.csv` already exists from v1/v2, do **not** redownload PortWatch.
Run the new candidate-overlay experiment directly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_candidate_overlay.ps1
```

The result will be written to:

```text
artifacts\empirical_v3\
```

To zip the evidence pack into Downloads:

```powershell
Compress-Archive -Path artifacts\empirical_v3\* -DestinationPath "$HOME\Downloads\empirical_v3_results.zip" -Force
```

Controlled synthetic demonstration:

```powershell
python -m market_information_dynamics.cli overlay-demo --out artifacts
```
