# Microstructure 전용 장후작업 폐기·현행 평가 통합 실행 review

작성: 2026-09-18 KST. Owner: `MicrostructureMachineAuxiliaryNaturalAcceptance0918`. 사용자 승인: [상세계획 MC0–MC6](../proposals/microstructure-reaction-context-postclose-consolidation-plan-2026-09-18.md) 구현·코드리뷰/수정보완 반복·검증 완료 후 commit/push·배포·장후 결과 제한 갱신. 증거 디렉터리는 `tmp/microstructure-consolidation-20260918/`다.

## 결정과 변경

전용 raw JSONL 재스캔·구 entry stage funnel·20분 favorable 전용 연구·독립 누적 rollup/backfill producer/CLI를 제거했다. wrapper의 enable env·전용 wait/실행/artifact wait를 제거하고 terminal marker에서 retired raw와 calibration 통합 진단을 구분한다. legacy raw5.71GB를 다시 읽지 않았다.

기존 기계/보조 AI calibration 안에서 전체 capture census·export200개 전 전체 case 통계·정확한 snapshot/route/venue/session·full-cost/cadence·같은 날짜 부모 SHA를 보존한다. 비용 source-only preflight는 기존 producer를 사용하고 AI replay와 독립한다. modern JSON/MD는 legacy 없이 생성되며 구 보고서가 있으면 원 byte/hash 사본을 보존하고 구 통계·retired source order를 현행 진단으로 전달하지 않는다.

마지막 calibration 이후 일일 소비는 작은 `--refresh-machine-evaluation-only` 경로로 갱신한다. 다른 summary/후보·보정/정책은 유지한다. EV refresh의 관련 source 의존성과 strict handoff의 modern identity/hash·세 요약 내용 일치 검사를 추가했다. 비용 결손은 정상 인계된 source gap이며 no-edge/실제 수익0이 아니다.

## 리뷰·수리·배포 경계

- 단순 disable만으로 env 재활성화가 가능한 문제: enable 선언과 호출 block/CLI를 제거했다.
- 전용 report 부재를 경고로 취급하고 구 통계를 현재 값으로 전달하는 문제: modern-only mode, retired/N/A, legacy byte 사본으로 전환했다.
- 늦은 부모 생성 후 daily의 이전 진단이 남는 문제: 기존 daily 전체 재계산 대신 한 section만 atomic refresh하며, strict verifier가 소비 부모/내용 불일치를 검출한다.
- 부모 hash 부재·변경 또는 같은 hash를 붙인 통계 조작이 조용히 통과하는 문제: 부모 날짜/파일명·실제 modern payload 내용까지 대조하고 strict 검사에서 차단했다. 추가 의미 결속 검증10 PASS, 최종 modern6 PASS.
- 보고서 읽기 atime을 source 변화로 오인할 가능성: dev/ino/size/mtime으로 비교한다.
- selected와 작업본의 다른 health/scale-in 변경 혼입 위험: selected `581b17cb12a72b0782846f2221317f25b4f2ecf5` 기반 clean worktree에서 자체 diff만 반영했다. selected의 live quote-health/adverse-flow guard 함수는 원문 보존했다. 이전 원천 route 보완은 명시적으로 포함한다.

새 production 파일/별도 tuner/grid/collector/job/shadow를 만들지 않았다. live feature/context hash/provenance projection·holding/entry guard와 별도 machine microstructure attribution/widget/저가주 정책 경로를 보존했다. Kiwoom request/FID/REG/auth/order protocol 변경은 없다.

## 대상 검증

- core producer/live/source adapter: 최초 selected-base 검증254 PASS, 비용 preflight 이전 구현을 옮기지 않은 wrapper1항목 발견 후 수리. 해당 항목과 modern 인계 재검증7 PASS.
- modern producer/consumer/live 관련 선별59 PASS. legacy 경제성/coverage 숫자를 유지하던 consumer 테스트를 retired/N/A 계약으로 수정했다.
- strict verifier/summary handoff206 PASS.
- 기존 holding receipt/state logger projection1 PASS.
- compile, `bash -n`, scoped `git diff --check`, 문서 링크와 print-only parser 결과는 `validation.json`을 따른다.

같은 성공 검증을 무조건 반복하거나 trading 전체 suite/성능 benchmark를 추가하지 않았다. 실제 broker/provider/알림·주문·full postclose/grid·과거 rollup 복원은 실행하지 않는다. scope gate 통과는 자연 정책 소비/실현 성과 acceptance가 아니다.

## 배포와 결과 갱신 receipt

검증 후 관련 source를 fast-forward 커밋·푸시하고 clean managed release로 선택한다. 실행 중 worker는 기존 root로 계속 수행한다. 전용 작업은 다음 정상 routed postclose에서 제거되며 별도 machine attribution 서비스는 중단하지 않는다. 구 선택과 release root는 rollback 증거로 보존한다. 실제 선택 commit/root/router·push·원천 보호·PID 상태는 `deployment.json`에 기록한다. 현재 worker 또는 trading bot 재시작, cron 복원, dated policy/env/lock 재발행은 수행하지 않는다.

결과 갱신은 이전 검증의 retained 9/16·9/17 전체 capture/case 진단과 source generation manifest를 재사용한다. 날짜별 diagnostic calibration parent와 최소 EV/runtime/workorder/scope handoff는 dated successor namespace에 작성하며 **전체 canonical calibration/정책 grid/EV/chain을 재실행한 결과가 아니다**. 9/17 기존 canonical daily의 microstructure section만 갱신하고 나머지 후보·실제 summary/원천은 유지한다. 다른 날짜의 canonical 정책·원본 ledger/보고서를 진단 projection으로 덮어쓰지 않는다. 원본 보호 hash·successor 경로·scope verifier와 canonical daily 소비는 `result-refresh.json`에 기록한다.

9/16의 기존 비용 차감3분 관측 CF1,213건은 기술적 진단이며 새 실제 이익/인과 feature ΔEV가 아니다. 9/17 verified3,342건은 당시 full-cost source가 없어 case/경제 결과0, EV·순익null이다. 과거 당일 비용 원천은 현재 master로 소급하지 않는다. legacy−0.803769% 부분 CF를 현행 정책 유지/폐기나 승격 기준으로 사용하지 않는다.

## 남은 acceptance

1. 다음 정상 실행에서 비용 source→calibration→modern section→최종 EV/daily/runtime/workorder의 같은 날짜·부모 SHA와 전용 raw 호출0을 확인한다.
2. source gap이면 actual producer owner·영향 분모·수리/irrecoverable 이유를 보고한다. 단순 기다림이나 같은 입력 replay로 historical source gap이 해소된다고 주장하지 않는다.
3. 실제 정책 후보/선정·PREOPEN/PID·자연 행동은 기존 기계/보조 AI owner 계약에서 추적한다. 통합 진단 자체는 새 정책/런타임 권한을 생성하지 않는다.
4. 실제 unique 완료 episode·정산 비용·applied version이 연결될 때만 rolling/cumulative 실제 EV·순익·tail·노출·동일 정의 예측 오차를 평가한다. 이 review/배포/부분 successor의 PASS를 전체 postclose DONE이나 경제성 PASS로 쓰지 않는다.
