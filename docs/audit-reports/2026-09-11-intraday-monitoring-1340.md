# 2026-09-11 장중 모니터링 13:40 종료 리뷰

관찰 구간은 `2026-09-11 13:15~13:40 KST`다. 사용자 요청에 따라 [장중 지시문](../intraday-monitoring-task-instructions.md)의 현재 owner, 배포/PID, Entry AI, submit/exit, 독립 매매기계, broker custody, source quality와 도래한 체크리스트를 점검했다. 이번 실행에서는 코드·정책·env·주문을 변경하거나 process를 재기동하지 않았다.

## 판정

**Intraday Control State: YELLOW.** 메인과 독립 매매기계의 R2 형상 통일, V2.14 실제 호출, broker reconciliation과 process-health는 유지됐다. 메인에서는 V2.14 `WAIT + probe intent`가 실제 1주 주문과 짧은 양수 runtime exit로 한 번 연결됐다. 반면 daywide funnel은 모든 제출 bundle이 probe-only인 `SUBMIT_DROUGHT_CRITICAL`이다. 독립 기계의 자연 신호 네 건은 `machine_entry_adverse_flow_v1`의 exact 0B/0D freshness·checkpoint/pre-transport 조건에서 broker 전송 전에 끝났지만, 저빈도 체결 종목을 제외해 청산 유동성과 자본 회전을 보호한 의도된 차단으로 판정한다. 비용 차감 누적 순익과 전체 기계 경로의 경제적 효과는 아직 닫히지 않았다.

## 배포·process·자원

| Owner | 13:40 상태 | 근거 |
| --- | --- | --- |
| Main | PID `363990`, start `13:07:36`, cwd `/home/ubuntu/KORStockScan-runtime-releases/unified-scalping-r2-20260911/src`, commit `57a90bd9`, runtime verify PASS | 마지막 관찰 `13:39:52`, process `Sl+`, detector PASS |
| Continuous widget/collector/notifier | R2 root에서 active | widget `364143`, notifier `364154`, Samsung/Doosan/Hanwha/widget-symbol/research collectors의 R2 소비를 재확인 |
| Samsung midday | PID `371354`, active/running, Result success | `13:14:00` 시작, state `READY`, position/order 없음 |
| Low-price midday | 예약 profile들이 R2에서 시작. 일부는 정상 window 종료, Hanse/NHN/SamsungE&A/SD Biosensor는 13:40에도 진행 | actual service root와 state를 대사 |

메인 RSS는 약 `1.16 GiB → 1.35 GiB`로 증가했고 CPU는 한 core 수준이었다. 시스템 available memory는 약 `4.0 GiB`, swap 사용은 `3.2 GiB`였다. `13:34` I/O wait가 순간 `19%`까지 올랐으나 이후 `2~5%`로 돌아왔고 blocked process나 detector 실패는 없었다. 13:14에 시작된 별도 전체 snapshot PID `372269`가 만든 13:16~13:17 resource 경보는 그 작업 종료 뒤 13:18부터 회복됐으며 13:39 detector도 PASS였다.

`systemctl --failed`의 세 unit은 새 crash가 아니다. `cj_cgv_morning`의 지난 window 기록과, `sk_telecom_midday`의 비용 경제성 비양수 및 `youngone_midday`의 profile revision 필요를 표시하는 사전검증 quarantine이다. 이를 늦은 재기동으로 보충하지 않았다.

## Main V2.14·작은 수익 경로

R2 시작 뒤 13:40 이전 `ai_confirmed` V2.14 trace는 13건이다. 6건이 Provider를 실제 호출해 6건 모두 parse 성공했고, 7건은 input preflight에서 차단됐다. 최종 action은 `WAIT 4 / DROP 9`, probe intent는 1건이었다. Provider 호출 6건은 모두 activation hash `14d30e97aa9b320d216419390d812ff174107e3f9e64a68a69639a0ec3301a2f`와 `active_bounded_krx_canary`를 기록했다.

그 1건은 한국화장품제조(`003350`)다.

- `13:11:43` V2.14/OpenAI/parse PASS, `WAIT + entry_probe_intent=true`
- `13:11:43` 1주 주문 `0045363` 제출·체결, 매수가 `16,000원`; `13:11:54` bundle terminal 기록
- `13:12:54` `FAST_EXIT trailing_peak_worsen_floor` 발동
- `13:12:55` 매도 주문 `0045452` 제출, `13:13:01` `16,210원` 전량 체결. 원시 가격수익률은 `+1.31%`, runtime `profit_rate=+1.08%`, 가격차는 `+210원`

고정 비교비용 23bps만 적용하면 약 `+173원`으로 양수지만 slippage와 exact broker fee/tax receipt가 아직 결속되지 않았다. 따라서 headline 실현 순손익은 `null`이며 이 한 건으로 경제성·프롬프트 우월성이나 drought 해소를 승인하지 않는다. 다만 **“비용을 차감하고 작은 수익을 빈번하게”**라는 목표에서 V2.14의 `WAIT + bounded 1주 probe → trailing exit` 실행 가능성이 이번 관찰에서 직접 확인된 유효 사례다.

반대 사례로 흥구석유(`024060`, 기존 1주)는 `13:29:18` AI 판단 불가 상태의 소프트손절 신호 뒤 주문 `0046685`로 `15,180원`에 전량 체결됐다. 매수 `15,700원`, 원시 가격수익률은 `-3.31%`, runtime `profit_rate=-3.54%`이며 exact 비용 손익은 `null`이다. 두 거래를 합산한 비용 후 순익은 broker 비용 대사 전에는 보고하지 않는다.

한국화장품제조의 당시 reaction context는 계산됐고 `fresh_short_window`였지만 telemetry는 `payload_included=false`, `confirmed_sent=false`, `internal_consumed=false`였다. V2.14의 현행 deterministic setup payload 경계를 따른 결과로, ask-depletion 원자료가 AI 판단에 직접 소비됐다는 증거는 아니다. 이 경계와 별개로 tick/quote feature는 전송됐다.

## Submit drought와 scanner/BBO

`13:40:03` sentinel은 `event_count=3557`, 최신 event `13:40:02`, source-quality `warning_excluded_rows` 22건이다. daywide economic participation은 bundle 9건, requested 39주, submitted 9주, source-quality-valid 9건이며 9건 모두 probe-only이고 full submitted bundle은 0건이다. 판정은 계속 `SUBMIT_DROUGHT_CRITICAL`이다. 현금·신규진입 배정자금 부족은 앞서 수리한 별도 제외 계약으로 drought 원인에 섞지 않았다.

공식 보통주 master는 R2 배포 점검의 2,604종목과 census primary missing 0을 유지했다. 이번 구간에 독립 market-wide recall의 새 maturity가 닫히지는 않았다. 기존 주요 forward KRX BBO `63/78`, shared-read budget defer 14·invalid BBO 1과 capture cadence/forward maturity 결손이 남아 있으므로 scanner coverage 정상은 계속 미확정이다.

## 독립 매매기계 micro/adverse-flow 자연 결과

13:40까지 네 profile에서 신규 signal이 발생했지만 broker accepted order는 0건이고 최종 broker 미체결도 0건이다.

| Profile | signal_decision_at | 결과 | 최초/직접 결손 |
| --- | --- | --- | --- |
| CJ CGV midday | `13:28:03.951` | 두 leg 모두 `SKIP_SOURCE_UNAVAILABLE`, submit attempt 0 | 0/1/3/5초에 trade watermark 및 depth freshness 결손 |
| TYM midday | `13:29:04.647` | 두 leg 모두 `SKIP_SOURCE_UNAVAILABLE`, submit attempt 0 | 0/1/3/5초의 depth/trade watermark 결손; 3초에도 starting depth stale |
| KEPCO midday | `13:34:05.382` | registry intent 뒤 모두 `ENTRY_ADVERSE_NOT_SENT`, broker order 0 | 일부 1/5초 window는 `CONTINUE`였으나 3초 checkpoint miss와 최종 pre-transport fresh source 미충족 |
| SK Eternix midday | `13:39:00.426` | registry intent 뒤 모두 `ENTRY_ADVERSE_NOT_SENT`, broker order 0 | 일부 0/3초 window는 `CONTINUE`였으나 1초 miss와 최종 pre-transport fresh source 미충족 |

0B·0D 등록 자체는 존재하고 동일 `_AL|krx_nxt_integrated` route의 snapshot도 갱신됐다. 관찰 중 0B/0D 최대 interarrival gap은 CJ CGV 약 `68.8초`, TYM 약 `93.5초`였고, live 계약의 최대 source age는 `1.5초`다. manager load·REG·writer 결손 없이 최근 0B 체결만 오래 비어 있었으므로 이 결과는 **저빈도 거래 종목을 진입에서 제외하는 의도된 유동성·자본회전 guard**다. 매수 후 빠르게 빠져나오기 어려운 모집단을 늘리지 않는 현재 목적에 부합한다.

이 조건은 승인된 `machine_entry_adverse_flow_v1` 설계가 source gap을 `SKIP_SOURCE_UNAVAILABLE`로 종결하도록 명시한 결과다. 이번 표본에는 fallback·freshness 완화·코드 수리가 필요하지 않으며 `intended_liquidity_and_turnover_safety_block`으로 보존한다. 네 자연 signal이 모두 broker 전송 0으로 끝난 사실만으로 구조적 모집단 고갈이나 runtime 결함을 만들지 않는다. 21:15 attribution/timing producer는 source-qualified `CONTINUE`, 저빈도 체결에 따른 source-unavailable, 그 밖의 실제 source-quality 결손과 pre-transport 차단을 서로 다른 분모로 집계하고, 전체 기계 경로의 비용 후 EV·회전 효과만 기존 owner에서 계속 확인한다.

## Broker·custody

`13:39:09` KRX+NXT read-only 대사 결과는 다음과 같다.

- 보유: 삼성전자 `005930` 25주, 우리기술 `032820` 1주, ICTK `456010` 1주
- 미체결: 0건
- 주문가능금액: 운영 floor 적용 `3,000,000원`; raw `526,465원`, floor provenance `operator_approved_2026_07_22`
- 우리기술·ICTK 각 1주는 registry 기준 external/manual remainder로 보존됐고 balanced=true다. ICTK의 수동관리 handoff는 자동 hard-stop 오류에서 제외하는 기존 정책을 유지했다.

13:08 대사에 있던 흥구석유 1주의 감소는 위 메인 매도 `0046685`와 일치한다. 독립 기계가 타 owner 보유를 흡수하거나 취소한 근거는 없다.

## 체크리스트 대사

| ID | 13:40 판정 | 이번 점검과 잔여 acceptance |
| --- | --- | --- |
| `MachineFillTelegramAcceptance0911` | `waiting` | notifier active. 구간 내 widget/episode 실제 fill이 없어 자연 수신 표본은 0; 20:00까지 OPEN |
| `MachineProfitStagnationStartupAcceptance0911` | `running/open` | R2 기동·정책 pin·자연 signal은 확인. 신규 machine fill/보조청산 및 비용 경제성, 14:35 through-window가 남음 |
| `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0911` | `open/source-warning` | observer canary healthy·stop_required=false, queue/drop/writer error 0. timestamp pre-enqueue exclusion의 전수 receipt coverage가 닫히지 않아 through-close OPEN |
| `RuntimeEnvIntradayObserve0911` | `open` | R2/V2.14 실제 호출과 1주 submit/두 exit 확인. drought, scanner recall과 exact 순익은 OPEN. 저빈도 machine 차단은 의도된 유동성·자본회전 guard로 수리 대상 아님 |
| `SimProbeIntradayCoverage0911` | `completed_scope_preserved` | 09:54 점검 receipt 재사용. 새 authority leak 없음; 재실행하지 않음 |
| `IntradaySourceQualityGateCheck0911` | `not_yet_due` | `14:20~14:35` window 전이므로 조기 raw audit 미실행 |
| POSTCLOSE owner | `not_yet_due` | 16:25 이후 설치 owner를 따름. machine 저빈도 차단은 결함 경보가 아니라 경제성·회전 attribution 표본으로 기존 `MachineLifecycleTurnoverObjectiveFollowup0911`에 전달 |
| `MachineOneDayQuantityExpiryAcceptance0914` | `not_yet_due` | 9/11 한시 신규 1주 override의 다음 거래일 만료·기본 수량 복귀 확인은 `2026-09-14 07:55~15:30` owner에 보존 |

현재 시각까지 OPEN과 미래 due를 모두 분류했으며 미분류는 0이다. `MachineProfitStagnationStartupAcceptance0911`의 관찰창이 14:35까지이므로 이 보고서가 해당 owner 전체를 닫지는 않는다.

## Review gate

이번 변경은 관찰 보고서와 기존 체크리스트의 receipt 보완뿐이다. 코드·runtime·policy에는 변경이 없다. 저빈도 체결을 정상 `CONTINUE`로 허용하는 완화안은 채택하지 않았고, 격리 worktree의 검토 중 변경도 모두 되돌렸다. 문서 링크/owner/권한을 재검토하고 print-only checklist parser와 `git diff --check`로 검증한다. Provider 재호출, report 재생성, Project/Calendar sync는 수행하지 않는다.
