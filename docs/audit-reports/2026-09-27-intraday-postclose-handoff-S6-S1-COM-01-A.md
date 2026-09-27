# 장중 생산자–장후 소비자 S6 수리 보고서 — S1-COM-01-A scanner 압축 reader

실행일: 2026-09-27 KST. 인계: [S1 공통 원천 보고서](./2026-09-27-intraday-postclose-handoff-S1.md) `S1-COM-01-A`, [S6 압축 원천 첫 묶음](./2026-09-27-intraday-postclose-handoff-S6.md) `S5-FIN-02`. 범위는 scanner pipeline event 생산·압축 원천 → `strategy_position_performance_report` loader → SCALPING/SCANNER fact·scale-in projection과 첫 보고서 소비자다. 정규 장후·PREOPEN·DB 재동기화는 실행하지 않았다.

## 결정·원천 증거

9/23 원본 `data/pipeline_events/pipeline_events_2026-09-23.jsonl`은 없고 `.jsonl.gz`는 **437,234,985 byte**다. 같은 경로의 압축 생산자 `pipeline_raw_archive_identity_v1` 영수증은 논리 원천 SHA `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`와 압축 세대의 크기를 기록한다. S1 원천 감사의 `scalping_scanner_candidate_promoted=3,216`과 `scalping_scanner_runtime_target_attach=3,639`은 서로 다른 stage 건수이며 전체 raw/API 모집단이 아니다. 이번 작업에서 6.5 GB 논리 원천을 다시 읽거나 fact를 재생성하지 않았다.

실패 회귀를 먼저 추가했다. 동일 promotion 한 행을 `.jsonl.gz`에만 두면 기존 `_load_scanner_promotion_events`는 **0건**을 반환하고, SCALPING/SCANNER fact는 `missing`이 됐다. 같은 행을 비압축 `.jsonl`에 두면 1건이었다. 과거 9/24 생성 fact가 당시 틀렸다는 결론은 내리지 않는다. 결손은 **압축 후 재처리** 경로다.

| 생산자 → artifact → 첫 소비자 | 수리한 계약 |
| --- | --- |
| `pipeline_event_logger` → 날짜별 base·cross-midnight late JSONL → 압축 생산자 | 기존 생산 형식과 `src/utils/jsonl_io.py`의 no-follow strict plain/gzip reader를 재사용한다. 각 part의 물리 SHA·크기, 해제 논리 SHA·크기, 행/객체 수를 기록한다. 존재하는 압축 생산자 영수증의 원경로·논리 SHA를 해제 결과와 대사한다. 생산자 영수증이 없으면 `not_observed`로 남기며 원본 동일성을 주장하지 않는다. |
| base/late → scanner promotion loader·scale-in projection | base와 late를 순서대로 읽고 plain/gzip 공존본의 내용이 다르면 거절한다. 동일 event 중복은 한 번만 투영하며 동일 stage·symbol·promotion ID·시각의 상충 내용은 임의 선택하지 않고 차단한다. 날짜·symbol·시각·명시된 promotion ID와 알려진 venue/session을 검사한다. base/late의 논리 SHA를 묶은 별도 `source_generation_sha256`을 기록한다. |
| loader → SCALPING/SCANNER fact·첫 보고서 | scanner stage별 원본·유효·중복/격리 건수, venue/session별 유효 건수와 미관측 원천 모집단 `null`을 fact-sync 영수증에 남긴다. 실패 중간의 부분 집계에는 `counts_complete=false`를 붙인다. 압축 원천 부재·손상·상충 또는 scanner 거래와 promotion이 연결되지 않는 경우 새 DB fact 교체 전에 `source_blocked` 영수증을 남기고 이전 세대를 보존한다. DB 장애 fallback 보고서도 로더가 찾은 scanner provenance를 버리지 않는다. |

잘못된 날짜·비어 있는 promotion identity·stock code 결손처럼 해당 scanner 행의 위치가 알려진 경우 행을 격리하고 사유별 건수를 남긴다. 식별할 수 없는 malformed JSON·손상 gzip은 전체 원천 검증 실패다. 유효한 빈 파일은 `valid_empty`, base와 late 모두 부재하면 `source_missing`이다. 9/23 이후 SCANNER fact가 있는데 해당 원천에서 causal promotion을 찾지 못하면 `scanner_lineage_unmatched`로 차단한다. 현 `TradePerformanceFact` DB에는 행별 scanner 격리 컬럼이 없으므로 안전한 부분 교체를 주장하지 않고 **기존 DB 세대를 보존**한다. 이 수리는 가격·비용·주문·정책의 권한을 바꾸지 않는다.

## 실패 회귀·리뷰·검증

fixture는 비압축/압축/동일 내용 공존 1회 소비와 논리 SHA, 압축 생산자 영수증 일치·불일치, plain/gzip 내용 충돌, late plain/gzip과 중복 scale-in 행, 잘못된 날짜 격리, malformed JSON·손상 gzip 차단, 원천 부재/빈 입력 구분, promotion ID 우선 매칭·venue/session 불일치·UTC→KST 시계, DB 교체 전 차단 및 DB 장애 fallback 보고서의 scanner 분류를 검증한다. S1의 처음 실패 fixture와 fallback·promotion ID 회귀도 구현 전 실패를 확인한 뒤 수리했다.

자가 리뷰에서 압축 reader만 고치면 DB 장애 fallback이 scanner 분류를 다시 `unknown`으로 지우는 결손, 두 stage 모집단을 합칠 위험, 명시적 promotion ID보다 최신 동일 symbol 이벤트를 고르는 문제, UTC 이벤트 시계와 KST BUY 시계 비교 문제를 찾아 각각 보완했다. 재리뷰에서 malformed/충돌 원천이 부분 scale-in 투영을 확정하지 않고 prior fact를 보존하는 경계를 확인했다. 이 묶음의 코드·fixture 미해결 결함은 0건이다.

| 검증 | 결과 |
| --- | --- |
| 영향 pytest: `test_strategy_position_performance_report.py`, `test_jsonl_io.py`, `test_threshold_cycle_wrappers.py`, `test_postclose_summary_handoff.py` | **158 passed** |
| 변경 Python 파일 `py_compile`; `git diff --check` | 통과 |
| wrapper `bash -n`·계약 | wrapper 변경 없음. 기존 wrapper 계약 pytest 포함; `bash -n deploy/run_threshold_cycle_postclose.sh` 통과 |
| 문서 링크·owner·권한, print-only backlog parser | 연결된 S1/S6 문서 존재; parser 통과, 외부 sync 없음 |

## 남은 경계·인계

현재 9/23 전체 압축 원천을 이 작업본으로 다시 읽거나 DB fact·보고서·stage terminal을 재생성하지 않았다. 따라서 **fixture의 동세대 수용**과 실제 9/23 자연 소비는 별도다. 압축 원천의 실제 전수 스캔 시간·CPU/RSS/I/O와 stage별 3,216/3,639 대사, 새 terminal→strict의 같은 세대 수용은 S7에서 측정한다. 선택 릴리스·정규 PREOPEN·실제 PID·자연 비용 후 결과는 S8에 남긴다. `S5-FIN-05`는 다음 자연 source date에서 profile manifest/detector 결손을 재현할 때까지 조건부이며, `S5-FIN-02` AI 압축 reader와 앞선 S6 작업본·SOR→KRX 작업본도 보존했다. 현재 KST 9/27 일일 체크리스트는 없고 9/28 체크리스트만 있으므로 이를 9/27 현재 실행 owner로 대체하지 않았다.

실주문·정책·서비스·provider·threshold·배포를 변경하지 않았고 정규 장후작업·PREOPEN을 실행하지 않았다.
