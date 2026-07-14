# Rising Missed Classifier Prior - 2026-07-14

- generated_at: 2026-07-14T20:48:08+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: counterfactual_source_unavailable
- prior_count: 22
- recommendation_counts: {"hold_sample": 12, "positive_prior": 3, "source_quality_blocked": 7}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_normal|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=strong_strength_momentum|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_scalp_sim|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_blocked_ai_score|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=rolling10d | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_unobserved|entry_source_parent=entry_source_scalp_sim|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_observed_other|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
