# GitHub setup

After downloading/unzipping the repository:

```bash
cd market-information-dynamics
git init
git add .
git commit -m "Initial research engine"
git branch -M main
```

Create an empty public GitHub repository named `market-information-dynamics`, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/market-information-dynamics.git
git push -u origin main
```

Do not commit API keys or downloaded data whose licence does not permit redistribution.
`FRED_API_KEY` belongs in your local environment, not in the repository.
