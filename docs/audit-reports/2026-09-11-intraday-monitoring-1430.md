# 2026-09-11 장중 모니터링 14:30 종료 리뷰

관찰 구간은 `2026-09-11 14:14~14:30 KST`다. [장중 지시문](../intraday-monitoring-task-instructions.md)에 따라 메인·독립 매매기계, broker/custody, source quality, micro observer와 현재 시각까지 도래한 체크리스트를 점검했다.

## 판정

**Intraday Control State: YELLOW.** 메인 PID는 정상이고 broker 전시장 잔고·미체결 대사는 닫혔다. 위젯과 한국전력 episode에서 자연 BUY/SELL 체결 및 Telegram `sent/message_id`가 생겼다. 한국전력은 1주를 `33,050원`에 매수해 원 목표 `33,250원`에 매도했으나, exact broker 비용이 없어 순손익 headline은 `null`이다. 메인 drought는 bundle 10건이 모두 probe-only라 계속 critical이다.

두 가지 잔여가 있다. 14:20 raw 감사에는 hard contract gap이 없었지만 입력 파일이 감사 중 append되어 canonical 결과가 fail-closed됐다. 또한 한국전력 owner registry에는 exact 매도 체결금액·시각이 있으나 episode state가 이를 투영하지 않아 장후에는 설정 목표가 proxy만 남고 exact broker-price·보유시간/micro timing cohort에서 탈락할 결함을 발견해 코드 수리를 review finding 0으로 닫았다. 병행 세션이 14:18 이후 배포 세대를 계속 갱신했으므로 이번 수리는 실행 중 release에 덮어쓰지 않고 `deployment_pending`으로 둔다.

## 런타임·배포

- 14:30 메인 PID `363990`, start `13:07:36`, CPU 약 한 core, RSS 약 `17.4%`; `/home/ubuntu/KORStockScan-runtime-releases/unified-scalping-r2-20260911` commit `57a90bd9`를 계속 소비했다.
- 병행 승인 작업은 14:17:57에 selector와 systemd 경로를 `/home/ubuntu/KORStockScan-runtime-releases/target-pressure-audit-20260911` commit `66a3189b`로 전환했다. widget PID `452008`, Samsung afternoon `452023` 및 현재·후속 low-price episode는 새 root를 소비한다. main은 시작 세대가 유지되며 자동 reload된 것으로 세지 않는다. 자세한 receipt는 [목표가 pressure 배포 리뷰](./2026-09-11-target-pressure-audit-evidence-deployment.md)다.
- 14:30에 예정된 afternoon episode 10개와 Samsung afternoon, widget/collector가 active였다. 신규 crash/restart loop·중복 owner·미체결 주문은 없었다.
- micro forward collector는 14:30:18까지 갱신됐고 `healthy_observer_canary_with_source_row_exclusions`, `stop_required=false`였다. timestamp rejection은 pre-enqueue에서 차단되지만 누적 20,840건 대비 상세 receipt는 bounded tail 64건이므로 전수 exclusion 증명과 through-close acceptance는 계속 OPEN이다.
- 디스크는 약 `14.46 GB` free, 사용률 `90%`였다. writer stop/critical watermark 증거는 없었다.

## Main BUY funnel

14:30:04 sentinel은 `SUBMIT_DROUGHT_CRITICAL + LATENCY_DROUGHT`다. KRX regular 기준:

- AI confirmed unique `211`, budget pass `430`, latency pass `80`, order bundle submitted `10`
- bundle `10`, requested `43주`, submitted `10주`; submitted notional `611,555/852,830원=71.7%`
- probe-only `10`, partial residual `0`, full submitted `0`
- latency root는 넓은 micro spread 중심이고 refresh `305`회 중 `269`회 적용, latency pass 회복 `58`, 회복 뒤 submit `9`
- cash/orderable shortage와 `max_position_qty_cap`은 기존 계약대로 drought 인과 분모에서 제외했다.

이 수치는 제출이 0이라는 상태는 아니지만 정상 full participation도 아니다. scanner recall의 독립 market-wide forward maturity와 비용 차감 terminal EV가 닫히지 않아 threshold·spread·guard를 장중 변경하거나 bot을 재기동하지 않았다.

## 독립 매매기계·Telegram

자연 체결 알림 네 건이 immutable owner registry 순서로 모두 1회 전송됐다.

| Owner | 주문 | 결과 | Telegram |
| --- | --- | --- | --- |
| widget Samsung | BUY `0045909`, SELL `0045917` | 각 1주 전량체결 | message `32218`, `32220` |
| episode KEPCO afternoon | BUY `0049652` @ `33,050`, SELL `0049752` @ `33,250` | 각 1주 전량체결, position 0 | message `32221`, `32240` |

notifier cursor는 `804`, delivery status는 모두 `sent`, 중복·failed·uncertain은 관측되지 않았다. 시스템의 Telegram API receipt와 message ID는 닫혔지만 사용자 단말 수신은 이 모니터링에서 독립 확인할 수 없어 해당 acceptance를 OPEN으로 유지한다.

한국전력은 동일 `episode:kepco_afternoon:015760:2026-09-11` owner로 BUY→target SELL이 결속됐고 broker/registry 수량은 0으로 닫혔다. 가격차는 200원이고 고정 23bps만 단순 적용하면 약 124원 양수이나, exact fee/tax/slippage receipt가 없어 실현 순손익으로 사용하지 않는다. 저빈도 0B 때문에 차단된 다른 profile은 청산 유동성·자본회전 보호의 의도된 결과로 유지했다.

## Broker·custody

14:30:07 cached-token read-only 조회는 KRX/NXT 모두 성공했다.

- 보유: 삼성전자 25주, 대우건설 1주, ICTK 1주
- 미체결: 0건; ka10075 normalization gap 0, rate-limit 0
- 한국전력 broker 수량 0, registry owner 수량 0
- raw 주문가능액 `526,465원`, 기존 operator floor 적용값 `3,000,000원`을 분리 보존
- 대우건설·ICTK 1주는 registry 밖 external/manual remainder로 balanced 처리됐으며 독립 매매기계가 흡수하지 않았다.

증거는 `tmp/intraday-monitor-20260911-1430/broker-143008.json`이다.

## 14:20 원천품질 감사

지정 명령을 14:20에 한 번 실행했다. 14:21:13 결과는 event `160,931`, hard blocking gap `0`, hard excluded row `0`이지만 `source_quality_raw_changed_during_audit`로 `tuning_input_allowed=false`다. unknown-token stage 4건과 review warning 4건은 `scalping_scanner_source_fetch_census`, `scalping_scanner_candidate_pool_census`, `scale_in_ai_authority_retry`, `scalp_fast_exit_quote_blocked`다. append 중 원천을 고정 snapshot으로 오인하지 않고 canonical FAIL을 유지하며 장후 source-quality owner로 넘긴다.

## 발견 결함과 수리

`kepco_afternoon_state.json`은 `target_filled_qty=1/status=COMPLETE`였지만 `target_fill_price=0`, `target_filled_at=""`였다. 같은 주문의 immutable registry에는 `FILL_RECORDED`, amount `33,250`, receive time `14:14:06.150412`가 존재한다. 실행·custody는 정상이나 장후 report가 complete economic row로 인정하지 못하는 데이터 전달 결함이다.

격리 worktree `fix/scalping-unification-20260911`에서 다음을 보완했다.

- registry fold가 `FILL_RECORDED` 시각을 후속 terminal transition 뒤에도 보존
- profit-stagnation episode owner가 동일 exact order/date/episode owner/position/symbol/전량 filled quantity와 나누어떨어지는 누적 체결금액일 때만 평균 체결가·마지막 fill receipt 시각을 state에 투영
- 결손·수량 불일치·비정수 평균은 계속 null/미대사로 유지

검증은 직접 suite `96 passed`, 인접 owner/broker/loop suite `366 passed, 2 skipped`, Python compile, `git diff --check` PASS다. 최종 재리뷰 시 selector는 병행 세션의 `6936e8fd` 세대로 다시 전진했으며 그 release 위 patch apply-check도 PASS다. 리뷰에서 order authority·target·quantity·broker guard 변화가 없음을 확인했고 미해결 finding은 0이다. 현재 완료 상태는 `code_review_closed / deployment_pending / current_9_11_state_not_rewritten`이다. 따라서 이후 자연 체결에는 배포가 필요하고 이미 끝난 한국전력 state는 자동 소급 수정하지 않으며 장후 exact cohort 결손으로 보존한다.

## 체크리스트 대사

| ID | 14:30 판정 | 남은 acceptance |
| --- | --- | --- |
| `MachineFillTelegramAcceptance0911` | `runtime_delivery_verified/open_user_receipt` | 네 자연 체결 sent/message ID 확인. 사용자 단말 수신과 20:00 window 잔여 |
| `MachineProfitStagnationStartupAcceptance0911` | `running/open` | 정책 pin과 한국전력 original target terminal 확인. 14:35 through-window, 수리 배포/PID와 exact 비용 경제성 잔여 |
| `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0911` | `open/source-warning` | collector healthy. bounded-tail 때문에 전체 timestamp exclusion과 through-close 잔여 |
| `RuntimeEnvIntradayObserve0911` | `open` | V2.14/main 정상, submit10이나 full0 drought와 scanner/economic acceptance 잔여. selector66a3189b/current main57a90bd9 세대 분리 |
| `IntradaySourceQualityGateCheck0911` | `executed/fail_closed` | 14:20 실행 완료. append 변경 FAIL과 unknown4를 장후 기존 owner에서 재확인 |
| POSTCLOSE owner | `not_yet_due` | 16:25 이후 설치 owner를 따름 |

14:30 현재 OPEN과 미래 due는 모두 분류했고 미분류는 0이다. 요청 종료가 14:30이므로 14:35까지의 machine window나 야간 작업으로 자동 연장하지 않았다.
