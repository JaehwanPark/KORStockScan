# Rising Missed Classifier Prior - 2026-07-27

- generated_at: 2026-07-28T01:00:34+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 20
- recommendation_counts: {"hold_sample": 11, "loss_filter": 1, "source_quality_blocked": 8}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_normal|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=strong_strength_momentum|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_scalp_sim|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_blocked_ai_score|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=mtd | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_scalp_sim|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=mtd | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_scalp_sim|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
