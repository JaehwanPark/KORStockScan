# Scalp Sim AI Deferred Review 2026-05-29

- generated_at: `2026-05-29T16:39:46`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-29.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `1514`

## Defer Reasons

- `sim_ai_budget_exhausted`: `1514`

## Critical Classes

- `soft_critical`: `1514`

## Critical Reasons

- `feature_signature_changed`: `1360`
- `legacy_critical_zone`: `1474`
- `near_safe_profit_band`: `484`
- `soft_loss`: `332`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-05-29T09:09:31.760920 | 노타(486990) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 105 |
| 2026-05-29T09:09:49.086246 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.81 | +0.98 | 0.17 | 123 |
| 2026-05-29T09:10:14.963718 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.54 | +0.54 | 0.0 | 149 |
| 2026-05-29T09:10:54.208591 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.09 | +0.18 | 0.27 | 301 |
| 2026-05-29T09:10:54.374637 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.18 | +0.18 | 0.0 | 188 |
| 2026-05-29T09:10:54.393436 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 188 |
| 2026-05-29T09:10:54.408201 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.15 | +0.28 | 0.43 | 188 |
| 2026-05-29T09:11:07.493107 | 노타(486990) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.52 | 0.0 | 201 |
| 2026-05-29T09:11:31.079489 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.59 | +0.59 | 0.0 | 338 |
| 2026-05-29T09:11:31.095100 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 323 |
| 2026-05-29T09:11:51.989977 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.07 | +0.09 | 0.16 | 188 |
| 2026-05-29T09:12:06.886498 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.46 | +0.73 | 0.27 | 374 |
| 2026-05-29T09:12:11.961350 | 한올바이오파마(009420) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.67 | 0.0 | 76 |
| 2026-05-29T09:12:24.787243 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.63 | +0.88 | 0.25 | 278 |
| 2026-05-29T09:12:25.132213 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 141 |
| 2026-05-29T09:12:59.006042 | 씨이랩(189330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.41 | +3.41 | 0.0 | 195 |
| 2026-05-29T09:13:10.121203 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.73 | +0.73 | 0.0 | 437 |
| 2026-05-29T09:13:32.179247 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.63 | +0.88 | 0.25 | 346 |
| 2026-05-29T09:13:47.080241 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 459 |
| 2026-05-29T09:15:34.136936 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.23 | 0.0 | 468 |
| 2026-05-29T09:15:48.289038 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.60 | 0.0 | 92 |
| 2026-05-29T09:16:06.657147 | 한올바이오파마(009420) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.96 | 0.44 | 310 |
| 2026-05-29T09:16:08.472270 | 디아이씨(092200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.52 | 0.0 | 58 |
| 2026-05-29T09:16:18.403840 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.09 | +0.33 | 0.42 | 611 |
| 2026-05-29T09:16:18.457543 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | +0.09 | 0.4 | 512 |
| 2026-05-29T09:16:18.644826 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | +0.11 | 0.23 | 173 |
| 2026-05-29T09:16:20.688235 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.16 | +1.26 | 0.1 | 641 |
| 2026-05-29T09:16:48.036920 | 클로봇(466100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.44 | 0.0 | 151 |
| 2026-05-29T09:16:49.798454 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.09 | +0.33 | 0.42 | 642 |
| 2026-05-29T09:17:14.685917 | 클로봇(466100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.56 | 0.0 | 178 |
| 2026-05-29T09:17:41.267934 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.01 | +1.35 | 0.34 | 595 |
| 2026-05-29T09:17:41.397556 | 한올바이오파마(009420) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.71 | +2.16 | 0.45 | 405 |
| 2026-05-29T09:17:58.480238 | 클로봇(466100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.56 | 0.0 | 222 |
| 2026-05-29T09:18:53.299420 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.27 | +2.51 | 0.24 | 277 |
| 2026-05-29T09:18:55.165808 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.10 | +1.26 | 0.16 | 795 |
| 2026-05-29T09:20:05.001943 | 한올바이오파마(009420) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.31 | +2.61 | 0.3 | 549 |
| 2026-05-29T09:20:06.445610 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 350 |
| 2026-05-29T09:20:06.476859 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.94 | 0.27 | 150 |
| 2026-05-29T09:20:34.439126 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.26 | 0.36 | 895 |
| 2026-05-29T09:20:38.294781 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +0.68 | 0.0 | 382 |
| 2026-05-29T09:20:42.707227 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.11 | 0.45 | 437 |
| 2026-05-29T09:20:42.806711 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.94 | 0.27 | 187 |
| 2026-05-29T09:20:58.673847 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.78 | +0.78 | 0.0 | 654 |
| 2026-05-29T09:21:12.242017 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 416 |
| 2026-05-29T09:21:27.386765 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.78 | +1.78 | 0.0 | 821 |
| 2026-05-29T09:22:01.091421 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.78 | +1.82 | 0.04 | 855 |
| 2026-05-29T09:22:12.569847 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.16 | +1.36 | 0.2 | 993 |
| 2026-05-29T09:22:19.354828 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 483 |
| 2026-05-29T09:22:27.802100 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | +0.28 | 0.59 | 881 |
| 2026-05-29T09:23:06.645059 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 507 |
| 2026-05-29T09:23:08.851933 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.35 | +1.82 | 0.47 | 923 |
| 2026-05-29T09:23:22.991256 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.87 | +1.87 | 0.0 | 1063 |
| 2026-05-29T09:23:43.974666 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.38 | 0.07 | 545 |
| 2026-05-29T09:23:56.665676 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.62 | +1.98 | 0.36 | 1097 |
| 2026-05-29T09:23:56.900028 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +0.68 | 0.0 | 580 |
| 2026-05-29T09:24:07.864563 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.33 | 0.56 | 1080 |
| 2026-05-29T09:24:09.372811 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.45 | 0.09 | 983 |
| 2026-05-29T09:24:17.782124 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.45 | 0.0 | 579 |
| 2026-05-29T09:24:27.510752 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.77 | 0.33 | 228 |
| 2026-05-29T09:24:29.723363 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.82 | +1.98 | 0.16 | 1130 |
| 2026-05-29T09:24:31.367643 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.68 | 0.18 | 615 |
| 2026-05-29T09:24:41.290635 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.36 | +0.45 | 0.09 | 1015 |
| 2026-05-29T09:24:44.542303 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.45 | 0.0 | 605 |
| 2026-05-29T09:24:59.520210 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.55 | +0.77 | 0.22 | 260 |
| 2026-05-29T09:25:08.263247 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.72 | +1.98 | 0.26 | 1168 |
| 2026-05-29T09:25:10.148789 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.11 | 0.45 | 705 |
| 2026-05-29T09:25:18.142511 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.49 | 0.04 | 639 |
| 2026-05-29T09:25:24.281285 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | +0.09 | 0.4 | 1058 |
| 2026-05-29T09:25:24.331872 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +0.79 | 0.0 | 1058 |
| 2026-05-29T09:25:43.484464 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.77 | +1.98 | 0.21 | 1204 |
| 2026-05-29T09:25:51.649526 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.49 | 0.0 | 672 |
| 2026-05-29T09:25:56.502979 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +0.79 | 0.0 | 1090 |
| 2026-05-29T09:25:59.545484 | 와이즈넛(096250) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 36 |
| 2026-05-29T09:26:11.871860 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.77 | +1.98 | 0.21 | 1232 |
| 2026-05-29T09:26:21.656909 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.52 | 0.0 | 702 |
| 2026-05-29T09:26:33.636523 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.13 | +1.13 | 0.0 | 1127 |
| 2026-05-29T09:26:51.889978 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.06 | +2.23 | 0.17 | 271 |
| 2026-05-29T09:27:04.007806 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.70 | 0.39 | 745 |
| 2026-05-29T09:27:07.173156 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.96 | +1.13 | 0.17 | 1161 |
| 2026-05-29T09:27:24.196290 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.33 | 0.56 | 1276 |
| 2026-05-29T09:27:26.834981 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.07 | +3.07 | 0.0 | 306 |
| 2026-05-29T09:27:32.775704 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.48 | 0.0 | 85 |
| 2026-05-29T09:27:35.689713 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.70 | 0.21 | 776 |
| 2026-05-29T09:27:57.541687 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.23 | +2.42 | 0.19 | 241 |
| 2026-05-29T09:28:12.881892 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.94 | 0.45 | 637 |
| 2026-05-29T09:28:12.902770 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.55 | +0.77 | 0.22 | 453 |
| 2026-05-29T09:28:15.972947 | 와이즈넛(096250) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.20 | +1.31 | 0.11 | 172 |
| 2026-05-29T09:28:18.073075 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.13 | 0.43 | 1232 |
| 2026-05-29T09:28:21.084420 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.70 | 0.14 | 822 |
| 2026-05-29T09:28:23.703467 | 포스코DX(022100) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.25 | +0.25 | 0.0 | 154 |
| 2026-05-29T09:28:39.941548 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.94 | +1.03 | 0.09 | 664 |
| 2026-05-29T09:28:39.955831 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.55 | +0.77 | 0.22 | 480 |
| 2026-05-29T09:28:39.983435 | 와이즈넛(096250) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.20 | +1.31 | 0.11 | 196 |
| 2026-05-29T09:28:56.959243 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.70 | 0.14 | 858 |
| 2026-05-29T09:28:57.007360 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.23 | +2.42 | 0.19 | 301 |
| 2026-05-29T09:29:01.776853 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 885 |
| 2026-05-29T09:29:03.306001 | 포스코DX(022100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.41 | 0.0 | 193 |
| 2026-05-29T09:29:17.968009 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.76 | +1.03 | 0.27 | 702 |
| 2026-05-29T09:29:17.992325 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.44 | +1.44 | 0.0 | 518 |
| 2026-05-29T09:29:26.171769 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.70 | 0.18 | 887 |
| 2026-05-29T09:29:26.206169 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.23 | +2.42 | 0.19 | 330 |
| 2026-05-29T09:29:41.873928 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 925 |
| 2026-05-29T09:29:50.080554 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | +0.09 | 0.56 | 1324 |
| 2026-05-29T09:30:00.978036 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.70 | 0.04 | 922 |
| 2026-05-29T09:30:00.991556 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.85 | +1.03 | 0.18 | 745 |
| 2026-05-29T09:30:01.006057 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.88 | +1.88 | 0.0 | 561 |
| 2026-05-29T09:30:01.051684 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.42 | +2.42 | 0.0 | 365 |
| 2026-05-29T09:30:09.098249 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 952 |
| 2026-05-29T09:30:17.581215 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.40 | +0.40 | 0.0 | 325 |
| 2026-05-29T09:30:31.637880 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +0.70 | 0.0 | 952 |
| 2026-05-29T09:30:31.650079 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +1.03 | 0.45 | 775 |
| 2026-05-29T09:30:31.674334 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.77 | +1.88 | 0.11 | 592 |
| 2026-05-29T09:30:31.695306 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.23 | +2.42 | 0.19 | 396 |
| 2026-05-29T09:30:39.697202 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 75 |
| 2026-05-29T09:30:51.206461 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.68 | 0.18 | 995 |
| 2026-05-29T09:30:53.269275 | 포스코DX(022100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.41 | 0.0 | 303 |
| 2026-05-29T09:31:24.740026 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.29 | +1.29 | 0.0 | 1418 |
| 2026-05-29T09:31:24.779898 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.11 | 0.45 | 1079 |
| 2026-05-29T09:31:24.795080 | 비츠로셀(082920) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.68 | 0.36 | 1028 |
| 2026-05-29T09:31:28.277451 | 포스코DX(022100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.57 | 0.0 | 338 |
| 2026-05-29T09:31:41.766867 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.27 | +4.27 | 0.0 | 409 |
| 2026-05-29T09:31:41.781955 | 와이즈넛(096250) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.09 | +1.31 | 0.22 | 378 |
| 2026-05-29T09:31:59.675581 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.33 | 0.56 | 1552 |
| 2026-05-29T09:31:59.744987 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.55 | 0.0 | 1453 |
| 2026-05-29T09:32:00.842764 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.34 | +0.11 | 0.45 | 1115 |
| 2026-05-29T09:32:04.566202 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | +0.48 | 0.91 | 357 |
| 2026-05-29T09:32:16.602401 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.28 | +1.28 | 0.0 | 1583 |
| 2026-05-29T09:32:30.738973 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.33 | 0.56 | 1583 |
| 2026-05-29T09:32:30.782258 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.38 | +1.55 | 0.17 | 1484 |
| 2026-05-29T09:32:34.101629 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.48 | 0.0 | 386 |
| 2026-05-29T09:32:38.361427 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +0.84 | 0.12 | 194 |
| 2026-05-29T09:32:52.658144 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.56 | +1.56 | 0.0 | 1619 |
| 2026-05-29T09:33:04.897989 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.09 | +0.33 | 0.42 | 1617 |
| 2026-05-29T09:33:04.989787 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.46 | +1.55 | 0.09 | 1519 |
| 2026-05-29T09:33:06.905053 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.11 | 0.45 | 1182 |
| 2026-05-29T09:33:07.195407 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +0.68 | 0.0 | 419 |
| 2026-05-29T09:33:11.038241 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.84 | 0.47 | 226 |
| 2026-05-29T09:33:15.586432 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.67 | +5.14 | 0.47 | 503 |
| 2026-05-29T09:33:27.466051 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.69 | +1.69 | 0.0 | 1654 |
| 2026-05-29T09:33:32.394127 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.20 | 0.64 | 217 |
| 2026-05-29T09:33:38.463611 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.38 | +1.55 | 0.17 | 1552 |
| 2026-05-29T09:33:38.495776 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.11 | 0.34 | 1213 |
| 2026-05-29T09:33:38.640190 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.88 | +0.88 | 0.0 | 451 |
| 2026-05-29T09:33:47.067657 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.99 | +0.99 | 0.0 | 1148 |
| 2026-05-29T09:33:47.169974 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.67 | +5.14 | 0.47 | 535 |
| 2026-05-29T09:34:08.788089 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.55 | 0.0 | 1582 |
| 2026-05-29T09:34:08.807445 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | +0.11 | 0.23 | 1243 |
| 2026-05-29T09:34:08.882921 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 481 |
| 2026-05-29T09:34:18.499989 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.06 | 0.0 | 1179 |
| 2026-05-29T09:34:19.955833 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.75 | +5.14 | 0.39 | 567 |
| 2026-05-29T09:34:26.705609 | 포스코DX(022100) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.05 | +1.37 | 0.32 | 517 |
| 2026-05-29T09:34:28.498477 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.66 | +2.66 | 0.0 | 1715 |
| 2026-05-29T09:34:35.205793 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.12 | +0.33 | 0.21 | 1707 |
| 2026-05-29T09:34:40.796203 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.10 | +2.14 | 0.04 | 1614 |
| 2026-05-29T09:34:40.870070 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.11 | 0.34 | 1276 |
| 2026-05-29T09:34:43.724177 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.18 | +1.59 | 0.41 | 516 |
| 2026-05-29T09:34:57.553227 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.16 | +1.16 | 0.0 | 1218 |
| 2026-05-29T09:35:06.091067 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +2.66 | +2.66 | 0.0 | 1753 |
| 2026-05-29T09:35:13.351592 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.90 | +2.90 | 0.0 | 1647 |
| 2026-05-29T09:35:13.391570 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.56 | 0.0 | 1308 |
| 2026-05-29T09:35:13.546790 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.18 | +1.59 | 0.41 | 546 |
| 2026-05-29T09:35:31.091439 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.34 | 0.0 | 1252 |
| 2026-05-29T09:35:36.086553 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.66 | +2.66 | 0.0 | 1783 |
| 2026-05-29T09:35:42.950197 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.58 | +3.67 | 0.09 | 1677 |
| 2026-05-29T09:35:42.973525 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.12 | +1.12 | 0.0 | 1338 |
| 2026-05-29T09:35:43.100186 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.59 | 0.2 | 575 |
| 2026-05-29T09:36:02.604464 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.41 | +1.41 | 0.0 | 1283 |
| 2026-05-29T09:36:39.863468 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.01 | +1.12 | 0.11 | 1394 |
| 2026-05-29T09:36:39.883007 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.41 | +1.41 | 0.0 | 1321 |
| 2026-05-29T09:36:43.200505 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.84 | 0.24 | 439 |
| 2026-05-29T09:37:03.453214 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.04 | -0.04 | 0.0 | 415 |
| 2026-05-29T09:37:08.271544 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.78 | +1.12 | 0.34 | 1423 |
| 2026-05-29T09:37:08.295137 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.27 | +1.41 | 0.14 | 1349 |
| 2026-05-29T09:37:11.690131 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.59 | +1.59 | 0.0 | 664 |
| 2026-05-29T09:37:11.709073 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.84 | 0.24 | 467 |
| 2026-05-29T09:37:23.585780 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.33 | +3.67 | 0.34 | 1777 |
| 2026-05-29T09:37:28.382392 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.48 | +3.48 | 0.0 | 1895 |
| 2026-05-29T09:37:44.269129 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.12 | +1.12 | 0.0 | 1459 |
| 2026-05-29T09:37:44.292178 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.24 | +1.41 | 0.17 | 1385 |
| 2026-05-29T09:37:44.442101 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.19 | +2.19 | 0.0 | 697 |
| 2026-05-29T09:37:44.466383 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.96 | +0.96 | 0.0 | 500 |
| 2026-05-29T09:38:00.588458 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.48 | +3.62 | 0.14 | 1927 |
| 2026-05-29T09:38:02.098630 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.41 | +3.67 | 0.26 | 1816 |
| 2026-05-29T09:38:13.490684 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.12 | +1.23 | 0.11 | 1488 |
| 2026-05-29T09:38:13.502502 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.24 | +1.41 | 0.17 | 1414 |
| 2026-05-29T09:38:13.544404 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.99 | +2.19 | 0.2 | 726 |
| 2026-05-29T09:38:13.553823 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.96 | +0.96 | 0.0 | 529 |
| 2026-05-29T09:38:21.546052 | 디아이씨(092200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 185 |
| 2026-05-29T09:38:48.306351 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.45 | +1.45 | 0.0 | 1449 |
| 2026-05-29T09:38:48.363837 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.60 | +2.80 | 0.2 | 761 |
| 2026-05-29T09:39:06.404765 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.68 | +5.68 | 0.0 | 1993 |
| 2026-05-29T09:39:06.498412 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.43 | +4.68 | 0.25 | 1880 |
| 2026-05-29T09:39:06.603467 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.20 | 0.64 | 552 |
| 2026-05-29T09:39:21.103751 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.52 | +1.52 | 0.0 | 1482 |
| 2026-05-29T09:39:23.550430 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +0.96 | 0.24 | 599 |
| 2026-05-29T09:39:37.137950 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.50 | +6.50 | 0.0 | 2024 |
| 2026-05-29T09:39:37.165257 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.02 | +5.02 | 0.0 | 1911 |
| 2026-05-29T09:39:37.269301 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.73 | +0.73 | 0.0 | 582 |
| 2026-05-29T09:40:08.386947 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.67 | +1.67 | 0.0 | 1529 |
| 2026-05-29T09:40:09.494749 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.32 | +1.32 | 0.0 | 645 |
| 2026-05-29T09:40:20.993491 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.60 | +5.02 | 0.42 | 1955 |
| 2026-05-29T09:40:28.256048 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.45 | 0.0 | 42 |
| 2026-05-29T09:40:42.865103 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.45 | +1.67 | 0.22 | 1564 |
| 2026-05-29T09:40:44.244801 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.15 | +2.15 | 0.0 | 680 |
| 2026-05-29T09:40:49.464922 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.68 | +5.02 | 0.34 | 1983 |
| 2026-05-29T09:40:57.582550 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.45 | 0.11 | 71 |
| 2026-05-29T09:41:11.680558 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.45 | +1.67 | 0.22 | 1592 |
| 2026-05-29T09:41:13.039302 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.91 | +2.39 | 0.48 | 708 |
| 2026-05-29T09:41:14.691883 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.73 | +1.05 | 0.32 | 680 |
| 2026-05-29T09:41:21.293689 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +4.68 | +5.02 | 0.34 | 2015 |
| 2026-05-29T09:41:24.635235 | 디아이씨(092200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.01 | 0.44 | 368 |
| 2026-05-29T09:41:50.178549 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.38 | +1.67 | 0.29 | 1631 |
| 2026-05-29T09:41:50.206513 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.91 | +2.39 | 0.48 | 746 |
| 2026-05-29T09:42:10.562780 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.80 | +6.80 | 0.0 | 2064 |
| 2026-05-29T09:42:20.540218 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.74 | +1.74 | 0.0 | 1661 |
| 2026-05-29T09:42:53.012569 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.56 | +1.81 | 0.25 | 1694 |
| 2026-05-29T09:42:53.080229 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.03 | +2.39 | 0.36 | 808 |
| 2026-05-29T09:43:01.310179 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | -0.04 | 0.28 | 773 |
| 2026-05-29T09:43:31.047844 | 디바이스(187870) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.92 | +0.92 | 0.0 | 330 |
| 2026-05-29T09:43:41.432149 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.24 | +0.24 | 0.0 | 192 |
| 2026-05-29T09:43:54.993830 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.09 | 0.32 | 2169 |
| 2026-05-29T09:43:55.035493 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.84 | +1.84 | 0.0 | 1756 |
| 2026-05-29T09:43:55.083343 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.91 | +2.39 | 0.48 | 870 |
| 2026-05-29T09:43:58.895077 | 디바이스(187870) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.69 | +1.88 | 0.19 | 358 |
| 2026-05-29T09:44:13.649992 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.53 | +0.53 | 0.0 | 224 |
| 2026-05-29T09:44:13.679644 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 144 |
| 2026-05-29T09:44:19.707624 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +0.79 | 0.0 | 150 |
| 2026-05-29T09:44:33.866289 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.99 | +1.99 | 0.0 | 1795 |
| 2026-05-29T09:44:40.825471 | 디바이스(187870) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.88 | +1.88 | 0.0 | 400 |
| 2026-05-29T09:44:51.911058 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.28 | +0.45 | 0.73 | 305 |
| 2026-05-29T09:44:51.920494 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.58 | 0.23 | 262 |
| 2026-05-29T09:45:01.666740 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.79 | 0.18 | 192 |
| 2026-05-29T09:45:14.142582 | 디바이스(187870) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.27 | +2.27 | 0.0 | 434 |
| 2026-05-29T09:45:14.183861 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 205 |
| 2026-05-29T09:45:22.991786 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.58 | 0.23 | 293 |
| 2026-05-29T09:45:31.837271 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.16 | +1.26 | 0.1 | 222 |
| 2026-05-29T09:45:39.812433 | 디바이스(187870) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.85 | +2.85 | 0.0 | 459 |
| 2026-05-29T09:46:14.285350 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.45 | 0.78 | 388 |
| 2026-05-29T09:46:15.771937 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.06 | +0.22 | 0.16 | 195 |
| 2026-05-29T09:46:36.288681 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | -0.23 | 0.24 | 235 |
| 2026-05-29T09:46:38.180587 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.95 | +1.05 | 0.1 | 1003 |
| 2026-05-29T09:46:42.873242 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.33 | +0.45 | 0.78 | 416 |
| 2026-05-29T09:46:53.771063 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +0.72 | 0.0 | 252 |
| 2026-05-29T09:47:35.193423 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.67 | +2.15 | 0.48 | 294 |
| 2026-05-29T09:47:45.574469 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.44 | 0.0 | 132 |
| 2026-05-29T09:47:51.193128 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.45 | 0.58 | 485 |
| 2026-05-29T09:47:51.258867 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +1.26 | 0.47 | 362 |
| 2026-05-29T09:48:19.237955 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.63 | +0.63 | 0.0 | 166 |
| 2026-05-29T09:48:21.256625 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.27 | +1.59 | 0.32 | 1106 |
| 2026-05-29T09:48:25.399019 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.07 | +0.45 | 0.52 | 519 |
| 2026-05-29T09:48:26.707189 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.35 | +1.35 | 0.0 | 397 |
| 2026-05-29T09:48:28.236929 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | +0.01 | 0.12 | 190 |
| 2026-05-29T09:49:09.010675 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.59 | +1.59 | 0.0 | 1154 |
| 2026-05-29T09:49:19.924218 | 솔트룩스(304100) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.50 | 0.16 | 573 |
| 2026-05-29T09:49:50.496801 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.27 | +1.69 | 0.42 | 1196 |
| 2026-05-29T09:50:05.140136 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.46 | +1.86 | 0.4 | 404 |
| 2026-05-29T09:50:25.240650 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 248 |
| 2026-05-29T09:50:41.600659 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.54 | +2.54 | 0.0 | 440 |
| 2026-05-29T09:50:57.182226 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | +0.31 | 0.72 | 548 |
| 2026-05-29T09:51:05.467672 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.37 | +1.69 | 0.32 | 1271 |
| 2026-05-29T09:51:12.243267 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.67 | +2.87 | 0.2 | 471 |
| 2026-05-29T09:51:17.496214 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | +0.22 | 0.65 | 497 |
| 2026-05-29T09:51:39.847127 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.48 | +1.69 | 0.21 | 1305 |
| 2026-05-29T09:52:04.948765 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.27 | +0.27 | 0.0 | 348 |
| 2026-05-29T09:52:15.774494 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.26 | +1.54 | 0.28 | 626 |
| 2026-05-29T09:52:17.187167 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.62 | +3.62 | 0.0 | 536 |
| 2026-05-29T09:52:17.266208 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.63 | +0.91 | 0.28 | 404 |
| 2026-05-29T09:52:31.555219 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 374 |
| 2026-05-29T09:52:31.587679 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.23 | 0.13 | 204 |
| 2026-05-29T09:52:36.299261 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.10 | 0.33 | 148 |
| 2026-05-29T09:53:04.896481 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.91 | 0.47 | 451 |
| 2026-05-29T09:53:13.769517 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.36 | +4.49 | 0.13 | 592 |
| 2026-05-29T09:53:35.581076 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | +0.37 | 0.4 | 438 |
| 2026-05-29T09:54:03.697709 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.63 | +1.63 | 0.0 | 734 |
| 2026-05-29T09:54:05.080694 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 468 |
| 2026-05-29T09:54:19.661610 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | +0.31 | 0.72 | 750 |
| 2026-05-29T09:54:39.274636 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.54 | +1.63 | 0.09 | 770 |
| 2026-05-29T09:54:39.296785 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.91 | 0.47 | 546 |
| 2026-05-29T09:54:39.368362 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 502 |
| 2026-05-29T09:54:39.540747 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +0.56 | 0.0 | 17 |
| 2026-05-29T09:55:15.652579 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 538 |
| 2026-05-29T09:55:15.689808 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.60 | 0.0 | 308 |
| 2026-05-29T09:55:47.480439 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.82 | +1.82 | 0.0 | 838 |
| 2026-05-29T09:55:47.504806 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 570 |
| 2026-05-29T09:55:47.548933 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.77 | 0.33 | 339 |
| 2026-05-29T09:56:01.290910 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.23 | 0.11 | 334 |
| 2026-05-29T09:56:17.267778 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | +0.37 | 0.8 | 600 |
| 2026-05-29T09:56:17.305343 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.77 | 0.17 | 369 |
| 2026-05-29T09:56:54.971938 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | +0.37 | 0.8 | 638 |
| 2026-05-29T09:57:06.707858 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.12 | +1.23 | 0.11 | 2621 |
| 2026-05-29T09:57:25.798565 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | +0.37 | 0.4 | 668 |
| 2026-05-29T09:57:40.607191 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.12 | +1.23 | 0.11 | 2655 |
| 2026-05-29T09:57:50.926066 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 694 |
| 2026-05-29T09:58:06.894814 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.77 | 0.17 | 479 |
| 2026-05-29T09:58:11.592317 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.46 | +1.46 | 0.0 | 2686 |
| 2026-05-29T09:58:39.294114 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 742 |
| 2026-05-29T09:58:42.792545 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.46 | 0.23 | 2717 |
| 2026-05-29T09:58:54.381107 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.77 | 0.33 | 526 |
| 2026-05-29T09:59:09.849338 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | +0.37 | 0.4 | 772 |
| 2026-05-29T09:59:15.279953 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.46 | +1.91 | 0.45 | 2750 |
| 2026-05-29T09:59:21.384373 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +0.77 | 0.09 | 553 |
| 2026-05-29T09:59:55.774197 | 수젠텍(253840) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.93 | 0.49 | 588 |
| 2026-05-29T10:00:23.964132 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.37 | 0.5 | 847 |
| 2026-05-29T10:01:14.477669 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 897 |
| 2026-05-29T10:01:21.693203 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 655 |
| 2026-05-29T10:01:25.853067 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 34 |
| 2026-05-29T10:02:07.592456 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.39 | +2.39 | 0.0 | 950 |
| 2026-05-29T10:02:40.893292 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 109 |
| 2026-05-29T10:04:24.002933 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.60 | 0.0 | 175 |
| 2026-05-29T10:04:32.910319 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 41 |
| 2026-05-29T10:04:59.194632 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 177 |
| 2026-05-29T10:05:01.466914 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 69 |
| 2026-05-29T10:05:09.480381 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.64 | +0.64 | 0.0 | 220 |
| 2026-05-29T10:05:15.004583 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 888 |
| 2026-05-29T10:05:20.976661 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.58 | 0.0 | 158 |
| 2026-05-29T10:05:36.610462 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.23 | 0.16 | 215 |
| 2026-05-29T10:05:38.593198 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +0.82 | 0.0 | 249 |
| 2026-05-29T10:05:38.609013 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.12 | 0.11 | 249 |
| 2026-05-29T10:05:45.539713 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 919 |
| 2026-05-29T10:05:50.899208 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.58 | 0.11 | 188 |
| 2026-05-29T10:05:59.677658 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.23 | 0.25 | 334 |
| 2026-05-29T10:06:07.872496 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.23 | 0.16 | 246 |
| 2026-05-29T10:06:10.782651 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.82 | 0.35 | 281 |
| 2026-05-29T10:06:10.791290 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.12 | 0.27 | 281 |
| 2026-05-29T10:06:15.684002 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.17 | 0.47 | 254 |
| 2026-05-29T10:06:18.709926 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 952 |
| 2026-05-29T10:06:20.868358 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | -0.23 | 0.24 | 348 |
| 2026-05-29T10:06:34.289760 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.91 | +1.01 | 0.1 | 1261 |
| 2026-05-29T10:06:40.738039 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.23 | 0.16 | 279 |
| 2026-05-29T10:06:48.204454 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.12 | 0.22 | 319 |
| 2026-05-29T10:06:48.349626 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.58 | 0.23 | 246 |
| 2026-05-29T10:06:50.139900 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.01 | 0.22 | 983 |
| 2026-05-29T10:06:54.283427 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.47 | -0.23 | 0.24 | 382 |
| 2026-05-29T10:06:59.365405 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 394 |
| 2026-05-29T10:07:06.542665 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +1.01 | 0.29 | 1293 |
| 2026-05-29T10:07:17.361669 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.12 | 0.33 | 348 |
| 2026-05-29T10:07:17.488256 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.08 | +0.16 | 0.08 | 185 |
| 2026-05-29T10:07:24.478003 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.01 | 0.11 | 1018 |
| 2026-05-29T10:07:24.538234 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.23 | 0.12 | 412 |
| 2026-05-29T10:07:27.471779 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.19 | +0.19 | 0.0 | 309 |
| 2026-05-29T10:07:38.697348 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.29 | +1.29 | 0.0 | 1325 |
| 2026-05-29T10:07:53.453353 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.82 | 0.41 | 384 |
| 2026-05-29T10:07:53.468477 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.12 | 0.22 | 384 |
| 2026-05-29T10:07:53.590430 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.40 | +0.48 | 0.08 | 221 |
| 2026-05-29T10:07:55.465019 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.01 | 0.22 | 1049 |
| 2026-05-29T10:07:55.661609 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | +0.02 | 0.07 | 450 |
| 2026-05-29T10:07:55.675965 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | -0.11 | 0.0 | 443 |
| 2026-05-29T10:08:01.308480 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | +0.09 | 0.56 | 3615 |
| 2026-05-29T10:08:01.707729 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.69 | 0.14 | 250 |
| 2026-05-29T10:09:34.991140 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.26 | 0.59 | 523 |
| 2026-05-29T10:09:35.078107 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | -0.01 | 0.0 | 486 |
| 2026-05-29T10:09:35.178195 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.36 | +0.48 | 0.12 | 323 |
| 2026-05-29T10:09:48.444909 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.83 | +2.20 | 0.37 | 467 |
| 2026-05-29T10:09:48.539590 | 한켐(457370) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 70 |
| 2026-05-29T10:09:50.148238 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.07 | +0.09 | 0.16 | 3724 |
| 2026-05-29T10:09:52.096751 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.05 | +2.05 | 0.0 | 1459 |
| 2026-05-29T10:09:52.191530 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | -0.16 | 0.0 | 560 |
| 2026-05-29T10:10:05.352558 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | +0.16 | 0.28 | 580 |
| 2026-05-29T10:10:05.381439 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.10 | 0.11 | 516 |
| 2026-05-29T10:10:06.896451 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.48 | 0.16 | 355 |
| 2026-05-29T10:10:08.504502 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.09 | +0.26 | 0.17 | 487 |
| 2026-05-29T10:10:10.306709 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.38 | 0.0 | 578 |
| 2026-05-29T10:10:10.372619 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.55 | +0.55 | 0.0 | 369 |
| 2026-05-29T10:10:23.359038 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.15 | +2.15 | 0.0 | 1490 |
| 2026-05-29T10:10:37.770836 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.83 | +2.20 | 0.37 | 516 |
| 2026-05-29T10:10:37.877032 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.56 | 0.08 | 386 |
| 2026-05-29T10:10:42.797545 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.55 | 0.22 | 402 |
| 2026-05-29T10:10:56.704619 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.28 | 0.29 | 624 |
| 2026-05-29T10:10:58.699479 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.31 | +2.31 | 0.0 | 520 |
| 2026-05-29T10:11:03.706617 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.41 | +1.82 | 0.41 | 432 |
| 2026-05-29T10:11:08.642039 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.87 | +0.95 | 0.08 | 416 |
| 2026-05-29T10:11:12.372501 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.47 | +1.47 | 0.0 | 640 |
| 2026-05-29T10:11:12.649613 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.55 | 0.11 | 432 |
| 2026-05-29T10:11:29.861661 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.39 | +2.39 | 0.0 | 568 |
| 2026-05-29T10:11:34.479657 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.31 | +2.74 | 0.43 | 556 |
| 2026-05-29T10:11:36.372593 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.05 | 0.35 | 534 |
| 2026-05-29T10:11:40.881796 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +0.95 | 0.16 | 449 |
| 2026-05-29T10:11:49.280381 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.59 | 0.37 | 677 |
| 2026-05-29T10:11:49.421225 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.00 | +1.00 | 0.0 | 468 |
| 2026-05-29T10:12:09.452142 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.10 | +2.10 | 0.0 | 567 |
| 2026-05-29T10:12:12.384360 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.23 | +0.23 | 0.0 | 707 |
| 2026-05-29T10:12:12.461492 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.34 | 0.0 | 611 |
| 2026-05-29T10:12:12.569240 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.95 | +0.95 | 0.0 | 480 |
| 2026-05-29T10:12:14.476047 | 로보스타(090360) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.59 | 0.37 | 702 |
| 2026-05-29T10:12:14.605783 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.11 | +1.11 | 0.0 | 494 |
| 2026-05-29T10:12:34.666834 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.05 | +0.05 | 0.0 | 296 |
| 2026-05-29T10:12:35.964237 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.23 | 0.25 | 177 |
| 2026-05-29T10:12:37.771190 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.41 | 0.08 | 3891 |
| 2026-05-29T10:12:37.964332 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.36 | +1.42 | 0.06 | 669 |
| 2026-05-29T10:12:37.999012 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.21 | +2.68 | 0.47 | 595 |
| 2026-05-29T10:12:51.368073 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 650 |
| 2026-05-29T10:12:52.760383 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.56 | 0.22 | 532 |
| 2026-05-29T10:13:00.470480 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | +0.26 | 0.69 | 729 |
| 2026-05-29T10:13:10.747468 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.42 | 0.43 | 1364 |
| 2026-05-29T10:13:10.873490 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.09 | +1.42 | 0.33 | 702 |
| 2026-05-29T10:13:13.967758 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 768 |
| 2026-05-29T10:13:19.482340 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 678 |
| 2026-05-29T10:13:19.500924 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.29 | +2.76 | 0.47 | 678 |
| 2026-05-29T10:13:20.784663 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.56 | 0.22 | 560 |
| 2026-05-29T10:13:40.538161 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.65 | 0.24 | 3954 |
| 2026-05-29T10:13:40.596083 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.42 | 0.76 | 1394 |
| 2026-05-29T10:13:44.298015 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.26 | 0.39 | 773 |
| 2026-05-29T10:14:07.528594 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.38 | 0.38 | 1714 |
| 2026-05-29T10:14:08.771299 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.82 | 0.27 | 617 |
| 2026-05-29T10:14:13.299170 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.42 | 0.76 | 1427 |
| 2026-05-29T10:14:17.745191 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.26 | 0.39 | 806 |
| 2026-05-29T10:14:17.762138 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.20 | +1.42 | 0.22 | 768 |
| 2026-05-29T10:14:22.275387 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.65 | 0.24 | 3996 |
| 2026-05-29T10:14:22.368357 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 741 |
| 2026-05-29T10:14:29.650076 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.28 | 0.29 | 837 |
| 2026-05-29T10:14:37.802983 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.57 | +2.76 | 0.19 | 756 |
| 2026-05-29T10:14:39.194071 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.56 | 0.33 | 638 |
| 2026-05-29T10:14:40.661811 | 한켐(457370) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.73 | +0.97 | 0.24 | 362 |
| 2026-05-29T10:15:02.676148 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.13 | +0.26 | 0.39 | 851 |
| 2026-05-29T10:15:02.710804 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.58 | +1.63 | 0.05 | 813 |
| 2026-05-29T10:15:02.744229 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 781 |
| 2026-05-29T10:15:02.846471 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.71 | +1.03 | 0.32 | 651 |
| 2026-05-29T10:15:12.428046 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.45 | +1.56 | 0.11 | 671 |
| 2026-05-29T10:15:12.490798 | 한켐(457370) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.81 | +0.97 | 0.16 | 394 |
| 2026-05-29T10:15:29.801033 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.44 | +1.63 | 0.19 | 840 |
| 2026-05-29T10:15:29.810622 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.42 | 0.08 | 808 |
| 2026-05-29T10:15:35.899176 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.28 | 0.73 | 903 |
| 2026-05-29T10:15:37.442943 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.56 | 0.22 | 696 |
| 2026-05-29T10:15:37.464202 | 한켐(457370) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +0.97 | 0.0 | 419 |
| 2026-05-29T10:15:37.569854 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.76 | 0.25 | 359 |
| 2026-05-29T10:15:39.045741 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.65 | 0.32 | 4073 |
| 2026-05-29T10:16:04.845003 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 843 |
| 2026-05-29T10:16:12.578121 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.56 | 0.33 | 731 |
| 2026-05-29T10:16:27.171166 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.16 | +0.26 | 0.1 | 936 |
| 2026-05-29T10:16:28.659099 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.25 | +0.25 | 0.0 | 185 |
| 2026-05-29T10:16:41.289784 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.45 | +1.56 | 0.11 | 760 |
| 2026-05-29T10:16:41.343223 | 한켐(457370) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.73 | +1.22 | 0.49 | 483 |
| 2026-05-29T10:16:43.399091 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.28 | 0.51 | 971 |
| 2026-05-29T10:17:04.894832 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.29 | +3.38 | 0.09 | 1891 |
| 2026-05-29T10:17:04.955471 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.44 | 0.46 | 999 |
| 2026-05-29T10:17:05.184990 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.76 | 0.25 | 447 |
| 2026-05-29T10:17:07.247594 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.35 | +2.35 | 0.0 | 938 |
| 2026-05-29T10:17:27.287504 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.00 | +1.00 | 0.0 | 1015 |
| 2026-05-29T10:17:33.569768 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.06 | 0.29 | 188 |
| 2026-05-29T10:17:33.671204 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.83 | +1.01 | 0.18 | 76 |
| 2026-05-29T10:17:39.352481 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.51 | +0.76 | 0.25 | 481 |
| 2026-05-29T10:17:51.461478 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.56 | +1.03 | 0.47 | 819 |
| 2026-05-29T10:18:00.187681 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.08 | +1.08 | 0.0 | 1048 |
| 2026-05-29T10:18:00.575844 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.36 | +1.36 | 0.0 | 103 |
| 2026-05-29T10:18:06.771816 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.67 | +3.86 | 0.19 | 1953 |
| 2026-05-29T10:18:06.893054 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.51 | +0.76 | 0.25 | 508 |
| 2026-05-29T10:18:34.265626 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.04 | +3.13 | 0.09 | 992 |
| 2026-05-29T10:18:38.367922 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.72 | +1.72 | 0.0 | 141 |
| 2026-05-29T10:18:43.402886 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.42 | 0.08 | 1002 |
| 2026-05-29T10:19:01.039731 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +1.80 | 0.0 | 1108 |
| 2026-05-29T10:19:01.101830 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.13 | +3.13 | 0.0 | 1019 |
| 2026-05-29T10:19:02.633324 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.54 | +1.72 | 0.18 | 165 |
| 2026-05-29T10:19:07.442442 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.20 | +5.20 | 0.0 | 1058 |
| 2026-05-29T10:19:07.487829 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.19 | +1.19 | 0.0 | 895 |
| 2026-05-29T10:19:13.490564 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.58 | 0.16 | 1032 |
| 2026-05-29T10:19:23.101562 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 359 |
| 2026-05-29T10:19:28.393038 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.26 | 0.59 | 1117 |
| 2026-05-29T10:19:36.234137 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.31 | +3.31 | 0.0 | 199 |
| 2026-05-29T10:19:39.581728 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.44 | 0.14 | 1154 |
| 2026-05-29T10:19:39.657519 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.42 | +5.86 | 0.44 | 1090 |
| 2026-05-29T10:19:39.688388 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.05 | +2.05 | 0.0 | 927 |
| 2026-05-29T10:19:40.090671 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.04 | -0.04 | 0.0 | 45 |
| 2026-05-29T10:19:45.992189 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.58 | 0.16 | 1064 |
| 2026-05-29T10:20:18.419356 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.89 | +2.36 | 0.47 | 966 |
| 2026-05-29T10:20:18.889368 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.70 | 0.18 | 83 |
| 2026-05-29T10:20:23.343813 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.42 | 0.76 | 1797 |
| 2026-05-29T10:20:23.509776 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.58 | 0.16 | 1102 |
| 2026-05-29T10:20:23.603251 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.51 | +0.76 | 0.25 | 645 |
| 2026-05-29T10:20:45.027341 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +0.69 | 0.0 | 1219 |
| 2026-05-29T10:20:59.725420 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.58 | 0.16 | 1138 |
| 2026-05-29T10:20:59.759954 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.65 | +1.13 | 0.48 | 456 |
| 2026-05-29T10:21:04.085379 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.26 | +0.26 | 0.0 | 1213 |
| 2026-05-29T10:21:07.090192 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.09 | +5.38 | 0.29 | 1145 |
| 2026-05-29T10:21:07.273202 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.46 | +0.46 | 0.0 | 26 |
| 2026-05-29T10:21:34.442433 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.58 | 0.0 | 1173 |
| 2026-05-29T10:21:49.274398 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.13 | +2.36 | 0.23 | 1057 |
| 2026-05-29T10:22:08.490260 | 예스티(122640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.46 | +0.81 | 0.35 | 88 |
| 2026-05-29T10:22:15.378250 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.28 | +5.38 | 0.1 | 1214 |
| 2026-05-29T10:22:15.396745 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.29 | +2.36 | 0.07 | 1083 |
| 2026-05-29T10:22:18.837843 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.65 | +1.13 | 0.48 | 535 |
| 2026-05-29T10:22:26.637020 | RISE 메타버스(401170) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +0.72 | 0.03 | 1321 |
| 2026-05-29T10:22:39.585145 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.39 | +0.39 | 0.0 | 43 |
| 2026-05-29T10:43:04.833606 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.89 | +4.89 | 0.0 | 1781 |
| 2026-05-29T10:43:04.852429 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.65 | +0.65 | 0.0 | 1719 |
| 2026-05-29T10:43:06.386144 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.04 | -0.04 | 0.0 | 1451 |
| 2026-05-29T10:44:50.132209 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +0.97 | 0.0 | 3263 |
| 2026-05-29T10:44:50.138086 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.80 | 0.29 | 2657 |
| 2026-05-29T10:44:50.165170 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.70 | 0.18 | 1555 |
| 2026-05-29T10:44:57.736154 | 유라클(088340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.52 | +2.62 | 0.1 | 2646 |
| 2026-05-29T10:44:57.755959 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 2576 |
| 2026-05-29T10:44:57.796649 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 2576 |
| 2026-05-29T10:44:57.822693 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.51 | 0.0 | 2119 |
| 2026-05-29T10:44:57.860224 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | -0.33 | 0.0 | 1382 |
| 2026-05-29T10:44:57.896728 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.04 | -0.04 | 0.0 | 108 |
| 2026-05-29T10:45:17.708813 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.13 | +2.13 | 0.0 | 2465 |
| 2026-05-29T10:45:29.690904 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.94 | +0.94 | 0.0 | 1379 |
| 2026-05-29T10:45:37.863066 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.65 | 0.29 | 1872 |
| 2026-05-29T10:45:43.232405 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.51 | +1.80 | 0.29 | 2711 |
| 2026-05-29T10:45:48.845118 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.13 | +2.44 | 0.31 | 2497 |
| 2026-05-29T10:46:09.915086 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 2311 |
| 2026-05-29T10:46:13.542227 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.80 | 0.29 | 2741 |
| 2026-05-29T10:46:16.554998 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.26 | +1.51 | 0.25 | 2198 |
| 2026-05-29T10:46:24.750962 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 195 |
| 2026-05-29T10:46:35.109658 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +0.97 | 0.11 | 3368 |
| 2026-05-29T10:46:41.181095 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 2343 |
| 2026-05-29T10:46:42.493620 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 144 |
| 2026-05-29T10:46:48.752011 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.80 | 0.29 | 2776 |
| 2026-05-29T10:46:50.783433 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.26 | +1.51 | 0.25 | 2232 |
| 2026-05-29T10:46:54.119193 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.29 | +1.29 | 0.0 | 1463 |
| 2026-05-29T10:47:12.652335 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 243 |
| 2026-05-29T10:47:53.900906 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.60 | 0.0 | 284 |
| 2026-05-29T10:47:53.929134 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 284 |
| 2026-05-29T10:48:00.448737 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 2759 |
| 2026-05-29T10:48:05.686909 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.51 | 0.0 | 2307 |
| 2026-05-29T10:53:48.255382 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.57 | +2.57 | 0.0 | 2093 |
| 2026-05-29T10:53:48.270323 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.14 | -0.14 | 0.0 | 1979 |
| 2026-05-29T10:53:48.310974 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.16 | +2.16 | 0.0 | 1912 |
| 2026-05-29T10:53:48.326978 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.64 | +1.64 | 0.0 | 1877 |
| 2026-05-29T10:53:51.157997 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 642 |
| 2026-05-29T10:53:51.188217 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 589 |
| 2026-05-29T10:53:51.197924 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 572 |
| 2026-05-29T10:53:51.216701 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.07 | -0.07 | 0.0 | 339 |
| 2026-05-29T10:54:23.065565 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.53 | 0.11 | 3836 |
| 2026-05-29T10:54:23.118713 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | -0.01 | 0.0 | 3230 |
| 2026-05-29T10:54:23.171747 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 2805 |
| 2026-05-29T10:54:23.191597 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.24 | +3.49 | 0.25 | 2685 |
| 2026-05-29T10:54:23.227090 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.95 | +2.95 | 0.0 | 2128 |
| 2026-05-29T10:54:23.236034 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.14 | 0.09 | 2014 |
| 2026-05-29T10:54:23.245067 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.37 | +2.37 | 0.0 | 1947 |
| 2026-05-29T10:54:23.264674 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.64 | +1.64 | 0.0 | 1912 |
| 2026-05-29T10:54:54.613626 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 403 |
| 2026-05-29T10:54:56.280714 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.53 | +0.53 | 0.0 | 3869 |
| 2026-05-29T10:54:57.540828 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 2839 |
| 2026-05-29T10:54:57.569560 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.76 | +3.13 | 0.37 | 2162 |
| 2026-05-29T10:54:59.161321 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 3177 |
| 2026-05-29T10:55:02.213036 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.24 | +3.49 | 0.25 | 2724 |
| 2026-05-29T10:55:02.252141 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.68 | +3.00 | 0.32 | 1986 |
| 2026-05-29T10:55:09.257187 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.38 | -0.38 | 0.0 | 2444 |
| 2026-05-29T10:55:17.321015 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.87 | +1.87 | 0.0 | 1966 |
| 2026-05-29T10:55:36.234407 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | +0.23 | 0.28 | 2087 |
| 2026-05-29T10:55:37.938894 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.47 | 0.08 | 3216 |
| 2026-05-29T10:55:37.970856 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.49 | 0.49 | 2759 |
| 2026-05-29T10:55:39.667143 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 2474 |
| 2026-05-29T10:55:51.448979 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.87 | +1.87 | 0.0 | 2000 |
| 2026-05-29T10:55:57.527593 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +0.97 | 0.0 | 3931 |
| 2026-05-29T10:55:57.548931 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 2899 |
| 2026-05-29T10:55:57.564659 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.76 | +3.13 | 0.37 | 2222 |
| 2026-05-29T10:56:05.513991 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 3333 |
| 2026-05-29T10:56:09.878669 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.26 | +1.58 | 0.32 | 3118 |
| 2026-05-29T10:56:09.922932 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.49 | 0.49 | 2791 |
| 2026-05-29T10:56:12.933732 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 2508 |
| 2026-05-29T10:56:12.959254 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.20 | +3.20 | 0.0 | 2057 |
| 2026-05-29T10:56:18.303424 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 3257 |
| 2026-05-29T10:56:18.436456 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.25 | +0.25 | 0.0 | 789 |
| 2026-05-29T10:56:18.447879 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | -0.02 | 0.11 | 737 |
| 2026-05-29T10:56:18.471009 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 720 |
| 2026-05-29T10:56:42.881931 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.49 | 0.49 | 2824 |
| 2026-05-29T10:56:47.628171 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.79 | +3.20 | 0.41 | 2091 |
| 2026-05-29T10:56:49.259901 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 820 |
| 2026-05-29T10:56:51.067638 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.19 | 0.49 | 519 |
| 2026-05-29T10:56:52.668474 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.83 | 0.47 | 180 |
| 2026-05-29T10:56:58.772754 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.75 | 0.14 | 2960 |
| 2026-05-29T10:57:12.691753 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | +0.35 | 0.43 | 3400 |
| 2026-05-29T10:57:15.547003 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.79 | +3.20 | 0.41 | 2119 |
| 2026-05-29T10:57:20.173088 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.49 | 0.0 | 851 |
| 2026-05-29T10:57:22.871524 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.38 | 0.0 | 54 |
| 2026-05-29T10:57:24.372817 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.87 | +1.87 | 0.0 | 2093 |
| 2026-05-29T10:57:41.208756 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.66 | +1.66 | 0.0 | 3209 |
| 2026-05-29T10:57:51.159118 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.20 | 0.2 | 2155 |
| 2026-05-29T10:57:53.980693 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.80 | +1.19 | 0.39 | 582 |
| 2026-05-29T10:57:58.755761 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.64 | +1.87 | 0.23 | 2128 |
| 2026-05-29T10:58:00.374466 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.49 | 0.12 | 891 |
| 2026-05-29T10:58:02.122490 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.51 | +3.51 | 0.0 | 2347 |
| 2026-05-29T10:58:03.756900 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.83 | 0.35 | 251 |
| 2026-05-29T10:58:11.417293 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.66 | +1.74 | 0.08 | 3239 |
| 2026-05-29T10:58:34.800216 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.10 | +3.20 | 0.1 | 2198 |
| 2026-05-29T10:58:34.829429 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.91 | +1.19 | 0.28 | 623 |
| 2026-05-29T10:58:36.414371 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.55 | 0.0 | 3395 |
| 2026-05-29T10:58:36.433870 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.38 | +0.06 | 0.44 | 2651 |
| 2026-05-29T10:58:36.443486 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.44 | +4.44 | 0.0 | 2381 |
| 2026-05-29T10:58:36.463280 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.49 | 0.12 | 927 |
| 2026-05-29T10:58:36.481806 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.83 | 0.47 | 284 |
| 2026-05-29T10:59:14.711861 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.49 | 0.12 | 965 |
| 2026-05-29T10:59:14.736655 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.19 | 0.49 | 663 |
| 2026-05-29T10:59:14.758525 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.77 | +1.77 | 0.0 | 322 |
| 2026-05-29T11:04:50.179465 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 2641 |
| 2026-05-29T11:04:50.211483 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.62 | +3.62 | 0.0 | 2574 |
| 2026-05-29T11:04:50.228378 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 2539 |
| 2026-05-29T11:04:50.245772 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.14 | +0.14 | 0.0 | 1301 |
| 2026-05-29T11:04:50.261928 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 1301 |
| 2026-05-29T11:04:50.282212 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | -0.33 | 0.0 | 1249 |
| 2026-05-29T11:04:50.330418 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.35 | +1.35 | 0.0 | 998 |
| 2026-05-29T11:04:50.340087 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.13 | +4.13 | 0.0 | 658 |
| 2026-05-29T11:04:50.360325 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.52 | 0.0 | 502 |
| 2026-05-29T11:05:10.152241 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.20 | +3.62 | 0.42 | 2594 |
| 2026-05-29T11:05:12.028225 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.59 | +0.59 | 0.0 | 2561 |
| 2026-05-29T11:05:12.082054 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.24 | +1.35 | 0.11 | 1020 |
| 2026-05-29T11:05:12.129017 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.66 | +4.13 | 0.47 | 679 |
| 2026-05-29T11:05:12.148569 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.52 | 0.07 | 524 |
| 2026-05-29T11:05:21.005967 | 엠로(058970) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.75 | +5.75 | 0.0 | 2786 |
| 2026-05-29T11:05:21.047053 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 1262 |
| 2026-05-29T11:05:56.665136 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 1367 |
| 2026-05-29T11:06:01.547938 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +0.86 | 0.0 | 573 |
| 2026-05-29T11:06:03.462451 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.55 | 0.32 | 3842 |
| 2026-05-29T11:06:17.095521 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3518 |
| 2026-05-29T11:06:30.222663 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.66 | +4.13 | 0.47 | 757 |
| 2026-05-29T11:06:31.745021 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +0.86 | 0.14 | 603 |
| 2026-05-29T11:06:34.860927 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.55 | 0.32 | 3873 |
| 2026-05-29T11:06:41.240899 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.06 | 0.29 | 3969 |
| 2026-05-29T11:06:41.309489 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.23 | -0.14 | 0.09 | 2752 |
| 2026-05-29T11:07:00.911387 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.70 | 0.19 | 1431 |
| 2026-05-29T11:07:03.662791 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +0.86 | 0.07 | 635 |
| 2026-05-29T11:07:05.480804 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.55 | 0.49 | 3904 |
| 2026-05-29T11:07:07.154694 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.41 | +3.72 | 0.31 | 2711 |
| 2026-05-29T11:07:13.288433 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.14 | -0.14 | 0.0 | 2784 |
| 2026-05-29T11:07:13.329823 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 1444 |
| 2026-05-29T11:07:15.241195 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 3913 |
| 2026-05-29T11:07:29.031732 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +0.70 | 0.0 | 1459 |
| 2026-05-29T11:07:29.058173 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.72 | +0.86 | 0.14 | 660 |
| 2026-05-29T11:07:35.934482 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.08 | +1.40 | 0.32 | 4629 |
| 2026-05-29T11:07:36.073646 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.99 | +1.35 | 0.36 | 1164 |
| 2026-05-29T11:07:39.022959 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.55 | 0.49 | 3937 |
| 2026-05-29T11:07:39.041774 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3600 |
| 2026-05-29T11:07:40.458027 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.70 | 0.23 | 2709 |
| 2026-05-29T11:07:42.280652 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.14 | 0.09 | 2813 |
| 2026-05-29T11:08:14.226265 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.70 | 0.35 | 2743 |
| 2026-05-29T11:08:17.139849 | LG(003550) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.19 | +1.66 | 0.47 | 3845 |
| 2026-05-29T11:08:18.550874 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 1440 |
| 2026-05-29T11:08:31.065206 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.86 | 0.44 | 722 |
| 2026-05-29T11:08:46.455029 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +0.89 | 0.21 | 3668 |
| 2026-05-29T11:08:48.370706 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.75 | +3.00 | 0.25 | 3550 |
| 2026-05-29T11:09:29.944194 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.06 | 0.51 | 4137 |
| 2026-05-29T11:09:40.666054 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +1.07 | 0.47 | 1591 |
| 2026-05-29T11:10:07.856658 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3749 |
| 2026-05-29T11:10:19.266001 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.86 | 0.48 | 831 |
| 2026-05-29T11:10:34.774467 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.00 | 0.0 | 3656 |
| 2026-05-29T11:10:34.873010 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.62 | +3.83 | 0.21 | 2919 |
| 2026-05-29T11:10:36.236728 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.32 | +1.56 | 0.24 | 1647 |
| 2026-05-29T11:10:44.774455 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3786 |
| 2026-05-29T11:11:15.558187 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +1.07 | 0.1 | 1686 |
| 2026-05-29T11:11:15.620663 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 362 |
| 2026-05-29T11:11:17.571202 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 1619 |
| 2026-05-29T11:11:19.428837 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3821 |
| 2026-05-29T11:11:47.611604 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.22 | 0.0 | 4275 |
| 2026-05-29T11:11:48.780740 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.16 | +1.16 | 0.0 | 1719 |
| 2026-05-29T11:12:02.010511 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.62 | +3.83 | 0.21 | 3006 |
| 2026-05-29T11:12:03.838029 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.95 | +2.06 | 0.11 | 4897 |
| 2026-05-29T11:12:12.476167 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.17 | 0.47 | 419 |
| 2026-05-29T11:12:20.743194 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.37 | +1.37 | 0.0 | 4308 |
| 2026-05-29T11:12:22.044363 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.07 | +1.25 | 0.18 | 1752 |
| 2026-05-29T11:12:28.425436 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 128 |
| 2026-05-29T11:12:30.156308 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.61 | +0.89 | 0.28 | 3892 |
| 2026-05-29T11:12:31.948716 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.52 | +3.83 | 0.31 | 3036 |
| 2026-05-29T11:17:39.953449 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.07 | +1.07 | 0.0 | 2070 |
| 2026-05-29T11:17:39.981681 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.44 | +1.44 | 0.0 | 2070 |
| 2026-05-29T11:17:41.249799 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 2003 |
| 2026-05-29T11:17:41.278041 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 1769 |
| 2026-05-29T11:17:41.331127 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.70 | +2.70 | 0.0 | 1273 |
| 2026-05-29T11:17:41.352766 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +0.70 | 0.0 | 748 |
| 2026-05-29T11:18:09.217694 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.07 | +1.07 | 0.0 | 2100 |
| 2026-05-29T11:18:09.261236 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.53 | +0.53 | 0.0 | 1797 |
| 2026-05-29T11:18:09.279132 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.63 | +2.70 | 0.07 | 1301 |
| 2026-05-29T11:18:47.885943 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +0.86 | 0.0 | 4695 |
| 2026-05-29T11:18:59.841587 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +0.91 | 0.05 | 1848 |
| 2026-05-29T11:18:59.870035 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.35 | 0.0 | 519 |
| 2026-05-29T11:19:16.356817 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.15 | +1.15 | 0.0 | 4724 |
| 2026-05-29T11:19:21.739428 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.42 | 0.0 | 541 |
| 2026-05-29T11:19:29.644222 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | -0.08 | 0.0 | 3904 |
| 2026-05-29T11:19:49.641905 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.24 | +3.49 | 0.25 | 4211 |
| 2026-05-29T11:19:51.076375 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.42 | 0.0 | 570 |
| 2026-05-29T11:19:58.232165 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.89 | +1.31 | 0.42 | 4340 |
| 2026-05-29T11:19:59.781946 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | -0.08 | 0.08 | 3934 |
| 2026-05-29T11:20:01.630824 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.39 | 0.33 | 4680 |
| 2026-05-29T11:20:07.829902 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.92 | +1.92 | 0.0 | 2218 |
| 2026-05-29T11:20:07.851760 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.14 | -0.05 | 0.09 | 2149 |
| 2026-05-29T11:20:15.781163 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.23 | 0.25 | 595 |
| 2026-05-29T11:20:19.307112 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.24 | +3.49 | 0.25 | 4241 |
| 2026-05-29T11:20:21.953651 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.42 | 0.0 | 601 |
| 2026-05-29T11:20:25.015170 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.71 | +1.15 | 0.44 | 4792 |
| 2026-05-29T11:20:30.976850 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | -0.08 | 0.0 | 3966 |
| 2026-05-29T11:20:33.958611 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.53 | +1.53 | 0.0 | 2244 |
| 2026-05-29T11:20:41.326172 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.17 | +2.17 | 0.0 | 5415 |
| 2026-05-29T11:20:41.376525 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.89 | +1.31 | 0.42 | 4383 |
| 2026-05-29T11:20:47.642989 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.28 | +1.39 | 0.11 | 139 |
| 2026-05-29T11:20:50.981580 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.24 | +3.49 | 0.25 | 4272 |
| 2026-05-29T11:20:51.055985 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.23 | 0.19 | 630 |
| 2026-05-29T11:21:06.962360 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.53 | +1.53 | 0.0 | 2277 |
| 2026-05-29T11:21:10.004505 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.71 | +1.15 | 0.44 | 4837 |
| 2026-05-29T11:21:11.549002 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.89 | +1.31 | 0.42 | 4413 |
| 2026-05-29T11:21:23.363416 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.49 | 0.49 | 4305 |
| 2026-05-29T11:21:31.249880 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +2.17 | +2.17 | 0.0 | 5464 |
| 2026-05-29T11:21:49.578315 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.34 | 0.0 | 185 |
| 2026-05-29T11:21:51.428142 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.52 | +1.87 | 0.35 | 998 |
| 2026-05-29T11:21:53.057165 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.71 | +1.15 | 0.44 | 4880 |
| 2026-05-29T11:21:53.083542 | 한글과컴퓨터(030520) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.00 | +3.49 | 0.49 | 4334 |
| 2026-05-29T11:22:15.081262 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.69 | 0.12 | 210 |
| 2026-05-29T11:22:31.958177 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.23 | 0.19 | 731 |
| 2026-05-29T11:22:35.121644 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.25 | +1.62 | 0.37 | 2366 |
| 2026-05-29T11:22:44.651574 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.62 | +1.62 | 0.0 | 2073 |
| 2026-05-29T11:23:33.836728 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.89 | +1.89 | 0.0 | 2122 |
| 2026-05-29T11:23:33.852951 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.40 | +1.87 | 0.47 | 1100 |
| 2026-05-29T11:23:47.448144 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.35 | 0.0 | 3676 |
| 2026-05-29T11:23:47.480039 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.90 | +2.09 | 0.19 | 807 |
| 2026-05-29T11:23:49.450652 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.36 | +2.36 | 0.0 | 321 |
| 2026-05-29T11:23:58.061180 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +1.92 | 0.12 | 2448 |
| 2026-05-29T11:23:58.074006 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.89 | +1.95 | 0.06 | 2146 |
| 2026-05-29T11:24:36.872218 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.84 | +2.17 | 0.33 | 5650 |
| 2026-05-29T11:24:46.143883 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +1.31 | 0.49 | 4628 |
| 2026-05-29T11:24:53.081899 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +1.92 | 0.12 | 2503 |
| 2026-05-29T11:25:01.841800 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.68 | +1.95 | 0.27 | 2210 |
| 2026-05-29T11:25:10.741876 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.28 | +2.28 | 0.0 | 5684 |
| 2026-05-29T11:25:25.106014 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | -0.11 | 0.0 | 3774 |
| 2026-05-29T11:25:25.117959 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +1.92 | 0.12 | 2536 |
| 2026-05-29T11:25:25.159336 | 데이타솔루션(263800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.71 | +2.09 | 0.38 | 904 |
| 2026-05-29T11:25:41.559780 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.49 | +2.49 | 0.0 | 5715 |
| 2026-05-29T11:25:52.359274 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.51 | 0.0 | 4287 |
| 2026-05-29T11:25:58.283285 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.11 | 0.24 | 3807 |
| 2026-05-29T11:25:58.313333 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.03 | +2.03 | 0.0 | 2569 |
| 2026-05-29T11:26:12.364361 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.60 | +2.60 | 0.0 | 5746 |
| 2026-05-29T11:26:12.485150 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.05 | 0.18 | 2514 |
| 2026-05-29T11:26:18.319452 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.80 | +0.95 | 0.15 | 4313 |
| 2026-05-29T11:26:27.699313 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +2.03 | 0.23 | 2598 |
| 2026-05-29T11:26:33.110279 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.35 | -0.11 | 0.24 | 3842 |
| 2026-05-29T11:26:43.380608 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.49 | +2.60 | 0.11 | 5777 |
| 2026-05-29T11:26:51.054628 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.95 | +0.95 | 0.0 | 4346 |
| 2026-05-29T11:26:51.162119 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.93 | +2.36 | 0.43 | 503 |
| 2026-05-29T11:27:00.145506 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +2.03 | 0.23 | 2631 |
| 2026-05-29T11:27:06.480265 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.11 | 0.12 | 3875 |
| 2026-05-29T11:27:21.053329 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.28 | +2.60 | 0.32 | 5814 |
| 2026-05-29T11:27:21.092589 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.24 | +1.24 | 0.0 | 4376 |
| 2026-05-29T11:27:29.283206 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.79 | +1.15 | 0.36 | 5217 |
| 2026-05-29T11:27:54.635836 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2616 |
| 2026-05-29T11:28:02.137401 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.60 | +2.60 | 0.0 | 5855 |
| 2026-05-29T11:28:02.158189 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 4417 |
| 2026-05-29T11:28:14.233220 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.11 | 0.24 | 3943 |
| 2026-05-29T11:28:21.781866 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2643 |
| 2026-05-29T11:28:23.745053 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +2.03 | 0.23 | 2714 |
| 2026-05-29T11:28:33.218617 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.49 | +2.60 | 0.11 | 5886 |
| 2026-05-29T11:28:33.256521 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.10 | +1.39 | 0.29 | 4448 |
| 2026-05-29T11:28:49.823954 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | +0.00 | 0.11 | 3979 |
| 2026-05-29T11:28:58.839102 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +1.15 | 0.29 | 5306 |
| 2026-05-29T11:28:58.902688 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2680 |
| 2026-05-29T11:29:08.032729 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.82 | +2.82 | 0.0 | 5921 |
| 2026-05-29T11:29:08.050783 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 4483 |
| 2026-05-29T11:29:30.045615 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.93 | +1.15 | 0.22 | 5337 |
| 2026-05-29T11:29:30.130216 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2711 |
| 2026-05-29T11:29:33.777212 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.68 | +1.11 | 0.43 | 163 |
| 2026-05-29T11:29:35.765101 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.60 | +2.82 | 0.22 | 5949 |
| 2026-05-29T11:29:35.802036 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 4510 |
| 2026-05-29T11:29:35.958527 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.18 | 0.16 | 240 |
| 2026-05-29T11:30:00.574053 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2742 |
| 2026-05-29T11:30:09.634736 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.10 | +1.39 | 0.29 | 4544 |
| 2026-05-29T11:30:14.572630 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.23 | 0.11 | 252 |
| 2026-05-29T11:30:18.333089 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.56 | +2.03 | 0.47 | 2829 |
| 2026-05-29T11:30:40.559886 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.10 | +1.39 | 0.29 | 4575 |
| 2026-05-29T11:30:42.337637 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.04 | +3.04 | 0.0 | 6016 |
| 2026-05-29T11:30:53.257999 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 290 |
| 2026-05-29T11:31:00.981728 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2802 |
| 2026-05-29T11:31:01.053034 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.05 | +0.05 | 0.0 | 185 |
| 2026-05-29T11:31:13.565309 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 165 |
| 2026-05-29T11:31:15.573266 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.04 | +3.15 | 0.11 | 6049 |
| 2026-05-29T11:31:15.621213 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.10 | +1.39 | 0.29 | 4610 |
| 2026-05-29T11:31:15.765956 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.65 | 0.0 | 265 |
| 2026-05-29T11:31:24.366450 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 322 |
| 2026-05-29T11:31:32.415791 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2834 |
| 2026-05-29T11:31:32.482247 | 씨이랩(189330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.40 | +0.40 | 0.0 | 148 |
| 2026-05-29T11:31:41.768396 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 193 |
| 2026-05-29T11:31:50.315117 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.65 | 0.0 | 300 |
| 2026-05-29T11:31:58.828430 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 356 |
| 2026-05-29T11:32:04.868157 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2866 |
| 2026-05-29T11:32:04.997576 | 씨이랩(189330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.57 | 0.0 | 180 |
| 2026-05-29T11:32:19.437557 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.65 | 0.0 | 329 |
| 2026-05-29T11:32:27.548018 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 385 |
| 2026-05-29T11:32:41.578560 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2903 |
| 2026-05-29T11:32:41.613791 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.30 | -0.18 | 0.12 | 426 |
| 2026-05-29T11:32:41.716636 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 253 |
| 2026-05-29T11:32:41.726116 | 씨이랩(189330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.75 | 0.09 | 217 |
| 2026-05-29T11:32:43.849203 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 4698 |
| 2026-05-29T11:32:43.879675 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 4213 |
| 2026-05-29T11:33:03.374394 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.08 | +1.15 | 0.07 | 5551 |
| 2026-05-29T11:33:03.472842 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | -0.12 | 0.0 | 421 |
| 2026-05-29T11:33:11.355750 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 2933 |
| 2026-05-29T11:33:11.384284 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.27 | -0.18 | 0.09 | 456 |
| 2026-05-29T11:33:11.404572 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 282 |
| 2026-05-29T11:33:20.167093 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 4249 |
| 2026-05-29T11:33:23.082156 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.90 | +2.08 | 0.18 | 392 |
| 2026-05-29T11:33:30.962043 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.15 | +1.15 | 0.0 | 5578 |
| 2026-05-29T11:33:31.114334 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | -0.01 | 0.0 | 448 |
| 2026-05-29T11:33:59.823033 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.71 | +3.15 | 0.44 | 6213 |
| 2026-05-29T11:34:01.366781 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | -0.14 | 0.27 | 4392 |
| 2026-05-29T11:34:01.381903 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 4290 |
| 2026-05-29T11:34:04.066701 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.38 | +2.44 | 0.06 | 433 |
| 2026-05-29T11:34:05.958358 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.37 | +1.37 | 0.0 | 5613 |
| 2026-05-29T11:34:07.805417 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.01 | -0.01 | 0.0 | 485 |
| 2026-05-29T11:34:12.007447 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.44 | 0.0 | 343 |
| 2026-05-29T11:34:33.758597 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.41 | -0.14 | 0.27 | 4424 |
| 2026-05-29T11:34:41.849468 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.37 | 0.15 | 5649 |
| 2026-05-29T11:34:43.014954 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 3024 |
| 2026-05-29T11:34:44.733026 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.58 | 0.0 | 376 |
| 2026-05-29T11:34:57.415573 | 아나패스(123860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.23 | 0.21 | 186 |
| 2026-05-29T11:34:59.107040 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.93 | +3.15 | 0.22 | 6272 |
| 2026-05-29T11:34:59.211516 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | -0.14 | 0.27 | 4450 |
| 2026-05-29T11:35:00.612336 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.93 | +3.11 | 0.18 | 490 |
| 2026-05-29T11:35:07.026246 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.10 | 0.11 | 544 |
| 2026-05-29T11:35:13.028849 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.22 | +1.37 | 0.15 | 5680 |
| 2026-05-29T11:35:14.243725 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 3056 |
| 2026-05-29T11:35:14.433518 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.58 | 0.27 | 406 |
| 2026-05-29T11:35:18.075251 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.47 | 0.17 | 4367 |
| 2026-05-29T11:35:34.162559 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.29 | +3.72 | 0.43 | 524 |
| 2026-05-29T11:35:34.219917 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.22 | +0.22 | 0.0 | 185 |
| 2026-05-29T11:35:38.143195 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.10 | 0.11 | 575 |
| 2026-05-29T11:35:47.474935 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.50 | 0.09 | 3089 |
| 2026-05-29T11:35:47.658103 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.31 | +0.58 | 0.27 | 439 |
| 2026-05-29T11:35:49.353863 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4398 |
| 2026-05-29T11:36:06.449491 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.19 | +0.19 | 0.0 | 490 |
| 2026-05-29T11:36:08.456796 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.21 | 0.22 | 606 |
| 2026-05-29T11:36:14.233430 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +0.69 | 0.0 | 3116 |
| 2026-05-29T11:36:14.433667 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.58 | 0.14 | 466 |
| 2026-05-29T11:36:16.175831 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.15 | +3.15 | 0.0 | 6349 |
| 2026-05-29T11:36:18.037738 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.34 | 0.0 | 229 |
| 2026-05-29T11:36:19.706224 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4429 |
| 2026-05-29T11:36:41.156852 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.83 | +1.83 | 0.0 | 4936 |
| 2026-05-29T11:36:41.327768 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.29 | +0.29 | 0.0 | 182 |
| 2026-05-29T11:36:49.167509 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.08 | +1.37 | 0.29 | 5777 |
| 2026-05-29T11:36:49.280150 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +0.69 | 0.0 | 3151 |
| 2026-05-29T11:36:49.373510 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.71 | +0.71 | 0.0 | 500 |
| 2026-05-29T11:36:49.453528 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.40 | +0.40 | 0.0 | 260 |
| 2026-05-29T11:36:51.072476 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 4460 |
| 2026-05-29T11:37:15.734692 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.41 | +3.72 | 0.31 | 625 |
| 2026-05-29T11:37:17.359641 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.69 | +1.83 | 0.14 | 4972 |
| 2026-05-29T11:37:18.947184 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.00 | +1.37 | 0.37 | 5806 |
| 2026-05-29T11:37:18.976441 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +0.69 | 0.0 | 3180 |
| 2026-05-29T11:37:19.033439 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.71 | +0.85 | 0.14 | 530 |
| 2026-05-29T11:37:19.046640 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.44 | 0.0 | 290 |
| 2026-05-29T11:37:19.056282 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 220 |
| 2026-05-29T11:37:22.392989 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4491 |
| 2026-05-29T11:37:31.567913 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.28 | -0.09 | 0.19 | 184 |
| 2026-05-29T11:37:33.364279 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.36 | +3.36 | 0.0 | 6427 |
| 2026-05-29T11:37:40.422601 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.10 | +0.21 | 0.11 | 698 |
| 2026-05-29T11:37:47.414066 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.18 | 0.2 | 3226 |
| 2026-05-29T11:37:47.504513 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.78 | +5.78 | 0.0 | 657 |
| 2026-05-29T11:37:50.607428 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.69 | +1.83 | 0.14 | 5005 |
| 2026-05-29T11:37:50.636148 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.87 | +0.87 | 0.0 | 3212 |
| 2026-05-29T11:37:50.765189 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.71 | +0.85 | 0.14 | 562 |
| 2026-05-29T11:37:50.803861 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.53 | 0.05 | 322 |
| 2026-05-29T11:37:55.825991 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4525 |
| 2026-05-29T11:38:25.184665 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.83 | +1.83 | 0.0 | 5040 |
| 2026-05-29T11:38:25.229746 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.87 | +0.87 | 0.0 | 3247 |
| 2026-05-29T11:38:26.684546 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.85 | 0.27 | 598 |
| 2026-05-29T11:38:26.749690 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.44 | +0.53 | 0.09 | 358 |
| 2026-05-29T11:38:28.225234 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.12 | +0.21 | 0.33 | 745 |
| 2026-05-29T11:38:37.415235 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4566 |
| 2026-05-29T11:39:08.569548 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.87 | +0.87 | 0.0 | 3290 |
| 2026-05-29T11:39:08.646450 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.49 | 0.0 | 981 |
| 2026-05-29T11:39:10.136189 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.27 | -0.10 | 0.17 | 815 |
| 2026-05-29T11:39:10.162503 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 674 |
| 2026-05-29T11:39:10.180573 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.98 | +0.98 | 0.0 | 641 |
| 2026-05-29T11:39:10.274121 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.53 | 0.05 | 401 |
| 2026-05-29T11:39:31.248202 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 695 |
| 2026-05-29T11:39:31.275792 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.38 | +1.38 | 0.0 | 662 |
| 2026-05-29T11:39:31.328709 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.70 | 0.2 | 422 |
| 2026-05-29T11:39:55.153407 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.37 | 0.15 | 5963 |
| 2026-05-29T11:39:59.710642 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.67 | 0.18 | 1032 |
| 2026-05-29T11:39:59.733007 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 724 |
| 2026-05-29T11:39:59.750428 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.25 | +1.38 | 0.13 | 691 |
| 2026-05-29T11:39:59.769155 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.70 | 0.22 | 451 |
| 2026-05-29T11:39:59.846242 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.49 | 0.13 | 78 |
| 2026-05-29T11:40:20.464014 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.18 | 0.51 | 3379 |
| 2026-05-29T11:40:20.569876 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.29 | +0.47 | 0.18 | 401 |
| 2026-05-29T11:40:25.359955 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.51 | 0.0 | 5993 |
| 2026-05-29T11:40:31.446306 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.67 | 0.36 | 1064 |
| 2026-05-29T11:40:31.469212 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 755 |
| 2026-05-29T11:40:31.505172 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.11 | +1.38 | 0.27 | 723 |
| 2026-05-29T11:40:31.525927 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.70 | 0.12 | 482 |
| 2026-05-29T11:40:31.547295 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | -0.00 | 0.41 | 364 |
| 2026-05-29T11:40:54.828862 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.21 | +0.21 | 0.0 | 892 |
| 2026-05-29T11:40:56.467117 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.62 | +1.62 | 0.0 | 6024 |
| 2026-05-29T11:40:56.740575 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 437 |
| 2026-05-29T11:41:00.265434 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 4709 |
| 2026-05-29T11:41:03.542022 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.67 | 0.0 | 1096 |
| 2026-05-29T11:41:03.575056 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 787 |
| 2026-05-29T11:41:03.606014 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.25 | +1.38 | 0.13 | 755 |
| 2026-05-29T11:41:03.633275 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.58 | +0.70 | 0.12 | 514 |
| 2026-05-29T11:41:03.681135 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.68 | 0.26 | 142 |
| 2026-05-29T11:41:05.364260 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | -0.14 | 0.18 | 4816 |
| 2026-05-29T11:41:28.460480 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.44 | +1.62 | 0.18 | 6056 |
| 2026-05-29T11:41:28.656723 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 469 |
| 2026-05-29T11:41:35.083272 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.67 | 0.18 | 1127 |
| 2026-05-29T11:41:35.171680 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.54 | +0.61 | 0.07 | 819 |
| 2026-05-29T11:41:35.210591 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.65 | 0.0 | 786 |
| 2026-05-29T11:41:35.238911 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.70 | 0.1 | 546 |
| 2026-05-29T11:41:43.050501 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.18 | 0.41 | 3461 |
| 2026-05-29T11:41:46.460362 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 944 |
| 2026-05-29T11:41:49.856334 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3451 |
| 2026-05-29T11:42:01.243729 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.73 | +1.73 | 0.0 | 6089 |
| 2026-05-29T11:42:01.279432 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.13 | +2.13 | 0.0 | 5256 |
| 2026-05-29T11:42:01.465924 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.64 | +0.64 | 0.0 | 502 |
| 2026-05-29T11:42:01.555272 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | -0.07 | 0.4 | 184 |
| 2026-05-29T11:42:03.073169 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4772 |
| 2026-05-29T11:42:03.274761 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.36 | +0.68 | 0.32 | 202 |
| 2026-05-29T11:42:04.780069 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.69 | +3.69 | 0.0 | 6698 |
| 2026-05-29T11:42:06.880899 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.67 | 0.0 | 1159 |
| 2026-05-29T11:42:06.943872 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 851 |
| 2026-05-29T11:42:07.027388 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.79 | 0.14 | 818 |
| 2026-05-29T11:42:08.611084 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.70 | 0.1 | 579 |
| 2026-05-29T11:42:36.240128 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.69 | +3.69 | 0.0 | 6729 |
| 2026-05-29T11:42:36.269377 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4805 |
| 2026-05-29T11:42:36.350685 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.64 | 0.17 | 537 |
| 2026-05-29T11:42:36.372508 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.68 | 0.26 | 235 |
| 2026-05-29T11:42:40.480998 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 884 |
| 2026-05-29T11:42:40.508017 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.99 | +1.99 | 0.0 | 852 |
| 2026-05-29T11:42:41.756308 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.70 | 0.2 | 613 |
| 2026-05-29T11:42:54.254607 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3516 |
| 2026-05-29T11:43:07.749950 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.87 | 0.36 | 6155 |
| 2026-05-29T11:43:12.837009 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.67 | 0.0 | 1225 |
| 2026-05-29T11:43:12.888405 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 917 |
| 2026-05-29T11:43:12.931506 | 현대모비스(012330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.79 | +1.99 | 0.2 | 884 |
| 2026-05-29T11:43:15.722257 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.33 | +1.33 | 0.0 | 274 |
| 2026-05-29T11:43:18.759319 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.18 | 0.31 | 3557 |
| 2026-05-29T11:43:19.978866 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.21 | +0.32 | 0.11 | 1037 |
| 2026-05-29T11:43:24.325051 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3546 |
| 2026-05-29T11:43:39.731778 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.28 | +2.28 | 0.0 | 5354 |
| 2026-05-29T11:43:41.717231 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4871 |
| 2026-05-29T11:43:41.780991 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.61 | 0.14 | 946 |
| 2026-05-29T11:43:44.480578 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.51 | +2.51 | 0.0 | 303 |
| 2026-05-29T11:43:47.775644 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.13 | +0.18 | 0.31 | 3586 |
| 2026-05-29T11:44:04.554076 | 한온시스템(018880) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.67 | 0.36 | 1277 |
| 2026-05-29T11:44:11.746824 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.28 | +2.28 | 0.0 | 5386 |
| 2026-05-29T11:44:11.767892 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5002 |
| 2026-05-29T11:44:16.856101 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.61 | +3.61 | 0.0 | 335 |
| 2026-05-29T11:44:18.615617 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.35 | +0.47 | 0.12 | 4908 |
| 2026-05-29T11:44:18.629148 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.91 | +0.91 | 0.0 | 3617 |
| 2026-05-29T11:44:23.610969 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3605 |
| 2026-05-29T11:44:28.878698 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 6147 |
| 2026-05-29T11:44:46.083025 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.58 | +1.87 | 0.29 | 6253 |
| 2026-05-29T11:44:47.776701 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.88 | +3.88 | 0.0 | 366 |
| 2026-05-29T11:44:49.383599 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.91 | 0.31 | 3648 |
| 2026-05-29T11:44:53.984226 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3635 |
| 2026-05-29T11:45:09.635522 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.32 | 0.33 | 1147 |
| 2026-05-29T11:45:12.659676 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.57 | +2.72 | 0.15 | 5447 |
| 2026-05-29T11:45:15.824221 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.47 | +3.69 | 0.22 | 6889 |
| 2026-05-29T11:45:15.982848 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.88 | +3.88 | 0.0 | 394 |
| 2026-05-29T11:45:19.168673 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.91 | 0.42 | 3677 |
| 2026-05-29T11:45:44.347984 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.86 | +2.86 | 0.0 | 5479 |
| 2026-05-29T11:45:44.455063 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.32 | 0.33 | 1182 |
| 2026-05-29T11:45:50.183463 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +0.91 | 0.21 | 3708 |
| 2026-05-29T11:45:50.393039 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.88 | +3.88 | 0.0 | 429 |
| 2026-05-29T11:45:55.539848 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.06 | 0.0 | 3697 |
| 2026-05-29T11:46:13.942164 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.47 | +3.69 | 0.22 | 6947 |
| 2026-05-29T11:46:15.884647 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.86 | +2.86 | 0.0 | 5510 |
| 2026-05-29T11:46:23.905664 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.58 | +1.87 | 0.29 | 6351 |
| 2026-05-29T11:46:23.945448 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.91 | 0.31 | 3742 |
| 2026-05-29T11:46:24.062740 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.88 | +3.88 | 0.0 | 463 |
| 2026-05-29T11:46:48.682600 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.72 | +2.86 | 0.14 | 5543 |
| 2026-05-29T11:46:53.872905 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.91 | 0.42 | 3772 |
| 2026-05-29T11:46:54.049117 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.27 | +4.27 | 0.0 | 493 |
| 2026-05-29T11:46:59.062921 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 5068 |
| 2026-05-29T11:47:06.871054 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5177 |
| 2026-05-29T11:47:19.274466 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.64 | +2.86 | 0.22 | 5574 |
| 2026-05-29T11:47:19.389353 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 1277 |
| 2026-05-29T11:47:21.157954 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.80 | +3.80 | 0.0 | 7014 |
| 2026-05-29T11:47:24.926955 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.92 | +4.92 | 0.0 | 523 |
| 2026-05-29T11:47:29.938075 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 6328 |
| 2026-05-29T11:47:29.961586 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 5099 |
| 2026-05-29T11:47:38.287217 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5209 |
| 2026-05-29T11:47:57.740980 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.80 | +3.91 | 0.11 | 7051 |
| 2026-05-29T11:48:10.477364 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.09 | +2.09 | 0.0 | 6458 |
| 2026-05-29T11:48:23.573619 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 1341 |
| 2026-05-29T11:48:32.418163 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.91 | +3.91 | 0.0 | 7086 |
| 2026-05-29T11:48:32.470084 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5263 |
| 2026-05-29T11:48:32.862061 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.44 | +5.57 | 0.13 | 591 |
| 2026-05-29T11:48:41.342047 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.09 | +2.09 | 0.0 | 6489 |
| 2026-05-29T11:48:54.827976 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 1372 |
| 2026-05-29T11:49:02.670877 | 카카오페이(377300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.91 | +3.91 | 0.0 | 7116 |
| 2026-05-29T11:49:05.453732 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.03 | +6.03 | 0.0 | 624 |
| 2026-05-29T11:49:07.049134 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5298 |
| 2026-05-29T11:49:23.457187 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.43 | 0.11 | 1401 |
| 2026-05-29T11:49:28.126683 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.87 | +1.06 | 0.19 | 3909 |
| 2026-05-29T11:49:31.975506 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.02 | +2.16 | 0.14 | 6539 |
| 2026-05-29T11:49:44.668482 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.01 | +3.01 | 0.0 | 5719 |
| 2026-05-29T11:49:44.719214 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5335 |
| 2026-05-29T11:49:57.347199 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.43 | 0.11 | 1434 |
| 2026-05-29T11:50:09.880748 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.09 | +2.16 | 0.07 | 6577 |
| 2026-05-29T11:50:17.907440 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 5369 |
| 2026-05-29T11:50:17.921584 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.24 | +0.47 | 0.23 | 5267 |
| 2026-05-29T11:50:31.173169 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.43 | 0.11 | 1468 |
| 2026-05-29T11:50:37.313387 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.91 | 0.42 | 3996 |
| 2026-05-29T11:50:39.751913 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.02 | +2.16 | 0.14 | 6607 |
| 2026-05-29T11:50:50.279565 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 3992 |
| 2026-05-29T11:50:57.966592 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.90 | +3.90 | 0.0 | 5793 |
| 2026-05-29T11:51:04.071045 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.54 | 0.22 | 1501 |
| 2026-05-29T11:51:04.283748 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | -0.23 | 0.1 | 7 |
| 2026-05-29T11:51:07.804551 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.01 | +1.01 | 0.0 | 4026 |
| 2026-05-29T11:51:29.136710 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.02 | +2.16 | 0.14 | 6656 |
| 2026-05-29T11:51:29.163860 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.75 | +3.90 | 0.15 | 5824 |
| 2026-05-29T11:51:43.623979 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.73 | +2.15 | 0.42 | 4062 |
| 2026-05-29T11:51:43.638042 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.69 | +1.06 | 0.37 | 4045 |
| 2026-05-29T11:51:57.825885 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 5468 |
| 2026-05-29T11:51:59.437542 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.04 | +4.04 | 0.0 | 5854 |
| 2026-05-29T11:52:08.000871 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.76 | +0.76 | 0.0 | 1565 |
| 2026-05-29T11:52:14.782249 | 툴젠(199800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.04 | +2.15 | 0.11 | 4093 |
| 2026-05-29T11:52:31.379981 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 94 |
| 2026-05-29T11:52:34.275355 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.04 | +4.04 | 0.0 | 5889 |
| 2026-05-29T11:52:40.785167 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.76 | 0.44 | 1598 |
| 2026-05-29T11:52:58.755063 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 5529 |
| 2026-05-29T11:53:00.664935 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | +0.37 | 0.7 | 123 |
| 2026-05-29T11:53:05.515316 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.75 | +4.04 | 0.29 | 5920 |
| 2026-05-29T11:53:11.780252 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.76 | 0.44 | 1629 |
| 2026-05-29T11:53:15.243067 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.23 | 0.22 | 5 |
| 2026-05-29T11:53:16.851254 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.47 | 0.7 | 5446 |
| 2026-05-29T11:53:27.321398 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 4 |
| 2026-05-29T11:53:29.044027 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | +0.42 | 0.74 | 5560 |
| 2026-05-29T11:53:39.933546 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.90 | +4.04 | 0.14 | 5955 |
| 2026-05-29T11:53:42.067595 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.76 | 0.44 | 1659 |
| 2026-05-29T11:54:06.458003 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.23 | 0.22 | 258 |
| 2026-05-29T11:54:08.156665 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.80 | +2.16 | 0.36 | 6816 |
| 2026-05-29T11:54:13.050972 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +0.77 | 0.0 | 195 |
| 2026-05-29T11:54:14.840184 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.75 | +4.04 | 0.29 | 5989 |
| 2026-05-29T11:54:14.925616 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.76 | 0.44 | 1692 |
| 2026-05-29T11:54:40.776316 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.87 | +2.16 | 0.29 | 6848 |
| 2026-05-29T11:54:41.058559 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.77 | 0.2 | 223 |
| 2026-05-29T11:54:50.556493 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.82 | +1.94 | 0.12 | 427 |
| 2026-05-29T11:54:50.675834 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | +0.13 | 0.54 | 249 |
| 2026-05-29T11:55:12.920072 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.02 | +2.16 | 0.14 | 6880 |
| 2026-05-29T11:55:15.957495 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +0.77 | 0.0 | 258 |
| 2026-05-29T11:55:22.439966 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.13 | 0.36 | 281 |
| 2026-05-29T11:55:43.187743 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.09 | +2.16 | 0.07 | 6911 |
| 2026-05-29T11:55:47.407781 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +0.77 | 0.0 | 290 |
| 2026-05-29T11:55:49.078795 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.43 | +0.76 | 0.33 | 1786 |
| 2026-05-29T11:55:50.766123 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | +0.13 | 0.45 | 309 |
| 2026-05-29T11:55:55.586441 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.02 | +0.02 | 0.0 | 183 |
| 2026-05-29T11:56:05.863612 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | +0.47 | 0.58 | 5615 |
| 2026-05-29T11:56:11.177673 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.42 | 0.1 | 5722 |
| 2026-05-29T11:56:15.136330 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.16 | +2.24 | 0.08 | 6942 |
| 2026-05-29T11:56:16.677940 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.97 | 0.4 | 319 |
| 2026-05-29T11:56:24.879144 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.43 | +0.76 | 0.33 | 1822 |
| 2026-05-29T11:56:28.745520 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | +0.13 | 0.45 | 347 |
| 2026-05-29T11:56:34.480503 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.18 | 0.2 | 191 |
| 2026-05-29T11:56:39.064136 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.07 | 0.32 | 1061 |
| 2026-05-29T11:56:48.986435 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.60 | +2.60 | 0.0 | 6976 |
| 2026-05-29T11:56:51.876939 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +0.97 | 0.0 | 354 |
| 2026-05-29T11:56:55.037242 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.43 | +0.76 | 0.33 | 1852 |
| 2026-05-29T11:57:09.750052 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.07 | 0.32 | 1092 |
| 2026-05-29T11:57:15.977497 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.27 | -0.23 | 0.04 | 188 |
| 2026-05-29T11:57:17.689466 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.42 | 0.1 | 5788 |
| 2026-05-29T11:57:22.112276 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.82 | +2.82 | 0.0 | 7009 |
| 2026-05-29T11:57:29.971107 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.76 | 0.44 | 1887 |
| 2026-05-29T11:57:31.379160 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | +0.13 | 0.54 | 410 |
| 2026-05-29T11:57:43.251222 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | -0.07 | 0.24 | 1126 |
| 2026-05-29T11:57:50.084242 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.22 | 0.45 | 280 |
| 2026-05-29T11:57:51.856248 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.51 | 0.0 | 5822 |
| 2026-05-29T11:57:53.664517 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.89 | +2.89 | 0.0 | 7041 |
| 2026-05-29T11:58:13.963512 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.31 | -0.07 | 0.24 | 1156 |
| 2026-05-29T11:58:15.347717 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | +0.13 | 0.54 | 454 |
| 2026-05-29T11:58:29.938034 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.74 | +2.89 | 0.15 | 7077 |
| 2026-05-29T11:58:29.961676 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.88 | +0.88 | 0.0 | 5861 |
| 2026-05-29T11:58:43.257620 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.07 | 0.32 | 1186 |
| 2026-05-29T11:58:46.338018 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.13 | 0.36 | 485 |
| 2026-05-29T11:58:58.466709 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.44 | 0.67 | 348 |
| 2026-05-29T11:59:00.345723 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.82 | +2.89 | 0.07 | 7108 |
| 2026-05-29T11:59:00.375633 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.88 | +1.06 | 0.18 | 5891 |
| 2026-05-29T11:59:01.790349 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.97 | 0.4 | 484 |
| 2026-05-29T11:59:21.782894 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | +0.13 | 0.18 | 520 |
| 2026-05-29T11:59:34.016403 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.96 | +2.96 | 0.0 | 7141 |
| 2026-05-29T11:59:34.049236 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.88 | +1.06 | 0.18 | 5925 |
| 2026-05-29T11:59:39.817119 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.18 | +1.18 | 0.0 | 522 |
| 2026-05-29T11:59:41.668936 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 7060 |
| 2026-05-29T11:59:41.730754 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.12 | +0.47 | 0.35 | 5831 |
| 2026-05-29T11:59:49.682640 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.44 | 0.89 | 399 |
| 2026-05-29T12:00:06.677167 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.88 | +1.06 | 0.18 | 5957 |
| 2026-05-29T12:00:10.023716 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +1.18 | 0.21 | 552 |
| 2026-05-29T12:00:14.620265 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.44 | 0.89 | 424 |
| 2026-05-29T12:00:19.755063 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 5869 |
| 2026-05-29T12:00:41.847066 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 46 |
| 2026-05-29T12:23:37.353705 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.48 | 0.0 | 2029 |
| 2026-05-29T12:23:38.997127 | NHN(181710) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.39 | +4.39 | 0.0 | 1961 |
| 2026-05-29T12:23:44.159017 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.91 | +1.91 | 0.0 | 1428 |
| 2026-05-29T12:24:10.600789 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.70 | 0.23 | 7300 |
| 2026-05-29T12:24:10.613842 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 5992 |
| 2026-05-29T12:24:10.692877 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 2062 |
| 2026-05-29T12:25:15.570460 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.70 | 0.23 | 7364 |
| 2026-05-29T12:25:15.601211 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.02 | 0.21 | 3439 |
| 2026-05-29T12:25:20.887733 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | +0.09 | 0.4 | 2783 |
| 2026-05-29T12:25:49.347920 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.70 | 0.35 | 7398 |
| 2026-05-29T12:25:49.360644 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.02 | 0.35 | 3473 |
| 2026-05-29T12:25:49.385138 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.45 | 0.0 | 1959 |
| 2026-05-29T12:25:51.107733 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.31 | +0.09 | 0.4 | 2813 |
| 2026-05-29T12:26:01.922664 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 8640 |
| 2026-05-29T12:26:01.941342 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.14 | +0.23 | 0.09 | 7513 |
| 2026-05-29T12:26:03.236406 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 1960 |
| 2026-05-29T12:26:03.262301 | 포바이포(389140) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.06 | +4.18 | 0.12 | 1567 |
| 2026-05-29T12:26:17.297790 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.02 | 0.21 | 3501 |
| 2026-05-29T12:26:17.349123 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.45 | 0.0 | 1987 |
| 2026-05-29T12:26:25.431443 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.10 | 0.44 | 3623 |
| 2026-05-29T12:26:58.664787 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.10 | 0.44 | 3656 |
| 2026-05-29T12:27:06.111270 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 6167 |
| 2026-05-29T12:27:09.151988 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +1.14 | 0.32 | 8707 |
| 2026-05-29T12:27:36.337458 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 6198 |
| 2026-05-29T12:27:42.782391 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +1.14 | 0.32 | 8741 |
| 2026-05-29T12:28:42.363636 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.50 | 0.09 | 6264 |
| 2026-05-29T12:28:42.428359 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.35 | 0.07 | 1679 |
| 2026-05-29T12:29:00.380199 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 7691 |
| 2026-05-29T12:29:00.415271 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.15 | +0.18 | 0.33 | 3003 |
| 2026-05-29T12:29:00.483292 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.29 | 0.73 | 313 |
| 2026-05-29T12:29:09.775699 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.22 | 0.23 | 2159 |
| 2026-05-29T12:29:13.278119 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.41 | +0.50 | 0.09 | 6295 |
| 2026-05-29T12:30:08.253718 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.46 | +0.46 | 0.0 | 102 |
| 2026-05-29T12:30:26.473316 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.29 | 0.31 | 399 |
| 2026-05-29T12:30:34.103766 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | +0.10 | 0.44 | 3871 |
| 2026-05-29T12:30:34.366759 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.46 | 0.12 | 128 |
| 2026-05-29T12:30:41.483012 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.22 | 0.23 | 2251 |
| 2026-05-29T12:30:45.583172 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 7796 |
| 2026-05-29T12:30:45.884006 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.01 | 0.44 | 378 |
| 2026-05-29T12:30:51.210013 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.70 | 0.35 | 7700 |
| 2026-05-29T12:30:53.170676 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +1.14 | 0.48 | 8931 |
| 2026-05-29T12:31:49.480368 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 7860 |
| 2026-05-29T12:31:49.547372 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.22 | 0.45 | 2319 |
| 2026-05-29T12:31:52.486689 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | -0.01 | 0.07 | 444 |
| 2026-05-29T12:31:54.000091 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.70 | 0.35 | 7763 |
| 2026-05-29T12:32:02.890806 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +1.14 | 0.48 | 9001 |
| 2026-05-29T12:32:06.340505 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 6468 |
| 2026-05-29T12:32:17.867499 | 신성델타테크(065350) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.10 | 0.55 | 3975 |
| 2026-05-29T12:32:19.491626 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 7890 |
| 2026-05-29T12:32:20.786680 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.08 | -0.01 | 0.07 | 473 |
| 2026-05-29T12:32:25.371991 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.35 | +0.70 | 0.35 | 7794 |
| 2026-05-29T12:32:34.244883 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.29 | 0.73 | 526 |
| 2026-05-29T12:32:35.762304 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.14 | 0.24 | 9034 |
| 2026-05-29T12:32:37.516622 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.50 | 0.0 | 6499 |
| 2026-05-29T12:33:01.298894 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.36 | 0.0 | 2409 |
| 2026-05-29T12:33:09.163325 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.29 | 0.73 | 561 |
| 2026-05-29T12:33:10.859980 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.14 | 0.24 | 9069 |
| 2026-05-29T12:33:17.991451 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | +0.22 | 0.67 | 2408 |
| 2026-05-29T12:33:21.562850 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.27 | +0.18 | 0.45 | 3264 |
| 2026-05-29T12:33:48.004494 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.14 | 0.24 | 9106 |
| 2026-05-29T12:34:06.825929 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.80 | +0.80 | 0.0 | 341 |
| 2026-05-29T12:34:14.151363 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.41 | -0.05 | 0.36 | 282 |
| 2026-05-29T12:34:17.538423 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.45 | +0.22 | 0.67 | 2467 |
| 2026-05-29T12:34:19.101749 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.90 | +1.14 | 0.24 | 9137 |
| 2026-05-29T12:34:51.365873 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.14 | 0.24 | 9170 |
| 2026-05-29T12:34:51.517373 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.29 | 0.31 | 664 |
| 2026-05-29T12:35:27.895744 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.80 | 0.46 | 422 |
| 2026-05-29T12:35:27.944941 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.30 | 0.0 | 356 |
| 2026-05-29T12:59:18.708081 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.32 | +1.32 | 0.0 | 3911 |
| 2026-05-29T12:59:18.719181 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.51 | 0.0 | 3515 |
| 2026-05-29T12:59:18.736511 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.80 | +0.80 | 0.0 | 2131 |
| 2026-05-29T12:59:18.763769 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.04 | +0.04 | 0.0 | 2131 |
| 2026-05-29T12:59:18.784416 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.49 | +3.49 | 0.0 | 2091 |
| 2026-05-29T12:59:20.429881 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.76 | +2.76 | 0.0 | 1788 |
| 2026-05-29T12:59:41.324132 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.34 | +2.34 | 0.0 | 8123 |
| 2026-05-29T12:59:45.392956 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.30 | +1.32 | 0.02 | 3937 |
| 2026-05-29T12:59:45.412382 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.76 | +0.76 | 0.0 | 3542 |
| 2026-05-29T12:59:45.430217 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.75 | +0.80 | 0.05 | 2158 |
| 2026-05-29T12:59:45.443193 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | +0.04 | 0.09 | 2158 |
| 2026-05-29T12:59:45.485551 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.49 | +3.49 | 0.0 | 2117 |
| 2026-05-29T13:00:11.041592 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +0.80 | 0.1 | 2183 |
| 2026-05-29T13:00:11.056108 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.30 | 0.0 | 2183 |
| 2026-05-29T13:00:11.079800 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.49 | +3.49 | 0.0 | 2143 |
| 2026-05-29T13:00:36.519651 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.49 | +3.57 | 0.08 | 2168 |
| 2026-05-29T13:00:41.073591 | 롯데이노베이트(286940) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.45 | -0.45 | 0.0 | 4051 |
| 2026-05-29T13:00:53.720374 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.89 | 0.31 | 3610 |
| 2026-05-29T13:00:59.341610 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.13 | +1.33 | 0.2 | 4011 |
| 2026-05-29T13:01:12.868966 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.34 | 0.0 | 4935 |
| 2026-05-29T13:01:12.932483 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2245 |
| 2026-05-29T13:01:37.238495 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.63 | +1.63 | 0.0 | 2269 |
| 2026-05-29T13:01:41.883797 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.23 | 0.0 | 10780 |
| 2026-05-29T13:01:41.890524 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 10780 |
| 2026-05-29T13:01:41.897026 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.14 | +0.23 | 0.09 | 9653 |
| 2026-05-29T13:01:41.922696 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.89 | +0.89 | 0.0 | 5626 |
| 2026-05-29T13:01:41.941227 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 4964 |
| 2026-05-29T13:01:41.948949 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.91 | +0.91 | 0.0 | 4313 |
| 2026-05-29T13:01:41.990748 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.02 | +0.02 | 0.0 | 4130 |
| 2026-05-29T13:01:43.226280 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.40 | +2.76 | 0.36 | 1931 |
| 2026-05-29T13:02:13.901398 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.10 | +0.02 | 0.12 | 4161 |
| 2026-05-29T13:02:13.997706 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.58 | +1.63 | 0.05 | 2306 |
| 2026-05-29T13:02:14.032354 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.12 | +3.57 | 0.45 | 2266 |
| 2026-05-29T13:02:18.228315 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.29 | -0.29 | 0.0 | 2032 |
| 2026-05-29T13:02:25.415661 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.50 | 0.2 | 5008 |
| 2026-05-29T13:02:25.546468 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.19 | 0.54 | 184 |
| 2026-05-29T13:02:58.720106 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 2351 |
| 2026-05-29T13:03:02.135358 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.50 | 0.08 | 5044 |
| 2026-05-29T13:03:10.562895 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.07 | 0.37 | 3747 |
| 2026-05-29T13:03:34.893694 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.14 | +1.38 | 0.24 | 4167 |
| 2026-05-29T13:03:42.828355 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.27 | +3.57 | 0.3 | 2355 |
| 2026-05-29T13:03:49.734936 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.63 | +3.63 | 0.0 | 8371 |
| 2026-05-29T13:03:51.616562 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.20 | +2.20 | 0.0 | 2404 |
| 2026-05-29T13:04:03.808395 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.50 | 0.08 | 5106 |
| 2026-05-29T13:04:08.615782 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.03 | +1.08 | 0.05 | 4460 |
| 2026-05-29T13:04:10.222673 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 2422 |
| 2026-05-29T13:04:11.910694 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.49 | +3.57 | 0.08 | 2384 |
| 2026-05-29T13:04:20.615161 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.18 | +4.18 | 0.0 | 8402 |
| 2026-05-29T13:04:35.529066 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.25 | +2.30 | 0.05 | 2448 |
| 2026-05-29T13:05:21.719870 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.24 | 0.59 | 9771 |
| 2026-05-29T13:05:21.730368 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.00 | +4.18 | 0.18 | 8463 |
| 2026-05-29T13:05:21.796289 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 4319 |
| 2026-05-29T13:05:21.809805 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.70 | +1.07 | 0.37 | 3878 |
| 2026-05-29T13:05:21.818072 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.56 | +2.56 | 0.0 | 2494 |
| 2026-05-29T13:05:21.832769 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.72 | +3.79 | 0.07 | 2454 |
| 2026-05-29T13:05:43.207206 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 4340 |
| 2026-05-29T13:05:44.636923 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.56 | +2.56 | 0.0 | 2517 |
| 2026-05-29T13:05:44.673248 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.72 | +3.79 | 0.07 | 2476 |
| 2026-05-29T13:05:56.104100 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.58 | 0.08 | 5218 |
| 2026-05-29T13:05:56.150964 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2528 |
| 2026-05-29T13:06:10.438836 | 현대이지웰(090850) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.46 | +4.73 | 0.27 | 8512 |
| 2026-05-29T13:06:10.528221 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 4367 |
| 2026-05-29T13:06:10.540033 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +1.07 | 0.49 | 3927 |
| 2026-05-29T13:06:10.588426 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.57 | +3.79 | 0.22 | 2502 |
| 2026-05-29T13:06:23.507425 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.24 | +1.24 | 0.0 | 5907 |
| 2026-05-29T13:06:45.976724 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.53 | +3.79 | 0.26 | 2538 |
| 2026-05-29T13:06:53.391213 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.31 | +1.31 | 0.0 | 5937 |
| 2026-05-29T13:06:57.736720 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.58 | 0.0 | 5280 |
| 2026-05-29T13:07:09.524294 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.30 | +1.30 | 0.0 | 4641 |
| 2026-05-29T13:07:12.749805 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +1.07 | 0.49 | 3989 |
| 2026-05-29T13:07:12.791037 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.49 | +3.79 | 0.3 | 2565 |
| 2026-05-29T13:07:16.044370 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 2608 |
| 2026-05-29T13:07:24.701246 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.39 | 0.16 | 11123 |
| 2026-05-29T13:07:24.807380 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.40 | +2.76 | 0.36 | 2273 |
| 2026-05-29T13:07:30.520580 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.31 | +1.31 | 0.0 | 5974 |
| 2026-05-29T13:07:30.545440 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.66 | 0.0 | 5313 |
| 2026-05-29T13:07:40.247100 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.33 | +1.33 | 0.0 | 4672 |
| 2026-05-29T13:08:16.526359 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | +0.24 | 0.35 | 9945 |
| 2026-05-29T13:08:16.603271 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.66 | 0.16 | 5359 |
| 2026-05-29T13:08:27.540706 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.31 | +1.31 | 0.0 | 6031 |
| 2026-05-29T13:08:27.590014 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.34 | 0.0 | 4719 |
| 2026-05-29T13:08:28.705116 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.34 | +1.60 | 0.26 | 4461 |
| 2026-05-29T13:08:28.715800 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.64 | +1.07 | 0.43 | 4065 |
| 2026-05-29T13:08:36.715201 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.11 | +0.24 | 0.35 | 9966 |
| 2026-05-29T13:08:36.748612 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 5379 |
| 2026-05-29T13:08:36.809409 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +1.15 | 0.38 | 4544 |
| 2026-05-29T13:08:47.117275 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.33 | +0.33 | 0.0 | 83 |
| 2026-05-29T13:08:55.005218 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.39 | +0.57 | 0.18 | 2707 |
| 2026-05-29T13:08:58.641497 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.31 | +1.31 | 0.0 | 6062 |
| 2026-05-29T13:08:58.678729 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.30 | +1.34 | 0.04 | 4750 |
| 2026-05-29T13:08:58.708191 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.64 | +1.07 | 0.43 | 4095 |
| 2026-05-29T13:09:00.617916 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 4537 |
| 2026-05-29T13:09:20.928765 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2733 |
| 2026-05-29T13:09:25.625792 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.25 | +2.56 | 0.31 | 2738 |
| 2026-05-29T13:09:42.601029 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 5445 |
| 2026-05-29T13:09:42.774369 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.17 | +0.19 | 0.36 | 621 |
| 2026-05-29T13:09:44.527210 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +1.31 | 0.49 | 6108 |
| 2026-05-29T13:09:57.549320 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.71 | +2.71 | 0.0 | 2770 |
| 2026-05-29T13:09:57.630664 | 한국피아이엠(448900) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.14 | 0.28 | 184 |
| 2026-05-29T13:09:59.327543 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.39 | 0.16 | 11278 |
| 2026-05-29T13:10:30.782587 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2803 |
| 2026-05-29T13:10:35.391032 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.66 | +2.71 | 0.05 | 2808 |
| 2026-05-29T13:11:06.039482 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +1.15 | 0.38 | 4694 |
| 2026-05-29T13:11:07.304730 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.57 | 0.0 | 2839 |
| 2026-05-29T13:11:09.105987 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 11347 |
| 2026-05-29T13:11:09.123256 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.14 | +0.23 | 0.09 | 10220 |
| 2026-05-29T13:11:10.651453 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.35 | +2.76 | 0.41 | 2843 |
| 2026-05-29T13:11:35.614756 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.39 | 0.49 | 11374 |
| 2026-05-29T13:11:35.685297 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.77 | +1.15 | 0.38 | 4723 |
| 2026-05-29T13:11:38.822305 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2871 |
| 2026-05-29T13:11:40.635030 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.40 | +2.76 | 0.36 | 2873 |
| 2026-05-29T13:11:53.419117 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 5576 |
| 2026-05-29T13:12:08.107931 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.65 | +1.15 | 0.5 | 4756 |
| 2026-05-29T13:12:08.130740 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2900 |
| 2026-05-29T13:12:11.098410 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.98 | +1.39 | 0.41 | 11409 |
| 2026-05-29T13:12:11.225964 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.56 | +2.76 | 0.2 | 2903 |
| 2026-05-29T13:12:18.884494 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.82 | +1.26 | 0.44 | 4296 |
| 2026-05-29T13:12:24.173799 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 5606 |
| 2026-05-29T13:12:24.320314 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.40 | +2.76 | 0.36 | 2572 |
| 2026-05-29T13:12:24.344587 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.17 | +0.19 | 0.36 | 782 |
| 2026-05-29T13:12:42.225838 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2934 |
| 2026-05-29T13:12:44.225125 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.71 | +2.76 | 0.05 | 2936 |
| 2026-05-29T13:12:47.514041 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.34 | +3.79 | 0.45 | 2899 |
| 2026-05-29T13:13:11.838610 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 2964 |
| 2026-05-29T13:13:17.021871 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.12 | +3.12 | 0.0 | 2969 |
| 2026-05-29T13:13:50.326189 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.33 | 0.68 | 386 |
| 2026-05-29T13:13:58.384456 | 두산(000150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.38 | +3.85 | 0.47 | 3011 |
| 2026-05-29T13:14:21.575715 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.65 | +1.15 | 0.5 | 4889 |
| 2026-05-29T13:14:21.593164 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.33 | +1.60 | 0.27 | 4814 |
| 2026-05-29T13:14:23.125297 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.39 | +0.57 | 0.18 | 3035 |
| 2026-05-29T13:14:30.830737 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 5733 |
| 2026-05-29T13:15:03.547515 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 3076 |
| 2026-05-29T13:15:08.224468 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 5771 |
| 2026-05-29T13:15:34.511006 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.77 | +1.15 | 0.38 | 4962 |
| 2026-05-29T13:15:44.639983 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 5807 |
| 2026-05-29T13:15:46.090984 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.43 | +0.43 | 0.0 | 984 |
| 2026-05-29T13:16:02.092398 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.14 | +1.39 | 0.25 | 11640 |
| 2026-05-29T13:16:17.347445 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.32 | 0.0 | 10528 |
| 2026-05-29T13:16:17.420609 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 1015 |
| 2026-05-29T13:16:17.509649 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.23 | 0.13 | 189 |
| 2026-05-29T13:16:30.535938 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.63 | +1.63 | 0.0 | 4943 |
| 2026-05-29T13:16:33.900423 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.14 | +1.39 | 0.25 | 11672 |
| 2026-05-29T13:16:47.811462 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.42 | 0.1 | 10558 |
| 2026-05-29T13:16:47.922255 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.67 | 0.06 | 1046 |
| 2026-05-29T13:17:05.828376 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.39 | 0.16 | 11704 |
| 2026-05-29T13:17:18.904756 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.42 | 0.1 | 10590 |
| 2026-05-29T13:17:37.821369 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.23 | 0.14 | 184 |
| 2026-05-29T13:17:45.702416 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.43 | +0.67 | 0.24 | 1104 |
| 2026-05-29T13:17:50.517892 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.32 | +0.42 | 0.1 | 10621 |
| 2026-05-29T13:17:53.625657 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | +0.05 | 0.08 | 223 |
| 2026-05-29T13:18:11.233034 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 5954 |
| 2026-05-29T13:18:13.207733 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.06 | +0.06 | 0.0 | 2987 |
| 2026-05-29T13:18:21.133059 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.51 | 0.0 | 10652 |
| 2026-05-29T13:18:22.906216 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.93 | +1.93 | 0.0 | 5055 |
| 2026-05-29T13:18:22.915205 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 3275 |
| 2026-05-29T13:18:22.963105 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.85 | +0.85 | 0.0 | 1141 |
| 2026-05-29T13:19:05.283822 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.85 | 0.24 | 1183 |
| 2026-05-29T13:19:07.757118 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.99 | +1.35 | 0.36 | 274 |
| 2026-05-29T13:19:11.012393 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.27 | +0.27 | 0.0 | 187 |
| 2026-05-29T13:19:14.314929 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 6017 |
| 2026-05-29T13:19:34.030924 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 10725 |
| 2026-05-29T13:19:34.109050 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.67 | +0.85 | 0.18 | 1212 |
| 2026-05-29T13:19:34.221472 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.92 | +1.35 | 0.43 | 301 |
| 2026-05-29T13:19:47.102780 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | -0.00 | +0.06 | 0.06 | 3081 |
| 2026-05-29T13:19:54.528306 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.34 | +0.66 | 0.32 | 6057 |
| 2026-05-29T13:20:02.634680 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 10753 |
| 2026-05-29T13:20:02.675613 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.43 | +0.85 | 0.42 | 1241 |
| 2026-05-29T13:20:11.387259 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 11890 |
| 2026-05-29T13:20:11.510813 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.44 | 0.0 | 248 |
| 2026-05-29T13:20:19.175321 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.13 | 0.48 | 220 |
| 2026-05-29T13:20:22.977592 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.06 | 0.12 | 3117 |
| 2026-05-29T13:20:29.598930 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 3402 |
| 2026-05-29T13:20:33.125647 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.51 | 0.19 | 10784 |
| 2026-05-29T13:20:36.216357 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.35 | 0.29 | 363 |
| 2026-05-29T13:20:40.780650 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 390 |
| 2026-05-29T13:20:57.840225 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 6120 |
| 2026-05-29T13:21:10.406800 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +1.21 | 0.24 | 1308 |
| 2026-05-29T13:21:10.614318 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 420 |
| 2026-05-29T13:21:10.634327 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.99 | +1.35 | 0.36 | 397 |
| 2026-05-29T13:21:20.028355 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.55 | 0.11 | 316 |
| 2026-05-29T13:21:24.577346 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 285 |
| 2026-05-29T13:21:33.032663 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 6155 |
| 2026-05-29T13:21:39.541617 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 10850 |
| 2026-05-29T13:21:39.668764 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.03 | +1.21 | 0.18 | 1338 |
| 2026-05-29T13:21:39.729935 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 449 |
| 2026-05-29T13:21:39.739420 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.06 | +1.35 | 0.29 | 426 |
| 2026-05-29T13:22:02.292066 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.55 | 0.11 | 359 |
| 2026-05-29T13:22:04.777163 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.37 | 0.72 | 325 |
| 2026-05-29T13:22:06.633127 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.50 | +0.66 | 0.16 | 6189 |
| 2026-05-29T13:22:07.716309 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.10 | +2.23 | 0.13 | 5280 |
| 2026-05-29T13:22:09.492998 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 10880 |
| 2026-05-29T13:22:09.519177 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.15 | +1.15 | 0.0 | 5357 |
| 2026-05-29T13:22:11.292927 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 481 |
| 2026-05-29T13:22:14.536529 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.51 | +1.51 | 0.0 | 1373 |
| 2026-05-29T13:22:29.027961 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | +0.37 | 0.84 | 350 |
| 2026-05-29T13:22:30.741146 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.76 | +2.93 | 0.17 | 3179 |
| 2026-05-29T13:22:35.222783 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.39 | 0.0 | 12033 |
| 2026-05-29T13:22:40.323922 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.42 | +0.51 | 0.09 | 10911 |
| 2026-05-29T13:22:40.332997 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.66 | 0.16 | 6223 |
| 2026-05-29T13:22:40.480384 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 510 |
| 2026-05-29T13:22:51.091204 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.90 | +1.15 | 0.25 | 5399 |
| 2026-05-29T13:23:14.223847 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 12072 |
| 2026-05-29T13:23:14.276742 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.50 | +0.66 | 0.16 | 6257 |
| 2026-05-29T13:23:18.741576 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 548 |
| 2026-05-29T13:23:27.336287 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.90 | +1.15 | 0.25 | 5435 |
| 2026-05-29T13:23:41.196053 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.47 | +0.37 | 0.84 | 422 |
| 2026-05-29T13:23:54.611619 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | -0.00 | +0.06 | 0.06 | 3329 |
| 2026-05-29T13:24:08.145017 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.29 | -0.23 | 0.06 | 187 |
| 2026-05-29T13:24:09.919004 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.40 | +1.40 | 0.0 | 5477 |
| 2026-05-29T13:24:11.607444 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.85 | +0.96 | 0.11 | 452 |
| 2026-05-29T13:24:15.949872 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | -0.02 | 0.0 | 5453 |
| 2026-05-29T13:24:31.093415 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.06 | +0.05 | 0.11 | 621 |
| 2026-05-29T13:24:34.173466 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.53 | +0.89 | 0.36 | 510 |
| 2026-05-29T13:24:35.898820 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.32 | +0.51 | 0.19 | 11026 |
| 2026-05-29T13:24:35.928954 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.92 | +2.23 | 0.31 | 5428 |
| 2026-05-29T13:24:43.042337 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.65 | +1.65 | 0.0 | 5511 |
| 2026-05-29T13:24:44.961905 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.12 | +0.57 | 0.45 | 3657 |
| 2026-05-29T13:24:45.169513 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.96 | 0.47 | 486 |
| 2026-05-29T13:24:48.539552 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.66 | 0.24 | 6351 |
| 2026-05-29T13:24:48.575628 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.18 | 0.2 | 5485 |
| 2026-05-29T13:24:59.165068 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | +0.17 | 0.33 | 710 |
| 2026-05-29T13:25:00.943342 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.07 | +0.05 | 0.12 | 650 |
| 2026-05-29T13:25:02.902926 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.89 | 0.23 | 539 |
| 2026-05-29T13:25:11.408145 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.15 | +2.15 | 0.0 | 5539 |
| 2026-05-29T13:25:18.337961 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.74 | 0.08 | 6381 |
| 2026-05-29T13:25:18.398205 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.18 | 0.41 | 5515 |
| 2026-05-29T13:25:39.485754 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.89 | 0.23 | 576 |
| 2026-05-29T13:25:42.700818 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 3715 |
| 2026-05-29T13:25:55.331789 | 고스트스튜디오(950190) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.03 | +2.15 | 0.12 | 5583 |
| 2026-05-29T13:25:55.350440 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.18 | 0.62 | 5552 |
| 2026-05-29T13:25:55.414620 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.02 | +2.23 | 0.21 | 5507 |
| 2026-05-29T13:25:58.141687 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.96 | +0.96 | 0.0 | 559 |
| 2026-05-29T13:26:05.109792 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.58 | +0.89 | 0.31 | 601 |
| 2026-05-29T13:26:15.049204 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.66 | 0.0 | 3747 |
| 2026-05-29T13:26:27.628348 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.83 | +2.23 | 0.4 | 5540 |
| 2026-05-29T13:26:29.031441 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.96 | 0.47 | 590 |
| 2026-05-29T13:26:32.684481 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.24 | +0.24 | 0.0 | 804 |
| 2026-05-29T13:26:38.728436 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.44 | +0.89 | 0.45 | 635 |
| 2026-05-29T13:26:44.579650 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.66 | 0.0 | 3777 |
| 2026-05-29T13:26:57.374049 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | +0.18 | 0.62 | 5614 |
| 2026-05-29T13:26:57.387209 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.17 | +0.06 | 0.23 | 3511 |
| 2026-05-29T13:27:00.443196 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.49 | +0.96 | 0.47 | 621 |
| 2026-05-29T13:27:02.249086 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.66 | +0.82 | 0.16 | 6485 |
| 2026-05-29T13:27:02.419382 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.22 | +0.05 | 0.27 | 772 |
| 2026-05-29T13:27:08.987493 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.41 | +0.89 | 0.48 | 665 |
| 2026-05-29T13:27:16.105870 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.66 | 0.09 | 3808 |
| 2026-05-29T13:28:11.518650 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.38 | 0.0 | 903 |
| 2026-05-29T13:28:24.543593 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.66 | 0.09 | 3877 |
| 2026-05-29T13:41:04.673690 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.17 | +0.17 | 0.0 | 1676 |
| 2026-05-29T13:41:04.703940 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.24 | -0.24 | 0.0 | 1614 |
| 2026-05-29T13:41:04.722272 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.43 | +3.43 | 0.0 | 1591 |
| 2026-05-29T13:41:04.743753 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | -0.02 | 0.0 | 1583 |
| 2026-05-29T13:41:04.757784 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.78 | +0.78 | 0.0 | 1501 |
| 2026-05-29T13:41:04.770027 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 1465 |
| 2026-05-29T13:41:04.811123 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.63 | +0.63 | 0.0 | 1204 |
| 2026-05-29T13:41:43.428420 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.45 | +2.45 | 0.0 | 12054 |
| 2026-05-29T13:41:44.779881 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.30 | 0.0 | 4677 |
| 2026-05-29T13:41:44.812898 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.91 | 0.34 | 4399 |
| 2026-05-29T13:41:46.731154 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.30 | -0.24 | 0.06 | 1656 |
| 2026-05-29T13:41:46.748828 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +3.43 | +3.43 | 0.0 | 1633 |
| 2026-05-29T13:41:46.781514 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +0.78 | 0.09 | 1543 |
| 2026-05-29T13:41:46.826505 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.23 | 0.12 | 1507 |
| 2026-05-29T13:41:46.843972 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.57 | +0.63 | 0.06 | 1246 |
| 2026-05-29T13:42:19.475553 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.63 | 0.06 | 1278 |
| 2026-05-29T13:42:25.426428 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.57 | +0.91 | 0.34 | 4439 |
| 2026-05-29T13:42:25.454036 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.78 | +0.78 | 0.0 | 1757 |
| 2026-05-29T13:42:25.483080 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.87 | 0.2 | 1582 |
| 2026-05-29T13:42:25.532682 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.63 | 0.18 | 1284 |
| 2026-05-29T13:42:30.942499 | 셀바스AI(108860) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.73 | +2.73 | 0.0 | 12102 |
| 2026-05-29T13:42:43.742306 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.30 | 0.0 | 4736 |
| 2026-05-29T13:42:43.757321 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.67 | +0.97 | 0.3 | 2602 |
| 2026-05-29T13:43:16.137461 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.78 | 0.4 | 1807 |
| 2026-05-29T13:43:17.981759 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 7460 |
| 2026-05-29T13:43:27.834077 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.45 | +0.63 | 0.18 | 1347 |
| 2026-05-29T13:43:35.205450 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.86 | +4.29 | 0.43 | 1742 |
| 2026-05-29T13:43:51.427707 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.38 | +0.78 | 0.4 | 1843 |
| 2026-05-29T13:44:17.248663 | 솔루스첨단소재(336370) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.24 | +2.43 | 0.19 | 191 |
| 2026-05-29T13:44:58.034731 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.21 | -0.21 | 0.0 | 1848 |
| 2026-05-29T13:44:58.054866 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.08 | 0.31 | 1816 |
| 2026-05-29T13:45:01.181338 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.38 | +0.63 | 0.25 | 1440 |
| 2026-05-29T13:46:22.250370 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.80 | 0.25 | 7645 |
| 2026-05-29T13:46:22.312516 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.00 | +4.29 | 0.29 | 1909 |
| 2026-05-29T13:46:33.857164 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 157 |
| 2026-05-29T13:47:13.856449 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | +0.01 | 0.36 | 1834 |
| 2026-05-29T13:48:04.844604 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.21 | +1.45 | 0.24 | 2923 |
| 2026-05-29T13:48:06.577502 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.05 | +1.05 | 0.0 | 2098 |
| 2026-05-29T13:48:09.929547 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.14 | +4.36 | 0.22 | 2016 |
| 2026-05-29T13:48:24.483205 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.40 | +0.40 | 0.0 | 2023 |
| 2026-05-29T13:48:39.906653 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.70 | +1.15 | 0.45 | 1956 |
| 2026-05-29T13:48:43.552574 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | +0.30 | 0.35 | 5096 |
| 2026-05-29T13:48:43.598812 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.93 | +4.36 | 0.43 | 2050 |
| 2026-05-29T13:48:50.054466 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.23 | 0.0 | 2048 |
| 2026-05-29T13:49:23.805683 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.13 | +1.44 | 0.31 | 2082 |
| 2026-05-29T13:49:23.846401 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.12 | 0.22 | 293 |
| 2026-05-29T13:49:25.627823 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.20 | +4.20 | 0.0 | 1704 |
| 2026-05-29T13:49:48.422115 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 1989 |
| 2026-05-29T13:49:53.085308 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.13 | +1.44 | 0.31 | 2111 |
| 2026-05-29T13:49:53.177292 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.12 | 0.11 | 322 |
| 2026-05-29T13:49:57.673679 | LG유플러스(032640) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.20 | +4.32 | 0.12 | 1737 |
| 2026-05-29T13:51:05.684064 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | -0.21 | 0.26 | 2215 |
| 2026-05-29T13:51:05.723876 | 세나테크놀로지(061090) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.02 | +1.44 | 0.42 | 2184 |
| 2026-05-29T13:51:23.917137 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.37 | 0.0 | 2085 |
| 2026-05-29T13:51:44.364764 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.86 | +2.86 | 0.0 | 7056 |
| 2026-05-29T13:53:10.211789 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.20 | +1.20 | 0.0 | 5084 |
| 2026-05-29T13:54:05.016959 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.30 | -0.21 | 0.09 | 2395 |
| 2026-05-29T13:54:10.185347 | 삼성전자(005930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.71 | 0.16 | 13928 |
| 2026-05-29T13:54:10.217582 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.31 | +1.80 | 0.49 | 8113 |
| 2026-05-29T13:54:31.646007 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.01 | 0.33 | 601 |
| 2026-05-29T13:54:39.719617 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.23 | 0.21 | 181 |
| 2026-05-29T13:54:41.248308 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8144 |
| 2026-05-29T13:55:02.727174 | ACE 코리아AI테크핵심산업(380340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.21 | 0.02 | 2452 |
| 2026-05-29T13:55:12.073049 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8174 |
| 2026-05-29T13:55:42.584736 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8205 |
| 2026-05-29T13:56:24.443676 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8247 |
| 2026-05-29T13:56:24.455320 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.02 | +3.09 | 0.07 | 7336 |
| 2026-05-29T13:56:27.446679 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.19 | -0.10 | 0.09 | 181 |
| 2026-05-29T13:56:48.859598 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.31 | +0.31 | 0.0 | 738 |
| 2026-05-29T13:56:50.810543 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | -0.01 | 0.0 | 291 |
| 2026-05-29T13:56:52.483340 | 삼화콘덴서(001820) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | +0.02 | 0.38 | 776 |
| 2026-05-29T13:56:54.167784 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8277 |
| 2026-05-29T13:57:30.566207 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.39 | +1.80 | 0.41 | 8313 |
| 2026-05-29T13:58:01.379681 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.31 | +1.80 | 0.49 | 8344 |
| 2026-05-29T13:58:01.455176 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.12 | +1.19 | 0.07 | 2693 |
| 2026-05-29T13:58:01.475711 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.35 | +1.58 | 0.23 | 2518 |
| 2026-05-29T13:58:35.760291 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | +0.37 | 0.84 | 2516 |
| 2026-05-29T13:58:35.862267 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.42 | +0.42 | 0.0 | 845 |
| 2026-05-29T13:59:04.333158 | 현대위아(011210) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.64 | +0.97 | 0.33 | 873 |
| 2026-05-29T13:59:15.772453 | SOL 자동차소부장Fn(464600) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.73 | +3.09 | 0.36 | 7508 |
| 2026-05-29T13:59:42.172663 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.57 | +0.57 | 0.0 | 5754 |
| 2026-05-29T13:59:42.185071 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.97 | +1.20 | 0.23 | 5476 |
| 2026-05-29T14:00:09.551351 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.01 | +0.10 | 0.11 | 490 |
| 2026-05-29T14:00:58.780945 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.30 | +0.57 | 0.27 | 5831 |
| 2026-05-29T14:01:11.609597 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +0.86 | +1.20 | 0.34 | 5566 |
| 2026-05-29T14:01:27.980853 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +6.31 | +6.31 | 0.0 | 14366 |
| 2026-05-29T14:01:35.578318 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 5868 |
| 2026-05-29T14:01:38.910754 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.19 | -0.06 | 0.13 | 493 |
| 2026-05-29T14:01:46.564627 | 코난테크놀로지(402030) | `sim_ai_budget_exhausted` | `soft_critical` | `legacy_critical_zone` | +0.86 | +1.20 | 0.34 | 5601 |
| 2026-05-29T14:02:06.747192 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 5899 |
| 2026-05-29T14:02:24.175002 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.23 | 0.12 | 383 |
| 2026-05-29T14:02:47.705057 | 한진칼(180640) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.48 | +0.57 | 0.09 | 5940 |
| 2026-05-29T14:02:49.944744 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.23 | 0.12 | 409 |
| 2026-05-29T14:02:51.665990 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.55 | +1.80 | 0.25 | 8634 |
| 2026-05-29T14:03:04.703266 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.01 | +0.10 | 0.11 | 665 |
| 2026-05-29T14:03:07.566326 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.35 | +0.35 | 0.0 | 61 |
| 2026-05-29T14:03:15.385709 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.46 | +1.52 | 0.06 | 3007 |
| 2026-05-29T14:03:20.278010 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.17 | 0.06 | 439 |
| 2026-05-29T14:03:51.880711 | 신세계 I&C(035510) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.17 | 0.18 | 471 |
| 2026-05-29T14:04:05.725485 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.47 | +1.80 | 0.33 | 8708 |
| 2026-05-29T14:51:57.466105 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 2969 |
| 2026-05-29T14:51:57.491740 | 솔루스첨단소재(336370) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.60 | +0.69 | 0.09 | 160 |
| 2026-05-29T14:54:43.534709 | 솔루스첨단소재(336370) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.52 | +0.69 | 0.17 | 326 |
| 2026-05-29T14:57:36.021410 | 솔루스첨단소재(336370) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.69 | +0.69 | 0.0 | 498 |
| 2026-05-29T14:57:45.736075 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 3317 |
| 2026-05-29T15:00:57.323972 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.47 | +0.47 | 0.0 | 3509 |
| 2026-05-29T15:06:38.050899 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.34 | 0.0 | 4478 |
| 2026-05-29T15:06:38.059293 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.14 | -0.14 | 0.0 | 4392 |
| 2026-05-29T15:06:40.831992 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.84 | +1.84 | 0.0 | 3971 |
| 2026-05-29T15:06:40.840239 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 3874 |
| 2026-05-29T15:06:43.815487 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.63 | +2.63 | 0.0 | 3855 |
| 2026-05-29T15:06:45.769392 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.61 | +0.61 | 0.0 | 6606 |
| 2026-05-29T15:06:46.897494 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.51 | +0.57 | 0.06 | 4493 |
| 2026-05-29T15:06:46.909135 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.19 | -0.14 | 0.05 | 4401 |
| 2026-05-29T15:06:48.414010 | 기가비스(420770) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.77 | +1.84 | 0.07 | 3979 |
| 2026-05-29T15:06:48.421719 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | -0.11 | 0.0 | 3882 |
| 2026-05-29T15:06:48.442268 | LG이노텍(011070) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.70 | +2.70 | 0.0 | 3860 |
| 2026-05-29T15:08:16.720462 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.12 | +0.23 | 0.11 | 3970 |
| 2026-05-29T15:09:03.934904 | LG에너지솔루션(373220) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.23 | 0.11 | 4624 |
| 2026-05-29T15:09:17.817730 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.85 | 0.48 | 6758 |
| 2026-05-29T15:09:22.151898 | 대덕전자(353200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +0.67 | +0.89 | 0.22 | 4648 |
| 2026-05-29T15:09:28.150404 | 롯데쇼핑(023530) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | -0.03 | 0.0 | 6979 |
| 2026-05-29T15:09:31.997475 | 나무기술(242040) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.23 | 0.46 | 4046 |
| 2026-05-29T15:09:48.745499 | 인텍플러스(064290) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.37 | +0.85 | 0.48 | 6789 |
