# Main 제출 모니터의 native 필수 입력 부족 계약 수리 — 2026-10-15

17:09/17:11 artifact_freshness 실패는 공통 주문 원장 장애의 재발이 아니다. 현재 d05ebbf87/PID2470537의 원장·프로세스는 정상이며, native producer가 설명한 필수 입력 부족을 observer가 미분류 오류로 처리하는 소비 계약 누락을 확인했다. 기존 통합 배포·재기동 승인의 결함 보완 범위다. 배포는 `DirectFamilyPreopenPolicyHandoff`, 원천 자연 수용은 `NonfixedDispatchReadinessReview1012`, 실제 AI→제출 연결은 `AuxiliaryCircuitRecoveryRepair1012`의 기존 Acceptance를 유지한다.

## 원본과 원인

고정한 observer는17:05:40.465512/run c525474eb2174f3c8a05fe751a255f0d다. 라온시큐어042510의16:59:52.154602/17:03:01.857161 두 probe는 `required_feature_insufficient / required_branch_feature_missing`을 기록했다. AL/SOR 원천·PID/start·family/scope·native epoch/sequence가 일치하며, legacy branch FALSE/manual branch UNKNOWN이다. manual branch의120초 필요 구간 대비 실제 관측57.398/58.411초로 ret/volume/backward_window가 부족했다. pending·historical TRUE·source censored는0이며 UNKNOWN 누적37/82다.

producer `zero_base_probe.native_wait_result`는 이 결과를 명시적으로 발행하지만 observer는 no-match 또는 pending만 검증해 `required_feature_insufficient_unclassified`로 처리했다. 알려지지 않은 진단 때문에 기존 bounded source warning 수용이 거부됐고, `source_observation_counts_invalid`도 함께 표시됐다. 관측 건수 자체의 오류는 아니다. 같은 구간49개 probe 중 원천 충족9개라는 실제 부족은 유지한다.

Main 평가10개 중 provider 분모5개, 실제 AI5회(PASS3/CAUTION2)다. PASS 중196170/aims-872fa3742b6f38238929는16:59:26 broker accepted를 기록했다. 다른 PASS2개는 latency_block이다. scanner 식별0을 모든 평가·제출0으로 해석하지 않는다. 주문 접수는 체결·경제성 증명이 아니다.

## 수리와 검증

기존 monitoring package의 receipt 검증을 재사용하고 branch readiness v2와 exact native identity, truth/missing_inputs를 추가 대조한다. 유효한 경우에만 `machine_probe:required_branch_feature_missing`과 별도 검증 census로 보존한다. 원천 충족·기계 평가·no-match·provider·주문 건수에 더하지 않는다. missing/tampered/stale/wrong PID·다른 세대·boolean count·pending/TRUE/censored 증거는 기존 fail-closed 경로에 남긴다. health consumer도 census 건수와 안전 플래그를 독립 검증한다.

intraday handoff는 원 PREOPEN source SHA에서 이번 검토본의 정확한 SHA로만 연결한다. 임의 변경을 허용하는 예외는 추가하지 않는다. Kiwoom wire 요청·응답·FID·복구 프로토콜, 전략·수량·hard safety·수동 이관은 변경하지 않는다. 원장 복구 인식 reader와 기존7b2e421e3/보유 계약 통합을 보존한다.

구현→자체 리뷰→native identity 타입 보강→재리뷰→표적 검증을 완료했다. monitor/최종 artifact consumer/handoff 회귀2,386개 PASS. 원본 두 행의 격리 검증과 고정 observer 재생에서 기존 모든 관측·원천 충족·평가·no-match 건수 및 원천 issue가 불변이고, health는 `not_eligible`에서 기존 `bounded_source_quality_observation / warning_pending`으로 바뀐다. `full_coverage_proven=false`, runtime/정책 적용 권한 false를 유지한다. 해당 범위 미해결 코드 결함0이다.

[원본·고정 구간 재생·시험 로그](../../tmp/submission-observer-alert-20261015-1710/)를 보존한다. broad report 재생성·provider 재호출·검증용 주문·외부 동기화는 실행하지 않는다. 실제 배포·정규 observer와 detector의 동일 run 수용은 별도 영수증으로 후속 기록한다. 원천 전체 충족과 경제성 개선은 이 수리의 완료 조건이 아니며 입증하지 않았다.

## 배포·정규 소비 수용

수정 df2afffa7은17:33:11 ordered complete/pass, PID2516478/start11706324에서 소비됐다.17:36:13.584013 자연 observer의 필수 입력 부족1건은 verified1/unclassified0, source coverage/admission/no-match false를 유지했다.17:37:23 detector가 동일 run/health를 소비했고 실패0이었다. [첫 실제 수용](../../tmp/submission-observer-alert-20261015-1710/postdeploy-verification.json), [자연 부족 원천](../../tmp/submission-observer-alert-20261015-1710/natural-feature-gap-acceptance.json).

그 사이 기존 PID의 별도 보유 사전 순회 경합이 확인돼 [추가 수리](main-holding-context-dictionary-race-repair-2026-10-15.md)를 통합했다. 최종 배포 코드는3803938c7dec2c50fb7e24270a527f3e48dd66bd이며17:43:44 재기동, PID2527556/start11769546이다.17:47:02 정규 detector의 실패0, 현재 observer 동일 run/health 소비 및 원 PREOPEN/정책/수동 제외/누적 등록 대기 원본 불변을 확인했다. [최종 수용](../../tmp/holding-context-race-20261015-1730/final-acceptance.json).

원천 관측 부족과 기존 holding_exit_sentinel_aftermarket_report stale·장후 최종화 지연 경고는 남는다. 전체 coverage·자연 제출 전체 성공·경제성을 완료로 표시하지 않는다.
