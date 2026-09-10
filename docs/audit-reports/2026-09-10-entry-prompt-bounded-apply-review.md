# 9/10 메인 진입 프롬프트·제출 연결 보완

## 판정과 사용자 승인 범위

사용자가 V2.13 복귀 이후 제출병목/판단품질 저하를 지적하고 장중 변경·적용·반복 검증을 명시 지시했다. 기존 `entry_setup_live_policy`의 **KRX|KRX_REGULAR / SCANNER / V2.14 one_share_exploration** 한 축을 우선 복구한다. 새 모델/Provider/수량/하드 guard를 만들거나 NXT에 KRX 근거를 전용하지 않는다. 실험은 1주, 일일 최대3회, residual/scale-in 금지이며 기존 가격·freshness·계좌·주문·cooldown·보호청산 veto가 우선이다. 자동 drought 정책 OFF의 과거 이력/성적은 수정하지 않고 당일 operator override를 분리한다.

이 작업의 종료 조건은 도달 가능한 policy/adapter/recheck 계약, 코드리뷰·격리 회귀, 승인된 실제 PID 반영과 초기 자연 관측이다. 무표본 또는 수익 미입증을 성공으로 치환하지 않으며 같은 자료·Provider 요청·재기동을 무제한 반복하지 않는다. 전략 EV/순이익 및 early micro 회복은 별도 남은 acceptance다.

## 확인한 원인과 반례

1. 08:35~08:42 main PID349443은 `decision_quality_v2_13_recovery_confirmation_probe`, recheck ENABLED=false, ALLOWED_SCOPES 빈값이다. V2.13의 유효 모델 BUY도 WAIT/probe intent로 변환되므로 probe-only 경로와 OFF consumer가 함께 선택된 상태다. 이 사실만으로 모든 주문 실패를 AI 탓으로 돌리지 않는다. [08:30 감사](2026-09-10-intraday-monitoring-0830.md)의 현금cap0·spread/latency·warmup·tick-speed·slot eviction은 각각 독립 owner다.
2. Main AI R0→R3의 source9/9 provider 미실행/연구후보0과 별개로 기존 setup-risk candidate는 `bounded_exploration_apply_ready`다. 원천 [후보](../../data/threshold_cycle/bounded_live_candidates/entry_setup_v2_14_bounded_live_candidate_2026-09-09.json) 파일 SHA256=`ed8193ee5cd0a07875d07c8d5fcbbd9a998facde82d415991773032d67eb093a`, effective9/10, prompt contract=`0bfbdebe183e810b3b0a0f8119e7aecd5c23409c3ea75675540e59b31b9789cb`. 자동 performance 승격은 실패이며 bounded exploration만 기존 계약에서 가능하다. #81 retired bridge는 사용하지 않는다.
3. 별도 KRX [상세 paired replay](../../data/report/ai_prompt_detailed_paired_replay/ai_prompt_detailed_paired_replay_2026-09-09_decision_quality_v2_14_setup_risk_adjudicator_venue_krx_session_krx_regular.json)는 기존 provider 결과30건 재사용, 신규호출0, schema/provider 실패0이다. 같은30건 Control DROP22/WAIT8 → Candidate DROP8/WAIT22, probe arm21이다. 이 WAIT는 실제 fill/수익 또는 즉시 BUY가 아니다. 전체231 decision에서 target-first31/adverse-first171/same-bar ambiguous14/neither15이고, target-first 중 deterministic INVALID23/WAIT_CONFIRMATION5/probe pending3이다. 따라서 prompt를 연결해도 setup 정의의 누락은 남는다.
4. 누적80 probe arm/67종목은 반사실 탐색 분모다. exposure1종목1건만 존재하며 performance floor 미달이다. arm 경로 tail28/80, catastrophic1은 손실 위험을 드러내는 진단으로 보존한다. 기존 탐색 계약의3회/1주·fresh recheck·보호청산을 유지하고 이를 양수 실매매 EV 승인으로 표현하지 않는다.
5. 나우459510 exact trace `analyze_target:459510:1788995877402:5697f8b0`의 미래정보 없는 저장 payload를 V2.14 setup builder에 넣어도 INVALID/`no_supported_setup`이다. `PREMARKET_KRX_LIKE` / integrated SOR source이며 exact NXT로 재라벨링하지 않았다. tape/liquidity supportive와 범용 range/no-setup 분류의 충돌은 **미해결 설계 finding**이다. +3.73% 사후 호가 변화는 실현손익·target-first 증거가 아니며 종목 정답을 prompt에 삽입하지 않는다.

## 구현·리뷰

`entry_setup_live_policy._runtime_probe_contract_errors`가 recheck ON만 보고 실제 consumer의 exact ALLOWED_SCOPES를 보지 않았다. KRX scope가 없으면 활성 후보를 표시해도 consumer에서 막힌다. 기존 정책 모듈에 같은 comma-separated/case-sensitive scope 검사를 추가하고 env provenance hash에 scope를 결속했다. missing/empty/NXT-only/wrong-case를 거부하며 명시 env에서 누락된 키를 process env로 채우지 않는다. 실주문·order API·Provider·프롬프트 본문·economic floor 변경은 없다.

관련 정책/ledger/AI adapter/recheck/PREOPEN 및 재기동 owner tests521 PASS. 기존 테스트 포함 횟수이며 앞선218과 합산하지 않는다. 별도 병행 WS 수신 기대 진단은 [해당 리뷰](2026-09-10-ws-opening-auction-quiet-review.md)의 범위를 따르고, adaptive-exit 미연결 작업은 활성화하지 않는다. 기존 dirty worktree는 보존한다.

08:41:27 staging env를 통한 실제 source/hash 재검증은 active_bounded_canary/blocking_reasons=[]다. 이는 dry-run이며 아직 PID 적용 receipt가 아니다. staged override는 ENABLED=true와 ALLOWED_SCOPES=KRX|KRX_REGULAR 두 값뿐이고 원 automatic env/상시 operator env는 보존한다.

## 반영·rollback·후속 acceptance

실제 반영 결과는 아래에 기록한다. 08:42:14 broker 선행 대사는 KRX/NXT 검증, 삼성전자25주·미체결0이다. 028050의 기존 manual successor 귀속 deficit는 별도 owner에서 유지하며 이번에 원장·청산을 변경하지 않는다. 원천은 `tmp/intraday-monitor-20260910-0830/broker-084214.json`이다.

Rollback은 당일 override의 ENABLED=false/ALLOWED_SCOPES 빈값 복원 → activation 재생성 → 표준 graceful restart다. 날짜를 바꾸어 이 override를 자동 연장하지 않는다. cap/계약/owner/provenance 위반, 주문오류·보호청산 지연·귀속 가능한 severe loss는 중지/rollback 사유다. 단순 무표본·비용후 EV 미입증은 수용 미완료이며 억지 BUY를 만들지 않는다.

기존 `RuntimeEnvIntradayObserve0910`에서 실제 eligible→AI verdict→probe intent→fresh recheck→submit/fill/terminal/net을 동일 lineage로 확인한다. 기존18:00 AI micro exact owner는 (a) INVALID가 진짜 invalidation인지 단순 no-supported-setup인지, (b) completed-bar 이전 fresh micro 회복과 부정 반례, (c) DROP 이후 재관측/slot, (d) 비용후 missed profit/avoided loss 및 stage/venue별 source 교집합을 계속 소유한다. KRX 연결을 PREMARKET/NXT 해소·전 종목 수익 개선으로 일반화하지 않는다.

### 실제 반영 receipt / 최종 경계

- 코드 gate: self-review→scope 누락 보완→재리뷰→521 tests PASS, Black/Ruff/compile/shell syntax/diff·print-only parser PASS. **이번 scope guard와 기존 bounded owner 연결의 미해결 구현 finding0**이며 위 early-micro 설계 finding을 닫은 것이 아니다. prompt/schema 본문이나 Provider 호출량을 추가 변경하지 않았다.
- 08:44:47 당일 operator env 두 값을 설치하고 기존 activation CLI만 실행했다. artifact SHA256=`9b39fbaa39d668e5584ac8da75b8b7fcfe9b80e5017ea87df920334315cca437`, active_bounded_canary, one_share_exploration, blocker0. 기존 inactive activation 원문은 `tmp/entry-prompt-0910-OhxPbb/activation-before.json`에 보존했다. 전체 PREOPEN/postclose 재생성·강제 BUY·Provider replay는 실행하지 않았다.
- 이 작업의 `restart.sh` 호출은 **1회**이며 PID349443→374288, verify PASS와 Samsung same-date handoff committed로 exit0이다. 뒤이어08:45:43 별도 restart flag 종료가 관측돼 PID375167로 바뀌었다. 해당 두 번째 요청의 발행 주체는 이번 작업에서 확정하지 않았고 자동 crash/retry로 단정하지 않는다. 최종 handoff ledger는374288→375167 committed이고 독립 Samsung PID327358·widget PID327676/NRestarts0이다. 이 세션에서 추가 restart를 요청하지 않았다.
- 08:47:05 최종 PID375167 env로 순수 resolver를 재검증했다: KRX/정규장/SCANNER만 V2.14 active, NXT/PREMARKET/WIDGET는 inactive fallback. 이는 실제 자연 AI 호출이 아니라 **현재 PID 설정을 이용한 consumer 도달성 검사**다. 보존 verify는 PID375167/pass, missing/mismatch0, runtime policy fail0, dated override fail0이다.
- 08:47:05 전시장 broker 대사는 삼성전자25주·미체결0/조회오류0이고 조회 중 PID도 동일했다. 중복 신규 주문 증거 없음. 028050 과거 귀속 gap을 손익·원장 보정으로 임의 해결하지 않았다. `post-apply-receipt.json`은 성공한 최종 원문이며 앞선 PID374288 종료 후 조회 실패는 주문 실행이 아니라 proc env 읽기에서 종료됐다.
- 보존된08:49:14 collector는 healthy/stop=false, 0B4213/0D4979, queue/writer error0, callback p95=0.100805ms/p99=0.109947ms, free minimum37,061,877,760bytes다. 첫-data 자연수신은08:46:07 이후 로그에 존재한다. 다음 수신 기대 휴지/재개 및 KRX 자연 신호는 해당 owner에서 분리한다.
- receipt 경로: `tmp/entry-prompt-0910-OhxPbb/{activation-applied.json,restart.log,post-apply-receipt.json,runtime-verify-375167.json,collector-after.json,applied-source-hashes.txt}`. 현재 working tree dirty/병행 변경을 보존했으며 clean commit 배포라고 주장하지 않는다. 커밋/푸시/병합은 이번 지시 범위에서 하지 않았다.

**현재 완료는 제한된 KRX policy/PID 연결과 안전한 수신·계좌 연속성이다. 정규장 실제 eligible/probe/submit/fill/terminal/비용후 EV는 아직 미확인이다.** 기존09:05~09:20 owner의 자연 표본으로 다음 최초 차단을 판정한다. 오늘 자료만으로 NXT prompt 승격, all-DROP/WAIT 전체 해소 또는 누적 순이익 개선을 선언하지 않는다. 동일 source에 대한 무한 재생·재기동 대신 각 수용조건에 맞는 다음 실제 표본을 사용한다.
