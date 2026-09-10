# 배포 이후 탐색 허용 미제출 원인과 입력 시점 정합화

검토일: 2026-09-10 KST. 범위: 13:51:53 고정 배포 이후부터 15:30 이전의 메인 Entry 탐색 허용 응답. 코드 수리와 실제 적용·경제성 검증은 별개다.

## 후속 사용자 승인 재기동 (16:22 KST)

- 사용자의 별도 `우아한 재기동` 지시에 따라 기존 검토 배포 `76995257`에서 이번 Entry 수정 5개 파일만 분리한 고정 release를 만들었다. 로컬 배포 commit `d0f57e0363c1e95e39473950121530ddd885d9cc`, branch `deploy/entry-revalidation-20260910`, 경로 `/home/ubuntu/KORStockScan-runtime-releases/entry-revalidation-20260910`이다. 원 작업폴더의 병행 adaptive-exit/widget/episode/PREOPEN 변경은 포함하지 않았다. 원 작업폴더의 미커밋 변경은 보존했으며 외부 push/main 병합은 이번 재기동에 포함하지 않았다.
- 정확한 새 배포본에서 6개 테스트 모듈 **1390 PASS**(45.84초, 기존 pandas 경고 1), compile·shell syntax·`git diff --check -- src deploy` PASS. 실제 runtime Python 차이는 Entry context와 sniper consumer 2개뿐이다. release의 `src/deploy`는 clean이며, shared data/logs/tmp 연결을 유지했다. 공유 데이터 mount 때문에 나타나는 worktree의 data 삭제 표시는 커밋하지 않았고 실제 데이터도 삭제하지 않았다.
- 기존 `restart.sh`의 flag→old PID drain→drained supervisor 교체→new PID strict verify 순서를 한 번 실행했다. 16:22:39 기존 PID772330 종료 요청 수용, **16:22:43 새 PID944889** 기동. source commit/root/`source_dirty=false`를 PID에서 확인했다. runtime verify의 passed/pid_passed=true, missing/mismatch 및 policy/dated fail 모두 0이다. 삼성 오전 owner는 이미 inactive여서 handoff prepare/commit은 `morning_owner_not_active / not_required`였으며 독립 owner를 기동하지 않았다.
- [16:22:26 사전 broker](../../tmp/intraday-monitor-20260910-1050/broker-162226.json)와 [16:22:59 사후 broker](../../tmp/intraday-monitor-20260910-1050/broker-162300.json)는 KRX/NXT 조회 성공, 삼성전자25주·미체결0·shared registry 수량 gap0으로 동일하다. 위젯 PID327676은 유지했다. 임의 매수·매도·취소·원장 재귀속은 하지 않았다.
- 기존 approval canonical SHA `95a10c8513acedad7044678cf026ce47ecf5c2f041aeec107ee8f3341da20da0`, pinned code10개/source3개 일치, 두 recheck 일일 budget100을 유지했다. KRX 장중 approval의 15:30 만료는 연장하지 않았으며 NXT 실주문 승격·프롬프트/Provider/수량/안전 기준 변경은 없다. 따라서 시간창 밖 V2.13 baseline 선택을 새 배포의 승인 유효성으로 오인하지 않는다.
- WS 로그인16:23:01, 실제 0D 첫 수신16:23:43 및 0B 첫 수신16:23:44 확인. 이전 PID의 누적 registration receipt를 새 PID 첫 수신 근거로 쓰지 않았다. 16:25:51 수집기는 `healthy_observer_canary`, 신규 process 체결1576/호가3721, callback p95 0.101912ms/p99 0.117576ms, worker/writer 오류와 queue full 모두0, trade/depth writer 각각2개, 디스크 여유약24.17GiB다.16:24:52 자연 broker refresh도 inventory1/open_orders0/verified=true였고 삼성전자 manual-control 보유는 외부 owner로 보존됐다. 위젯 PID327676 유지 및 main singleton944889를 재확인했다.
- 이 절 이후 실제 post-apply 구간은16:22:43부터이며 아래의 미배포·미커밋 문구는 앞선 수리 완료 당시 기록이다. 병목 개선·체결·순이익은 아직 검증되지 않았다. 내일07:55 cron은 원 작업폴더 경로 그대로다. 이번 고정 배포만으로 내일 동일 release 자동 기동을 보장하지 않으며 기존 `KRXDaily100NextDayStartupAcceptance0911`가 기동 경로/당일 정책/실제 PID 확인을 소유한다.

## 판정

- Entry 탐색 허용 응답은 11건, 최초 WATCHING 판단 기준 기회는 9개다. 흥구석유·에스투더블유는 같은 기회의 추가 AI 재검증이 각 1건 있으므로 독립 기회로 더하지 않는다.
- 9개 기회의 최초 차단은 재관측 freshness 4개, micro 확인 부족 3개, 제출 spread 1개, 제출 weak-pullback 확인 부족 1개다. `blocked_ai_score` 요약만으로 모델의 WAIT 거부 또는 점수 부족으로 귀속하면 안 된다.
- freshness 4개에서 재관측 정책 1500ms와 snapshot 취득에 재사용한 제출용 700ms 제한의 불일치를 확인했다. 더 최신인 753~1233ms snapshot을 버리고 3893~9252ms 이전 snapshot으로 평가했다. 최종 제출의 700ms 안전 기준은 변경하지 않고 재관측 입력 취득에 해당 단계의 기존 정책을 적용한다.
- 별도 pre-submit AI 재검증은 history/보조 입력 준비 전에 잡은 WS 데이터를 계속 사용했다. 느린 준비 뒤 local cache를 한 번 더 취득하고 canonical snapshot을 재검증하도록 보완했다. 실제 새 tape가 없으면 과거 tape를 새 호가에 붙이지 않는다.

## 원천 대사

현재 대상 배포: `/home/ubuntu/KORStockScan-runtime-releases/holding-input-76995257`, commit `769952574cfbc3f7fa4af3115c847abc99237377`, PID `772330`. 16:04 전후 확인에서도 동일 cwd이며 release의 `src/deploy`는 clean이다. 작업폴더의 다른 세션 보유 입력·적응형 청산 변경은 보존했다.

입력은 [AI trace](../../data/ai_decision_trace/ai_decision_trace_2026-09-10.jsonl), [Sentinel event cache](../../data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-09-10.jsonl), raw `data/pipeline_events/pipeline_events_2026-09-10.jsonl`이다. raw 읽기 범위 `[2735812625,3539230135)`의 SHA256은 `bd1f88ad6f033a32ce8f165bfe8a68fdb5e4753d992be4307af93708a202143c`다. 읽은 범위에는 앞뒤 여유분이 있으며 분석은 13:51:53 이상·15:30 미만으로 제한했다. growing 파일 전체 hash나 전일/다른 PID 실적으로 대체하지 않는다.

| 최초 판단 시각 | 종목·record | 최초 미제출 원인 | 직접 근거 |
| --- | --- | --- | --- |
| 13:57:03 | 퀄리타스반도체 432720 / 42356 | strong_micro_confirmation_missing | 재관측 WS age 223ms, 매수압력·tick acceleration·micro VWAP 확인 부족 |
| 14:01:39 | HDC 012630 / 42400 | quote_freshness_not_confirmed | 입력 4006ms, 미채택 최신 snapshot 1064.694ms |
| 14:02:01 | SK디앤디 210980 / 42497 | strong_micro_confirmation_missing | 재관측 WS age 80ms, tick acceleration·micro VWAP 확인 부족 |
| 14:02:13 | 컴투스 078340 / 42336 | latency_state_danger / spread_above_caution_below_guard_cap | probe armed 뒤 제출 attempt `feb300e2ddda4b5bbb75ab4764bdc7b2`, spread 71.633bps, relief low_signal |
| 14:23:11 | 한국석유 004090 / 42218 | quote_freshness_not_confirmed | 입력 3893ms, 미채택 최신 snapshot 753.044ms |
| 14:26:13 | 흥구석유 024060 / 42331 | weak_momentum_caution_without_micro_confirmation | 14:26:16 후속 AI→probe armed→latency pass→attempt `8e877586e65346b591ae3ae945a428dd`의 weak-pullback 차단 |
| 14:42:17 | 티에프이 425420 / 42377 | quote_freshness_not_confirmed | 입력 5309ms, 미채택 최신 snapshot 1233.176ms |
| 14:44:12 | 알파칩스 117670 / 42580 | strong_micro_confirmation_missing | 재관측 WS age 127ms, 매수압력·tick acceleration 확인 부족; 16초 뒤 과열 차단을 첫 원인으로 대체하지 않음 |
| 14:59:51 | 에스투더블유 488280 / 42154 | quote_freshness_not_confirmed | 14:59:54 후속 AI 뒤 입력 9252ms, 미채택 최신 snapshot 1043.698ms |

WAIT handoff의 pending parent trace 또는 `ai_confirmed`의 exact trace와 후속 재검증을 확인했다. record/종목이 같다는 이유만으로 수십 분 뒤 다른 시도를 원인으로 붙이지 않았다. 위 4개는 입력 취득 단계의 수리 대상이지 수리 후 BUY/체결/수익 4건을 보장하는 표본이 아니다. fresh tape·micro 및 후단 guard는 별도로 통과해야 한다.

기존 Sentinel `input_preflight_gap=64`는 누적 전이 집계다. 별도 raw/cache 차단 76행 중 배포 이전 75행·이후 플리토 1행과 분모가 다르다. 플리토 14:49:42는 최신 WS age 5419.169ms, 입력 준비 2105.614ms였으므로 수리 뒤에도 실제 새 source가 없으면 차단이 맞다.

## 구현·리뷰 범위

1. `sniper_state_handlers._refresh_entry_opportunity_recheck_inputs`: 현재 recheck config의 age limit을 local snapshot 취득에 전달한다. 최종 제출 호출의 기본 age 제한, handoff 검증, quota, 주문/수량/custody guard는 그대로다.
2. `_pre_submit_refresh_real_ws_snapshot`: 취득 age owner/상한을 기록하고 미래·NaN·무한대 timestamp를 fresh로 clamp하지 않는다. 신규 REST/WS 요청이나 FID/route protocol 변경은 없다.
3. `_retry_entry_ai_submit_authority_before_block`: history/보조 입력 준비 뒤 local cache를 단회 재취득한다. 새 snapshot에 tape가 없으면 빈 tape로 후단 source-quality 검증을 받는다. history 준비·최종 취득·snapshot 재검증 시간을 분리한다. 기존 exact entry-price handoff는 별도 TTL/identity 계약을 유지한다.
4. `entry_candle_context.revalidate_entry_candle_snapshot`: 외부 조회 없이 새 호가·체결과 준비된 candle을 결속한다. candle의 원시각, forming 표시, 수급 원시각을 보존하고 source age/skew를 새 평가 시각에 재계산한다. route 변경·시계 역전은 실패 처리하고 새 parent identity를 합성하지 않는다.
5. 첫 리뷰에서 optional 수급 clock의 문자열/epoch 변환과 원천 route alias 비교 문제를 보완했다. 기존 authority-only 테스트가 live candle 취득에 의존하던 부분도 mock으로 격리했다. 최초 실행에서 read-admission 거절 로그가 있었으나 `admission_attempt_sent=false`였고 실제 broker/provider 요청을 실행하지 않았다.

검증 대상은 기존 `src/engine/scalping`과 해당 소비자이며 새 회귀 테스트는 `src/tests/test_entry_snapshot_revalidation.py`에 배치했다. engine root 신규 모듈·배포본 변경은 없다. 다른 세션의 holding/exit 수정은 이번 코드 완료 범위로 합산하지 않는다.

## 검증과 남은 수용 조건

- 최종 통합 검증 **1390 PASS**(36.25초), 기존 pandas_ta/Pandas 비관련 경고 1개. 이전 집중48·연관342·제출1045 실행은 중복이므로 더하지 않는다. 새 회귀 15개에는 invalid candle age가 시간이 지나 정상으로 바뀌지 않는 검증도 포함했다.
- 최종 재리뷰: 이번 입력 정합화 변경 범위의 미해결 finding 0. `py_compile`, 관련 Ruff, 변경 구간 Black, `git diff --check` 통과. 문서 print-only parser29건, `CodeImprovementWorkorderReview0910`/`PostcloseSourceQualityGateReview0910` 각각 당일 owner 1회 확인. 외부 Project/Calendar 동기화는 실행하지 않았다.
- 재관측 753/1044/1065/1234ms 입력 취득과 동일 입력의 최종 제출 handoff 거절을 함께 검증한다. stale/future/nonfinite/route 변경, 느린 준비 뒤 새 quote/tape, 원 bar·수급 clock 불변을 회귀 범위로 둔다.
- 정책 기준 완화, Provider 추가 replay, 실주문·취소, 배포·재기동은 수행하지 않았다. 현재 실행 중인 고정 배포본에는 이 수리가 반영되지 않았다.
- 목적은 인위적인 입력 노후화로 사라지는 평가 기회를 줄이는 것이며, micro·spread 완화나 수익 증가를 이미 검증한 것이 아니다.
- 장후 기존 `CodeImprovementWorkorderReview0910` 및 `PostcloseSourceQualityGateReview0910`에서 9개 기회의 exact first-blocker와 배포 세대를 유지해 대사한다. 새 코드 미배포 기간을 post-apply 성과로 포함하지 않는다. 실제 적용 후에만 quote/tape age, 준비시간, recheck→submit→fill→terminal 및 비용 차감 EV/순이익을 평가한다.
- 앞선 보유 검토의 net executable 손익 결손은 이 Entry 시점 수리와 다른 입력 생산자 범위다. 비용·슬리피지 결손을 0으로 채우지 않으며 기존 장후 경제성 source-gap owner에서 별도 확인한다. 이 보고서로 보유 AI·청산 정책 전체 결함이 해소됐다고 주장하지 않는다.

최종 검증 작업폴더 파일 SHA256:

- `src/engine/scalping/entry_candle_context.py`: `56f99000329a8c546d8896dabe525234d5b9043fbc66057b306700f4d6c6114b`
- `src/engine/sniper_state_handlers.py`: `8848f7c0faefd16c9ff0bf8f938aace40f443c0135d38bccc6bfff0e087d744e` (다른 세션의 기존 holding 수정 포함; 그 변경을 이번 리뷰 완료로 간주하지 않음)
- `src/tests/test_entry_snapshot_revalidation.py`: `56aa159a780ac6191579a804fff8ddb539be5bd5932961a8354b5fcdc8e59d24`

이 파일 hash는 미커밋 작업폴더의 검증 receipt이며 고정 배포 commit/런타임 반영 receipt가 아니다. 이번 요청에서 커밋·푸시·main 병합은 수행하지 않았다.
