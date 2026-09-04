# Rising Missed Classifier Prior - 2026-09-04

- generated_at: 2026-09-05T00:52:30+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 92
- blocker_outcome_prior_count: 15
- bounded_probe_exploration_candidate_count: 1
- recommendation_counts: {"hold_sample": 61, "loss_filter": 27, "positive_prior": 1, "recheck_prior": 3}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=recheck_prior | confidence=low | window=rolling10d | reason=rolling10d_positive_thin_or_fallback_sim_recheck
- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=liquidity_high|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=high | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,OPEN_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,REALTIME_RANK_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner

## Blocker Outcome Priors

- tp1_selector|rising_missed_tp1_wait_confirmation_pending | assessment=bounded_probe_exploration_candidate | sample=34 | target_first=12 | adverse_first=16 | payoff_proxy=0.129412
- tp1_selector|tp1_micro_ws_unavailable | assessment=hold_loss_dominant | sample=621 | target_first=34 | adverse_first=106 | payoff_proxy=-0.048309
- tp1_selector|rising_missed_tp1_nxt_fast_tape_confirmation_required | assessment=hold_loss_dominant | sample=470 | target_first=32 | adverse_first=88 | payoff_proxy=-0.042553
- tp1_selector|rising_missed_tp1_lane_not_eligible | assessment=hold_loss_dominant | sample=300 | target_first=18 | adverse_first=100 | payoff_proxy=-0.155333
- latency_block|latency_state_danger | assessment=hold_loss_dominant | sample=109 | target_first=4 | adverse_first=96 | payoff_proxy=-0.568807
- tp1_selector|rising_missed_tp1_hard_negative_evidence | assessment=hold_loss_dominant | sample=68 | target_first=10 | adverse_first=32 | payoff_proxy=-0.138235
- rising_missed_tick_speed_entry_block|tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=41 | target_first=4 | adverse_first=21 | payoff_proxy=-0.231707
- tp1_selector|rising_missed_tp1_insufficient_positive_support | assessment=hold_loss_dominant | sample=34 | target_first=5 | adverse_first=10 | payoff_proxy=-0.014706
- tp1_selector|rising_missed_tp1_ai_state_blocked | assessment=hold_loss_dominant | sample=14 | target_first=1 | adverse_first=6 | payoff_proxy=-0.207143
- tp1_selector|tp1_rest_budget_cache_unavailable | assessment=accumulate_mixed_recovery | sample=14 | target_first=1 | adverse_first=1 | payoff_proxy=0.042857
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60 | assessment=hold_loss_dominant | sample=13 | target_first=0 | adverse_first=2 | payoff_proxy=-0.107692
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60+tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=10 | target_first=0 | adverse_first=1 | payoff_proxy=-0.07
- tp1_selector|tp1_freshness_envelope_unavailable | assessment=hold_loss_dominant | sample=5 | target_first=0 | adverse_first=2 | payoff_proxy=-0.28
- rising_missed_scout_quality_guard_blocked|fresh_adverse_micro_submit_safety | assessment=hold_loss_dominant | sample=3 | target_first=0 | adverse_first=1 | payoff_proxy=-0.233333
- real_weak_ai_micro_entry_block|source_quality_unknown | assessment=hold_loss_dominant | sample=1 | target_first=0 | adverse_first=1 | payoff_proxy=-0.7

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
