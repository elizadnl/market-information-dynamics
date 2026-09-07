# Data design

## Planned node families

### Financial
- Broad equity index / liquid ETF returns
- FX returns
- Commodity prices/futures proxies
- Rates / yield changes
- Volatility / risk indicators

### Physical economy
- Public maritime trade / port activity exports
- Public energy production / inventory series
- Selected trade or industrial-flow indicators

### Macro state (lower frequency)
- Industrial production
- Inflation / producer prices
- Trade

Macro variables are point-in-time features, not silently backfilled revised histories.

## Canonical long-form schema

| column | meaning |
|---|---|
| `observation_time` | economic/market timestamp represented by the value |
| `available_at` | earliest time the value could have been known |
| `feature` | stable feature identifier |
| `value` | numeric observation |
| `source` | public source name |
| `frequency` | original observation frequency |
| `transform` | transformation applied downstream |

## Transformations

Financial prices are generally converted to returns/changes before multivariate modelling.
Physical series require explicit seasonal adjustment or year-on-year/rolling anomaly
features. Transform parameters must be fitted inside each training window where fitting is
required.
