# Scalp Sim AI Deferred Review 2026-06-19

- generated_at: `2026-06-19T15:50:17`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-19.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `102`

## Defer Reasons

- `sim_ai_budget_exhausted`: `102`

## Critical Classes

- `non_critical`: `1`
- `soft_critical`: `101`

## Critical Reasons

- `feature_signature_changed`: `101`
- `legacy_critical_zone`: `80`
- `near_safe_profit_band`: `12`
- `normal_review`: `1`
- `soft_loss`: `43`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-19T09:13:27.757308 | 시프트업(462870) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.88 | +0.88 | 0.0 | 374 |
| 2026-06-19T09:14:09.553063 | 에코프로에이치엔(383310) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.79 | +0.79 | 0.0 | 290 |
| 2026-06-19T09:16:52.429942 | 에코프로에이치엔(383310) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.21 | +0.79 | 0.58 | 453 |
| 2026-06-19T09:16:53.037398 | 대한전선(001440) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.40 | +1.40 | 0.0 | 454 |
| 2026-06-19T09:17:03.891008 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.21 | +1.21 | 0.0 | 391 |
| 2026-06-19T09:17:07.827764 | ISC(095340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.43 | +1.43 | 0.0 | 395 |
| 2026-06-19T09:21:15.863287 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | -0.32 | 0.0 | 536 |
| 2026-06-19T09:21:15.900774 | 리가켐바이오(141080) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.78 | +1.78 | 0.0 | 536 |
| 2026-06-19T09:21:17.803123 | 인탑스(049070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.46 | -0.46 | 0.0 | 351 |
| 2026-06-19T09:25:52.279336 | 인탑스(049070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 626 |
| 2026-06-19T09:25:55.315994 | 위더스제약(330350) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.89 | +0.89 | 0.0 | 276 |
| 2026-06-19T09:29:11.528406 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.03 | +0.03 | 0.0 | 1011 |
| 2026-06-19T09:29:14.724218 | 인탑스(049070) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 828 |
| 2026-06-19T09:32:13.734483 | 리가켐바이오(141080) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.37 | 0.0 | 1194 |
| 2026-06-19T09:32:18.302807 | SK네트웍스(001740) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.51 | +0.51 | 0.0 | 1012 |
| 2026-06-19T09:32:18.413032 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.22 | +1.22 | 0.0 | 659 |
| 2026-06-19T09:32:18.483230 | 위더스제약(330350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.25 | +5.25 | 0.0 | 659 |
| 2026-06-19T09:35:51.871986 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.99 | +1.22 | 0.23 | 872 |
| 2026-06-19T09:43:56.156239 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.84 | +0.84 | 0.0 | 1357 |
| 2026-06-19T09:50:59.998136 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.91 | +2.91 | 0.0 | 1780 |
| 2026-06-19T10:00:41.868649 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.98 | +3.98 | 0.0 | 2362 |
| 2026-06-19T10:00:42.448776 | LS머트리얼즈(417200) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.34 | 0.0 | 1561 |
| 2026-06-19T10:00:46.090759 | SK(034730) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.36 | 0.0 | 1416 |
| 2026-06-19T10:01:09.662684 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.56 | +1.56 | 0.0 | 597 |
| 2026-06-19T10:04:15.301398 | 비나텍(126340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +5.89 | +5.89 | 0.0 | 2576 |
| 2026-06-19T10:04:22.722767 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.41 | +1.56 | 0.15 | 790 |
| 2026-06-19T10:04:54.745681 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.09 | +0.09 | 0.0 | 314 |
| 2026-06-19T10:07:02.550316 | SOL 자동차TOP3플러스(466930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.96 | +1.96 | 0.0 | 950 |
| 2026-06-19T10:07:02.650332 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.23 | +1.39 | 0.16 | 795 |
| 2026-06-19T10:09:31.794488 | LS머트리얼즈(417200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.18 | +1.18 | 0.0 | 2091 |
| 2026-06-19T10:09:35.397193 | 현대차(005380) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.91 | +1.39 | 0.48 | 948 |
| 2026-06-19T10:09:35.438280 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.05 | +0.12 | 0.07 | 595 |
| 2026-06-19T10:15:50.062983 | RISE 200위클리커버드콜(475720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.35 | -0.23 | 0.12 | 424 |
| 2026-06-19T10:16:02.584256 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.23 | 0.13 | 436 |
| 2026-06-19T10:17:53.338520 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.75 | +0.75 | 0.0 | 1093 |
| 2026-06-19T10:20:31.147864 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.86 | +0.86 | 0.0 | 1251 |
| 2026-06-19T10:20:31.239167 | RISE 200위클리커버드콜(475720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.29 | -0.23 | 0.06 | 705 |
| 2026-06-19T10:20:31.358871 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | -0.23 | 0.09 | 705 |
| 2026-06-19T10:24:29.705141 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.17 | +1.17 | 0.0 | 1489 |
| 2026-06-19T10:24:29.727047 | RISE 200위클리커버드콜(475720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 944 |
| 2026-06-19T10:24:29.751969 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.22 | -0.22 | 0.0 | 944 |
| 2026-06-19T10:28:53.314229 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.20 | -0.20 | 0.0 | 1207 |
| 2026-06-19T10:32:39.975019 | RISE 200위클리커버드콜(475720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.26 | -0.17 | 0.09 | 1434 |
| 2026-06-19T10:32:40.138240 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.29 | -0.20 | 0.09 | 1434 |
| 2026-06-19T10:32:40.247579 | 에스에이엠티(031330) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.49 | +2.49 | 0.0 | 661 |
| 2026-06-19T10:32:40.346339 | 아바텍(149950) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.40 | +0.57 | 0.97 | 661 |
| 2026-06-19T10:39:37.299637 | RISE 코리아밸류업(495050) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.36 | 0.0 | 1851 |
| 2026-06-19T10:39:37.395287 | 에스에이엠티(031330) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.86 | +0.86 | 0.0 | 1078 |
| 2026-06-19T10:39:37.467285 | 아바텍(149950) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.28 | +0.28 | 0.0 | 1078 |
| 2026-06-19T10:39:40.245951 | TIME 코스피액티브(385720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | -0.47 | 0.0 | 596 |
| 2026-06-19T10:46:37.561584 | DB하이텍(000990) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.42 | -0.42 | 0.0 | 734 |
| 2026-06-19T11:08:43.742242 | 리노공업(058470) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.44 | -0.44 | 0.0 | 1517 |
| 2026-06-19T11:09:53.174340 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.84 | +1.84 | 0.0 | 384 |
| 2026-06-19T11:23:15.667896 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.42 | +1.42 | 0.0 | 1186 |
| 2026-06-19T11:23:19.368882 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.28 | -0.28 | 0.0 | 977 |
| 2026-06-19T11:26:26.718925 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.11 | -0.11 | 0.0 | 1164 |
| 2026-06-19T11:29:24.323856 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.70 | +1.77 | 0.07 | 1555 |
| 2026-06-19T11:29:25.959425 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 1344 |
| 2026-06-19T11:29:49.402938 | 상지건설(042940) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.83 | +0.83 | 0.0 | 387 |
| 2026-06-19T11:29:49.966820 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.26 | -0.23 | 0.03 | 388 |
| 2026-06-19T11:32:30.388562 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.49 | +1.77 | 0.28 | 1741 |
| 2026-06-19T11:32:32.383842 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.05 | -0.05 | 0.0 | 1530 |
| 2026-06-19T11:39:48.838026 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.35 | +2.35 | 0.0 | 2180 |
| 2026-06-19T11:39:48.878550 | 삼성생명(032830) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | -0.43 | 0.0 | 1967 |
| 2026-06-19T11:39:50.252791 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.06 | +0.06 | 0.0 | 1968 |
| 2026-06-19T11:39:50.321985 | 심텍(222800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.31 | -0.31 | 0.0 | 988 |
| 2026-06-19T11:39:51.596297 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | -0.13 | 0.0 | 989 |
| 2026-06-19T11:43:40.336298 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.12 | +0.12 | 0.0 | 2198 |
| 2026-06-19T11:43:40.457931 | 심텍(222800) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | -0.08 | 0.0 | 1218 |
| 2026-06-19T11:43:41.898233 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | -0.03 | 0.0 | 1220 |
| 2026-06-19T11:47:05.282055 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.39 | -0.28 | 0.11 | 4042 |
| 2026-06-19T11:47:06.975958 | 삼성생명(032830) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | -0.03 | 0.0 | 2405 |
| 2026-06-19T11:47:08.372695 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.19 | +0.19 | 0.0 | 2406 |
| 2026-06-19T11:47:12.753295 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | -0.02 | 0.0 | 1430 |
| 2026-06-19T12:06:24.142290 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.17 | -0.17 | 0.0 | 3562 |
| 2026-06-19T12:06:27.394653 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.32 | -0.32 | 0.0 | 2585 |
| 2026-06-19T12:10:20.360641 | RISE 200(148020) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.38 | -0.17 | 0.21 | 3798 |
| 2026-06-19T12:10:21.824638 | PLUS 200(152100) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.49 | -0.32 | 0.17 | 2819 |
| 2026-06-19T13:35:59.396987 | 한울앤제주(276730) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.70 | +1.70 | 0.0 | 2655 |
| 2026-06-19T13:36:03.756473 | TIME 코리아밸류업액티브(495060) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.09 | +0.09 | 0.0 | 2297 |
| 2026-06-19T13:36:03.791389 | PLUS 글로벌HBM반도체(442580) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.11 | +0.11 | 0.0 | 2297 |
| 2026-06-19T13:36:05.424813 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.46 | +0.46 | 0.0 | 2299 |
| 2026-06-19T13:40:13.082549 | TIME 코리아밸류업액티브(495060) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.02 | +0.09 | 0.07 | 2546 |
| 2026-06-19T13:40:13.117885 | PLUS 글로벌HBM반도체(442580) | `sim_ai_budget_exhausted` | `non_critical` | `normal_review` | +0.14 | +0.14 | 0.0 | 2546 |
| 2026-06-19T13:40:14.718070 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.57 | +0.57 | 0.0 | 2548 |
| 2026-06-19T14:01:39.843977 | 위더스제약(330350) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.25 | +1.25 | 0.0 | 1532 |
| 2026-06-19T14:17:46.139787 | RISE 200위클리커버드콜(475720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 4799 |
| 2026-06-19T14:17:46.203239 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.57 | +0.57 | 0.0 | 4800 |
| 2026-06-19T14:17:47.521065 | 피앤에스로보틱스(460940) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.35 | +3.35 | 0.0 | 2500 |
| 2026-06-19T14:17:50.546932 | TIME 미국나스닥100액티브(426030) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.07 | +0.07 | 0.0 | 1259 |
| 2026-06-19T14:17:50.589144 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.80 | +0.80 | 0.0 | 1259 |
| 2026-06-19T14:17:50.684817 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.02 | +1.02 | 0.0 | 1259 |
| 2026-06-19T14:44:33.434986 | SK스퀘어(402340) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.06 | +0.06 | 0.0 | 6407 |
| 2026-06-19T14:44:34.886030 | 피앤에스로보틱스(460940) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.71 | +1.71 | 0.0 | 4107 |
| 2026-06-19T14:44:36.237890 | TIME 미국나스닥100액티브(426030) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.15 | -0.15 | 0.0 | 2865 |
| 2026-06-19T14:44:36.353103 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.14 | +0.14 | 0.0 | 2865 |
| 2026-06-19T14:44:36.462274 | 화신(010690) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +3.73 | +3.73 | 0.0 | 2865 |
| 2026-06-19T15:15:29.570335 | TIME 글로벌AI인공지능액티브(456600) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.36 | -0.36 | 0.0 | 5962 |
| 2026-06-19T15:15:29.912004 | TIME 미국나스닥100액티브(426030) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | -0.03 | 0.0 | 4718 |
| 2026-06-19T15:15:30.151580 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.62 | +2.62 | 0.0 | 4719 |
| 2026-06-19T15:15:30.554004 | 한화엔진(082740) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.77 | +0.77 | 0.0 | 3482 |
| 2026-06-19T15:15:47.633065 | RISE 미국AI밸류체인데일리고정커버드콜(490590) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 1892 |
