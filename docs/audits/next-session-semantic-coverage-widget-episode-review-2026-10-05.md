# 의미감시·Widget/Episode 보완 실행 리뷰

작성일:2026-10-05 KST. 소유 계획은 [통합 상세계획§6](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md), 실행 소유자는 [현재 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)다. 사용자 계획 실행/코드리뷰·수정보완 지시에 따라 구현과 기존 원천의 유한 연구를 실행했다.

## 1. 수용 범위와 결과

**검토 범위의 코드 결함은 보완·재리뷰·표적 검증으로 닫았다.** 실제 배포, 설치된 독립 consumer pin, 장후 최종 세대,10/6 PID 소비와 새 날짜 경제성은 이 코드 수용 결과와 별개다. 현재 prepared 재검증은 FAIL이며 과거 PASS를 현재 정상 기동 보장으로 사용하지 않는다.

S1–S8의 native 지정/fixed-pair 분기, receipt 소유 완료 날짜와 다음 due target, Widget/Episode projection, Episode61 profile 상태표, 알림 generation 소비를 구현했다. 원 v2 소비자 계약 동일 bytes를 durable runtime 경로에 복사하고 기존 machine final-refresh 성공 후 optional Samsung sidecar를 연결했다. 새로운 엔진 root 모듈·cron·거래 허가 stage를 만들지 않았다.

Widget 새 selector에서180초 수익 종료 건수 비감소 veto를 제거하고 count를 진단으로 옮겼다. immutable 이전 정책은 legacy validation으로 읽을 수 있지만 새 후보 생성은 새 계약만 사용한다. EV/net/tail/capital/source/support/custody의 기존 역할을 유지했다. confirmation 외 진입 quote 지연은 연구 helper에만 노출하며 실제 selector의 새 tuning axis로 발행하지 않는다.

Episode persisted state에는 기존 durable raw의 profile/date/PID/cwd/policy/sequence meta만 복사했다. 수집 API·실행/수량/add/exit·격리 조건을 바꾸지 않았다.120초 freshness는 감시 신선도이며 inventory 청산이나 기동 권한을 제한하는 새 guard가 아니다.

## 2. 반복 리뷰에서 수정한 사항

| 발견·위험 | 보완과 회귀 |
|---|---|
| 정상 operator designation을 일반 carry와 비교한 오탐, fixed-pair를 일반 신규 후보로 검사 | proof별 native binding·B0/C0/P_t/activation 검증. 정상/parent/request/source 변조 및 기존 general 경로 |
| holiday source 추측과 controller의 실제 `date`/schema 필드 불일치 | receipt-owned 완료 세대 선택. 최신 corrupt index를 과거 PASS로 대체하지 않음. 휴일/자정/07:35 경계 |
| projection이 경쟁 publisher의 다른 report/policy bytes에 결속될 위험 | on-disk 객체/SHA 확인→봉인→재확인. source/kernel/duplicate count 변조와 생성 중 읽기 |
| failed worker가 lock 해제 후 성공 terminal을 덮을 위험 | 실패 terminal도 date lock 안에서 작성. busy worker는 index 보존, 기다림/동일 입력 재사용/변조 회귀 |
| unit 설정 또는 과거 capture를 실제 현재 PID 소비로 판단할 위험 | 실제 `/proc` cwd와 source PID/date/policy/sequence·신선도 결속. 과거 실패/future_due·quarantine·preflight/terminal 분리 |
| 이전 날짜 incident가 필터에서 탈락하거나 새 generation이 중복으로 억제됨 | exact source/target/owner/scope/reason/generation fingerprint. 새 세대 incident·이전 미회복 이력·정상 회복·unobservable mock |
| 자동 family 재생 중 바뀌는 terminal을 원천 변조로 해석 | pending/running은 unobservable, 회복하지 않음. 완료 이후 native 재검증 유지 |
| 단일 날짜에 빈 holdout을 만들거나 일부 저장 bar만으로 전체 무신호 결론 | 단일 날짜 calibration만 계산. native 유효 lookback feature별 전체 진입 clock coverage. 부분 창 경제 비교 차단/원 prefix 진단 보존 |
| sealed Samsung 결과의 candidate/authority와 generation 경로가 index와 다를 위험 | result schema/candidate/native authority, owner/order flag, identity digest/경로/상태 결속. 허용 플래그 변조 반례 |
| 자동 native publisher가 이전 연구 보고서를 덮어써 입력 SHA만 남는 위험 | 사용한 보고서 동일 bytes를 별도 source_reports에 보존·봉인. 원 live 파일 변경 후 보존 사본 SHA 회귀 |

Python producer/consumer의 실패·결손·세대·날짜·권한 경로와 wrapper의 native 실패 전파/optional 연구 실패를 함께 검토했다. 아직 생성되지 않은 자연 원천과 물리 설치 문제를 코드가 해결한 것으로 표시하지 않았다.

## 3. 실제 보유 원천 계산

[최종6가설 계산](../../tmp/next-session-semantic-widget-episode-implementation-20261005/existing-source-research-v3/result.json), [분모 요약](../../tmp/next-session-semantic-widget-episode-implementation-20261005/research-summary.json)을 보존한다. 기존 report·raw·kernel SHA와 사용한 보고서의 원 bytes를 보존했으며 provider/API/실주문/정책 publisher를 호출하지 않았다. 초기 계산의 partial-window 해석 위험을 수정하고20:43 자연 report 세대 변경 후 같은 고정 정의를 재계산했다. 이전 결과는 역사 증거로 보존했다.

- Widget 삼성 KRX_REGULAR은 exact initial/leg fill·last-trade·틱 절삭 add·guard·평균 체결·target terminal 결속 부재로 `scale_in_runtime_trigger_source_missing`이다. 정확 add replay를 구현한 것으로 표시하지 않는다.
- Widget 삼성 NXT_PREMARKET은 독립4기회. 학습3 중 comparable2·검열1, 마지막 역사 비교1은 검열이다. 확인2↔3/1quote 지연은 대조와 같다. ENTRY_READY 필터는 관측 손실1을 제외하지만 완결 진입0·승률null·역사 비교 unresolved여서 운영 후보가 아니다. 대조 comparable base CF -16,003원/기회 EV -0.30657088%는 실제 브로커 손익이 아니다.
- Episode61개는 비삼성. 저장 분봉이 있는58개에서3정의를 계산했다. **전체 진입 창29개는 세 정의 모두 완결/held outcome0, 부분 창29개는 `source_window_incomplete`,3개는 bar 없음**이다. 미관측을 승률0 또는 무수익 정책 증거로 쓰지 않는다.
- Episode9/29 raw1,204 모두 lineage-invalid,9/30 valid-empty,10/2 raw1,178 중1,072valid/106conflict다. native 원천 검증을 통과한 body만 계산에 전달했으며106개 과거 conflict를 정상으로 바꾸지 않았다.

## 4. 검증과 감시 비용

[검증 기록](../../tmp/next-session-semantic-widget-episode-implementation-20261005/validation.json)에 정확 명령·exit·파일 SHA·검토 결과를 남긴다.

- 주요8 suite **648 PASS**: native 지정, ArtifactFreshness, notifier, Widget selector/publisher/legacy loader, Episode runtime 및 native 가격 replay, 새 coverage/lock/wrapper 계약.
- 마지막 Samsung authority/candidate/generation 보완 후 감시3 suite **189 PASS**, 보고서 원 bytes 보존 보완 후 영향5 suite **349 PASS**. 최종 count와 정확 명령은 위 검증 기록을 따른다.
- 변경 Python compile, wrapper `bash -n`, wrapper의 native exit/sidecar 선택 실행 계약, `git diff --check`, document link/owner/print-only parser 검증.
- Kiwoom 요청/응답/FID/auth/REG/REMOVE/continuation을 변경하지 않아 공식 API gate의 신규 protocol 조회 대상이 아니다. 거래 기동, 토큰/API 조회, Telegram 실제 송신, 외부 문서 sync는 실행하지 않았다.

고정 machine 입력의 [이전](../../tmp/next-session-semantic-widget-episode-implementation-20261005/baseline.json)/[확장 후](../../tmp/next-session-semantic-widget-episode-implementation-20261005/after.json) lookup은 wall1.591→2.961초, RSS250,344→251,872KiB였다. native designation 재검증과 추가 coverage로 비용이 증가했으며 속도 개선을 주장하지 않는다. 추가 wall 약1.37초는5분 주기의 약0.46%, 전체 약0.99%다. 큰 report/grid를 감시마다 재생하지 않았고 family projection은709KB/119KB다. 자동 handoff 세대가 동시에 바뀌었으므로 전체 체인이 동일 상태였다는 성능 parity를 주장하지 않는다. 현재 코드 검증에서 이 bounded 비용 때문에 native 검증을 줄이지 않았다.

## 5. 현재 준비와 실제 소비 잔여

[selected cwd native 준비 검증·12보호 SHA](../../tmp/next-session-semantic-widget-episode-implementation-20261005/current-readiness-and-protection.json)의20:38 KST 결과는 generation/full **FAIL**이다.20:10에 원래 예약된 Widget source10/2와 Main/controller source10/5가 진행 중이다. 변경된 running terminal로 `strict_stage_generation_stale:widget_policy`/`strict_generation_changed_during_recheck`가 발생했고 full 검사는 tower/checklist/collector 세대 불일치도 표시했다. 새로운 projection 때문에 정책이 바뀌었다고 해석하지 않는다.

12개 보호 SHA는 모두 이전과 같았다. selected3d0e5106, Widget/Episode의 독립e6d4d3b9 pin, 현재/10/6 정책, 원 frozen/v2, 준비 index/receipt/10/6checklist를 보존했다. 실제 코드 배포·정책 생성·재기동과 future PID를 수용했다는 뜻은 아니다. 진행 중 wrapper 코드/입력을 바꾸거나 lock을 삭제하지 않았다.

[최종 의미 조회](../../tmp/next-session-semantic-widget-episode-implementation-20261005/final-semantics.json)는 정상 designation과 삼성 waiting을 확인하고, Main 운영 결손3finding 및 Episode 원천 결손은 유지한다. family 생성 중에는 handoff/Widget을 관측 불가로 표시한다. 현재 Widget dated loader의 [직접 검증](../../tmp/next-session-semantic-widget-episode-implementation-20261005/widget-native-loader.json)은 PASS이며 삼성2세션 eligible/타종목2세션 blocked다. 당일 실제 PID 소비 증거는 아니다.

Widget20:43 succeeded 후에는 이전 projection의 report 세대 mismatch가 나타났다. completed stage SHA/native loader PASS를 확인해 **projection만** [현재 세대에 재결속](../../tmp/next-session-semantic-widget-episode-implementation-20261005/widget-completed-projection-rebinding.json)했다. 이후 Widget warning은 실제 scale-in source 결손만 남았다. [20:53 native 준비](../../tmp/next-session-semantic-widget-episode-implementation-20261005/post-widget-generation-readiness.json)는 여전히FAIL이고 Main/controller10/5는 진행 중이다. 정책/12보호 SHA는 동일하며 전체 준비 완료는 미수용이다.

잔여 owner/종료 검사는 다음과 같다.

1. `DirectFamilyPreopenPolicyHandoff`/`WidgetEpisodeNextSessionStartup1006`: 자동 작업 종료 후 실제 완료 source→target10/6을 확인하고 최종 세대를 동결하여 summary/intake→strict→controller→prepared.07:32 apply/restore·07:35 activation·실제 PID와 정책/hash를 별도 검증한다.
2. `SemanticPolicyCoverageRemediation1006`/`SamsungFrozenCandidateValidation1006`: 검토된 감시/producer/wrapper release와 독립 pin 설치·자연 주기/알림·삼성 이후 날짜 sidecar. 현재 source10/6의3경로 부재는 waiting이며 과거 입력으로 독립 검증을 만들지 않는다.
3. `WidgetEpisodeMachineResearchContract1006`: 기존 Widget runtime leg/guard ledger와 Episode29부분창·3bar없음의 저장 완료 분봉을 정확 identity/clock/SHA로 연결 가능한지 확인. 새 수집 없이 같은6정의를 종료/인계하고 실제 새 날짜 결과에서 고정 비교한다. 개선 후보가 없었던 사실과 원천 부족을 구별한다.

**미수용:** 운영/stop/plan 원천 결손 해소, source가 없는 exact scale-in replay, 새 날짜 성능, 격리3개 해제, 모든 Episode 정상 기동, 실제 비용 후 순수익. 이 항목들을 코드 결함0/테스트 PASS에 포함하지 않는다.


## 야간 후속 준비의 추가 리뷰

사용자 요청으로 통합 배포·다음날 준비를 진행했다. 추가 원인은 휴장일 EOD `skipped_non_trading_day`를 Main/controller가 완료 대기로 소비하는 결함이었다. 공유 canonical calendar gate를 매매 자원 격리/producer/controller 이전에 배치하고 Widget/final-refresh의 휴장일 과거 원천 자동 재발행도 차단했다. 유효 원 날짜 explicit recovery, native source guard 및 실패 exit는 유지했다. 이 변경은 Kiwoom 요청/응답 parser 변경이 아니다.

휴장일/비canonical 날짜·native controller producer 미호출·4wrapper SKIP와 기존 wrapper 회귀75건 PASS. review에서 snapshot 불변성·calendar import 경로·오류 fail closed·bot stop 이전 순서·분석 worker exact identity/종료를 확인했다. 기존 원천 재결속은 KRX와SOR 경계 및 scale-in 미기록을 구별하여 결손을 유지했다. native10/6 Episode apply **계획만**61profile 검증PASS(58carry/3격리); 당일 applied/authority로 대신하지 않는다.

설정·준비의 최종 결과는 [야간 실행 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/next-session-final-preparation.json)를 따른다.10/6 실제 PID 소비는 사용자 명시에 따라 오늘 검증 대상에서 제외하며 당일 OPEN을 유지한다.


최종 native 재생에서 표시용 sentinel archive의 물리 경로 결함을 추가로 발견했다. gzip decoded logical SHA/bytes로 정합을 확인하고 nonempty conflict/corrupt/missing 반례 및 empty display-only shadow의 명시 제외를 검증했다. payload/replay·policy/date/custody 검사를 해제하지 않았으며 collector known source 부재를 valid-empty로 바꾸지 않는다. 수정 후 영향 회귀와 원9/30 SHA 대사를 통과한 release에서 다시 봉인한다.
