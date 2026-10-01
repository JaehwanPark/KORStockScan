# 현재 릴리스 장후작업 연계 의미적 감시기 보완계획

기준일: 2026-10-01 KST. 계획 당시 기준과 구현·배포의 실행 영수증은 별도다. 사용자 후속 승인으로 P0~P3 구현·리뷰·배포를 수행하며 [구현·배포 기록](../audits/semantic-monitor-postclose-integration-implementation-2026-10-01.md)에 실제 결과를 남긴다.

## 1. 목표와 현재 기준

장후 작업의 실행 완료, 원천 적격성, 후보 검증, 정책 발행, 다음 기동 소비를 기존 의미감시 결과에서 각각 확인한다. 원천·계산 실패가 성공 terminal 뒤에 숨는 누락과 정당한 정책 유지가 장애로 표시되는 오탐을 함께 줄인다. 감시기는 기존 producer의 계약을 검사하며 후보를 다시 탐색하거나 정책을 선택하지 않는다.

- 현재 selector는 `integrated-postclose-startup-20261001-0a8fa0a0`, 전체 commit `0a8fa0a0522c09261570bf961d737b328894a5b9`를 선택한다. 실제 릴리스 HEAD와 `src/`·`deploy/`·`restart.sh` clean 상태를 대조했다. 작업본 HEAD는 후속 문서 commit `818567e2`이며 두 감시 소스는 릴리스와 바이트가 같다.
- `artifact_freshness.py` SHA256: `7061d0681441282da5f7c5de5d9bcee1f0abd2fd2fb649940adc93021ba74bb1`. `submission_bottleneck_monitor.py`: `ca85a2bb607d6299e2c9f707b26ad61f58a27a8ad04310438638e6a9cd770e56`.
- [통합 배포 기록](../audits/integrated-release-next-startup-handoff-2026-10-01.md)과 [장후 구현·리뷰](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md)가 개선 코드의 근거다. 새 기계 회복 순위 `missed_entry_recovery_priority_v7`과 보조 `train_top1_frozen_paired_net_ev_holdout_gate_v4`는 **10/2 원천의 장후 계산부터** 적용된다. 10/2 장중 정책 선택과 실제 PID 소비는 별도다.
- 9/30용 10/1 05:00 detector는 보조 라벨 결손 6건, 주 경제성 비교 가능 0/6, `writer_plan_hash_missing`을 이미 기록했다. 이 과거 결손은 수리 전 이력이다. 새 10/2 계약 수용이나 실패 건수로 합산하지 않는다.
- 가장 최근 10/1 21:50 full detector는 기계·보조 의미 결과가 `not_assessed`이며 보고서 전체는 `fail`이다. 이 실행은 22:17 새 selector 선택보다 앞선다. 새로운 릴리스의 감시 자연 소비를 증명하지 않는다. Main OFF와 과거 원천을 사용하는 10/2 준비가 [기동 인계](../audits/integrated-release-next-startup-handoff-2026-10-01.md)에 명시돼 있다.

## 2. 확인된 보완 지점

| 접점 | 현재 코드 근거 | 보완할 내용 |
| --- | --- | --- |
| 보조 검증 구간 | `compact_auxiliary_paired_replay.evaluate_auxiliary_stage`는 `same_day_holdout_keys`·시간순 `split_manifest`를 생성한다. `_auxiliary_result_semantics`는 선택 검증과 전체 holdout 존재 검사에서 `holdout_day`만 요구한다. | 적법한 같은 날 시간순 검증을 결손으로 오인하지 않는다. 키가 있다는 사실만으로 독립성 통과 처리하지 않고 purge·시각 경계를 확인한다. |
| 보조 v4 선정 증거 | 현재 감시기는 5/3 지원·2/1 변경·쌍 EV·응답 결손 등을 검사하지만 `selection_rank_version`, `frozen_train_choice`, `auxiliary_train_selection`, full-cost와 학습 hash의 결속을 명시적으로 대사하지 않는다. | 학습 1위 동결→그 후보 한 개 검증→발행의 동일 policy/prompt/부모/hash를 확인한다. 2위 재선택과 마찰비용의 full-cost 대체를 찾는다. |
| 기계 두 생산 경로 | `postclose_summary_handoff.stage_commands`에서 `main_machine_policy`는 `--winrate-policy-only`, `legacy_machine_report`는 `--machine-only`를 호출한다. v7은 후자의 full evaluation에 포함된다. | win-rate sidecar와 v7 회복 평가를 각 실제 소유 단계에서 검사한다. 승률 선택·비용 쌍 비교·실현 순익을 하나의 합격으로 묶지 않는다. |
| 기계 실행 세대 | `_machine_result_semantics`는 full report의 내부 hash/날짜와 sidecar를 검사하나 보조처럼 해당 stage terminal의 원출력 hash를 직접 대사하지 않는다. | 기존 stage 검사와 결속해 성공 terminal 뒤 보고서 변경·부재를 탐지하고, 구세대 성공을 현재 성공으로 재사용하지 않는다. |
| 비용·원천 해석 | 현재 보조 감시는 owner 주 비교 0건과 라벨 source gap을 전체 findings로 표시한다. v4 독립 full-cost checkpoint와 owner 운영 비교 v8의 요건은 다르다. | 두 평가 계약의 적격/제외/결손을 별도 표시한다. owner stop/seed 결손이 유효한 독립 CF 정책까지 일괄 무효화하지 않으며, 독립 CF가 owner 경제성을 복구했다고도 표시하지 않는다. |
| Telegram 도달 | `_is_alert_result`는 `fail`과 인증 detector의 `warning`만 알린다. 장후 의미 findings는 `artifact_freshness`의 warning에 머무를 수 있다. | 명시적인 조치 대상 의미 findings만 warning 알림에 포함한다. 정상 carry·표본 대기·OFF/퇴역 부재는 일반 장애로 발송하지 않는다. |
| 실행 코드 선택 | BUY Funnel cron은 release router를 쓰지만 설치된 full error detector cron은 기본 작업공간 `run_error_detection.sh`를 직접 실행한다. 현재 소스 일치는 확인했으나 향후 변경 시 서로 달라질 수 있다. | 보고서에 실제 감시 실행 root/commit/소스 hash와 selector를 기록하고, 정규 detector의 선택 릴리스 소비 경로를 보완한다. cron 시각과 기존 환경·로그 소유자는 유지한다. |

## 3. 기존 소유자와 연결 구조

새 daemon, 장후 evaluator, 병렬 보고서 생산자는 만들지 않는다. `src/engine/error_detectors/artifact_freshness.py`가 장후 의미 검사의 주 소유자다. `submission_bottleneck_monitor.py`는 장중 source→machine→compact→pending 결속을 맡고 장후 전체 원천을 반복 읽지 않는다.

| 단계 | 재사용할 정확일자 근거 | 감시·인계 소유자 |
| --- | --- | --- |
| 원천 생성/감사 | 같은 attempt의 route·관측시각·plan/trace hash, preflight/final 원천 감사, 제외 행·완료봉 cache 영수증 | 장중 source semantics / 기존 감사 producer |
| 후행 라벨 | `ai_decision_outcome_labels`의 해시·당일 compact 모집단·가격/비용/경계별 상태 | `outcome_labels` stage / artifact freshness |
| 기계 선정 | winrate report/terminal과 full report의 v7 selection·train checkpoint·scope evidence | `main_machine_policy` 및 `legacy_machine_report` |
| 보조 선정 | compact report의 v4 scope·동결 선택·split·full-cost·prompt 응답 | `main_auxiliary_policy` |
| Widget/Episode | 각각의 stage terminal, publication/refresh receipt, 정확 policy/source hash 및 native 격리 사유 | `widget_policy` / `episode_policy`; 기존 stage 검사 재사용 |
| 최종 인계 | runtime summary→현재 checklist→strict verifier `--require-summary-handoff`→controller done→finalization generation | `postclose_summary_handoff`, `cron_completion`, 기존 generation 검사 |
| 다음 기동 | prepared readiness→실제 PREOPEN succeeded→Main/Widget/Episode 소비 영수증 | `next_preopen_readiness` 및 기존 startup/process 검사 |

원천일 `source_date`, 검사시각 `as_of`, 실제 적용일 `target_date`, 선정 코드 버전을 별도 기록한다. 자정 이후 원천일은 장후 wrapper의 명시값을 유지하고 적용일은 기존 KRX calendar resolver를 사용한다. 10/2 이후 날짜를 문자열 덧셈으로 만들지 않는다.

## 4. 수정 순서와 완료 기준

### P0 — 버전·분모·carry 해석 정합화

1. 감시기의 버전 분기는 producer가 기록한 버전을 먼저 검사하고 원천 날짜의 적용 경계와 대사한다. v3/v4 및 기계 기존 버전/v7을 별도 읽는다. 과거 날짜를 새 계약으로 소급 검사하지 않는다. 10/2의 필수 버전이 없거나 모순되면 원인으로 남긴다.
2. 기존 상태를 유지하면서 `execution`, `source`, `selection`, `publication`, `consumption`의 검사 결과를 details에 명시한다. 정당한 `incumbent_carry`, 유효 빈 모집단, 표본/관측 대기, 계산 실패, `source_gap`, `source_invalid`, 기한 후 필수 영수증 부재를 구별한다. exit 0와 `succeeded`는 실행 결과이고 정책 적격성의 대체 근거가 아니다.
3. 당일 owner 비교 6건, 누적 독립 진단 44건, full-cost 후보·train/holdout·purge 분모를 각각 검사한다. 전체 진단 eligible과 실제 candidate population을 같다고 가정하지 않는다. 부분 결손은 해당 행/계약만 제외하며 전역 감사 무효·격리 실패만 전체 차단으로 표시한다.
4. 라벨 해시·행별 상태 검사는 유지하되 compact와 무관한 holding/exit 라벨까지 compact 장애 분모로 합치지 않는다. 정확 모집단 join이 불가능하면 커버리지 검증 결손으로 남긴다. 현재 신선도와 후행 기간의 censor를 같은 `stale`로 바꾸지 않는다.

완료 기준: 정상 다일/같은 날 carry·후보 선정이 오탐 없이 분류되고, 깨진 분모·hash·버전이 통과하지 않는다. valid-empty에는 해당 단계의 자연 모집단 census가 필요하다. 예정시각 전 부재는 실패가 아니며, 의도적 Main OFF/전일 source 준비도 명시된 운영 영수증으로 확인한다.

### P1 — 새 기계·보조 선정 증거와 terminal 결속

1. 보조 v4의 `frozen_train_choice`와 `auxiliary_train_selection.scopes`·선택 policy/prompt·부모 기계 hash·train population hash·`split_manifest`를 대사한다. 같은 날 분할은 `postclose_entry_validation.split_manifest_valid` 등 기존 순수 검증을 재사용해 기회 중복·겹침·purge와 `train_observation_end < holdout_start`를 확인한다. 기존 v3의 허용 계약은 유지한다.
2. 선택 후보가 정확 동결 1위인지 확인한다. `holdout_errors`, full-cost 후보 수·cost 불완전 진단 수, `metric_authority`, 정확 응답 완료 수, 관측된 변경 방향 지원을 읽는다. 전체 trial 수를 완료 후보 수로 세지 않는다. VETO 0건은 PASS-only 연구의 결함이 아니며 관측하지 않은 VETO→PASS 개선을 증명하지 않는다.
3. owner v8과 독립 full-cost checkpoint를 계약별 검사한다. stop 경로·owner seed·포트폴리오·추론비용은 해당 owner 계약의 요건이며 독립 단계에 일괄 추가하지 않는다. CAUTION은 checkpoint 미진입 CF로 표시하고 후속 owner 경로 없이는 영구 손실 회피/실제 PnL로 귀속하지 않는다.
4. 기계 v7은 full evaluation 안의 scope selection·학습 hash·split·회복 고유 기회·기존 성공 보존·검증 회복과 producer의 promotion errors를 읽는다. `no_recovery_qualified_candidate`는 계산을 마친 정상 carry일 수 있다. `strategy_population_empty`, 필수 raw/비용/부모 결손과 계산 중단은 별도 원인이다. 기존 `entry_strategy_policy.promotion_errors`와 report evidence를 재사용하며 감시기가 새로운 rank/EV 하한을 만들지 않는다.
5. 기존 `stage_receipt_issues`/출력 검사를 재사용해 machine full report, winrate sidecar, auxiliary report와 해당 stage terminal의 날짜·원파일 hash·현재 generation을 연결한다. 검사가 성공해도 실제 정책 발행이나 소비는 뒤 단계 영수증으로만 인정한다. 새 원본 생성 도중 파일이 바뀌면 읽기를 제한적으로 재검증하거나 `unobservable`로 끝내며 서로 다른 세대를 섞지 않는다.

완료 기준: same-day 유효 후보·정당한 carry, train 1위 검증 실패/2위 성공, full-cost 결손 행 격리, 동결 선택 변조·parent/source 변경, 성공 terminal 뒤 보고서 교체를 각각 올바르게 판정한다. 새로운 보고서 재생성이나 provider 호출 없이 봉인된 입력 fixture로 재현한다.

### P2 — 정책·최종 인계·준비·소비를 연결

1. 정책 발행 상태와 부모 CAS·bundle/정책 hash·적용일을 대사한다. M1 선발행 후 M0/A1 보류, M1/A0 보존, 정당한 incumbent generation ancestry를 기존 발행기 계약대로 인정한다. 단순히 최신 bundle hash가 과거 terminal hash와 다르다는 이유만으로 변조로 단정하지 않는다.
2. Widget/Episode에는 별도 경제 evaluator를 추가하지 않고 기존 publication/refresh·격리 근거를 재사용한다. 격리 profile은 그 이유·소비 경계를 표시하며 누락 표본으로 복원하지 않는다. 코드 릴리스 일치와 owner별 policy pin 일치를 따로 확인한다.
3. summary·strict·controller·finalization은 동일 원천 generation의 영수증을 읽는다. verifier/controller 자체 hash를 summary 입력에 넣어 순환을 만들지 않는다. finalizer 내부 detector의 자기 terminal 대기는 기존 bounded-wait 계약을 유지한다.
4. prepared 검증은 `next_preopen_readiness.verify_prepared`의 읽기 전용 경로와 결과를 재사용한다. detector가 직접 `prepare`/active env/정책을 쓰지 않는다. 준비 PASS, 실제 PREOPEN, PID 소비를 각각 표시하고 미래 기동을 미리 정상으로 처리하지 않는다.
5. 감시 코드 배포로 selector/commit이 바뀌면 준비 영수증은 새 릴리스 기준 재생성·검증이 필요한 대상이다. 기존 readiness.json의 hash를 고쳐 일치시키지 않는다. 활성 프로세스의 동작 변경 여부와 재기동 필요는 당시의 별도 배포 범위에서 확인한다.

완료 기준: 준비 이후 selector 변경·stale readiness·실패 PREOPEN·PID 미소비를 놓치지 않고, 정책 유지/새 후보 없음만으로 startup 장애를 만들지 않는다. 실제 주문·체결·비용 후 성과는 native terminal 자료가 있을 때만 표시한다.

### P3 — 알림과 감시 실행 경로

1. `notify_error_detection_admin.py`는 `artifact_freshness`의 **명시된 조치 대상 의미 finding**만 warning 알림에 포함한다. 전체 warning을 일괄 발송하지 않는다. 비용/원천 결속 결손, 후보 증거 충돌, 기한 후 필수 handoff·소비 결손을 대상으로 하고 정상 carry·표본 대기·희소 체결·OFF/퇴역 부재는 보고서에만 남긴다. 변조/무효와 경제적 후보 탈락은 서로 다른 심각도로 유지한다.
2. 알림에는 원천일, 검사시각, stage/family/scope, 현재 원인, affected/eligible/전체 분모, artifact·generation/hash, 기존 수리 owner·closure test를 넣는다. 과거 결손과 신규 원천 재발을 별도 표시한다. 큰 원천 JSON이나 전체 후보 목록을 Telegram에 붙이지 않는다.
3. 기존 notification state를 확장하되 incident 키는 source date+owner/stage+scope+원인으로 안정화한다. 재생성 hash 자체는 매번 새 경보가 되는 키로 사용하지 않고 증거로 저장한다. 같은 미해결 원인은 억제하며 같은 scope의 새 검증 영수증이 있을 때만 recovery로 표시한다. `not_assessed`/부분 tail/파일 부재를 recovery로 바꾸지 않는다. 현재 경보 종료와 과거 데이터 복구도 별도다.
4. full detector의 실제 root/commit/source hash와 selector 차이를 기록한다. 필요한 router target·installer/wrapper 수정은 기존 환경·시각·로그·lock을 보존하는 최소 변경으로 설계하고 cron 관련 문서의 승인된 변경 범위와 함께 리뷰한다. 보고서 자신의 provenance는 기록 전용이다. 현재 소스가 같다는 이유로 과거 21:50 실행에 새 릴리스 소비를 소급 표기하지 않는다.

완료 기준: 의미 warning 1건의 mock 발송, 재발/중복 억제, 정상 carry 무발송, 관측 불능의 잘못된 recovery 방지, 실제 실행 root와 selector 불일치 검출을 통과한다. 계획/검증 단계에서 실제 Telegram 발송은 하지 않는다.

## 5. 검증·성능·종결

수정→자체 리뷰→보완→재리뷰→표적 검증 순서로 닫는다. 코드 변경은 위 기존 소유자와 현재 tests 파일에 한정하고 신규 source producer/CLI/module을 먼저 만들지 않는다.

| 검증군 | 핵심 반례 | 수용 기준 |
| --- | --- | --- |
| 상태/버전 | v3 과거, v4 당일, 미래 미도래, 정상 empty/carry, 원천 실패, 부분 격리 | 해당 계약과 시각에 맞는 결과; 과거 계약에 새 문턱 적용 0건 |
| 독립 검증 | 같은 날 split/purge, 겹침/중복, 학습 1위 실패, 응답 fallback, PASS-only/VETO 회복 | 허용 same-day 오탐 0건; 무증거 후보 통과 0건 |
| 비용/분모 | 마찰 vs full-cost, 0/null, 당일/누적, owner/독립 CF, actual/partial/CF | 비용 결손 임의 복원 0건; 각각 모수 보존 |
| generation/소비 | 변경된 보고서, CAS/부모 ancestry, stale strict/controller/readiness, release 불일치 | 구세대 PASS/준비/PID의 잘못된 재사용 0건 |
| 알림 | 조치 warning, carry, 반복/재발, partial/unobservable, 기존 상태 migration | 필요한 mock 경보 도달; 기존 결손의 잘못된 recovery 0건 |

- 관련 시험: `src/tests/test_error_detector_artifact_freshness.py`, `test_notify_error_detection_admin.py`, `test_error_detector.py`, `test_postclose_summary_handoff.py`, `test_postclose_entry_validation.py`, `test_submission_bottleneck_monitor.py`의 영향 사례만 먼저 실행한다. wrapper/router 변경 시 기존 계약 suite와 `bash -n`도 수행한다. 문서 단계는 링크·owner·print-only parser와 `git diff --check`로 닫는다.
- 성능: detector의 기존 단일 파일/압축 해제 64 MiB 제한을 유지한다. 새 검증은 기존 bounded report/compact receipt만 읽고 다일 raw·후보 재생·provider/broker 호출은 0이다. 동일 봉인 보고서 세트의 구/신 3회 비교에서 wall/CPU 중앙값 ≤기존×1.20, RSS ≤기존×1.10+64 MiB와 기존 절대 guard를 확인한다. 변경 없는 보고서의 검증 캐시는 date/schema/소스 hash/검증 코드 hash가 모두 일치할 때만 재사용한다.
  - 구현 리뷰 보완: 주기 감시가 native whole-chain verifier를 반복 계산하던 초안은 성능 한도를 초과해 폐기했다. native `generation_only` 읽기 전용 옵션으로 봉인된 PASS의 현재 세대만 대사하고 검증 범위를 결과에 명시한다. 준비 생성·정식 verify·PREOPEN·finalization 기본 전체 재검증은 유지하며 CLI에는 경량 옵션을 노출하지 않는다. Widget/Episode 출력은 JSON 전체 재파싱 대신 bounded streaming SHA로 대사한다. 캐시·새 daemon·새 보고서 producer는 추가하지 않았다.
- 코드 완료는 mock 계약 통과까지다. 10/2 자연 수용에서는 먼저 실제 감시 실행 코드와 장후 생산 릴리스를 확인하고, 각 stage 종료 뒤 현재 generation의 의미 결과와 필요한 알림 영수증을 대사한다. 최종 strict/controller/finalization은 각 기존 실행 owner가 닫는다. 미발생 후보/주문은 `not_observed`, 필수 원천/실행 결손은 해당 owner의 `blocked`로 기록하고 표본을 기다리며 같은 입력 재생을 반복하지 않는다.
- 실행 owner: 신규 감시 코드/회귀는 다음 체크리스트의 `PostcloseSemanticMonitorContractRepair1002` 하나가 맡는다. 자연 기계·보조 stage는 기존 `MainMachineMissedEntryPriority1002`·`CompactAuxiliaryPassVetoPostclose1002`, 기동은 `FinalPolicyStartupAcceptance1002`를 재사용한다. 생략/실패에는 artifact·첫 실패 단계·기존 owner·다음 조치·closure test를 남긴다.

## 6. 참조와 이번 작업의 종결

- [기존 원천 감시 계획](machine-auxiliary-source-gap-prevention-plan-2026-09-29.md) §6–§7의 장중/장후 결속을 유지하며 이 문서가 새 장후 버전 연계 보완을 소유한다.
- [기계 개선 계획](main-machine-missed-entry-priority-postclose-plan-2026-10-01.md), [보조 개선 계획](compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md), [현재 체크리스트](../checklists/2026-10-01-stage2-todo-checklist.md), [다음 실행 체크리스트](../checklists/2026-10-02-stage2-todo-checklist.md).
- 이번 작업에서는 계획·현재 릴리스/설치 cron·기존 artifact의 읽기 전용 대사와 문서 검증만 수행한다. 코드 구현·테스트 결과, deployment/PID, 실제 알림·자연 정책 성과는 그 실행에서 얻은 영수증으로 추가한다. 원천·보고서 재생성이나 runtime 조치를 계획 수립의 완료 조건으로 삼지 않는다.
- 문서 재리뷰: 새 계획 및 연결한 3개 문서의 로컬 링크 결손 0건, print-only parser 29개 항목 파싱, 신규 수리 owner와 기존 자연 수용 owner의 현재 OPEN 행 각 1개를 확인했다. 공백/diff 검사도 수행했다. runtime 코드·매매 suite·보고서 재생성·외부 동기화는 이번 문서 범위에 포함하지 않았다.
