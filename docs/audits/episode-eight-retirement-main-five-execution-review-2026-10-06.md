# 에피소드 8종목 퇴역·Main 5종목 전환 실행 검토

## 범위와 권한

사용자가 [계획](../proposals/jeju-episode-retirement-hpsp-alteogen-main-fixed-watch-initial-policy-plan-2026-10-06.md) 구현, 반복 코드리뷰·수정, 배포·재기동을 승인했다. 신규 HPSP·알테오젠·주성엔지니어링은 기존 비삼성 Main 부모를 초기 정책으로 사용하며 경제성 사전 입증을 요구하지 않는다. 다른 작업본과 과거 원천/소유권 증거는 보존한다.

## 구현과 리뷰

- 8종목의 27개 전용 profile와 54개 timer를 실행 catalog/override/날짜 lookup/installer/wrapper에서 제거했다. 3개 quarantine과 영원무역·카카오 자동 paired 연구 scope도 제거했다. 공용 replay와 remaining 명시적 연구 권한은 유지한다.
- 동일 종목을 새 시간대/이름으로 등록하거나 자동 확장하는 우회 경로를 symbol/owner guard로 막았다. 신규 Main-only 3종목도 episode 자동 등록에서 제외한다.
- 남는 모든 날짜별 profile 값을 작업 전 asdict 원본과 대조하여 변경 0개를 확인했다. 현행 registry는 10종목·31개 profile이며 10/6 원 applied 파일은 직접 수정하지 않는다.
- Main spec는 5종목, 종목별 최대 1 target/독립 ID, 기존 cap 내 예약을 유지한다. 모든 fixed-watch helper에 날짜·route·generation 검증을 적용하여 legacy AI silent fallback을 차단했다. 초기 non-Samsung 지정은 수익성 검증 gate가 아니다.
- WS publication과 연구 writer의 lock/원 capture clock을 분리하고 capture 실패·busy·not_observed를 별도 표시했다.
- NXT는 신규 3종목의 exact-date 기존 listing 원천이 입증될 때만 등록한다. 현재 해당 원천 결손을 source WAIT로 공개하고 KRX 정규장 기술 경로를 유지한다.
- 리뷰에서 동적 후보의 퇴역 symbol 재유입, 신규 3종목 장후 보고서 consumer 누락, 후보 변경 시 admission recipe 부모 hash 불일치를 찾아 수정했다.
- 그룹 manifest/개별 잔여 주문·intent/활성 service/중간 실패/rollback 및 원 퇴역 영수증의 후속 code-only guard binding을 반대 사례로 검증했다.

## 원천 및 운영 증빙

실행 증빙: `/home/ubuntu/KORStockScan/tmp/jeju-eight-episode-main-five-execution-20261006/`.

초기 broker 2회 snapshot은 같으며 퇴역 8종목 잔고·미체결·전체 날짜 intent는 각각 0이다. 실제 제거 직전에 native producer가 다시 조회한다. 원 정책/PREOPEN/bootstrap와 이전 장후 원본을 freeze하고 후속 release/PID와 별도로 대조한다.

Kiwoom 공식 upstream SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인했다. 기존 읽기 collector를 사용하며 protocol/FID/control packet은 변경하지 않았다. inspected paths·시각·각 파일 SHA는 `official-reference.json`에 기록했다. `kiwoom_docs` 부재와 SDK/spec/realtime/Postman 대조를 기록했다.

## 완료 및 관측 경계

코드 검증, bounded 연구, 설치 퇴역, 배포/PID 검증 결과는 실행 완료 후 아래에 기록한다. 자연 source/기계 trace/제출/체결/비용 수익은 서로 대체하지 않는다. 자연 관측이 없는 적격 session은 `not_observed`이며 기존 실제 원천 결손을 성공으로 채우지 않는다. 현재 checklist의 `JejuEpisodeRetirementHpspAlteogenMainFixedWatch`가 후속 자연 수용을 소유한다.

## 최종 코드 검증 및 제한 연구

- 통합 pytest: **1,304 PASS**, 기존 pandas deprecation warning 1개. compile/import·shell syntax·diff whitespace 검사 PASS. checklist print-only parser에서 실행 owner 1개를 확인했다.
- 신규 3종목별 baseline 포함 10개씩, 합계 30개를 frozen parent/source/kernel 계약으로 평가했다. 모두 `source_gap`: 적격 native fixed-watch 기회 0개다. 기존 다른 origin/진입 identity 결손을 상시감시 원천으로 재표기하지 않았다. HPSP 기존 행 59개, 알테오젠 11개, 주성 54개(정확한 수량은 아래 JSON 증빙 우선); 제외 원인은 원 기회 lineage·지원 scope·원 비용/검열 계약이다. 성과 증거는 없으며 초기 정책 지정과 분리한다.
- 기존 두산 보고서도 같은 단계 계약으로 생성했고 10개 후보·native 기회 0개·`source_gap`을 기록했다.
- 다음 10/7 native baseline builder는 격리 출력에서 31개 policy 생성 및 검증 PASS, 10/6 remaining policy 값 변경 0개다. 실 적용 bundle/PREOPEN은 오늘 장후·내일 정규 producer의 exact-date 산출물을 기다리며 이 임시 파일로 정상 소비를 대신하지 않는다.
- 원 정책/PREOPEN/bootstrap 및 기존 장후 원본 34개 SHA는 그대로다. 원 보고서의 결손과 invalid capture는 원 증거로 유지한다.

## 배포 진입 단계 추가 리뷰

첫 배포 커밋 `04920b5b`에서 Python `-I`로 실행하는 native router가 새 퇴역 validator의 package import를 찾지 못했다. 프로세스 종료 전에 차단되어 기존 Main PID는 유지됐다. router가 인접한 검토 guard의 profile 선언을 AST로 읽고 순수 JSON 계약을 검증하도록 보완했다. 환경의 `PYTHONPATH`를 기동 권한으로 사용하지 않는다. 격리 interpreter subprocess 회귀를 포함한 router 90개 테스트와 실제 `-I --print-plan` PASS를 확인했다.

설치 상태 점검 분기도 동일한 격리 계약으로 정리하고 subprocess 회귀에서 함께 실행했다. 최종 router 90개 PASS 및 실제 wrapper의 `--check-release-set`/`--check-cron` PASS: remaining service 62개, policy pin 186개, cron target 8개다. 퇴역 mask의 loaded 관측 수와 설치된 전체 mask 수는 구분한다.

## 최종 배포·운영 확인

- 최종 코드 커밋: `511664f30558eb878039405d6baa1eea09498d65`; release: `/home/ubuntu/KORStockScan-runtime-releases/episode-eight-retired-main-five-20261006-511664f3`. Main singleton PID `169115`, cwd는 이 release의 `src`다. 앞선 PID `126945`, `167369`는 정상 종료했다. 실제 PID의 5종목 enable env는 모두 `true`다.
- 18:21:05 KST native bootstrap/PID env verification PASS. 원 manifest SHA `4399f577fb7245f69df9a381312b689d042b8fecafed7d9222b66b13313d11da` 및 freeze한 원 정책/PREOPEN/장후 자료 34개 SHA가 그대로다. 기동 초기 첫 heartbeat 검사는 15.3초 지연을 기록했으며, 초기화 완료 후 재점검은 `All processes and threads healthy` PASS였다. 첫 16.3초 loop pressure 후 제한이 native 방식으로 회복되고 이후 loop metric은 141.4~232.6ms였다. 전체 세션 부하 보증으로 해석하지 않는다.
- native group retirement는 18:14:53 KST terminal, receipt SHA `eddbb29455de4e5c03f2ea56487221e3f749db26b4ef352772650deff318882f`. 각 종목 broker/custody/전체 날짜 intent flat을 확인해 전용 timer 54파일을 제거하고 instance 54개를 mask했다. 기존 두산 6개를 포함한 설치 mask는 총 60개다. 퇴역 3개 preflight의 과거 failed 상태는 before receipt를 보존한 뒤 `reset-failed`로 정리했으며 masked/inactive/PID 0이다. 서비스나 주문을 복구하지 않았다.
- 원 auto-apply의 sealed 결과와 marker 파일 SHA `105360a878d5fc4657f66f0ffb1eecb23b0e0085ef1b20bec3d38dd43bed9c4f`를 대조해 provenance가 일치하는 퇴역 8개 `machine_owner_scope` 호환 표시만 제거했다. 모든 다른 줄·수동 veto는 보존했다. `compatibility-marker-cleanup.json`과 원 파일 backup으로 대조할 수 있다. 과거 auto-apply 원 결과는 재작성하지 않았다.
- expander·owner PREOPEN·live/preflight template의 다음 시작 code를 최종 release에 pin했다. 정책 env/hash는 그대로다. 남은 31개 profile의 live/preflight 62개 service에서 policy pin 186개 PASS, cron 경로 8개 PASS다. 다른 에피소드 프로세스를 이번 전환으로 기동하지 않았다.
- 배포 후 native account 재조회는 KRX/NXT 모두 정상: 잔고 0, 미체결 0, 활성 DB 보유 0, 미해결 intent 0. custody registry 1,409개 event와 기존 증거를 보존했다.

### 정책 범위와 자연 관측

| Main 종목 | 초기 기계 정책 scope | 현재 관측 |
|---|---|---|
| 삼성전자 `005930` | 기존 Samsung | 실제 당일 fixed-watch admission 및 WS `_AL` 등록 관측 |
| 두산에너빌리티 `034020` | 기존 non-Samsung | 실제 당일 fixed-watch admission 및 WS `_AL` 등록 관측 |
| HPSP `403870` | 기존 non-Samsung | enable 확인, NXT exact-date 적격 증빙 결손으로 admission WAIT |
| 알테오젠 `196170` | 기존 non-Samsung | enable 확인, NXT exact-date 적격 증빙 결손으로 admission WAIT |
| 주성엔지니어링 `036930` | 기존 non-Samsung | enable 확인, NXT exact-date 적격 증빙 결손으로 admission WAIT |

비삼성 초기 parent SHA는 `6b6fb2040270dab41a05e2a84bda0baed9c06714aa0b587997b2982a87df2b4a`, 원 Main bundle SHA는 `bd76748c22aaf913af104996be3073664ef355f24c3e6291c47f28e107aedabe`다. 신규 3종목의 초기 지정에 경제성 적격성 검증을 다시 붙이지 않았다. NXT 적격 증빙은 원천/venue 계약이므로 면제 대상이 아니다. 5종목 helper→기계 resolver/compact 역할은 회귀로 검증했고, 미관측 자연 trace를 성공 receipt로 만들지 않았다.

실제 PID의 연속 WS 발행을 20회/11개 frame으로 제한 관측했다. 발행 age p50/p95/max는 0.597/1.028/1.189초, capture lock은 64.314/68.242/68.242ms다. writer loss와 projection error는 0이다. 연구 capture 상태는 별도 기록하며 frame 발행으로 fact 저장을 대신 입증하지 않는다. 이 관측은 현재 admission된 2종목과 shared consumer 범위이며 신규 3종목을 포함한 전체 장중 부하 증거는 아니다. 지연/예외 writer가 다음 frame을 막지 않는 경우는 별도 pytest로 검증했다.

### 남은 경계와 다음 소유자

G0~G5의 기술 전환·제한 연구 수행과 실제 release/PID 소비는 완료했다. G6의 신규 3종목 자연 source/기계 trace, 다음 10/7 exact-date owner PREOPEN·정책 producer·남은 episode 실제 기동은 `not_observed`다. 새 standing authority는 10/7부터 15종목 현재 owner scope를 사용하며 원 계좌/유효기간/자동 적용 시간대를 유지한다. 신규 3종목 NXT 증빙은 기존 listing/eligibility producer가 소유하고, KRX 정규장 경로는 해당 NXT 대기를 적용하지 않는다.

현재 checklist의 같은 stable ID를 다음 PREOPEN/기동 자연 검증으로 인계한다. 기존 `strict_checklist_generation_stale` finalization 알림과 원 운영 경제성·보조판정·episode 원천 결손은 전체 장후 PASS로 재표기하지 않는다. 오늘 장후·다음 PREOPEN의 native exact-date generation 결과는 해당 기존 소유자가 검증한다. 원 소비 자료를 현재 값으로 채우거나 과거 보고서를 새 코드로 덮어쓰지 않았다. 검토 범위에서 미해결 코드 결함은 없고, 아직 발생하지 않은 자연 증빙과 기존 원천 결손은 별도 잔여 사항이다.
