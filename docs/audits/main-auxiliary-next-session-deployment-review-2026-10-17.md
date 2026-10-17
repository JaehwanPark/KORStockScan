# 보조 입력·프롬프트 다음 영업일 배포 검증 — 2026-10-17

사용자가 배포·재기동과 다음 영업일 정상가동 점검을 승인했다. 적용 대상은 직접 비교 연구에서 확정한 두산에너빌리티 `034020|PRE|20000_TO_100000|NXT`, 알테오젠 `196170|PRE|GE_100000|NXT` 두 보조 경로다. 삼성·REGULAR·AFTER 및 다른 126개 연결은 승계한다. 기계정책 수치·Main/manual custody·수량·계좌·주문·provider·hard safety를 변경하지 않는다.

## 원 연구와 적용 근거

[원 직접 비교 연구](main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md)의 50쌍/100응답, 원 확인점·입력·라벨·실패·예산 2,047/2,047회를 보존했다. 두 PRE 경로는 각각 PASS 승리 3/3→8/8, 1/1→7/7이다. 해당 범위 20점이 모두 WIN이고 2개 원천 구간에 집중되어 있다. 실패 차단 개선이나 미관찰 holdout으로 확대 해석하지 않는다. 새 연구/provider 호출은 없다.

원 연구 부모는 10/16 `8809c82e…`, 적용 대상은 10/19 준비 정책이다. source/target의 128개 기존 보조 연결과 두 적용 경로의 기계 backend·payload·branch 목록·정의·기존 보조 payload 일치를 확인했다. 날짜·전체 code-refresh 세대가 다르므로 원 증빙을 다시 쓰지 않고 별도 next-session 승계 manifest로 결속한다. 다른 AFTER 기계 범위의 실제 차이를 숨기거나 전체 기계정책이 원 연구 부모와 동일하다고 주장하지 않는다.

## 코드 리뷰와 검증

- 최종 코드 `57d4d4664c6ce766bf0e949e6f91a4a1c0618dc7`, 관리 릴리스 `auxiliary-next-session-20261017-57d4d4664`. 선행 `bafb98de0` 검증·미발행 시도와 `2fa874239` 발행·실패 시도를 보존했다.
- 미래 발행은 승인·정지 상태·다음 영업일·PREOPEN 미시도·선택/정책/준비본 CAS와 native 잠금을 요구한다. 128개 최종 연결·2개 changes·rollback·00:00 적용·revocation를 대조하고 기존 current pointer를 유지한다.
- 원 108 고정 릴리스의 1,171개 Python source inventory, 실제 50쌍/100응답 cold 재검증 및 현재 의미 계약 12파일 동등성을 확인했다. 원 실패 증빙·미완료 시도·역사 bytes를 보존했다.
- 독립 리뷰에서 추가 범위 혼입, 적용시각·취소 metadata, 같은 코드의 릴리스 경로 변경, 빈 WAL, 검증 예외 전파, registry 부모 누락, 정상 장중 후속 overlay 차단을 수리했다. 최종 B 통합 139 PASS, A 최종 영향 177 PASS, 원 정책 code handoff 표적 2,066 PASS이며 일부 범위가 겹치므로 합산 수치로 표시하지 않는다. A/B 연결 검증과 compile/diff도 PASS다.
- 실제 원 delay/holding/stop inventory 25/22/17개를 원 7f 정책 digest와 대사했다. G/SDK의 정확한 원/후 source pair 두 쌍을 추가했고 dirty verifier·commit bytes·aggregate 검증은 유지했다.
- 격리 환경은 네트워크 차단·host root 읽기 전용·14개 private CoW mount를 사용한다. 원 ledger/정책 디렉터리 전체 복제는 0건이다. 역사 snapshot bytes 투영은 private namespace 안에서만 수행하고 원 alias 복구 후 세 family C.verify를 통과했다.

- 첫 배포 preflight에서 원 6개 OPEN이 7개로 늘어나는 것을 차단했다. 새 auxiliary 코드 capability의 정확한 세대 승계 누락이었다. 원 `d04…→2cfa…` 계약과 보고서·fixture를 보존하고 `d04…→dea0…` 한 쌍만 별도 등록했다. 현재 코드 84 PASS fixture의 코드·계획·증거 hash를 독립 대조했고 추가 회귀 348 PASS·재리뷰 finding 0을 확인했다. 실제 selector는 이 결함 수리 전 변경하지 않았다.

- 실제 `2fa874239` 발행 뒤 A 최종검증에서 역사 10/16 generation에 현재 10/19 compatibility를 재요구하는 결함을 발견했다. Main·보조 current는 불변이었다. 실제 target19 current→previous chain만 compatibility를 검증하고 모든 역사 source SHA는 계속 봉인하도록 수리했다. foreign day/bundle이 실제 ancestry에 들어가면 거부한다. 최종 영향 177 PASS·독립 finding 0이며 실제 발행 데이터의 읽기 전용 probe도 128범위/1,558개 의존성 PASS다. 원 실패 future generation/manifest/traceback과 기존 준비본의 예상 stale 상태는 삭제하거나 성공으로 바꾸지 않았다. 새 최종 target generation에 별도 발행해 정상 준비본으로 닫는다.

## 배포와 다음 영업일 준비

15:06:33 KST 최종 `57d4d4664` 릴리스를 정규 경로에 배포·선택했다. 원 selector·실패 시도·준비본을 보존하고 native 잠금 아래 발행했다. 배포 후 전체 계약 검증을 통과했다.

- 10/19 대상 bundle: `327ab8912d3d8b3d2fa50d967b23990c169e0683a4412629b39264dcd995421f`.
- 두 PRE 범위의 미래 보조 overlay: `ba9243476f614341f61425ff7f4135d13fe6c104b055ab4aeb739faa950da206`. 128개 연결 중 두 범위만 변경했다. Main current와 보조 current의 원 bytes/hash는 불변이다.
- 15:11:40 KST 미래 발행·전체 next_preopen 준비 검증 완료: `future_overlay_prepared_verified`, `current_full_contract=pass`, findings 0. 최종 reader 128범위·1,559개 의존성 검증도 통과했다. 앞선 실패 데이터의 read-only probe 1,558개와 최종 발행본을 구분한다.
- 정규 cron 필수 8개·release set·10/19 PREOPEN/Main dispatch 점검 PASS. 최종 경로는 모두 `57d4d4664`다. source 10/16 strict·controller와 finalization 세대 현재성 검사 PASS, `strict_checklist_generation_stale` 미발생이다. 실제 finalization DONE marker는 아직 없으며 다음 영업일 정규 실행을 성공으로 대신 기록하지 않았다.
- 네트워크 차단 read-only 전체 health 7개 검사: FAIL 0, 초기화 결손 0, report 계약 PASS, 운영 변경 0. `cron_completion`, process/resource/stale-lock/auth 검사는 PASS다. 아래 원천·역사 로그 경고를 남겼으므로 경고 없는 상태로 보고하지 않는다.

## 남은 경고와 후속 소유권

`initial_quantity_economic_source_gap`은 이전 7f health에서도 동일 source SHA의 완료13건 모두 비용/terminal/수량 근거 결손으로 확인됐다. `main_trailing_research_handoff_invalid`도 이전 a41 reader에서 같은 원 holding/research 자료로 재현된다. 이번 보조 배포로 새로 생긴 실패가 아니며, 현재 Main stop 정책과 기존 trailing 값은 불변이다. 기존 baseline 승계로 다음 기동 준비 검증은 통과했으나 원천 연구 계약을 성공으로 바꾸지 않는다.

- 수량: 10/19 기존 `InitialQuantityProducerConsumerRepair1010`에서 원 terminal·실제 비용·수량 source를 대사한다. 결손은 null/제외/source_gap을 유지하며 동일 세대 자연 수집·소비로 닫는다.
- trailing: 10/19 기존 `HoldingProfitExitSourceContractRepair`에서 native 연구 코드·source generation의 정확한 인계를 복구·검증한다. 이번 보조정책 승인으로 보유 연구 인계까지 승인 또는 수리된 것으로 취급하지 않는다.
- `actionable_current_owner_unresolved`는 현재 10/17과 미래 10/19 OPEN의 날짜 경계를 적용한 결과다. 미래 owner를 현재 완료 근거로 빌려 경고를 없애지 않았다. 원6개 OPEN을 유지했다.
- `log_scanner`의 UNKNOWN 2건은 10:48:14·10:48:40 KST offline 연구 작업본의 `config_dev.json` 부재 기록이다. PID/commit 귀속은 미확정이다. 현재 릴리스의 공유 data·`config_prod.json` 존재/JSON 유효성을 확인했으며 이 두 역사 로그는 10/19 기동 차단 원인이 아니다. 원 로그·cursor는 수정하지 않았다.

근거: `final-artifact-warnings-review.json`, `final-log-warnings-review.json`, `final-health-contract.json`. 기동 준비 PASS와 원천·경제성 연구 OPEN을 분리한다.

오늘 10/17은 토요일이며 다음 영업일은 10/19이다. 정규 경로는 05:35 finalization → 07:35 PREOPEN → 07:55 Main이다. 원 checklist 6개 OPEN은 실제 증빙이 생길 때까지 유지한다. 주말 PREOPEN 성공 또는 미래 PID 소비를 만들어 기동하지 않는다.

배포·다음 영업일 준비는 완료했다. 현재 Main/supervisor가 없어 재기동된 PID는 없다. 실제 10/19 PREOPEN 활성화·PID/start ticks·정확 overlay 소비·첫 health는 기존 `DirectFamilyPreopenPolicyHandoff`의 종결 검사다. 자연 AI 호출·주문·체결·비용 후 성과는 아직 관찰하지 않았으며 향후 오류 부재를 보장하지 않는다.

검증용 종료 scratch만 논리 용량 1,396,620,990바이트 정리했다. 근거는 `base-attempts/bafb98de0/fixture-scratch-cleanup.json`의 1,139,663,148바이트와 `cleanup-owned-build-scratch.json`의 256,957,842바이트다. 원 연구·실패·복구·source-validation·prepared snapshot·고정 검증 릴리스는 유지했다. 이 논리 용량을 실제 filesystem 회수량으로 대신 보고하지 않는다.

증거 디렉터리: `/home/ubuntu/KORStockScan/data/report/auxiliary_next_session_deployment/2026-10-17`.
