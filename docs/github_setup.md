# GitHub setup

After downloading/unzipping the repository:

```bash
cd market-information-dynamics
git init
git add .
git commit -m "Initial research release"
git branch -M main
```

Create an empty public GitHub repository named `market-information-dynamics`, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/market-information-dynamics.git
git push -u origin main
```

Do not commit API keys or downloaded data whose licence does not permit redistribution.
If you choose to use a FRED API key, keep `FRED_API_KEY` in your local environment rather than the repository. The default public-data path can run without committing credentials.
