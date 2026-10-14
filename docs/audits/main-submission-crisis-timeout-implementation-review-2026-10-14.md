# Main 제출 응답·timeout·위기 감지 제거 구현 리뷰 — 2026-10-14

## 범위와 기준

사용자의 최신 배포 기준 계획 보완·기능 제거·6건 오류 해소·반복 리뷰/수정 후 배포·재기동 승인 및 추가18:36:07 artifact_freshness 경보를 처리한다. [보완계획](../proposals/main-postrestart-submission-bottleneck-review-and-remediation-plan-2026-10-14.md)을 실행 owner별로 구현한다. 기반은 f71c7d5f9/PID1025115/start3338102다. 동일 commit의 분리 worktree에서 작업하여 기존 workspace의 무관한 변경을 보존한다.

## 구현과 근거

- 위기 감지: scanner/60분 daemon·startup heartbeat·필수 heartbeat/DB 저장·조회·ORM·RSS/번역/알림/state writer 및 전용 의존성 선언 제거. 관련 운영/과거 문서9개 정리. 실제 DB와 과거 로그·sealed evidence는 보존했다. 누락 process 경보를 만들지 않도록 required heartbeat consumer도 함께 수정했다.
- 응답 계약: 정확한 incumbent v1 registry를 기존 compact wire v2로 파생하는 sealed repair manifest를 추가했다. 원 logical input·prompt·model·native signal/semantic guard 유지, 공통PASS·all assessed signals·bound risk 인용을 구조로 요구한다.128scope parent/source CAS, original raw/immutable registry·old confirmation·rollback·거부 반례를 검증했다. 연구 호출/경제성 선정을 수행한 것으로 기록하지 않는다.
- timeout:6건은3개 과거 PID의 원5초 잔여1936–3475ms 소진이다.2건 늦은 SDK 응답에도 최종 유효시간은79.7/74.7ms만 남았다.429/키 장애/요청 포화는 입증되지 않았다.5000→8000 timeout 단독 증액과 reserve100ms 임의 축소는 채택하지 않았다. 같은 요청의 검증된 registry 반환값을 재사용해 중복load1회를 없앴으며 generation/native age/revocation/model 검사는 유지한다. 실제 SDK Future 종료의 type/status를 비밀값·응답본문 없이 추가 기록해 다음 장애 원인을 구분한다. 늦은 응답은 admission하지 않는다.
- 구조비교:실제7registry×13fixture91쌍의 논리 parity, PASS decode91/CAUTION126 통과. canonical PASS364→106B, 전체 input/schema/prompt8237→7404B. 중복load84쌍 교대 실험 중앙값0.253→0.157ms. 이 값은 토큰 청구나 실운영 timeout 개선율이 아니다.
- 원천대사:과거45 terminal+cutoff pending2를 보존했다. native stale10은원 seq/epoch 일치·age4.220–73.572초이며 route missing16은도착0/0이다. 데이터가 없던 것을 downstream유실로 추정해 Kiwoom 재등록·fallback·stale완화를 도입하지 않았다.
- 현재 제출 경로:18:23:27–18:35:07 현재PID26요청/20응답/6timeout, rawPASS10/validPASS7/executablePASS1을 exact trace prefix로 동결했다. executablePASS1은동일attempt budgetpass/SAFE→2주 sizing→ORDER_TYPE_PREFLIGHT_BLOCKED이며 broker제출0이다. 이 로컬 NXT venue eligibility 계약과 추가18:36observer 경보의 수리 결과는 아래 최종검증에 기록한다.
- NXT 원천·전달: 실제 실패는 type6 금지가 아닌 `eligibility_unknown`이다. EOD-only 당일 원천 생산 공백, Main caller의 evidence 누락, explicit NXT에 SOR 승인 helper를 적용하던 오류를 수리했다. Main 시작·날짜 변경의 bounded 공식 ka10099 수집과 EOD가 canonical 저장 함수를 공유하고, 원5초의 마지막 만료 재검사 전에 local DB evidence를 전달한다. explicit NXT만 완전한 해당 축·종목/날짜/API/revision/time/payload hash를 검증하며 원 PARTIAL/KRX unknown과 SOR 독립 승인·주문 안전장치는 유지한다. 완전한 재수집에서 빠진 당일 기존 ka10099 row는 UNKNOWN/source_missing으로 갱신하고 새 원천 및 누락 처리 전 row를 immutable receipt에 보존한다. [독립 수리 리뷰](../../tmp/submit-crisis-timeout-20261014/runtime-market-eligibility-review.json)는 누락→거부→재등장 회복과 producer→Main adapter→NXT preflight를 검증한다. 수집 PASS가 모든 종목 적격성을 뜻하지 않는다.
- 18:36 경보: [회수 manifest](../../tmp/submit-crisis-timeout-20261014/alert-183607/manifest.json)대로 원18:36:07 경보의 exact artifact는 회수하지 못했다. 보존한 보고서는18:36:19.746942(`source_as_of`18:35:13.923993), detector는18:38:45다. 후속 보고서의 fixed-watch68은 읽은45분 모집단이며 현재 PID600초 분모와 구분한다. 같은 completion clock의 중복 keyword로 disposition이 누락되는 결함을 수리했고, 원천 전용 stage를 기존 cache의 forward index에 보존한다. 배포 준비는 검증된 cursor에서만 최대4×32MiB append하고 과거 미수집 구간을 채우지 않는다. 실제 결손·변조·한도 초과는 계속 partial/fail이다. [70행 오프라인 비교](../../tmp/submit-crisis-timeout-20261014/alert-183607/frozen-source-window-parity.json)의 필드/semantic 동등성은 당시 원천 전체 완전성이나 경보 정상화가 아니다.

## 검증·재리뷰

코드 변경은 producer→reader→Main 실행 guard·다음날 source handoff까지 검토한다. 초기120개 제거 관련 시험,104개 timeout/auxiliary 시험,98개 transition/tuning/wire/extended-policy 시험,771개 당시 exact handoff pin 시험과 독립75개 재검증은 각 evidence에 보존한다. 후속 wire/zero-base source130개, NXT producer/consumer 독립195개, startup/EOD/scheduler 관련148개, observer source 관련993개 시험도 통과했다. NXT 시험의 SQLite 날짜 adapter 경고와 기존 fork 경고는 보존한다. EOD import 시험은 production 설정을 변경하지 않고 임시 synthetic config harness를 사용했으며 실제 API·주문은 호출하지 않았다. 중복된 suite실행수를 고유 test총수로 더하지 않는다. 최종 통합검증 결과와 코드 hash는 `tmp/submit-crisis-timeout-20261014/final-gate.json`이 소유하며, 이전 pin 시험을 최종 bytes 검증으로 대체하지 않는다.

NXT session 계약 수정 전의 `fresh-confirmation-parity-comparison.json`은 f71 대 당시 후보128scope/76,800rows/621hits·signalhash동일·mismatch0의 역사 검증이다. 최종 후보에서는 native 계약 module33개 중 `session_contract.py`1개가 변경되므로 module bytes 전체 불변을 주장하지 않는다. 정의·정책값을 유지한 정확한 최종 session source pair로 다시 실행한128scope/76,800rows/621hits는 signal hash까지 동일하고 mismatch0이다. `final-confirmation-parity-comparison.json`·`final-confirmation-parity-provenance.json`과 최종 gate가 그 결과를 소유한다. auxiliary reader 변경은 원 report와e792overlay 각각의 원 frozen reader 및 새 codehash에 결속한 별도 compatibility receipt로 인계한다. 이전 parity·PREOPEN PASS를 최종 bytes 검증이나 새 PID소비로 재사용하지 않는다.

최초 통합시험은13실패/3668통과였으며 실패13개 모두 f71 기준의 분리 worktree에서도 같은 `machine_submit_lineage_rejected`로 재현됐다. 원 로그를 보존하고 해당 guard 시험에만 실제 observation revision binder를 통과하는 명시적 synthetic machine identity를 추가했다. 운영 검사를 우회하지 않고 원13개 모두 목적 guard까지 도달하여 통과했으며, 최종 bytes를 고정한30개 suite 통합시험은 **3682 PASS / 실패0 / 기존 fork 경고7**이며147.722초 동안 source bytes가 불변임을 확인했다. Python compile과 diff 검사도 통과했다.

Python compile·diff·로컬링크/현재owner/AUTO·print-onlyparser를 확인한다. 원 PREOPEN→최종 AI·Main caller·async/observer의 인계 계약 대상 경로별 exact SHA쌍을 등록하고 dirty/원본/후보변조 반례를 거부한다. 전체 release 검토와 이 source-pair 검증은 별개이며, 검토된 최종범위의 미해결 결함과 테스트결과는 최종gate에서 판정한다. 무결함을 일반보증하지 않는다.

## 배포·실제 소비·잔여 수용

배포의 권위있는 결과는 `data/report/main_submission_crisis_timeout_deployment/2026-10-14/deployment-result.json`과 같은 디렉터리의 build/compatibility/native parity/manifest/publication/PID 검증이다. 문서의 code gate는 배포가 실행됐다는 receipt가 아니다. immutable reviewed release에서 exact baselineCAS·gracefuldrain→문서/selector→auxiliaryCAS→nativeprepare/readiness→Mainstart/attest한다. 원 정책10개는불변, auxiliarycurrent는검토한128scope후속세대로만 바뀐다. 기존 hold나실패receipt를 강제해제하지 않는다.

새 PID/cwd/start·nativebundle·auxiliarymanifest/registry소비·위기daemon부재·첫health·정규observer를 확인한다. 자연PASS→budget→intent/send/broker/fill/terminal·비용후성과는 기존checklist owner가수용하며 인위적인시험주문/AI호출을만들지 않는다. 원6건오류·18:36경보·sourcegap·아직없는성과는보존한다. 외부Project/Calendar sync와 광범위보고재생성은실행하지 않는다.
