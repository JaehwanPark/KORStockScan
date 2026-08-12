# Samsung morning re-entry research — 2026-08-10

- decision: `holdout_pass_source_only_reentry_candidate`
- authority: source-only; no runtime or order mutation
- reconstructed first-episode complete dates: `35` / `44`
- grid candidates: `31920`

- parameters: `{'family': 'low_hold_reclaim_passive_split', 'lookback_bars': 15, 'rolling_high_drawdown_pct': 0.75, 'rolling_low_proximity_pct': 0.35, 'scan_end': '10:00', 'entry_valid_completed_bars': 3, 'entry_offset_ticks': -1, 'confirmation_bars': 2, 'reclaim_ticks': 1, 'confirmation_low_hold_required': True, 'entry_anchor': 'confirmation_close'}`
- calibration: `{'signal_episodes': 17, 'attempted_legs': 34, 'completed_legs': 32, 'no_fill_legs': 2, 'held_legs': 0, 'notional_weighted_ev_pct': 0.11355}`
- holdout: `{'signal_episodes': 12, 'attempted_legs': 24, 'completed_legs': 19, 'no_fill_legs': 5, 'held_legs': 0, 'notional_weighted_ev_pct': 0.170116}`

Each family used calibration-only selection before holdout evaluation; the same holdout was reused across the disclosed family iteration. Minute-bar touches are not real fill evidence.
