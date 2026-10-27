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


### 최초 전환의 native 장 종료 연결 — 2026-10-21

기준 `1fd10ef9c`, 실제 incumbent `ea68c5a85`/Main1724066/start19233026. 장중 두 restart 분기는 여전히 self-SIGTERM이지만, 20:00 native market-close 분기는 반복문을 종료하여 기존 finally와 WS/collector close를 실행한다. 기존 ordered pin은 running+새 actor 필드만 허용하여, 이미 정상 종료된 legacy collector도 전환하지 못했다. 기존 shared WS frame의 process PID/start/boot/root/commit과 completed_bar_integrity.observer_epoch가 빠진 collector actor 결속을 제공함을 현 PID에서 확인했다. 원 snapshot과 종료 영수증에 필드를 소급 추가하지 않는다.

기존 ordered owner의 pin을 확장했다. 같은 날의 실제 소비 selector, 정상 market_close heartbeat/미종결0, 원 WS actor/epoch와 native immutable closed receipt를 재시작 요청 전에 모두 검증한다. 살아 있는 Main은 기존 flag/소유 hold/정책 preflight/90초 종료 절차를 유지한다. 이미 장후 격리된 Main은 기존 closed-consumption 증명에 같은 collector 종료 검증을 추가한다. 종료 후 latest, WS frame, closed receipt 원본 해시를 다시 검증하며 하나라도 변경되면 selection으로 진행하지 않는다. 현재 running legacy PID는 계속 차단한다. 20:00라는 시각이나 프로세스 부재 자체는 전환 승인이 아니다.

회귀: 원 기준은 정상 legacy 종료 fixture에서도 actor_unproven으로 실패했다. 수리본 ordered tests257 및 구 collector-close/새 최초 전환의 delay·stop·holding handoff30 PASS. 다른 PID/start/boot/root/commit/epoch, 미래·전일 시각, 비정상 종료·미종결·alive, 원천 손실, 누락/심볼릭 링크/변경 closed, 불완전 거부 증빙을 차단한다. 원 정책과 앞선 정확 코드 세대는 보존한다. compile 및 diff-check PASS. 증거는 `tmp/quantity-first-transition-20261021/first-transition-baseline.log`; 현재 파일 검증과 자연 수용을 구분한다.

교체·제거: 기존 running-only pin을 동일 owner의 running/이미 종료된 native source 분기로 `consolidated`; 별도 종료 명령·worker·모듈·스케줄 추가 없음. 기존 WS producer, heartbeat, native epoch validator는 현재 caller가 있으므로 `retained`; 이미 발행한 collector-close handoff는 구 후보/정책 읽기 때문에 `retained`. 이전의 첫 전환 경로 미구현은 이 연결로 보완했으나 실제20:00 종료 증빙/PID 전환은 아직 미관측이다. 기존 DirectFamilyPreopenPolicyHandoff에서 동일 PID의 자연 closed와 현재 정책/parity를 확인한 뒤 후보의 ordered CLI로 전환하고 새 PID 소비/observer/full-health를 검증한다. 수량 원천 보완은 별도 기존 InitialQuantityProducerConsumerRepair1010에서 진행한다.

변경량(기준1fd10ef9c): non-test2파일 +108/-12, tests2파일 +115/-8, docs3파일 +17/-0. 이동0. 순증은 기존 종료 증빙을 첫 전환에서 검증하는 분기와 잘못된 원천/세대 음성 회귀이며 매매 기준·수량·guard 변경 없음.

## Research direction and execution — 2026-10-22

사용자 지시의 방향성 갱신·실행과 “근래 약세장에서도 상승 기회를 놓치는가” 질문을 함께 연구했다. [소유 연구 계획의 현재 방향](../proposals/main-cumulative-opportunity-and-executable-quote-research-plan-2026-10-17.md#현재-연구-방향-갱신--2026-10-22)을 먼저 갱신했다. workspace 기준609cdcf12403ec2e2ed7e273cd49e839e781ac9d, selected e9ee2c8eaf97e68df3a82acb23b97998525a3b4e/PID3247910/start29788309, 현재 기계 bundle e815509ba4546974dfb8be2f63730befd4c63289059f5a879271e7057b413b19이다. 이전 연구 대비128개 등록 scope 중7개의 membership이 바뀌었으므로 이전 개선을 현재 개선에 합산하지 않았다. native source21의 현재 membership을 다시 결속했다.

### 원천·동결·검증 범위

전체75개 파티션·8,376,172행, 적격4,787,473행이다. 과거72개는 normalized hash·feature/kernel·exact native key/ask/라벨이 같은 범위만 재사용하고, 현재 native membership에9,835개 기존 확인점과648개 새 확인점을 다시 연결했다. 새 source21은 **462,855행 중256,485행**이 적격이다. 진행 중 설명의452,855행은 합산 오기이며 이 manifest/행수 대조가 최종 값이다. 새3개만 root/hold/특징을 계산했으며 전체 역사 가격 경로를 다시 재생하지 않았다. [manifest](../../tmp/main-machine-cumulative-dual-track-research-20261022/manifest.json), [원천 범위](../../tmp/main-machine-cumulative-dual-track-research-20261022/source-coverage.json).

10/21 NXT PRE14,314행은 미증명으로 제외됐다. SOR REGULAR388,468행 중196,412행은10:56:59.186~15:20:00.083, AFTER60,073행은15:30:01.382~19:59:59.983에 적격이다. 원10/19·20 결손과10/21 장 초반 결손은 복구·기회0으로 바꾸지 않았다. 진행 중10/22 원천은 이번 비교에 넣지 않았다. 실제 수집된 종목과 증명된 구간 밖의 시장 전체 포착률을 주장하지 않는다.

A17~28을 재사용하고 F35~38을 새 outcome 계산 전에 동결했다. source20까지의 선택을 먼저 고정한 뒤 source21에 적용한 날짜 분리 비교와 source21까지 합친 누적 재탐색을 분리했다. 현재 parent 자체가 source21을 사용했으므로 날짜 분리 비교도 독립 holdout이라 부르지 않는다. 시장 맥락은07:58:09의 기존 로그 `하락장(20일선 breadth 19.9%)`로 확인했다. 이 분류는 종목 session return이나 당일 지수 하락률과 다르며 장후 시장 요약을 진입 특징에 넣지 않았다.

### 약세장 맥락에서의 미포착 상승

기존 ENTER_NOW/A 밖에서도 매5초 구간의 첫 적격 실제 ask를 미래 outcome과 무관하게 추출했다. 기존 비용0.0023·30분·net 목표+0.4%·stop−3%의 연속 tick 라벨을 적용한32,104개 grid 중 W2,650/STOP7/TIMEOUT19,253/U10,194였다. WIN의 entry→target이 겹치지 않게 시간순으로 정리한 **78개 상승 창**을 진단 분모로 삼았다. 이는 사후 관측된 가격 창이며78개 실제 거래나 시장 전체 기회를 뜻하지 않는다. [가격 창과 실제 key/ask/시각](../../tmp/main-machine-cumulative-dual-track-research-20261022/missed-opportunities.json).

| 관측 분모 | 상승 창 | 현재 native 포착 | 현재 미포착 |
|---|---:|---:|---:|
| 고정 감시 | 26 | 4 | 22 |
| 비상시감시 | 52 | 3 | 49 |
| 합계 | 78 | 7 | 71 |

현재 native WIN의 target이 그 창 안에 있으면 창 이전에 이미 발생한 확인도 포착으로 인정했다. 기존 A 전체와 현재 정책을 합치면14개 창을 포착하고64개는 둘 다 포착하지 못한다. 따라서 관측한 하락장 맥락의 적격 경로에도 상승이 있었으며 현재 패턴 재생이 포괄하지 못한 기회가 확인된다. 실제 Main 감시 편입·기계판정 소비·AI·submit receipt를 전수 연결한 것은 아니므로 실제 미제출 주문이나 실현수익 손실로 단정하지 않는다.

78개 창의 시작 quote age는 모두 알려져 있고700ms 이하였다. 이는 이후 AI/Main 전달·제출 직전 quote 적격 증명이 아니다. 현재 미포착71개 중34개는 창 시작의60초 특징,50개는180초 특징이 미확정이었다. 기존 A도 포착하지 못한64개에서는 각각34/49개다. 이 분류는 서로 겹치며 창 전체가 계속 warmup이었다는 결론이 아니다. 초기 관측 준비성·패턴 정의·확인 시점의 공백을 구분해야 한다.

| 실제 관측 사례 | 창 시작 ask | 목표 도달 관측 가격·시각 | 판정 범위 |
|---|---:|---|---|
| 알테오젠196170,10:59:00.083 | 238,500 | 240,500,11:14:25.083 | 현재 미포착, 기존 A가 포착 가능한 창 |
| 주성036930,11:16:31.482 | 205,000 | 206,500,11:22:30.982 | 현재/기존 A 모두 미포착 |
| 삼성005930,11:35:45.085 | 225,000 | 226,500,11:56:03.683 | 현재/기존 A 모두 미포착 |

세 사례는 독립 선형 라벨과 source key/ask로 재검증했다. [사례별 root·hold·gate 추적](../../tmp/main-machine-cumulative-dual-track-research-20261022/interpretation.json)에 실패 조건을 공개했다. 주성/삼성의 관측 spread 약0.244%/0.222%는 여러 A의0.08~0.10% 연구 필터보다 컸다. root 부재·가격 hold 취소·수익률/낙폭/거래량 조건도 함께 작용했다. 관측 호가 간격을 공식 tick 규정이라고 주장하거나 spread 하나를 전체 원인으로 확정하지 않는다.

### 현재 parent 대비 누적 A/F 비교

baseline의 확정 분모가 있는28개 scope를 비교한다. 다른5개는 baseline 미정 진단으로 남겨 상대 개선을 만들지 않았다. 각 scope의 비율을 우선해 선택한 결과의 합계이며 전역 합계 비율 최적화가 아니다. [검토 완료 비교](../../tmp/main-machine-cumulative-dual-track-research-20261022/interpretation.json).

| 비교 | W | STOP | TIMEOUT | U | 확정 분모 | 선도달 비율 | 서로 다른 목표 시각 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 현재 | 1,931 | 303 | 568 | 7,757 | 2,802 | 68.92% | 255 |
| 추가 포착 A | 1,951 | 303 | 569 | 7,768 | 2,823 | 69.11% | 259 |
| 실패 감소 F | 1,400 | 33 | 267 | 7,128 | 1,700 | 82.35% | 173 |
| 비율 우선 결합 | 1,420 | 33 | 268 | 7,139 | 1,721 | 82.51% | 177 |
| 기회 확대 대안 | 1,982 | 302 | 574 | 7,993 | 2,858 | 69.35% | 261 |

비율 우선 결합은 W531/STOP270/TIMEOUT301/U629를 제거하고 W20/TIMEOUT1/U11을 더했다. W는 순511개 줄고 목표 시각4개를 새로 얻지만82개를 잃는다. 기회 확대안은 W52/TIMEOUT64/U275를 추가하고 W1/STOP1/TIMEOUT58/U39를 제거했다. W 순+51, 새로운 목표 시각7개/상실1개다. 원래 승리를 무조건 보존하는 새 gate를 추가하지 않았고 실제 손익을 만들지 않았다.

F35는 비상시감시 AFTER 저가, F38은 주성 REGULAR 고가와 삼성 AFTER에서 비율 우선안에 선택됐다. F36/F37은 선택되지 않았고 새 F35~38은 기회 확대안에는 선택되지 않았다. 이번 유한 탐색은 각 누적/날짜분리 선택마다2,297,856개 조합을 비교했다. source21 날짜 분리에서는 현재118/297(39.73%), A128/342(37.43%), F117/292(40.07%), 결합127/337(37.69%)이었다. 후행 날짜에서 W가 늘어도 비율이 악화되는 반례를 숨기지 않는다. [날짜별 비교](../../tmp/main-machine-cumulative-dual-track-research-20261022/comparisons.json).

### 후발 spread 단일 조건 대조

위 반례를 본 뒤 A18/A19/A22/A27의 연구용 spread 조건만 제거한 A29~32를 별도 동결했다. actual ask·비용 라벨·source/quote/hold·나머지 조건은 유지했다. 이 후발 탐색은 source21만 대상으로 하며 독립 검증이 아니다. [대조 정의](../../tmp/main-machine-cumulative-dual-track-research-20261022/spread-ablation-freeze.json), [원 결과](../../tmp/main-machine-cumulative-dual-track-research-20261022/spread-ablation-result.json), [동일 parent를 맞춘 해석](../../tmp/main-machine-cumulative-dual-track-research-20261022/spread-ablation-review.json).

현재+기존 네 parent는 W139/TIMEOUT412/U64,139/551=25.23%이며 spread 제거 후에는 W140/TIMEOUT464/U98,140/604=23.18%다. 추가87개 확인점은 W1/TIMEOUT52/U34이고 목표 시각16개와 상승 창11개는 그대로다. 현재7→대조11개를 spread 제거의 효과로 잘못 읽지 않는다. 기존 네 parent도 이미11개를 포착했다. **spread 조건만 삭제하는 방향은 이번 개선안으로 선택하지 않는다.** 초기 특징 결손과 약세 반등의 root/hold/확인 시점이 후속 가설의 핵심이다. TIMEOUT은 실제 금전 손실이 아니다.

### 자체 검토·보완·완료 범위

첫 비교에서 `(day,item,epoch,sequence)`만 사용해 동일 epoch의 정규장/AFTER sequence498을 합치는 결함을 발견했다. 알테오젠 AFTER의 current TIMEOUT1개가 REGULAR의 비current 확인점에 가려졌다. 첫 결과와 코드·75개 point/native bytes를 [원 시도](../../tmp/main-machine-cumulative-dual-track-research-20261022/attempts/session-key-v1/preservation-map.json)에 보존했다. 기존 분석 writer/consumer의 identity를 session까지 포함하도록 수리하고 실제 writer→global consumer 회귀를 추가했다. 완료된 point의 key만 bounded migration했으며 가격/특징/라벨은 다시 계산하지 않았다. 모든 scope의 선택 정의와78개 창의 포착 결과가 그대로임을 확인했다. 최종 current는1,931/2,802, source21은118/297이다.

표적 회귀39개 PASS. 원 신호 UNKNOWN 보존·조건부 regime·OR·prefix/source break·hold/라벨 계약, 세션 key 재사용의 writer/consumer 음성을 포함한다. 주성 완전 경로3,269행·native 확인7개에서 현재 코드와 projection 불일치0, 독립 grid 라벨20개·추가 대조20개·사례3개와 원천/코드468개 봉인을 검증했다. 새3개 계산 elapsed 합34.84초/최대RSS420,040KiB, 후발 대조45.84초/최대RSS541,400KiB다. 각각2GiB/CPU480초/wall600초 한도를 유지했다. 초기 pytest 동명 파일 수집 오류는 importlib 수집 방식으로 고쳤으며 최종39개 모두 실행했다. [최종 회귀](../../tmp/main-machine-cumulative-dual-track-research-20261022/final-tests.log), [검증](../../tmp/main-machine-cumulative-dual-track-research-20261022/validation.json).

교체·제거: 이전4필드 전역 비교 identity는 `removed`/session 포함5필드로 `replaced`다. immutable native projection의4필드 reader와 과거 봉인 연구·등록 정의는 해당 과거 증빙의 현재 소비자가 있어 `retained`다. 새 point writer는 항상 세션을 결속하며 별도 runtime 호환 wrapper를 추가하지 않았다. 기존 feature/root/hold/label/metric owner를 직접 재사용했다. 새 임시 제어가 필요한 이유는 과거 연구 코드 hash를 현재 정책이 소비해 수정할 수 없기 때문이다. 일회성 migration은 원 실패 재현/검토 증거로만 `retained`이며 active worker/스케줄/등록은 없다. production source/test/entrypoint 변경0, runtime 제거 보류0이다. 동시 작업의 AGENTS·checklist·runbook·다른 audit는 보존했다.

연구 실행과 방향 갱신은 완료했다. 코드 등록·정책 선택/발행·배포/재기동·provider·실주문은 실행하지 않았다. 연구의 missed window·W·비율은 실제 주문·체결·비용 후 경제성이나 독립 미래 검증이 아니다. source21을 사용한 현재 parent와 누적 탐색을 운영 승인으로 전용하지 않는다. 기존 정책 반영 owner가 같은 definition/field/scope·UNKNOWN·현재 source·정확 가격/native parity와 family 계약으로 이 결과를 소비할 수 있도록 원 결과·한계·반례를 보존했다.

최종 문서·경계 검증: 링크43개·Python compile·`git diff --check`·print-only parser PASS, 현재 selector/정책 pointer/PID3247910/start29788309와 cwd 불변이다. 기준609cdcf 대비 production source/tests +0/-0, 임시 non-test 분석4파일 +534/-0, 임시 회귀1파일 +52/-0, 소유 문서2파일 +88/-0이다. 이동0이며 분석 순증은 현재 parent 재결속·세션 identity 수리/유한 migration·독립 가격 창·후발 단일 조건 대조에 필요하다. 새 runtime owner/branch/entrypoint·스케줄0이고 외부 sync는 실행하지 않았다. [완료 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/completion-checks.json).

## 미포착64개 인과 분리와 반등 가설 — 2026-10-22

이번 추가 지시는 원래64개 상승 창의 초기 특징 결손과 패턴 조건을 나눠 분석하고, 안전기준을 유지한 새 패턴을 실제 연구하는 것이다. 이전78개 창·64개 반례의 identity와 라벨을 그대로 유지했다. 아래의 “미포착”은 **같은 창에서 성공한 목표 도달 부재**이며 기존 신호 자체가 없었다는 뜻이 아니다. 기계의 offline 가격 CF와 실제 Main 감시·AI·submit·체결은 별개다. [동결 정의](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/freeze.json), [전체64개 인과·비교 결과](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/result.json).

### 관측 입력과 패턴 조건의 분리

각 창의 시작부터 목표까지 기존 A17~28별로 root와 확인 필터에 필요한 입력의 유한/UNKNOWN 여부를 추적했다. 아래 “준비”는 **최소 한 기존 A의 필요한 입력을 모두 관측함**을 뜻하며 모든 A가 준비되거나 조건이 TRUE라는 뜻이 아니다. 세 범주는 서로 겹치지 않는다. 준비된 시점에도 root 발생·가격 hold·필터·동일 창 목표 도달은 별도 조건이다.

| 준비성에 따른 진단 | 창 수 | 고정 감시 | 비상시감시 | REGULAR / AFTER |
|---|---:|---:|---:|---:|
| 목표까지 어떤 기존 A도 입력을 모두 갖추지 못함 | 41 | 1 | 40 | 27 / 14 |
| 시작에는 미준비, 목표 전에 일부 A 입력 준비 | 4 | 1 | 3 | 2 / 2 |
| 시작부터 일부 A 입력 준비, 성공 포착 없음 | 19 | 13 | 6 | 16 / 3 |
| 합계 | 64 | 15 | 49 | 45 / 19 |

41개 중39개는 목표에 도달했을 때도 연속 관측 길이가120초 미만이었다. 기존 A17~28은 각각180초 특징 또는120초 거래량/돌파 이력 등을 요구하므로 이 입력 결손이 실제 경로에서 확인된다. 나머지025560/219750 AFTER는 각각134.494초·127.800초였지만 관측이7틱·3틱뿐이었다. `buy10`·구조·거래량 비교 구간이 미확정이었고180초 특징도 없었다. 시간 경과만으로 모든 특징이 생기지 않는다. [목표 시점의 분기별 결손과 exact key](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/validation.json).

시작의 ret180 미확정49개를49개의 단독 원인으로 부르지 않는다. 이 중4개는 다른 기존 A를 이미 계산할 수 있었고, 나머지45개는 위41+4개다. 전체64개의 관측 구간 시작은 최초 수집 행50개·적격 제외 행 이후 경계14개였다. 적격 제외 경계의 원 실패·원천 품질을 복구된 것으로 바꾸지 않았다. 최초 수집 행만으로 감시 편입 지연·수집 누락·생산자 버그 중 하나를 확정할 수 없다. 기존 source21의 미증명 장 초반과10/19·20 결손은 여전히 제외/null이며 이 표의0건으로 대체하지 않는다.

입력이 준비된19개는 모두 창 안에서 적어도 한 branch의 가격 hold 취소와 알려진 FALSE 필터를 보였다. 도중 준비된4개도 모두 hold 취소를 보였고3개는 FALSE 필터를 보였다. 전체64개에서는 root가 전혀 없는 창6개, 가격 hold 취소가 있는 창45개, 알려진 FALSE 필터가 있는 창42개였다. 이 세 값은 **중복 진단**이며64개를 다시 독점 귀속한 수가 아니다. spread 실패23창·buy10 실패24창·60초 상한 실패26창·VWAP 실패21창·거래량 실패17창 등이 겹쳤다. 단일 조건이나 UNKNOWN 하나가 전체 미포착의 유일 원인이라고 단정하지 않는다. 실제 root·hold·개별 필터별 횟수와 UNKNOWN은 위 원 결과에 보존했다.

기존 A 확인점은5개 창에20개 있었다. 삼성 두 창의 WIN8개는 원 창보다 늦은 목표였고, 삼성 다른 한 창10개는 U, 주성 두 창 각1개는 TIMEOUT이었다. 따라서 이5개는 “신호 없음” 대신 “시점/목표 가격 또는 미확정 outcome 차이”도 원인이다. 과거 `no_current_or_researched_addition_confirmation` 값은 원78개 분모의 identity 보존용으로 유지하지만 이번 해석에서는 성공 포착 부재로 명시했다. 원 자료를 개명·덮어써 과거 비교를 바꾸지 않았다.

### 새30~60초 반등 정의와 전체 경로 대조

새 A33~38은 결과 계산 전에 동결했다. 긴 특징을0·TRUE로 채우는 대신 자기 정의의 짧은 관측 구간을 온전히 요구한다. 종목 `session` 부호는 시장 지수 regime가 아니다. 기존07:58 하락장 breadth 기록은 연구 맥락이며 미래 시장 요약은 진입 특징에 넣지 않았다.

| ID | root·hold | 실제 prefix 확인 조건 요약 |
|---|---|---|
| A33 | 첫 미세 반전·1초 | 30초 수익률≥0, 저점 대비 회복≥0.05%, 30초 VWAP 이상, 매수10틱≥50% |
| A34 | 첫 미세 반전·3초 | 종목 session≤0, 30초 수익률≥0·회복≥0.1%·고점 대비 낙폭≤0.8%, 30초 VWAP 이상, 매수≥60% |
| A35 | 직전30초 고점 돌파·1초 | 30초 수익률0~0.3%, 30초 VWAP 이상, 매수≥60% |
| A36 | 30초 VWAP 회복·3초 | 종목 session≤0, 30초 수익률0~0.2% 미만, 현30초/이전30초 거래량≥1, 매수≥60% |
| A37 | 첫 미세 반전·1초 | 종목 session≤0, 60초 수익률≥0·VWAP 이상, 30초 회복≥0.1%, 매수≥60% |
| A38 | 직전30초 고점 돌파·3초 | 종목 session>0, 30초 수익률0.03~0.3%, 60초 VWAP 이상, 현30초/이전30초 거래량≥1, 매수≥60% |

모두 root/확인 시 동일 `_AL` item·적격 epoch/sequence·알려진 quote age 및 기존 연구 상한5,000ms·spread≤0.10%를 요구했다. UNKNOWN→TRUE는 새 돌파/VWAP 전환이 아니며 hold 중 가격이 root보다 낮아지면 취소했다. 실제 ask·비용0.0023·net 목표+0.4%·softstop−3%·30분 라벨, 완료 동일 item 분봉의 검열 계약을 유지했다. 이 연구 quote 상한은 AI/제출의 더 엄격한 freshness·출처·안전 재검증을 승인하지 않는다. 운영 guard/정책은 바꾸지 않았다.

결과가 아닌 날짜·적격성으로 고른 이전 최신 SOR REGULAR10/08(39번)·AFTER10/15(53번), source21 AFTER73번·REGULAR74번의4개 파티션만 계산했다. **1,076,781행 중806,597행 적격**이며 이전2개는 제한된 부정 대조군이다. 10/21의 WIN 창만 계산하지 않고 해당 두 session의 모든 적격 종목·전체 가격 경로를 사용했다. 각 scope의64개 OR 조합을 이전 대조군으로 선택한 정의는10/21에 그대로 적용했다. source21을 본 가설 방향·현재 parent이므로 이 비교도 독립 holdout은 아니다.

| 10/21 비교 | W | STOP | TIMEOUT | U | W / 확정 분모 | 78개 창 포착 | 원64개 순추가 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 현재 native | 118 | 0 | 179 | 30 | 118/297 = 39.73% | 7 | 0 |
| 현재+기존 A 전체 | 160 | 0 | 507 | 103 | 160/667 = 23.99% | 14 | 0 |
| 현재+A33 | 126 | 0 | 251 | 191 | 126/377 = 33.42% | 13 | 4 |
| 현재+A34 | 122 | 0 | 201 | 53 | 122/323 = 37.77% | 10 | 1 |
| 현재+A37 | 123 | 0 | 213 | 59 | 123/336 = 36.61% | 11 | 2 |
| 현재+새6개 전체 | 130 | 0 | 272 | 238 | 130/402 = 32.34% | 13 | 4 |
| 현재+기존 A+새6개 | 172 | 0 | 592 | 304 | 172/764 = 22.51% | 18 | 4 |

A35/A36/A38은 원64개 추가 포착0, 새 W도0이었다. A33의4개가 모든 새 포착을 포함하며 A34/A37의 포착을 독립 기회로 더하지 않는다. 새6개를 현재에 합치면 W+12/TIMEOUT+93/U+208이고, **기존 A 전체를 이미 합친 기준에서는 W+12/TIMEOUT+85/U+201**이다. 원64개 중60개는 여전히 미포착이다. U는 손실·실패0·TIMEOUT이 아니며 TIMEOUT도 실제 금전 손실이 아니다.

| A33이 추가 포착한 원 창 | 창 시작→원 목표 | A33 확인 ask·시각→그 ask의 목표 | 입력 분류 |
|---|---|---|---|
| 삼성005930 | 13:04:50.182→13:24:57.698 | 220,000·13:17:02.082→13:20:14.084 | 시작부터 일부 A 준비 |
| 삼성005930 | 14:11:20.086→14:18:07.286 | 220,500·14:12:35.582→14:18:07.286 | 초기 결손 후 준비; 확인 때 ret180은 여전히 UNKNOWN |
| 삼성005930 | 14:38:40.086→15:01:21.582 | 221,000·14:41:53.182→15:01:21.582 | 시작부터 일부 A 준비 |
| 비상시감시127120 | 14:56:56.783→14:57:15.084 | 18,700·14:57:15.084→14:57:15.084 | 목표까지 기존 A 입력 미준비 |

마지막 사례는 서로 다른 native sequence가 같은 밀리초에 기록됐다. entry 뒤의 틱만 사용하는 독립 선형 라벨도 WIN이지만 실제 실행 시간을 가정할 수 없다. 동일 시각 경계 사례를 제외한 보수적 진단에서는 원64개 추가 포착은3개다. 앞선3개도 실제 주문/체결 가능성의 증명은 아니다. 삼성13:04 창처럼 다른 실제 ask에서 목표가 먼저 온 경우는 그 ask의 비용 라벨이며 원 창의 시작 ask를 바꾼 결과가 아니다.

전체 합계의 악화만으로 모든 scope를 탈락시키지는 않았다. [scope별 비교](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/scope-comparisons.json)에서 삼성 AFTER는 현재106/271(39.11%)→새6개108/274(39.42%)이고, HPSP REGULAR는4/4→A34의5/5지만 같은 목표 시각1개다. 반면 원64개를 되찾은 삼성 REGULAR와 비상시감시 REGULAR 저가는 현재 확정 분모가0이라 상대 비율 개선을 만들 수 없다. 삼성 REGULAR A33은 W6/TIMEOUT6/U8, 비상시감시 저가 A33은 W1/U30이다. 한 W나 같은 시각 다중 확인을 독립 반복 성과로 해석하지 않는다.

이전 두 대조군에서는 현재437/502(87.05%)→새6개509/823(61.85%), 추가 W72/STOP2/TIMEOUT247/U906이었다. scope별 이전 선택은 비상시감시 AFTER 저가에만 조합을 골랐고, source21에서는 새 W0/TIMEOUT0/U9·원64개 추가 포착0이었다. 그 밖은 current였다. 따라서 **여섯 패턴을 전역 추가하는 안은 선택하지 않는다.** A33은 짧은 반등·확인 시점 공백을 실제로 메운 탐색 후보로 보존하되, 현재 결과를 운영 승격이나 독립 미래 성과로 전용하지 않는다. 원64개의 대부분은 비상시감시의 관측 준비성 문제이며 단순 hold 축소나 spread 삭제만으로 해소되지 않는다.

### 검토·보완·검증과 적용 경계

검토 중 같은 timestamp의 첫 행을 창 시작으로 잘못 고를 가능성을 발견해 native epoch/sequence exact identity로 찾도록 고쳤고 동시각 회귀를 추가했다. 새 패턴의 root/확인 모두에서 미확정 age·경로 불일치·spread 초과를 차단했고 비유한 수량을 새 VWAP/거래량에서 UNKNOWN으로 유지했다. 경계·누락·hold·prefix·기존 A·날짜/session identity 회귀 및 독립44개 tick 라벨/ask/key 검증을 수행했다. 별도 검증 도구의 첫 fixed-universe 참조 오류는 기존 `C.group` 소유자를 사용하도록 고쳤으며 분석 worker의 숫자는 바꾸지 않았다. 동결된 과거 helper의 importlib 로딩은 일부가 sys.modules에 없으므로 전이 참조를 추적해 기존 봉인과 대조했다. 기존 봉인이 없는5개 helper는 freeze 이전 mtime와 이번 hash를 별도 기록한 **후발 코드 봉인**이며 사전 봉인으로 주장하지 않는다. 테스트의 infinity 입력은 normalized 계약 밖의 과거 불변 helper 경고를 명시적으로 검증하고 새 특징은 UNKNOWN을 유지했다.

4개 worker는 순차 nice19·2GiB/CPU480초/wall600초 이내, elapsed 합89.43초·최대RSS452,184KiB였다. 과거75개 전체를 재생하거나 예산·TTL을 확대하지 않았다. 검증은 별도 bounded source/독립 라벨/두 희소 사례 대조였으며 경제 보고서나 provider를 재생성하지 않았다.

교체·제거: 이전 봉인 A/F·feature/root/hold/label/metric은 과거 정책 증빙과 이번 대조의 소비자가 있어 `retained`다. 새로운30초 특징/원64개 분류/새6개 offline 정의는 [기존 임시 연구의 하위 실행](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/research.py)에만 추가했다. 기존 hash-bound 연구를 수정할 수 없어 새 실험을 그 소유자의 하위 디렉터리에 두었다. 별도 production 모듈·wrapper·등록·자동 스케줄을 만들지 않았다. 기존64개를 “무신호”로 해석하는 설명은 이번 결과로 `consolidated`했으며 원 artifact identity는 `retained`다. production source/test 대체·삭제 대상0, runtime 제거 보류0이다.

연구 기준은 원e9ee2c8ea 코드·기계 bundle e815509b다. 실행 시작 snapshot에는 병행된9476e9ecd selector 전환과 원PID 보존 상태가 포함됐고, 실행 중 새PID3535467/start30205342의 native receipt를 관측했다. 연구가 배포/재기동한 것이 아니며 selector 불변을 주장하지 않는다. 새 선택 release의 이번 import된 runtime 코드38개 SHA는 모두 동일하고 기계 pointer bytes도 그대로였다. [동시 전환과 코드 parity](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/runtime-parity.json). 새 PID의 자연 판정·제출·실현 경제성은 이 연구의 완료 증거가 아니다. 운영 후보 등록·정책 발행·배포/재기동·provider·주문은 이번 작업에서 실행하지 않았다.

마지막 검증 중 별도bf26ddf0e selector 전환(`drained_awaiting_verified_start`, actual PID receipt 부재)도 관측했다. optional receipt가 없는 중간 세대를 완료 PID로 간주하지 않고 원 snapshot을 보존했다. 그 작업의 기동/최종 소비를 이 연구가 확인·복구한 것으로 주장하지 않는다. 정책 pointer 동일성과 연구 원천/코드·문서 검증만 연구 완료 범위로 삼았다.

최종 재검토: 표적 회귀71개 PASS·독립 라벨44개 일치·Python compile·문서 링크52개·`git diff --check`·print-only parser PASS다. 이번 요청 시작609cdcf 기준 production source/tests +0/-0, 임시 non-test 분석2파일 +390/-0·회귀1파일 +93/-0, 소유 문서2파일 +91/-0, 이동0이다. 순증은 봉인된 과거 연구를 건드리지 않고64개 전체 인과와 새 짧은 특징을 계산·반증하는 데 필요했다. 새 runtime branch/entrypoint·wrapper·등록·스케줄0, 외부 sync0이다. 문서 밖 별도 일정/OPEN owner를 만들지 않았다. [완료 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/completion-checks.json).

## 41개 입력 미준비의 실제 등록·수집·소비 추적 — 2026-10-22

사용자 추가 지시는 정상 신규 편입과 수집·전달·특징 결함을 끝까지 구분하고 확인된 결함을 구현·검토·보완·회귀검증하는 것이다. 앞선41개는 **연구 가설 A17~28 중 어느 것도 필요한 입력을 모두 갖추지 못한 창**이다. 당시 실제 선택된 Main 패턴의 입력 실패41건이나 원천 유실41건을 뜻하지 않는다. 당시 실제 선택 정의의 요구는0/60/61/63초였고 연구 가설의120~180초와 달랐다. 이 구분을 하지 않은 “기계 입력 미준비” 해석은 이번 증거로 정정한다. 원41개 identity·원가격 outcome은 삭제하거나 덮어쓰지 않았다.

### 원천부터 최종 판정 영수증까지

기준 workspace609cdcf, 선택fc51a179b/PID3913010/start30436408, bundle e815509b를 고정하고 source21의23개 종목·41개 창을 조사했다. raw SOR REGULAR406,993,706bytes·AFTER63,521,481bytes와 pipeline2,103,614,940bytes에서 대상만 낮은 우선순위로 추출했다. 가격 원천 hash는 원 normalized의 원천 영수증과 일치했다. [추출 원천·offset·SHA](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/extraction.json), [41개 최종 연결](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/reviewed-result.json).

| 실제 등록·원천 경계 | 창 수 | 확인된 원인·범위 |
|---|---:|---|
| 신규 exact-item probe의 관측 창 | 39 | 22개 로컬 등록 중 해당 item/lease/transport epoch와 연결. 초기 연구 이력 부족과 실제 패턴/신선도 결과를 분리 |
| 목표가 로컬 probe 종료 뒤에 나온 창 | 1 | 025560 AFTER:17:27:42.688 시작,17:28:27~28 로컬 release,17:29:57.182 목표. 보존 가격 WIN은 유지하되 같은 등록이 소비할 실행 기회로 세지 않음 |
| 재기동 뒤 적격 epoch의 첫 고정 감시 창 | 1 | 034020 REGULAR:10:56:48 WS 초기화→10:56:59 우선 등록→10:56:59.186 첫0B/sequence1. 이전10:55:29.451의 다른 epoch는 원 close 증빙 결손으로 제외 |

40개 창은 정확히 하나의 local lease와 연결됐고35개 대상 pipeline 기록 중 같은 lease의 실제 결과가40개 창 모두에 연결됐다. 고정034020은 probe가 아닌 startup 우선 등록 경로였다. 290720은 동일 등록에서 실제 `assessed/ENTER_NOW` 영수증이 있었으며 창의 목표와 동일 시점의 성공 포착인지는 별개다. 원 “41개 연구 입력 미준비”를 실제 Main 전체 미판정으로 해석할 수 없다는 직접 반례다. connection REG 응답이나 local sent registry를 종목별 broker ACK로 바꾸지 않았다.

실제 영수증의 terminal 결과는 창별로 `pattern_not_matched`16, `observation_incomplete`20, `source_unavailable`3, `assessed`1, 과거 epoch 경계1이다. 같은 등록에 여러 창이 있으므로 독립 probe/거래41건이 아니다. 불완전20개는 `native_history_observed_current_source_stale`13개 창과039980의 `confirmation_pending_at_residence_end`7개 창이다. 앞선13개는 마지막 실제0B가 오래된 상태였고 pending7개는 원 기한 내 확인 미완료였다. 실제 소비 시각의 stale/UNKNOWN/hold를 그대로 유지했다.

raw→normalized의38,177행을 가격·수량·매수/매도 방향·quote·시각·item·두 namespace로 대조해 불일치0이었다. 22개 등록의 소비 시점까지4,117개 실제 틱에서 native sequence 단절0을 확인하고, 같은 틱을 이전/수정 준비성 reader와 함께 재생했다. 10/21 해당 collector epoch의0B callback/enqueued/worker/writer는 각각256,497건, queue drop·writer error·unexplained gap은0, raw reconciliation 완료였다. callback p95/p99는0.114106/0.130765ms였다. 수집·보존·전달 손실을 이41개의 원인으로 입증한 증거는 없었다. 첫0B의 등록 후 지연은0.059~88.179초였으며 등록 전 원천이나 broker 전체 송신 완전성을 추정하지 않는다.

새 등록의 짧은 prefix, 체결 희소성, 실제 패턴 조건, 원 기한 끝의 freshness/hold가 서로 다른 원인이다. raw의 후속 수신이 존재해도 local release 이후의 운영 소비 권한까지 증명하지 않는다. 025560의 가격 라벨을 수집 오류/수익0으로 고치거나 등록 시간을 늘려 WIN으로 만들지 않았다. 034020의 복구 불가능한 과거 epoch는 제외/null이며 현재 데이터를 소급 결속하지 않았다. 현재 close/consumer 계약이 이미 수리된 경로를 과거 결손만으로 다시 고치지 않았다.

### 확인된 첫 결함과 수리

**진단 reader 결함:** `reversal_source_diagnostics.branch_readiness`가 event quote fact인 `spread`를 trade rolling cache에서만 찾았다. native quote는 현재·동일 identity로 존재하고 detector는 FALSE인데도 prefix의 키 부재를 입력 결손으로 표시했다. 실제5개 등록의 최종 진단에서 확인했고 해당 등록에는 원20개 창이 연결된다. 이는20개의 주문 실패나 매 순간20개 입력 손실을 뜻하지 않는다. 특히127120 등은 실제 `pattern_not_matched`였고 spread가 미계산된 거래 신호가 아니었다.

격리 작업본 `/home/ubuntu/KORStockScan-worktrees/machine-input-trace-20261022`, 기준fc51a179b에서 기존 진단 owner만 고쳤다. [수리 patch](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/reviewed.patch), commit `e48ac8ef3` (`codex/machine-input-trace-20261022`). 정확한 current row·feature identity·현재 quote를 확인한 **prefix 표시에서만** 누락된 spread를 계산한다. registered/legacy는 기존 ask/bid 비율, manual/cumulative는 기존 trade 분모를 사용한다. 실제 confirmation의 명시적 UNKNOWN, producer의 기존 값, stale/invalid/crossed quote, 다른 identity/generation은 채우지 않는다. 원 cache·ready queue·coverage truth·신호는 수정하지 않는다. 입력이 계산 가능해도 조건 합격이나 매수 권한이 되지 않는다.

수리 전 실제 State→진단 reader 회귀2개 FAIL/음성7개 PASS를 보존했다. 수리 후 분모별 회귀·stale/missing/crossed/nonfinite·source invalid·prefix 불일치·명시적 UNKNOWN·다른 generation 음성11개를 포함해 **선택 release 기반201개 PASS**였다. 원41개에 대응하는22개 등록 재생에서도 두 reader의 detector truth/quote 적격과 state bytes가 같고 prefix 표시만 교정됐다. pipeline의 실제 `stock_code`와 stringified dict/`None` reader 회귀7개도 PASS였다.

workspace로 가져올 때 선택 release의 별도 fixture context가 달라 전체 patch가 적용되지 않는 것을 `--check`에서 확인했다. source hunk와 새 테스트 블록만 옮겨 병행 변경을 보존했고 workspace 관련162개 PASS로 다시 검증했다. 선택 release의 후속 `observe_snapshot(original_root=...)`·native quote receipt 변경을 이 수리로 제거하지 않았다. [선택 기준 회귀](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/final-tests.log), [workspace 회귀](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/workspace-fixed-tests.log). 기존 pandas_ta 의존성의 Pandas4Warning1개는 보존했고 warning을 숨기는 수정은 하지 않았다.

초기 임시 추출에서 pipeline의 `code`를 잘못 읽어0개가 추출된 시도도 보존했다. 실제 producer schema가 `stock_code`이고 nested field가 Python dict 문자열임을 확인해 수정했다. 가격 원천은 재독하지 않고 pipeline만 한 차례 추가 읽어35개를 정확 복원했으며 이후 분석은 추출본만 사용했다. 이 분석 도구 오류를 운영 데이터 결손으로 보고하지 않았다. 원 추출 시도와 zero-match 결과는 같은 디렉터리에 남겼다.

### 검토·교체·완료 경계

`branch_readiness`의 누락 키→입력 결손 경로는 같은 함수의 exact prefix quote projection으로 `consolidated`했다. 이전 실제 확인 원장·explicit UNKNOWN·rolling cache·lease parser·회귀 fixture는 현재 consumer와 원 증빙이 있어 `retained`다. 새 production 모듈/compatibility wrapper/dispatch/registry/스케줄0, 대체 후 남은 중복 구현0, 제거 보류0이다. immutable parent 연구는 hash 소비자가 있어 그대로 보존했고, 임시 source-trace는 기존 연구 하위에서 기존 lease parser·feature/label owner를 재사용한다.

코드 수정은 **production non-test1파일 +15/-0, 기존 test1파일 +59/-0**, 이동0이다. 순증은 branch별 기존 spread 의미를 보존하는 표시 교정과 실제 producer→reader 음성 회귀에 필요했다. 임시 분석171행·임시 회귀26행은 raw/normalized/lease/실제 terminal의 연결과 분석 도구 원 오류의 재발 방지를 담당한다. 계좌·프로토콜 parser·FID·REG/REMOVE/recovery·인증·요청·원 timeout·선택 패턴·실제 매수/매도·guard는 바꾸지 않았으므로 Kiwoom wire 변경 gate 대상 수정은 없다.

원인 분석과 source-only 코드 수리·검토·보완·회귀는 완료했다. 정상 준비 대기를 강제 TRUE로 만들지 않았고, 이 수정으로 원41개를 즉시 추가 매수한다고 주장하지 않는다. runtime 배포·재기동·실제 PID의 수정 코드 소비는 수행하지 않았으며 원천 회복·자연 주문·비용 후 경제성과 별개다. 추가 운영 적용은 기존 release routing/실제 소비 계약의 별도 범위다.

최종 compile·`git diff --check`·소유 문서 링크59개·print-only parser PASS다. 이번 요청의 소유 문서 수정은 audit44행·proposal2행 추가/삭제0이며 앞선 연구 기록과 다른 세션 변경을 보존했다. selectedfc51a179b·정책 pointer bytes 불변을 확인했고, 수정 코드의 실제 PID 소비를 주장하지 않는다. [최종 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/completion-checks.json).

## 배포 뒤 첫 자연 probe의 spread 표시 수용 — 2026-10-23

사용자의 배포·재기동 완료 통보 뒤, 첫 자연 probe와 실제 PID의 spread 표시를 관찰했다. 위10/22의 미배포 기록은 당시 상태로 보존한다. 이번 점검의 workspace 기준은609cdcf이며 현재 선택본은9a8e59bfc, 실제 Main은PID1134876/start35426396이다. `/proc` cwd는 선택 release의`src`와 일치하고 진단 owner SHA는검토본`bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee`와 같다. bundle1d9e5b09·family80648f36·execution manifest6b6eddd1의 native PID 소비 영수증은128/128 scope, legacy carry0이다.

**자연 수용 PASS:** 08:04:00.943967의 첫 결과456160은`observation_incomplete/confirmation_pending_at_residence_end`였다. 해당 scope는 spread 필수가 아니므로 이 첫 결과만으로 수리를 수용하지 않았다. 08:07:25까지의 같은 PID 결과8건을 보존하고, spread 필수6건의 exact item/lease/transport epoch/native sequence·feature identity·scope hash·family와 source0B를 대조했다. 08:09:41 재확인에서도 selector·정책 pointer·PID 소비 영수증 원 bytes와 PID/start/cwd가 같았다.

| 자연 표본 | 원천과 실제 PID의 대조 | 판정 |
|---|---|---|
| 304100, 08:05:30 | trade14270/bid14270/ask14280 → spread0.0700770847932726%, `missing_inputs=[]`, detector FALSE, 최종`pattern_not_matched` | 첫 적격 prefix의 오표시 해소 |
| 019170·108860·439090·249420 | 같은 native identity의 원천으로 계산한 spread와 실제 표시값의 차이 모두0, 해당 spread 분기의`missing_inputs=[]`, detector FALSE | 추가4건도 오표시 없음 |
| 114840, 08:05:02 | trade10940/bid10940/**ask=null**, spread=null, `spread/executable_quote` 미준비, detector UNKNOWN, 최종`required_feature_insufficient` | 실제 호가 결손의 정상 차단 유지 |

양성5건의 해당 spread 분기는 모두`prefix_context_no_confirmation`·`native_quote_usable=true`이며 trade 분모의 기존 산식`100*(ask-bid)/trade`와 정확히 일치한다. 원래 FALSE는 FALSE로 유지되고,019170·439090의 pending terminal도 유지됐다. 다른 분기의 관측 창 부족은 이 spread 수용으로 해소됐다고 하지 않는다. 114840은 current source여도 실행 호가가 없으므로 값을 만들지 않았다. 관찰8건에서 수리 대상 오표시 재발0이며, 이번 자연 수용의 범위는 **NXT PRE manual/cumulative trade 분모**다. 다른 route·registered/bid 분모의 자연 실행이나 이후 전수 무재발·주문·체결·비용 후 경제성을 입증한 것은 아니다. 기존 분모별·stale/UNKNOWN/identity/generation 회귀 결과는 위10/22 기록대로이며 이번에는 코드 결함 재발이 없어 재수리나 동일 trading suite 재실행을 하지 않았다.

[검증 assertion·실제 PID·첫 결과](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/verification.json), [실제8건 원문](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/probe-events-initial.jsonl), [6건 원천·offset·SHA·계산 대조](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/source-match.json). 원천은26,384,712bytes snapshot을 한 번만 읽고6개 exact row를 보존했다. pipeline은7,152,518bytes까지의 완결 JSONL 경계·inode/offset을 기록했다. 전체 일일 원천을 반복 scan/hash하거나 live probe/provider 호출로 표본을 만들지 않았다.

이번 변경은 기존 audit에 자연 소비 근거를 덧붙인 문서 수정뿐이다. production/test 변경0·이동0·신규 모듈/dispatch/스케줄0이며, 기존 진단 owner·producer·consumer·음성 회귀는 현재 소비와 수리 증빙 때문에`retained`다. 교체·제거·보류 대상은`none`이다. 정책·기한·source TTL·broker/hard safety·selector·runtime을 바꾸지 않았고 기존 checklist의 다른 장전/장후 Acceptance는 닫지 않는다. 첫 자연 probe와 해당 spread 표시 수용은 완료했으며, 새 현재 결손이나 오표시가 확인되면 같은 진단 owner와 이 연구 기록에서 원인을 추적한다.

## 프리마켓 전체 관찰과 정규장 SOR·registered/bid 자연 수용 — 2026-10-23

사용자 후속 지시로 프리마켓 기계판정과 정규장 SOR·registered/bid 자연 probe를 같은 PID에서 관찰한다. 기준 workspace609cdcf, 선택9a8e59bfc/PID1134876/start35426396·bundle1d9e5b09는 앞선 첫 자연 수용과 같다. 새 실행 항목은 오늘 체크리스트의`MachineSpreadNaturalAcceptance1023` 한 곳에 등록했고, 원 strict가 결속한91d9874a 체크리스트는 native historical archive의 정확한 SHA로 확인·보존했다. working 문서 수정으로 strict/controller/PREOPEN을 재봉인하지 않았다.

### 프리마켓 종료까지 확인한 결과

08:04:00.943967~08:40:47.342823의 자연 결과는 **19종목·97건**이며, 주문97건이나 독립 상승 기회97개가 아니다. 결과는`assessed/ENTER_NOW`4, `pattern_not_matched`26, `observation_incomplete`52, `required_feature_insufficient`4, `source_unavailable`11이다. ENTER_NOW4회는053800·439090 각1회와304100의2회다. 별도 고정감시도 평가하므로 probe 결과와 Main 전체의 제출 분모를 합치지 않았다.

고정감시를 포함한 Main의 보존된 제출 terminal10건은`main_entry_order_route_invalid`5, `latency_block`3, `pre_submit_liquidity_guard_block`2이며 해당 terminal의 broker 승인0이다. 병행 기존 owner의 전체 Main 분모는 ENTER_NOW17(상시13/비상시4)·AI raw PASS12/CAUTION5·실행 유효PASS10이며 같은 terminal10건으로 연결된다. legacy `ai_confirmed`13에는 CAUTION3이 포함되므로 승인 분모로 쓰지 않는다. 기계/AI 통과가 제출·체결이나 순익을 증명하지 않는다.

우리 초기 점검은 로그의`premarket_krx_like`와 guard의`krx_like_premarket` 차이를 의심했지만 실제 session producer는 후자를 만든다. 같은 실제 producer cohort와 정상 NXT 입력은 원 검사에서 통과하며, 진단 로그는 현재 판단의 별도 provenance로 덮인다. 이 가설을 확정 원인으로 삼아 producer/주문 guard를 수정하지 않았다. [초기 가설의 반증](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/route-hypothesis-check.json). 이후 확인한 병행 `MainEntrySourceTerminalRepair1022`/`DirectFamilyPreopenPolicyHandoff`의 수리 기록에서는 **명시 NXT를 candle/context에 전달하지 않아 전역 SOR 기본값이 소비된 최초 생산 결함**을 증명했다. 기존 caller의 전달 수리·2641회귀는 해당 owner의 격리 후보cbedebd1 기록이며 이번 관찰에서 재실행한 검증이 아니다. 실제 PID9a8에는 아직 미반영이고 native 인계/P5·배포·PID 수용은 같은 기존 owner에 남는다. [별도 원인·수리·운영 잔여](postclose-root-cause-recovery-review-2026-10-19.md#premarket-submission-route-and-native-policy-proof-repair-2026-10-23), [전체 Main 분모와 실제 첫 차단](../../tmp/submission-session-audit-20261023/report.md).

유효 호가의 spread 필수 분기61건은 모두 같은 PID/start와 readiness의 정확한`timestamp/epoch/sequence`에 결속되고 spread가 유한한 알려진 값이며 미준비 목록에 없었다. 호가를 쓸 수 없는19건은`executable_quote` 결손과 incomplete 표시를 유지했다. 나머지 결과를 이61건의 spread 양성 검증으로 세지 않는다. 최초5개 PRE 호가 산식의 exact raw 대조는 앞 절의`source-match.json`이며, 이번61건 전부의 raw 산식을 다시 읽어 재계산했다고 주장하지 않는다. [프리마켓 분모·판정·assertion](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/premarket-observation.json).

08:40 이후 pipeline 정지는 기존`SCALPING_BUY_WINDOWS=08:03~08:40,09:03~15:10,16:00~19:40`의 정상 탐색 종료였다. 08:42:51에도 NXT raw writer는 갱신됐고 Main PID/start/cwd는 유지됐다. 08:50 동시호가의 무수신·호가 age 증가를 장애로 덮거나 과거 quote를 fresh로 승격하지 않았다. 운영 시간창이나 WS 등록·재연결·Main을 변경하지 않았다.

### 정규장 자연 표본의 수용 조건

08:52의 초기 기록에서는 정규장 표본이 아직 미래 창이었다. 기존09:03 탐색 재개 뒤`other_non_fixed|REGULAR|LT_20000`·SOR·union_v6의`G4`를 관찰했다. G4는 등록 패턴이며 필수 spread의 분모가 bid인 현재 선택 정의다. optional spread나 PRE/trade 분모를 registered/bid 수용으로 바꾸지 않았다. [현재 선택 scope·hash·payload](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/regular-target.json).

자연 prefix의 item/lease/native epoch/sequence·feature identity·현재 quote·scope/registry/family·PID/root/start와 exact raw0B를 대사하고, `100*(ask/bid-1)`과 실제 표시값의 일치·spread 미준비 해소를 확인해야 완료한다. UNKNOWN/명시적 미확정·stale/교차/결손 quote·다른 generation을 채우지 않는 기존 안전계약은 유지한다. 전용 임시 관찰은 inode/offset·완결 JSONL 경계를 보존해 회차당 최대16MiB를 증분으로 읽는다. 표본용 provider/주문 호출이나 운영 producer의 중복 실행은 없다.

### 09:05 첫 정규장 결과와 실제 PID의 수용

09:03 자연 claim5건의 첫 결과는09:05:31에 나왔다. 그중065450·357880의 G4는`prefix_context_no_confirmation`·`native_quote_usable=true`였고 아래 exact raw0B와 결속됐다. 두 건 모두`feature_availability=complete`·`missing_inputs=[]`, detector/lifecycle FALSE·최종`pattern_not_matched`로 기존 조건 미충족을 유지했다. source censored0이며 관측은각149.815/149.161초로 원 기한 안에서 끝났다.

| 종목·현재 native sequence | 원천 trade / bid / ask | bid 분모 계산값 = PID spread (%) | 결과 |
|---|---|---|---|
| 065450_AL / 4138 | 4015 / 4015 / 4020 | 0.12453300124533051 | spread 미준비 없음·FALSE 유지 |
| 357880_AL / 2139 | 1923 / 1921 / 1924 | 0.1561686621551317 | spread 미준비 없음·FALSE 유지 |

두 건의 transport epoch는1792709745762419이며 서로 다른 exact lease를 유지했다. 357880은 trade와 bid가 달라 분모 구분까지 직접 검증한다. branch 정의2c39d400·registry2d94b2f9·scope89f13b38·family80648f36이 선택 정책과 같고, native receipt·source clock·readiness·feature·raw의 item/epoch/sequence와 timestamp가 일치했다. raw quote age는둘 다0ms, terminal0B age는94.862/200.251ms,0D age는184.526/77.03ms였다. local registration이나 connection REG 응답을 종목별 broker ACK로 바꾸지 않았다.

같은 배치019170의`actual_branch_confirmation`은 producer 확인값을 보존하는 별도 basis이므로 이번 prefix 교정의 양성2건에 넣지 않았다. 다른2건은 spread 필수 G4 scope가 아니었다. [최초 정규장5건 원문](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/first-regular-probe-events.jsonl), [두 prefix의 원천·offset·SHA·정확 계산](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/regular-source-match.json).

**정규장 SOR·registered/bid의 자연 표시 수용 PASS**다. 09:09:27에도 PID1134876/start35426396/cwd·선택9a8e59bfc·검토 진단 코드SHA가 일치하고, 원 selector·정책 pointer·128/128 native PID 소비 영수증 bytes가 같았다. 추출본뿐 아니라 pipeline/raw 원 파일의 해당 offset 행 SHA도 재대조했다. [최종 assertion·PID·정책·표본](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source-trace/natural-probe-20261023/regular-sor-registered/regular-verification.json). 정규장 raw30,707,891bytes에서16MiB tail을 한 번 읽어2행을 추출했으며 이후 검증은 추출본과 exact offset 행만 읽었다. 임시 관찰 process는 첫 적격 자연 결과를 확인하고 종료됐고 설치/cron/운영 dispatch를 만들지 않았다.

재발이 없어 이번 관찰의 production source/test 추가·삭제각0, 이동0·운영 교체/제거/보류 대상`none`이다. 기존 진단 producer/consumer·guard·회귀는 현재 소비와 원 수리 증빙 때문에`retained`다. source21의 원 동결 분석은 덮어쓰지 않고 같은 연구 하위에 날짜별 임시 증분 reader를 뒀다. 처음 offline assertion 명령의 괄호 SyntaxError는 실행 전 실패로 보존했고, 이를 고친 뒤 같은 추출본을 검증해 PASS했다. Main/정책/시간창/source TTL/등록/주문/하드 안전 변경0이며 동일 trading suite를 반복하지 않았다. 프리마켓 경로 전달 수리의 실제 운영 소비는 위 별도 기존 owner의 OPEN이며 이 spread 수용으로 해소됐다고 하지 않는다. 전체 시장·이후 전수 무재발·주문·경제성이나 기존 장전/장후 owner의 완료를 주장하지 않는다. 병행 세션의 체크리스트 갱신도 원문 그대로 보존하고 이번 항목만 완료했다.


## 정규장 점검과 source22 반등 후속 연구 — 2026-10-23

사용자 지시에 따라 AGENTS를 재로딩하고 Plan Rebase §1~§8·당일 checklist·장중 지시문의 현재 계약을 확인했다. `$korstockscan-review-gate`의 구현→검토→보완→재검토→검증을 적용했다. 이번 범위는 정규장 단회 점검·방향 갱신·실제 offline 연구이며 postclose heavy producer나 provider 연구를 중복 실행하지 않는다. baseline workspace609cdcf와 기존 dirty·병행 세션 변경을 보존했다.

### 현재 PID와 정규장 분모

다른 ordered 작업의10:14 selector 전환 중에는 actual PID receipt가 없었다. 이를 기동 실패나 현재 소비 완료로 단정하지 않았다.10:17:05 새926ebca82/PID1982231/start36273583, 실제 cwd와10:17:08 기계 bundle1d9e5b09/family80648f36의128/128 native 소비를 확인했다.10:34 재대사에서도 같은 PID/root/start와 소비가 유지됐다. 이 연구가 배포/재기동한 것은 아니다. 정책 cohort KRX·통합 `_AL` 원천·SOR 주문 경로이며 실제 체결 거래소는 미증명이다.

10:33경 native Sentinel source-window reader로 실제 actor birth10:16:27.830 이후를 검증했다. projection identity45,320bytes·indexed497,815bytes·raw append7,457,487bytes를 읽어43행/범위 complete를 확인했다. 이 complete는 등록된 source-window stage의 읽기 범위이며 Main 전체 action·경제 분모의 완전성은 아니다. 앞선 raw tail 두 구간 사이4,662,205bytes 공백은 원 receipt에 유지하며 이 인덱스 대사로 해당 stage의 현재 PID 범위를 확인했다. [현재 관측과 영수증](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/live/monitoring-result.json), [native source-window](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/live/native-source-window-receipt.json).

| 현재 PID의 자연 probe 결과 | 건수 | 해석 |
|---|---:|---|
| pattern_not_matched | 13 | native FALSE; ENTER_NOW로 승격하지 않음 |
| observation_incomplete | 9 | 마지막 현재 source stale; 과거 틱의 존재와 별개 |
| source_unavailable | 11 | route snapshot 부재8·0B age 초과3 |
| required_feature_insufficient | 2 | 478560의 첫 native tick/60초 이력 미확정,006280의 executable quote 결손 |
| ENTER_NOW | 0 | 이 probe 분모에서만0; Main 전체0의 근거로 전용하지 않음 |

해당 시점 새 PID의 Main 정식 trace는 없었다.08시 이후 보존 trace 중 정규장 exact attempt20개는 이전 PID의15 source_invalid+5 ENTER_NOW였다. source_invalid15개의 original capture를 전부 연결했고 path_changed9·input deadline1·preflight5를 확인했다. preflight5는 완료 봉/age/통합 원천 증명 결손3·input refresh 실패2이며 임의 복구하지 않았다. 이전1134876의 ENTER_NOW2개는 source 미평가,1785522의3개는 raw PASS 뒤 signal_expired_or_changed1·transport timeout1·CAUTION1이었다. 실행 유효 PASS는 이 trace 집합에서0이고 broker 제출 관측도0이나 전체 broker/체결 분모는 증명하지 않았다. 별도 무소속 trace1개는 이20개에 넣지 않았다. 과거 guard 결과를 현재 PID 재발이나 패턴 조건 실패로 합치지 않았다.

현재 PID의008830/005870/019170은 G4 registered/bid prefix 양성3건이다. 같은 item/native transport epoch/route sequence의 원천 bid/ask와100*(ask/bid−1)이 각각0.3571428571/0.1941747573/0.2288329519%로 표시와 차이0, missing spread0·FALSE 유지였다. 실제 confirmation의451760과 spread를 요구하지 않는028050은 prefix 교정 양성에 넣지 않았다. [원천 대조](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/live/spread-source-check.json). 처음 분석 assertion은 native microsecond와 직렬화 millisecond의 완전 일치·비필수 spread·양성 수4를 잘못 가정했다. 보존된 추출본에서 직렬화 구간과 실제 feature_fields를 적용해3건으로 바로잡았으며 운영 원천이나 코드를 고치지 않았다.

현재 관측 상태는 YELLOW다.10:30:32 정규 observer는 같은 actor에서 warning_pending/recorded_guard_or_cohort_pending이고 full coverage는 미증명이다.10:34:01 시장 원천은 BROAD_WEAKNESS, KOSPI−2.08%/KOSDAQ−2.80%다.09:15 market-opportunity census는 exact BBO 결속 부족·insufficient_evidence_scanner_recall이므로 시장 전체 기회 부재/탐색 정상의 증거가 아니다. 체크리스트 OPEN은 당시7개를 전수 분류했다: DirectFamilyPreopenPolicyHandoff는 전체 family 수용 미완료/overdue_unresolved, HoldingProfitExitSourceContractRepair는 기존 구현 owner running, 나머지 장후·명시NXT 수용5개는 not_yet_due다. 추가 연구 owner1개도 다음 종료 원천 대기/not_yet_due이며 다른 owner의 완료·권한을 바꾸지 않는다.

### 종료 source22의 전체 경로 재생

원64개/source21 후향 연구를 반복하지 않고 이미 종료·봉인된10/22 SOR 정규388,638행/383종목과 AFTER68,387행/83종목만 계산했다. 잘못된 item4/67행은 제외해 적격456,954행을 사용했다. native source/machine seal·records digest·현행 bundle membership·원 ask·동일 item/epoch/sequence와 완료 분봉을 결속했다. source22 native 확인점160/189개의 identity·ask·공통 라벨이 모두 일치했고 현재 selected State를 이용한 독립 종목 재생도196170의3개/005870의7개 확인점 불일치0이었다. 현행 parent 자체가 source22로 선택됐으므로 독립 holdout이라고 부르지 않는다. 당시 실제 정책의 주문 성과가 아니라 **현재 정책을 source22에 적용한 반사실**이다.

동결 A17~28/A33~38의 수치·root·hold·UNKNOWN을 유지했고 새 조합 탐색은 하지 않았다. actual ask·비용0.0023·net 목표+0.4%·stop−3%·30분과 동일 item의 봉인 완료 분봉 보조를 incumbent와 후보에 같이 적용했다. 신규 후보의 root/확인에는 기존 known quote age≤5,000ms·spread≤0.10%를 유지했으며 운영 AI/submit의 더 엄격한 freshness를 대체하지 않는다. 각5초 첫 적격 ask에서 시작한 WIN 경로는 item/epoch별 target까지 겹치지 않게 정리했다. 이355개 창은 감시 자료의 가격 진단 분모이며 시장 전체 기회나 독립 체결 수가 아니다.

| Session·비교 | W / STOP / TIMEOUT / U | 확정 목표 선도달 비율 | 관측 상승 창 포착 |
|---|---|---:|---:|
| REGULAR 현재 | 127 / 1 / 30 / 2 | 127/158=80.38% | 5/269 |
| REGULAR 현재+기존 A | 384 / 21 / 347 / 280 | 51.06% | 26/269 |
| REGULAR 현재+A33 | 404 / 31 / 362 / 346 | 50.69% | 40/269 |
| REGULAR 현재+새6개 | 548 / 47 / 544 / 495 | 48.11% | 43/269 |
| REGULAR 현재+기존 A+새6개 | 750 / 63 / 805 / 731 | 46.35% | 48/269 |
| AFTER 현재 | 82 / 13 / 21 / 73 | 82/116=70.69% | 23/86 |
| AFTER 현재+기존 A | 183 / 13 / 137 / 199 | 54.95% | 26/86 |
| AFTER 현재+A33 | 150 / 13 / 87 / 154 | 60.00% | 27/86 |
| AFTER 현재+새6개 | 170 / 13 / 113 / 180 | 57.43% | 27/86 |
| AFTER 현재+기존 A+새6개 | 243 / 13 / 202 / 285 | 53.06% | 28/86 |

현재 대비 새6개의 추가는 정규 W421/STOP46/TIMEOUT514/U493, AFTER W88/STOP0/TIMEOUT92/U107이며 제거0이다. 기존 A까지 포함한 기준에서 새6개의 순추가 창은 정규22·AFTER2다. W는 같은 상승의 여러 확인점을 포함하므로 포착 창 증가와 더하지 않는다. TIMEOUT은 금전 손실이 아니며 U를 실패/성공/0으로 채우지 않는다. scope별 숫자와 단일 A34~38의 악화도 [전체 결과](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/result.json)에 보존한다.

### 명확한 가격 기회와 남는 실행 한계

추가 대조에서는 original ask 이후 동일 item·연속 native source에서 age가 알려진 실제 bid가 비용 포함+0.4% 이상에 도달하고 그 전에 trade stop이 발생하지 않았는지 확인했다. 거래 가격 WIN355개 중185개(정규135·AFTER50)에서 이 더 강한 관측을 확인했다. 현재 포착이 없던 경우는 정규135·AFTER35개다. 새6개가 기존 A 기준보다 추가 포착한22/2개 중 original ask의 bid 목표까지 확인된 경우는10/2개다. 다른12개 정규 창의 bid 검증이 없다고 가격 WIN을 손실로 바꾸지 않았다. [독립 라벨·bid·당시 시장 상태 대조](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/validation.json).

| 같은 정의가 추가 포착한 사례 | 새 확인 ask → 후속 실제 bid | 확인 이후 소요 | 비용 가정 후 관측값 |
|---|---|---:|---:|
| 003010 REGULAR | 10:46:26.105의11,690 → 10:49:24.505의11,770 | 178.400초 | +0.4528% |
| 주성036930 REGULAR | 10:39:18.119의193,500 → 10:39:43.604의194,800 | 25.485초 | +0.4403% |
| 주성036930 REGULAR | 11:08:36.104의189,100 → 11:11:17.404의190,300 | 161.300초 | +0.4031% |
| 주성036930 AFTER | 18:07:49.627의184,900 → 18:19:58.628의186,100 | 729.001초 | +0.4175% |

앞선 정규장 사례들은 진입 전44~97초의 원 시장 기록과 결속돼 양 시장 약세를 확인했다. 정규 미포착 bid 검증135개 중 직전 기록은 BROAD70·SINGLE17·NEAR26·미기록22이며 기록 나이는4~238초다. AFTER35개는 마지막15:28 정규장 기록과49~240분 떨어져 있으므로 당시 AFTER 실시간 약세라고 단정하지 않는다. 미래 장마감 요약은 진입 특징에 쓰지 않았다. 비용0.23%는 설정된 반사실 비용이고 broker 실비가 아니며 depth/수량/queue·실제 체결·실현 PnL은 미증명/null이다. 명확한 관측 가격 상승과 실제 매수 가능성의 최종 증명은 다르다.

정규135개 중113개는 비상시감시, 나머지22개는 고정 감시다. 창 시작에 기존 A 입력을 모두 갖춘 정의가 없는 경우94개·일부 정의가 준비된 경우41개였고,77개는 목표 때도 연속 관측120초 미만이었다. AFTER35개는33개 비상시감시·2개 주성이며 시작 입력 미준비13/준비22개다. 이는 연구 A의 입력 기준이고 실제 선택 branch의 입력 결함 수가 아니다. 이 준비성·기간 진단끼리는 중복된다. 기존/새 A를 모두 합쳐도 bid 검증 미포착은 정규118·AFTER31개가 남았다. [입력·감시군 분리](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/interpretation.json).

### 판단·검토·후속 owner

전역 새6개 추가는 비율·STOP 악화로 미채택한다. 작은 탐색 후보는 A33 비상시감시 AFTER 저가 scope(50W/72확정69.44%→57W/80확정71.25%; 추가 W7/TIMEOUT1/U2), A35 주성 AFTER 고가 scope(4W/6확정66.67%→16W/21확정76.19%; 추가 W12/TIMEOUT3/U12)다. 이 범위도 source22를 본 작은 후향 결과이며 기존 누적·다른 날짜의 반례를 넘는 운영 후보라고 하지 않는다. 삼성 REGULAR에서 A33은79.20%→74.65%, 주성 REGULAR은새 STOP27을 더하므로 scope 혼합이나 승리만의 선택을 하지 않는다. source23 종료·봉인/native 계산 뒤 같은 정의로 날짜 분리/누적 비교할 owner는 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)이며10/26 07:40~08:00이다. 현재 단회 연구는 완료했고 후속 신규 원천 수용은 OPEN이다.

자체 검토에서 incumbent만 완료 분봉을 쓰면 비대칭이 되는 점을 계산 전에 보완해 모든 신규 후보에 같은 봉인 분봉을 적용했다. 이후 code pin·source SHA·349 native 확인점·State parity·독립 선형 라벨48개와 bid 음성 회귀를 확인했다. 정규/AFTER worker는 순차 nice19·각2GiB/CPU480초/wall600초 범위에서10.30/2.01초, 독립 검증은 별도 단회로 수행했다. 원천은 기존 압축 정규화2개만 읽었고 정상 과거75개 파티션을 재생하지 않았다. live I/O는 stat→최대16MiB tail·기존 검증 인덱스·작은 trace/capture에 한정했다.

교체·제거: 봉인 source21 연구·A/F·feature/root/hold/label은 현재 대조·역사 hash consumer가 있어 retained다. 신규 임시 하위 실행은 봉인 원본을 수정할 수 없어 그 아래 source22-review에 두었으며 기존 owners를 import했다. production module/wrapper/dispatch/등록/스케줄 추가0, 대체할 runtime 구현none·보류none이다. 과거 방향은 당시 증거로 retained하고 현재 방향은 proposal 맨 앞과 본 절로 consolidated했다. production non-test/tests 추가·삭제각0, 임시 분석287행·임시 회귀46행, 이동0이며 순증은 새 날짜·현행 membership·독립 bid/source 검증에 필요했다. provider/정책/TTL/guard/수량/주문/배포·재기동 변경0이다. 문서·parser·최종 compile/diff 결과는 같은 하위 실행의 completion-checks.json에 기록한다.

최종 재검토에서 pytest의 현재 작업 경로 때문에 workspace kernel이 먼저 import된 것을 명시적 module-origin 회귀가 검출했다(44 PASS/identity1 FAIL). 원 실패를 보존하고 selected release cwd·config/rootdir를 고정한 동일 회귀는 **45개 PASS**다. 계산 worker와 독립 검증의32개 code pin은 처음부터926ebca82의 native State/kernel을 사용했으므로 원천 재생을 반복하지 않았다. Python compile·문서162링크/anchor·현재 파싱 OPEN owner1개·print-only parser·git diff --check PASS이며 외부 sync는 실행하지 않았다. 본 요청의 문서는 proposal+12/−0·audit+71/−0·current checklist+5/−0, production source/tests+0/−0, 이동0이다. [완료 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/completion-checks.json).

## 정규장 미포착135개 실제 경로 추적 — 2026-10-23

**135개 전부를 실제 감시·판정 기록과 연결했다. 새 수집·전달 결함은 이 범위에서 확인되지 않았고, 과거 initial BUY 체결 투영 결함1개 창과 연구 reader 결함은 구분해 검증했다. 새 전역 패턴은 실패 증가로 미채택한다.** baseline609cdcf의 기존 dirty·병행 변경은 보존했다. 이번 사용자 지시는 인과 추적·offline 연구·확인된 결함의 source-only 수리이며 배포/재기동·정책/주문 권한이 아니다. 같은 review-gate로 구현→검토→보완→재검토→회귀를 수행했다.

### 원 분모와 실제 역사 정책

135개는 **현행1d9e5b09 정책을 종료 source22에 적용했을 때 미포착인 관측 상승 창**이다. 실제10/22에 기계판정이 한 번도 없었던135건이라는 뜻이 아니다. 원 day/item/collector epoch/sequence/session·ask·후속 bid와51종목을 그대로 동결했다. 실제10/22 PID 소비 원문은 모두 e815509b/family99008ee1이며,75e0fbbf7·90bf2d11f·70fc572f8·b1519a2d4의 해당 detector7개 파일 SHA는 연구 실행926ebca82와 일치했다. 현재 membership으로 과거 실제 판정을 덮어쓰지 않았다. REGULAR 정책 cohort KRX·통합 `_AL`·broker SOR이고 실제 KRX/NXT 체결 거래소는 미증명이다.

collector의 epoch/sequence와 실제 WebSocket/native epoch/sequence는 별도 namespace다. 실제 lease·item·WS epoch·native sequence·PID/start·scope·정책 영수증을 연결했다. 비상시감시113개 모두 창 시작에 정확한 local lease가 있었고 고정 감시22개도 운영 시간·Main 기록에 연결됐다. native State와 보존 source의257개 lease/84,832행은 count·연속 sequence 불일치0이다. 이는 **실제 State→보존 자료 범위의 정합성**이며 broker 상류 누락·시장 전체 recall의 완전성 증명은 아니다. [동결·원천 읽기 영수증](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/freeze.json), [전체 join](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/joined.json), [행 정합성](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/state-to-source-continuity.json).

| 실제 경로로 구분한 주원인 | 창 | 근거와 한계 |
|---|---:|---|
| Main 정규 진입09:03 전 목표 도달 | 4 | 운영 시간 제외; 감시 미등록 결함으로 바꾸지 않음 |
| 처음 probe의 local release 뒤 목표 도달 | 21 | 실제 lease가 가격 관측보다 일찍 종료; 후속 lease는 첫 소비 기회를 소급 연장하지 않음 |
| 관측 중 실제 root/패턴 조건의 알려진 FALSE | 100 | 비상시감시88+고정12; UNKNOWN도 함께 존재할 수 있음 |
| 목표 전 native root 자체가 없음 | 4 | 003010·069330 두 창·091580; 짧거나 드문 틱의 정상 입력 미확정도 공존 |
| 창 안에 실제 Main 기계판정이 이미 존재 | 3 | 주성1/HPSP2개 창; 이후 경로·AI 결과를 따로 추적 |
| native 신호가 claim 전 무효화되거나 목표 뒤 소비 | 2 | 주성의 실제 lifecycle·queue/claim clock으로 확인 |
| 과거 initial fill 투영 결함으로 BUY_ORDERED 잔류 | 1 | 주성11:07 창;09:19 실제 체결 이후 상태 결함,10/22 12:11 복구 확인 |
| 합계 | **135** | 원135 identity 보존, 중복 없는 주원인 분류 |

입력 미확정은 배타적인 주원인과 별도로 보존했다. 창 안 native UNKNOWN이 한 번이라도 있는 경우80개, 실제 root에서 missing 필터가 발생한 경우9개이며 서로 중복된다. 따라서100개를 “모든 입력이 완전한100개”라고 하지 않는다. 반대로 기존 A17~28의 연구 특징 미준비94개를 실제 선택 branch 결함94건으로 전용하지 않는다. 선택 predicate는 알려진 조건이 하나라도 FALSE면 다른 미확정이 있어도 FALSE다. native root 실패가 없는4개는 목표까지16/8/13/11틱, 연속 관측8.236/62.902/79.300/12.396초였다. UNKNOWN을 TRUE로 바꾸거나 긴 특징을 가짜로 채우지 않았다.

100개 조건 실패 창의 최근 root 진단에서 관측된 알려진 실패는 spread75·DD 상단61/하단58·structure49·session_trend48·ret_min26 등이며 **조건별 창 수는 중복**된다. G4는 종목 session UP·ret≥0.2%·FALLING 구조·0.2%≤DD<0.4%·spread≤0.1%를 동시에 요구한다. 시장 약세 중 반등 가격이 있다고 이 정의가 자동 충족되는 것은 아니다. 선택 G1/G2와 manual cumulative membership도 원 정책대로 유지했다. 최종 probe의 observation_incomplete/policy_unavailable를 창 전체 원인으로 역투영하지 않았다. ws_session_not_ready로 끝난3개 창도 같은 lease의 이전 native FALSE가 있었고 TRUE0이며, 새 수집 결손의 증거가 아니었다. [135개 최종 원인·각 probe·필터·입력 결손](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/causes-final.json).

### 기계 이후 경로와 확인된 과거 결함

실제 기계판정이 있던3개 창에는 ENTER_NOW4개와 source_invalid1개의 capture가 있었다. 주성09:13은 source 미평가 뒤 reversal_signal_path_changed, HPSP09:00~09:05는 경로 변경·first_ai_wait·CAUTION/blocked_ai_score,09:07~09:10은 CAUTION/blocked_ai_score로 연결됐다. 당시 legacy BuyScore prior 부재와 AI threshold 차단은 실제 기록대로 보존했다. 이들을 새 패턴이 없어서 놓친 건으로 다시 세지 않는다. [exact attempt/capture 연결](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/joined.json), [고정 감시 downstream](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/fixed-funnel.json).

주성09:00:25~09:05:44에는 원 lifecycle14개가 모두 first_turn_invalidated였고 Main claim0이었다. 일부는 같은 wall clock의 다음 sequence에서 즉시 부적격이 됐다.09:17:15~09:18:41에는4개 중3개가 claim 전 무효화되고1개는 목표 근처 claim 후 Main 기록이 목표 뒤에 남았다. 실제09:18:41.938 disposition은 reversal_signal_path_changed다. 기존 native wake는 설치돼 있었다. symbol-only queue 방문과 native claim을 구분했고, 단명한 FIRST를 연장하거나 stale 신호를 재사용하지 않았다. [원 logger 경로·offset·SHA](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/runtime-lifecycles.json), [창별 lifecycle 최종 버전](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/window-lifecycles.json).

주성11:07~11:12는 당시49445/order0013982의09:19:24 실제1주 체결이 local pending/odno 발행보다 먼저 왔고 initial ENTRY_BUY 투영이 누락돼 BUY_ORDERED가 남았던 **기존 확정 결함**이다. 기존 owner가 initial native ledger binding 및 `_restore_registered_entry_buy`의 동일 일자 terminal 복구로 수리했고10/22 12:11:46 HOLDING1·registry/DB/broker1 일치를 확인했다. requested2의 미제출 잔량을 추가 제출하지 않았다. 이미 보유한 종목의 이 상승 창을 새 initial BUY를 놓친 기회로 추가 계산하지 않는다. 이번에57143fe21의 ancestry와 선택본 원 source를 재확인하고 early-fill fault16개·late REST staging1개·terminal initial recovery34개 등을 다시 검증했다. 원 fill·수량·history는 수정하지 않았다. [원인→수리의 기존 owner](postclose-root-cause-recovery-review-2026-10-19.md#entry-receipt-custody-race-and-repeated-cancel-2026-10-22), [실제 복구](postclose-root-cause-recovery-review-2026-10-19.md#integrated-entry-receipt-and-quantity-deployment-2026-10-22), [원 주문 증빙](../../tmp/order-cancel-receipt-incident-20261022-0920/owner-order-events.json). 과거 spread prefix 오표시도 이미 수리된 e48ac8ef3의 역사 진단이며 새 collection loss로 재분류하지 않는다.

### 짧은 관측 prefix 후보의 전체 비교

A39~43의 정의를 계산 전에 동결했다. FIRST+15초 회복,15초 돌파,15초 VWAP 재회복,3초 유지 FIRST,10틱 trade/bid 전진의5가설이다. ret15/VWAP15·DD15·회복·buy10과 필요한 경우30초 거래량 비교를 실제 prefix에서만 계산했다. 실제 physical lease 종료 뒤 특징을 다음 lease에 넘기지 않는다. root/confirmation의 동일 item·알려진 quote age≤5,000ms·spread≤0.10%와 기존 운영 safety를 유지했다. 이 연구 상한은 live AI/submit의 더 엄격한 guard를 대체하지 않는다. [정의·원천·코드 동결v2](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/candidate-freeze-v2.json).

10/21 REGULAR 전체 적격 종목485개와10/22 383개를 각각 비교했다.135개 승리 창만 골라 성과를 계산하지 않았다. actual ask·비용0.23%·net 목표+0.4%·stop−3%·30분·같은 완료 분봉 보조를 대조군과 후보에 동일 적용했다. source22를 보고 가설을 만들었으므로 두 날짜 비교도 독립 holdout이 아니다. 아래 W는 확인점이며 독립 주문·실현 승률이 아니다.

| source22 비교 | W / STOP / TIMEOUT / U | 확정 목표 선도달 비율 | 135개 중 포착 |
|---|---|---:|---:|
| 현행1d9 | 127 / 1 / 30 / 2 | 80.38% | 0 |
| 현행+A39 | 293 / 16 / 209 / 215 | 56.56% | 11 |
| 현행+A40 | 157 / 7 / 76 / 47 | 65.42% | 2 |
| 현행+A41 | 159 / 4 / 77 / 58 | 66.25% | 2 |
| 현행+A42 | 221 / 10 / 143 / 145 | 59.09% | 9 |
| 현행+A43 | 266 / 16 / 145 / 134 | 62.30% | 11 |
| 현행+5개 합집합 | 424 / 30 / 367 / 421 | 51.64% | 14 |

5개 합집합의 순추가는 W297/STOP29/TIMEOUT337/U419이며 기존 A17~38보다 새로 포착한 창은3개다.14개 중 처음 local lease 또는 고정 감시 안의 확인은13개다. 나머지 A40 한 창은 같은 collector epoch의 후속 lease에 속하므로 첫 probe 성공으로 부르지 않는다.10/21의 같은 현행 membership은 native 원 라벨부터 W0/TIMEOUT114였다. 새5개와 합치면 W13/STOP0/TIMEOUT183/U157·6.63%이며 추가 W13/TIMEOUT69/U157이다. 이는 당시 실제 e815 정책의 성과나 이전 parent 연구의118W와 다른 비교다. 날짜·scope별 악화와 U를 숨기지 않았다. [전체 날짜·scope·순추가·포착 대조](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/candidate-review-final.json).

새3개는 같은 실제 관측 lease 안에서 후보 ask→후속 known-age bid도 목표에 도달했다:289220의12:47:03.951 ask1,635→bid1,646(+0.4412%,4.695초),12:47:10.144 ask1,660→bid1,671(+0.4311%,2.218초),357880의13:38:23.246 ask1,809→bid1,824(+0.5973%,83.899초)다. 가격 기회는 존재했지만 앞의 짧은 두 건을 실행 여유가 입증된 거래로 바꾸지 않는다. 수량/depth·실제 체결·broker 비용·실현 PnL은 null/미증명이다. 전역 추가는 STOP·TIMEOUT·확정 비율 악화로 미채택이며 좁은 scope를 결과 뒤에 새로 고쳐 채택하지 않았다.

### 검토·수정보완·경계와 후속 수용

두 연구 결함을 수정했다. 첫 native 재생은 probe REMOVE 뒤 State 폐기를 누락해 이전 lease 이력을 이어 붙였고 DD를 잘못된 projection에서 비교했다. `_release_exact_probe_item`→`invalidate_observation_interval`과 실제 lifecycle census로 reset을 복구하고 diagnostic_rolling DD 및 current source/quote의 truth만 대조해 **257개 비교의 feature/truth 불일치0**을 확인했다. 수정 전 결과도 보존했다. 새 A43의 초안은 원 quote age UNKNOWN을 native ProgressWindow의 허용값처럼 처리했다. 연구 reader의 복사 행에서 bid/ask만 무효화해10개 known quote가 다시 쌓일 때까지 bid 전진을 UNKNOWN으로 유지했다. trade return과 현재 spread 기반 가격 전진은 보존했다. v1 코드/정의/결과를 그대로 두고 v2로 동결·두 날짜만 재계산했으며 결과 집계는 동일했다. 원 결함 재현 실패→수리 후 통과와 prefix 불변·lease 단절·stale/결손/다른 item/교차 호가 음성 회귀를 확인했다.

selected926 root/cwd/PYTHONPATH의 module-origin 검증을 포함한 **87개 회귀 PASS**, 독립 선형 라벨24개와 별도 status/origin 층화14개(W4/STOP2/TIMEOUT4/U4)도 PASS다. 첫 회귀의 “현재 spread 기반 가격 전진까지 과거 quote 결손으로 지워야 한다”는 과잉 assertion1개는 유효 trade 사실을 보존하도록 고쳤으며 실패 log를 보존했다. production non-test/tests 추가·삭제0·운영 wrapper/dispatch/등록/스케줄/분기 추가0·이동0이다. 새 임시 실행은 기존 봉인 source22 연구 아래에만 있으며 native detector/feature/label/lease/index owner를 재사용한다. 원 봉인 연구는 불변 hash consumer 때문에 retained, 최종 해석은 본 절/causes-final로 consolidated, 잘못된 첫 재생과 v1 후보는 실패 증빙으로 retained하고 운영 소비자는 없다. 대체할 runtime 구현 none·제거 보류 none이다. 새 임시 코드/문서의 정확한 증감·compile/link/parser/diff 결과는 [완료 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/completion-checks.json)에 기록한다.

연구 시작10:50에는926ebca82/PID1982231/start36273583과1d9의128/128 소비가 유효했다.11:58 최종 확인에는 병행 ordered 작업이 selector를 a2ca8e7d8로 바꿨고 drained_awaiting_verified_start·새 PID 소비 미증명 상태였다. 이 연구는 해당 전환을 실행/복구하지 않았다. 관련 detector/diagnostic/receipt/sync10개 source SHA는926과 새 선택본이 일치했다. 이전 PID를 현재 PID 수용으로 재사용하지 않는다. [시간·선택본·source parity](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/runtime-final-snapshot.json).

5GB pipeline·407MB market raw를 전수 재독하지 않았다. 기존 검증 index는 source-window16.17MB·선택 compact payload0.38MB를 읽었고 header89.69MB는 한 번 순회했다. 원 AI payload27.57MB와 closed lifecycle log20.73/20.95MB를 각 한 번 읽고 이후에는 추출본만 썼다. candidate v2 두 worker는2GiB/CPU480초 한도 아래5.34/9.44초·RSS403/386MiB였고 재계산 범위는 quote-clock 수정에 영향을 받는 두 날짜뿐이었다. 새 수집/AI/Provider 호출·DB/원장 수정·정책/TTL/guard/수량·배포/재기동·주문 변경0이다.

이번135개 추적·후보 연구는 완료다. source23 종료·봉인/native 계산 뒤 A17~43을 같은 정의·physical lease 경계로 날짜별/누적 비교하는 다음 수용만 기존 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)의10/26 07:40~08:00 OPEN으로 유지한다. 경제·체결 증명이나 명시NXT 자연 수용 및 다른 수리 owner의 완료를 대신하지 않는다.


## 조건 불충족100개 scope별 후속 연구 — 2026-10-23

**결정: 전역 추가는 계속 미채택이며, 비상시감시 저가 정규장에 한정한 A42·A43·A44를 후속 연구 후보로 남긴다.** 100개를 실제 선택 branch·부모 root·필수 특징·호가·scope까지 추적했다. 실제 판정 시점에 호가 계약이 막은49개, 유효 호가에서도 원 branch의 필수 특징이 미준비인19개, 유효 호가와 알려진 특징에서 전략 조건이 막은32개로 구분된다.32개 전부가 실행 가능한 누락 매수라는 뜻은 아니다.100개 실제 native coverage를 원 재생과 대조해 전부 일치했고 이번 범위에서 production 판정 결함은 새로 확인되지 않았다.

### 원천·실제 선택·분모

앞 절의135개 중 `known_pattern_condition_or_root_failure`100개를 고정했다. 과거 실제 판정은 source22의 e815 정책으로, 개선 비교는 현재1d9e5b09 membership으로 수행하여 분모를 섞지 않았다. 실제 scope는 정책 cohort KRX·정규장·SOR이고 원천은 통합 `symbol_AL`이다. 실제 체결 거래소를 KRX/NXT로 추정하지 않는다. 원 State→보존 source257개/84,832행 대조·receipt는 재사용했으며 broker 상류 완전성의 새 증명은 아니다.

동결 source21/22 정규장 전체 적격 종목에 같은 정의를 적용했다. 원100개만의 승리 표본에 후보를 맞추지 않았으며 물리 감시 lease 경계에서 이력을 끊었다. source22는 기존 parent에도 사용된 개발 날짜이고 source21도 재사용된 비교 날짜여서 독립 holdout이 아니다. 현행 baseline은 source22 W127/STOP1/TIMEOUT30/U2·확정 비율80.38%, source21 W0/STOP0/TIMEOUT114/U0이다. 확정 비율은 `W/(W+STOP+TIMEOUT)` 진단값이며 비용0.23%·순목표+0.4%·stop−3%·1,800초의 가격 경로 라벨이다. 실제 주문/체결, 수량/depth, 실현 비용/PnL은 미증명/null이다.

### 실제 branch·조건과 정당한 차단

아래 세 분류는 창마다 상호 배타적이다. 안전한 native 평가가 하나라도 있고 필요한 특징이 모두 알려졌으면 전략 차단으로 분류하고, 그런 평가가 없으면 호가 전부 차단과 특징 미준비를 나눈다. 따라서 알려진 FALSE와 다른 gate의 UNKNOWN이 같은 창에 공존할 수 있으며 기존100개의 분류가 잘못됐다는 뜻은 아니다.

| 실제 scope | 창 | native 평가 시 호가 차단 | 안전한 호가에서 필수 특징 미준비 | 안전·필수 특징 준비 뒤 전략 차단 |
|---|---:|---:|---:|---:|
| 비상시감시·2만원 미만·G4 | 76 | 36 | 14 | 26 |
| 비상시감시·2만~10만원·G1 및 cumulative | 12 | 7 | 4 | 1 |
| 삼성·전 가격 | 2 | 0 | 0 | 2 |
| 두산034020·2만~10만원 | 2 | 0 | 1 | 1 |
| 주성036930·10만원 이상 | 3 | 1 | 0 | 2 |
| 알테오젠196170·10만원 이상 | 2 | 2 | 0 | 0 |
| HPSP403870·2만~10만원 | 3 | 3 | 0 | 0 |
| 합계 | **100** | **49** | **19** | **32** |

49개는 **실제 native root/평가 시점**의 차단이다. 창 전체 어느 시점에도 안전한 호가가 없던 것은41개이고, 나머지8개는 native 평가 밖에서만 안전한 호가가 있었다. 이를 창 전체/시장 전체의 거래 불가능으로 확대하지 않는다. 새35개 scope 후보는 이49개를 포착하지 않았다.19개 중2개는 새로운 짧은 prefix 정의의 필수 특징이 모두 알려진 시점에 포착됐으며, 기존60초 특징 UNKNOWN을 채워 통과시킨 것이 아니다. 원32개 중9개를 새35개가 포착했다.35개 합집합은 총11개이며 후보별 중복을 합산하지 않는다.

실제 선택 branch15개와 원인 추적에 필요한 부모5개를 함께 보존했다. 아래 실패 수는 해당 조건이 한 번 이상 FALSE였던 창 수라 서로 중복되며, parent root 부재를 child filter 실패로 바꾸지 않았다.

| scope | 실제 선택과 부모 | 확인된 조건/한계 |
|---|---|---|
| 저가 비상시감시76 | G4, FIRST_UPTICK | spread75·DD상한61·DD하한44·structure42·session_trend38·ret60하한25개. quote/특징이 모두 준비된 평가에서 **structure만 실패한6개 창/39개 평가**가 있어 좁은 가설을 구성했다. |
| 중가 비상시감시12 | G1, `manual_cumulative_834813b5bca104d4f65876d7` → `manual_path_dca327a873720e53` | G1 DD하한12·session_trend10·ret상한8·structure7·DD상한1. cumulative는7개 창에서 parent root 자체가 없어 child의 ret/volume 탓으로 분류하지 않았다. |
| 삼성2 | `legacy_dd5_ge_1_2_v1`, cumulative032eee → path918aff, path35c2d4 | legacy DD≥1.2 미달2. 다른 두 경로도 DD/수익률/구조 등의 실제 조건 실패가 있으며 복합 조건을 한 gate 완화로 대체하지 않았다. |
| 두산2 | D1, cumulativef3ee30 → pathad9afa | D1 DD하한2, parent DD하한·VWAP·ret하한 각2. 한 창은 안전한 평가에서도 원 필수 특징이 부족하다. |
| 주성3 | cumulative4a9cc3 → `legacy_dd5_0_8_vol_up_v1`, path7d9fd5 | legacy DD≥0.8·volume≥1 조건 실패가 각각3개 창에 존재. volume UNKNOWN이 있으면 legacy는 UNKNOWN을 먼저 반환한다. |
| 알테오젠2 | cumulative06a0b1 → 같은 legacy, path9e8f22 | legacy DD하한2, path ret상한·DD하한2. 모두 실제 평가 시 호가 차단이라 조건만 바꿔 통과시키지 않는다. |
| HPSP3 | legacy DD1.2, cumulative2e9c71 → typeae4445, cumulativec0dd5f, pathf37911 | legacy DD미달3·type의ret상한/DD하한/structure각3·hold branch의spread/DD각3·path session_trend3. 모두 native 호가 보호 대상이다. |

전체 ID·원 정의·각 branch의 평가/미평가·FALSE/UNKNOWN과 원 값은 [동결 정의](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/freeze-v3.json), [100개 native 추적](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/branch-diagnosis.json), [scope별 전체 집계](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/result.json)에 있다. G4의 원 규정은 FIRST, session_trend=UP, ret60≥0.2%, structure=FALLING, 0.2≤DD<0.4%, bid 분모 spread≤0.1%다. 최초 구조만 실패한6개는003010·179880·289220 두 창·357880·417200이며 MIXED/RISING이었다. 고점 추격/구조 불확실 차단이라는 원 규정은 정상 작동하지만, 되돌림 뒤 구조가 회복된 경우까지 제외할 가능성을 검증했다.

### 좁은 후보와 STOP·TIMEOUT의 같은 분모 비교

먼저 원 A39~43의 수치와 hold를 바꾸지 않고7개 scope별 추가35개를 동결했다. 후보 root와 confirmation 모두 기존 trade 분모 spread와 registered bid 분모 spread≤0.1%, known quote age≤5,000ms, 같은 item·lease·epoch·session을 요구한다. 기존 정책의 신호는 보존한다. 그 뒤 G4의 단일 전략 조건5개를 각각 진단하는 정의를 outcome 계산 전에 동결했다. quote/UNKNOWN은 제거 대상이 아니며 다른 조건은 전부 TRUE여야 한다. A44는 그중 **원 G4에 structure=MIXED/RISING인 경우를 추가하는 가설**이다. spread·DD·ret60·session_trend·FIRST root 및 모든 원 필수 입력은 유지한다.

A39는15초 회복+1초 유지, A40은15초 돌파+1초 유지, A41은15초 VWAP 회복+1초 유지다. **A42**는 FIRST+3초 유지·ret15≥0.03%·VWAP15 이상·buy10≥70·DD15≤0.4%, **A43**은 FIRST+1초 유지·trade/bid 각각10틱 전진≥0.03%·현재 spread 대비 가격 전진≥1·buy10≥60이다. A42의3초는 앞선 연구에서 이미 동결된 패턴 확인 길이이며 새 실행 시간상한이 아니다. 기존5초 실행 기한·stale/충돌·AI·수량·broker/account·hard guard를 늘리거나 해제하지 않았다.

표는 **비상시감시·2만원 미만·정규장에만 추가**했을 때의 순추가 신호다. W/STOP/TIMEOUT/U는 독립 거래 수가 아니며 한 상승/하락 구간의 여러 확인을 포함한다. 원100개 포착은 후보 ask 이후 trade 목표가 원 창의 목표 시각까지 도달한 경우, 더 엄격한 bid 열은 같은 lease의 실제 bid 목표도 그 시각까지 확인된 경우다.

| 후보 | source22 추가 W/STOP/TIMEOUT/U | 100개 중 포착 창 | 그중 원 목표 시각 전 실제 bid 확인 | 현행+추가 확정 비율 | source21 추가 W/STOP/TIMEOUT/U |
|---|---:|---:|---:|---:|---:|
| A39 | 20/1/0/69 | 7 | 3 | 82.12% | 0/0/0/11 |
| A40 | 1/0/0/10 | 0 | 0 | 80.50% | 0/0/0/5 |
| A41 | 2/0/0/11 | 1 | 0 | 80.62% | 0/0/0/4 |
| A42 | 10/0/0/51 | 5 | 2 | 81.55% | 0/0/0/12 |
| A43 | 17/1/0/52 | 7 | 3 | 81.82% | 1/0/0/13 |
| A44 | 63/2/0/44 | 4 | 2 | 85.20% | 0/0/0/0 |

두 날짜 누적 전체 현행은W127/STOP1/TIMEOUT144/U2·46.69%다. 저가 후보만 더하면 A42는W137/STOP1/TIMEOUT144/U65·48.58%, A43은W145/STOP2/TIMEOUT144/U67·49.83%, A44는W190/STOP3/TIMEOUT144/U46·56.38%다. source22의 개선 방향이 누적에도 남지만, 같은 날짜 재사용과 큰 U 비중 때문에 새 날짜 검증이나 경제 증명을 대신하지 않는다.

source22 저가 scope의 현행 resolved 표본은0이라 그 scope의 원 비율은 null이다. 표의80%대는 전체 현행 분모에 좁은 추가를 합친 진단값이며 저가 scope 자체의 기존 대비 수익 개선률이 아니다. A44 추가 W63은 목표 시각15개이며003010의26개·179880의23개에 집중된다. 같은 목표 시각의 반복 확인을 독립 증거로 늘리지 않았다. source21에는 A44 추가 자체가0이고 A42도 확정 표본0이므로 두 날짜의 재현성을 입증하지 못했다.

A44의 원100개 포착4개 중003010은09:04:37.905 ask12,190→14.957초 뒤 bid12,270(비용 후+0.4248%),179880은09:57:42.002 ask15,680→3.603초 뒤 bid15,790(+0.4699%)로 원 목표 시각 전에 실제 bid 상승이 확인됐다. 나머지289220 두 창의 bid 목표는 원 창의 목표보다 늦어 별도 열에서 제외했다. 저가 A39~44 전체를 합쳐 원 목표 전에 실제 bid까지 확인된 고유 창은5개다. 매수 당시 수량 체결과 Main의 실제 소비까지 입증한 것은 아니다.

다른 scope도 숨기지 않았다. 주성 A39는 추가W131/STOP14/TIMEOUT124/U50, A43은W121/STOP14/TIMEOUT115/U64로 전체 확정 비율60.42%/60.78%까지 악화한다. 두산·알테오젠 A39는 TIMEOUT25/14가 늘고 source21에서도10/44가 늘었다. 삼성 A39는 source22 W4/TIMEOUT15/U30, 중가 비상시감시는 확정 이익 없이 U만 남는다. HPSP의 앞선 A42 한 양성은 정확한 bid 분모 spread를 적용하면 사라져 두 날짜 모두 추가0이다. 이 scope들은 좁은 후속 후보에서 제외한다. G4의 나머지 단일 gate 진단은 DD상한 제외 시 W7/U4지만 원100개 포착0, ret하한 제외 시 U4뿐이고 session_trend/DD하한은 추가0이었다. 원100개 바깥의 작은 양성을 근거로 새 DD 임계치를 선택하지 않았다.

### 반례·미확정·실행 가능성

A39/A43의 공통 STOP은138360의09:03:37.945 ask1,790→09:04:54.461이다. 같은 FIRST root에서 A42의3초 확인점은 **존재**했고, buy10=38.2152로 원70 조건을 만족하지 않아 차단됐다. 이를 “3초 hold 자체가 실패했다”로 설명하지 않는다. A44의 STOP2는099520의09:17:37.177/37.704 ask1,369→09:17:48.763으로 **하나의 하락 구간에 대한 두 확인**이다. ret60=3.5552%·session+4.5837%·MIXED·DD0.2188%·spread0.0731%로, 구조만 허용하면 급등 뒤 추격도 들어온다는 반례다. 이 결과를 본 뒤 ret 상한을 새로 맞추지 않았다.

**TIMEOUT0은 TIMEOUT 증가가 없다는 확정 증거가 아니다.** 저가 후보·진단의 고유 U191개 중190개는 같은 item의 완료 분봉이 없고1개도 분봉 결과가 U다. 해당 lease에서 확인 뒤 남은 관측은 최대142.204초로1,800초 horizon보다 짧다. U를 무손실/0수익이나 시간 초과 없음으로 바꾸지 않았다. A42의 STOP0 역시 이 미확정 범위를 포함한 안전 보장이 아니다.

A44의 FIRST 신호는109개 중99개가 다음 하락/관측 종료를 고려한 유효시간 **상한1초 미만**,75개는100ms 미만,59개는 같은 normalized ms 안에서 무효화된다. 기존5초 기한·첫 하락·관측 종료 중 이른 경계로 계산한 상한이며 실제 Main의 claim/AI/제출 latency 검증은 아니다. 따라서 W63이 많다는 이유만으로 실전 추가63건으로 부르지 않는다. 향후 검증은 원 기한 안의 실제 소비 가능성을 확인하며 deadline 연장으로 대체하지 않는다. [정확 반례·bid·미확정·수명 대조](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/assessment.json).

### 구현·자체 리뷰·수정보완·최종 검증

수정은 임시 연구 reader에 한정했다. 첫 추적은 cumulative의 선택 branch만 읽고 native parent 평가를 놓쳤고, 보완 중 legacy volume 결손의 UNKNOWN 우선순위를 registered의 FALSE 우선순위와 같게 취급한 오류를 발견했다. native condition call과 diagnostic 기록을 함께 읽되 값을 바꾸지 않도록 고쳐 원 plain State·원 재생의100개 coverage와 일치시켰다. 첫 집계의 defaultdict 조회가 빈 포착 key를 만들어 합집합100으로 부풀린 오류도 nonempty key만 세어 **11개**로 수정하고 분류 교차표 합과 재대조했다. 원 코드/동결/실패 log/잘못된 출력은 별도 보존했고 최종 집계가 해석을 대체한다.

original defect 실패 재현→수리 후 통과, native State/condition producer와 consumer 일치, legacy/registered의 서로 다른 UNKNOWN 계약, stale/결손/다른 item/교차 호가·bid 분모 경계, 날짜/lease/epoch/session 격리, G4 복수 실패/UNKNOWN/호가 제외 불가를 포함해 **35개 회귀 PASS**다. candidate 계산부의 AST가 reader 수정 전후 동일함을 확인해 영향 없는 전수 계산은 반복하지 않았다. G4 새 라벨6개를 별도 선형 oracle로 층화 대조했다. 두 날짜 전체 비교·100개 parity·35개 scope안과5개 gate 대조·compile/link/owner/parser/diff·변경량은 [최종 검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/completion-checks.json)에 기록한다.

baseline commit은 `609cdcf12403ec2e2ed7e273cd49e839e781ac9d`이다. production non-test/tests 추가·삭제0, 운영 entrypoint/dispatch/등록/스케줄/분기 추가0, 이동0이다. 새 임시 코드는 기존 봉인 연구의 native detector·feature·label·lease·bid reader를 재사용하며 이번 요청의 계측·scope 비교만 담당한다. runtime replacement는 none이다. 이전 연구/첫 실패본은 원 hash·실패 증빙 consumer 때문에 retained, 잘못된 최종 해석은 본 절과 result/assessment로 consolidated, 제거할 운영 구현/임시 호환 wrapper 및 deferred removal은 none이다. 순증은 요청된100개 원인 계측과 좁은 반사실·반례 검증 및 재현용 테스트이고 새 운영 owner를 만들지 않았다.

체크리스트 수정 전 selected a2ca8e7d8의 native `preserve_checklist('2026-10-23')`로 원 strict SHA91d9874a…를 재검증·보존했다.12:42 read-only snapshot의 selector는 a2ca8e7d8, 상태는 pid_receipt_attested, bundle은1d9e5b09다. 연구가 사용한 봉인926과 선택본의 관련12개 source SHA 일치를 확인했다. 이 snapshot을 현재 Main health나 후보 소비 증명으로 확대하지 않는다. [문서 보존](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/checklist-preservation.json), [시점·선택본·parity](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/runtime-context.json). 이번 연구의 production·원장/DB·정책/guard/TTL·provider·배포/재기동·주문 변경0이다.5GB pipeline/407MB raw 재전수 읽기 없이 기존 compact 증빙과 두 종료 날짜의 compressed normalized 및 완료 분봉만 사용했다.

100개 추적과 좁은 후보 연구는 완료다. 후속은 동일 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)의10/26 07:40~08:00에 source23 종료·봉인/native report를 확인한 뒤, A42/A43/A44의 원 정의와 음성 scope 대조를 새 날짜/누적 분모로 비교한다. U 결손·STOP/TIMEOUT 증가·원 목표 전 bid·신호 유효시간/원 deadline 내 소비를 함께 검증한다. 기존 A17~43 비교와 원 역사/수용을 보존하며 새 승격 문턱이나 실제 정책 적용 권한은 추가하지 않는다.


## A42·A43·A44 미확정 원인과 보존 원천 복원 — 2026-10-23

**결정: 연구 입력에 빠졌던 보존 REST 분봉 revision을 편입해 고유 미확정159개 중17개를 복원했다(W6/STOP2/TIMEOUT9).** A42·A43의10/22 STOP/TIMEOUT0·현행 대비 확정 비율 개선 해석을 수정한다. A44의U44는 그대로 남는다. 감시·수집·보존·라벨링을 추적한 범위에서 새 운영 결함은 확인되지 않았으며, 원래의 U는 관측 계약에 맞는 제외였다. 이후 보존 원천을 발견한 것은 별도 복원 generation이고 원 봉인 결과/정책을 덮어쓰지 않았다.

### 대상과 최초 관측 종료

대상은 앞 절에서 남긴 **비상시감시·2만원 미만·정규장·SOR**의 A42/A43/A44다. source21의U12/U13/0은 고유21개, source22의U51/U52/U44는 고유138개이며 두 날짜 합계159개다. 같은 시각에 A42/A43이 함께 확인된 중복을 합산하지 않는다. 앞 절의U191은 A39~43 및 단일 gate 진단을 포함한 다른 분모다. 정책 cohort KRX·원천 `symbol_AL`/krx_nxt_integrated·broker SOR·실제 체결 거래소 미상을 유지했다. 원래의 모든 root·확인·호가·특징·lease 경계와 비용/목표/STOP/1,800초를 보존했다.

| 최초 연속 관측 종료 | source21 | source22 | 고유 합계 | 증명한 범위 |
|---|---:|---:|---:|---|
| 명시된 동일 lease 해제, horizon 전 종료 | 21 | 135 | **156** | create/release item·lease·transport epoch·원 log line 대조. 원가격 경로 내부의 invalid/sequence/clock 단절0. |
| 재기동 중 REMOVE 미확인·수집기 정상 종료 | 0 | 3 | **3** | 모두290720의 동일 lease. release ACK를 만들지 않고 원 오류와 closed epoch를 각각 보존. |
| 수리되지 않은 내부 원천 단절로 최초 U | 0 | 0 | **0** | 이번159개 경로 안에서만 확인. 상류 시장/브로커 전체 완전성을 뜻하지 않는다. |

명시 해제156개는57개 대상 lease 중56개에 속한다. 실제 lease 길이는 source21 148.882~149.574초, source22 148.557~149.938초다. 당시 source22의 queue150초 배정 계약과 일치하며, 현재 또는 다른 세대의180초 관측 정책을 과거에 적용하지 않았다. 확인 신호 뒤 연속 관측 여유는 source21 4.400~130.781초, source22 0.090~142.204초로1,800초보다 짧다. 감시 해제 뒤 가격을 수신하지 않은 것을 수집 손실/정상 무거래로 단정하지 않는다. 기존 lease를30분으로 연장하거나 새 구독을 만들지 않았다.

나머지3개는290720의11:41:32.608/33.601(A42),11:42:12.034(A43)다.11:42:36 우아한 종료 시작→11:42:42 `ws_remove_unconfirmed`와 마지막 관측→11:42:46.014 collector closed 영수증을 결속했다. 해당 native epoch의 enqueue/worker/persisted308,521 일치·source loss0·raw reconciliation 완료를 확인했다. 다음 source epoch의 뒤늦은 가격을 이어 붙이지 않았다. REMOVE 실패를 정상 해제 성공으로 바꾸지 않으며, 구 generation 종료와 item 해제 영수증은 서로 다른 증거다. [159개 개별 lease·원인·종료](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/result.json).

### 수집·정규화·보존·분봉 발행 추적

봉인 source의 원 logical prefix와 현재 원장을 대조했다. source21의 gzip은 압축 전406,993,706B/388,468행의 원 SHA, source22의 원장은406,650,251B/388,638행의 원 SHA가 각각 일치했다. 원장→정규화 타깃 종목37,555행(2,057+35,498)의 가격·호가·수량·시각·native/collector identity·적격 표시가 전부 일치했다. 관련5개 closed epoch의 native validator와 손실/정합 계약도 통과했다. 압축/삭제/보존 유실 또는 이미 받은 유효 행의 정규화 누락은 이 범위에서 확인되지 않았다. [물리/논리 보존 검증](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/preservation-2026-10-21.json), [source22](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/preservation-2026-10-22.json).

원 source.json과 봉인 bar-catalog가 알려준 분봉 원천에서는158개에 같은 item의 분봉이 없고,010140 한 건만 짧은 checkpoint가 있었다. `forward_collector._writer_for`→`CompletedBarProjection.consume`은 명시된 symbol scope에서만 분봉을 발행하며, 짧은 lease 밖의 누락 틱이나 조용한 분을 생성하지 않는다. 당시 source22 코드의 기본 발행 목록은 고정5종목이고, 실제010140 checkpoint도 원 영수증대로 별도 존재한다. 기본값을 실제 historical env로 단정하지 않았다.010140의 checkpoint는complete2/gap1/pending1로 종료부가 부족하여 `completed_bar_end_missing`였다. 파일 부재와 짧은 원천은 보존 유실과 다르며 scope만 넓혀도 원래 수신하지 않은30분 경로가 복구되지는 않는다.

추가 보존 원천을 끝까지 확인했다. `machine_completed_price_source`에는10/21·10/22 캐시가 없다. 기존 SharedCandleRead512개 슬롯(112.71MB)을 한 번 조사해 같은 `_AL`35개를 찾았고, 실제 장기 보존 owner인 `main_minute_history`의 일자별 indexed immutable revision으로 연결했다. 최신 일자 DB의 current68/49개를 읽어, source22의003010/290720/002710/328130 **4개 exact item revision**을 동결했다. source21 대상에는 해당 revision이 없었다. 이후 소비는 native `completed_history.read(..., revision=..., include_forming=False)`로 manifest/bar hash·available clock·원 request code/base date·HTTP/admission·오류 상태를 확인한다. 수정주가1·원 minute timestamp·같은 날짜/item을 유지했으며 native의 기존 보수적 분봉 라벨러를 재사용했다. 새 provider/REST 요청·토큰 조회·수집·원장/DB 쓰기는0이다. [원천 탐색](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/existing-candle-inventory.json), [4개 불변 revision과 선택 규칙](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/backfill-freeze.json).

### 복원 결과와 남은 미확정

원159개 중 새 보존 분봉과 연결된 것은29개다.17개를 복원했고12개는 기존 분봉 계약으로 계속 U다. source21 고유21개는 변동 없고 source22 고유138개는17개 복원 뒤121개가 남는다.

| 보존 원천 편입 뒤 상태 | 고유 수 | 처리 |
|---|---:|---|
| WIN 복원 | 6 | 비용 포함 목표 선도달. 실제 bid/체결/PnL 증명으로 전용하지 않음. |
| STOP 복원 | 2 | 003010의 같은 하락 구간에 대한 A42/A43 각1확인. 독립 손절 거래2개가 아님. |
| TIMEOUT 복원 | 9 | 충분한 분봉 구간에서 기존 라벨러가1,800초 목표/STOP 미도달을 확인. |
| 충분한 후속 원천 부족 | 130 | 원 WS/REST 동일 item 분봉 전무129개+010140의 짧은 WS 분봉1개. |
| 분봉은 있으나 보수적 라벨 계약상 U | 12 | clock_disagreement8·entry/horizon boundary_touch3·end_missing1. |
| 합계 | **159** | 원159개 identity 유지, 누락/중복 제거 없음. |

재기동3개 중 A43 한 개는 보존 분봉으로WIN(11:42:12.034 이후227.966초, bar-end 상한)을 복원했고 A42 두 개는 clock disagreement로 U를 유지한다. 새 STOP 두 확인은003010에서 같은13:40 분봉 끝에 도달하며 진입 뒤1,746.956/1,749.356초다. 이처럼 감시가 먼저 끝났던 구간에 실제 실패도 있어 U를 무손실로 보아서는 안 된다. 초 단위 경로/entry/horizon이 애매한 분봉을 임의로 WIN/STOP으로 바꾸지 않았다. 원 tick 관측과 충돌하는 확정 분봉 결과는0건이며, 다른 item/날짜/미래 revision을 대체 원천으로 쓰지 않는다. [개별 복원·남은 사유](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/recovered.json).

| source22 저가 추가안 | 기존 W/STOP/TIMEOUT/U | 복원 뒤 W/STOP/TIMEOUT/U | 고정 현행+추가 확정 비율: 이전→복원 뒤 |
|---|---:|---:|---:|
| A42 | 10/0/0/51 | **11/1/4/45** | 81.55%→**79.31%** |
| A43 | 17/1/0/52 | **22/2/6/40** | 81.82%→**79.26%** |
| A44 | 63/2/0/44 | **63/2/0/44** | 85.20%→85.20% |

현행 원 baseline W127/STOP1/TIMEOUT30/U2·80.38%를 고정해 비교했다. A42/A43의 source22 우위 해석은 철회하며, A44의 TIMEOUT0도 U44가 남은 제한된 관측이다. 두 날짜 누적 전체 현행46.69%에 대해 복원 뒤 A42는W138/STOP2/TIMEOUT148/U59·47.92%, A43은W150/STOP3/TIMEOUT150/U55·49.50%, A44는W190/STOP3/TIMEOUT144/U46·56.38%다. 누적 방향과 단일 날짜 악화를 함께 남겼다. 새 일별 승리 유지/EV/표본 문턱을 만들지 않으며, 독립 holdout·실제 체결·수량/depth·실현 경제성은 계속 미증명이다. 기존100개 포착 창/bid 증명 수를 분봉 라벨로 늘리지 않았다.

### 수리·리뷰·회귀와 소비 경계

확인된 보완점은 **연구 consumer가 보존 REST revision을 입력에 포함하지 않았던 원천 발견 누락**이다. 원 운영 라벨러가 존재하지 않는 tick 경로를 U로 둔 것은 정상이다. 기존 봉인 연구의 hash를 보존하기 위해 그 아래 `unresolved/trace.py`에서 원인 추적과 `recover`를 확장했으며, native history producer/reader·label kernel을 재사용했다. 일자/정확 item·원 provenance를 확인해4개 revision을 먼저 동결한 뒤 모든159개를 동일 규칙으로 다시 소비했다. 원 U/실패/PID/정책 bytes를 수동 수정하지 않았다. 이 입력 누락 보완과 새 결과 소비는 완료이며, 원천 자체가 없는130개를 복구 완료로 표시하지 않는다.

자체 리뷰에서 임시 reader의 두 결함을 수정했다. 압축 manifest의 물리 bytes를 논리 bytes와 비교한 오류는 물리 shard identity/size/compression과 봉인 logical prefix SHA를 각각 검증하도록 고쳤다. 과거 유효 closed receipt에 PID 필드가 반드시 있다는 가정도 native validator가 허용한 optional identity를 null로 보존하도록 수정했다. source21의 PID를 후대 값으로 채우지 않았다. dirty workspace의 다른 reader로 검사한 한 실패는 정확한 봉인926 cwd/PYTHONPATH로 재검증했고, 선택a2ca8e7d8와 관련5개 code SHA 일치를 확인했다. 원 실패 코드/기록을 보존했다. production 데이터나 기준을 바꿔 검사를 맞추지 않았다.

원 실패 재현→수정 후 통과, 압축/비압축 원장→정규화, native history producer→revision reader→라벨 consumer, 변조/미래 revision·item/date·오류 provenance 거부, 누락/sequence gap/짧은 분봉의 U 유지, shutdown과 현재 미확정/다른 epoch 분리를 포함해 **62개 관련 회귀 PASS**다. 보존 분봉과 결속된29개 전부를 독립 선형 oracle로 대조했다. 출력을 재사용할 때 원 hash를 확인했으며, 원인 추적 코드는 `trace-causal.py`로 보존해 결과의 원 code SHA를 유지했다. [최종 회귀](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/regressions-final.log), [최종 변경·검사](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/completion-checks.json).

최종 raw 검증은8.44초였고 두 원장 논리813,643,957B를 읽었다. 앞선 임시 reader 오류2회에서 source21을 재독한 논리813,987,412B도 별도 실패 비용으로 공개한다. 원인/metadata preflight 후 최소 두 partition만 재실행했고 이후 원장 재독 없이 작은 원인 결과·4개 revision snapshot만 소비했다. 실제 recovery는 indexed current117개/4선택으로 수행하며512슬롯 탐색을 매번 반복하는 새 소비 경로를 만들지 않았다. 새 운영 producer/validator/cron 또는 provider surface는 추가하지 않았다.

baseline609cdcf12403ec2e2ed7e273cd49e839e781ac9d·production non-test/tests 증감0·runtime entrypoint/등록/스케줄/분기/이동0이다. 새 임시 소스/테스트·실패 증빙 snapshot과 문서 증감은 최종 검사에 분리 기록한다. runtime replacement는none, 원 native history/label owner는 현재 소비 때문에retained, 원 봉인 연구·실패본·trace-causal은 hash/회귀 consumer 때문에retained, 최신 해석은본 절/recovered로consolidated, 임시 호환 wrapper/deferred removal은none이다. 문서 수정 전 native preserve_checklist로 strict91d9874a…를 보존했다. 이번 read-only runtime snapshot의 selecteda2ca8e7d8/PID2333464/start36885727은 context이며 새 연구 후보 소비/배포 증명이 아니다. [시점·parity](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/runtime-context.json), [strict 보존](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/source22-review/causal-trace/narrow-scope/unresolved/checklist-preservation.json).

이번 원인 추적·연구 reader 수리·17개 복원은 완료다. 남은142개는 식별된 원천 부족/보수적 라벨 이유와 원 identity를 유지한다. 다음 수용은 같은 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)의10/26 07:40~08:00에 source23 종료·봉인/native report와 보존 minute-history revision을 함께 고정해 A17~44를 날짜/누적·scope별로 비교한다. A42/A43의 복원 실패를 음성 대조에 유지하고 A44의 짧은 신호 수명/U44를 함께 검증한다. 새 구독/감시 연장·정책/guard/실행 기한·배포/재기동·주문 권한은 추가하지 않는다.

### 보존 REST 분봉의 기존 생산자·소비자 통합 — 2026-10-23

**결정: 보존 REST 편입을 기존 연구 생산자·소비자에 통합하고 불변 배포 후보 `d53c36e59f6e6178cfb9de22f6b1a91ca1bf92f6`를 준비했다. 후보 P5와 회귀검증은 PASS이며 배포·재기동은 실행하지 않았다.** 임시 연구에서 발견한 입력 누락을 정식 일별 source 생성 경로에서 보완한다. 원래 없는 tick을 U로 둔 운영 판정, 과거 봉인 결과와 정책은 그대로 보존했다.

원인과 수정은 `completed_history`의 일자별 current→immutable revision 인덱스에서 시작한다. 기존 `continuous_reversal_postclose.completed_bars`는 broker 보존 파일과 WS checkpoint만 발견했고 REST 보존 revision을 발견하지 않았다. 선택9e 원 코드에 새 생산자→소비자 회귀를 적용하면 exact item이 없는 KeyError가 재현된다. [원 결함 재현](../../tmp/main-machine-rest-history-integration-20261023/original-defect.log). 같은 저장 owner에 `outcome_revisions`/`outcome_rows`를 추가해 native revision/bar hash·available clock·원 API/request code/base date·HTTP/admission·오류 및 완료 봉을 검증한다. provider/REST 요청·원 DB 변경·DB 복제나 전체 DB 해시는 없다. 손상된 한 scope/revision은 이유를 가진 제외 영수증으로 남기고 정상 WS/다른 exact item은 유지한다.

기존 `completed_bars`가 WS·broker·REST의 실제 bytes를 불변 파일로 봉인하고 `path/sha256/kind/source_date/origin_path`를 기록한다. REST 영수증에는 원 생산자 코드 hash와 현재 소비자 코드 hash도 각각 결속한다. 새 source manifest의 `completed_bar_sources`는 부모 세대의 고정 참조를 이어받는다. branch/registered/path/operating/cumulative 소비자는 그 source를 전달하고, 해당 날짜의 고정 목록이 있으면 현재 DB/WS를 다시 발견하지 않는다. 원 파일명과 무관하게 종류가 유지되고, 고정 자료가 변조·누락되면 차단한다. 새 모듈·보고서 생산자·wrapper를 만들지 않고 기존 저장·연구·라벨 owner를 확장했다.

REST 수정주가와 raw WS는 독립 라벨 series로 평가하며 서로 또는 다른 REST revision의 앞뒤 봉을 합치지 않는다. exact `_AL`/`_NX`/plain item을 구분하고 SOR route에서 실제 NXT venue를 역추론하지 않는다. 출처별 WIN/STOP/TIMEOUT 충돌 및 clock/both-barriers/boundary 모호성은 U다. 기존0/−60초 분봉 시각의 보수 비교·비용/목표/STOP/TIMEOUT·실행 기한과 quote stale/conflict, 입력 UNKNOWN, 수량·체결·실현 PnL 결손을 유지한다. REST 결과는 outcome 보완 전용이며 당시 특징 이력이나 주문 가능한 bid를 만들지 않는다.

리뷰에서 보완한 사항은 누락 revision을 숨기던 inner join을 left join으로 교체한 명시적 제외, scope·bar 변조/미래 clock 검증, 봉인 파일 종류·원 경로 보존, 독립 series의 모호성을 다른 series의 WIN으로 덮지 않는 처리다. 매매 kernel에서 offline `Bars` 외 AST와 native history `key/read/publish/_completed`의 AST는 선택6d와 동일하다. 연구 의존성은 입력 영수증과 기존 인계의 정확한 전체 코드 묶음으로 결속하며 `continuous_reversal_policy_v6` 및 그 매매 정책 코드 목록은 선택6d와 byte 동일하다. [AST·컴파일 검증](../../tmp/main-machine-rest-history-integration-20261023/safety-ast-parity.json).

첫 후보027a35968의 P5는 `entry_consumer_reviewed_dependency_unreviewed:...continuous_reversal_policy_v6.py`로 intake에서 차단됐다. 이 실패와 불변 후보는 보존했다. 기존 `intraday_release_handoff`의 완전한 reviewed dependency profile과 `startup_validation_code_context`의 독립 원본/현재 source-pair 목록에 검토한 exact bytes를 결속했고, 기존 발행 profile·정책 원본·과거 리뷰 이력은 유지했다. 새 실행 경로나 검사 우회는 없다. 일부 의존성 누락·dirty/committed 변경·이전 source 혼합 차단과 과거 소비본의 정상 인계를 함께 회귀했다. [원 P5 실패](../../data/report/main_startup_validation/2026-10-23/e103fe2bfcf440368aa679fbf547c691/final.json).

검증 결과는 최종 불변 후보의 연구/정책/공유 소비자 **375 PASS**, 인계·독립 준비 검증 **99 PASS**, 변경14개 Python compile 및 scoped `git diff --check` PASS다. 추가 실행 중 fixture의 새 keyword 누락, 테스트 Path import 누락과 Numba cache 쓰기 경로 문제를 구분해 수정/테스트 환경 경로 지정했고 원 실패 로그를 보존했다. 설치·가드/격리 완화는 없었다. [375개 회귀](../../tmp/main-machine-rest-history-integration-20261023/final-release-regressions.log), [99개 인계 회귀](../../tmp/main-machine-rest-history-integration-20261023/final-release-handoff-regressions.log).

실제10/21·10/22의 원159개를 최종 생산자로 읽어 W6/STOP2/TIMEOUT9/U142가 앞선 복원과159/159 일치했다. 이후 원천 발견 함수를 막고 고정 참조만 다시 소비해도 전수 일치한다. 금지 network 연결을 막았고 새 provider 호출0이다. 원천 자체가 없는130개와 보수적 라벨12개는 그대로이며 실현 수익으로 환산하지 않는다. [실제 입력·고정 참조·개별 결과](../../tmp/main-machine-rest-history-integration-20261023/actual-regression.json), [최종 후보 실행](../../tmp/main-machine-rest-history-integration-20261023/actual-regression-final-release.log).

| 기존 경로/구현 | 처분 | 대체 또는 유지 근거 |
|---|---|---|
| 임시 `unresolved/trace.py`의 REST 발견·복원 실행 | consolidated | 후속 생산은 native `completed_history`→`completed_bars`→기존5종 소비자로 통합. 원 임시 파일/해시는 과거 복원 및 회귀 증거로 retained, scheduled/runtime caller 없음. |
| 기존 `completed_bars`의 mutable 원천 경로 반환·소비자의 새 발견 | consolidated | 새 source generation에서는 불변 bytes/종류/원 경로/SHA로 대체. 중복 라벨러나 새 dispatch 없음. |
| 기존 단일 WS/broker `Bars` 라벨 계산 | retained | 기존 계산을 독립 series마다 한 번 재사용하고 충돌/모호성 합의만 추가. clock/비용/경계 규칙은 원 owner 하나가 유지. |
| `completed_bar_sources`가 없는 과거 source reader | retained | 실제 봉인 과거 세대와 정책 이력의 현재 소비자가 존재하며 기존 snapshot_sink/report 영수증을 유지. 과거 source에 새 필드를 수동 삽입하지 않는다. 새 일별 세대의 동결·재소비 검증은 같은 checklist owner가 소유. |

기준은 작업 시작 선택9e820cbf8에서 준비 중 새 선택 **6d8891ac3**로 변경되어 최종 후보는6d를 부모로 기존 수량/보유/observer 변경을 포함했다. 최종 선택6d 대비 비테스트 source10파일 **+253/−26**, test4파일 **+166/−4**이며 새 source/test 파일·모듈/CLI/등록·스케줄은0이다. 문서의 이번 변경은 기존 감사/제안/checklist3파일 **+35/−1**이며 다른 세션의 문서 변경은 이 집계에서 제외한다. 순증은 휴대 가능한 native revision 검증·동결 입력 재소비·독립 source 합의와 정확한 코드 결속/회귀에 해당한다. 다른 작업자의 shared workspace 변경은 후보에 섞지 않았다. source-only patch와 분리 집계는 [검토 patch](../../tmp/main-machine-rest-history-integration-20261023/reviewed-source.patch), [집계](../../tmp/main-machine-rest-history-integration-20261023/source-change-counts.json)에 보존한다.

불변 후보 경로는 `/home/ubuntu/KORStockScan-runtime-releases/machine-rest-integrated-20261023-d53c36e59`, 준비 branch는 `codex/machine-rest-integrated-20261023`이다. native release validation, 공유 data/logs/tmp/.venv/docs/restart.flag와 clean runtime source를 검증했다. 관리 release/worktree 수와 legacy origin 탐색 상한256 및 후속 준비 여유를 확인했고 삭제는 하지 않았다. P5 target은 **2026-10-23**, 실행 commit은 **d53c36e59**, 검증된 incumbent는 **6d8891ac3**다. 격리 Main에서 machine128 scope와 원 정책 소비자들을 native 계약대로 읽고 금지 시도0·자식 종료·원천 불변을 확인했다. `runtime_effect/actual_pid_consumed/allowed_runtime_apply=false`다. [최종 P5](../../data/report/main_startup_validation/2026-10-23/2f50a865e73741258a4f87b520f3be1c/final.json)의 SHA256은 `c662139821ca156835b5b1f64a58d815eeb50d705583690c8ad568299f446e0a`, [준비 영수증](../../tmp/main-machine-rest-history-integration-20261023/release-preparation.json)이 정확한 selector·PID/start 및 정책 hash를 소유한다.

배포 준비 시점의 실제 선택은6d8891ac3/PID3299469/start38150614이며 후보를 선택하거나 Main을 재기동하지 않았다. 새 정책 발행·provider/주문·guard 변경0이다. 배포/PID 소비와 새 자연 연구 생산은 별도 수용이며, 기존 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)의 **2026-10-26 07:40~08:00**, source23 종료·봉인/native generation 후 고정 입력 재소비·A17~44 날짜/누적·scope별 비교를 OPEN으로 유지한다. 새로운 날짜나 선택본에서 배포할 때는 그 시점 native handoff/P5/date/selection 재검증을 따른다.

### 배포 후 실제 PID의 정책·연구 코드 검증 — 2026-10-23

**결정: 사용자 배포·재기동 뒤 실제 선택97a72d632/PID3606961/start38501423의 정책 소비와 d53c36e59 연구 코드 반영을 검증했다.** 현재 실행본은 준비본d53의 후손 `97a72d6326d4d8e64e085e3320c11566ff56c58e`, root는 `/home/ubuntu/KORStockScan-runtime-releases/weakness-rest-integrated-20261023-97a72d632`다. 선택16:25:29·PID 영수증16:28:22와 `/proc`의 PID/start/cwd가 일치한다. 준비본 변경14파일은 현재 source·Git bytes와 전부 동일하며 runtime source는 clean이다. 후속 delta6파일은 별도 weakness/cron/test 변경이고 연구 통합 파일은 덮어쓰지 않았다. [코드·PID 결속](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/integration-code-verification.json).

선택본의 native `intraday_release_handoff --verify --target-date 2026-10-23 --pid 3606961`를 documented native custody environment로 실행한 결과 **PASS/findings[]/actual_pid_consumed=true**다. manifest `131abef39e624b33cd9394e1397d224aa52a1d2dbc7a1479fa345e6a1e0b7ef6`와 원 handoff/소비·PID identity를 함께 검증했다. 비밀 account/journal 값은 출력하지 않았다. candidate P5 `da7cb52aa8674d0fb0607f86fa2912fa`와 selected P5 `9cf4e72b2aa74623989271ba5817f9c2` 모두 passed·load_check_passed·자식 종료다. 기계128scope와12종 소비자의 정책 hash는 준비 당시와 동일하며 기계/보조 bundle은 `1d9e5b0924fec60f473bea1b4a8a51ed8bc242f3af533c592e1a04342726e7b6`다. 실제 Main 로그16:28:28의 `[MAIN_POLICY_STARTUP] current policy reader verified`도 확인했다. 로그 한 줄 자체에 PID가 있다는 주장이 아니라 native PID/start/cwd·소비 영수증과 함께 결속했다. [native PID 재검증](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/native-pid-verification.json), [정책·P5 대사](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/matching-policy-and-p5.json), [bounded 기동 로그](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/main-startup-log-projection.json).

선택된97a source에서 기존 생산자·소비자 회귀 **72 PASS**다. 원159개는 준비 당시 봉인 자료의 hash를 검증해 읽고, live DB 발견과 network 연결을 금지한 채 선택본 consumer로 다시 계산해 W6/STOP2/TIMEOUT9/U142가159/159 일치했다. 원 보고서/DB/정책은 재생성하지 않았고 이번 검증의 provider/주문/재배포·재기동0, 코드 수정0이다. 재현된 이 범위에서 새 수리 대상은 없으며 기존 consolidated/retained 처분도 그대로다. [선택본 회귀](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/selected-source-consumer-regressions.log), [선택본 실제 입력 재소비](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/selected-frozen-source-replay.json).

현재 observer16:31은 같은97a/3606961·38501423 actor birth를 결속한 current publication이지만 semantic 상태는 **partial**, `current_observation_verified=false`다. health16:32:46의 process/log/auth/resource/lock은 PASS이며 artifact 및 cron 경고는 유지한다. 별도 auxiliary research-only source22 보고서의 code-generation은507700d0, 현재 native generation은8659bf21로 달라 원 `policy_generation_unverified`와 원 owner unresolved를 보존한다. 이는 과거 연구의 현 코드 capability 결속 미완료이며 위 실제 기계/보조 정책 소비 PASS와 구분한다. 원천 age/gap/incomplete 관측과06:50 이후 복구된 finalization 경고도 전체 GREEN으로 바꾸지 않는다. [동일 시점 observer 원 bytes](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/observer-snapshot.json), [health 원 bytes](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/health-snapshot.json).

연구 저장·소비 코드는 배포되어 선택본에서 직접 검증했으나, Main PID가 offline 장후 연구를 자연 실행했다거나 source23 native 생산·봉인·최종 소비가 완료됐다고 하지 않는다. 기존 [MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용)의10/26 07:40~08:00 OPEN에서 source23 자연 generation·고정 REST 입력 재소비·날짜/누적 비교를 확인한다. 현 코드의 연구 generation/fixture 결속과 과거 연구 경고도 그 증거와 별도로 재확인하며 stale PASS로 대체하지 않는다. [최종 검증 결과·잔여 경고](../../tmp/main-machine-rest-history-integration-20261023/postdeploy-97a72d632/result.json). 이번 작업은 비테스트 source/test 추가·삭제0이며 기존 감사/checklist만 갱신했다.


## Probe source and five-second latency integration — 2026-10-27

- Owner: `MainEntrySourceTerminalRepair1022`. User approved integration of `50dc2f84d`, ordered restart, source diagnosis and exact REGULAR/SOR/_AL natural timing validation. Baseline `bcfedb8ad`, PID295584/start71535364. Keep the original five-second signal lifetime, policy, provider, custody, route, account/order/quantity and hard safety contracts.
- Bounded native source-window reconciliation from12:14 through12:47:77 probe receipts/76 symbols, all producerPID295584. Reasons:17 route snapshot missing,38 native history with stale current source,9 trade age exceeded,2 missing trade,11 observed no matching pattern. Exact item/lease, local REG request, source hash, transport epoch and terminal clocks are preserved in [reconciliation](../../tmp/probe-latency-integration-20261027/source-reconciliation-before.json), backed by frozen native projections and generation/byte receipts.
- Wire and normalized receipt counts agree in all77. All49 native sequence comparisons agree.58 available wire-to-native clock pairs have median1.589ms/max6.917ms. These observations reject a general internal delivery-loss explanation in this bounded cohort; they do not certify every packet or a broker execution venue.17 exact leases saw neither0B nor0D; connection-level success lacks item attribution, so quiet trading versus item registration/upstream receipt failure remains unproved. Preserve these gaps and unknown values.49 native samples distinguish current no-match from stale history; no stale row receives decision authority.
- `50dc2f84d` consolidates the public family assessment body under `_assess_validated`; only loader-issued immutable families reuse structural proof while source dependencies are rechecked. Mutable/forged/evicted families retain full validation. `_IdentityPass` removes the duplicate leaf metadata syscall; fresh leaf checks, symlink/ancestor/cached generation checks remain. BUY report call completion owns its exact terminal, and later unbound watch gates form a separate cycle. Old exact preparation readers remain for native predecessor custody. No new production module, dispatch, policy or threshold.
- Re-review: original runtime738 +independent preparation173 regressions and128-scope native parity retained; additional runtime/probe/ordered transition625 PASS and quantity/history/new-loss negatives95 PASS. Offline native execute verifies lock scope, preparation-before-start, failure unwind/no start, current observer before health. Candidate source is clean; original five-second guard and assessment predicates are unchanged.
- First ordered attempt stopped in preflight before any startup hold/drain/selection: `quantity_monitor_manifest_invalid`. The candidate loader hash is a declared dependency of the source10/26 quantity monitor projection; the exact candidate proof had not been prepared. The native projection producer revalidated the existing stage/report, published only the candidate code-scoped manifest (`publish_current=False`), and passed the same deployment currentness consumer in44.804s. Original report, stage, selected manifest, quantity policy and selector hashes are unchanged. Historical exclusion IDs/hashes/null remain. [Native proof](../../tmp/probe-latency-integration-20261027/quantity-candidate-projection.json).
- Preserve the failed transition directory and logs. Use a new clean documentation successor containing50dc2f84d for the next native ordered attempt; do not remove/rename the original failed transition or bypass its exclusive generation directory. Before restart, revalidate candidate quantity/trailing currentness, exact active-policy custody, candidate P5 and original selector/PID. After prepare, validate the selected P5 before start; then attest the actual PID and publish current observer/health.
- Baseline→50dc2f84d delta: non-test source+140/-16; tests+203/-1; docs0. This integration adds only evidence and existing-owner progress; production sources remain byte-identical to50dc2f84d. Natural Main acceptance/submit preparation and latency improvement remain OPEN until matching current-PID REGULAR/SOR/_AL signal/request/terminal clocks occur. No order or subscription is created for acceptance. Remaining no-wire source ambiguity stays OPEN under the same owner; current or unknown loss remains detectable.

- Linked auxiliary capability follow-up: `50dc2f84d` also changes `continuous_reversal_policy_v6.py`, a declared auxiliary report dependency. Current capability was unverified (`82a2c8b...` original versus`9fb5d5b0...` current); the original six consumer regressions failed. Extend the existing frozen-input successor table only for the exact10/23 and10/26 originals, with both old and fresh native fixture evidence still required. Update the existing independent preparation and complete intraday code profiles; retain the consumed latency profile as historical custody. No report/source/policy rewrite or new wrapper/owner. Re-review plus218 targeted regressions PASS, including tampered/missing source or fixture, unknown origin/current code and mixed/dirty complete-generation rejection. Source delta+58/-0; tests+40/-2. Existing generic consumer negative tests are reused. Fresh native auxiliary fixture and all four current report consumers precede final successor deployment.
- Intermediate transition: `cd2eb9ea1` includes50dc2f84d and completed native ordered deployment13:09:28. Main557509/start71862400 attested13:08:57; current WebSocket producer agrees. Candidate/selected P5 and current observer publication passed. This is intermediate PID evidence while the report capability follow-up is prepared, not the final-PID natural latency acceptance.

### Final integrated deployment and bounded natural observations — 2026-10-27

`50dc2f84d` is an ancestor of the selected clean integration `6d0d197562c67ebdf5cd3524e71001c5257eb603`. Native ordered transition completed13:27:29; Main670131/start71972259, cwd`probe-latency-20261027-6d0d19756/src`, actual policy consumption attested13:27:03 and independently verified PASS/findings0. Candidate P5`c2cc69467b9749d9b3cd428a4564fc1a` and selected/prepared P5`e340bb372eac4928b0f851bc20f45519` both passed. All four current report capability consumers verified; fresh auxiliary fixture107 PASS follows the218 regressions. Original quantity stage/replay/selected manifest/policy hashes remain unchanged. The original failed50dc transition remains preserved. [Transition and actual PID evidence](../../tmp/probe-latency-integration-20261027/capability-complete/postdeploy-summary.json), [native PID verification](../../tmp/probe-latency-integration-20261027/capability-complete/actual-pid-native-verification.log).

The new actor's WS producer/root/commit/transport matched;10 registered `_AL` items had20 current-transport0B/0D receipts. This confirms reception in that bounded snapshot, not every lease, physical execution venue or a holding branch: there were no active holdings. An earlier read-only snapshot check stopped on age>15s; its failure is preserved, and a later independently refreshed native snapshot passed without changing the freshness guard. [Source observation](../../tmp/probe-latency-integration-20261027/capability-complete/market-consumption-current.json).

By13:37:17, the exact actor had22 probe receipts:6 route snapshots missing,2 trade-age guards,3 observed history with source gaps,5 stale-current histories,5 current no-match and1 confirmation still pending at residence end. Wire/normalized counts agree22/22;14 comparable native sequences agree, none disagree.16 available0B packet-to-native endpoints have median2.037ms/max4.219ms. The6 no-wire leases are377330/235cbce5c5794a00a020f88b216fc36a,299170/d5ac1c5959e549cfbc8b61901844a3db,037030/0a6490380c0d4662a4133848879892ca,036170/5d33b8f37d7a4a4c91863c19caee8bc8,065530/a5ac1b4a0572498085fd945a95e45b47,011370/a514777572fb4dff9dff3690da0581c5. Each keeps its source discovery hash, local REG request, exact`krx_nxt_integrated`/`_AL`, transport1793075205230016 and PID670131. Broker item ACK remains null; neither these6 nor the prior actor's17 no-wire leases are certified as quiet trading or repaired historical input. Discovery hashes are not tick-row hashes; derived field hashes are not original line-byte hashes. [Exact reconciliation](../../tmp/probe-latency-integration-20261027/capability-complete/source-reconciliation-current.json).

A separate current source incident is distinguished from sparse trading:350 timestamp-rejection records across10 symbols, local collector epoch1793075205160548119, preserve exchange13:27:46–13:27:55 and application ingress13:28:04.354–13:28:05.429. Exchange-to-ingress lag10.309–18.560s; packet-to-normalization median1ms/max120ms, rejection-check median1ms/max130ms. All stayed excluded by existing guards. The journal prefix SHA is`23b5a471bb94d09a041c657fbada45d17539d87c81353db6f25c6577b3ade886`; it is a live prefix, not a fabricated terminal seal. Instrumented snapshot-lock wait max38.409ms and Main-loop work max3.813s do not identify the earlier18s gap. Upstream, network and application receive scheduling remain unproved alternatives; no API/normalizer/guard change is justified by this evidence alone. [Clocks and exact rejection originals](../../tmp/probe-latency-integration-20261027/capability-complete/timestamp-delay-reconciliation.json).

Natural latency improvement is **not demonstrated**. Samsung005930/SOR/_AL/REGULAR generated3 exact async requests at native sequences2950/2962/2966, with2 evaluation traces (`aims-b5d5a87f778e63b28405`, `aims-59079585f0104924f94e`). First ENTER_NOW reached a provider with729ms remaining and ended unavailable/expired; the next evaluation encountered the existing transport circuit, and the third request ended before a valid evaluation. All3 were rejected as`result_not_commit_eligible`; Main acceptance/submission preparation was not reached. Every native revalidation preserves original deadline minus signal epoch=5.0s. Approximate same-PID epoch/perf projection gives signal-to-claim3.32/4.36/4.76s; coordinator-ready to Main guard277.458/63.392/161.805ms. These are distinct stages, not additive policy timings or proof that a different threshold would help. [Exact natural joins](../../tmp/probe-latency-integration-20261027/capability-complete/natural-latency-join.json). The compact header reader initially returned0 because its verified cursor preceded these events; the native forward-window reader plus bounded raw suffix supplies6 exact dispositions, preserving the coverage distinction.

The last completed native artifact check13:39:42 has6PASS/1WARNING/0FAIL, including artifact freshness PASS with the existing verified-wait exception. The later13:41:21 sweep has4PASS/3WARNING/0FAIL: I/O wait32.01% and artifact validation deferred for resource contention, alongside the historical cron warning; process/PID consumption remains PASS. Preserve both observations, not a single GREEN claim. Decision/source coverage remains partial. Historical postclose recovery after06:50 remains a warning. Initial resource-contention deferrals were retained; no health artifact was forced to PASS. Source age/loss, unknown ACK, new generation and original deadline guards remain active. The current source-delay cause and Main pre-claim time attribution stay OPEN under`MainEntrySourceTerminalRepair1022`, next current window13:40–15:20 REGULAR/SOR/_AL;16:05–16:15 AFTER applies only to its separate route/session acceptance. Continue exact native receive timestamps and Main phase/claim/request/terminal joins; no new order/subscription or TTL extension to manufacture acceptance.

Replacement/removal: assessment-body ownership is consolidated in`_assess_validated`, duplicate leaf-stat removed, call-local terminal ownership retained, exact auxiliary successor pairs added to the existing owner. Previous complete code profiles are retained for consumed predecessor/history readers. No new production module/wrapper/registry or retired authority. Baseline`bcfedb8ad` to selected6d0: non-test source+198/-16, tests+242/-2; final documentation delta is recorded in the completion manifest. Source growth is exact historical capability pairs/profiles and guarded proof reuse; no policy value or scope expansion. Managed releases152→154 and registered worktrees255→258, deletion0; native inventory has no configured directory/worktree count cap, service-unit256 and historical-origin discovery256 are distinct.16GiB working reserve and2 recovery copies were reserved; final free space65,713,979,392B. [Inventory](../../tmp/probe-latency-integration-20261027/capability-complete/inventory-after.json).


## Preclaim guard and exact lease causal follow-up - 2026-10-27

Owner: `MainEntrySourceTerminalRepair1022`. Baseline code `76e232fe7` is the documentation successor of selected `6d0d19756`; source is identical. Actual actor is Main670131/start71972259, REGULAR, policy cohort KRX, data `SOR/005930_AL`, requested broker SOR; actual exchange remains UNKNOWN. Latest user scope is preparation only: no restart, drain, startup hold or selector publication. Preserve Main670131 and selected6d0. Guard/TTL/provider/policy changes are not authorized.

- The original six empty leases are 377330/235cbce5c5794a00a020f88b216fc36a, 299170/d5ac1c5959e549cfbc8b61901844a3db, 037030/0a6490380c0d4662a4133848879892ca, 036170/5d33b8f37d7a4a4c91863c19caee8bc8, 065530/a5ac1b4a0572498085fd945a95e45b47, 011370/a514777572fb4dff9dff3690da0581c5. Exact discovery hashes, original rows and registration receipts remain in [original reconciliation](../../tmp/probe-latency-integration-20261027/capability-complete/source-reconciliation-current.json). All six are current KRX eligible and non-NXT; other non-NXT symbols received `_AL`, so this does not prove an unsupported route. Same-connection SOR peers produced respectively333/296/300/305/246/295 accepted rows during these lease intervals, with zero matching item rows. [Bounded source offsets, IDs and SHA witnesses](../../tmp/probe-latency-integration-20261027/causal-followup/lease-peer-reconciliation.json). This excludes whole-connection silence during those intervals, not item-specific registration failure or legitimate quote/trade silence. Exact item ACK stays null; no backfilled normal/no-trade receipt.
- Separately, the startup source has an18.180s application-receive gap followed by350 stale rows across10 symbols. Their exchange-to-ingress age is10.309-18.560s, while subsequent normalization is mostly1ms. The original six intervals are outside this gap. [Bounded accepted prefix](../../tmp/probe-latency-integration-20261027/causal-followup/startup-ingress-window.json) and [preserved rejections](../../tmp/probe-latency-integration-20261027/capability-complete/timestamp-delay-reconciliation.json) do not distinguish upstream/network from event-loop/process scheduling. Keep this cause OPEN; no stale guard or timeout relaxation.
- Three Samsung signals are one overlapping episode, not three independent opportunities. Main first visited them in31.804/7.555/20.927ms, then an actual extreme-sell guard blocked them. The native rule is an8s window, both buy ratios <=.35 and negative net buy quantity. First/second recorded ratios were about.13, net quantity about-23,000; at13:36:48.959 the ratios were.42 and the guard continued. First claim followed about37ms later. Therefore3.328/4.359/4.759s signal-to-claim is not all scheduler latency. Same-symbol in-flight ownership also consumed later signals' original budgets. [Exact guard event window](../../tmp/probe-latency-integration-20261027/causal-followup/guard-window.json).
- Initial-signal and guard-clear asks were both221,500. Same absolute exit times have zero entry-price difference. Observed bid marks after5/30/60s were unchanged; after5min they were lower, after30min higher. With the exact request's declared.0023 cost assumption, the initial mark at5min is-.4557% and at30min+.4472%. These are counterfactual quote marks, not fills, broker-confirmed costs, trailing strategy returns or independent holdout evidence. This episode neither proves excessive guard blocking nor establishes positive economic protection. [Source-bound comparison](../../tmp/probe-latency-integration-20261027/causal-followup/guard-quote-comparison.json). Keep the5s deadline and safety thresholds; sufficient service time after a delayed claim remains unproven.
- A separate classification defect is reproduced: after local preparation exhausts the deadline, `EntryTransportCircuit.admit()` returns None even with state CLOSED; the AI owner labels every None as `entry_transport_circuit_open`. Native circuit evidence has CLOSED/generation0/failures1/threshold5/unsettled0. [Current actor receipt](../../tmp/probe-latency-integration-20261027/causal-followup/current-performance-1420.json). The original full producer-to-trace regression fails with `entry_circuit_open` instead of `entry_deadline_expired`. Repair checks the same remaining budget at admission and uses the existing local-deadline terminal; no provider call, failure increment, reset, key rotation or budget renewal.

Implementation and replacement review:

- `record_native_preclaim_guard` is replaced by `record_native_preclaim_gate`; no old forwarding alias remains. Existing first-guard evidence stays intact; bounded last blocked visit/count, actual continued visit and numeric inputs join the same signal/item/epoch/deadline. Missing/nonfinite values remain null. Discrete visits are not treated as continuous blocking or broker/Main acceptance. Existing callers/tests migrate; remaining Main safety gates still run.
- Existing Main phase-window owner retains aggregate duration for the entire observed window while detailed intervals stay bounded to32. Missing prefixes remain unobserved. Native lifecycle snapshots copy the bounded recent rows so review consumers cannot mutate their evidence.
- Existing WS exact-receipt owner now requires the packet's original transport epoch; a late old-connection packet cannot become a new lease's receive witness. Per-connection route/type counter baselines bind peer activity to the exact lease without extra subscriptions or per-packet scans over all leases. Peer traffic never proves item ACK or no-trade. Existing normalization and first-missing-boundary classification stay intact.
- Existing WS receive loop and runtime-performance owner separate monotonic receive-await and handler times, same-thread CPU and wall-clock changes, retaining only32 slow completed cycles. Await time explicitly includes unresolved network/upstream/event-loop/process scheduling. No new worker, request, retry, timeout or registry. Missing future samples remain OPEN.
- Official Kiwoom HEAD953e5dbff123f437ab4d11a78a95191a685eb51f was rechecked; relevant spec/core/realtime/Postman paths and hashes are in [reference gate](../../tmp/probe-latency-integration-20261027/causal-followup/official-reference.json). No upstream request/FID/control semantics change.
- Review caught mutable snapshot exposure and backward gate-visit clocks; both were corrected and covered. The large whole-file formatter consumed unnecessary resources and was terminated at14:17; preserve its log and exclude the14:16 request from latency-improvement comparisons. Bounded targeted compile/diff checks replace repeating that formatter.

Code/test closure, candidate readiness, deployment, actual PID consumption, natural acceptance and economics remain separate. Under the latest preparation-only instruction, finish a clean immutable candidate, native active-policy handoff and isolated candidate P5 without changing the selected release or Main. Exact new-PID REGULAR/SOR/_AL gate/claim/request/Main terminal evidence remains OPEN until a later authorized transition. If a transition is later authorized today, the remaining regular window ends15:20; otherwise the next regular acceptance window is2026-10-28 09:30-10:00, subject to native calendar and actual selection. AFTER16:05-16:15 cannot close the regular branch. Original six no-wire causes and startup ingress stall remain OPEN; source/ACK/null and new-loss detection are preserved. No order or subscription may be manufactured for acceptance.

Shared handler changes also invalidate rising-missed and holding-vote capability generations. The existing code-handoff owner receives exact original-to-successor pairs, with full reviewed dependency profiles in both deployment and independent preparation readers. Historical generations remain accepted only through their complete original profiles. Fresh native fixtures are required; original reports are not regenerated or marked economically complete. The full affected run passed1409 cases with one new-test fixture setup failure; adding its omitted stale-metadata precondition produced21/21 targeted passes, including real producer, trace, report consumer and unchanged circuits. Exact-profile and independent preparation regressions passed142 cases; six historical-profile fixture cases initially lacked the entry_capability commit mapping, then passed6/6 after restoring that fixture mapping. Capability regressions passed1668 cases; one obsolete auxiliary expected hash was corrected to the already-deployed10/26 original, then all4 current-family cases passed. Original failure logs are retained. No product acceptance list was broadened for these fixture failures. Native candidate evidence is recorded separately under the preparation directory.

Replacement accounting against76e232fe7: non-test source+259/-19, tests+224/-17; documentation additions are recorded in the final preparation manifest. No production module, process, worker, CLI or registration was added. Source growth is bounded diagnostic fields and exact reviewed historical/source profiles; the former preclaim helper was removed, existing wire/phase/circuit owners retained and corrected. The new natural-data requirements stay with MainEntrySourceTerminalRepair1022; no parallel tracking or inferred source recovery.
