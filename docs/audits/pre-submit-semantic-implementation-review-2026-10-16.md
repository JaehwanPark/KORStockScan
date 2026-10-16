# 매수 지연·의미감시 구현 리뷰 — 2026-10-16

## 범위와 권한

사용자 승인에 따라 현재 selected6c97e83f1에서 격리 구현한다. 현재 정책/PREOPEN/수동·퇴역 custody와 안전 guard를 보존하고 정확한 코드 인계 후 ordered 배포한다. 원 실패 배포·기존 source gap·원장 bytes를 보존한다.

## 확인된 원인과 수정

- native producer의 continuous_reversal matched branch와 delay reader의 필드/구 catalog가 달랐다. UNION의 primary null을 허용하고 extended catalog의 정확한 definition refs를 고정해 세 경로에 같은 helper를 적용한다. v4 hash에 matched/refs/상황/선택 시간을 포함하고 구 v2/v3 digest를 유지한다.
- sharded reader가0초 cell을 삭제해30초 상위 정책으로 떨어졌다. 지원되는0초 cell도 메모리 lookup에 유지한다.
- canonical data와 release/data symlink의 문자열 비교로 실제 같은 요약을 unobservable로 만들었다. resolved source와 동일 세대 stat을 검증한다. 원 producer가 최근20분 집계를 게시해 반복 전체 JSON decode를 줄인다.
- signal_ready의 모든 후행 호가가 있어도 주문 terminal을 요구했다. 관측 완료와 실제 price_ready 주문 terminal을 분리한다. 실제 stale/clock-invalid 호가 제외는 유지한다.
- machine/auxiliary/joint comparison, 봉인 적용일/다음 예정일을 분리한다. optional 약세 연구는 기존 감시·incident·owner에 연결하며 native calendar·scope·cursor currentness를 확인한다.
- 과거 재분류는 exact machine SHA/evaluation/symbol/parent/causal capture가 일치할 때만 수행한다. SQLite와 날짜별 단일 스트림을 사용하고 plain/gzip logical seal을 보존한다. 원 commit/quote 해시는 변경하지 않는다.

## 검증과 실행 증거

증거 디렉터리: `/home/ubuntu/KORStockScan/tmp/pre-submit-semantic-20261016/`. 초기 core904개, monitor318개 회귀가 통과했다. 추가 native join/압축 무결성·signal terminal·alias 회귀에서 발견한 catalog legacy definition hash 누락과 fixture route 표기를 보완했다. 확장 회귀와 exact 후보 인계는 진행 중이다.

코드 closure, 불변 후보 선택, 새 PID 소비, 자연 v4 생성, 장후 정책 생성, 비용 후 성과는 별도 판정한다. 현재 자연/배포 완료를 주장하지 않는다.

## 남은 수용

최종 반복 리뷰/확장 시험→exact active-policy/code handoff→ordered drain/select/start/consumed→bounded observer→영향 범위 장후 projection 및 재계산의 native terminal을 확인한다. 현행 당일0초 정책을 재기동에서 그대로 소비하며 후속19일 정책 준비는 별도 generation으로 보존한다.


## 배포 전 코드 closure

최종 core1,271개, 계약2,554개, source/인계2,316개 및 별도 호환성2,434개 묶음 PASS(중복 포함; 합산한 고유 시험 수로 표시하지 않음). 압축 전환·CRC/내용/late/충돌 alias6개 PASS. Python compile, exact reviewed source7개와 추가 dependency2개 SHA, diff 및 print-only parser를 검증했다. 리뷰 범위의 미해결 코드 finding0이며 배포·자연 수용은 아래 실제 영수증으로 별도 갱신한다.

동결된 당일 요약9,251행+fixture1개에서 producer 최근 구간118행의 count/identity parity를 확인했다. 같은 프로세스 warm 기준 full8,790,806B→manifest35,041B, native 읽기 중앙값89.081ms→bounded 읽기/해시0.253ms, 상황 조회 p95 12.324µs, 최초 writer 이관0.116초다. 실제 Main 주문 latency 개선이나 cold I/O로 해석하지 않는다. `performance.json`과 `targeted-validation.json`에 원 snapshot SHA/시험 로그를 결속했다.

후속 리뷰에서 압축 pipeline의 물리 파일명 변경을 원천 유실로 보던 delay ledger 경계를 수리했다. 원 ledger를 다시 쓰지 않고 original logical SHA/byte 수와 전체 gzip CRC를 검증한다. 검증 cache는 최대64개 metadata/digest이며 append·inode/ctime/alias 변경을 다시 검증한다. 재계산은 완결된15일 원천을 먼저 격리 생성하여19일 target으로 검증하고, 현재16일 정책/PREOPEN pointer를 보존한다.16일 당일 누적 정책과 전체 strict/controller는 정규 장후 수용이 소유한다.
