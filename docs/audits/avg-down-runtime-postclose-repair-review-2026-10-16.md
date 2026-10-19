# AVG_DOWN 런타임·장후 연구 보완 검토 — 2026-10-16

## 범위와 기준

- 사용자 지시: 배포본 `922b9cbc3`, PID `3729660` 기준 보완 → 코드리뷰 → 수정보완 → 커밋. 배포는 별도 세션에서 수행한다.
- 기준 커밋: `922b9cbc370c4c6c002b3c1fcdb3ed061719e4a2`.
- 독립 worktree: `/home/ubuntu/KORStockScan-worktrees/avg-down-lifecycle-20261016`; branch: `fix/avg-down-lifecycle-20261016`. 원 workspace의 미커밋·동시 작업은 포함하지 않았다.
- 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [당일 checklist](../checklists/2026-10-16-stage2-todo-checklist.md), [원 구현계획](../proposals/avg-down-shared-rebound-receipt-and-pyramid-retirement-implementation-plan-2026-09-28.md).
- 14:11–14:15 KST에 확인하고 14:44–14:46에 재확인한 선택본·프로세스: `/proc/3729660/cwd`는 `KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3/src`, 시작 ticks는 `19142841`.
- `data/runtime/runtime_release_selection.json`의 선택 SHA가 기준 커밋과 일치한다. `data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-16.json`은 PID `3729660`, `passed=true`, `pid_passed=true`, 검증 시각 `14:11:31+09:00`이다.
- `data/runtime/mechanistic_entry_policy/consumed/2026-10-16/3729660.json`은 `continuous_reversal_pid_consumption_v6`, 같은 release commit, family SHA `75af4c634cc9bd3695e2e2d810371a3ff9978b5de8945c853757838631df54ce`이다. 이 영수증은 수정 전 배포본의 소비 증거다.

## 결함과 수정

| 결함 | 보완 | 확인한 경계 |
| --- | --- | --- |
| 실제 Main은 continuous reversal v6를 소비하지만 물타기 평가는 이전 mechanistic 경로만 사용 | 선택된 family의 기존 native snapshot을 읽고 동일한 순수 dispatcher로 평가 | Main ready/claim·정책 상태 기록을 소비하거나 변경하지 않음. 원 정의가 반등인 matched branch만 ADD 신호가 됨 |
| Main 고정관심 보유의 `SCALP_BASE`와 entry 정책 scope가 불일치 | 원 admission의 코드·날짜·세션·route·generation을 검증한 뒤 정책 조회에만 `SCANNER` 사용 | 실제 보유 tag·custody는 유지. 이전 날짜/세션의 유효 admission도 보유 동안 유지. 다른 owner는 채택하지 않음 |
| 정규장 통합시장의 정책 venue가 canonical `KRX`와 불일치 | 기존 venue resolver의 정규화 사용 | native 원천은 정확한 item의 SOR/KRX/NXT partition을 계속 사용 |
| native 신호가 만료되어도 새 holding permit의 유효기간이 남을 수 있음 | native 5초 expiry를 permit 검사와 최종 submit 직전 모두 검사 | 기존 permit 2초, source·position digest, 가격·수량·계좌·cooldown·공통 stop 및 hard safety 유지 |
| ADD 완료/취소/다음 주문 초기화가 체결 map을 지워 최초 BUY identity로 돌아감 | 보유 기간 전체의 exact BUY legs를 누적하고 receipt v2로 저장·복원 | `(order_no, execution_no, qty)` 불일치 거부. v1도 검증 후 읽음. 실제 SELL 완료/재진입에는 원 보유 legs 정리 |
| 현재 ADD reason이 체결 후 반등평가 전환 대상에서 누락 | `shared_main_rebound_entry` 체결을 기존 `POST_ADD_EVAL`로 연결 | 신규 주문 제출만으로 전환하지 않고 실제 accepted fill에서 전환 |
| 장후 lineage에서 누락 BUY identity끼리 같다고 판단 가능 | BUY·bundle·vote policy hash와 최소 유효 투표 수를 검증 | 결손은 `lineage_gap_buy_fill_identity` / `lineage_gap_policy_identity` / `lineage_gap_valid_vote`로 유지 |
| partitioned 장후 보고서가 보유 신호·투표 원본을 버리고 항상 빈 목록 재생 | per-position 신호·exact BUY·원 요청 참조를 봉인해 동일 strict 완료/비용 cohort에서 재생 | 원 요청 bytes를 봉인 시점과 소비 시점에 검증. 미검증/변조 입력 제외. 대용량 결손은 명시적 row exclusion |
| ADD 투표를 exit 장후 owner의 독립 수치 후보로 제시 | `ADD_REBOUND` 후보 grid 제거, incumbent 진단 재생만 유지 | 실제 ADD 시점은 선택된 Main machine이 소유. exit 숫자 연구의 기존 범위 유지 |

새 runtime adapter는 역할 패키지 `src/engine/scalping/avg_down_rebound.py`, 회귀는 `src/tests/test_avg_down_rebound.py`에 배치했다. engine root에 새 모듈을 만들지 않았다. 장후 assembly의 code contract에도 새 adapter와 replay consumer를 포함했다.

## 리뷰와 재검증

1. producer → holding scope → Main family → source preflight → ADD vote → permit → 주문/체결 → receipt 복원 → 장후 완료/비용 소비 순서로 검토했다.
2. 최초 회귀에서 발견한 aftermarket admission bucket 대소문자와 stream closure의 `nonlocal` 누락을 수정했다. 기존 partitioned source-gap 기대값도 실제 봉인 입력 계약에 맞춰 검증했다.
3. 재리뷰에서 원 요청 검증의 시점을 보완했다. 봉인 후 원 payload 파일이 바뀌면 해당 VALID 투표는 소비 시점에 제외된다. 실제 원 요청 capture/ledger/assembly를 사용하는 fixture로 정상·미검증·봉인 후 변조를 검증했다.
4. 실제 receipt handler의 ADD 체결 → pending cleanup → identity 유지 → 재기동 복원, 취소 후 다음 ADD·복수 재기동, v1 bytes 보존을 검증했다. 실제 v6 family/native buffer fixture에서 ADD 판독 후에도 같은 Main claim이 가능함을 확인했다.

최종 대상 검증: **1,522 passed, 40.97초**.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/pytest -q -p no:cacheprovider \
  src/tests/test_avg_down_rebound.py \
  src/tests/test_holding_exit_vote.py \
  src/tests/test_holding_path_vote_replay.py \
  src/tests/test_trade_review_report_revival.py \
  src/tests/test_sniper_scale_in.py \
  src/tests/test_ai_engine_openai_transport.py \
  src/tests/test_reversal_extended_policy.py \
  src/tests/test_research_json_stream.py \
  src/tests/test_main_trailing_source_assembler.py \
  src/tests/test_holding_exit_observation_report.py \
  src/tests/test_holding_vote_numeric_successor.py \
  src/tests/test_scale_in_split_order_plan.py \
  src/tests/test_engine_location_gate.py
```

추가 gate도 통과했다: 변경 Python 21개 compile, `git diff --check`, 문서 상대 링크 4개, print-only backlog parser(`--print-backlog-only --limit 500`, exit 0). 실제 provider·broker 호출, 광범위 장후 보고서 재생성, external sync는 이 코드 검증에 포함하지 않았다.

## Kiwoom 공식 참조

복원·체결 경로 수정 전 2026-10-16 `14:21:33+09:00`에 공식 저장소 HEAD를 확인했다: [Kiwoom REST API commit 953e5db](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f).

- 확인 경로: `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `00`·`kt10000`, `kiwoom/realtime/schemas.py`, `decoders.py`, `events.py`, `kiwoom/core/client.py`, Postman PRD/MOCK의 `kt10000`.
- 해당 revision에는 `kiwoom_docs` 디렉터리가 없다. 주문/체결 식별자 `9203/909`, 수량 `900/902/911/915`, 누적대금 `903`, 가격 `901/910/914`, route `2134–2136`을 대조했다.
- 이번 수정은 기존 accepted execution의 내부 보유 identity를 보존한다. REST 요청·WebSocket parser/FID·인증·REG/REMOVE·연속조회 wire 계약은 수정하지 않았다. 기존 SDK/Postman 차이로 새 해석을 만들지 않았다.

## 배포 인계와 남은 수용 범위

- **코드 수정·대상 검증 완료이며 배포·재기동은 미실행이다.** 다른 세션은 이 branch의 커밋을 실제 선택본과 대조한 뒤 기존 배포 절차로 인계한다. 별도 작업의 미커밋 파일을 덮어쓰지 않는다.
- 기준 PID의 `KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED`, KRX/NXT/PREMARKET별 활성값은 모두 `false`다. 이 활성 계약은 변경하지 않았다. 따라서 이 커밋만으로 자연 ADD 유효 투표·주문이 발생한다고 판정할 수 없다. forensic context를 live 입력으로 승격하지 않는다.
- 당일 정책·bootstrap·새 PID 소비는 [당일 checklist](../checklists/2026-10-16-stage2-todo-checklist.md)의 `DirectFamilyPreopenPolicyHandoff` 등 기존 소비 확인 owner가 맡는다. 배포 후에는 새 source hash로 정상 장후 assembly/report 및 strict handoff가 생성·소비되는지 별도 확인한다. 이전 산출물을 새 코드의 결과로 간주하지 않는다.
- receipt v2는 새 reader가 v1과 함께 읽는다. v1 전용 옛 코드로 rollback하면 새 v2 receipt의 복원이 거부된다. rollback 시에는 이 reader 호환성을 포함해야 하며 원 receipt 삭제·과거 체결 재생성으로 맞추지 않는다.
- 자연 실행 수용은 동일 보유의 반등 신호 → 유효 ADD 투표 → 실제 submit/accepted/fill → 청산/실비용으로 확인한다. 현재 paired ADD/NO_ADD 경제성은 관측되지 않았으며 `null`을 유지한다. 완료 보유의 PnL만으로 물타기의 추가 효과를 주장하지 않는다.
- S15·VCP·PYRAMID 신규 판단/튜닝은 복원하지 않았다. 과거 미결 주문의 복구·정산 소비는 유지했다. 주문·provider·threshold·env·정책 selector·프로세스에 대한 실제 변경은 이 작업에 없다.

## 2026-10-19 후속: 필수 투표 입력의 활성 계약 복구

### 기준과 확인된 결함

사용자의 정상작동 점검 후 다음 액션·구현·코드리뷰·수정보완 지시를 수행했다. 기준 선택본은 다른 세션이 17:30에 배포한 `34798c60c43984ab9fb97b07e224f9a29883503d`, PID `1889422`, 시작 ticks `4311591`이다. 격리 branch `fix/avg-down-vote-input-20261019`에서 수정했으며 원 workspace의 문서·wrapper 정리·수동관리 변경은 포함하지 않았다.

직전 선택본 `e7f4e2e8f`의 17:24 KST까지 ADD 검토는 삼성전자49350 71건, 알테오젠49375 125건, 주성49374 17건이 모두 INSUFFICIENT/AI 호출0이었다. 보유 컨텍스트·holding flow의 OFF가 `forensic_context_only=true` → `ai_market_snapshot_missing` / `holding_flow_evidence_missing` / `rebound_tape_or_quote_flow_missing`으로 이어졌다. 10/16 코드 수정은 배포되어 있었으나 필수 투표 입력이 optional context 활성 계약에 종속되어 실제 작동을 막았다. 이 통계는 실제 AI 응답 수가 아니다.

### 구현과 교체·제거 처분

| 기존 함수/dispatch | 처분 | 대체 또는 현재 소비자·이유 |
| --- | --- | --- |
| vote worker의 `holding_score` 조회 dispatch 2곳 | removed | 동일 worker의 `holding_path_vote`로 이관. 기존 tick/분봉 조회 owner·호출 주기 안에서 exact request code와 metadata를 사용한다. 퇴역 score endpoint는 호출하지 않는다 |
| 투표 입력이 전역 context OFF에만 종속된 판단 | consolidated | `holding_path_vote_policy.runtime_vote_input_enabled`가 기존 native loader의 당일 loaded receipt·source/target 날짜·bundle hash를 검사한다. 기존 holding context builder를 재사용하며 새 모듈/별도 builder/활성화 파일은 만들지 않는다 |
| `holding_decision_context_enabled`의 일반 holding/flow/overnight 계약 | retained | 일반 holding/flow 소비자와 기존 promotion/시장별/stage env 계약에 필요하다. 새 receipt는 정확히 `holding_path_vote` 입력에만 적용하며 overnight는 계속 퇴역이다 |
| `_holding_context_call_views`와 disabled forensic reader | retained | 일반 AI 소비자·원 입력 결손 진단에서 runtime/forensic 분리를 유지한다. 과거 forensic 객체의 재사용·승격은 하지 않는다 |
| `build_path_vote_input`의 무조건 context projection | removed | enabled runtime context만 투영하고 forensic 및 blocked/disabled/잘못된 source-quality 입력을 거부한다. typed gap에는 원 입력 정책 receipt를 보존한다 |
| 정규장 SOR 실행 뷰의 기존 stage 집합 | consolidated | 기존 `_integrated_sor_execution_view_proof`에 현재 vote stage를 등록했다. 동일 source·route·수량·시세 증명을 통과해야 하며 기초 거래소를 추정하지 않는다 |
| 일반 disabled 분봉 legacy 조회 분기 | retained | 활성화되지 않은 일반 holding 소비자가 사용한다. 투표는 당일 정책이 유효할 때 기존 exact-route metadata 조회로 이동한다 |
| 30초 차단 로그에서 판단 잠금만 보이는 경로 | retained | 현재 gate 사유를 보존하며 마지막 실제 반등 평가 사유·시각을 함께 기록한다. 진단 필드는 주문 판단에 쓰지 않는다 |

별도 validator/CLI/wrapper/registry/스케줄은 추가하지 않았다. 기존 호출의 동적 import와 역할 package 소비자를 대조했다. 정책의 source-code contract에는 현재 필수 입력을 만드는 `holding_decision_context.py`와 SOR 증명 owner `ai_market_snapshot.py`를 추가했다. 유예된 제거 항목은 없다. 기준34798 대비 non-test source 6파일 `+79/-11`(순증68), 기존 test 3파일 `+158/-4`(순증154), 기존 review 문서 1파일 `+40/-0`이다. 파일 이동·새 source/test 파일은 없으며 순증은 당일 정책에 결속한 입력 활성·진단과 3시장 통합 회귀에 사용했다.

### 활성 범위와 안전 계약

- 활성화 근거는 이미 native 로더가 source/strict handoff까지 검증한 당일 보유 투표 정책이다. baseline fallback, rejected, 만료, 잘못된 hash/date 영수증은 새 입력 경로를 활성화하지 않는다. 일반 holding/flow 및 전역 multi-timeframe promotion을 켜지 않는다.
- 해당 builder는 원 WS/분봉·기존 broker snapshot cache를 재사용한다. 투표 분봉 조회는 호출자가 선언한60개를 사용하며 일반 context의430개 범위를 상속하지 않는다. token 없이 구축하고 investor/추가 tape/멀티타임프레임 auxiliary fetch를 하지 않는다. HOLD deferral 권한은 false다. 필수 입력이 유효해진 이후의 provider 호출은 기존 due worker·symbol cadence·동일 모델/endpoint 안에서 진행한다.
- stale/충돌/source blocker·실행 가능한 호가·매수 identity·보유 변경·공통 stop·수동/퇴역 owner·주문/계좌/수량/한도 검사는 유지한다. 두 유효 투표는 permission이며 Main 반등 신호를 만들거나 주문을 직접 허가하지 않는다.
- 이 변경은 필수 입력의 활성 의미를 바꾼다. 별도 배포 세션은 새 code contract와 실제 당일 정책의 검증된 handoff를 정식으로 준비해야 한다. 새 정책 로더의 거부를 env 강제 설정이나 과거 영수증 재사용으로 해소하지 않는다.

### 공식 API 확인과 검증

2026-10-19 `17:33:28+09:00`에 공식 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 다시 확인하고 새 checkout에서 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 ka10003/ka10080 request·response, `kiwoom/core/client.py`, Postman PRD/MOCK를 대조했다. `kiwoom_docs`는 해당 commit에 없다. 두 POST endpoint(`/api/dostk/stkinfo`, `/api/dostk/chart`)와 `stk_cd`의 KRX/NXT/SOR suffix, 시간·원/주 단위, auth/continuation/오류 계약을 유지한다. SDK JSON/Postman query 차이는 기존 gap으로 보존하며 wire/parser/auth/REG/주문을 변경하지 않는다.

최종 묶음 **11파일 1,558 PASS / 57.04초**다. 장전·정규장·장후의 전역 context OFF + 유효 당일 receipt에서 정상 input → 기존 collector → durable ledger → 첫 투표 INSUFFICIENT → 독립 두 번째 투표 PASS를 검증했다. malformed/expired/rejected receipt, forensic 및 source-quality 차단 입력, 일반 holding/overnight 비활성 유지도 포함한다. 최종 재리뷰의60개 조회 제한 후 context/분봉6개, 평가 시각 정합성 후 반등/공통stop/expiry28개를 추가 검증했다. 최초 확대 검증의 진입 가격 fixture1건은 metadata 조회 mock 누락으로 실패했고 기준/수정본 개별 실행은 모두 PASS였다. 동일 입력을 metadata refresh에도 공급하도록 기존 fixture만 보완한 뒤 전체 묶음을 통과했다. 실 API는 테스트 차단기가 거부했으며 실제 통신으로 채우지 않았다.

대상 파일: `test_holding_decision_context.py`, `test_holding_exit_vote.py`, `test_holding_path_vote_replay.py`, `test_ai_market_snapshot.py`, `test_sniper_scale_in.py`, `test_avg_down_rebound.py`, `test_holding_vote_numeric_successor.py`, `test_holding_flow_override.py`, `test_multi_timeframe_context.py`, `test_engine_location_gate.py`, `test_ai_engine_openai_transport.py`. 변경 Python9개 compile, 문서 상대 링크5개/owner/authority, print-only parser(exit0) 및 diff 검사도 통과했다. Shell·스케줄은 변경하지 않아 bash 검사는 생략했다. 최종 자체 리뷰 범위의 미해결 결함은0이며 운영 배포·현재 PID 소비·자연 체결 수용은 별도다.

이번 후속은 코드·대상 검증·배포 인계까지다. 실제 provider/broker 호출, 배포·Main 재기동·env/정책 변경·장후 보고서 재생성·external sync는 수행하지 않는다. 자연 소비는 [10/19 checklist](../checklists/2026-10-19-stage2-todo-checklist.md)의 기존 `DirectFamilyPreopenPolicyHandoff` owner에서 새 PID의 정상 입력·자연 요청/응답·유효 투표와 반등/주문/체결을 확인한다. 과거 INSUFFICIENT 원문과 경제성 null은 보존한다.


## 2026-10-19 통합: 세 시장 AVG_DOWN과 승인된 배포

사용자는 `1a9e00396`와 통합·리뷰·수정보완 및 배포·재기동을 승인했고, 추가로 장전·정규장·애프터마켓 모두 물타기가 가동되도록 지시했다. 기준은 선택본34798c60c/PID1889422/start4311591이며, 격리 `deploy/avg-down-sor-integrated-20261019`에서 b54fe963f의 필수 입력 복구와1a9e00396의 Main SOR 진입 수리를 통합했다. 앞 절의 배포 미실행 표기는 당시 결과이며 이번 승인과 실행은 별도로 기록한다.

- 세 시장 모두 당일 native holding-vote receipt에 결속한 입력 구축·collector·durable vote ledger를 사용한다. 기존 buy window는08:03~08:40,09:03~15:10,16:00~19:40이며 세션 내 휴장·종목 eligibility와 hard guard를 유지한다. 모든 보유에 무조건 ADD하지 않는다.
- 실제 추가매수 submit owner의 기본 route는 장전NXT·정규장SOR·애프터마켓NXT다. 세 시각을 기존 split-submit fixture에 매개변수로 넣어 broker 직전 route와 stop 우선 차단을 확인한다. Main 최초 진입의 SOR binding과 AVG_DOWN의 기본 route owner는 각각 현재 소비자를 유지한다.
- frozen holding 연구 계약에 필수 context/SOR proof source 두 개가 추가된 만큼, 기존 `intraday_release_handoff`의 exact Git source pair·전체 dependency generation·family별 extension으로 인계한다. 원 PREOPEN 정책 digest·source·threshold는 재발행하지 않는다. 장후 연구는 현재 입력과 실제 완료·비용 근거를 계속 분리하며 이번 수리만으로 paired 경제성은 인정하지 않는다.
- 교체/제거: 기존 Main route binder는1a9의 공통 binder로 consolidated, vote dispatch 두 곳은b54에서 removed, 기존 code-handoff generation은 과거 immutable receipt 소비를 위해 retained, 새 exact generation은 현재 candidate의 native pre-stop/selected 소비자가 사용한다. 새 module·CLI·wrapper·schedule·retired trading authority·임시 호환 경로는 추가하지 않았다. 기존 audit와`DirectFamilyPreopenPolicyHandoff` owner를 재사용한다.
- 리뷰 범위: merged source→context→vote→permit→각 시장 route→broker guard 및 frozen 정책→현재 source generation→native handoff. 역사 fixture의 inventory와 cleanup bytes는 원 generation에 고정하여 현재 입력 목록 확대가 과거 증거를 변형하지 않도록 했다. 새 입력 변조·family extension 누락은 거부한다.

검증·실제 배포 및 PID 소비 근거는 `tmp/avg-down-sor-deploy-20261019/`에 따로 보존한다. 실제 체결과 비용 경제성은 자연 evidence가 있을 때만 수용한다.

통합 검증: 대상16파일 **1,864 PASS /103.71초**, native 인계 회귀 **2,534 PASS /46.09초**(합4,398), Python19파일 compile 및 diff·print-only parser PASS. 기존 fixture의6개 세션/stop 조합도 PASS다. 기준34798 대비 통합 범위 규모(이 결과 문단 전 집계)는 source 10파일 +215/-21 (순증194), tests 9파일 +446/-16 (순증430), docs 3파일 +178/-0 (순증178)이다. 파일 이동은 없으며 순증은 필수 입력 복구·SOR source 결속·당일 정책 인계 및 실패 회귀에 사용했다. 현재 자체 리뷰 미해결 사항은0이다. 원 workspace 변경은 포함하지 않았다.
