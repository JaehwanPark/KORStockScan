# S6 `S2-ENT-04` pre-submit 시각·quote 원천 수리

실행일: **2026-09-28 KST**. 범위: [S2 `S2-ENT-04`](2026-09-27-intraday-postclose-handoff-S2.md), [S4](2026-09-27-intraday-postclose-handoff-S4.md), [현재 checklist `DirectFamilySourceRepairPreSubmitDelay`](../checklists/2026-09-28-stage2-todo-checklist.md). **판정: 생산자–첫 reader의 route/epoch/시각/논리 세대 계약을 작업본에서 수리했다. 9/23 자연 자료는 계속 source gap이며 경제성·PID 수용은 미완료다.**

## 원천·dispatch·영향

`src/engine/sniper_state_handlers.py`의 `_submit_watching_triggered_entry`가 main SCALPING의 0초/조건부 지연 decision을 기록한다. `kiwoom_sniper_v2.py`의 watched-stock loop가 기한이 된 30/60/120/180초 local WS snapshot을 `observe_pre_submit_delay_quote`에 넘긴다. wrapper `deploy/run_threshold_cycle_postclose.sh`의 `RUN_PRE_SUBMIT_DELAY_TUNING=true` 경로가 `postclose_summary_handoff --stage pre_submit_delay --launch`를 dispatch하고, 첫 reader는 `src/engine/scalping/pre_submit_delay_tuning.py`이다. wrapper·등록·정책은 수정하지 않았다.

9/23 기존 보고서 `data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-09-23.json`의 원천 SHA는 `d5d00ee808b9356e110afdf889188ec99e47b060d82662d236d4f02703954787`이다. 원천 partition 5개에서 대상 stage **원본 10 event = committed 2 + quote 6 + terminal 2**, 동일 event SHA 중복 0. committed/eligible은 각각 2 attempt다. 두 terminal의 고유 submit attempt ID는 남았지만 모두 `returned_false`, `submit_call_broker_accepted=False`, `actual_order_submitted=False`다. broker order/execution·체결 clock·실제 비용은 이 family 영수증에서 **미관측**이며 PnL은 `null`이다. 장중 quote observation과 실주문·체결·경제성 모집단을 합치지 않는다.

| horizon | 적격 attempt | 관측 quote | 유효 | 격리 | 미관측 | 9/23 사유 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0초 | 2 | 2 | 0 | 2 | 0 | 두 route가 비어 있음 |
| 30초 | 2 | 1 | 0 | 1 | 1 | 빈 route, 실제 offset 34.358초 |
| 60초 | 2 | 1 | 0 | 1 | 1 | 빈 route, depth age 1.062초/stale |
| 120초 | 2 | 1 | 0 | 1 | 1 | 빈 route, 실제 offset 127.066초 |
| 180초 | 2 | 1 | 0 | 1 | 1 | 빈 route, depth age 1.085초/stale |

이 수치는 **9/23 원천과 기존 보고서의 분모**다. 새 코드의 `horizon_source_quality` 자연 결과가 아니다. 기존 quote에는 transport epoch·0D route-depth SHA·decision generation이 없어서 나중의 파일이나 근접 시각 quote로 채울 수 없다. 늦게 온 quote와 실제 미관측 horizon을 분리한다. 원본 10/유효 event 10의 파일 판독과 경제성 유효 quote 0은 서로 다른 단위다.

## 실패 재현 → 수리 → 자체 재리뷰

1. 먼저 `test_reader_quarantines_cross_epoch_and_mutated_quote_receipts`, `test_reader_accepts_exact_generation_once_and_rejects_late_clock`를 작성했다. 최초 실행 **2 failed**: 첫 reader가 generation/epoch가 다른 `quote_valid=True`와 clock 변경을 그대로 유효 가격 경로로 인정했다. 기존 테스트도 출처·epoch 없는 가짜 quote를 유효로 기대했다.
2. 생산자는 commit에 `decision_source_sha256`을 기록하고 frozen route, transport epoch, 정책 SHA, machine observation, 수량·owner·session을 결속한다. quote에는 같은 decision SHA, 관측 clock·offset, route/epoch, 정확한 0D route-depth receipt SHA와 quote 논리 SHA를 넣는다. flat BBO가 다른 route의 0D receipt와 다르면 source-invalid로 기록한다. 원인(`late/early`, route, depth/epoch, stale/conflict, price/depth)을 분리한다. terminal에는 decision SHA와 call 종료 clock을 남긴다. 이 변경은 source-only observer/영수증이며 주문 동작을 바꾸지 않는다.
3. 첫 reader는 source date + record + symbol + intent로 묶고 commit SHA, quote SHA·0D source SHA·route/epoch·commit↔quote clock·depth freshness를 재검증한다. 충돌하는 horizon·commit·terminal은 한쪽을 선택하지 않고 격리한다. 동일 event SHA 재입력은 한 번만 세고 identity 충돌은 거절한다. raw·중복·유효·격리·미관측을 source/horizon census로 남긴다. terminal은 같은 decision generation과 역행하지 않는 종료 clock일 때만 유효 관측으로 세며 응답 불확실·broker ACK 후 execution terminal 미관측·미제출 종료를 분리한다. terminal이 누락된 재기동 가능 구간은 원인을 단정하지 않는 `unobserved`다. 원천 partition이 존재하지만 비어 있으면 `valid_empty`로 구분한다. 구세대 quote/terminal은 새 세대 적격 분모에 들어가지 않는다.
4. 자체 재리뷰에서 flat BBO와 다른 route-depth의 결합, malformed route snapshot, 동일 horizon 중복, terminal 세대 불일치, `None`의 wire 문자열화, 충돌 quote를 미관측으로 잘못 세는 문제를 찾아 수정·재검토했다. **범위 내 미해결 코드 결함 0**. producer/reader가 source-only 원천을 실주문·비용 증거로 승격하지 않는지도 확인했다. Broker API/response parser는 수정하지 않았으므로 공식 Kiwoom reference gate는 호출하지 않았다.

## 검증·남은 gate

- 영향 pytest: `test_pre_submit_delay_tuning.py`와 `test_postclose_summary_handoff.py` 전체 **92 passed**. Python compile 3파일, `git diff --check` 통과. wrapper 수정 없음으로 `bash -n`/wrapper 계약 재검사는 해당 없음. 문서 print-only parser는 `--print-backlog-only --limit 500`으로 실행해 exit 0·현재 checklist owner 1건 파싱을 확인했다. 보고서 상대 링크 3개도 존재한다.
- 현재 선택 포인터는 9/28 09:58 KST의 `30e66ae584a78911211d461483c01ecf03f6887c` 릴리스이며 그 릴리스의 PID receipt는 존재한다. **이번 수리는 미커밋 작업본**이므로 그 포인터/PID가 이번 코드를 소비했다고 보지 않는다. 정규 장후작업·PREOPEN·배포·주문·취소는 실행하지 않았다.
- 다음 자연 source date의 닫힘 검사 owner: `pre_submit_delay_tuning`/장중 main observer. 동일 record·submit attempt·decision SHA의 0/30/60/120/180초마다 exact 0D route/epoch·depth SHA와 clock을 확보하고, raw/valid/quarantined/unobserved가 horizon별로 합계 일치하는지 확인한다. persistent BUY intent→broker order/execution→full/partial/open/uncertain terminal과 실제 비용을 별도 원천에서 연결한 뒤에만 paired EV/독립 holdout을 판단한다. 재기동으로 observation state가 소실되면 `unobserved`이며 가격 경로 0으로 보지 않는다. 이 자연 수용·전체 성능/terminal은 S7, 선택 릴리스·PREOPEN·이번 코드의 PID 소비는 S8로 인계한다. `DirectFamilySourceRepairLowPriceTwoLeg`, 조건부 `S5-FIN-05`는 별도 묶음이다.

결론: **작업본 계약 수리 및 fixture 검증 완료, 9/23 source gap 유지.** 0초가 최적이라는 판정, 체결·비용 조정 수익성, 독립 holdout, 자연 PID 소비 판정은 하지 않는다.
