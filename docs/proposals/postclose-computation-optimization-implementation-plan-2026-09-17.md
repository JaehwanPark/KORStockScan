# 장후 계산 최적화 3후보 구현 계획 — 2026-09-17

## 1. 목표·범위·현 상태

상태: **O0 main wrapper 계측·O3 행 내부 중복 계산 제거·O2 삼성 공통 feature/AVG_DOWN cache 정정 감지·저가주 rolling feature 및 replay/tick/비용 의존 결속·O1 discovery-local floor 재파싱 제거 부분 구현**. [부분 구현·검증](../audit-reports/2026-09-17-postclose-computation-optimization-scoped-implementation.md)을 기준으로 하며 전체 O0–O3 완료가 아니다. 대상은 ① main AI quality/provider replay ② 삼성 entry·저가주 2leg·AVG_DOWN 연구 계산 ③ source-quality/cumulative EV 반복 원천 처리다. 계획 문서 자체는 production 실행·provider/주문 호출·배포·재기동 권한이 아니며 별도 사용자 실행 요청 범위만 따른다.

목표는 동일한 유효 전체 모집단·후보·정책 의미를 유지하면서 parsing/replay/반복 결과 계산을 줄이는 것이다. 전수 연구의 정확성 보완은 [연구 로직 점검](../audit-reports/2026-09-17-widget-episode-policy-research-logic-review.md) 및 [전수 튜닝 계획](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md) U10A/B에 따른다. 계산 변경과 경제성·선정 의미 변경을 별도 diff/검증으로 구분한다.

## 2. 시간 기준과 계측 선행

2026-09-16/최근 완료·실패 receipt를 구분한 기존 장후 점검 기준이다. 이 수치를 세 후보 각각의 CPU baseline으로 대입하지 않는다.

| 관측 | 시간 | 해석 |
| --- | --- | --- |
| EOD update 9/16 | 20:05:04→20:54:59, 2,995초 | completed_with_warnings. 장후 원천 준비 대기; 세 후보의 연구 계산시간이 아님 |
| Machine final refresh 9/16 | 21:16:06→21:38:13, 1,327초 / 23:35:13→23:58:40, 1,407초 | 모두 실패. CPU는 85.25/100.682초. wrapper에 `source-wait-sec=900` 존재; wall 전체를 계산 병목으로 해석하지 않음 |
| Tuning monitoring 9/15 | 20:10:01→23:15:50, 11,749초 | predecessor wait 10,920초 포함. 후속 실행 약 229초 |
| Monitoring 9/16 recovery | 00:11:35→00:16:10, 275초 | parquet 68초·검증 압축 107초·shadow diff 97초. 연구 family 계산 외 I/O 후보 |
| Entry AI paired batch 9/16 | artifact generated→finished 약 73초 | provider=openai. artifact 시각 차이이며 wrapper 전체 실행시간의 증거는 아님 |

근거 owner: `data/runtime/update_kospi_status/update_kospi_2026-09-16.json`, `data/report/tuning_monitoring/status/tuning_monitoring_postclose_2026-09-16.json`, 해당 `logs/update_kospi.log`, `logs/tuning_monitoring_cron.log`, `logs/threshold_cycle_postclose_cron.log`, systemd final-refresh terminal journal. 로그는 stat 후 bounded tail로 확인한다. 위 표는 기존 관측 snapshot이며 이번 계획 작성으로 최신 상태를 재생성하지 않았다.

### O0 — 공통 계측/기준 fixture

- 변경 지점: [postclose wrapper](../../deploy/run_threshold_cycle_postclose.sh)의 기존 `run_postclose_cmd`, [machine refresh wrapper](../../deploy/run_machine_microstructure_final_refresh.sh)의 기존 단계; producer 내부 source/replay/aggregate/write 경계. 기존 marker/status에 부가 정보를 넣고 필수 신규 timer/report를 만들지 않는다.
- 단계별 wall, child-inclusive CPU, peak RSS, read bytes/rows, cache hit/miss 사유, provider call/transport/retry, source/predecessor/reservation wait를 구분한다. TERM·failure도 부분 계측과 원래 exit code를 남긴다. CPU/RSS 측정 방식과 지원 여부를 기록하며 shell 부모의 사용량을 child 전체로 오인하지 않는다.
- 완료 일반일·고거래량일의 **고정된 복사 fixture**로 cold/warm/하루 append/과거 수정/비용 변경/중단 재개를 비교한다. 실패하거나 원천 미완성인 production run은 성공 baseline으로 쓰지 않는다.
- 원천 해시·clean baseline·exclusion·신호/정책/비용·label-as-of·후보 grid·expected calendar를 봉인한다. 동시 수정 중인 장중 원천을 full scan하여 benchmark하지 않는다. 64MiB 초과 또는 성장 중인 raw는 기존 summary/bounded 접근으로 inventory만 하고 연구 full pass는 허용된 완료 snapshot에서 수행한다.
- 단계별 작업량과 critical path를 확인한 뒤 O3→O2→O1 순으로 중복 local 계산을 줄인다. Provider transport가 지배하면 같은 입력의 중복 호출을 줄이는 것 외 속도 효과를 별도로 적는다.

산출물: 고정 fixture manifest, 단계별 baseline/after receipt, 변경 없는 canonical 경제성·선정 output. 기존 report 형식을 유지하고 timing 필드는 selection/hash 계약에서 적절히 분리한다.

## 3. O1 — Main AI quality evaluation/provider replay

### 현재와 변경 대상

[ai_quality_cycle.py](../../src/engine/scalping/micro_reversion/ai_quality_cycle.py)의 `_collect_rolling_inputs`, `_historical_backfill_already_covered`, `_run_bounded_historical_provider_backfill`, `_checkpoint_provider_reservation_bindings`, `run_cycle`이 owner다. 이미 historical coverage 검사, checkpoint, provider reservation/budget이 존재한다. 새 캐시로 이를 대체하지 않고 **같은 결과의 재파싱·재집계와 정확히 같은 최종 요청의 중복**을 줄인다.

### 구현 단계

1. Local source normalization을 source-date/generation 단위로 분리한다. 동일 frozen decision/outcome/paired 입력을 한 번 정규화하고 R0–R3/후속 집계에 전달한다. 프롬프트에 필요한 필드와 원래 source identity를 손실 없이 보존한다.
2. 기존 coverage/checkpoint의 재사용 키를 검토하고 누락된 의미 차원을 보완한다: exact parent/input content hash, provider/model, prompt/reviewer/classifier/schema revision, source-quality/exclusion hash, scope/venue/session, 정책·비용·label horizon 및 as-of. budget/reservation ledger는 결과 content와 별개로 실제 호출 이력을 유지한다.
3. 완료되고 검증된 동일 요청 결과만 재사용한다. replay/output에는 원래 provider receipt/run ID·시각과 이번 local 집계 시각을 따로 남긴다. timeout/in-flight/orphan의 성공 여부가 불명확하면 기존 recovery 계약으로 처리하며 blind retry로 중복 과금을 만들지 않는다.
4. 날짜 append는 신규 input과 그 영향을 받는 rolling aggregates만 재계산한다. prompt/schema/model/source/비용 수정은 영향 범위를 invalidation한다. historical source correction이면 수정 날짜 이후 의존 집계를 재평가한다.
5. 검증된 checkpoint는 write-temp→fsync/atomic replace 및 기존 lock 계약으로 관리한다. corrupt/mismatch는 원래 안전한 reader로 fallback하거나 기존 source block으로 남기며 cached PASS를 강제로 소비하지 않는다.

### 금지·검증·목표

- Provider/model routing·프롬프트 전략·자동 apply 계약·standing approval·일일/parent call cap을 최적화 명목으로 변경하지 않는다. CALL 부족을 빠르게 하기 위해 표본·미진입 arm을 줄이지 않는다. 새 provider 병렬 호출은 이 패키지 범위에 넣지 않는다.
- 회귀: 동일 완료 요청 warm call=0; prompt/parent/schema/venue/session 변경은 hit 금지; timeout 중단 재개 reservation 보존; unknown economics null; 두 프로세스 같은 키의 일관된 결과; 전체 cohort count와 선정 canonical output 동일.
- 사용 suite: `src/tests/test_micro_reversion_ai_quality_cycle.py`, `test_main_ai_quality_runtime_family.py`, `test_main_ai_quality_standing_authorization.py`, `test_micro_reversion_ai_quality_bridge.py`. Provider test는 mock/저장 fixture만 사용한다.
- 계측 후 목표: 동일 generation의 재파싱 1회, 유효 완료 checkpoint warm provider 호출 0회, local source/aggregate CPU 30% 이상 감소를 목표로 한다. transport 지연·새 요청 비용은 별도 보고한다. 목표 미달이면 원인/실제 수치를 제시하며 PASS로 숫자를 만들지 않는다.

## 4. O2 — 삼성 entry·저가주 2leg·AVG_DOWN 연구 계산

### 현재와 변경 대상

- [samsung_machine_entry_tuning](../../src/engine/monitoring/samsung_machine_entry_tuning.py): owner leg/lifecycle aggregate 및 `_axis_observations`, `build_policy_candidate`. 삼성의 subset-tightening 설명을 full relaxation 경제성 연구로 바꾸지 않는다.
- [low_price_two_leg_expanded_candidate_research](../../src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py): minute-bar loading/기존 `_load_source_cache`, `_source_cache_contract`, `research_input_fingerprint`, `reusable_report`와 profile replay. 기존 source/result 캐시가 있어 중복 구축하지 않는다.
  - [기존 entry spot helper](../../src/engine/monitoring/low_price_two_leg_entry_spot_research.py)의 `build_day_contexts`는 전체 lookback의 rolling extrema/연속성 계산을 재사용한다. 기존 전체 grid·후보별 state·holdout·비용·선정 의미를 보존한다. Report fingerprint에 replay/tick helper와 실제 비용 계약을 결속하고 손상/non-object JSON은 miss로 처리한다. 이 부분 검증은 full candidate/day checkpoint·append/정정 matrix 완료가 아니다.
  - O2 관측창 재생 후속: 기존 `select_profile_spot`의 calibration 전반/후반/전체를 `_evaluate_candidate_windows`의 한 clean-prefix 재생으로 처리한다. 각 창의 종료 시점 evidence·HELD 이월·후보별 state·원래 full grid/선정은 유지한다. [부분 리뷰 §11](../audit-reports/2026-09-17-postclose-computation-optimization-scoped-implementation.md#11-o2-calibration-관측창-clean-prefix-재생-통합)을 따른다. Persistent day checkpoint·append/정정 및 전체 scale matrix는 여전히 미완료다.
  - O2 report 재사용 선행 보완: writer가 입력 fingerprint와 별개로 실제 결과 본문 digest를 발급하고 reader는 정상 terminal·exact date/input·안정된 regular file·본문 및 기존 native 추천 계약을 검증한다. 구 receipt/손상/진행 중 결과는 cache miss이며 원천 bar의 재수집 권한이 아니다. Warm reuse에서도 `--notify`의 기존 bounded/dedup 전달을 수행하고 실패는 exit0으로 숨기지 않는다. [리뷰 §13·배포 §14](../audit-reports/2026-09-17-postclose-computation-optimization-scoped-implementation.md#13-o2-report-재사용-무결성후행-전달-보완)를 따른다. 새로운 경제성 floor·승인·collector/job 없이 기존 자동 장후 경로로 소비한다. Persistent day checkpoint·append/정정은 여전히 별도 잔여 작업이다.
  - O2 profile checkpoint 후속: 기존 expanded CLI/source-cache에 hash-bound profile selection checkpoint를 연결해 unchanged profile을 재사용하고 실제 bar 정정 symbol만 full grid 재계산한다. Source-quality gate 우선·본문/identity/date/cost/authority·pinned atomic publication·현재 정책/native 후행 검증을 유지한다. [리뷰 §15·배포 §16](../audit-reports/2026-09-17-postclose-computation-optimization-scoped-implementation.md#15-o2-profile-selection-checkpoint종목별-정정-무효화): 작업본389/managed345 physical·shared PASS, synthetic warm selection CPU95.454~99.395% 감소(키 생성/원천 loading/전체 runtime/RSS/경제성 제외). 새 job·floor·승인 없이 기존 자동 장후 경로에 배포했으며 main PID는 유지했다. **완료 selection checkpoint일 뿐 day-state append resume가 아니므로** 새 날짜/partition 이동·cost/grid/profile 정정은 해당 profile full replay, O2 전체 family/day-state/append 및 O0/O1/O3/P1–P6·자연 후행/경제성은 OPEN이다.
- [scalping_avg_down_recovery_calibration](../../src/engine/monitoring/scalping_avg_down_recovery_calibration.py): `_replay_source_files`, `_load_replay_cache`, `build_report`의 source normalization/replay/summary. 실제 ADD와 source-only/CF를 합치지 않는다.

### 구현 단계

1. family별 고정 source-day 자료를 날짜/종목/owner/session/route/epoch·source/cost/parser hash로 정규화한다. 분봉 prefix low/high·완료 bar·시간 index 등 후보 불변 특징은 한 번 계산한다. Stateful cooldown/leg/target replay 결과를 불변 특징으로 오인하지 않는다.
2. 기존 grid의 동일 공통 경로를 재사용한다. low-price profile의 같은 drawdown/proximity trigger를 한 번 계산한 뒤 차이가 있는 수량·target·hold/exit만 분기한다. AVG_DOWN은 동일 parent/lifecycle/paired-exit 경로를 공유하되 candidate 변경 시 영향을 받는 state부터 다시 재생한다.
3. 결과를 source-day/candidate-semantic-key 단위로 checkpoint한다. 키에 profile/모든 tunable parameter·owner·수량·entry/exit/cooldown·cost·expected source-day/holdout partition을 포함한다. Source cache는 비용 불변 가격 자료와 경제성 결과를 나누어 비용 변경 시 raw 재다운로드 없이 경제성만 재계산한다.
4. 계산은 bounded iterator/chunk로 처리하고 stable grid order/tie-break를 유지한다. winner·gate counters·incremental caps·필수 diagnostics만 memory에 유지하되 선정 계약이 요구하는 대안 후보를 버리지 않는다. 공통 owner state를 여러 후보가 mutation으로 공유하지 않는다.
5. 날짜 append 시 신규 날짜만 replay하고 calibration/holdout 이동으로 영향받는 집계는 갱신한다. 과거 정정·profile/exit/cost 수정은 해당 replay와 dependent aggregate를 무효화한다. Family 간 source facts는 공유 가능하나 eligibility와 apply 권한은 공유하지 않는다.

### 정확성과 성능 acceptance

- 모든 등록 grid·유효 no-submit opportunity·valid-zero source day를 유지한다. random sampling, grid 축소, 상위 종목만 계산, sample floor 완화로 속도를 맞추지 않는다.
- U10 의미 보완 전후 output 차이는 correctness 변경으로 설명한다. 성능 동등성은 **동일한 수정 완료 의미**의 reference/optimized 구현 사이에서 검사한다. 과거 filled-only 결과 일치를 전수 완료 acceptance로 쓰지 않는다.
- Reference/optimized의 episode/leg 원천 identity·filled/held/censored disposition·net PnL·notional/자본 점유·calibration/holdout/half·선정·cap incremental·carry 이유를 비교한다. 수치 누적 순서/반올림을 유지하여 near-zero gate와 tie가 달라지지 않게 한다.
- Fixtures: zero signal, held leg, 두 target 동일 bar touch, partial fill, 반복 anchor, 비용 effective-date 경계, source missing/corrupt, 4·5번째 entry의 음수 incremental, 한 날 append, source 정정, TERM 재개, cross-profile 겹침.
- 사용 suite: `test_samsung_machine_entry_tuning.py`, `test_low_price_two_leg_expanded_candidate_research.py`, `test_low_price_two_leg_entry_spot_research.py`, `test_scalping_avg_down_recovery_calibration.py`, `test_avg_down_replay.py`, `test_avg_down_policy_replay.py`. 변경한 함수의 suite만 선택한다.
- 계측 후 목표: family/candidate grid compute CPU 50% 이상 감소, warm 동일 report는 유효 fingerprint 재사용, 한 날짜 append 비용은 신규 replay+필수 partition 집계 수준. peak RSS는 baseline 이하를 목표로 하며 실제 resource 계약을 넘지 않는다.

## 5. O3 — Source-quality/cumulative EV 반복 원천 처리

### 현재와 변경 대상

[observation_source_quality_audit.py](../../src/engine/observation_source_quality_audit.py)의 `_raw_generation`, `_streaming_contract_audit`, `build_observation_source_quality_audit`는 이미 streaming과 generation-before/after 안정성 검사를 한다. [threshold_cycle_ev_report.py](../../src/engine/threshold_cycle_ev_report.py) 및 postclose wrapper가 같은 source를 읽는 구간을 O0에서 확정한다. 실제 반복 I/O가 확인된 reader만 변경하며 추측으로 전체 consumer를 갈아엎지 않는다.

### 구현 단계

1. 기존 final-source freeze 경계에서 한 번의 raw pass로 verified compact projection/index를 생성한다. logical source ID·physical source generation·완전성/row count·canonical line digest·parser/schema contract·clean baseline/exclusion을 결속한다. source를 이미 검증한 generation이면 receipt를 재사용하고 매 consumer가 raw 전체를 다시 hash하지 않도록 검증 책임을 명시한다.
2. Consumer는 검증된 projection의 필요한 column/record-role만 읽는다. raw line identity/provenance는 보존하며 full/partial real, sim/probe/CF, owner/venue/session을 구분한다. projection 손실로 outcome/quantity/cost가 null이 되거나 CF가 actual로 바뀌지 않게 한다.
3. Preflight→final reuse는 동일 input일 때만 허용한다. append가 있으면 봉인된 prefix의 검증과 신규 완전 line의 delta audit·집계를 수행하고 exclusion 및 contract 수정은 재검증한다. prefix rewrite/truncate/rotate/gzip 변화는 기존 streaming full fallback 대상이다. byte offset만 믿고 prefix 불변을 가정하지 않는다.
4. 안정된 prefix와 append를 증명할 수 없는 writer에서는 delta 최적화를 포기한다. 변경 중 raw는 현재 generation fail-closed 판정을 유지하고 안전한 완료 snapshot을 기다린다. no-follow/lock/atomic replace 보호를 유지한다.
5. Cumulative EV는 날짜별 충분통계와 exact-cost outcome을 저장하여 변경 날짜 및 rolling/MTD/cumulative 의존 집계만 재계산한다. 중복 lifecycle/native ID 제거, valid-zero day, null economics, exclusion 변경을 full reference와 대사한다. 압축/파케 변환의 손실 없는 검증과 기존 shadow diff를 생략하지 않는다.

### 검증·목표

- Warm identical source generation에서 full decode/audit 최대 1회, 이후 verified projection 읽기. 실제 source 감사를 필요한 날 한 번은 수행한다. identity 검증을 피해서 얻은 cache hit는 인정하지 않는다.
- 동일 source/schema/parser에서 stage counts·hard gate·row exclusions·source consumption status·EV numerator/denominator/선정/authority가 reference와 동일해야 한다. Preflight PASS 뒤 신규 bad row가 append되면 final gate가 그대로 PASS로 남아서는 안 된다.
- Corrupt sidecar, swapped raw, symlink/no-follow 위반, same-size rewrite, incomplete last line, conflicting duplicate, plain↔gzip, contract/exclusion/cost 정정 fixture를 사용한다. raw missing·invalid high-volume 입력의 fail-closed 및 identifiable row 격리 계약을 유지한다.
- 사용 suite: `test_observation_source_quality_audit.py`, `test_threshold_cycle_ev_report.py`, `test_threshold_cycle_wrappers.py`와 수정한 compact consumer suite.
- 계측 후 목표: 실제 중복 raw decode/read bytes 60% 이상 감소, audit/aggregate CPU 30% 이상 감소. 압축·parquet wall/RSS는 별도 기록한다. source 준비/체인 wait 0으로 만들기 위해 순서를 바꾸지 않는다.

## 6. 전달·구현 순서·롤백

| 단계 | 완료 산출물 | 다음 단계 조건 |
| --- | --- | --- |
| O0 | frozen fixture manifest/phase receipt/현재 reader map | compute·I/O·provider·wait를 분리, 기존 resource·권한 확인 |
| O3 | verified projection/delta audit와 full reference parity | final source/exclusion 정확성·fallback·concurrency 검사 통과 |
| O2 | family별 replay/checkpoint·동일 의미 oracle 비교 | U10 변경 의미와 성능 변경 분리, full grid/zero-day/holdout parity |
| O1 | 기존 provider checkpoint 확장·local aggregate 재사용 | exact-request 재사용/예약·예산·재개 계약 보존 |
| 자연 확인 | 다음 허용된 장후 run의 phase/consumer receipt | source→tower→checklist→strict verifier→controller/cleanup 기존 순서 보존 |

새 공통 코드가 필요하면 기존 `src/engine/monitoring`, `automation`, `infrastructure`의 역할/근접 consumer를 먼저 조사한다. `src/engine` root에 새 Python 모듈을 추가하지 않는다. 새 파일/테스트는 location gate와 ownership 이유를 적용한다. 운영 wrapper 변경 구현 시에만 관련 운영문서·현재 checklist를 함께 갱신한다. 이 계획 작성은 운영 instruction을 변경하거나 실행하지 않는다.

각 패키지는 implementation→self review→보완→re-review→targeted pytest/import·compile→wrapper 변경 시 `bash -n`/contract tests→`git diff --check`로 닫는다. Document/checklist 변경은 print-only parser를 사용한다. parity가 깨지면 신규 cache 경로를 비활성화하고 검증된 기존 reader/replay로 되돌린다. 원본 raw·exclusion·provider reservation·정책 receipt를 삭제하지 않는다. 경제성 계약 자체의 source block은 fallback으로 우회하지 않는다.

현재 U10A/B 구현 owner는 오늘 체크리스트 `KiwoomCommonHealthOpportunityCostAcceptance0917`, widget 자연 source/evaluation owner는 `WidgetPostcloseEvaluationPinAcceptance0916`이다. 본 계획은 계산 후속의 범위 문서이며 별도 자동 실행 OPEN/cron을 만들지 않았다. 사용자가 계산 구현을 지시하면 그때 owner·일정·허용 resource를 정하고 이 순서로 진행한다. source code/targeted 검증, selected release, 실제 wrapper/PID 소비, 자연 정책 생성, 비용차감 실현수익은 각각 보고한다.

문서-only 검증은 링크·owner·authority 검토, diff check 및 print-only parser로 수행한다. 위 성능 백분율은 구현 후 측정할 목표이며 이번 작성으로 달성된 실측 결과가 아니다.

## 7. 전체 폐루프·연구 universe 확대의 추가 성능 패키지

[전체 폐루프 상세계획](./widget-episode-full-closed-loop-and-scale-performance-implementation-plan-2026-09-17.md) C0–C8/P1–P6을 이번 확대 범위 owner로 참조한다. 기존 widget source closure에서 구현된 prefix/setup/exit reuse·bounded day cache·projection·checkpoint는 다시 미착수로 표시하지 않는다. 신규 census admission·전향적 seed K·executable CF·joint rule replay·성과 attribution의 추가 비용이 대상이다.

| 추가 패키지 | 기존 후보와의 연결 | 구현 선후·oracle |
| --- | --- | --- |
| P1 공통 day source/manifest·single decode | O0/O3 | C0 fixture/semantic dependency→C1 native ledger; writer freeze와 consumer 검증책임 확정 |
| P2 raw quote/depth/TTL/seed execution index | O3/O2 | C2 budget/clock/epoch→C3 prospective contract 먼저; raw-only를 과거 seed 신호로 만들지 않음 |
| P3 incremental full-grid/partition | O2 | 수정 완료 의미 reference→기존 day cache/feature reuse 확장; 새 day/정정/dependent state만 replay |
| P4 공통 경제성·joint interval/registered rule replay | O2/O3 | C4 기존 allocator·owner를 고정한 calibration/holdout/joint economics oracle; 권한과 eligibility 공유 금지 |
| P5 readiness/phase 재개·중복 refresh 방지 | O0 | 기존 wrapper 단계 contract/lock→동일 target·source completion을 기다려 필요한 단계만 재실행 |
| P6 memory/storage/scale matrix | O0/O3 | N19/50/100·D72/120·G전체1,536/cap1–5·K1/4 cold/warm/append/정정/TERM 계측; live/rollback evidence 보호 |

상세 계획 §7의 `12N초` REST cycle과 `N×D×G×B` 계산 모델로 관측 capacity·CPU·read bytes·disk를 따로 예측한다. 최종19종목 synthetic cold1,209.895초/warm43.818초/RSS281.3MiB는 **확대 폐루프 구현 전 engineering baseline**이다. 단순 비례에서100종목 cold약6,368초는 단계budget5,400초를 초과할 수 있으며 실제 provider/EOD wait를 더하면 critical path는 더 길어진다. 기존21:15 refresh의900초 wait와 nightly acceptance도 포함해 deadline을 검증한다. N100/D120 stage budget·RSS/parity 목표와 추가 compute20% 목표는 후속 실측 대상이다.

모든 단계의 optimization key·invalidation을 source/code/helper/seed/수량/비용/exclusion/label as-of/calendar/parent allocator까지 확장한다. N/K 확대가 raw TR을 후보수만큼 늘리지 않아야 한다. Cold/warm/매일 incremental 비용을 따로 기록하고 unchanged replay0·동일 source provider 중복0을 검증한다. Cache byte cap/LRU는 고정 working set·현재 free disk 계측 후 숫자로 확정하며 원본 raw·policy·receipt retention을 축소하지 않는다.

O3→O2→O1의 기존 local 최적화 우선순위는 유지하되, C1–C4 correctness 변경 의미가 봉인되기 전에 성능 parity를 주장하지 않는다. 위젯/episode 확대 critical path는 P1/P2/P3/P4를 먼저 닫고 provider O1은 실제 병목일 때 이어서 적용한다. 계획 작성만으로 CPUQuota·MemoryMax·REST/provider cap·timer·sampling/floor를 바꾸지 않는다. Backlog는 native ledger/phase checkpoint에 남고 미완료 joint/source를 완료 policy로 발행하지 않는다.

이번 전체 폐루프 source 구현과 반복 리뷰·규모 실측/배포 상태는 [09-17 구현 기록](../audit-reports/2026-09-17-widget-episode-full-closed-loop-implementation.md)을 따른다. C0–C8/P1–P6 producer/consumer를 연결하며 자연 신규 정책·actual next-date 소비·경제성은 기존 stable-ID acceptance owner에서 따로 확인한다. Final-refresh의 native account source 취득은 N/K에 비례하지 않고 기존 read adapter/cached token만 사용한다. Timer/grid/caps/sample/hard guard는 유지한다.
