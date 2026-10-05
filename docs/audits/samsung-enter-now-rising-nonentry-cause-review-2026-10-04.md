# 삼성전자 ENTER_NOW 이후 상승·미진입 원인 분해

작성일: 2026-10-04 KST. 사용자 요청: 삼성전자 ENTER_NOW 중 이후 상승했지만 진입하지 못한 원인을 분해하고, 기존 정책 승계의 의미를 재점검한다.

> 범위 정정: 이후 사용자는 보조판정을 제외한 기계 신호 품질 및 ENTER/RECHECK/BLOCK 상승 집합 통합 분석을 명시했다. 현재 결론은 [기계 전용 통합 비교](samsung-machine-all-action-outcome-union-review-2026-10-04.md)를 따른다. 아래는 앞선 후단 원인 조사 기록이며, §6 후단 우선순위는 현재 연구 우선순위로 사용하지 않는다. 특히 ENTER의25미확정은 추가 대조에서 모두 가격/비용 결손 없이600초 내 양 경계 미도달로 확인됐다. 목표8관측의 존재로 기계 신호 품질이 적정하다고 결론내릴 수 없다.

## 1. 결론과 기존 정책 승계의 의미

**기계가 유효한 상승 신호를 전혀 만들지 못했다는 결론은 아니다.** 보관3일의 ENTER_NOW41관측 중 비용 결합 목표 선도달8관측이 있다. 실제 Main 기계 판정→보조 AI 원응답까지 정확하게 연결되는 목표 사례는3건이며, 이3건은 서로 다른 후단에서 진입하지 못했다.

| 9/29 기계 판정 시각 | Main record | 보조 AI | 확인된 첫 실질 차단 | 이후 경로 목표 접촉 |
|---|---:|---|---|---|
| 09:09:06.922 | 48810 | PASS→BUY | 분할 probe의 후속 방향 원천 미확보 | 09:14:00 |
| 10:27:49.612 | 48851 | 전송 기한 초과→WAIT | AI 응답 미확보; 같은 watch 재검토는 cooldown 뒤 종료 | 10:37:00 |
| 10:31:57.819 | 48852 | PASS | 후처리 `remote_buy_guard(risk=3)`가 WAIT로 변경 | 10:38:00 |

이 표는 실제 체결 수익이 아니라 당시 ask/비용에 결속된 후속 가격 경로다. 브로커 제출 실패나 미체결3건으로 분류하지 않는다. 원 기계 신호 부족과 신호 이후 실행 제한은 다른 원인이다.

**기존 정책 승계는 우수성 보증이 아니다.** 앞선 장후 생성기는 등록9가설·native 학습24기회/후단3기회, 별도 전체 refinement91가설을 비교했지만 교체 후보를 선정하지 못했다. 기존 정책을 기본값으로 가져온 것이며, 이번3건의 후단 차단이 적정하다고 검증한 결과가 아니다. [당시 장후 결과](postclose-outcome-readiness-closure-review-2026-10-03.md)의 Main/보조 원천 결손·후단 지원 부족을 정책 성능 PASS로 읽으면 안 된다. 성공100%/80% 보존율은 최종 탈락 조건이 아니었다.

이번 관점 전환으로 확인한 검토 대상은 **기계 판정 뒤의 추가 veto와 재검토/제출 원천 소비**다. 기계 숫자 임계값만 반복 탐색하면 이 사례를 회수하지 못한다. 현재 승계 정책도 비교 대상이며, 개선 후보를 찾지 못했다는 이유만으로 효과가 검증된 정책이라고 표현하지 않는다.

## 2. 분모·상승 정의·연결 수준

선행 연구와 같은9/29·9/30·10/2 원본을 사용했다. 기존 projection의 삼성전자 ENTER_NOW41행을 원 machine capture와 대조하고, 일자별 전체 pipeline에서 삼성전자 이벤트를 추출했다. AI trace는 `machine_observation_sha256`와 snapshot/record를 함께 확인했다. 알려진 record의 이력을 같은 attempt의 이벤트와 별도로 보존했다.

| 날짜 | ENTER_NOW 관측 | 목표 선도달 | 손절 선도달 | 미확정 |
|---|---:|---:|---:|---:|
| 9/29 | 35 | 8 | 7 | 20 |
| 9/30 | 1 | 0 | 1 | 0 |
| 10/2 | 5 | 0 | 0 | 5 |
| 합계 | **41** | **8** | **8** | **25** |

주 지표는600초 안에 왕복 비용+0.1% 목표가 가격-0.7% 손절보다 먼저 접촉하는 기존 유효 라벨이다.3일 모두 이미 연구에 사용했으므로 독립 검증 성과로 부르지 않는다.

전체41 중 AI 원응답에 정확히 연결되는 Main은17관측(목표3·손절3·미확정11)이다. 나머지24관측은 정확한 AI 연결이 없다(목표5·손절5·미확정14). 목표5개는 가까운 시각의 zero-base 발견→승격 이력과 대응되지만 옛 capture에 원 discovery source hash가 없어 **시각·동일 bundle·행동의 고유 근접 연결**로만 표시했다.8목표를8개 독립 Main 진입 기회로 세지 않는다.

상승을 단순600초 후 비용 전 가격 상승으로 바꾸면12관측, 비용 후 양수면7관측이다. 비용 전 상승12 중 정확한 Main 연결은4건이다. 추가 Main 사례09:33:42(record48834)는 비용 전+0.1832%이나 비용 후-0.1384%이고,09:33:59의 `signal_deadline_exceeded`에 걸렸다. 이를 비용 목표 선도달3건에 합치지 않는다.10/2 ENTER_NOW5건에 유효 목표 라벨이 없다는 사실도 당일 삼성전자의 장중 상승 구간 전체가 없었다는 뜻은 아니다.

## 3. Main의 정확한 세 사례

### 3.1 09:09 — 통과 후 분할 진입 원천에서 종료

- 원 기계 hash `69ba0c1e…`, promotion `ZBPROM-005930-1790640543975-5`, record48810.
- 09:09:11.160 AI PASS, BUY. `budget_pass`, `latency_pass`와 유동성 PASS가 확인된다. 과열 검사는 `PASS/overbought_not_available`로 기록됐으므로 과열 원천이 충분했다는 의미로 확대하지 않는다.
- 09:09:12.021 sizing plan: 목표2주.09:09:12.024 `entry_split_probe_admission_deferred`의 원인은 **`residual_source_path_unavailable`**다.
- 확인된 방향 group은 `price_tick`만 존재했다. `successor_ws_tick_ready=False`, `successor_live_micro_ready=False`, micro state=`insufficient`, successor venue=`UNKNOWN`이다.0B 수신 시계는0.189초 전이지만 원 tick event time=0이며, 신뢰 가능한 후속 pressure 원천이 준비됐다는 증거는 없었다. 신선한 수신 시계만으로 방향 원천을 대신하지 않았다.
- 같은 local submit attempt `eff53629f0024455a6365981eb1ffc37`의 종료는 `returned_false`, broker accepted=`False`다. 당시 commit `fb77a749`의 deferred 분기는 실제 제출 전에 False를 반환한다.

기존 Sentinel은 이 점을 `lineage_gap_superseded_without_terminal`로 표시했다. 원 이벤트의 source line5372·5374에는 보류와 local terminal이 존재한다. 따라서 **이번 점의 연결 결손 요약은 불완전했고 원인 복원이 가능했다.** 마지막 watch eviction의 `below_buy_ratio`만 보아도 실제 마지막 제출 차단을 놓친다. 같은 흐름의 뒤쪽에는 예산·latency 통과와 source defer가 명시돼 있기 때문이다.

원본: `data/pipeline_events/pipeline_events_2026-09-29.jsonl.gz`의5346/5362/5365/5371–5374행. [대상 record 원 이벤트](../../tmp/samsung-enter-now-nonentry-20261004/target-record-evidence.json)에 원 경로/line을 보존했다.

### 3.2 10:27 — AI 전송 기한 초과와 같은 watch 재시도 단절

- 원 기계 hash `1bf491ad…`, record48851, 원응답 trace `analyze_target:005930:1790645269863:62f84b91`.
- `provider_called=True`, transport=`http`, `timeout=True`, parse=`not_attempted_transport_timeout`, 화면 판정=`not_evaluated_transport`다. VETO 판정이 아니다.
- response_ms=6,181, HTTP provider total=4,601ms, 시도1회, HTTP wall deadline/timeout budget exceeded가 기록됐다. 여기서 말하는 timeout은 보조 AI의 OpenAI HTTP 경로이며 Kiwoom `kt00011`의2초 응답 결손으로 읽지 않는다.
- 결과는 `entry_ai_screen_unavailable_bounded_recheck`/WAIT다. 같은 record의10:28:03 runtime skip은 `entry_cooldown_active`, 잔여164초, pending recheck=`False`였다.10:28:05 WS snapshot gap도 있었고10:28:22에는 cooldown 사유로 watch가 종료됐다.
- 같은 watch에서 성공한 AI 재응답이나 브로커 제출은 확인되지 않았다. 이후 다른 watch의10:31 기계 ENTER와 혼합해 이 시도의 재시도 성공으로 계산하지 않는다.

**생산자는 bounded recheck 의도를 기록했지만 이 사례의 소비 흐름은 cooldown/eviction으로 끝났다.** 의도 필드만으로 실제 재검토 수행을 주장할 수 없다. 이것이 당시 원천의 재시도/상태 소비 점검 지점이다.

원본 pipeline line15795·15833·15834·15900과 [정확한 AI 원응답](../../tmp/samsung-enter-now-nonentry-20261004/target-cases.json).

### 3.3 10:31 — 기계·AI PASS 이후 별도 수치 veto

- 원 기계 hash `63e7cf06…`, record48852. AI raw/effective verdict 모두 PASS, semantic validation PASS다.
- 최종 action은 WAIT이며 reason에 `entry_setup_ready_ai_pass | remote_buy_guard(risk=3)`가 남아 있다.
- 당시 입력에서 다음3조건이 같은 count를 재현한다: 고가 대비 거리-0.182%≥-0.35%, tick acceleration0<1, 매도/매수 top3 잔량 비2.557≥1.35. large sell=false, micro VWAP 거리+20.44bp여서 나머지2조건은 해당하지 않는다. 보관되지 않은 후속 WS 값을 합성해 전체 runtime을 재생한 것은 아니다.
- 당시 commit `2c9ca579`의 guard는 risk flag2개 이상이면 BUY를 WAIT로 바꾸고 score를 최대74로 내렸다. pipeline의 `blocked_ai_score`/`entry_policy_no_buy_score_prior`는 뒤에 나타난 표현이다. 이 건을 **AI가 VETO했다거나 점수만75로 높이면 되는 문제**로 분류하면 원인을 놓친다.
- 이후09초 안 WS snapshot gap, cooldown152초·반등 재검토 최소0.6% 대비 실제0.091%가 기록됐고10:32:39 watch가 종료됐다.

원본 pipeline line16380·16384·16385·16497 인근·16592, [입력 risk 재구성](../../tmp/samsung-enter-now-nonentry-20261004/remote-guard-input-reconstruction.json). 이 guard는 원격 시세 비교값이 아니라 AI 응답 뒤에 실행되는 로컬 수치 규칙이다.

## 4. AI에 정확히 연결되지 않은 목표5관측

| 기계 관측 | 근접한 발견→승격 흐름 | 대응 record의 결과 | 연결 한계 |
|---|---|---|---|
|09:09:03|48810|§3.1의 Main09:09:06으로 진행|원 capture→discovery hash 직접 연결 없음|
|09:31:30|48827|`below_buy_ratio`, 매수 비중0.27·net buy qty-13,012;09:31:32 감시 종료|원 capture 연결은 근접 추정; discovery→attach→record는 source signature 연결|
|10:27:46|48851|§3.2 AI 전송 실패 흐름|원 capture 직접 연결 없음|
|10:31:51|48852|§3.3 후처리 WAIT 흐름|원 capture 직접 연결 없음|
|10:32:56|48856|cooldown116초, pending recheck=false;10:33:15 감시 종료|원 capture 직접 연결 없음|

이5관측의 가까운 zero-base event는 주문 권한이 없는 발견 판정이다.3개는 이미 위 Main3건의 앞단과 대응하므로 별도 실패3건으로 중복 합산하지 않는다.09:31의 발견 ENTER 후 별도 strength/momentum prefilter,10:32:56의 재발견 ENTER 후 cooldown도 추가 조사 가치가 있으나 정확한 machine-capture 계보 없는 수치를 정식 기회 지원수로 만들지 않는다.

## 5. 현재 코드와 과거 현상을 구분한 점검

이번 턴에 실제 selector를 읽은 결과 Main 선택 release는 `integrated-source-review-20261004-9c0c0632`, commit `9c0c0632faaf61c7c4434c2fa77b8673125e050d`다. 해당 물리 release의3개 관련 파일과 작업본은 byte가 같았다. 현재 effective loader의 KRX 정규 machine은 기존 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`다. 날짜 인자10/6의 effective lookup도 같은 정책을 반환하지만 미래 PREOPEN/PID 적용을 실행한 것은 아니다.

| 지점 | 현재 코드 직접 확인 | 결론 |
|---|---|---|
| 후속 tick source | `_probe_residual_successor_source_fields`가 현재 raw WS ticks에서 feature 재계산하는 경로와 live micro에 같은 WS를 전달하는 보완을 포함 |9/29 옛 코드와 다름. 해당 당시 submit WS의 완전한 입력이 없어 오늘 코드에서 같은 점이 통과한다고 확정하지 않음|
| AI unavailable | WAIT와 bounded recheck 의도는 존재. 의도 문자열만으로 실제 cooldown/queue 소비를 증명할 수 없음 |9/29 같은 watch의 미재시도는 확인. 현재 자연 재검토 수행 여부는 별도 확인 필요|
| remote guard | `_apply_remote_entry_guard`가 현재도 호출되며 risk≥2에서WAIT로 변경. 현재는 compatibility score50·submit candidate false를 명시 |추가 veto 자체는 남음. 과거의 score74 표면은 변경됐으며 현재도 상승을 막는 빈도/순효과는 미계산|

근거: [selector·정책·코드 SHA](../../tmp/samsung-enter-now-nonentry-20261004/current-code-policy.json), [옛 commit 코드](../../tmp/samsung-enter-now-nonentry-20261004/historical-code-evidence.json), 현재 [guard](../../src/engine/ai_engine_openai.py), [후속 원천 소비](../../src/engine/sniper_state_handlers.py).

따라서 기존 machine policy hash 유지와 전체 실행 코드 불변은 같은 말이 아니다. 반대로 코드가 보완됐다는 사실도 이3개 기회가 지금 모두 체결된다는 증거가 아니다.

## 6. 판단과 다음 점검 우선순위

이번 결과는 신호 희소 문제와 별개로 **이미 통과한 신호를 실제 진입으로 연결하는 과정의 손실**을 보여 준다. 먼저 다음 세 가지를 전체 ENTER 집합의 성공·실패 양쪽에서 비교할 필요가 있다.

1. **원천 전달·재검토 소비:** 현재 후속 source 보완이 동일 원천을 제대로 쓰는지, AI 전송 실패의 bounded recheck가 실제 예약·재평가 또는 명시적 종료로 소비되는지 검증한다. 원천 결손을 정상적인 무조건 진입으로 대체하지 않는다.
2. **추가 veto의 순효과:** machine+AI PASS 이후 remote guard 적용/비적용이 막아 준 손절과 놓친 목표를 같은 시각·route·비용·기회에서 비교한다. guard의 source/hard safety와 중복 soft 선별 역할을 코드상 분리해 검토한다. 원칙적으로 고수하거나 상승3건만으로 바로 삭제하지 않는다.
3. **전체 진입 정책의 대조:** 기계 점수만의 후보 대신 발견→기계→AI→후처리→제출 가능 여부를 포함한 후보를 incumbent와 비교한다. 기존 정책에도 동일한 승률·기회·결손 공개 기준을 적용한다. “교체 후보0”을 “기존 정책 적정”으로 보고하지 않는다.

이는 다음 점검 방향이며 정책 변경·guard 해제·배포 승인 요청이나 실행은 아니다. 현재 요청 범위의 과거 원인 분석을 완료했다. 고정 threshold/기계 후보 탐색을 추가 실행하지 않았다.

## 7. 검증과 산출물

- [41관측 전체 색인](../../tmp/samsung-enter-now-nonentry-20261004/case-index.csv), [8목표 상세](../../tmp/samsung-enter-now-nonentry-20261004/target-cases.json), [집계](../../tmp/samsung-enter-now-nonentry-20261004/summary.json).
- [원본 경로·물리 hash](../../tmp/samsung-enter-now-nonentry-20261004/source-manifest.json), [검증 receipt](../../tmp/samsung-enter-now-nonentry-20261004/review.json).
- 실제 AI hash/snapshot/record, local submit attempt id/terminal, timeout≠VETO, PASS≠최종BUY, 근접 discovery≠정확 native를 assertion으로 확인했다. 원본16개 source seal 보존, 오프라인 스크립트 compile·문서 link/owner·diff·print-only parser를 검증했다.
- 작업은 보관 파일 읽기와 격리 진단 산출물/문서 기록에 한정했다. 운영 코드 수정·후보 발행·서비스/PID 변경·provider/API/주문 호출은0이다. live trading suite·전체 장후 재생성은 실행하지 않았고 실제 미래 성능을 검증하지 않았다.
