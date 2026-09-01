# Lower-price two-leg live machines

## Scope

Forty-five independent regular-session profiles implement the user-selected active
scope. Every profile owns its process, lock, durable state,
authority artifact, and exact broker-order ledger.

| Profile | Symbol | Session | Scan bars |
|---|---|---|---|
| `samsung_heavy_midday` | 삼성중공업 `010140` | SOR regular | 13:20 through 13:29 |
| `samsung_heavy_afternoon` | 삼성중공업 `010140` | SOR regular | 14:00 through 14:40 |
| `sk_eternix_midday` | SK이터닉스 `475150` | SOR regular | 13:30 through 13:39 |
| `mirae_asset_morning` | 미래에셋증권 `006800` | SOR regular | 09:35 through 09:44 |
| `jeju_semiconductor_morning` | 제주반도체 `080220` | SOR regular | 09:10 through 09:49 |
| `doosan_enerbility_morning` | 두산에너빌리티 `034020` | SOR regular | 09:20 through 09:49 |
| `hanwha_ocean_late_morning` | 한화오션 `042660` | SOR regular | 10:05 through 10:24 |
| `kakao_morning` | 카카오 `035720` | SOR regular | 09:20 through 09:39 |
| `kakao_late_morning` | 카카오 `035720` | SOR regular | 10:05 through 10:24 |
| `sk_eternix_morning` | SK이터닉스 `475150` | SOR regular | 09:50 through 09:59 |
| `mirae_asset_midday` | 미래에셋증권 `006800` | SOR regular | 13:15 through 13:24 |
| `kepco_afternoon` | 한국전력 `015760` | SOR regular | 14:00 through 14:29 |
| `sk_eternix_afternoon` | SK이터닉스 `475150` | SOR regular | 14:15 through 14:40 |
| `samsung_heavy_morning` | 삼성중공업 `010140` | SOR regular | 09:20 through 09:29 |
| `doosan_enerbility_late_morning` | 두산에너빌리티 `034020` | SOR regular | 10:15 through 10:34 |
| `kakao_midday` | 카카오 `035720` | SOR regular | 13:20 through 13:39 |
| `sk_telecom_afternoon` | SK텔레콤 `017670` | SOR regular | 14:25 through 14:34 |
| `samsung_ea_morning` | 삼성E&A `028050` | SOR regular | 09:45 through 09:59 |
| `samsung_ea_late_morning` | 삼성E&A `028050` | SOR regular | 10:05 through 10:14 |
| `samsung_ea_afternoon` | 삼성E&A `028050` | SOR regular | 14:05 through 14:34 |
| `sk_telecom_late_morning` | SK텔레콤 `017670` | SOR regular | 10:45 through 10:54 |
| `hanse_morning` | 한세실업 `105630` | SOR regular | 09:15 through 09:44 |
| `hanse_afternoon` | 한세실업 `105630` | SOR regular | 14:20 through 14:29 |
| `cj_cgv_midday` | CJ CGV `079160` | SOR regular | 13:20 through 13:49 |
| `cj_cgv_afternoon` | CJ CGV `079160` | SOR regular | 14:15 through 14:24 |
| `tym_midday` | TYM `002900` | SOR regular | 13:15 through 13:44 |
| `tym_afternoon` | TYM `002900` | SOR regular | 14:30 through 14:39 |
| `cj_cgv_late_morning` | CJ CGV `079160` | SOR regular | 10:00 through 10:09 |
| `kepco_late_morning` | 한국전력 `015760` | SOR regular | 10:00 through 10:59 |
| `kepco_midday` | 한국전력 `015760` | SOR regular | 13:30 through 13:49 |
| `hanse_late_morning` | 한세실업 `105630` | SOR regular | 10:00 through 10:19 |
| `hanse_midday` | 한세실업 `105630` | SOR regular | 13:20 through 13:49 |
| `nhn_afternoon` | NHN `181710` | SOR regular | 14:00 through 14:40 |
| `youngone_morning` | 영원무역 `111770` | SOR regular | 09:20 through 09:39 |
| `youngone_afternoon` | 영원무역 `111770` | SOR regular | 14:30 through 14:40 |
| `sk_eternix_late_morning` | SK이터닉스 `475150` | SOR regular | 10:45 through 10:54 |
| `mirae_asset_late_morning` | 미래에셋증권 `006800` | SOR regular | 10:00 through 10:29 |
| `kepco_morning` | 한국전력 `015760` | SOR regular | 09:35 through 09:59 |
| `nhn_morning` | NHN `181710` | SOR regular | 09:40 through 09:49 |
| `nhn_late_morning` | NHN `181710` | SOR regular | 10:30 through 10:49 |
| `sd_biosensor_morning` | 에스디바이오센서 `137310` | SOR regular | 09:30 through 09:49 |
| `sd_biosensor_late_morning` | 에스디바이오센서 `137310` | SOR regular | 10:40 through 10:59 |
| `sd_biosensor_midday` | 에스디바이오센서 `137310` | SOR regular | 13:25 through 13:54 |
| `doosan_enerbility_afternoon` | 두산에너빌리티 `034020` | SOR regular | 14:10 through 14:29 |
| `samsung_ea_midday` | 삼성E&A `028050` | SOR regular | 13:20 through 13:49 |

The original 30-day calibration and 16-day untouched holdout selected independent entry
contracts: Samsung Heavy midday uses 30 bars, drawdown at least 0.75%, and
near-low at most 0.35%; Samsung Heavy afternoon keeps 30 bars, 1.25%, and
0.20%. The former SK Eternix midday 20-bar/2.00%/0.75% contract is historical
through 2026-08-18. From the explicit
2026-08-13 operator quantity change, one signal creates exactly two independent
10-share limit buys: one at the signal close and one at one tick below (maximum
20 shares). Entry orders remain valid for five subsequently completed one-minute
bars. A partial buy fill cancels only the remaining quantity of that exact owned
order; after cancellation reconciliation, the confirmed filled quantity owns one
same-quantity limit target at that profile generation's frozen tick distance. There is no
stop loss, target timeout, forced sale, or target cancellation; an unclosed
position remains held.

The operator-approved
`WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2` applies to all
profiles without changing their signal, quantity, target, or no-stop holding
contracts. A current-session `active|release_pending` latch blocks PLANNED BUY
submission only for the profile's verified listing market. For an already open
BUY leg, the machine cancels only after the current-day original order number is
present in that profile's owned-order ledger and the broker snapshot confirms a
positive remaining quantity in the same cycle. Partial fills remain owned and
receive their normal target after cancellation reconciliation. Missing market
scope, stale/unavailable reconciliation, another profile/widget/main/manual
order, SELL/target orders, and existing holdings are outside this authority.

The four 2026-08-12 additions use the full clean-baseline 47-date window with
31 calibration dates and the latest 16 dates as holdout. Their conservative
execution proxy requires one-tick penetration beyond both entry and target:

| Profile | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---:|---:|---:|---|---:|---:|
| `mirae_asset_morning` | 15 | 1.75% | 0.50% | -1/-2 ticks | 5 | +4 ticks |
| `jeju_semiconductor_morning` | 20 | 2.50% | 0.10% | close/-1 tick | 3 | +4 ticks |
| `doosan_enerbility_morning` | 15 | 2.00% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `hanwha_ocean_late_morning` | 20 | 1.25% | 0.10% | close/-1 tick | 5 | +4 ticks |

The six 2026-08-12 postclose selections use all 48 clean-baseline trading
dates, split into 32 calibration dates and the latest 16 untouched holdout
dates. They are exactly the three new-symbol and three existing-symbol
time-extension rows shown in the admin Telegram notice, rather than every
hidden report recommendation:

Their deployable preflight input is the tracked
`data/config/low_price_two_leg_expanded_profile_evidence_2026-08-12.json`
projection. It binds the original v5 report canonical SHA, the exact six
recommendation rows, both calibration halves, holdout/full metrics, and the
user-approved scope. The ignored 3.7MB runtime report is audit/source evidence,
not a deployment dependency.

| Profile | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---:|---:|---:|---|---:|---:|
| `kakao_morning` | 15 | 0.75% | 0.35% | close/-1 tick | 5 | +3 ticks from 2026-08-14 |
| `kepco_afternoon` | 60 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `kakao_late_morning` | 15 | 0.50% | 0.35% | close/-1 tick | 5 | +2 ticks |
| `sk_eternix_morning` | 15 | 1.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `mirae_asset_midday` | 45 | 1.00% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `sk_eternix_afternoon` | 45 | 2.50% | 0.50% | close/-1 tick | 5 | +2 ticks |

Kakao morning kept its frozen-research +2-tick baseline for the 2026-08-13
execution record, then applies an explicit user-directed +3-tick target transition
from the 2026-08-14 through 2026-08-18 exact-date PREOPEN policies. The service consumes that applied
target instead of the compiled baseline, and the authority artifact records the
before/after value and effective date. At the observed 39,250/39,200 fills this
means independent targets of 39,400/39,350. It does not change Kakao late morning,
any other profile, entry criteria, 10-share-per-leg allocation, no-stop holding, or broker
guards. Postclose research includes +3 ticks as a source-only execution-plan option;
ordinary bounded entry tuning cannot change this operator-owned target axis.
The 2026-08-19 user-approved profile revision supersedes that historical target
with the new +4-tick baseline. It never cancels or replaces an already-owned
target order.

## 2026-08-18 recommendation implementation

The tracked
`data/config/low_price_two_leg_expanded_profile_evidence_2026-08-18.json`
projection binds the complete 51-trading-day clean-baseline report, its canonical
hash, all 14 passing recommendation rows, 35-day calibration, 16-day untouched
holdout, and the explicit user approval. The revision is effective only from the
2026-08-19 exact-date PREOPEN artifact. Applied artifacts through 2026-08-18 keep
the prior 13-profile inventory and policy generation.

Seven existing profiles replace their entry-generation baseline:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `mirae_asset_midday` | 13:15~13:24 | 45 | 1.00% | 0.20% | close/-1 tick | 5 | +4 ticks |
| `sk_eternix_morning` | 09:50~09:59 | 15 | 2.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `sk_eternix_midday` | 13:30~13:39 | 60 | 0.75% | 0.35% | close/-1 tick | 5 | +4 ticks |
| `doosan_enerbility_morning` | 09:20~09:49 | 15 | 1.75% | 0.20% | close/-1 tick | 5 | +4 ticks |
| `mirae_asset_morning` | 09:35~09:44 | 30 | 1.75% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `kakao_morning` | 09:20~09:39 | 15 | 0.75% | 0.35% | close/-1 tick | 5 | +4 ticks |
| `kakao_late_morning` | 10:05~10:24 | 20 | 0.50% | 0.05% | close/-1 tick | 5 | +4 ticks |

Seven new independent profiles use the following frozen rows:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `samsung_heavy_morning` | 09:20~09:29 | 20 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `doosan_enerbility_late_morning` | 10:15~10:59 | 30 | 1.75% | 0.05% | close/-1 tick | 5 | +2 ticks |
| `kakao_midday` | 13:20~13:39 | 30 | 0.50% | 0.35% | close/-1 tick | 5 | +2 ticks |
| `sk_telecom_afternoon` | 14:25~14:34 | 15 | 0.75% | 0.20% | close/-1 tick | 5 | +2 ticks |
| `samsung_ea_morning` | 09:45~09:59 | 15 | 1.25% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `samsung_ea_late_morning` | 10:05~10:14 | 20 | 1.50% | 0.20% | close/-1 tick | 5 | +2 ticks |
| `samsung_ea_afternoon` | 14:05~14:34 | 60 | 1.25% | 0.75% | close/-1 tick | 5 | +2 ticks |

The fixed Theborn Korea `475560` morning observation is not one of these 14
passing recommendations and remains source-only. Prior-date open or held orders
remain bound to the entry offsets and target ticks recorded when they were
created; the new generation cannot cancel, replace, or reinterpret them.

KEPCO afternoon had 16 completed holdout legs and two held legs (11.11% of
filled legs), with completed-only notional EV `+0.064355%` and held mark
`-1.297293%`. This is accepted only within the reviewed source-only carry
budget of at most 25% held/fill and at least `-3%` held mark. It does not add a
stop, timeout, forced sale, or unrealized PnL to completed EV.

## 2026-08-19 recommendation implementation

The tracked `data/config/low_price_two_leg_expanded_profile_evidence_2026-08-19.json`
projection binds the complete 52-trading-day report, 36-day calibration, 16-day
holdout, all 11 passing recommendations, and the source report canonical hash.
This reviewed generation is retained as the staged base for the combined
2026-08-21 generation. The later 2026-08-20 recommendation delta replaces only
its overlapping rows; 2026-08-20 services and prior-date owned orders keep their
original generation.

Eight existing profiles adopt these approved policies:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `doosan_enerbility_late_morning` | 10:15~10:34 | 45 | 1.50% | 0.05% | close/-1 tick | 5 | +4 ticks |
| `samsung_heavy_morning` | 09:20~09:29 | 20 | 1.75% | 0.75% | -1/-2 ticks | 5 | +4 ticks |
| `kakao_midday` | 13:20~13:39 | 15 | 0.50% | 0.20% | close/-1 tick | 5 | +4 ticks |
| `kakao_late_morning` | 10:05~10:24 | 15 | 0.50% | 0.05% | close/-1 tick | 5 | +4 ticks |
| `sk_telecom_afternoon` | 14:25~14:34 | 20 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `samsung_ea_morning` | 09:45~09:59 | 15 | 1.75% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `sk_eternix_afternoon` | 14:15~14:40 | 15 | 2.00% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `samsung_ea_afternoon` | 14:05~14:34 | 20 | 0.75% | 0.35% | close/-1 tick | 5 | +4 ticks |

Three new independent profiles are added:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `sk_telecom_late_morning` | 10:45~10:59 | 60 | 1.25% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `hanse_morning` | 09:15~09:44 | 15 | 0.75% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `hanse_afternoon` | 14:20~14:29 | 30 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |

The fixed Theborn Korea observation remains source-only. No recommendation
changes quantity, stop/hold behavior, SOR routing, broker guards, or another
owner's ledger.

## 2026-08-20 recommendation implementation

The tracked `data/config/low_price_two_leg_expanded_profile_evidence_2026-08-20.json`
projection binds the complete 53-trading-day report, 37-day calibration,
16-day holdout, the final nine recommendation rows, and the source report
canonical hash. It is a delta over the reviewed 2026-08-19 staged generation,
not a replacement for its non-overlapping profiles. The single exact-date
transition therefore moves the active 20-profile 2026-08-20 inventory to the
combined 27-profile generation on 2026-08-21.

Five existing rows are rebound to the latest evidence; Samsung E&A morning and
SK Telecom afternoon change values, while the other three retain the same
selected policy with fresher provenance:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `doosan_enerbility_late_morning` | 10:15~10:34 | 45 | 1.50% | 0.05% | close/-1 tick | 5 | +4 ticks |
| `samsung_heavy_morning` | 09:20~09:29 | 20 | 1.75% | 0.75% | -1/-2 ticks | 5 | +4 ticks |
| `samsung_ea_morning` | 09:45~09:59 | 15 | 2.00% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `kakao_late_morning` | 10:05~10:24 | 15 | 0.50% | 0.05% | close/-1 tick | 5 | +4 ticks |
| `sk_telecom_afternoon` | 14:25~14:34 | 15 | 0.75% | 0.50% | close/-1 tick | 5 | +4 ticks |

Four new independent profiles are added:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `cj_cgv_midday` | 13:20~13:49 | 60 | 0.75% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `cj_cgv_afternoon` | 14:15~14:24 | 20 | 0.50% | 0.35% | close/-1 tick | 5 | +2 ticks |
| `tym_midday` | 13:15~13:44 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `tym_afternoon` | 14:30~14:39 | 20 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |

The fixed Theborn Korea observation remains source-only. The four new timer
pairs and manual-owner exclusions are implemented but are not installed or
started by this source change. Existing open orders and held positions retain
their signal-date policy snapshot and custody owner.

The Doosan Enerbility and Hanwha Ocean episode profiles are parallel to their
widget auto-trading owners. Neither owner reads the other's state, position
quantity, or order numbers, and neither may cancel or sell the other's orders
or quantity. Both may independently submit orders for the same symbol.

## 2026-08-21 recommendation implementation

The tracked `data/config/low_price_two_leg_expanded_profile_evidence_2026-08-21.json`
projection binds the complete 54-trading-day clean baseline, 38-day calibration,
16-day holdout, all 14 final recommendations, and the source report canonical
hash. The exact-date transition preserves the 27-profile Friday generation and
selects the 35-profile generation only from 2026-08-24. Existing orders and held
positions retain their entry-date policy snapshot.

Six existing profiles adopt the reviewed logic improvements:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `cj_cgv_afternoon` | 14:15~14:24 | 30 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `kepco_afternoon` | 14:00~14:29 | 45 | 0.75% | 0.75% | close/-1 tick | 3 | +4 ticks |
| `tym_midday` | 13:15~13:44 | 20 | 0.50% | 0.35% | close/-1 tick | 5 | +4 ticks |
| `hanse_morning` | 09:15~09:44 | 15 | 0.75% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `samsung_ea_late_morning` | 10:05~10:14 | 45 | 1.00% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `hanse_afternoon` | 14:20~14:29 | 15 | 0.50% | 0.75% | -1/-2 ticks | 5 | +4 ticks |

Eight new independent profiles use the following frozen rows:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `cj_cgv_late_morning` | 10:00~10:09 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `kepco_late_morning` | 10:00~10:59 | 15 | 0.75% | 0.05% | close/-1 tick | 5 | +2 ticks |
| `kepco_midday` | 13:30~13:49 | 45 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `hanse_late_morning` | 10:00~10:59 | 30 | 0.75% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `hanse_midday` | 13:20~13:49 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `nhn_afternoon` | 14:00~14:40 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `youngone_morning` | 09:20~09:39 | 20 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `youngone_afternoon` | 14:30~14:40 | 30 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |

The fixed Theborn Korea observation and non-passing profiles remain source-only.
This source implementation adds timer definitions and ownership guards but does
not install, enable, or start a service.

## 2026-08-24 recommendation implementation

The tracked `data/config/low_price_two_leg_expanded_profile_evidence_2026-08-24.json`
is a compact immutable projection of the 55-trading-day clean-baseline report.
It binds the source report canonical hash, positive calibration halves, full and
holdout sample floors, all 12 final recommendations, and the explicit user
approval. The exact-date transition keeps the 35-profile generation through
2026-08-24 and selects the 40-profile generation only from 2026-08-25. Existing
orders and held positions remain bound to their original policy snapshot.

Seven existing profiles adopt the reviewed logic improvements:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `cj_cgv_late_morning` | 10:00~10:09 | 45 | 1.00% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `kepco_late_morning` | 10:00~10:59 | 20 | 0.75% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `nhn_afternoon` | 14:00~14:40 | 60 | 1.00% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `hanse_afternoon` | 14:20~14:29 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `youngone_afternoon` | 14:30~14:39 | 45 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `hanse_late_morning` | 10:00~10:59 | 20 | 0.75% | 0.35% | close/-1 tick | 5 | +4 ticks |
| `hanse_midday` | 13:20~13:49 | 45 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |

Five new independent profiles are added:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `sk_eternix_late_morning` | 10:45~10:54 | 15 | 1.50% | 0.20% | close/-1 tick | 5 | +2 ticks |
| `mirae_asset_late_morning` | 10:00~10:59 | 20 | 0.75% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `kepco_morning` | 09:35~09:59 | 15 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `nhn_morning` | 09:40~09:49 | 20 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `nhn_late_morning` | 10:30~10:49 | 30 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |

The implementation adds source definitions, wrappers, timers, manual-owner
coverage, exact-date policy lineage, and preflight evidence validation. Source
review alone does not activate the timers: installation is a separate operator
action through `deploy/install_low_price_two_leg_systemd.sh`, and each trading
service still requires its same-day preflight authority before it can start.
Quantity, no-stop custody, SOR routing, broker guards, provider, and another
machine's order ledger are unchanged.

## 2026-08-26 recommendation implementation

The tracked `data/config/low_price_two_leg_expanded_profile_evidence_2026-08-26.json`
binds the 57-trading-day source report canonical hash, all 12 positive
calibration/holdout recommendations, and the explicit user implementation
instruction. The exact-date transition keeps the 40-profile generation through
2026-08-26 and selects 45 profiles only from 2026-08-27. Existing orders and
held positions remain bound to their original policy snapshot.

Seven existing profiles adopt the reviewed entry-generation rows:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---:|---|---:|---:|
| `sk_eternix_late_morning` | 10:45~10:54 | 15 | 1.75% | 0.20% | close/-1 tick | 5 | +4 ticks |
| `cj_cgv_late_morning` | 10:00~10:09 | 15 | 0.50% | 0.35% | close/-1 tick | 5 | +4 ticks |
| `mirae_asset_late_morning` | 10:00~10:29 | 20 | 1.00% | 0.35% | -1/-2 ticks | 5 | +4 ticks |
| `kepco_morning` | 09:35~09:59 | 15 | 0.50% | 0.75% | close/-1 tick | 5 | +4 ticks |
| `nhn_late_morning` | 10:30~10:49 | 30 | 0.50% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `sk_telecom_late_morning` | 10:45~10:54 | 30 | 0.75% | 0.20% | close/-1 tick | 5 | +4 ticks |
| `hanse_late_morning` | 10:00~10:19 | 20 | 0.75% | 0.20% | close/-1 tick | 5 | +4 ticks |

Five new independent profiles are added:

| Profile | Scan bars | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---|---:|---:|---|---:|---:|
| `sd_biosensor_morning` | 09:30~09:49 | 15 | 0.75% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `sd_biosensor_late_morning` | 10:40~10:59 | 30 | 0.50% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `sd_biosensor_midday` | 13:25~13:54 | 20 | 0.75% | 0.20% | close/-1 tick | 5 | +2 ticks |
| `doosan_enerbility_afternoon` | 14:10~14:29 | 15 | 0.75% | 0.05% | close/-1 tick | 5 | +2 ticks |
| `samsung_ea_midday` | 13:20~13:49 | 30 | 1.00% | 0.75% | close/-1 tick | 5 | +2 ticks |

The wrappers and ten exact timers cover every new profile. Preflight still
requires the exact-date applied policy, immutable evidence, main-bot presence,
manual-owner exclusion, shared token, and all broker/order guards. This revision
does not change provider route, quantity, no-stop custody, or another owner's
orders.

## Runtime authority and isolation

The live service is fail-closed unless all of the following are true for the
exact profile and date:

- the immutable profile and exact live-confirmation string match;
- the profile-specific enable environment variable is true;
- the shared cached Kiwoom token is available;
- the main bot process is active;
- the symbol has an explicit `manual_operator` exclusion from the primary bot;
- the profile-bound frozen clean-baseline source replay and result pass;
- the exact-date PREOPEN policy artifact and same-day authority artifact pass;
- the endpoint is `https://api.kiwoom.com`, the route is SOR, and each new entry
  leg is exactly 10 shares. Legacy owned one-share orders remain valid custody
  state and are never resized retroactively.

Activation requires protected `manual_operator` markers for every profile symbol.
The reviewed installer adds the Youngone, NHN, SK Eternix, and Mirae Asset
markers together with the previously installed markers immediately before enabling the new timers, so
source implementation alone does not partially transfer their runtime owner.
This excludes the symbols from
the primary bot while leaving the Doosan/Hanwha widget owners and episode
owners mutually independent. Timer installation remains a separate reviewed
operator action:

```bash
sudo deploy/install_low_price_two_leg_systemd.sh
```

Rollback removes only these units and preserves state, authority, orders, and
held-position evidence:

```bash
sudo deploy/uninstall_low_price_two_leg_systemd.sh
```

## Profile-specific tuning

Postclose `low_price_two_leg_tuning` reads only each profile's durable actual
broker state and its own prior reports.  It never re-queries historical prices
and never pools different symbols or sessions.  Its sole decision window is
`clean_baseline_cumulative`: every available actual-state daily observation
from `2026-06-05` through the target date, including explicit reconciliation
of a carried episode to its original trade date, with notional-weighted EV as
the primary metric.  Trading dates before machine observation began, or dates
without an observation, are disclosed as coverage gaps but are not imputed as
outcomes and are not backfilled from historical market replay.

After the active-profile tuning and expanded-candidate research reports are
available, `machine_microstructure_attribution` discovers both inventories
again and joins target-date micro-reversion 0B/0D paths to signal anchors.  A
new active or prospective profile is therefore present even when its micro
producer has no rows.  That condition is reported as an explicit coverage gap,
never as a zero return, and blocks only the supplemental micro context; the
existing actual-state tuning and candidate path continues unchanged.  This
companion report is diagnostic-only and has no PREOPEN or broker authority.
Repairable gaps feed the next KRX date's bounded source-only 0B/0D collection
set.  The current dynamic episode universe also remains in the shared four-symbol
daily `micro_policy_sample_accumulation` rotation so a one-day repair does not
leave the policy evidence discontinuous; manual-control exclusions are deliberately
not applied to collection or evaluation.  A micro-conditioned episode-policy review opens only after the
same owner/symbol/session has at least five observed trading days and 20 matched
anchors, BBO coverage of at least 95%, depth-window coverage of at least 90%,
no invalid contract rows, and positive cost-adjusted paired EV in rolling
5/10/20-day windows without worse p10 or held/unresolved outcomes.  The first
runtime linkage still requires a new bounded family, rollback, and explicit
operator approval, and may apply only through an exact-date PREOPEN artifact.

From `2026-08-14`, each attempted row must match the exact-date PREOPEN applied
policy hash and fields. Target validation uses that applied policy, so the
historical Kakao morning +3-tick target is not compared with a different policy
generation. New target reconciliations persist broker `kt00007.cntr_uv`;
only broker-priced completed legs contribute to decision EV and its 20-leg floor.
Older configured-target proxy results remain separately labeled diagnostics.
The postclose producer also reads the official account realized-PnL endpoint
`ka10073` for realization-days that contain a completed episode. The
realization day comes from the broker target-order date or verified manual-sell
receipt date, with `target_filled_at` used only for older rows that lack that
receipt provenance; a carried
episode remains attributed to its original entry date while its exact costs are
queried on the actual exit-reconciliation date. Its exact net PnL,
commission, and tax replace the fixed-cost estimate only when one episode
profile owns that symbol-realization-day and the account aggregate matches the episode's
filled quantity, weighted buy price, weighted sell price, and
`gross profit - commission - tax`. A query failure, mismatch, or same-symbol
multi-profile realization day is never apportioned heuristically; completed
legs with different or partly missing realization dates also remain on the
reviewed `0.23%` round-trip fallback. Historical report rows are recalculated
from their persisted broker fill prices under the current fallback instead of
being discarded when an older report used a different fixed cost.

An attempted episode with any held or unresolved leg remains visible as
inventory risk but the entire episode, including an already completed sibling
leg, stays outside decision EV until both legs are terminal. Samsung and
lower-price tuners use this same complete-episode rule. After at least 20
completed legs in that clean-baseline actual-observation window,
positive current and candidate EV, and no held/unresolved inventory, one
profile may propose one tightening axis for the next PREOPEN:

- drawdown from the profile baseline to at most `baseline + 0.25%p`, or
- near-low proximity from the profile baseline to at most `baseline - 0.10%p`.

Across all forty-eight profiles and the existing Samsung regular machines, at most one
profile/machine and one entry axis may change per day.  The Samsung candidate is
produced first; if it owns a valid mutation, or its same-date candidate is
invalid, the lower-price family carries all policies forward. Quantity is fixed
at 10 shares per leg (20 total) by explicit operator authority; each
profile's frozen 50:50 entry offsets, target ticks, entry validity, route, stop/hold
behavior, provider, bot, cap, and broker guards are immutable.  Each preflight
first materializes or reuses the exact-date applied policy and binds its hash to
the profile authority artifact. The live template service requires the same
profile's preflight unit again at service start, even when the earlier timer
already completed. Authority or exact-date applied-policy rejection exits
(`4/5`) are fail-closed terminal startup results and are not restart-looped;
this prevents a mutable source/profile transition from producing repeated
broker-gateway startup attempts between the timer preflight and live start.

The retired Daewoo E&C profiles are absent from the runtime allowlist, wrappers,
and install timers. The installer also removes any legacy Daewoo timer files and
stops their exact service instances without deleting state or held-position
evidence.

The 2026-08-12 postclose tuning candidate predates the six-profile expansion.
For the 2026-08-13 PREOPEN transition only, its exact seven-profile v2 policy is
validated first and the six newly approved profiles are added at their frozen
baselines. The candidate and applied-policy inventory contained all thirteen
profiles through 2026-08-18. From the 2026-08-19 revision it must contain all
twenty. The reviewed 2026-08-19 stage contained twenty-three profiles, but it
never becomes a separate active date generation. Target dates from 2026-08-21
must contain the combined twenty-seven profiles: the prior 11 recommendations
are carried forward unless replaced by one of the latest nine rows, and four
new profiles are added. Both evidence generations are recorded in the
exact-date `profile_revision_transition`; a partial or stale inventory fails
closed. A valid 2026-08-20 bounded tuning mutation is still checked against its
20-profile source lineage, but it is not applied concurrently with this
same-stage user-approved revision; the 27-profile baseline owns the transition.
The artifact enumerates the 15 profiles affected by the combined approvals, so
an unrelated ignored mutation is labeled separately rather than attributed to
user approval. Subsequent exact-date generations contain 35 profiles from
2026-08-24, 40 from 2026-08-25, and 45 from 2026-08-27. The user-approved
2026-08-27 postclose generation takes effect only on 2026-08-28: it revises
eight existing profiles and adds `sk_telecom_morning`, producing 46 profiles.
Its nine-row evidence hash and source-report hash are checked independently;
target dates through 2026-08-27 continue to resolve the immutable 45-profile
generation so open orders and held custody are never reinterpreted.
The user-approved 2026-08-28 postclose generation takes effect only on
2026-08-31: it revises five existing profiles and adds `fan_ocean_morning` and
`fan_ocean_late_morning`, producing 48 profiles. Its seven-row evidence is bound
to canonical SHA-256
`d5f6e6cb6f80e2fa70c1807f39dc18955060f74d14cdf2111821f1a6b9d1e944`.
Target dates from 2026-08-28 through 2026-08-30 continue to resolve the
immutable 46-profile generation; existing orders and held custody retain their
original signal-date policy snapshot across the 48-profile transition.

## Daily implementation-candidate recommendation

The 20:10 postclose chain runs `low_price_two_leg_expanded_candidate_research`
after the actual-profile tuning step. It uses every KRX trading date from the
clean baseline (`2026-06-05`) through the target date. The latest 16 dates remain
untouched holdout evidence; every earlier clean-baseline date forms an expanding
calibration window. The reviewed new-symbol universe combines the fixed seed
set with up to five source-qualified dynamic seeds from the latest completed
daily recommendation snapshot, with all four supported regular-session lanes
evaluated separately.

A separate existing-symbol time-extension lane evaluates only supported
midday/afternoon sessions that have no active profile for that symbol. Active
symbol/session pairs are excluded rather than retuned through this discovery
producer. Active symbol/session pairs are excluded, while unimplemented
midday/afternoon windows for the newly added symbols remain eligible for the
separate time-extension lane.

Only profiles with matching source-qualified trading dates, positive
notional-weighted holdout EV, the required calibration/holdout sample floors,
the bounded no-stop carry budget, and a latest close at or below KRW 100,000
enter the ranked recommendation list. The JSON and Markdown report are atomically written before
an `ADMIN_ONLY` Telegram message is attempted. Delivery retries up to three
times, and a target-date state file prevents duplicate notices during postclose
recovery. Missing Telegram configuration, exhausted delivery retries, or a
report authority mismatch closes the postclose wrapper as failed rather than
silently claiming daily delivery.

If the cached Kiwoom token is unavailable or one of the new/existing-symbol
sources fails the full clean-baseline common-date/source-quality contract, the
producer writes a
`source_quality_blocked` report and sends an admin notice stating that no daily
recommendation was produced. This isolated research-source block does not stop
unrelated postclose producers. Telegram configuration or delivery failure still
fails the wrapper because daily delivery itself was not completed.

This is recommendation-only automation. It cannot add a profile, install or
start a service, create a PREOPEN policy, submit an order, or change quantity,
targets, stops, providers, the main bot, caps, or broker guards. A recommended
profile still requires a separate user instruction, implementation, and review
gate.

The fixed reviewed universe also contains the operator-directed source-only
observation candidate `candidate_475560_morning` for 더본코리아. Its immutable
policy is `09:40~09:59`, lookback `20`, drawdown `0.50%`, near-low `0.35%`,
entries `(signal close, signal close - 1 tick)`, five completed-bar validity,
and a `+4 tick` target. The postclose report accumulates the same candidate
against the latest 16 trading-day holdout and reports progress toward three
episodes and four completed legs. It cannot be re-optimized, installed, started,
or promoted to the machine-recommendation list or real orders by this observation
contract. Its primary decision metric is completed-leg
`notional_weighted_ev_pct`; official-history success, the complete clean-baseline
date window, exact fixed-policy identity, valid SOR OHLC, and separation of active
unrealized legs are mandatory source gates. Completed-minute evidence does not
prove fresh-BBO spread, passive-fill feasibility, or spread-and-fee-adjusted
target EV. Those prospective checks require a separate reviewed
execution-quality contract. Thin OOS evidence and diagnostic win rate cannot
become live authority.

## Episode read request control

All live lower-price profiles share the episode-only read controller for
`ka10080` market data and `kt00007` order/execution reconciliation.
A process reuses one successful completed-bar snapshot within the same KST
minute, and independent episode processes serialize a remaining `ka10080`
or `kt00007` request at a conservative local interval of 0.4 seconds. Two legs
with the same symbol, order date, payload, and continuation key reuse a
successful `kt00007` response for at most one second, collapsing the duplicate
account read within one reconciliation cycle. An explicit Kiwoom `1700` or
HTTP 429 read failure is retried at most twice with bounded backoff.
The official reference identifies error 1700 but does not publish the local
0.4-second value; that interval is an operational burst guard based on observed
traffic. Failed/invalid snapshots are not cached. Order and cancel API IDs never
enter this retry path, so an ambiguous broker write cannot be replayed.
A successful response is cached for the rest of the KST minute only when it
already contains the immediately preceding completed candle. A boundary response
that still ends two or more minutes behind is returned once but not cached, so the
next bounded poll can observe the newly published candle.

## Manual exit reconciliation

An operator who manually sells a held episode can close only that exact owner
ledger through `python -m src.trading.order.manual_episode_exit_reconciliation`.
The command is dry-run by default and prints a state-derived confirmation
string. `--apply --confirm ...` is accepted only after the service lock is free,
every held-inventory target is already terminal `HELD`, no partial target exit exists,
and one official `kt00007` sell receipt matches the owner symbol, exact whole
held quantity, zero remainder, order date, and order number. A cross-profile
aggregate sale, partial fill, live target, receipt ambiguity, or balance-based
inference fails closed. A shared receipt registry also prevents the same sell
order from being assigned to a second owner. It never submits or cancels an
order and never edits another owner ledger. The verified manual sell price and
broker receipt order date remain broker-priced outcome evidence for postclose tuning.

## Official Kiwoom reference evidence

- Repository: `Kiwoom-Securities/Kiwoom-REST-API`
- Commit: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Retrieved: `2026-08-20T15:34:48+09:00`
- Inspected: `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`,
  `kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core`, the Postman collection, and
  `examples/국내주식/차트/get_domestic_stock_minute_chart.py`
- Requests: `ka10080`, `kt10000`, `kt10001`, `kt10003`, and `kt00007`
