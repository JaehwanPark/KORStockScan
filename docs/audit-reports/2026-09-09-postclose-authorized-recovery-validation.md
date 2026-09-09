# 9/9 후속 승인 복구 검증 — hash-bound evidence

Source9/9, user approval22:50:32 KST, execution effective9/10. 이 문서는 처리 companion의 비순환 코드/테스트 근거이며 이후 최종 요약/상태를 덮어써 갱신하지 않는다. 실행·source hash와 최종 판정은 [후속 리뷰](2026-09-09-postclose-authorized-recovery-review.md)에 따로 기록한다.

## 구현·재리뷰 범위

- one-share implemented source-only 기존 family의 잘못된 반복 implement-now 승격 제외. 실제 source gap의 escalation은 유지.
- machine pre-enqueue census/closed/lossless receipt 검증과 마지막 exact epoch 제한. market/depth/reference 세 입력 모두 epoch fence. R0/Provider 전역 hold·과거 유실·실주문 권한 비변경.
- main Micro delivery의 명시적 sim-only390평가 분리. 실제 order/record/owner 충돌과 unknown authority는 계속 검출. 실제 main raw는 보존.
- workorder 직접 consumer 명시 및 report-only panic lifecycle의 원래 provenance 비권한 필드를 최상위 native row에도 명시. panic SELL action/guard 변경 없음.
- scanner bounded rejection count0을 horizon 미발행으로 구분. 선언된 rejection·episode ID·네 비권한 필드 검증, 실제 schedule0/invalid 권한은 fail-closed. 같은 시각 다른 status/count/authority의 dedup 방지, cache v16. 실제330 generation 완전/metadata conflict0. 과거 raw를 합성하지 않은 parser 수리다.
- 9/10 저가주 기존 numeric1변경·기존1재확인·신규3, dated transition/evidence/preflight/launcher/timer와 standing authority19종목 승계. 두10주 leg·기존 custody/target·기존 quarantine3 유지. 현재 매매 service는 기동하지 않음.

## 검증

통합17개 targeted test 파일 **884 PASS**. 이후 report-only 최상위 권한 누락 보완은 workorder/runtime-summary/intake **211 PASS**. 앞선 부분288/428/187/310/273/6을 고유 합계로 중복 합산하지 않는다. Python compile, shell syntax, systemd 신규6timer verify 및 git diff --check PASS.

재리뷰: zero rejection 뒤 실제 schedule을 같은 timestamp로 입력한 첫 회귀5실패를 fingerprint로 수정한 후273 PASS. 미래 policy에서는9/8→9/10 두 revision을 건너도 승인 ID만 overlay하고 미승인 actual policy binding을 보존하는6개 회귀 PASS. 증거 canonical hash의 float 직렬화 차이는 파일 실측 hash로 재결속 후 검증했다. 문서/owner 변경은 print-only parser44행 PASS이며 외부 Project/Calendar sync/token 검사는 하지 않았다.

이 변경 범위의 미해결 코드 review finding0과 남은 원천 결손을 분리한다. 아래11요청을 구현 완료라고 주장하지 않는다. 각 native source의 consumer 메타데이터만 고쳐 원래 결손을 완료 처리하지도 않는다.

## 남은 native 요청의 최초 결손/수용조건

| Native ID | 현재 근거와 남은 조건 | 기존 acceptance owner |
| --- | --- | --- |
| `order_entry-prompt-revision-8d1f2fb1740c1769eec7ede1` |13 exact case의 비용 source_unavailable. parent V2.14/영문 초안 보존. distinct reviewed version/hash·동일부모 비용 비교 입력 결속 전 Provider/선정 변경 금지 | AIDecisionActionOutcomeNaturalEvidence0908 |
| `order_entry-prompt-revision-f7e1931a9128531084ba87ac` |2 exact case의 동일 비용/버전 결손. 새 원천 없이 replay를 반복하지 않음 | AIDecisionActionOutcomeNaturalEvidence0908 |
| `order_microstructure_v3_evaluation_anchor_contract_missing` |302430,14:31:32.351393, evaluation d72b1fba9baf439e921764ccfadf58f9의 record_id 결손. UUID/시간만으로 record를 발명하지 않음. exact 원 record/receipt 필요 | AIDecisionActionOutcomeNaturalEvidence0908 |
| `order_microstructure_v3_evaluation_venue_missing_or_conflicting` |main162evaluation의 micro venue 결손, 예000990/record41611/08:07:15.473700. effective venue와 micro 원천 route를 동일하다고 추정하지 않음 | AIDecisionActionOutcomeNaturalEvidence0908 |
| `order_observation_source_quality_unknown_token_provenance_gap` |4stage: stat score_prior neutral_or_unknown449, source-fetch census UNKNOWN rows1809 및 venue10, candidate-pool UNKNOWN rows200, holding free-text reason1. 의미/producer/source-only 권한 검증 없이 UNKNOWN→KRX·정상으로 치환 금지. retired stat 원천은 재활성화/성과 수리 대상이 아님 | PostcloseRecoverySourceAcceptance0908 |
| `order_pipeline_event_compaction_v2_shadow` |raw291147/producer290196,951결손,20:01:59 flush deadline초과. 원래 producer terminal/flush receipt 없는 구간을 raw-derived summary로 덮어 parity를 승인하지 않음. raw suppressionOFF 유지 | PostcloseRecoverySourceAcceptance0908 |
| `order_scanner_eligible_no_heavy_closed_loop` |eligible1795중9 미소비, KRX4/NXT5. exact executable BBO 최초결손 KRX2/NXT1. 후단 safety·무노출을 scanner 미발견과 합치지 않음 | ScannerLookupAttentionNaturalEvidence0908 |
| `order_scanner_funnel_executable_bbo_join` |공식master유효16674중 BBO1155(6.927%); venue별 분리, primaryEV null. bounded observer를 전수탈락으로 외삽하지 않음. 당시 exact BBO/terminal 원천 없는 row는 재생성으로 복구 불가 | ScannerLookupAttentionNaturalEvidence0908 |
| `order_ws_decision_stage_stale_backoff_attribution` |snapshot/decision queue/backoff의 exact epoch·receipt 결손은 살아 있는 상태로 보고. count만으로 외부/내부 원인이나 정책 개선을 발명하지 않음 | ScannerLookupAttentionNaturalEvidence0908 |
| `order_ws_total_stale_escalation` |raw stale 발생과 source/route freshness 근거를 유지. 새 수신 receipt 없이 resubscribe/재기동/guard 완화로 수용조건을 바꾸지 않음 | ScannerLookupAttentionNaturalEvidence0908 |
| `order_ws_trade_tick_quiet_low_liquidity_classification` |0B quiet와 정상 저유동성의 분류에 필요한 ordered route/epoch·시장 거래 근거 부족. quiet를 healthy나 장애로 임의 정규화하지 않음 | ScannerLookupAttentionNaturalEvidence0908 |

이 표의 차단은 기존 직접 원천/정의 결손이다. 진단 코드 수리에 새 양수EV·실주문·all-horizon floor를 붙인 것이 아니다. report·test만 완료된 원인은 단계별 repair 상태로 보존하고, native order의 원래 acceptance가 닫히기 전에는 `blocked_missing_evidence`로 유지한다.

## RED와 다음 실행 경계

machine signal18/eligible0:17신호는 검증된14:41:37 epoch 이전, widget NXT17:55 신호는 마지막 exact raw14:42:44 이후다. manual exit timestamp 결손6도 남는다. source-only helper가 검증된 epoch를 읽었다고 과거 BBO/체결시각을 복원한 것이 아니다. controller의 requires_structural_repair를 삭제/완화하지 않는다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0909` 및 다음 checklist의 동일경로 원천 확인을 따른다.

별도 승인5추천은 원본 native ID/row/hash의 successor ledger에만 기록한다. 이는72행과 더할5개 고유 작업이 아니다. 원래 source-only recommendation decision을 live로 덮어쓰지 않고 별도9/10승인·기존guard·설치receipt·미래정책/PID/경제성을 구분한다. 미승인 adaptive-exit numeric envelope/첫 실거래는 발명하지 않는다.
