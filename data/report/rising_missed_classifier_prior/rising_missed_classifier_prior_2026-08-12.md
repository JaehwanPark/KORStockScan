# Rising Missed Classifier Prior - 2026-08-12

- generated_at: 2026-08-12T21:19:37+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 94
- blocker_outcome_prior_count: 14
- bounded_probe_exploration_candidate_count: 2
- recommendation_counts: {"hold_sample": 54, "loss_filter": 30, "positive_prior": 8, "recheck_prior": 1, "source_quality_blocked": 1}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=recheck_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_wait_requote_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_ok|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_watch|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior

## Blocker Outcome Priors

- tp1_selector|rising_missed_tp1_wait_confirmation_pending | assessment=bounded_probe_exploration_candidate | sample=17 | target_first=4 | adverse_first=5 | payoff_proxy=0.1
- rising_missed_tick_speed_entry_block|tick_acceleration_ratio_lt_1 | assessment=bounded_probe_exploration_candidate | sample=4 | target_first=2 | adverse_first=1 | payoff_proxy=0.475
- tp1_selector|tp1_micro_ws_unavailable | assessment=hold_loss_dominant | sample=313 | target_first=14 | adverse_first=43 | payoff_proxy=-0.038019
- tp1_selector|rising_missed_tp1_nxt_fast_tape_confirmation_required | assessment=hold_loss_dominant | sample=278 | target_first=16 | adverse_first=45 | payoff_proxy=-0.038489
- tp1_selector|rising_missed_tp1_lane_not_eligible | assessment=hold_loss_dominant | sample=117 | target_first=12 | adverse_first=33 | payoff_proxy=-0.064103
- tp1_selector|rising_missed_tp1_insufficient_positive_support | assessment=hold_loss_dominant | sample=29 | target_first=3 | adverse_first=8 | payoff_proxy=-0.058621
- tp1_selector|rising_missed_tp1_ai_state_blocked | assessment=hold_loss_dominant | sample=28 | target_first=5 | adverse_first=11 | payoff_proxy=-0.042857
- tp1_selector|rising_missed_tp1_hard_negative_evidence | assessment=hold_loss_dominant | sample=27 | target_first=3 | adverse_first=14 | payoff_proxy=-0.218519
- latency_block|latency_state_danger | assessment=hold_loss_dominant | sample=20 | target_first=3 | adverse_first=13 | payoff_proxy=-0.26
- tp1_selector|tp1_rest_budget_cache_unavailable | assessment=accumulate_mixed_recovery | sample=8 | target_first=3 | adverse_first=0 | payoff_proxy=0.4875
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60+tick_acceleration_ratio_lt_1 | assessment=hold_sample | sample=3 | target_first=0 | adverse_first=0 | payoff_proxy=0.0
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60 | assessment=hold_loss_dominant | sample=2 | target_first=0 | adverse_first=1 | payoff_proxy=-0.35
- tp1_selector|tp1_freshness_envelope_unavailable | assessment=hold_loss_dominant | sample=2 | target_first=0 | adverse_first=1 | payoff_proxy=-0.35
- real_weak_ai_micro_entry_block|weak_ai_buy_pressure_micro_context | assessment=hold_sample | sample=1 | target_first=0 | adverse_first=0 | payoff_proxy=0.0

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
