# Stage Hook Runtime Scaffold - 2026-06-02

## Summary

- status: `pass`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implemented_hook_count: `2`
- implemented_hook_names: `['holding_flow_runner_debounce_guard', 'plateau_breakdown_exit_arbitration_probe']`

## Hooks

### `holding_flow_runner_debounce_guard`
- stage: `holding`
- hook_class: `runtime_arbitration_hook`
- initial_runtime_state: `disabled`
- requires_separate_runtime_apply_candidate: `True`
- action_namespace_scope: `review_only_labels_not_runtime_actions`

### `plateau_breakdown_exit_arbitration_probe`
- stage: `exit`
- hook_class: `runtime_arbitration_hook`
- initial_runtime_state: `disabled`
- requires_separate_runtime_apply_candidate: `True`
- action_namespace_scope: `review_only_labels_not_runtime_actions`

