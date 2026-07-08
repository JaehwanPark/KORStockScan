# Rising Missed Classifier Prior - 2026-07-08

- generated_at: 2026-07-08T20:46:27+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: counterfactual_source_unavailable
- prior_count: 32
- recommendation_counts: {"hold_sample": 12, "loss_filter": 5, "positive_prior": 7, "recheck_prior": 1, "source_quality_blocked": 7}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=recheck_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_wait_requote_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_normal|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_ok|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=strong_strength_momentum|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=OPEN_TOP,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=REALTIME_RANK_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=rising_missed_forced_scout_loser_without_winner
- entry_score_parent=-|entry_source_parent=entry_source_wait6579|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_action_decision|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=source_quality_blocked | confidence=blocked | window=rolling10d | reason=child_conflict_or_source_quality_gap
- entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
