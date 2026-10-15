# Main 가격 전진·회복 12가설 구현 검토 — 2026-10-15

## 1. 범위와 결정

사용자 “구현하고 코드리뷰 후 수정보완 반복”에 따라 [정책 반영 계획](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md) §10의 A17~A20·F23~F30을 구현했다. 기존 실행본 `d05ebbf8770cb63b51a4ae57e9d2924de3fdf975`에서 격리한 `/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015`, branch `codex/entry-progress-cumulative-20261015`가 작업본이다. 운영 코드·데이터와 다른 세션의 미커밋 변경은 이 작업본에 공유하지 않았다.

검토 상태: **구현·자체 리뷰·수정보완·재리뷰·격리 검증 완료 / private 준비 완료**. 추가 연구는 기존 38가설과 별도 불변 버전으로 등록한다. 기존 정의 1,430개와 registry SHA `2d94b2f9dbf86b722ad3fa06d87636b23dc8b80eb74aff484e5bcc5291c7d22f`를 보존했다. 새 resource는 전체 50가설의 3,510개 exact-scope 정의를 포함한다. 원 보조 입력/응답·프롬프트·provider·수동관리·보유 수리 코드는 변경하지 않았다.

최신 연구 result SHA는 `5210ddad3d5ec1c74b942cbf6b49b65d2ecd9c44d8d963644487e4f4654b8363`, manifest SHA는 `8f60c9f3f894650cf0841a49f971a047386553849adfd73bf68ed98bfd6b09a7`이다. parent bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`와 cost .0023·실제 ask·+0.4%/-3%·1800초 label은 유지했다. 승률→W 수→동일 membership current→고정 ID 기준이며, 새 성공 보존율·최소 표본/날짜·holdout·EV gate를 추가하지 않았다.

## 2. 구현 소유권

새 Python engine-root 모듈은 만들지 않았다. 역할은 기존 scalping catalog/runtime/registration/postclose, 회귀는 `src/tests`가 소유한다.

| 소유 파일 | 구현 |
|---|---|
| [고정 resource](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_price_progress_data.json), [catalog](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_cumulative_catalog.py) | 사전 고정 50가설·48 scope, 버전별 결과/정의/그룹/제안·registry 검증. 기존 resource와 ID/hash 보존 |
| [runtime](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_cumulative_runtime.py), [공유 State](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_extended_state.py) | 연속 10체결 가격·bid, 30초 bid 앵커, 현재 spread 대비 범위/전진. 최초 bid 상승 뒤 체결가·bid 1/3초 유지와 확인 후 ready 무효화 |
| [등록](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_cumulative_registration.py), [v6 consumer](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/continuous_reversal_policy_v6.py) | 기존/신규 batch를 구분한 prepare·source archive·intake·manifest/보조 승계. 기존 pending 충돌·parent CAS·날짜·코드 봉인 유지 |
| [장후 계산](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/engine/scalping/reversal_cumulative_postclose.py) | 등록한 버전의 고정 대안만 비교. feature/truth/label 재사용, immutable checkpoint, 압축 비교표, 현재/선정 요약과 보조 membership 연결 |
| [새 회귀](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/src/tests/test_reversal_price_progress.py) | 독립 prefix 계산·인과 root·실패 후 재사용 금지·UNKNOWN/OR·route·구버전·보조 승계·pending 충돌·hash cache 변경 격리 |

가격 특징은 연속 유효 체결 10개, bid 특징은 같은 구간의 quote 연속성이 필요하다. quote만 결손이면 가격 특징은 보존한다. 30초 앵커는 그 시각 이하의 마지막 실제 row를 사용한다. F UNKNOWN은 원 확인점 보존, A UNKNOWN은 불일치다. source 단절 뒤 창·pending은 재설정한다.

A17/A18은 원 FIRST 이후 **처음** bid가 상승한 지점을 소비한다. 그때 체결가가 원 FIRST보다 낮거나, quote/native가 끊기거나, 원 저점 이탈·30초 만료·유지 중 체결가/bid 후퇴이면 같은 시도를 다시 사용하지 않는다. 확인 뒤 5초 claim 대기 중 bid가 후퇴해도 해당 ready를 제거한다. A19/A20은 기존 인과 구조/VWAP root와 유지 계약을 사용하고 새 확인점 필터를 붙였다.

## 3. 리뷰에서 보완한 사항

1. **기존 등록 파손:** 새 정의를 기존 catalog의 단일 해시에 합치면 이미 접수된 38가설 등록이 무효화된다. 기존 registry를 고정하고 신규 registry와 결과 SHA별 그룹·해시·승계를 추가했다. 기존 승인에 새 batch 이름만 붙여도 통과하지 않는다.
2. **무관측 범위 누락:** 관측 22 scope만 구현하면 나머지 가격대가 사라진다. 새 catalog에 48개를 모두 열거하고 무확인은 current로 남겼다. 전체 운영 구조 128 scope를 검증했으며 독립 KRX/NXT/SOR 원천을 복제하지 않는다. 새 가설 등록 대상은 연구로 고정한 48 scope, 다른 80 scope는 실제 current를 유지한다. 원천에 없는 종목·route를 학습한 것으로 부르지 않는다.
3. **장후 버전 혼합:** 정제 child 계산·variants·선정·요약·보조 initial binding이 기존 38가설 전역 상수를 읽던 부분을 등록 batch의 불변 자료로 바꿨다. 구버전 장후에서 신규 F를 평가하거나 신규 26개 무확인 scope 요약에서 KeyError가 나지 않도록 했다.
4. **호가 유지의 빈틈:** 가격만 유지돼도 bid가 후퇴할 수 있다. 최초 bid 상승의 소비·양쪽 유지·정확한 turn/root/confirmation 순서·quote 연속성 proof 및 ready 제거를 추가했다. 기존 보조 phase/prompt는 그대로 사용한다.
5. **반복 해시 계산:** 매 평가마다 3,510개 고정 정의를 다시 digest하던 비용을 import 시 해시 검증한 resource에서 한 번 유도한 불변 tuple로 재사용한다. 요청에는 새 dict를 반환해 변조가 cache에 전파되지 않으며 요청·정의·그룹·batch 검증은 유지한다.
6. **등록 충돌:** 새 private 준비안이 있어도 기존 `c15491190e72…` 등록을 덮어쓰지 않는다. 격리 intake 반례에서 기존 pending과 current가 byte 그대로 남는 것을 확인했다. [실제 기존 등록 reader](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/existing-registration-reader.json)도 새 코드에서 기존 등록과 보존 근거5개를 읽고 원 bytes 불변을 확인했다. 같은 parent의 다른 등록 요청과 consumed 재적용 방지도 기존 계약을 유지한다.

## 4. 검증

- [최종 회귀](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/final-review-tests.log): **214 passed**. 초기 160 PASS+1 실패는 작업본 `.venv` 경로 부재였으며, 프로젝트 가상환경 연결 후 해당 반례를 재검증하고 최종 전체 집합도 통과했다. 구현 전 구버전 테스트 fixture의 정의 집합을 legacy와 합집합으로 구분한 실패 이력도 원 로그에 남겼다.
- [대안 대조](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/variant-validation.json): 고정 표현84,798개 중 원 연구의 **35,558개 대안 전부**에서 W/STOP/TIMEOUT/U 일치, 48 scope 선정 성적·실제 확인점 membership 일치. 추가 표현은 원 연구에서 hit가 없는 정의/branch 별칭이며 새 가설 탐색이 아니다.
- [native 원천 대조](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/native-parity.json): 27 partitions·5,587,427행·확인점247,284개·선정9,451개, 불일치0. 새 root typed proof272,519회·F 삼치449,730회·선정 typed proof9,069회 통과. 원천27개 hash와 코드 fingerprint, 최초 root·확인 key/시각/ask·원 branch·A/F 삼치 결과·선정 membership·typed proof를 대조한다. 원 연구의 검증된 후행 label은 재사용하며 모든 label을 새로 독립 계산한 것으로 표현하지 않는다.
- [v6 구조·reader](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/native-reader.json): 128 scope 구조, 변경15 scope, parent 불변, 합성 native ENTER_NOW→기존 typed 보조 입력 확인. 운영 등록·stage/PID 소비 증거가 아니다.
- Python9개 파일 compile·diff·소유 문서 링크/owner·print-only parser는 최종 [리뷰 receipt](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/readiness.json)가 소유한다. shell 변경이 없어 bash 검사는 해당 없음이다.

## 5. 성능과 수용 한계

HPSP 10/7 REGULAR 동일10,000행·첫200행 제외 CPU 기준이다. [기존 실행본](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/benchmark-old.json)의 기존 F05 정책 p50/p95/p99는 80.73/307.67/318.77µs, [새 코드의 동일 정책](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/benchmark-unchanged.json)은 80.72/310.31/326.95µs, [A19 추가 정책](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/benchmark-selected.json)은 89.46/322.68/383.54µs다. 동일 정책의 확인874개가 유지됐고 A19는875개다. 새 기능의 p95 CPU 증분은 기존 코드 대비 약15µs다. RSS는 약50→60MiB이며 새 고정 resource의 상주 비용을 포함한다. 단일 구간·동시 활동이 있는 격리 측정으로 전체 PID/WS queue/실주문 지연을 대신하지 않는다.

[최적화 전](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/assessment-benchmark.log)과 [최적화 후](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/assessment-benchmark-optimized.log)의 동일 새 family·22회 측정에서 평가+typed 투영 p95 CPU는 **83.30→55.14ms**, 약34% 감소했다. 기존 incumbent 검증은 별도 약40~42ms다. provider 시간·실제 전체5초 루프는 포함하지 않는다.

[장후 계산](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/postclose-benchmark.json)은 실제52,267행·확인6,094개·84,926개 표현(전체 current128 포함)의 한 partition에서 새 checkpoint30.22초, cache2.87초·raw replay0·결과 동일을 확인했다. 최대RSS 약378MiB, 운영JSON 약2.53MB·비교표gzip 약1.29MB다. 이전37.78/3.68초 측정은 code fingerprint가 다른 별도 로그로 남겼고 paired 속도 개선으로 확대하지 않는다. 새 per-tick 파일/API/provider 작업은 없다.

## 6. 준비 산출물과 다음 수용

[준비안](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/deploy-wait/prepared-registration.json)의 상태는 `prepared_waiting_deployment`, content SHA는 `82796bfeee2778ef25433e4cb41d89696ec006653910f5b1a9bf5ac204b4b1db`다. 48 scope와 작은 근거5개를 private archive에 봉인했다. private 준비의 publication10/15·target10/16·parent·code/source 봉인 및 `operator_receipt=null`을 확인한다. 기존 운영 pending/current/candidate를 변경하지 않는다. 실제 등록 시 이미 접수된38가설의 소비 여부와 현재 parent를 다시 확인한다. 같은 parent의 기존 등록과 충돌하면 자동 대체하지 않고, parent가 바뀌면 변경된 membership 기준의 재비교와 별도 successor가 필요하다.

이 작업의 완료는 구현·코드 리뷰·보완·격리 검증 및 검토 가능한 준비안이다. 운영 등록·정책 발행·배포/재기동·자연 신호·실현 수익은 이후 별도 수용이다. 기존 `CumulativePolicyAdoptionDeployment1015`와 `DirectFamilyPreopenPolicyHandoff`를 재사용하며 새로운 중복 OPEN을 만들지 않는다. 보유 계약은 다른 세션의 소유이며 실제 preset/trailing/manual·비용 결합 때 원천 receipt를 확인한다. 주성의 소실된 과거 전이·partial bundle을 소급 복구하거나 모델 손익을 실현 수익으로 기록하지 않는다.
