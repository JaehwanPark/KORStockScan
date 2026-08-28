# Rising Missed Classifier Prior - 2026-08-28

- generated_at: 2026-08-28T21:28:33+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 115
- blocker_outcome_prior_count: 14
- bounded_probe_exploration_candidate_count: 1
- recommendation_counts: {"hold_sample": 60, "loss_filter": 51, "positive_prior": 1, "source_quality_blocked": 3}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=medium | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=wait_requote | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_ok|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=overbought_watch|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=mtd | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation

## Blocker Outcome Priors

- tp1_selector|rising_missed_tp1_wait_confirmation_pending | assessment=bounded_probe_exploration_candidate | sample=31 | target_first=12 | adverse_first=14 | payoff_proxy=0.187097
- tp1_selector|tp1_micro_ws_unavailable | assessment=hold_loss_dominant | sample=533 | target_first=29 | adverse_first=86 | payoff_proxy=-0.042214
- tp1_selector|rising_missed_tp1_nxt_fast_tape_confirmation_required | assessment=hold_loss_dominant | sample=401 | target_first=28 | adverse_first=72 | payoff_proxy=-0.034913
- tp1_selector|rising_missed_tp1_lane_not_eligible | assessment=hold_loss_dominant | sample=288 | target_first=19 | adverse_first=92 | payoff_proxy=-0.137847
- latency_block|latency_state_danger | assessment=hold_loss_dominant | sample=85 | target_first=6 | adverse_first=73 | payoff_proxy=-0.509412
- tp1_selector|rising_missed_tp1_hard_negative_evidence | assessment=hold_loss_dominant | sample=62 | target_first=11 | adverse_first=27 | payoff_proxy=-0.074194
- tp1_selector|rising_missed_tp1_insufficient_positive_support | assessment=hold_loss_dominant | sample=35 | target_first=4 | adverse_first=10 | payoff_proxy=-0.051429
- rising_missed_tick_speed_entry_block|tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=31 | target_first=4 | adverse_first=15 | payoff_proxy=-0.170968
- tp1_selector|tp1_rest_budget_cache_unavailable | assessment=accumulate_mixed_recovery | sample=16 | target_first=3 | adverse_first=1 | payoff_proxy=0.2
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60 | assessment=hold_loss_dominant | sample=10 | target_first=0 | adverse_first=1 | payoff_proxy=-0.07
- tp1_selector|rising_missed_tp1_ai_state_blocked | assessment=hold_loss_dominant | sample=7 | target_first=1 | adverse_first=2 | payoff_proxy=-0.014286
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60+tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=6 | target_first=0 | adverse_first=1 | payoff_proxy=-0.116667
- tp1_selector|tp1_freshness_envelope_unavailable | assessment=hold_loss_dominant | sample=4 | target_first=0 | adverse_first=1 | payoff_proxy=-0.175
- rising_missed_scout_quality_guard_blocked|fresh_adverse_micro_submit_safety | assessment=hold_loss_dominant | sample=3 | target_first=0 | adverse_first=1 | payoff_proxy=-0.233333

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
