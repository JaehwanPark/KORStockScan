# Rising Missed Classifier Prior - 2026-09-03

- generated_at: 2026-09-03T23:51:28+09:00
- runtime_effect: false
- allowed_runtime_apply: false
- counterfactual_status: available
- prior_count: 111
- blocker_outcome_prior_count: 15
- bounded_probe_exploration_candidate_count: 2
- recommendation_counts: {"hold_sample": 54, "loss_filter": 55, "positive_prior": 1, "source_quality_blocked": 1}

## Top Priors

- entry_score_parent=-|entry_source_parent=-|source_signature=-|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=positive_prior | confidence=high | window=rolling10d | reason=rolling10d_positive_ev_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,HIGH_PROXIMITY_CONFIRMATION,OPEN_TOP,REALTIME_RANK_START,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED,VALUE_TOP|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,LOW_REBOUND_RISING_MISSED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,VALUE_TOP,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PREV_CLOSE_GAINER,VI_TRIGGERED|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,NEW_HIGH_CONFIRMATION,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=insufficient_positive_rolling_prior
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=hold_sample | confidence=low | window=None | reason=counterfactual_missed_winner_waiting_rolling_confirmation
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner
- entry_score_parent=-|entry_source_parent=-|source_signature=BID_IMBALANCE_SURGE,OPEN_TOP,PREV_CLOSE_GAINER,REALTIME_RANK_START,VALUE_TOP,VI_TRIGGERED,VOLUME_SURGE_POSITIVE|liquidity_bucket=-|strength_bucket=-|overbought_bucket=-|chosen_action=- | recommendation=loss_filter | confidence=medium | window=None | reason=counterfactual_avoided_loser_exceeds_missed_winner

## Blocker Outcome Priors

- tp1_selector|rising_missed_tp1_insufficient_positive_support | assessment=bounded_probe_exploration_candidate | sample=46 | target_first=6 | adverse_first=10 | payoff_proxy=0.017391
- tp1_selector|rising_missed_tp1_wait_confirmation_pending | assessment=bounded_probe_exploration_candidate | sample=36 | target_first=12 | adverse_first=17 | payoff_proxy=0.102778
- tp1_selector|tp1_micro_ws_unavailable | assessment=hold_loss_dominant | sample=605 | target_first=33 | adverse_first=101 | payoff_proxy=-0.04595
- tp1_selector|rising_missed_tp1_nxt_fast_tape_confirmation_required | assessment=hold_loss_dominant | sample=484 | target_first=34 | adverse_first=89 | payoff_proxy=-0.037397
- tp1_selector|rising_missed_tp1_lane_not_eligible | assessment=hold_loss_dominant | sample=326 | target_first=17 | adverse_first=105 | payoff_proxy=-0.157669
- latency_block|latency_state_danger | assessment=hold_loss_dominant | sample=106 | target_first=4 | adverse_first=94 | payoff_proxy=-0.571698
- tp1_selector|rising_missed_tp1_hard_negative_evidence | assessment=hold_loss_dominant | sample=72 | target_first=11 | adverse_first=33 | payoff_proxy=-0.122222
- rising_missed_tick_speed_entry_block|tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=40 | target_first=4 | adverse_first=20 | payoff_proxy=-0.22
- tp1_selector|tp1_rest_budget_cache_unavailable | assessment=accumulate_mixed_recovery | sample=15 | target_first=1 | adverse_first=1 | payoff_proxy=0.04
- tp1_selector|rising_missed_tp1_ai_state_blocked | assessment=hold_loss_dominant | sample=14 | target_first=1 | adverse_first=6 | payoff_proxy=-0.207143
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60 | assessment=hold_loss_dominant | sample=13 | target_first=0 | adverse_first=2 | payoff_proxy=-0.107692
- rising_missed_tick_speed_entry_block|tick_window_span_sec_ge_60+tick_acceleration_ratio_lt_1 | assessment=hold_loss_dominant | sample=9 | target_first=0 | adverse_first=1 | payoff_proxy=-0.077778
- tp1_selector|tp1_freshness_envelope_unavailable | assessment=hold_loss_dominant | sample=4 | target_first=0 | adverse_first=2 | payoff_proxy=-0.35
- rising_missed_scout_quality_guard_blocked|fresh_adverse_micro_submit_safety | assessment=hold_loss_dominant | sample=3 | target_first=0 | adverse_first=1 | payoff_proxy=-0.233333
- real_weak_ai_micro_entry_block|source_quality_unknown | assessment=hold_loss_dominant | sample=1 | target_first=0 | adverse_first=1 | payoff_proxy=-0.7

## Code Improvement Orders

- order_rising_missed_classifier_prior_bridge | runtime_effect: false | allowed_runtime_apply: false
