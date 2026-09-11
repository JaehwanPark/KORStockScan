# 9/11 08:50까지 장중 모니터링

대상 거래일 2026-09-11. 사용자 요청에 따라 08:19 KST 시작, 08:50 KST 관찰 종료. **YELLOW**이며 아래 값은 각 관찰시각의 기록이다. 본 창은 배포·재기동·정책·주문·custody 변경을 실행하지 않았다.

## 실행과 최초 병목

- 08:19~08:20 기존 main PID14564/340c1d00, widget15604, 삼성 preflight15182/live PID0. 당일 소유권 자동 적용은 07:32 `symbol_owner_auto_apply_owner_or_machine_scope_mismatch:108320`으로 차단됐다. [별도 수리 기록](2026-09-11-owner-scope-startup-repair.md)의 검토된 수리를 중복하지 않는다.
- 08:20:50까지 pipeline의 scanner-pruned 2,270행/473 unique symbols는 모두 `manual_control_excluded` / `symbol_owner_policy_fail_closed:SymbolOwnerPolicyError`다. 반복 scan 행을 고유 기회로 세지 않는다. 이 구간의 AI 미호출은 모델 DROP으로 집계하지 않는다.
- 08:21 다른 작업의 종료·전환을 관찰했다. widget 정상 stop, 삼성 preflight SIGTERM, main 종료. 이 창은 종료 명령을 실행하지 않았다. 수신 중단 구간은 새 원천으로 소급 복원하지 않는다.
- 08:22 공통 selector는 `main-owner-scope-20260911`/`b4de92bfee5e8f9f68f522292dd4b71509e14d28`로 변경됐다. 별도 복구 manifest와 96 drop-in을 관찰했으며 배포·사용자 승인 자체는 해당 작업의 receipt에 귀속한다.
- 08:24 main34365, widget34176, 삼성35141 기동. 당일 policy 20종목 activation 검사와 PID policy path가 일치한다. main runtime verify PASS/PID34365/mismatch0/missing0. 삼성 authority는9/11 ready다. 증거: `tmp/owner-scope-recovery-20260911/{policy-verification,pid-receipts}.json`.
- 08:25:25 detector7개 모두 PASS. 삼성 상태 BUY_OPEN은 두 leg PLANNED/주문번호 공백/체결0인 armed 상태이며 실제 주문 접수 성공이 아니다.
- 08:27 main의 새 promotion18/attach18, prune BBO56행 관찰. 전체 소유권 오류 차단은 해소됐지만 accepted submit 회복·경제성은 별도 미확인이다. 475400의 spread DANGER와000720의 의도한 qty0 차단을 AI 판단과 합치지 않는다.

## 계좌·수집·정책

- 08:27:09 cached-token 기존 조회 경로로 KRX/NXT inventory와 전체 미체결을 읽었다. 삼성전자25주, 미체결0, inventory error0/미체결 정규화 gap0. 삼성E&A·SK텔레콤 broker 잔고0. 증거 `tmp/intraday-monitor-20260911-0850/broker-0827.json`. 전체 기존 episode 원장 수량 정리 완료를 의미하지 않는다. SK텔레콤 이전 HELD 잔존은 별도 수리 기록의 기존 결손이다.
- 08:28:27 micro healthy, worker0B22236/0D19494, persisted22094/19465, worker/writer/queue-full 오류0. free25.91GB로 low watermark5GiB 상회. counter는 새 process 누적이며 이전 PID와 합산하지 않는다.
- 08:28:32 WS snapshot32종목, 새 registration epoch1/0B+0D 요청 receipt 확인. 등록 요청과 종목별 실제 수신을 구분한다.
- KRX9/11 activation은 source9/10의 V2.14/one-share exploration/daily100. `KRX_REGULAR` 적용이므로08시대 provider 호출을 KRX acceptance 필수로 요구하지 않는다. 다음 실제 KRX endpoint 소비·체결·EV는 기존 owner에 남긴다.
- 오늘 machine 신규1주 override는 [기존 승인](2026-09-11-one-day-machine-quantity.md)과96 successor의95 계약 보존을 기준으로 확인한다. 기본 entry_qty10 표시만으로 실제1주 override 실패를 단정하지 않고 자연 quantity receipt/주문을 대사한다.

## 체크리스트와 잔여

현재 OPEN15개를 전수 읽었다.07:30~08:05 KRX startup은 기동/정책 부분 확인과 이후 KRX 자연 소비를 분리한다.07:55~14:35 machine startup은 복구 후 관찰 중이다.08:40~08:45 micro는 도래 시 재확인,08:50~08:55 env는08:50 종료 경계에서 점검한다.08:55 scout,09:05 runtime,09:35 sim 최소 확인,14:20 source audit,16:30 Daily,17:00 intervention,21:15 workorder,21:30 machine,21:40 summary/source audit 및9/14 quantity expiry는 미래 예정으로 분류한다. 미래 작업을 조기 실행하지 않는다.

scanner 외부 독립 모집단·executable outcome을 닫기 전 recall 정상이나 놓친 순이익을 확정하지 않는다. 현재 R0/진단 수집과 장후 R1~R3/Provider 경제성은 별도다. 장후 producer를 조기 재생성하지 않는다.08:50부터 정상 quiet를 무수신 장애로 오판하지 않되 실제 queue/writer/연결 오류는 별도로 유지한다.

## 종료 검증

08:50:15 관찰 종료. main34365/widget34176/Samsung35141 가동, detector PASS, PREOPEN apply auto_bounded_live_ready, runtime verify PASS/PID34365/pid_mismatches=[]/pid_missing=[]/missing_family_count=0. 원천 hash와 전체 검증 결과는 `tmp/intraday-monitor-20260911-0850/final-0850.json`에 보존했다.08:40 micro 점검은 healthy,08:50에는 invalid_depth_timestamp1행의 enqueue 이전 exact exclusion receipt가 확인된 healthy_observer_canary_with_source_row_exclusions다. stop_required=false이며 through-close 원천 acceptance는 OPEN이다. 관찰 종합 YELLOW: 기동 복구와 입력 복구가 실제 제출/순이익 개선을 증명하지 않는다.

## 08:35 사용자 최소1주 질의

현재 선택 코드의 `position_sizing_allocator.py`는 최소1주 계산 뒤 `max_position_qty_cap`을 적용한다. 현대건설000720의08:24:24 입력은 cash capacity1/현금244048원/가격130900원, pre_cap_qty1→effective_qty0, binding_caps=max_position_qty_cap이다.222800도 같은 비중 한도 차단이다. 최소1주 설정이 켜졌다는 사실은 최종 제출1주 보장이 아니다.

현재 예외는 `broker_confirmed_one_share_floor && current_position_qty==0 && stage_qty_cap==1 && broker_qty_cap>=1`이며 호출부는 현금 부족을 보완하는 승인된 margin1주 경로에 이 값을 설정한다. 현금1주 구매 가능 시 `cash_one_share_capacity_available`로 margin 권한false라 예외가 적용되지 않는다. 이 비대칭과 “안전조건 통과 탐색 최소1주” 목표의 정합성은 기존 sizing owner에서 검토해야 한다. 질문을 수량·비중 guard 수정 승인으로 해석하지 않았으며 live 코드는 변경하지 않았다. KRX V2.14 one-share exploration과 현재 PREMARKET rising-missed 경로의 authority를 합치지 않는다.

## 사용자 요청: 자금 부족 drought 제외 구현

현금 부족으로 종결된 exact submit attempt와, 신규 진입에서 현금1주 capacity는 있으나 max_position_qty_cap 때문에 pre_cap_qty1 이상→effective_qty0이 된 배정자금 부족을 drought 평가 분모에서 제외한다. valid capacity 계약·당일 선행 source timestamp/hash·가격/현금/수량, 신규진입 stage·현재 sizing formula·단독 binding cap을 검증한다. scale-in/보유 한도·조회 실패·결손·다른 cap 또는 이후 같은 시도 제출 성공은 이 배정자금 제외로 감추지 않는다. 현금 부족과 배정 한도 부족은 서로 다른 reason으로 보존하며 실제 수량/주문 guard는 변경하지 않았다.

수리 worktree `review-cash-shortfall-drought-20260911`에서 검토한 sentinel·공유 validator·기존 테스트를 workspace의 동일 base 파일과 대사하여 반영했다. 최종 추가 리뷰에서 call-finish receipt가 제외 후 고아 시도로 남는 문제를 수정하고 재검증했다. 실제 오전 진단은11시도=제외3+잔여8; 제외 종목은000720 현대건설,222800 심텍,443060 HD현대마린솔루션이다. 근거 `tmp/intraday-monitor-20260911-0850/capital-shortfall-validation-final.json`. 최초 validation 실패 파일은 수리 전 증거로 보존하며 최종 partition PASS와 구분한다. PREMARKET 시간 gate를 정규장 critical 판정으로 재라벨링하지 않았다.

JSON에 raw exact ledger/stage/blocker/zero-qty 진단·제외 이유/증거를 보존하고 Markdown에도 제외 건수를 표시한다. 동일 consumer의 제외 증거·분모 보존 검증을 추가했다. sentinel/공유 contract/recheck controller 테스트203개 통과, compile 및 diff 검증 수행. 검토 범위 미해결 finding0이며 수익 개선 검증은 별도다.

설치된 장중 sentinel cron은 workspace wrapper를09:05부터5분마다 읽으므로 다음 실행에 이 수정이 자동 소비되는 경로다. 실제09:05 산출물은 아직 미확인이다. main/장후 선택 release는 변경하지 않았으므로 고정 배포의 장후 consumer 반영은 별도 배포·세대 대사가 필요하다. 실제 매매 봇 재기동은 이 보고 분류 수정에 필요하지 않다. 다음 자연 보고/장후 배포 확인은 기존 RuntimeEnvIntradayObserve0911/CodeImprovementWorkorderReview0911에 인계한다.

최종 문서 검증: print-only backlog parser 성공, 현재9/11 OPEN15개 ID 유일성 확인, git diff --check 통과. 외부 sync는 실행하지 않았다.

## 후속 사용자 요청: 장중 변경 코드 반복 리뷰

이번 후속 리뷰는 sentinel/공유 drought validator/직접 recheck consumer와 추가 테스트를 대상으로 수행했다. 다른 작업 창의 배포·owner custody 변경은 수정 범위에 포함하지 않았다.

- 중복 원천 행: exact ledger가 dedup한 원천의 별도 객체가 제외 뒤 남아 시도를 다시 만들 수 있는 반례를 재현했다. 같은 시각·pipeline·stage·종목·record·fields의 서명으로 해당 중복도 제거한다. 다른 시도·재평가·성공 제출을 제외하지 않는다.
- 숫자 검증: pre_cap_qty/effective_qty/budget_base의 bool이 정수처럼 받아들여지는 반례를 차단했다. config의 숫자1도 True로 승인하지 않는다.
- 시간 검증: offset을 지우고 비교하면 미래 UTC source가 과거 KST로 보일 수 있었다. naive timestamp는 기존 KST 계약으로, aware timestamp는 KST로 변환하여 실제 시간 순서를 비교한다.
- consumer 검증: 제외행 terminal stage·대상 날짜, raw ledger 중복·총수 불일치를 거부한다. 캐시 ON/OFF와 summary ON/OFF의4개 조합에서 producer 결과와 scope evidence consumer 검증이 동일함을 확인했다.

위 반례 수정 → 재리뷰 → regression을 반복했다. 최종 관련 테스트217개 통과, Python compile/diff 검증 및 문서 print-only parser 통과. 검토 범위 미해결 finding0. 기존08:50 모니터링 수치와203개 테스트는 당시 기록이며 이번 후속 검증217개와 구분한다. 실제 매매 코드·수량/주문 guard·선택 release·process는 변경하지 않았다. 이번 요청은 코드 리뷰이며08:50 종료된 모니터링을 연장한 것으로 보고하지 않는다. 다음 자연 산출물과 고정 장후 release 세대 확인은 기존 인계 owner를 유지한다.
