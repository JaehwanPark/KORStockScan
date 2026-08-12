# Four-profile two-leg episode policy research — 2026-08-11

Clean-baseline integrated-SOR regular-session evidence covers 47 KRX trading
dates from 2026-06-05 through 2026-08-11. The first 31 dates selected policy
candidates and the latest 16 dates were used only as the final holdout gate.

The execution stress requires the completed one-minute low to penetrate a buy
limit by one tick and a strictly later completed-bar high to penetrate the
target by one tick. Same-bar fill and target completion are forbidden. EV is
notional weighted after a 0.20% round-trip cost. An unfilled target is `HELD`;
there is no stop loss or forced exit.

| Profile | Window | L/DD/NL | Entry offsets | Valid | Target | Holdout episodes | Complete/attempt | Held | Holdout EV |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `mirae_asset_morning` | 09:35–09:44 | 15/1.75/0.50 | -1/-2 | 5 | +4 | 4 | 4/8 | 0 | +0.195075% |
| `jeju_semiconductor_morning` | 09:10–09:49 | 20/2.50/0.10 | 0/-1 | 3 | +4 | 6 | 8/12 | 0 | +0.264243% |
| `doosan_enerbility_morning` | 09:20–09:49 | 15/2.00/0.50 | 0/-1 | 5 | +4 | 5 | 10/10 | 0 | +0.375457% |
| `hanwha_ocean_late_morning` | 10:05–10:24 | 20/1.25/0.10 | 0/-1 | 5 | +4 | 5 | 9/10 | 0 | +0.235306% |

The report itself is source-only evidence. It does not create a machine,
service, authority artifact, or broker order. Live authority requires the
separate immutable profile, exact-date applied policy, same-day preflight, and
explicit confirmation contracts.
