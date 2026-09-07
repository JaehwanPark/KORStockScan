# 2026-09-07 장중 결함 2~5 보완·재리뷰

사용자 범위: `1항을 제외하고 2~5항 결함보완하고 코드리뷰, 결함이 없을때까지 반복실행`. 1항의 삼성 custody/주문 owner는 이번 변경에서 제외했다. 기존 10:20 기록은 [이전 모니터링](./2026-09-07-intraday-1020-monitoring.md), 실행 원칙은 Plan Rebase §1~§8 및 당일 체크리스트를 적용했다.

판정: 아래 코드·계측 결함은 구현→리뷰→추가 수정→재검증을 완료했다. 현재 PID 반영, scanner 전체 recall 정상, source 결손 복구 또는 실현 EV 개선을 뜻하지 않는다. 주문·계좌·수량·provider route·prompt·threshold·bot/PID·설치 trigger를 변경하지 않았다. Kiwoom 요청·응답/FID/REG/복구 구현 변경도 없다.

## 2. Scanner 보고의 포착 정상 오판

- 결함: venue/panel의 cadence 판정이 세션별 결과에 `any`를 사용해 정상 장전 세션으로 장중 결손을 가렸다. 충분한 계측 floor만 있으면 실제 promotion/후단 소비와 무관하게 `scanner_coverage_valid_submit_drought_downstream`을 반환했다. primary 분모는 venue 합계라 세션별 결손이 섞였다.
- 보완: 관측·예정 세션 모두의 floor, 마지막 수집 이후 gap, 세션 완전 부재를 검사한다. 예정 범위는 기존 설치 wrapper의 NXT 08시, KRX/NXT 정규장, NXT 장후 계약을 따른다. KRX 장전은 설치상 미예정이므로 수집 결손으로 만들지 않는다. 명시된 session과 capture 시각 불일치도 거부한다.
- 보완: 실제 SLA 내 promotion, fast/heavy/AI trace, terminal attribution을 확인한 뒤 판정한다. 미포착과 의도적 제외가 구별되지 않으면 `insufficient_evidence_scanner_recall`과 직접 blocker를 유지한다. promotion 이후 소비 결손은 `post_promotion_handoff_gap_candidate`로 분리한다. 제출이 있으면 새 보고 상태 `scanner_coverage_valid_with_submissions`를 사용하여 drought로 오기하지 않는다. 이 상태의 소비자는 JSON/Markdown 보고뿐이며 runtime 권한이 없다.
- 보완: `by_venue_session`에 독립 분모·named primary numerator·단계별 counts/recall을 출력하고, causal row의 benchmark→각 stage 지연 p50/p95를 별도로 추가했다. missing session은 UNKNOWN 진단 분모에 보존하며 정상 판정에는 사용하지 않는다. venue 합계는 diagnostic only로 표시한다.
- 검증: 정상 이전 세션+불량 현재 세션, 현재 세션 완전 부재, 미예정 KRX 장전 제외, session/시각 불일치, source 정상+promotion 0, 후단 trace 단절, 제출 존재, UNKNOWN 분모 보존 회귀검증을 통과했다.

당일 09:15 기존 artifact를 읽기 전용 재평가한 공식-master eligible episode는 KRX 정규장 25, NXT 장전 43, NXT 정규장 27이다. 관측된 promotion 비율 8%/0%/0%는 아직 **정상 승인된 시장 전체 recall이 아닌 partial observer 진단값**이다. master lookup, cadence, BBO coverage/resolved/right-censor floor가 남아 최종 상태는 `insufficient_evidence_scanner_recall`이다. 누락된 당시 BBO나 공식 종목분류를 추정·보간하지 않았다.

## 3. AI stale 입력 원인 계측

- 결함: source snapshot에는 원천 시각·age·quality가 있지만 일반 decision trace에는 blocker만 남아, 원천 age와 내부 지연을 구분하는 재검증에 필요한 값이 빠졌다.
- 보완: 기존 `ai_input_preflight_*` metadata 전달 경로에 source별 source/observed_at/age/quality/freshness limit/route를 넣고 decision trace에 보존한다. Entry-price 등의 prefix filter도 통과하는 기존 namespace를 사용한다.
- 경계: 계측은 source observed_at→snapshot capture 구간이다. exchange/local receive 두 clock이 없으면 외부 수신 전 지연은 `unproven_without_exchange_and_receive_clocks`로 남긴다. queue 원인을 임의 확정하지 않으며 stale 차단이나 snapshot/prompt input은 바꾸지 않는다.
- 검증: tape 10초 stale와 fresh BBO를 각각 보존하고 snapshot 내용·preflight 차단이 그대로임을 검증했다. endpoint metadata→trace 전달과 기존 OpenAI transport 테스트도 통과했다.

## 4. Parse 실패와 timeout 오분류 정정

이전 보고의 `OpenAI analyze_target parse 실패 2`는 잘못된 분류였다. 두 raw trace는 모두 response ID가 없는 HTTP wall-clock timeout이며 reason에 `while queueing provider call`이 기록돼 있다. request ID:

- `analyze_target:095610:1788736641911:5b7d6ca7` — 08:17:34, budget 5000ms, provider_total_ms 11974.
- `analyze_target:066570:1788739688460:537c543f` — 09:08:25, budget 5000ms, provider_total_ms 16121.

`parse_ok=false`만으로 parser 실행·실패를 주장하지 않도록 trace에 `parse_status`를 추가했다. timeout, preflight 미실행, 성공, 응답 receipt가 입증된 parse 실패, receipt 부족을 분리한다. 기존 parse_ok 호환 필드는 유지했다. queue/dispatch 재검증에 필요한 attempt/elapsed/wall-deadline/future-cancelled metadata도 trace에 보존한다. timeout 자체가 해결됐다는 주장은 하지 않는다.

10:20 cutoff 원천 trace 85건의 재분류 결과는 parsed 45, transport timeout 2, input preflight 미실행 38, 입증된 parse_failed 0이다. Provider 재호출 없이 기존 raw만 사용했다. timeout budget·worker 수·provider route 변경은 없다.

## 5. Micro 호가 결손을 건너뛰는 후행 경제성 평가

- 결함: `build_future_outcome`에서 canonical ordering이 유효한 행의 missing/stale BBO·quote age를 실행가격 계산에서만 건너뛰었다. 이후 정상 endpoint가 있으면 sequence가 이어진 것처럼 mature outcome을 만들 수 있었다.
- 보완: exact symbol/venue/session/epoch와 outcome 시간창 안의 missing/stale 호가를 rejected path timestamp로 보존한다. 그 결손을 포함한 horizon은 mature=false, 경제성 값은 None으로 유지한다. 기존 timestamp-regression 제외도 동일 경로로 유지하고 직접 사유 및 ordering subtype count를 별도로 보존한다. subtype을 primary reason 합계에 중복 가산하지 않는다.
- 격리: 다른 scope의 invalid row는 영향을 주지 않는다. 정상 경로에는 빈 진단 필드를 추가하지 않아 기존 outcome hash를 보존한다. 결손이 있는 기존 결과는 source 재계산과 hash 비교에서 차단되며 원천을 가진 해당 결과를 재생성해야 한다. 날짜 전체 폐기나 0 EV 보간은 없다.
- downstream: Main AI의 source commitment 및 action-neutral label 검증은 `rebuild_future_outcome_from_source` 결과와 저장 outcome/hash를 대조한다. 수정된 bridge를 우회하여 이전 결손 outcome을 현재 source 근거로 사용하는 경로가 아님을 확인했다.
- 검증: missing bid/ask, missing quote age, stale quote, timestamp-regression 각각에 정상 control은 mature, 결손 candidate는 immature/None이 됨을 검증했다. foreign epoch는 제외되고 정상 outcome hash도 보존된다.

당일 10:20 cutoff canonical stream 202,284행 중 SOR 정규장의 quarantined 69 + exceeded 142 = 211행이 모두 `market_path_consumer_ineligible`로 제외됐다. 나머지 202,073행의 path validator 통과는 BBO 완전성·경제성 승인이나 completed 표본 수가 아니다. KRX·SOR 세션별 원천을 분리했으며 SOR를 KRX/NXT 실행 근거로 바꾸지 않았다.

## 리뷰·검증과 반영 경계

- KORStockScan review gate로 producer→metadata filter→trace, snapshot→report→renderer, market stream→future outcome→Main AI 재계산 소비자를 확인했다.
- 반복 리뷰 보완: 현재 세션 0건, 미예정 KRX 장전 오탐, UNKNOWN 분모 유실, endpoint prefix filter 누락, 정상 outcome hash 변경을 각각 수정했다. 최종 수정 범위에 남은 코드 finding 0.
- 관련 9개 파일 pytest **853 PASS**. 이후 마지막 cadence 보완은 scanner 전체 **54 PASS** 재검증. Ruff, Python compile, git diff --check 통과. 체크리스트 parser PASS 및 `Intraday2to5SourceAcceptance0907` 인식을 확인했다.
- 읽기 전용 원천 검증: `tmp/intraday_20260907_2to5_repair_replay.json`. 입력별 고정 prefix 크기·SHA256과 partial tail 제외 기록을 보존했다. `tmp/intraday_2to5_cadence_source.jsonl`은 기존 09:15 report watermark에 제한한 source 재현이다. 이 cadence 전용 replay의 pipeline/AI 입력은 비어 있으므로 그 결과를 scanner 포착 증거로 쓰지 않았다. 원래 report의 episode 상세에 대한 판정과 구분해 저장했다.
- 메인 봇 재기동/runtime apply/Provider 호출/주문 API/비싼 전체 report 재생성 없음. source-only 예정 producer가 이후 새 코드를 읽을 수 있지만 실제 scheduled artifact와 현재 PID의 신규 trace receipt는 별도 확인 대상이다. 자동 반영 성공이나 수익 개선으로 선행 보고하지 않는다.
- rollback: 이번 네 구현 파일 및 대응 테스트의 diff를 되돌리는 source-only/계측 rollback. 기존 raw·owner ledger·PREOPEN 정책은 변경 대상이 아니다.

## 남은 source acceptance

| owner / shortage_id | 현재 판정 | 다음 acceptance |
| --- | --- | --- |
| scanner_recall_krx_20260907 | blocked_missing_evidence | 다음 정규 census에서 official master/hash, 세션별 cadence, causal stage/SLA 및 executable BBO floor 확인. 과거 영구 결손은 제외/진단 상태로 유지 |
| ai_input_timing_20260907 | implemented_not_loaded / blocked_missing_evidence | 별도로 허용된 정상 기동 후 exact natural trace에서 source timing 및 transport timing receipt 확인. exchange/receive 근거 없는 외부 원인 추정 금지 |
| main_ai_net_economic_20260907 | pending scheduled source-only consumer | 다음 정상 local outcome/label 생성에서 결손 horizon 제외 및 source-rebuild hash 확인. 신규 source-quality-valid mature 표본이 동일 corrected path를 통과하기 전 resolved로 표시하지 않음 |

실행·재확인 owner는 당일 체크리스트 `Intraday2to5SourceAcceptance0907`이다. 유효 표본 유입률·rolling 만료·maturity가 닫히지 않아 finite ETA는 만들지 않는다.

## 10:59 병합·재기동 후속 evidence

위 구현 완료 시점의 미기동 기록 이후 사용자 `커밋&푸시&main 병합, 필요시 우아한 재기동` 지시를 받아 진행했다. 기능 커밋 `886f8cbe`, main merge `cc86f4da`를 원격에 push했다. 관련 12개 pytest 파일 1,074 PASS, 반복 리뷰 finding 0과 diff/parser PASS 후 표준 `restart.sh`로 PID `46656 → 195755`를 교체했다.

- 신규 PID 실행 코드 `cc86f4da`, source dirty=false, exact-date runtime verify pass, mismatch/missing=0/0, runtime/dated policy fail=0/0, 퇴역 canonical env 15개 explicit OFF다. launcher commit은 기존 `327e8722`이지만 SHA256 `648b3cd86264d72d46b9c7ee8e8d175072a3f646ebe70425f73afc95b919cf1b`가 현재 파일과 동일하여 supervisor 교체는 하지 않았다.
- Samsung 오전 서비스는 inactive이며 기존 custody guard가 unresolved custody 없음으로 판정하여 prepare/commit 모두 `not_required`다. 별도 machine authority나 policy는 발행하지 않았다.
- 전시장 broker snapshot(10:57:46/10:59:26) hash는 `9d8db7db131e997278cc964061d77a49949555f7e4b9c04dd62149b3da5f0a24`로 동일했다. 005930 40주(위젯 20주 및 기존 미확정 잔여 20주), 010140 episode 10주, 042660 episode 20주와 매도 미체결 0003725/0021509/0027015/0027165/0028708을 보존했다. 요청에서 제외된 1항 잔여 custody owner 확정은 수행하지 않았다.
- 10:59:09 WS LOGIN ACK, 10:59:22 이후 첫 체결 0B/호가 0D, main/scanner/sniper heartbeat를 확인했다. 원천 evidence: `tmp/intraday_merge_restart_20260907.log`, `tmp/intraday_merge_restart_before_20260907.json`, `tmp/intraday_merge_restart_after_20260907.json`, `tmp/intraday_merge_restart_acceptance_20260907.json`.
- AI 계측은 신규 코드 기동 확인으로 상태를 갱신하되, 자연 호출의 metadata/transport trace receipt·정규 census/label 소비·EV 개선은 아직 별도 acceptance다. 위 표의 `implemented_not_loaded`는 재기동 전 기록이며 현재 natural receipt 확인 owner는 `Intraday2to5SourceAcceptance0907`이다. 실행 중 생성되는 data cache/report/runtime artifact는 소스 커밋에서 제외했다.
