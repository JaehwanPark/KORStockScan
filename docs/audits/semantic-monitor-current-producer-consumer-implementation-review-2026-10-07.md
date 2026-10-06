# 의미적 감시기 현행화 구현·반복 검토

2026-10-07 KST. 사용자는 구현·반복 코드리뷰·전체 작업본 통합 배포·재기동을 명시 승인했다. 실행 owner: `SemanticMonitorProducerConsumerRefresh1007`.

## 결함과 보완

- 현행 반전 capture에 구 strategy_raw_input과 당일 legacy 선정 보고서를 요구해 machine_raw_input_missing 95건을 제출 결손처럼 전달했다. 해당 hash의 exact raw capture와 BLOCK 판정은 실제 존재했다. frozen native family·source/publication/effective date 및 raw 승률 선정으로 dispatch하고 기존 generation만 legacy 검사한다.
- notifier의 main_machine_policy 누락과 cumulative_winrate_selected 복구 누락을 수리했다. native 복구에는 동일 source/target/stage/scope, 현재 관측일의 검증 generation/status binding 및 clean findings가 필요하다.
- 생산자에 새 receipt와 실제 보조 request 원본/hash를 연결했다. quote as-of보다 뒤에 발생하되 snapshot 읽기/판정 이전인 WS 반전을 구 quote clock으로 거부하던 소비자 clock 혼동도 수리했다. 새 receipt 누락/변조는 명시 결손; 기존 capture는 별도 계수한다.
- 실제 request 준비/원 응답은 별도로 관측하며 compose의 provider_called metadata는 실제 호출 근거로 쓰지 않는다.
- current parsed OPEN owner에 연결하고 원 producer owner/counts를 보존했다. OFF와 historical 진단은 현재 알림에서 분리하되 seal/hash 손상과 surviving episode 원천 결손은 감추지 않는다.
- 퇴역 owner의 unit/process/신규 BUY를 registry/transition 원천으로 검사하며 Main·기존 custody exit는 허용한다. episode 적용 deadline은 실제 07:35 producer +60초 publication grace로 정렬했다.
- artifact coverage 40개 및 native 13단계 기능 연결을 확인한다. code-only handoff가 연구 kernel/auxiliary issued contract bytes를 변경하지 않는다.

## 반복 검토·검증

1차 검토에서 WS event/quote clock의 잘못된 선후 비교, legacy metadata의 새 component hash 오해, notifier native 복구 및 missing owner/count 손실 위험을 보완했다. 2차 검토에서 새 계약 receipt 삭제, ENTER input/prompt/schema 변조, provider preparation/execution 혼동, OFF 사유, 07:35 producer 실패 및 bounded inode 변경을 보완했다. 기존 kernel 변경 테스트는 보존 원본의 custody 검증 계약에 맞게 정정했다.

최종 targeted pytest·compile·diff-check·print-only parser, immutable release 검증 및 실제 재기동 결과는 `data/report/semantic_monitor_refresh/2026-10-07/`의 영수증에 기록한다. 배포 전 작업본 PASS는 운영 적용 증거가 아니다.

## 유지한 경계·잔여 수용

기계/보조 12+12셀, 비용·30분/+0.4%/soft −3% 라벨, 운영 quota=None, provider 간격/timeout/중복 및 broker/order/수량/자본/가격/custody/manual/retirement hard guard를 보존한다. Kiwoom protocol 요청/FID/응답 parser는 변경하지 않는다. EOD·frozen 연구·정책은 그대로다.

Rebase §7의 구 2종목/선정 계약과 현행 명시 override·5종목/12셀의 문서 충돌은 공개하고 baseline 파일을 수정하지 않았다. HPSP·알테오젠·주성의 same-date NXT eligibility 결손은 별도의 원천·고정감시 OPEN이며 의미적 감시의 코드 결함과 구분한다. provider/submit/fill/economics 자연 미관측 및 외부 Windows 퇴역 확인은 미관측 상태로 남긴다.

3차 검토에서 퇴역 census가 pytest 대상 파일 인자를 실행 entrypoint로 오인한 사례를 수정했다. 실행 module/script만 검사하고 shell/python -c와 pytest target 인자는 owner 증거로 사용하지 않는다. 장중 문서 변경은 원 PREOPEN 재생성 대신 native controller/summary/checklist reseal을 policy-preserving handoff에 결속한다. 관련 변조 fixture는 정책 변경·controller/checklist 사후 변경·잘못된 날짜를 차단했다. 반복 source/PID 검증은 invocation 내부의 hash 검증 완료 generation·정확 PID/cwd/start ticks별로 재사용한다.

최종 code gate: 관련 25개 test module **1,266 PASS**(38.22초), 수정 Python compile·기존 실행 wrapper bash -n·git diff --check·print-only backlog parser PASS. 반복 검토 범위의 미해결 코드 결함 0. 검사 batch/원 실패/재검토 로그는 tmp/semantic-monitor-*-tests-20261007.log에 보존했다. 배포·실제 PID·자연 관측은 이어서 별도 영수증에 남긴다.

배포 직전 추가 검토: 새 PID bootstrap verification과 selector attestation 갱신을 원 summary에 결속하지 못하는 결함을 수정했다. 원 summary/controller/정책/env를 변경하지 않고 검증된 intraday reseal·consumed PID의 정확한 source/date/hash만 인정한다. summary·consumption·env 변조는 거부하고 actual PID 증명과 report의 PID 미확정 표현을 분리한다. 관련 startup/summary/readiness/finalization/strict/bootstrap 회귀 **234 PASS**(5.43초). 기존 startup test fixture의 BOOTSTRAP_DIR도 tmp_path로 격리했다. 장후 summary 회복은 원 10/6 publication과 10/7 prepared session을 지정하여 10/8 정책 선택으로 넘어가지 않게 한다.
