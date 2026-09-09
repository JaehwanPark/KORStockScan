# 2026-09-09 10:00 장중 모니터링·micro 저장 cap 적용

## 판정

09:36~10:00 KST 모니터링 결과는 `YELLOW`다. main과 독립 machine owner는 진행했으나 source-only micro forward collector가 09:05:13에 2GiB projection guard로 정상 self-stop했다. EBS/root filesystem 확장 뒤 사용자가 적용을 명시 승인해 projection stop만 partition hard-total과 같은 4GiB로 올렸고, main을 표준 graceful 경로로 한 번 재기동했다.

이는 저장 용량 cap이며 매매 수량·자본 cap, threshold, provider, 주문·청산 또는 hard safety 변경이 아니다. 09:05 이전의 drop/reject를 복원하거나 오늘 source-quality 및 경제성 acceptance를 완료하지 않는다.

## 10:00까지 관찰

- 기존 main PID `24260`은 10:00까지 살아 있었고 heartbeat/scanner/sniper가 전진했다. Samsung 오전 owner는 두 BUY가 미체결 뒤 취소되어 신규 보유 없이 정상 종료했다.
- 저가주 machine은 exact-date timer/preflight를 따랐다. 10:00 현재 오전 profile은 `NO_TRADE` 또는 정상 terminal이고, 한국전력 오전은 20주 `TARGET_OPEN`이다. 09:59 late-morning 네 profile은 `READY/bar_evaluated_no_signal`로 자연 관찰 중이었다. owner·주문·custody를 main과 합치지 않았다.
- `SimProbeIntradayCoverage0909` 범위의 source-only feedback은 `actual_order_submitted=false`를 유지했다. rising-missed workorder 2건은 구현됐지만 자체 broker/runtime 권한이 없는 source-only 개선이며, runtime family 선택과 동일시하지 않았다.
- 10:05 후속 sentinel은 main AI-confirmed unique 72, latency-pass unique 17, submitted/holding-started 0/0으로 `SUBMIT_DROUGHT_CRITICAL`이었다. exact attempt conservation은 PASS지만 top blocker는 insufficient history·latency danger·window buy value였고, 경제 bundle/실현 EV 표본은 0이라 threshold를 완화하지 않았다. 독립 market census도 official master/cadence/executable-BBO/resolved floor 결손으로 `partial_diagnostics_ready`; KRX/NXT forward-exact provider reach가 모두 0이라 scanner 정상이나 자연 기회 부재로 확정하지 않았다.
- risky-micro source-only rolling 표본은 575 resolved/18일/323종목이지만 선택 profile 비용차감 EV가 `-0.014587%`이고 당일은 `-0.036661%`다. cap 상향은 원천 수집 지연을 막는 운영 보완일 뿐 양(+) EV나 실주문 승격 근거가 아니며, 현행 promotion은 non-positive EV와 별도 PREOPEN·사용자 승인 부재로 계속 차단한다.
- panic-sell-defense cron 경고는 KOSDAQ industry source 결손이 반복된 source-quality warning이다. 정상 snapshot에서 일시 PASS로 회복했으나 10:00에도 최근 오류 warning이 남아 있으므로 threshold 변경이나 main 재기동 원인으로 사용하지 않았다.

## cap 원인과 변경

- 09:05:13 receipt: producer 0B `185,971`, 0D `232,247`, path drop `127`, depth drop `0`, invalid depth timestamp reject `38`; writer/depth-writer 오류는 없었다.
- 이전 projection은 `2,302,937,758` bytes로 2GiB stop `2,147,483,648` bytes를 약 7.24% 초과했다. 실제 writer bytes는 path `147,968,747`, depth `243,481,502`였으므로 즉시 실제 partition hard-total 초과가 아니라 장마감 projection guard였다.
- EBS 확인 뒤 root는 약 125GiB이고 available bytes는 `42,452,365,312`였다. 5GiB low/1GiB critical watermark를 충분히 상회했다.
- [path_journal.py](../../src/engine/scalping/micro_reversion/path_journal.py)의 기본 `max_projected_partition_bytes`만 2GiB→4GiB로 올렸다. 기존 `max_partition_total_bytes=4GiB`, shard 512MiB×최대 8, retention 및 disk watermark는 유지하고 projection cap이 hard-total을 초과하면 구성 오류로 거부한다.
- 변경 commit은 `5cda9104d1ef9ecd3fdce024b629e22ca9b6ad7d`다. frozen callback baseline은 재측정하지 않았고 PathStoragePolicy 호환 변경과 나머지 module AST를 각각 고정했다.

## 리뷰·배포 receipt

- cap 관련 observation test `23 passed`. storage/collector/canary 묶음에서 기존 9/8 ingress 수리 `7077831a`의 WebSocket hash가 frozen guard에 반영되지 않은 contract drift 1건을 추가로 발견했다. 원래 baseline hash와 리뷰된 replacement full hash를 함께 고정해 임의 후속 변경은 계속 실패하도록 보완했고 최종 묶음 `194 passed`로 닫았다. 이 보완 테스트 commit은 `3cfc4e3b`이며 runtime code 변경은 없다. restart/authority handoff `17 passed`, compile, `bash -n restart.sh src/run_bot.sh`, `git diff --check`도 PASS했다.
- 재기동 직전 read-only broker snapshot은 KRX/NXT complete, position quantities `[10,20,25]`, open BUY `0`, open SELL `0001493/0021516/0021521` 각 10주였다. owner registry·custody·policy·runtime env 5개 hash를 고정했다.
- `restart.sh`는 기존 PID를 정상 종료하고 10:01:29 새 PID `135119`를 시작했다. 새 PID는 commit `5cda9104`, startup `source_dirty=false`; exact-date runtime verifier는 `status=pass`, PID pass, selected 18, missing/unverified/runtime-policy/dated-override failure 0이다. Samsung handoff는 `morning_owner_not_active/not_required`였다.
- 재기동 직후 broker snapshot의 position quantities와 세 미체결 SELL은 동일했고 open BUY는 계속 0이었다. 위 5개 owner/policy hash도 동일했다.
- 새 PID의 10:02:23 micro receipt는 `healthy_observer_canary`, stop false, 0B `3,767`, 0D `4,052`, writer/depth-writer 2/2, queue/drop/worker/writer/storage/projection 오류 0, 최소 free bytes 약 42.27GB다. callback p95/p99는 0.096/0.107ms이고 거래·주문 권한은 false다.

## 남은 acceptance

- 10:07:24 첫 5분 projection은 `976,924,381` bytes로 4GiB 아래였다. 같은 receipt에서 0B `29,632`, 0D `37,979`, partition `70,026,465` bytes, writer/depth-writer 2/2, drop/error/projection breach 0, canary healthy/stop false를 확인했다. capacity repair의 배포·자연 counter acceptance는 충족했으며 through-close source 품질 수용은 별도다.
- 10:13:25 재확인은 projection `938,487,041` bytes, 0B `67,635`, 0D `80,002`, drop/error/breach 0, stop false였다. 다만 신규 invalid depth timestamp reject 1건이 enqueue 전에 격리되어 상태는 `healthy_observer_canary_with_source_row_exclusions`다. collector는 지속하되 exact rejected-row exclusion이 미입증이므로 Provider hold는 유지한다.
- 09:05 이전 path drop 127과 invalid depth timestamp 38은 exact scope exclusion이 입증되지 않았으므로 당일 Provider replay/promotion hold를 유지한다. 오늘 장마감까지 clean window가 이어져도 과거 결손을 복구됐다고 바꾸지 않는다.
- panic-sell-defense source-quality warning, 독립 시장 상승 분모/recall, main submit/fill/terminal/net EV, machine TARGET_OPEN terminal 및 비용 차감 EV는 각 기존 checklist owner에서 계속 대사한다.

## 10:18~10:46 YELLOW 수리·재리뷰·재기동

### 결론

코드와 운영 원인이 확인된 두 YELLOW는 닫았다. micro timestamp exclusion 증명은 current-process exact receipt가 완전할 때만 통과하도록 보완했고, market-panic breadth는 승인된 market-weakness entry guard의 300초 freshness 입력이라는 실제 소비 계약에 맞춰 shared read coordinator의 `runtime_required` 예약 슬롯을 사용하도록 수정했다. 최종 commit은 `15a8a4ede2e521ec5a9b862dc5675914051a3119`이며 코드리뷰·보완·재리뷰 뒤 미해결 finding은 0건이다.

전체 장중 상태를 GREEN으로 바꾸지는 않는다. main submit drought와 scanner official-master/BBO/cadence/maturity 결손은 여전히 자연·경제성 YELLOW이며, 이를 없애기 위한 threshold·provider·수량/cap·주문·hard-safety 변경은 하지 않았다.

### 수정과 검증

- `micro_reversion.canary_monitor`는 current-process rejection 합계와 0B/0D counter, bounded receipt 수·연속 index·PID/symbol/item/venue/type/epoch/check 시각/reason/stage, stale reason count가 모두 일치할 때만 exact row exclusion을 증명한다. 누락·malformed·counter mismatch·64건 tail 초과는 fail-closed한다. 이전 PID의 행이나 과거 결손을 합성하지 않는다.
- `market_panic_breadth_collector`는 KOSPI/KOSDAQ별 attempt/admission/HTTP/return-code/row/rate-limit provenance와 all-market readiness를 기록한다. admission 뒤 HTTP 200·return code 0인데 semantic row만 빈 경우에만 1회 재시도하며 admission·transport·rate-limit 실패는 재호출하지 않는다. token-wide 5회/초와 다른 execution-critical 예약은 그대로다.
- Kiwoom 공식 reference gate는 commit `234560d213acd8871ae344b5481aecd2f30287fa`의 `kiwoom/_data/kiwoom_api_spec.json#ka20003`, `kiwoom/specs.py`, `kiwoom/core/errors.py`, Postman collection을 10:29:22 KST에 확인했다. 현행 POST `/api/dostk/sect`, `api-id=ka20003`, `inds_cd=001|101` 계약과 일치한다.
- collector/canary/wrapper/notifier/machine guard/forward collector/attribution 관련 357 tests, Ruff, compile 및 `git diff --check`가 PASS했다. review 중 tuple 직렬화 전 형태, malformed receipt 예외, receipt-type/counter 불일치, admission 실패 재시도 문제를 추가 발견해 모두 보완했다.

### 자연 receipt와 재기동 불변성

- 최종 코드의 10:42·10:44·10:46 cron은 연속 성공했다. 10:42 기준 breadth는 source-quality `ok`, KOSPI31/KOSDAQ34행이며 두 요청 모두 1회, shared-read admitted, HTTP200, return code0, rate-limit false였다. 10:48 주기도 같은 계약으로 DONE했다.
- 10:55:14 자동 error detector는 `summary_severity=pass`, detector7/초기화 실패0/운영 mutation0이다. artifact freshness·panic cron·process/thread·resource·lock 관찰이 모두 pass이고 장후 항목은 `not_yet_due`, Swing은 의도된 OFF로 분리됐다. 이는 운영 경보 YELLOW 해소 근거이며 submit/scanner 경제성 acceptance를 대신하지 않는다.
- 재기동 전 broker 대사는 KRX/NXT complete, 보유 7종목(`005930`25, `010140`10, `015760`20, `028670`20, `035720`20, `042660`20, `181710`20), 미체결 SELL11, open BUY0이었다. registry·owner env·symbol policy·runtime env·market-weakness policy 5개 SHA를 고정했다.
- 표준 graceful restart로 PID135119를 정상 종료하고 10:44:51 PID190811을 시작했다. 새 PID는 commit `15a8a4ed`, source-dirty false, exact-date verifier PASS(selected18, missing/unverified/runtime-policy/dated-override failure0)다. Samsung handoff는 `morning_owner_not_active/not_required`였다.
- 재기동 뒤 보유·미체결 SELL11/open BUY0과 다섯 SHA는 정확히 같았다. 10:45:26 fresh micro는 stop=false, 0B1168/0D1277, reject/drop/queue/worker/writer/projection breach0이었다. 이어 10:53:58 자연 invalid-depth timestamp 1건이 발생했고 exact receipt1/1·counter/type 일치, coverage `complete_current_process`, `exact_rejected_row_exclusion_proven=true`, stop=false로 새 계측의 자연 acceptance까지 닫혔다.

### 남은 YELLOW

- 09:05 이전 path drop127·invalid timestamp38과 PID135119의 과거 결손은 복원되지 않았다. 새 계측은 PID190811 이후 current-process 결손만 증명하므로 오늘 Provider replay/promotion hold와 through-close 확인을 유지한다.
- scanner report의 `900340`, `0001A0`은 실제 보통주지만 검증된 전일 official common-stock master에 없어 `official_symbol_master_lookup_gap`이 맞다. 다음 canonical master와 cadence/BBO/maturity source가 닫히기 전 recall 정상이나 기회 부재로 재분류하지 않는다.
- 10:05 main은 AI-confirmed72·latency-pass17·submitted0이다. submit/fill/terminal/net-economic 표본이 없어 drought는 계속 YELLOW이며 안전·가격·threshold를 완화하지 않는다.
