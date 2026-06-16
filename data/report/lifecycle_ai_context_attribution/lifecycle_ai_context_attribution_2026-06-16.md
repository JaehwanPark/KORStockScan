# Lifecycle AI Context Attribution - 2026-06-16

- authority: `postclose_context_attribution_only`
- runtime_effect: `False`
- context eligible/applied/skipped: `3183` / `3183` / `0`
- replay_budget: `30` / mode: `observed_no_context_fields_or_degrade`
- implementation_status: `implemented`

## Stage Attribution
| stage | eligible | applied | completed | align | replay | delta | ev | contribution | quality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `entry` | `3183` | `3183` | `0` | `0.0518` | `0` | `None` | `None` | `-0.3137` | `observational_only_pending_outcome` |
| `submit` | `0` | `0` | `0` | `None` | `0` | `None` | `None` | `0.0` | `hold_sample` |
| `holding` | `0` | `0` | `0` | `None` | `0` | `None` | `None` | `0.0` | `hold_sample` |
| `scale_in` | `0` | `0` | `0` | `None` | `0` | `None` | `None` | `0.0` | `hold_sample` |
| `exit` | `0` | `0` | `0` | `None` | `0` | `None` | `None` | `0.0` | `hold_sample` |

## Forbidden Uses
- `['real_order_gate', 'pre_submit_block', 'provider_route', 'bot_restart', 'threshold_env_mutation', 'telegram_buy_sell']`
