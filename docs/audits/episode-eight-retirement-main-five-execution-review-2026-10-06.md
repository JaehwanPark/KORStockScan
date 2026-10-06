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
