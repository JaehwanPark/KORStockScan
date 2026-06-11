# Lifecycle AI Context - 2026-06-11

- context_version: `lifecycle_ai_context_v1_2026-06-11`
- authority: `ai_advisory_prompt_context_only`
- runtime_effect: `False`
- provider_status: `{'provider': 'none', 'status': 'deterministic_fallback', 'schema_name': 'lifecycle_ai_context_v1', 'fallback_used': True}`

## Stage Contexts
| stage | prompt | policy_key | hint | contribution | quality |
| --- | --- | --- | --- | --- | --- |
| `entry` | `True` | `entry:weighted_adm_v1` | `WAIT_REQUOTE` | `0.0` | `observational_only_pending_outcome` |
| `submit` | `False` | `submit:weighted_adm_v1` | `NO_CHANGE` | `0.0` | `hold_sample` |
| `holding` | `True` | `holding:weighted_adm_v1` | `EXIT` | `0.0` | `hold_sample` |
| `scale_in` | `False` | `scale_in:weighted_adm_v1` | `NO_CHANGE` | `0.0` | `hold_sample` |
| `exit` | `True` | `exit:weighted_adm_v1` | `EXIT` | `0.0` | `hold_sample` |

## Forbidden Uses
- `['real_order_gate', 'pre_submit_block', 'provider_route', 'bot_restart', 'threshold_env_mutation', 'telegram_buy_sell']`
