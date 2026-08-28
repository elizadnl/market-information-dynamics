# Windows quick start — v0.7

Run these commands from the repository root.

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

If `artifacts/empirical_v3/` already exists, v4 needs **no data download and no model refit**.
It only performs causal online aggregation of the frozen v3 forecast experts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_online_aggregation.ps1
```

Outputs:

```text
artifacts\empirical_v4\
```

Zip them to Downloads with:

```powershell
Compress-Archive -Path artifacts\empirical_v4\* -DestinationPath "$HOME\Downloads\empirical_v4_results.zip" -Force
```

Controlled regime-switch demonstration:

```powershell
python -m market_information_dynamics.cli online-demo --out artifacts
```

The statistical protocol for September-2026 onward is frozen in
`docs/prospective_protocol.md`.
