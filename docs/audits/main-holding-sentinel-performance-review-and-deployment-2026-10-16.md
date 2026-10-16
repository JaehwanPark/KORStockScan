# Holding sentinel 반복 읽기·계산 개선 및 배포 검증 — 2026-10-16

## 범위와 승인

사용자는 holding 지연 분석 후 코드리뷰·수정보완·배포·재기동을 승인했다. [원인 분석과 기동 후 검증](main-postclose-source-gap-final-release-review-2026-10-16.md)의 후속 구현이며 기존 `HoldingProfitExitSourceContractRepair`와 `DirectFamilyPreopenPolicyHandoff`를 사용한다. 정책·provider·주문·수량·threshold·freshness·Main/manual/retired custody와 원 결손을 보존한다.

기준 selected release는 `63b758ac8e98ace56e62419b677f374449fd724f`, Main PID `3474098`, start ticks `18613546`이다. 기존 격리 작업트리 `postclose-source-gap-final-release-20261016`의 `178b3bbae607d65a6a681c787185643cc29b92c4`에서 진행했다. 다른 workspace 수정은 통합/정리하지 않는다. source 위치는 기존 report producer `src/engine/holding_exit_sentinel.py`, 회귀는 기존 `src/tests/test_holding_exit_sentinel.py`다. 새 engine-root 모듈을 만들지 않는다.

`e9cfb9bcaf4f84491d4593587bc48c2bdde4ae85`는 Git 조상 자체가 아니라 63b의 통합된 코드 내용으로 포함된다. 원 변경 23개 파일 중 19개는 blob이 동일하고 4개는 최신 SOR/체결 시각/필수 TP source 보완을 포함한다. e9를 다시 merge할 때 생기는 차이는 coverage 초기화의 이전 위치 재추가뿐이다. 현재 코드는 동일 BUY identity의 `begin_coverage`를 cap 조기 return 전으로 옮겼으므로 중복 실행을 복원하지 않는다. 이번 변경은 그 23개 파일을 다시 수정하지 않는다. 증거: 정규 workspace `tmp/holding-sentinel-performance-20261016/e9-inclusion-check.json`.

## 구현과 리뷰 보완

1. scope 귀속은 record별 explicit timestamp를 한 번 정렬하고 이분 검색한다. 좌우 최단 거리·동일 timestamp의 복수 scope·동률 conflict·invalid record·원 event 순서를 유지한다. 같은 event의 scope parsing도 한 번만 수행한다.
2. 전일 비교만 native cache 세대에 결속한 작은 투영을 재사용한다. 원 source cache의 증분 유지·행 census 뒤 native writer의 shared lock을 잡고 전후 inode/ctime/mtime/size 및 전체 행 수를 확인한다. reader/store 코드 해시·필드·열 계약이 달라지면 재계산한다. 현재 일자 인과 감사는 모든 원 fields를 계속 읽는다.
3. 전일 투영은 요약에 필요한 43개 고유 필드와 원 identity/header를 보존하며 compact column 배열로 저장한다. 실제 전일 투영은 26,344,275 bytes로 기존 32MiB 캐시 상한 안이다. 원 478,787,144-byte source cache와 raw/receipt는 변경하지 않는다. 상한을 넘으면 공용 helper의 계산 fallback을 유지한다.
4. stage별 unique attempt는 stage마다 전체 행을 다시 읽는 대신 한 pass에서 모은다. 동일 입력 generation의 사전 중복 hash는 제거하고 native auditor가 최종 date/cutoff 필터 후 한 번 계산한다. 독립 원 report/generation 검증을 제거하지 않는다.
5. 초기 실제 자료에서 큰 dict 투영이 캐시 상한을 넘는 문제가 나와 column 형식으로 줄였다. 직렬화 후 list가 되는 tuple을 contract에 남기면 warm reuse가 실패하는 문제를 회귀에서 재현했고 list 계약으로 수정했다. warm run에서 전일 source cache를 열면 실패하는 테스트, source append/hash/code 계약 변경, source mutation/population, nearest 동률/정렬/invalid ID 및 거리 계산량 상한을 확인했다. summary consumer의 필드 추가가 projection 누락으로 이어지지 않도록 필드 계약도 검사한다.

## 동일 원천 parity와 성능

처음에는 이미 append된 입력을 과거 보고서와 비교했고 격리 worktree의 policy selector가 없어 binding gap이 났다. 이 실패를 PASS로 쓰지 않는다. 실제 selected release의 변경되지 않은 정책 consumer를 사용하고, 원 native generation SHA가 정확히 일치하는 원천 prefix 36,103개를 고정했다. 당시 cache snapshot 이후 append된 16개는 이 private 역사적 parity에서만 제외했다. 원천·정책 검증을 bypass하지 않았으며 정규 보고서의 현재 입력은 제외하지 않는다.

- 원 기준 시각: `2026-10-16T13:00:05.562981+09:00`.
- 원 generation: `c55c7bd09de83eabde317e399bcc92c84089200b5a39660bcf50307ba57bcd52`.
- **전체 report dict 동일**, 달라진 top-level field 0. 과거 source gap 5건·policy/runtime 소비·scope/분모·baseline/분류를 포함한다.
- 전체 candidate warm run 2회: **5.580 / 5.585초**. 원 운영 wrapper 12:48 시도는 339초였고 13:00 시도는 365초였다. 각 측정의 실행 환경/원천 snapshot 차이는 보존하며 운영 개선율은 새 배포의 실제 wrapper로 확인한다.
- warm 전일 native cache read **0회**를 실제 open guard로 확인했다. 전체 프로세스 read characters 약 462.3MB로 원 951.3MB보다 작다. 현재 일자 원 fields와 정책 ancestry 검증은 유지했다. 기존 479MB 전일 cache는 26.3MB 투영으로 재사용한다.
- 측정 프로세스 peak RSS는 **468,492 KiB**, 원 프로세스 관측 RSS는 851,944 KiB였다. peak/current RSS의 차이를 보존한다.

원본 실패 시도와 최종 증거는 정규 workspace `tmp/holding-sentinel-performance-20261016/`에 둔다: `holding-tests-{first,second,third}.log`, `exact-input-parity.json`, `verified-exact-input-parity.json`, `verified-native-parity-benchmark.json`, `final-integration-tests.log`. 후자의 검증된 native parity만 수용 근거다.

## 검증과 운영 수용

구현→self review→보완→재리뷰 뒤 **2,679개 회귀 PASS**(21.61초), 변경 Python 2개 compile, 문서 print-only parser·link·diff 검사를 통과했다. 리뷰 범위 미해결 finding은 0이며 원 WARN/unknown을 성공이나 0원으로 바꾸지 않는다. entry_cancel_wait/rising_missed/auxiliary/holding_vote 네 capability 구성 해시가 실제 selected release와 모두 동일함을 확인했다. 원 exact-code fixture를 재사용하며 같은 fixture를 다시 생성하지 않았다. 증거: `capabilities-unchanged.json`.

승인된 후속은 clean immutable release 생성→현재 정책/PREOPEN·PID·broker/WS 확인→정규 ordered drain/select/start→새 PID 소비→기동 이후 새 holding/BUY 보고서→정확한 보고서 SHA를 소비한 full detector다. 기동 전 보고서·이전 PASS·selector만으로 종료하지 않는다. 배포 terminal/실제 지연/남은 source acceptance는 후속 영수증을 아래에 추가한다.
