# Start here on Windows

This release is designed to be used as a **fresh repository**. Do not apply old patch files to it.

## 1. Extract once

Extract the ZIP so that the folder you open directly contains `README.md`, `pyproject.toml`, `src/`, `tests/`, and `configs/`.

## 2. Test locally

Open PowerShell in that folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

## 3. Create a new empty GitHub repository

Create a public repo. Do not add a README, `.gitignore`, or licence on GitHub because they are already included here.

## 4. Push the whole folder

```powershell
git init
git add .
git commit -m "Initial clean research release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/market-information-dynamics.git
git push -u origin main
```

## 5. Run the public-data study

```powershell
python -m market_information_dynamics.cli public-research --start 2019-01-01
```

PortWatch is downloaded in small yearly chunks and cached under `data/cache/portwatch`. If ArcGIS times out halfway through, rerun the same command: completed chunks are reused instead of downloaded again.
