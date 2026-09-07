$ErrorActionPreference = "Stop"

Write-Host "Setting up Market Information Dynamics..."
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
Write-Host "Setup complete."
Write-Host "Run the public study with:"
Write-Host "python -m market_information_dynamics.cli public-research --start 2019-01-01"
