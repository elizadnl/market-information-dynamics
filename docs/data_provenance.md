# Data provenance and admissibility

A public URL is not enough to make a series admissible for a quantitative backtest. Every
node is classified by what can actually be reconstructed about its historical information
set.

| class | meaning | use |
|---|---|---|
| **A — vintage exact** | historical release/vintage timestamps can be reconstructed | eligible for strongest OOS claims |
| **B — timestamped** | observation and publication timing are known, but revisions/vintages are incomplete | eligible with documented caveats |
| **C — lag modelled** | current history is public, but historical availability must be approximated with a conservative lag | exploratory / sensitivity analysis |
| **D — current-history only** | historical availability cannot be defended | descriptive only |

## FRED / ALFRED

FRED is used for daily market/financial series. The client prefers the official JSON API
when a key is present and otherwise uses FRED's public `fredgraph.csv` endpoint. The repo
stores series identifiers and transformations, not redistributed raw market histories.

For future macroeconomic variables, the stronger intended implementation is ALFRED/vintage
metadata rather than revised historical values.

## IMF PortWatch

The physical layer uses IMF PortWatch's public ArcGIS `Daily_Chokepoints_Data` table. The
live service currently exposes daily `date`, `portid`, `portname`, vessel-count fields
(`n_container`, `n_dry_bulk`, `n_tanker`, `n_total`, etc.) and capacity fields. Its ArcGIS
service reports a 1,000-record maximum, so the adapter paginates explicitly.

Public documentation used to validate the interface:

- World Bank Development Data Partnership tutorial, **Maritime Port Activity**:
  https://worldbank.github.io/alternative-data-for-crisis/notebooks/disruptions-business-trade/maritime-port-activity.html
- ArcGIS layer metadata:
  https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0

### Historical availability limitation

The live PortWatch history does **not** by itself reconstruct every historical publication
vintage. The first pilot therefore assigns PortWatch **Class C** and uses a pre-specified
10-calendar-day availability lag with complete 7/14/21-day sensitivity runs.

That limitation is deliberate and visible in the code. Treating today's populated
historical PortWatch panel as if every row had been available on its observation date would
be look-ahead bias.

## Repository policy

`data/raw/`, `data/interim/` and `data/processed/` are git-ignored. Reproducibility comes
from source identifiers, acquisition code, configs and derived evidence tables/figures—not
from committing third-party raw datasets whose redistribution terms may differ by source.
