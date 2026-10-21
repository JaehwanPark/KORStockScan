# Main 기계판정 패턴 누적 연구 — 2026-10-21

## 결정과 연구 계약

사용자 지시의 추가 포착(A), ENTER_NOW 실패 감소(F), 결합(A+F)을 현재 정책 기준으로 실행한다. 오프라인 수동 연구이며 현재 정책 선택, 보조평가 입력·응답·membership, 배포, 재기동, provider, 주문, 호가 TTL 또는 hard safety를 변경하지 않는다.

지표는 일반 원칙과 승인된 family 예외로 구분한다. [Plan Rebase §1/§3/§7](../plan-korStockScanPerformanceOptimization.rebase.md#1-current-decision-state)의 Main 기계진입 예외와 실제 현재 family의 `selection_metric=cumulative_raw_win_fraction`을 연구 비교 기준으로 사용한다. 비용 포함 목표 선도달 비율 `W/(W+STOP+TIMEOUT)`을 우선하고 동률이면 W 수, current, 적은 정의 수, 고정 ID 순으로 정리한다. 원천 결손 U와 TIMEOUT은 실제 금전 손실이 아니다. 일반 family의 승률은 진단 지표이며 실제 기대수익·순이익은 별도 실제 체결·확정 비용·완료 결과로 확인한다. 이번 오프라인 탐색에 새로운 EV·성공 보존·표본 하한을 추가하지 않는다. 운영 등록·정책 승계는 해당 family의 기존 승인·원천·적용일·소비 계약이 별도로 소유한다. AGENTS와 Plan Rebase의 내용을 이번 연구에서 개정하지 않는다.

원 연구의 [계획](../proposals/main-cumulative-opportunity-and-executable-quote-research-plan-2026-10-17.md)과 [검토](main-cumulative-opportunity-failure-and-nonfixed-quote-review-2026-10-17.md)는 과거 결과로 보존한다. 과거 parent 대비 개선을 이번 개선에 합산하지 않는다.

## 기준선과 방법

- workspace baseline: `1f90a93fa5ee35ee03255a44649f07f26f1b4af0`; 실제 선택 코드: `e0d07d4abb6457ff99955db7596e9a0f9b24f2f2`.
- 연구 policy snapshot: `3691a72e3d31e4a4bc9d7e3cae6c89eb98131045b8740ae1692aa51ca465eaaf`. 현재 family membership과 source20 native machine 보고서의 모든 scope membership이 일치한다.
- 종료된 source20 보고서의 72개 파티션·원천/코드/기존 연구/분봉 571개 봉인을 사용한다. 진행 중인10/21 원천은 포함하지 않는다. native projection의 원 코드 지문과 현재 정책 코드 지문은 따로 보존하며 동일하다고 주장하지 않는다.
- 원래 native 확인점·당시 prefix facts·라벨을 검증된 읽기 전용 `offline_comparison_store.Store(readonly=True)`로 읽는다. 현재 membership의 기존 native 기준선은 W1528/STOP281/TIMEOUT540/U10269다. 새 A는 실제 원천의 당시 수신 prefix, 기존 hold·source break·quote·실제 ask 계약으로 계산하고 동일 item의 봉인 완료 분봉만 결과 보조에 사용한다.
- 연구 quote 적격은 기존 kernel의 age 미기록 또는 최대5,000ms 계약을 그대로 사용한다. 이것은 실제 AI 입력 전/제출 직전의 더 엄격한 quote·동일 route·deadline 통과 증거가 아니다. 이 연구로 새로운 TTL을 정하거나 실제 제출 가능·체결 성과를 승인하지 않는다.
- 기존 A17~24·F23~30을 재사용하며 A25~28·F31~34를 결과 전 동결한다. 새 A는 돌파 강도/스프레드, 완만한 추세의5초 유지, 얕은 눌림의5초 유지, VWAP 회복의3초 유지다. 새 F는 개별 종목 세션 중립/약세/강세와 두 가지 확인 구조를 구분한다. 이는 지수 기반 시장 regime 증명이 아니다. 정확한 임계값과 정의는 [manifest](../../tmp/main-machine-cumulative-dual-track-research-20261021/manifest.json)에 보존한다.
- 12개 A의4096 OR 조합과 CURRENT+12개 F를 같은 scope에서 비교한다. A-only/F-only/결합 및 baseline 비율 이상에서 W를 최대화하는 기회 확대 대안을 각각 공개한다. 고정 감시/비상시감시, 날짜·시장·세션, 추가/제거 W·STOP·TIMEOUT·U와 중복 목표 도달 시각을 구분한다.
- 같은 누적 자료를 사용한 탐색이다. 기존 가설을 이미 평가한 날짜도 독립 holdout으로 부르지 않는다. 10/19·20의 보존 정규화 원천은 현재 적격 표시가 모두0이다. 그 결손은 탐색의 성공·실패0건 또는 새 유효 검증일로 바꾸지 않는다.
- 기존 frozen feature/hold/label/scalar filter와 native projection을 재사용한다. 파티션마다 원천을 한 번 읽고, 조합은 확인점 bitset으로 계산한다. 단일 낮은 우선순위 worker, 기존 2GiB/CPU480초/wall600초 한도를 유지한다.

## 검토와 교체·제거

- 기존 봉인 연구 스크립트·원천·등록 정의: `retained`. 현재 정책의 원 연구 해시와 historical native reader가 소비하므로 수정하지 않는다.
- 이번 실행 제어: 기존 offline 연구 소유 위치인 `tmp/main-machine-cumulative-dual-track-research-20261021/`의 임시 실행 CLI와 원 결과를 소비하는 해석 단계가 담당한다. 과거 스크립트를 확장하면 정책이 참조하는 봉인이 바뀌므로 이번 날짜의 제어 파일이 필요하다. 기존 feature·hold·label·filter 및 읽기 전용 store를 직접 재사용하며 새 runtime producer/validator framework/등록/스케줄은 없다.
- 기존 연구 대비 원천 전체를 조합마다 재생하는 방식: `consolidated`. 현재 native membership은 원 projection을 재사용하고 새 A의 원천 특징은 파티션당 한 번 계산한다. scalar 전체행 gate는 동등성이 검증된 열 연산으로 계산하며 scalar owner는 기존 frozen 결과의 reader와 동등성 회귀에 유지한다.
- 원천 당일의 분봉만 포함한 첫 준비안은 역사 A 라벨을 불필요하게 검열하는 결함이 있어 본 계산 전에 폐기하고, source20 native 보고서의 모든 역사 분봉 영수증으로 보완했다. 원 준비 시도는 [attempts](../../tmp/main-machine-cumulative-dual-track-research-20261021/attempts/)에 보존한다.
- 코드 자체와 기존 원본을 제거하거나 새 호환 wrapper로 대체하지 않는다. 제거 보류된 runtime 경로는 없다. production source/test/entrypoint 추가·삭제는0이다. 기준 commit 대비 임시 non-test 분석2파일 +489/-0행, 임시 회귀1파일 +55/-0행과 이 연구 기록을 추가했다. 이동은 없다. 순증은 봉인된 과거 owner를 재사용하는 실행 제어,4개 새 A/4개 새 F, 유한 조합 및 분모 미정·기회 중복의 해석이다. 새 runtime owner/branch/스케줄은 없다. 동시 작업의 다른 audit/checklist/runbook 변경은 이 연구 diff에 포함하지 않는다.

## 계산 전 검증

- 현재 코드의 완전한3개 종목 경로27,408행에서 기존 native 확인점41개와 exact identity membership이 일치했다. [native 비교](../../tmp/main-machine-cumulative-dual-track-research-20261021/preflight.json).
- 기존 회귀와 새 UNKNOWN/조건부 F/구조 매핑/열 연산 동등성 회귀36개 PASS. 미래 suffix 불변, source break, hold 취소, 실제 ask 라벨을 포함한다. [검사 로그](../../tmp/main-machine-cumulative-dual-track-research-20261021/tests.log).
- 검토·보완·재검토 후 본 계산을 실행한다. 검증 PASS는 후보 등록·현재 PID 소비·새 실현성과의 증거가 아니다.

## 본 계산 결과

72개 파티션, 총7,913,317행 중 적격4,530,988행을 처리했다. 원천 날짜는12개, 적격 행이 있는 날짜는9개, 확인점이 있는 날짜는8개다. 총21,842개 확인점을33개 scope에서1,757,184개 조합으로 비교했다. 원본 source20 native projection의 현재 membership 기준선 W1528/STOP281/TIMEOUT540/U10269를 정확히 복원했다.

검토에서 baseline의 확정 분모가 없는5개 scope를 별도 진단으로 분리했다. 이는 새 표본 하한이나 선택 탈락 조건이 아니라 미정 비율에서 상대 개선율을 만들지 않기 위한 보고 분리다. 원래 전체 결과·순위·membership은 수정하지 않았다. [전체 결과](../../tmp/main-machine-cumulative-dual-track-research-20261021/result.json)와 [비교·기회 시각·실제 사례](../../tmp/main-machine-cumulative-dual-track-research-20261021/reviewed-comparison.json)를 함께 보존한다.

아래는 비교 가능한28개 scope다. 각 scope의 비율을 우선해 선택한 조합의 전체 합계이며 전체 합계 비율을 직접 전역 최적화한 결과가 아니다.

| 비교 | W | STOP | TIMEOUT | U | 확정 분모 | 목표 선도달 비율 | 서로 다른 목표 시각 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 현재 기준선 | 1,528 | 281 | 540 | 10,018 | 2,349 | 65.05% | 203 |
| 추가 포착 A | 1,548 | 281 | 541 | 10,029 | 2,370 | 65.32% | 207 |
| 실패 감소 F | 1,190 | 26 | 422 | 9,773 | 1,638 | 72.65% | 131 |
| scope별 비율 우선 결합 | 1,210 | 26 | 423 | 9,784 | 1,659 | 72.94% | 135 |
| 기회 확대 대안 | 1,565 | 279 | 539 | 10,177 | 2,383 | 65.67% | 209 |

- 비율 우선 결합은 선도달 비율이65.05%에서72.94%로 오르지만 W가318개 줄어든다. 기존 W338/STOP255/TIMEOUT118/U245를 제거하고 W20/TIMEOUT1/U11을 추가한다. 새로운 목표 시각4개를 얻고 기존 목표 시각72개를 잃어203→135개다.
- 기회 확대안은 기존 W 제거0, 새 W37/STOP0/TIMEOUT31/U195를 추가하고 STOP2/TIMEOUT32/U36을 제거한다. W1528→1565, 비율65.05%→65.67%, 서로 다른 목표 시각203→209개다. W37개의 증가를37개의 독립 거래로 부르지 않는다. 새 목표 시각은6개이며 이 또한 실제 체결/손익 증빙이 아니다.
- 전체33개 scope를 합친 원 결과는 기준선65.05%·W1528, A64.91%·W1552, F72.65%·W1190, 결합72.26%·W1214, 기회 확대65.27%·W1569다. 분모 없는 scope의 진단 확인점이 섞인 값이므로 위28개 비교와 혼용하지 않는다. baseline 미정5개는 두산 AFTER NXT/REGULAR NXT, 알테오젠 AFTER NXT, 삼성 PRE SOR/REGULAR NXT다. 그중4개에 추가 후보가 있지만 두 scope는 W0인 시간 내 미도달만 생겼다. 이 결과에 상대 개선이나 운영 수용 의미를 붙이지 않는다.
- 고정/비상시감시도 분리했다. 전체33개 scope 기준 현재 고정 감시의 W1197/확정1715(69.80%), 비상시감시의 W331/확정634(52.21%)다. 기회 확대는 각각 W1203/1726(69.70%), W366/678(53.98%)다. 전체 비율 상승만으로 고정 감시도 개선됐다고 주장하지 않는다.

### 새 가설과 반례

- A25·A26·A28은 이번 순위 우선안이나 기회 확대안에 선택되지 않았다. 적격 후행 날짜가 없으므로 미래에 무효임을 입증한 결과는 아니다.
- A27(얕은 눌림 회복의5초 확인)은 비상시감시 PRE/SOR 저가 scope 한 곳에서 선택됐다. 다른 선택 A를 유지한 한계 기여는 결합안 W5, 기회 확대안 W2지만 **새로운 목표 도달 시각은 두 경우 모두0**이다. 같은 상승 경로의 늦은 확인점을 늘린 효과와 새로운 상승 포착을 구분해야 한다.
- F33(개별 종목 강세일 때 구조·60초 수익률 상/하한·spread 확인)은 비상시감시 PRE/SOR 저가에서 선택됐다. A18+A27과 결합하면 baseline201/350에서22/24로 비율은 높아지나, 기존 W197과 STOP148을 제거한다. 희생한 성공 기회를 숨기지 않는다.
- F34(매수·VWAP·수익률 확인 또는 상승 구조·거래량·spread 확인)는 주성 AFTER/SOR 고가에서54/89→38/46, 비상시감시 PRE/SOR 중가에서46/176→4/12다. 주성에서는 W16과TIMEOUT27을 제거하며 STOP 감소를 입증한 사례는 아니다. F31·F32는 선택되지 않았다.
- 새 정의를 포함한 모든 조합은 같은 누적 자료에서 탐색했다. 이미 여러 연구에 사용된 날짜를 새 독립 holdout으로 부르지 않는다. 10/19·20의 적격0은 그대로 남으며 최신 후행 검증을 확보했다는 결론은 없다.

### 수용 범위와 소비자

연구 가설과 결과 비교는 완료했다. 운영 정책 선택·등록·발행·실제 PID 적용·새 실현성과 수용은 실행하지 않았다. 새로운 prefix 특징(ret180/dd180/recover60)·root 및 F34의 OR 조건은 현재 typed catalog/조건 소비자가 동일 의미로 처리하는지 별도 확인해야 한다. 기존 정책반영 owner는 정의/field/scope/OR·UNKNOWN·원천/가격/native parity와 보조평가 호환성을 검토할 때 이 결과를 소비한다. 연구상의 후보 ID를 현재 runtime ID나 바로 실행 가능한 정책으로 취급하지 않는다.

## 최종 검증과 경계

- 표적 회귀44개 PASS. 기존36개와 완료 분봉의 목표/양 장벽/경계/결손/시간 미도달/ask 결손8개를 포함한다. 마지막 로그의 경고1개는 `-c /dev/null`에서 pytest cache를 `/dev`에 만들지 못한 경고이며 검사 누락·애플리케이션 실패가 아니다. [로그](../../tmp/main-machine-cumulative-dual-track-research-20261021/final-tests.log).
- [최종 검증](../../tmp/main-machine-cumulative-dual-track-research-20261021/validation.json): 독립 선형 틱 라벨137개, exact key/ask147개,3개 완전 종목 경로27,408행·기존 확인점41개 일치, 원천/코드/분봉 봉인571개 PASS. 별도 완료 분봉10개 사례는 원시 틱이 먼저 미확정임과 동일 item 분봉의 결과 일치를 확인했다. [분봉 검증](../../tmp/main-machine-cumulative-dual-track-research-20261021/bar-supplement-validation.json).
- 결과 해석 단계는 원 순위·membership을 다시 검색하거나 바꾸지 않고 모든 역할의 전체 지표를 원 결과와 전수 대조한 뒤, 확정 분모 유무와 실제 목표 시각 증감을 계산했다. 이 단계는 새 정책 선택/승인 guard가 아니다.
- 본 계산의 파티션별 elapsed 합계513.45초, 최대RSS705.29MiB다. 압축된 입력 크기102,206,554B와 행 수를 별도로 기록했다. 원천 특징 계산은 파티션당 한 번이며 입력 봉인·독립 검증 읽기는 별도다. 전체 실제 물리 디스크 I/O를 독립 계측하거나32MiB 생산 예산을 입증한 결과는 아니다.
- 계산 중 외부 작업이 선택 릴리스를193668e7f/PID1358421로 전환했다. 본 연구는 재기동·선택·provider·주문을 실행하지 않았고 원 e0d 기준선/PID 시도와 selector 변경을 분리 보존했다. Main/보조 정책 포인터는 그대로다. 넓은 scalping 봉인226개 중 새 릴리스에서3개 실시간 원천/회복·진단 파일이 달라졌고, 연구 결과를 새 PID의 자연 관측/실행 성과로 전용하지 않는다. [외부 전환 대조](../../tmp/main-machine-cumulative-dual-track-research-20261021/external-transition-comparison.json).
- source19·20 epoch 증빙의 인과 수리/복구는 아래 결손 기록에 남긴다. 이 연구 계산의 완료는 그 생산자 결함이 수리됐다는 뜻이 아니다. 실제 시장 주문·실현손익 테스트, 실시간 provider, canonical 장후 재생성은 실행하지 않았다.
- Python compile, 문서 링크14개/권한/소유 경계, `git diff --check`, print-only parser PASS. 외부 Project/Calendar sync는 실행하지 않았다.


## 10/19·20 적격0의 의미와 원인 범위

사용자의 생산자 코드 결함 여부 질문에 따라 [원본 epoch 대조](../../tmp/main-machine-cumulative-dual-track-research-20261021/source-epoch-gap.json)를 추가했다. 모든 해당 파티션의 직접 제외 사유는 `source_epoch_unverified`다. 원시 가격이 모두 잘못됐다는 뜻이나 실제 시장 기회가0이라는 뜻은 아니다.

정규장 기준10/19의339,537행은9개 수집 epoch에 속하지만 보존된 유효 종료 증빙은 다른 epoch `1792408975403344583` 하나이며 그 수집 건수는0이다. 10/20의343,612행은10개 epoch지만 유효 종료 증빙은 다른 epoch `1792493874709471241` 하나이고 역시 수집0건이다. 10/19의 별도 종료 증빙은 `unaccounted_raw_row_exclusion`으로 거부돼 적격 epoch로 사용할 수 없다. 이는 모든 날짜를 일괄 거부하는 새 guard가 아니라 각 행의 수집 epoch와 검증된 종료 증빙이 연결되지 않는 상태다.

확인된 최초 계약 결손은 수집 epoch→종료 증빙 보존→장후 발견/소비 사이의 인계다. `kiwoom_websocket._close_micro_reversion_forward_collector`, `canary_monitor.write_canary_runtime_snapshot`이 종료·보존을, `continuous_reversal_source._source_quality_receipt`, `observer_source_quality.main_raw_epoch_validation`이 발견·검증을 소유한다. 특정 생산자 함수 결함, 과거 프로세스 강제 종료, 별도 영수증의 발견 누락 중 어느 것이 실제 원인인지는 아직 입증하지 않았다. 정규화기의 미증명 epoch 제외를 풀거나0건 종료 영수증으로 다른 epoch를 승인하지 않는다.

다음 조치는 정확한 과거 PID/종료 원본과 영수증 custody를 대조하고 현재 close/restart 발행 경로를 재현하는 것이다. 원본 epoch 증명이 없으면 과거 표본의 복구를 주장하지 않는다. 이번 연구는 이미 적격인 누적 분모로 계속하며 이 결손을 새 검증일이나 성과로 계상하지 않는다. 현재 프로세스 재기동·수집 변경·producer 코드 수리는 이 연구에서 실행하지 않았다.

### 후속 인과 진단: 종료·보존·소비

사용자의 후속 지시에 따라 위 미확정 원인을 추적했다. 기준 commit은 `1f90a93fa5ee35ee03255a44649f07f26f1b4af0`다. [검토 완료 진단](../../tmp/main-machine-cumulative-dual-track-research-20261021/source-epoch-diagnosis/reviewed-result.json)에 원본 hash, 각 epoch의 첫/끝 수신, 과거 전환/PID/start ticks, 실제 코드와 격리 재현을 결속했다. 기존 10개 정규화 파티션만 한 번 읽어 총928,714행·29개 epoch를 대조했으며 원시 전체 재생이나 canonical 장후 재생성은 하지 않았다.

| 단계 | 판정 | 근거 |
|---|---|---|
| 종료 | 일차 원인 확인 | 10/19의13개 epoch·481,383행과10/20의15개 epoch·435,526행은 재시작 전 수신됐고 해당 종료 영수증이 없다. 두 restart 분기의 self-SIGTERM이 cleanup을 건너뛰는 경로를 재현했다. |
| 보존 | 별도 증빙 결손 확인 | 나머지10/19 epoch의11,805행은 정상 close·writer count 일치다. 종료 파일도 보존됐지만 pre-enqueue 거부121건 중 마지막64건만 남아 전체 거부 증명을 충족하지 못한다. |
| 소비 | 이번 결손의 최초 원인으로 입증되지 않음 | 원 source manifest의 종료 영수증 hash와 현재 closed 원본이 일치하고, 실제 발견 목록도 일치한다. 정상 영수증의 후속 boot 생존·동일 epoch 소비 회귀는 PASS다. 미증명 epoch 제외는 현재 계약의 동작이다. |

**종료의 인과 경로.** `bot_main.py`는 `run_sniper`를 daemon thread로 시작한다. 관제탑의 restart.flag 분기와 `kiwoom_sniper_v2.run_sniper`의 restart.flag 분기 모두 `os.kill(os.getpid(), signal.SIGTERM)`을 실행한다. 이 경로에는 SIGTERM handler가 없으며, pipeline 요약 drain은 WebSocket/수집기 종료를 수행하지 않는다. 기본 SIGTERM 종료는 Python stack을 풀지 않아 `run_sniper`의 `finally`에 있는 `WS_MANAGER.stop()`을 건너뛴다. 따라서 `_close_micro_reversion_forward_collector` → collector close/reconciliation → final canary snapshot → `closed/<date>-<epoch>.json`에 도달하지 않는다. 운영 배포의 `Deployment.drain`은 PID와 supervisor 부재를 확인하지만 수집 epoch의 최종 증빙까지 확인하지 않는다. 프로세스 소멸은 이 원천 계약의 종료 성공 증거가 아니었다.

당시28개 commit과 현재193668e7f의 두 restart 분기를 확인했다. 초기19/20 코드와 현재 코드에는 정상 close 이후의 immutable closed 발행 경로가 이미 있다. 현재 선택193668e7f/PID1358421/start18840517도 `/proc` cwd/start ticks가 일치하고 SIGTERM catch/ignore/block bit가 모두0이다. 따라서 과거 릴리스에만 국한된 가설이 아니라 현재 경로에도 같은 위험이 남는다. 해당 PID에 신호를 보내거나 재기동하지 않았다.

정규장 예시는10/20 epoch1792453443511229483이다. 정규장31,573행을 포함한 전체49,221행의 마지막 수신09:15:56.969, restart 로그09:15:54, ordered drain09:16:02.746, 실제 이전 PID3846509/start9795483/commitab1c46633이 연결된다. 이후 epoch의 clean-close 영수증으로 이49,221행을 승인할 수 없다. 전체 epoch별 대응은 진단 JSON에 보존한다.

자체 검토에서19:56 recovery 전환의 `predecessor_identity`를 실제 직전 수집 PID로 읽으면 잘못된다는 점을 보완했다. 그 필드는 원 실패 이전의 역사 predecessor3081598을 보존한다. 마지막14,351행의 실제 수집자는 실패 candidate68213의 PID3745840/start13706728이며 기존 `approved-failed-main-drained.json`의19:56:28.152 증거와 실제 코드로 별도 결속했다. 최초 진단 결과와 이전 문서 bytes는 그대로 두고 검토 결과에 이 구분을 기록했다. 원 custody identity를 수정하지 않았다.

**보존의 인과 경로.** `forward_collector`는 `TIMESTAMP_REJECTION_SAMPLE_LIMIT=64`인 deque에 마지막 거부 표본만 보관한다. 반면 `canary_monitor.timestamp_source_quality_census`와 `closed_pre_enqueue_epoch_quarantine_validation`은 총수·유형별 수·연속 rejection index가 전체 모집단과 같아야 증빙을 인정한다. 문제 영수증에는121건 중 index58~121만 있어57건의 증빙이 없다. `main_raw_epoch_validation`의 `unaccounted_raw_row_exclusion`은 이 불일치에서 발생한다. 저장된 raw11,805행이 없다는 뜻이나 실제 손익0이라는 뜻이 아니며 다른 적격 조건까지 통과했다고 주장하지도 않는다. 이는 닫힌 JSON 파일의 발견 누락이 아니라, bounded 진단 tail만으로 전체 거부 증명을 제공하지 못하는 생산자→소비자 계약 결손이다. 단순 cap 확대나 소비자 완화로 닫지 않는다.

**격리 검증.** 원 restart 분기의 broadcast/요약 drain만 mock하고 실제 self-SIGTERM을 격리 child에서 실행했다. 두 분기 모두 raw1행이 저장된 뒤 exit-15, cleanup 미호출, closed 영수증0개였다. 정상 break 대조군은 exit0, cleanup 호출, closed1개였다. 전체 봇을 기동한 검증은 아니며 살아 있는 Main에는 영향을 주지 않는다. 별도 실제 collector→canary writer→epoch validator→normalizer 대조에서 정상 raw1행과 거부64건이면 적격1행, 거부65건이면 같은 정상 raw1행도 적격0행이 됐다. tail이64로 잘리면서 전체 증명 조건이 깨지는 경계를 직접 확인했다. 기존 종료 영수증 생존·잘못된 epoch/충돌 거부·bounded tail·producer epoch 회귀7개도 PASS다.

**다음 수리 순서와 완료 기준.**

1. 종료 owner인 `bot_main`/`run_sniper`의 중복 restart 경로를 하나의 협력적 종료 경로로 연결한다. producer 중단→worker/writer drain→epoch별 close/reconciliation→immutable 영수증 보존을 끝낸 뒤 프로세스를 종료하도록 한다. `ordered_intraday_deploy`의 기존 drain acceptance도 실제 직전 수집 PID/epoch 증빙과 결속한다. 현재10초 bound를 늘리는 것으로 대체하지 않는다.
2. 증빙 owner인 `forward_collector`의 기존 거부 기록/보존 경로를 수리한다. 진단64건 tail은 그 용도로 유지하되 소비자가 요구하는 exact rejection identity/coverage를 유실 없이 영속 보존하고 기존 canary/epoch 소비자에 연결한다. 별도 wrapper나 증명 없는 성공 표시는 추가하지 않는다. 재접속 epoch, writer 실패, 부분 기록,65건 이상, 날짜 경계와 다른 PID 증빙을 함께 검증한다.
3. 같은 격리 재현에서 두 restart 경로 모두 실제 해당 epoch의 closed 증빙을 만들고 정상 행을 소비하는지 확인한다. wrong-date/다른 epoch/누락·손실 증빙은 계속 제외돼야 한다. 코드 리뷰·회귀 완료, 배포/PID 소비, 다음 자연 종료 수용은 별개로 보고한다. 과거 표본은 원본 증빙의 독립 보존본을 찾은 범위만 복구 가능하며 이번 진단으로 새 closed 영수증을 소급 생성하지 않는다.

교체·제거: 이번 진단에서 production source/test/dispatch는 `retained`이며 변경+0/-0이다. 기존 close writer와 epoch guard는 정상 종료/장후 소비의 현재 owner이므로 유지한다. 향후 수리는 기존 두 restart 분기와64건 진단 tail의 증명 용도 오용을 교체·통합해야 하며 별도 runtime owner/스케줄은 필요하지 않다. 이 기록과 기존 evidence 위치의 일회성 진단 코드만 추가했다. 수리는 아직 구현·배포되지 않았으며, 완료된 연구 계산과 분리해 원인 분석 완료/인과 수리 미완료로 남긴다.

후속 검증: 관련 회귀7개, 격리 종료 대조3개와64/65건 생산자→소비자 대조2개 PASS. 진단 코드 compile, 문서 링크15개, 원 closed3개 SHA 불변, selector/PID receipt 불변, `git diff --check`, print-only backlog parser PASS. production source/test +0/-0, 이 audit만 +32/-0, 임시 진단 코드1파일 +261/-0이며 이동·새 runtime entrypoint는 없다. 동시 작업의 checklist/runbook/다른 audit는 수정하지 않았다. 외부 sync·실행 PID 신호·provider·주문 호출은0이다.


### 종료와 거부 증빙 생산자 수리 — 2026-10-21

구현 기준은 현재 배포 `ea68c5a85`의 문서 후속 `b53ebf689`다. 격리 worktree `collector-epoch-close-20261021`에서 기존 두 재시작 분기를 공통 협력 종료 요청으로 통합했다. Main은 non-daemon 엔진의 native finally가 끝난 뒤 요약 drain으로 진행한다. SIGTERM·KeyboardInterrupt와 야간 재시작도 같은 요청을 사용하며 강제 종료 fallback을 두지 않는다. 다른 worker 정리 예외가 있어도 WebSocket/수집기 finally를 실행하고, 최종 canary 저장 실패 시 collector를 보존하고 실패를 반환한다. callback quiescence→worker→writer는 기존10초의 같은 deadline을 사용한다.

거부64건 tail은 진단용으로 유지한다. 기존 collector worker가 bounded queue의 모든 거부를 `timestamp_rejections/<initial_epoch>.jsonl`에 기록하고 종료 시 fsync·행 수·byte 수·SHA·PID/start ticks를 결속한다. queue full·write/fsync 실패는 incomplete이며 성공 영수증을 만들지 않는다. canary/epoch 소비자는 순차 index·유형별 수·동일 PID/start·정확한 reconnect epoch membership과 파일 SHA를 streaming 검증한다. current-epoch quarantine 범위는 그대로다. 새 journal이 잘못됐을 때64건 tail로 되돌아가 승인하지 않는다. 기존 원본의 legacy reader는 유지한다.

immutable closed 발행은 기존 collector owner에 남는다. 날짜를 넘긴 종료는 실제 종료 시각과 raw의 source_date를 각각 기록하며 native 정규화 소비자가 해당 날짜를 검증한다. 동일 epoch 재발행은 원 영수증을 유지하고 다른 snapshot 충돌은 실패한다. ordered 배포 owner는 종료 전 실제 actor/epoch를 고정하고, 종료 후 PID 소멸과 immutable native closed 증빙을 함께 확인한다. 단계 상태도 기존 startup hold를 유지하며 과거 단계로 되돌리지 않는다. 구버전의 actor 증명 부재를 우회하는 예외는 추가하지 않았다.

Kiwoom 공식 gate는11:08:57 KST upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`, `kiwoom/specs.py`, `kiwoom/realtime/{stream,packets,events,schemas,decoders}.py`, Postman을 재확인했다. 해당 tree에 `kiwoom_docs`는 없으며 기존 wire/FID/REG/REMOVE/주문 계약은 변경하지 않았다. [조회 hash와 시각](../../tmp/main-machine-cumulative-dual-track-research-20261021/epoch-repair/official-reference.json)을 보존했다.

자체 검토에서 종료 저장 실패의 객체 유실, 재시도 시 close counter 변경, 자정 날짜 결속, callback의 I/O 금지, SIGTERM handler의 재진입 lock 위험, 배포 단계 역행을 보완했다. 기존 전체 loop/startup AST 비교는 종료 제어 변경만 역투영하여 매매 본문이 기존과 동일함을 검증한다. 별도 provider·주문 호출은 없다.

검증 근거는 [기존 진단의 수리 하위 디렉터리](../../tmp/main-machine-cumulative-dual-track-research-20261021/epoch-repair/)다. 두 실제 restart 분기를 격리 child에서 실행하여 raw1행+거부65건의 native closed/소비를 확인했다.64·65·121·1,000건, reconnect, 잘못된 날짜/PID/start/epoch/index/hash, 누락·부분 파일, queue/write/fsync 실패, 영수증 저장 실패·재시도와 구버전 혼합을 검증했다.20,000건/15,548,894B의 callback+drain+close는0.936초, native 검증은0.137초 이내였고 진단 tail64·정상 raw1·queue loss0이었다. 전체 raw를 재해시하지 않고 거부 journal을 한 행씩 읽는다. 새 측정의 콜백 p99는0.033177ms로 기존 한도2ms를 유지한다. [동결 측정](../audit-reports/2026-10-21-collector-epoch-latency-validation.json.txt).

교체·제거: 두 self-SIGTERM 분기와 야간 self-SIGTERM dispatch는 `removed`/공통 request로 `consolidated`, 중복 선행 summary drain은 Main의 join 이후 단일 호출로 `consolidated`다. 기존 collector worker·raw writer·canary writer·native epoch validator·정규화 consumer는 현 호출자가 있어 `retained`하며 동일 owner를 확장했다.64건 tail의 전건 증명 용도는 새 생산자의 sealed journal로 `replaced`;64건 legacy reader는 과거 immutable 영수증 소비 때문에 `retained`다. 새 Python module·scheduler·provider·매매 branch·wrapper는 없다. 기존 restart owner의 공유 종료 함수와 기존 ordered owner의 pin/close 검증만 추가했다. 종료 보장에 필요한 non-test 순증과 별도 실패 회귀를 원인 수리로 구분하며, 과거 audit 원문은 이 수정 전에 존재한 사용자 증거다.

배포/PID 수용은 OPEN이다.11:22:49 incumbent `ea68c5a85`/PID1724066/start19233026, epoch1792547808026387070은 running·raw26,488·거부0·closed 없음이다. [읽기 전용 native pin 결과](../../tmp/main-machine-cumulative-dual-track-research-20261021/epoch-repair/incumbent-stop-contract.json)는 `deployment_collector_shutdown_actor_unproven`이다. 현 PID의 기본 SIGTERM은 여전히 cleanup을 건너뛰며 외부의 native 협력 종료 명령은 확인되지 않았다. 승인된 배포라도 이 조건에서 restart.flag를 발행해 새 결손을 만들거나 소급 closed 증빙을 만들지 않았다. 다음 수용은 기존 `DirectFamilyPreopenPolicyHandoff`에서 종료 가능한 predecessor/native stopped-consumption 경로, exact 정책/parity/보고서 currentness, 새 PID의 actor와 다음 자연 epoch closed 소비를 각각 확인한다. 강제 종료·실행 코드 주입·guard/timeout 변경은 해결 경로가 아니다. 과거928,714행의 미증명 상태와 원 실패 기록은 그대로 유지한다.

최종 검증: 관련 계약699개, pipeline56개, 원/후속 정책 handoff30개로 고유785개 PASS를 확인했다. 이후 단계 상태 보완의 ordered232개와 고정 소스 후속 handoff15개도 PASS다. compile·diff·문서 링크·print-only parser를 확인하며 canonical current owner는1개다. 초기 혼합 실행의 writer lock 경합 실패는 격리 및 전체 pipeline56개로 재검증했고, 검증 중 수정된 fingerprint 혼합 시도도 원 로그를 보존한 뒤 고정 소스로 재검증했다. `b53ebf689` 대비 non-test source +462/-131, tests +277/-23, docs 자체 수정 +196/-0; 새로 추적한 기존 audit121행은 별도 보존분이다. 이동0·새 module0·새 스케줄0이며 source 순증331행은 협력 종료·완전한 증빙 보존/검증·기존 handoff의 정확한 소스 결속이다. 배포/새 PID 소비/자연 종료 수용/경제성은 이 코드 검증과 별개이며 미완료다.

코드 commit `fb51bb3a8`과 고정된 후속 검증에서 기존 정책128scope·76,800행·598신호·동일 신호SHA `958e471cca3b0e833e20486dbef9aecd6973b0273c53979d8ff1d9a4eb1a42fc`의 native parity PASS를 확인했다. [parity 원본](../../tmp/main-machine-cumulative-dual-track-research-20261021/epoch-repair/fresh-confirmation-parity-provenance.json). 기계 정책 native module 변경0, provider/주문 호출0이다. 후속 문서 +2/-0은 앞선 코드 commit 계수와 별개다. 현재 selector/PID는 그대로 유지하고 원천 미증명 상태를 배포 성공으로 표시하지 않았다.
