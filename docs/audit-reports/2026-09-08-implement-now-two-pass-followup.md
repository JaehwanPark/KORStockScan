# 9/8 implement-now 실제 2-pass 후속 실행

대상 source date: `2026-09-08`. 시작: `23:26 KST`. 사용자 요청: `다음액션 실행`.

## 범위와 원본

22:59의 [61건 분류 ledger](2026-09-08-postclose-monitoring-intake-ledger.json)는 수정하지 않는다. 당시 구현 요청11건은 기존 검증1·증거 차단10이었고 신규 Pass1/2 구현은0이었다. 이번 실행은 그 차단10건의 producer/consumer를 다시 읽고 실제 수정 가능한 보고·계측 계약을 보완하는 별도 작업이다. 원본 JSON은 `/tmp/korstockscan-implement-now-0908.Z7shxZ/`에도 보존했다.

## Pass 1

1. **Scanner BBO receipt parser**: `pipeline_event_logger.py`는 fields를 `str(value)`로 저장하지만 WS 보고서는 source-only 권한과 terminal을 Python boolean으로만 비교했다. 실제 원천의 `"False"/"True"`를 거부해 모든 scheduled episode를 미대사로 세었다. JSON boolean과 로거의 정확한 문자열만 허용하는 tri-state parser로 보완했다. 결측·unknown·숫자0/1·임의 문자열은 권한 근거가 아니다. configuration에서도 unknown을 false로 바꾸지 않는다. 캐시는 v14로 분리했다.
2. **Micro 결손 추적**: venue100/holding payload116의 unique 결손 수를 유지하면서 종목·record·시각·stage·endpoint·evaluation ID와 원본 delivery 값을 workorder에 전달한다. 원인별 unique receipt20개까지, 초과·truncation·전수 count를 명시한다. 이 수정은 진단 근거 보완이며 venue 추정, 누락 payload 정상화 또는 live AI 입력 변경이 아니다.
3. **Pattern AI 구현 가능성**: named currentness check가 PASS인데 generic source-quality 주장이 반복되는 두 native ID는 원본 응답/이유를 보존한다. `pattern_review_actionability_v1`으로 exact failing field/row/consumer 근거 대기를 발급하고 workorder consumer가 이를 `defer_evidence`로 소비한다. generic 파일 목록·pytest 경로만으로 구현 권한을 만들지 않는다. 실제 failed check는 그대로 구현 대상으로 유지한다. Provider 추가 호출은0이다.

Pass1 WS 재생성은 기존 receipt232 episode를 복원했다. 첫 workorder 재생성은 max-orders를24로 지정해 selected31이 됐지만 원래 계약은 max-orders12였다. 최종 controller는 원래12를 사용하며 전수44개 source/native ID는 선택 여부와 무관하게 대사한다. 선택 행 이동을 신규 추천으로 세지 않는다.

## Pass 2

재생성 결과를 재판독해 collector의 실제 `daily_request_budget_rejected`와 `anchor_schedule_latency_exceeded`를 receipt accounting이 누락한 추가 결함을 수정했다. 전자는 bounded rejection, 후자는 `source_quality_not_admitted`로 분리한다. 알 수 없는 상태가 섞이면 계속 미대사이고, schedule 이후 미완결은 rejection으로 덮지 않는다.

당일 전수16,073 episode 보존식은 `232 scheduled_complete + 24 scheduled_receipt_gap + 15,159 bounded_not_admitted + 657 source_quality_not_admitted + 1 admission_receipt_gap`이다. 최초 미대사914→Pass1 682→Pass2 25. **889건의 진단 귀속 수리이지 신규 BBO 요청·체결·순이익 증가가 아니다.** BBO 가격·EV·resolved/right-censored floor 및 full-population 외삽 금지는 변경하지 않았다.

잔여24개 scheduled gap은 과거 PID20318/461794/682672의 episode다. 대표 원본 schedule은09:24:15(code520098),12:20:33(032820),16:21:28(126720)에 각각10개 offset을 명시한다. 현재 저장된 prefix6/9개를 full completion으로 바꾸지 않았다. code130660/`SCANGEN-20318-1788827192975-11103616514905`는 admission receipt 결손1건이다. 모두 원본 인덱스/episode로 분리되며 현재 날짜 재수집으로 복원하지 않는다.

## 남은 경계

| owner/native 범위 | 확인 결과와 남은 acceptance |
| --- | --- |
| BBO join | parser·사유 분류 수리는 구현/재생성 확인. 과거25개 source gap·미완결의 결측 관측값을 유효 가격·완료 표본으로 보간하지 않으며 다음 자연 receipt는 `PostcloseSourceQualityGateReview0908`에서 확인 |
| eligible→heavy / scan conservation | eligible26/1,521 및 ranked279/terminal65/missing214 유지. 원본에 없는 terminal/rank는 합성 불가 |
| WS backoff / both stale / quiet volume | repair-cycle 결손21,662·1,180, cumulative-volume 결손5,692 유지. 추가 resubscribe·주문/guard 변경 없이 같은 기존 품질 owner에서 exact 신규 원천 확인 |
| Micro venue / holding payload | 결손100/116 유지. 진단 receipt 추가는 원본 수리·실전 payload 적용이 아님. 기존 Micro continuity·AI action-outcome owner 유지 |
| Pattern AI 2건 | 구현 가능성 분류 수리는 확인하되 원래 AI 주장 자체는 미해결 증거 대기. `PatternLabSmallNetNaturalEvidence0908`, 기존2/2 Provider budget 유지 |

## 검증과 최종 전달

`korstockscan-review-gate`에 따라 producer→직접 consumer·silent fail·source-only 권한·원본/hash·중복/결손 분리를 재검토했다. 최종 관련8개 suite **395 tests PASS**, Python compile·`git diff --check` PASS. Micro 원본 결손 수100/116 불변, Pattern 원본 Provider 응답 불변, 실제 BBO/경제성 표본과 receipt accounting의 분모 분리를 확인했다.

최종 canonical workorder generation은 `2026-09-08-5b2ea0c29812`(max-orders12, selected25/nonselected19)다. workorder→runtime summary→일반 verifier→tower→checklist→strict verifier의6개 복구 action은 모두 exit0이며, **23:49:33 strict summary/drought handoff PASS → 23:49:34 controller JSON done/cron DONE**을 확인했다. 필수 산출물 누락·downstream 누락·stale downstream은 각각0이다. verifier 전체 상태 warning과 source/economic 결손은 그대로 보존한다.

[후속61건 ledger](2026-09-08-implement-now-two-pass-ledger.json)는 원본과 별도로 저장했다. native 추가0/삭제0, Pattern2건만 `implement_now→defer_evidence`로 바뀌었다. 현재 구현 요청9건=기존 검증1+원천 증거 차단8, 비구현52건=관측28+defer19+reject3+Pattern 증거 대기2다. BBO parser/분류와 Micro provenance는 실제 코드 수리·consumer 검증을 마쳤지만 원래 native root-cause acceptance가 아직 남아, 전체 native 완료 계수 `implemented_pass1/2`에는 넣지 않았다. 이 계수0은 이번 실제 코드 구현이 없었다는 뜻이 아니다. 2-pass 실행·수리 검증 완료와 전체 원천 결손 해결 완료를 분리한다.

finalization의7개 predecessor artifact/log를 읽기 전용으로 다시 대사해 모두 DONE을 확인했다. 이번 수정은 diagnostic parser/provenance/actionability와 요약 consumer에 한정되어 cleanup/raw/archive 또는 detector 구현을 바꾸지 않았고 후행 FAIL도 없다. 따라서 영향받지 않은 cleanup **22:53:19**, detector **22:53:21** receipt를 원래 시각으로 재사용했다. 새 finalization 실행이나 새 detector 검사를 수행했다고 보고하지 않는다. KEPCO custody 원장 SHA `7b168c72466f8baa052c577c8523e1060e8138bed4da8f76518c1e657d5f7174`도 불변이다.

매매 process·env·operator lock·주문·수량·threshold·Provider route 변경, 새 Provider 호출, API budget 상향, 외부 Project/Calendar sync, commit/push/merge는 수행하지 않았다. 전체 implement-now 결손이나 실제 submit drought/순이익 개선 완료를 주장하지 않는다.

최종 문서 검증: print-only backlog parser exit0/count42, 후속61건의 owner/native ID 유일성·보존식·실제 source pointer/decision/hash 전수 대사 PASS, 원본 ledger hash 불변. 9/9 기존 `CodeImprovementWorkorderReview0909`에 남은 acceptance를 연결했고 신규 중복 체크박스는 만들지 않았다. 체크리스트 문구 보완 후 summary/drought handoff를 읽기 전용으로 재검사해 모두 PASS다.
