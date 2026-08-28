# Start here on Windows — v0.5

## If you already have the clean v0.4 Git repository

Do **not** create another GitHub repository. Keep your existing `.git` history and your
`data/processed/` + `data/cache/` directories.

1. Extract the v0.5 ZIP somewhere separate, for example:
   `C:\Users\<you>\Downloads\market-information-dynamics-v0.5`.
2. Copy the release files over the existing repository while leaving `.git`, local data,
   caches and virtual environments alone. The easiest robust command is `robocopy`:

```powershell
robocopy "$HOME\Downloads\market-information-dynamics-v0.5" `
         "$HOME\Downloads\market-information-dynamics-clean-v0.4" `
         /E /XD .git data .venv build __pycache__ .pytest_cache
```

Adjust only the destination if your existing repository folder has a different name.
`robocopy` exit codes 0–7 are normal/success states.

3. Enter the existing repository and reinstall/test:

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

4. Commit the release:

```powershell
git add .
git commit -m "Add predictive edge survival research"
git push
```

## Run empirical v2

If empirical v1 already created `data/processed/public_pilot.csv`, v2 reuses it and does not
redownload the public data:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_signal_survival.ps1
```

Or directly:

```powershell
python -m market_information_dynamics.cli empirical-v2 `
  --panel data/processed/public_pilot.csv `
  --financial-config configs/universe_v1.yaml `
  --experiment-config configs/empirical_v2.yaml `
  --out artifacts/empirical_v2
```

The multi-horizon walk-forward run is materially heavier than empirical v1. Let it finish;
do not interrupt simply because there is no terminal output for a while.

## If this is a completely fresh clone

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
python -m market_information_dynamics.cli public-pilot --start 2019-01-01
powershell -ExecutionPolicy Bypass -File scripts\run_signal_survival.ps1
```
