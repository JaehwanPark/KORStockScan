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


### 배포 gate 재리뷰

첫 후보d37a67dc7의 active Main parity는128scope/76,800행/598hit·신호 hash 일치였다. 그러나 live bootstrap은8940ea4ad 계보(holding code c34bc30c, stop code12103eeb)를 소비하고, delay는 원7f prepared-code handoff를 유지한다. 첫 pre-stop은 새 handler의894 source pair 미등록으로 차단됐다. 두 원본의 exact pair를 결속하고894 holding inventory의 새 입력2개에만 extension을 추가했다. 두 원본·세 family의 정상/입력 변조/extension 실패18회귀를 통과했다. 원 manifest/PREOPEN/policy/selector 및 PID1889422는 변경하지 않았다.

격리 P5 첫 시도도 intake에서 `startup_native_machine_closure_invalid`로 실패했다. native verification 자체는 PASS였고193개 source·aux manifest/frozen inventory·delay2개가 관측됐지만, 장중 verifier가 `load` 대신 이미 읽은 bundle의 `validate`를 호출하여 bundle 관측만0이었다. 기존 P5 owner에서 두 native 경계를 함께 관측하고 semantic validate 성공 후에만 기록하도록 보완했다. 새 generator나 캐시 PASS는 만들지 않았다. 거부된 native validate는 계속 실패하며 원 실패 영수증과 diagnostic bytes를 보존한다. 기존 load 관측은 현재 preopen 소비자 때문에 retained, validate 관측은 같은 verifier의 현재 intraday 소비를 보완한다. 운영 정책과 runtime apply 권한은 변경하지 않는다.

재리뷰 후 native 인계·P5 회귀2파일 **2,615 PASS /60.17초**다. 그중 native bundle load/validate 정상과 validate 거부를 포함한다. 보완4개 Python compile 및 diff 검사 PASS이며 배포 gate를 다시 실행한다. 첫 후보와 실패 영수증은 삭제하지 않는다.


### 현재 장중 인계의 격리 소비 보완

6b199823e의4개 native pre-stop gate는 모두 PASS였지만 P5는 `prepared_code_source_not_regular_bounded`로 차단됐다. 현재 PID의 stop/holding은 원894 정책을 이미 소비한 intraday handoff가 owner이며 두 family의 별도 prepared-code receipt는 발행되지 않았다. 기존 resolver가 준비용 receipt만 찾던 경로를 같은 owner에서 보완했다. source/selector/원 manifest·policy·정책 코드 inventory와 실제 소비된 handoff·consumption·현재 PID/start/cwd를 검증한 뒤 기존 read-only validation proof로 전달한다. 기존 prepared-origin 분기는 미래/준비 소비 때문에 retained이며 runtime receipt를 새로 발행하거나 Main 정지로 증거를 만들지 않는다.

격리 child도 source hash·정확한 handoff 경로·원 manifest·정책/날짜·소비 receipt·PID identity·frozen 원문 결속을 독립 검증한다. parent는 child 종료 후 동일 PID identity를 다시 확인한다. 신규 apply/주문/PID 소비 권한은 false이며 기존 Main/수동/퇴역 custody와 OS 격리는 유지한다. 실제 source 파일이 없는 축약 역사 fixture는 원 Git tree가 소유하던 selector 파일을 복원하여 검증하고, 현 generation과 섞지 않았다. 과거59·76-source와 현재 전체 generation을 각각 보존했다.

사용자가 전달한 artifact_freshness alert도 보존했다.18:21~18:22 관측은 선택34798/PID1889422의 scanner current source coverage 결손이며, fixed-watch20과 scanner0을 구분한다.0B 지연/결손·route snapshot 결손·유효 no-match는 각각 원 진단으로 남기고 report partial을 full 또는 주문 실패로 바꾸지 않는다. 해당 health artifact의 operational mutation은0이다. 이 관측을 새 AVG_DOWN 코드/PID의 자연 소비로 간주하지 않는다.

최종 보완 검증: native 정책 인계·격리 child·P5 네 파일 **2,770 PASS /90.51초**, 앞서 통합 런타임16파일1,864 PASS(합4,634), 현 코드 generation capability4개431 PASS·Python25파일 compile·print-only parser·diff PASS다. 마지막 수정 후 자체 리뷰 범위 미해결0이다. 범위34798 대비 source 13파일 +322/-22 (순증300), tests 12파일 +564/-37 (순증527), docs 3파일 +202/-0 (순증202)(이 문단 전 집계)이며 module 이동/신규 CLI는 없다. source 순증은 필수 vote 입력과 실제 source generation을 유지한 안전한 정책 인계·격리 소비를 위해 사용했다.


### 보존 PREOPEN scope와 현재 native Main closure

399b05164의4개 pre-stop gate도 PASS였다. 다음 P5는 `startup_main_native_full_validation_required`로 차단됐다. native readiness는 원 PREOPEN/checklist를 보존하는 장중 scope를 명시하고, 이번 호출에서 Main의 N.validate·aux manifest·frozen validation·원천 digest는 실제로 다시 검증한다. 기존 P5가 readiness 전체의 scope를 current_full 하나로 한정했던 결함을 보완했다. scope 원문은 유지하며 독립 `same_invocation_selected_intraday_native_validation` basis로 선택본·원 PREOPEN commit과 이번 호출의 전체 Main closure를 검증한다. 단순 sealed-generation PASS나 과거 PASS 재사용은 계속 거부한다.

새 누락 회귀에서 child가 native bundle 관측 누락을 독립 재검사하지 않는 것도 확인했다. child가 실제 policy의 family SHA·target·bundle 관측과 full closure를 다시 결속하도록 수정했다. 이 누락·알 수 없는 scope·원본 commit 불일치·basis 바꿔치기를 포함한 격리86회귀 PASS/36.49초다. 기존 immutable 후보 및 P5 실패 영수증은 보존했다. native4gate PASS가 P5 또는 실제 기동 성공은 아니라는 구분을 유지한다.


### 보조 reader 계보와 18:37 원천 색인 경고 보완

8e90f15f1의 P5는 보조 reader의 원 c32689f5와 선택 cleanup eacdffe2를 같은 origin inventory로 합치면서 차단됐다. 원 manifest/code inventory와 현재 selected bytes를 각각 유지하고 이미 등록된 exact reviewed pair만 건너도록 parent와 child를 함께 보완했다. 실제 진단 trace는 `final-8e90f15f1/inventory-conflict-diagnostic.log`에 보존했다. 같은 native parity에 포함된 SOR session source3a4b68c7→dfd0ff3b도 P5의 exact reviewed history에 결속했다. native 신호128scope/76,800행/598hit parity는 별도 사전 gate로 계속 필수다.

사용자가18:37 전달한 TRAILING_SOURCE_INDEX_GAP은 실제 invalid=`append_chain_gap` 고착이었다. index의 source signature는17:41의1,227,927,333바이트, 검증 prefix cursor는801,760,912바이트였고 원본은18:39에1,484,851,207바이트였다. 현재 source를 pending으로 보고하지 않고 정상 완료로 오인하는 조치는 하지 않았다.

기존 `main_trailing_source_store`에만 복구를 확장했다. 기존 background 유지보수가 pipeline append-chain invalid에 한해서 최대64MiB cache의 SQLite snapshot을 보존·검증하고, 원 writer의 partition/physical file lock에서 exact state·inode·archive를 재검사한 뒤 전체 prefix migration을0부터 다시 시작한다. 큰 snapshot I/O는 native writer lock 밖에서 최대0.5초로 제한하고, lock 안의 reset은50ms progress budget을 둔다. 원문 JSONL은 읽거나 변경하지 않는 reset이며 실제 raw 재검증은 기존8MiB/50ms build_step이 수행한다. 완료 전 read_rows/generation은 계속 pending이다. archive 생성/검증 실패·잠금 경합·원본 교체·세대 변경은 invalid를 보존한다. 기존 queued append의 bytes가 명시적 prefix 범위에 이미 포함되면 backfill owner에 맡겨 이중 집계·재무효화를 방지한다. 로그에는 InputPending의 상세 사유를 함께 기록한다.

교체·제거: 기존 sticky append-gap 상태는 archive+전체 prefix 재검증으로 consolidated, 다른 invalid/namespace는 기존 fail-closed reader가 현재 소비하므로 retained다. 기존 raw writer·파일/SQLite schema·CLI·스케줄·매매 판단은 retained이며 새 module/producer framework/임시 wrapper는 없다. failed index snapshot과 raw bytes는 보존한다. 복구 시작은 검증 완료나 경제성 승격이 아니다.

회귀는 writer·색인·장후 재생·격리4파일292 PASS/75.28초, 추가 custody25 PASS/4.81초, 최종 source/native114 PASS/43.18초다. 과거 재생 fixture가 새 live enabled 계약을 누락한 부분을 보완했다. writer drain의 v2 오류 사유 차이는 수정 전 b54에서도 동일하게 실패함을 재현했고, 원문 변경에 대한 native/legacy 두 정식 거부를 검증하도록 fixture를 보완했다. 운영 source guard는 완화하지 않았다. 원 검증 실패 로그는 보존했다.

최종 source/native114 PASS 및 현재 generation 인계18 PASS/17.86초, Python29개 compile·diff·print-only parser PASS 후 리뷰 미해결0이다. baseline34798 대비 현재 전체 범위는 source 14파일 +483/-36 (순증447), tests 15파일 +720/-42 (순증678), docs 3파일 +228/-0 (순증228)(이 문단 전 집계)다. 추가 source 순증은 기존 P5의 실제 장중 source 계보·격리 경계와 고착 색인의 보존/검증 복구에 사용했다. package/CLI/스케줄 이동은 없다.


### Native reader 추가 의존성 결속

3eedb6e5c의 네 native pre-stop gate는 PASS였지만 P5는 `startup_main_manifest_dependency_set_changed`로 차단됐다. 실제 native reader는 manifest의 원천/ledger/baseline 외에 선택본의 Python reader 의존성16개를 반환하고, 기존 격리 consumer는 그 추가 집합을 누락했다. 기존 owner에서 관측 목록을 선택본 Git 원문·실제 파일 SHA에 결속하고, child가 정확한 의존성 집합·signature·source hash를 독립 재검사하도록 보완했다. 원 manifest와 역사 code inventory를 변경하지 않는다. selected/src 밖·symlink·누락·signature 변조를 거부한다. 기존 manifest reader는 retained이며 중복 구현이나 새 module은 추가하지 않았다.

격리 child를 포함한 해당93회귀 PASS/41.64초다. 새 후보에서 P5를 다시 수행하며 통과 전 incumbent1889422를 유지한다. 네 gate의 PASS와 P5·실제 PID 소비는 각각 별도다. 실패 영수증 `7564ee7ada914cfb94df5bb0229c8d7a`와 원본 의존성 bytes는 보존했다.


### Prepared/live manifest의 소비 경계

eab2c040d의 P5는 intake와 native Main closure를 통과하고 실제 격리 child에 도달했으나 `startup_code_context_intraday_manifest_changed`로 거부됐다. 준비 manifest와 실제 기동 manifest는 생성 시각·env 파일 위치·direct-family 선택 기록이 각각 다르다. 기존 child가 두 원문 전체를 동일시한 결함을 수정했다. 각각 content seal·원 파일 source SHA·소비 handoff를 유지하고, family policy receipt·전체 env overrides·날짜·원본 release 계보를 정확히 비교한다. 원 manifest를 재발행하지 않는다. 생성 metadata 차이는 통과하되 sealed env 변경과 manifest seal 변조는 거부하는 OS 격리 회귀를 포함하여 해당95개 PASS다. 기존 source/receipt readers는 각 generation의 현재 소비자로 retained이며 새 경로나 wrapper는 없다. 실패43506176045f4df3b1bc11e61385e861의 원문과 현재 incumbent를 보존한 채 새 후보 P5를 수행한다.


### 실제 child의 보조 reader와 손절 미래 관측 소비

5dea19f3d의 P5는 격리 설치를 통과한 뒤 native Main 로더12개를 실제로 실행했다. 보조 reader는 검증된 manifest의 reader 원본c326를 delegation에 전달하지 않아 거부됐고, stop은 carry 정책의 미래 미소비 vote tail 검증에서 운영 writer flock을 시도하여 격리 장벽이 거부했다. 이후 consumer의 context_invalid는 그 금지 시도에 따른 후속 결과였다. 실패1b960c16cd90463e8c4583bfd34ebceb와 isolation 원문은 보존했다.

기존 P5 owner에서 원 semantic source와 충돌하지 않는 manifest의 next-session/reader 원본 hash를 그대로 전달한다. child의 exact reviewed-pair·Git/source/manifest 검증은 유지한다. stop의 기존 미래 tail reader를 공통 snapshot 함수로 통합하고, 실제 OS 격리·현재 Main proof·정확한 stop policy/source/target/data-root를 재검증한 child만 운영 잠금 없이 같은 native snapshot 검사를 실행한다. partial·과거 행·scope/position·inode/stat/prefix 변경은 계속 거부한다. 일반 runtime/research reader는 기존 native writer lock을 유지한다. `_future_unconsumed_vote_tail_locked`는 removed, 공통 `_future_unconsumed_vote_tail_snapshot`은 consolidated이며 기존 wrapper와 격리 branch가 현재 소비자다. 새 module·CLI·스케줄·운영 허용 flag는 없다.

해당 C/stop 묶음은 최초271 PASS/2 fixture 실패였고, 새 fixture의 Path import와 공유 dictionary alias를 보완했다. 같은 실제 OS 격리의 신규6개는 모두 PASS/8.78초이며 negative case는 각각 의도한 native 사유도 확인한다. 기존 writer lock·tail·source 및 격리 회귀를 포함한 고유273개가 통과했다. exact 두 원본/세 family 인계18개 PASS/17.08초다. 새 stop 코드 generation의 holding capability를 정식 fixture producer로 다시 검증·게시한 후 새 P5를 실행한다. 원 정책·PREOPEN·현재 PID는 계속 보존한다.


### Parent의 scope 영수증 대사와 검증 시간

2dd0b5df5의 기본120초 격리 시도는 금지 동작0건 상태에서 timeout5acb60e5c25a4d4da036899311e3cf87이었다. 기존 CLI의 허용 범위인300초로 별도 재실행37f9d1ecac634dfc998434e82fc4b857을 수행했고, 실제 child의12개 consumer가 모두 loaded/승인 parent-only였으며 findings와 금지 동작은0이었다. 원 실패 bytes는 유지한다. 300초는 read-only 격리 검증 예산이며 runtime 주문·시세·AI deadline 변경은 없다.

Parent의 마지막 delegation 대사에 남아 있던 current_full 전용 조건이 실제 intraday scope를 거부했다. 같은 기존 owner에서 해당 대사를 함수 하나로 이관하고, 검증된 native basis·scope를 그대로 비교하도록 보완했다. run/request·Main 정책·native PID·manifest 정확한 집합·해시 재사용 수치·authority false 검사는 모두 유지한다. 기존 inline 검사는 removed, `_validate_native_delegation`으로 consolidated했으며 run_validation의 현재 소비자 하나다. 새 module/CLI/validator framework는 없다. Parent의 나머지 delay·request/consumer 원천·logical source 대사도 기존 native 함수로 독립 점검하여 모두 PASS였다. 이 진단을 P5 완료로 승격하지 않고 새 immutable 후보의 전체 P5를 재수행한다.

두 scope와 변경 scope/basis/PID/manifest/authority 거부를 포함한 parent86개 PASS/8.60초다. 변경 Python30개 compile·전체 diff 검사도 통과했다. 자체 리뷰에서 확인된 변경은 수정했으며 실제 배포는 전체 P5 성공 후에만 수행한다.


### 19:44 운영 전환과 큰 캐시 cleanup 보완

최종 code deb996a22689ac08e171ea38966d070d63d236ee는 P5 9052d6c8074f42c09309f3e7e998f559의12소비자 로딩·원천 재대사·child 종료 PASS, findings/금지 동작0건 후 ordered 배포를 완료했다.19:44:02 native 완료/PID2399775/start5109403/cwd 해당 release/src를 확인했다. 원 PREOPEN·policy/env·manual SHA와 failed attempts는 보존했다. quantity의 동일 승인 과거5건 projection 및 현재 observer 게시도 기존 producer/lock에서 exit0이었다. 초기150초 startup의 실제 producer timeout75와 source-only 실패 영수증은 보존하며, 후속 full 게시만으로 원 실패를 성공으로 바꾸지 않는다. 최신19:48:39 health는 artifact warning/log scanner pass다. 과거19:45 실패와 현재 원천·장후 코드 계약 warning을 구분한다.

인덱스의 원 실패 cache snapshot은 생성됐지만 reset이 진전되지 않았다. 실제 selected owner를 한 차례 호출하여 DELETE FROM rows가50ms에서 OperationalError:interrupted로 rollback됨을 확인했다. 원 trace는 final-deb996a22/index-native-recovery-attempt.json이다. 기존 source owner에서 원 snapshot과 invalid 상태를 유지하며128행/최대8MiB·minute128개씩 정리하도록 수정했다. 각 DELETE 전에도 원50ms deadline을 확인하고, derived partition이 비었을 때만 cursor0 prefix migration으로 전환한다. raw는 변경하지 않는다. 다른 source 행·부분 정리 중 source 교체·unbounded/NULL body 거부와 archive 원본 전체 보존을 검증했다. 기존 bulk-delete 경로는 removed, bounded cleanup으로 consolidated이며 native background와 승인된 source-only 복구가 현재 소비자다. 새 module/CLI/스케줄은 없다.

전체 source/handoff2,572 PASS/57.91초 후 명시적 per-row deadline 재리뷰를 수행했다. 최종 source29개 PASS/5.29초 및 exact generation18개 PASS를 확인했고 compile·diff·print-only parser를 실행한다. 이 후속은 원천 cache 수리이며 Main의 정책·주문·시장 시간값을 변경하지 않는다. 실제 prefix 전체 검증·현재 native generation 소비는 별도 확인한다.

### 원천 복구 완료와 이미 소비한 generation 보존

19:59:38 source-only native 검증에서 invalid가 해제되고 전체 prefix와 append chain이 일치했다. 원본 쓰기·네트워크 시도·정책 변경·주문은0이다. 후속20:05:09에는 실제 선택 deb996a226의 reader(SHA f052d476)로 다시 검증했다. 원천1,769,045,113바이트, raw273,086행/selected4,083행, prefix cursor=catchup_end1,723,264,151, producer_end=당시 raw 크기이며 generation95cf2f51d663d81d26c56e53a9e90930c5d4276d10822e2cae77e4131bec73a4다. 이는 native chain 증명이며 whole-file SHA는 아니다. 마지막 index gap 로그는19:46:05이며 failed cache snapshot과 원 JSONL을 보존했다. 실제 운영에서 bounded DELETE 실행 여부와 복구 완료를 혼동하지 않는다. 큰 캐시 cleanup 코드는201c5e5ae source-only 소비 및 대상29회귀를 검증했으며 Main2399775의 코드 소비는 여전히deb다.

201c5e5ae 후보의 재리뷰에서 이미 소비한deb의 prepared-delay를 최신 dependency generation으로만 검증하던 결함을 발견했다. 기존 intraday owner에deb의14개 exact source SHA와 전체 dependency/extension closure를 동결하고 source-store SHA를 selector로 사용한다. 파일별 대체 hash나 일반 fallback은 허용하지 않는다. 이전 generation은 현재 PID의 원 정책·영수증 인증 때문에 retained이며, 최신 generation 소비는 기존 native pre-stop/selected owner가 담당한다. 새 module·dispatch·CLI·schedule은 없고 제거를 유예한 중복 구현도 없다. 두 generation·두 origin·세 family의 정상/입력 변조/extension 누락36회귀 PASS/29.93초다. 보존된deb receipt가 현재 consumer인 동안 exact historical closure를 유지하며, 이 회귀가 제거·변경 시의 closure test다.

20:03:53 health에서 artifact_freshness는warning, log_scanner는PASS였다. 원19:45 missing-sentinel 실패는 보존하고 현재 full health 성공으로 승격하지 않는다. 남은 warning은 entry_cancel_wait/rising_missed/holding_vote 연구 generation과 main_trailing_research_handoff의 현재 code 결속이다. 원 연구·PREOPEN bytes와 비용/outcome null은 유지한다. 원천 복구만으로 연구 완료를 선언하거나 보고서를 재생성하지 않는다.

20:00 native terminal은 market_close_unresolved_scalping_positions/005930 한 건이며20:03 process_health FAIL의 직접 근거다. 이 terminal을 정상 종료로 바꾸거나 재기동으로 새 receipt를 만들지 않는다. 세 시장 AVG_DOWN 통합 배포는deb/PID2399775에서 완료했으며, 추가 helper 변경은 clean candidate/native 인계 검증까지 준비하고 Main 재기동은 보류한다. 종료 보유·체결/비용 정합은 기존 HoldingProfitExitSourceContractRepair owner에서 실제 journal·broker terminal로 해소해야 한다. 현재 자연 AVG_DOWN 표본은19:56의 scalping_cutoff 및 stale tick/quote 입력 차단으로 유효 투표·주문·체결을 입증하지 못하며 경제성도 미검증이다.

### 사용자 재기동 후속과 동일 선택본 복구

이후 사용자가 재기동·가동 확인을 명시적으로 지시했다.20:05 EOD와20:10 장후 wrapper가deb에서 실행 중이므로 해당 선택본을 유지했다. 후속6746ac681 후보는 native parity128scope/76,800행/598hit와4개 인계 gate 및 P5 aa2ae0aaaec448e0bd8711f677011024를 통과했다. 실제 재기동 대상deb도 새 P5 3d23491b07914810a65be77d987c2b83의12로더/금지0/findings0/child 종료를 확인했다. 두 P5는 검증이며 실제 PID 소비와 구분한다.6746ac681은 Main에 배포하지 않았고 다음 전환은 새 selector/PID 기준으로 다시 인계해야 한다.

첫 graceful restart는 이전 PID 종료 후 supervisor 재기동이 이어지지 않아exit3이었다. 공식 start의 기동 전 bootstrap도 holding_path_vote_policy_receipt_mismatch/stale_env·main_stop_confirmation_invalid로 거부됐다. 원 stdout·실패·20:00 terminal을 보존했다. 실제 원인은 이미 소비한 같은 release의 보유/손절 code-contract reader가 종료된 이전 PID의 live custody를 다시 요구한 것이다. 격리 P5의 검증 문맥과 일반 supervisor의 실제 기동 문맥을 같은 성공으로 취급하지 않는다.

기존 prepared_policy_code_handoff.issue를 release-set·detector·selector lock 아래 사용했다. Main/supervisor 부재, 원 prepared894·당일 정책·Git source closure·원 policy/PREOPEN/env SHA를 검증하고 holding_vote/main_stop의 정확한 코드 호환 영수증만 발행했다. 원 정책·threshold·PREOPEN·env·이전 시도는 수정하지 않았다. 원 family reader와 정식 issuer는 현재 소비자로 retained이며 새 module/CLI/우회 flag는 없다. 두 native verify 및 일반 bootstrap PASS 후 공식 start에서 PID2502290/start5347863/cwd deb/src를 생성했고20:23:21 native PID 소비를 확인했다. 새 code-compatibility receipt는 actual_pid_consumed=false이며 실제 소비 근거는 별도 launcher/선택/consumption 영수증이다.

20:29:06 현재 선택본 reader의 원천1,769,050,629B/raw273,087행 native generation 검증이 PASS다. 마지막 index gap은19:46:05이며, 보존 cache29,360,128B/SHA4365f089b35b816394298a814171486c500ce85d02eaad3235274e669a3ff956의 quick_check=ok/원3,569행도 확인했다. 새 PID의 startup source producer/observer는각exit0이고, 현재 health와 observer 원문 SHA가 일치한다. actor2502290/5347863 및 current generation을 검증했다. 관측기는 bounded_no_applicable_observations/unmet0이며 전체 매매 표본 coverage·실주문·경제성을 입증하지 않는다.

사용자 후속 지시에 따라 미해결 보유와 그 파생 process/log 경보는 이번 판정에서 제외한다. 원 로그·detector 판정은 보존한다.20:26:37 artifact 검증은 digest lock의 bounded 대기로 deferred였고20:27:57 자연 full 검사에서 다시 실행됐다. 로그 스캐너·resource PASS, 해당 보유 로그 외 신규 ERROR0이다. 남은 warning은 원16일 entry_cancel_wait 연구 generation/code 결속과 EOD·장후 산출물 대기이며, trailing 연구 현재성·다음 정책·자연 AVG_DOWN 수용도 기존 owner에 유지한다. EOD는20:26에1,050/2,625를 진행했으며 terminal이나 장후 완료로 승격하지 않는다. 최신 근거는 tmp/avg-down-sor-deploy-20261019/restart-2009/restart-final-readback.json이다.

최종 범위(기준34798c60c, 다른 workspace 변경 제외): non-test source 15파일 +634/-54(순증580), tests 15파일 +891/-42(순증849), docs 4파일 +296/-0이다. 파일 이동·새 source/test module·CLI·schedule은 없으며 source 순증은 필수 입력·세 시장 route·실제 native 계보/격리 소비·색인 복구에 사용했다. 변경 Python30개 compile, 원본/현재36개 인계 회귀, source29개 및 두 clean candidate의 P5/native gate를 검증했다. 문서 링크·owner·권한·print-only parser와 diff 검사를 최종 확인한다. 현재 수리 범위의 미해결 코드 지적은0이며, 남은 연구·일정·자연 표본은 각 기존 OPEN owner의 별도 수용이다.
