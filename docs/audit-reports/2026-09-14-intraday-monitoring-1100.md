# 2026-09-14 장중 모니터링 11:00 리뷰

- 관찰 범위: 2026-09-14 KST 장전부터 11:00:16까지
- 판정: `YELLOW`
- 기준: 장중 지시문과 9/14 체크리스트의 11시까지 도래 항목

## 런타임과 배포

11:00:16 현재 메인 PID는 `230444`, cwd는 `runtime-entry-lifecycle-r4-20260914/src`, commit은 `a3170943`이다. `threshold_runtime_env_verify_2026-09-14.json`은 `status=pass`, `pid=230444`이며 1주 split-probe 설정과 `position_sizing_dynamic_formula:2026-09-11`이 유지된다. 10:09:50의 PID `173304`, 10:43:53의 PID `222298`, 10:49:36의 PID `230444` 전환은 병행 승인 복구 배포였고 각 successor는 선행 commit을 포함했다. 마지막 PID에서 detector PASS, pipeline/AI trace 증가와 신규 source 소비를 확인했다.

독립 매매기계 systemd drop-in 17개는 10:12에 successor 공통 형상으로 갱신했다. 당시 실행 중인 주문 owner는 custody 보존을 위해 강제 재기동하지 않았고 다음 자연 기동부터 갱신 root를 소비하도록 했다. CJ CGV morning preflight의 기존 quarantine 실패 외 새 독립 기계 실패는 없었다.

## Entry AI와 submit

10:32:18 키다리스튜디오 `020120`은 기계 `ENTER_NOW` 뒤 AI가 `CAUTION/ADVERSE_TAPE`를 반환했으나 contradiction fact에는 `liquidity_adverse`만 결속해 `entry_risk_code_fact_binding_invalid`로 semantic reject됐다. 최종 `WAIT`, submit 0은 invalid 응답의 fail-closed 결과이며 AI PASS가 WAIT로 잘못 매핑된 사례가 아니다. 이 행은 장후 prompt/input 품질 개선 표본으로 남긴다.

10:41 대한광통신 `010170`은 V2.15.2 동일 bundle에서 기계 `ENTER_NOW`와 AI `PASS`가 결속됐고 `entry_machine_pass_submit_candidate=true`로 기존 submit guard에 전달됐다. 이후 정상 동적 수량 3주, 주문가 14,320원, broker 주문번호 `0031943`으로 실제 제출됐다. 따라서 `ENTER_NOW + AI PASS -> BUY 후보 -> submit`의 코드·배포·최초 자연 소비는 확인됐다. fill/terminal과 비용 차감 순이익은 아직 별도 acceptance다.

11:00 buy-funnel은 KRX 정규장 `ai_confirmed=245`, `budget_pass=10`, `latency_pass=3`, `order_bundle_submitted=1`이며 exact attempt key 결손과 stage-order 위반은 0이다. primary는 여전히 `SUBMIT_DROUGHT_CRITICAL`, secondary는 `LATENCY_DROUGHT|UPSTREAM_AI_THRESHOLD`다. 현금 부족 제외 계약은 유지되지만 10:03 코스메카코리아 `blocked_zero_qty`는 broker cash capacity가 4주로 양수인 반면 tier target budget이 1주 가격보다 작아 생긴 `guard_intended_zero`이므로 broker-proven cash shortfall로 재분류하지 않았다.

## 원천·오류·observer

10:26 I/O wait 42.75% 경보는 36.11%를 거쳐 10:29 detector PASS로 회복했다. PID·출력 정지는 없었다. 10:45:57 DB하이텍 holding-score OpenAI 단발 timeout은 fail-closed됐고 10:47 detector PASS로 회복했다. 반복 burst, crash loop, broker 오류는 관찰되지 않았다.

11:00 micro collector는 `healthy_observer_canary_with_source_row_exclusions`, stop=false다. 0B/0D callback은 54,914/59,005, callback p95/p99는 0.099/0.124ms, queue/drop/worker/writer error는 모두 0, writer 3/3 alive, sequence gap 0이다. invalid depth timestamp 14건은 receipt 14/14로 격리됐고 최소 free bytes는 약 28.2GB다. `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. through-close와 경제성 수용은 OPEN이다.

## 체크리스트 대사

- `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0914`: 정상 수집 중, through-close가 남아 OPEN.
- `SimProbeIntradayCoverage0914`: 당일 실주문 authority leak 0, 비우선 sim 자연 입력 0으로 완료.
- 14:20 이후 source-quality, 15:25 이후 SOR canary와 장후 항목: 11시 현재 `not_yet_due`.
- 현재 시각까지 도래한 OPEN의 미분류는 0이다.

코드 변경은 하지 않았다. 첫 AI PASS submit과 source 상태는 자연 증거이며 비용 차감 경제성 개선을 확정하지 않는다.
