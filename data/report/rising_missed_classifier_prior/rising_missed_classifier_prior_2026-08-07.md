# Rising Missed Classifier Prior - 2026-08-07

- generated_at: 2026-08-07T21:50:18+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 84
- blocker_outcome_prior_count: 13
- bounded_probe_exploration_candidate_count: 1
- recommendation_counts: {"hold_sample": 49, "loss_filter": 24, "positive_prior": 8, "recheck_prior": 1, "source_quality_blocked": 2}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=recheck_prior | confidence=medium | window=rolling5d | reason=rolling5d_positive_wait_requote_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_ok|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling5d | reason=rolling5d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_watch|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling5d | reason=rolling5d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling5d | reason=rolling5d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner

## Blocker Outcome Priors

- rising_missed_tick_speed_entry_block|tick_acceleration_ratio_lt_1 | assessment=bounded_probe_exploration_candidate | sample=2 | target_first=1 | adverse_first=0 | payoff_proxy=0.65
- tp1_selector|tp1_micro_ws_unavailable | assessment=hold_loss_dominant | sample=214 | target_first=9 | adverse_first=30 | payoff_proxy=-0.043458
- tp1_selector|rising_missed_tp1_nxt_fast_tape_confirmation_required | assessment=hold_loss_dominant | sample=205 | target_first=12 | adverse_first=31 | payoff_proxy=-0.029756
- tp1_selector|rising_missed_tp1_lane_not_eligible | assessment=hold_loss_dominant | sample=82 | target_first=8 | adverse_first=18 | payoff_proxy=-0.026829
- tp1_selector|rising_missed_tp1_ai_state_blocked | assessment=hold_loss_dominant | sample=28 | target_first=5 | adverse_first=11 | payoff_proxy=-0.042857
- tp1_selector|rising_missed_tp1_insufficient_positive_support | assessment=hold_loss_dominant | sample=25 | target_first=3 | adverse_first=6 | payoff_proxy=-0.012
- tp1_selector|rising_missed_tp1_hard_negative_evidence | assessment=hold_loss_dominant | sample=16 | target_first=2 | adverse_first=7 | payoff_proxy=-0.14375
- latency_block|latency_state_danger | assessment=accumulate_mixed_recovery | sample=9 | target_first=2 | adverse_first=3 | payoff_proxy=0.055556
- tp1_selector|rising_missed_tp1_wait_confirmation_pending | assessment=hold_loss_dominant | sample=8 | target_first=1 | adverse_first=2 | payoff_proxy=-0.0125
- tp1_selector|tp1_rest_budget_cache_unavailable | assessment=accumulate_mixed_recovery | sample=8 | target_first=3 | adverse_first=0 | payoff_proxy=0.4875
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60+tick_acceleration_ratio_lt_1 | assessment=hold_sample | sample=2 | target_first=0 | adverse_first=0 | payoff_proxy=0.0
- tp1_selector|tp1_freshness_envelope_unavailable | assessment=hold_loss_dominant | sample=2 | target_first=0 | adverse_first=1 | payoff_proxy=-0.35
- real_weak_ai_micro_entry_block|weak_ai_buy_pressure_micro_context | assessment=hold_sample | sample=1 | target_first=0 | adverse_first=0 | payoff_proxy=0.0

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
