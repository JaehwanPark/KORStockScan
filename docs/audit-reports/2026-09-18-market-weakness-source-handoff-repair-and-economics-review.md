# Market weakness 원천·날짜 인계 수리 및 경제성 재검증 — 2026-09-18

## 판단

원천/수집 대상 인계의 구조적 결함을 수리하고 native9/17 attribution→튜닝→effective9/18 정책 파일을 갱신했다. 새 경제성 후보는 없으며 기존 발동2회·해제3회 carry다. 자연 시장 관측, 연속0B/0D 호가 수집, 실제 적용 버전의 완료 손익은 서로 다른 acceptance다. Main의 기존 PREOPEN 인계 실패를 우회하지 않는다. 이 수리로 전체 장후 chain을 DONE으로 만들지 않는다.

## 결함·수리·회귀 검증

1. Widget calibration의 scanner 연구179·research watch13·자동 발견2개를 모두 active owner로 취급해201개가 absolute cap200을 넘었다. 명시된 research origin194개를 prospective 연구로 보존하고 established/native owner와 실제 execution owner는 active로 유지한다. `active_owner_collection_target_capacity_exceeded`가 후행 attribution과 날짜별 튜닝을 끊던 직접 원인이다.
2. Active owner 수를 research budget4에서 차감해 prospective 수집이 항상0이 됐다. 기존 prospective budget4(상한8)을 active coverage와 독립 적용하되 전체200symbol/400registration item cap은 유지한다. 다중 route active399item일 때 prospective는1개만 선택한다. v3 marker 없는 기존 shared-budget artifact 및 v1/v2 소비는 유지한다. 주문/cap/env를 바꾸는 행위가 아니다.
3. `KRX_NXT_AFTERMARKET`를 문자열 앞부분 KRX로 오인했다. 명시적 `market_data_route=krx_nxt_integrated`, `market_venue=KRX_NXT` 계약이 있을 때 SOR의 `<symbol>_AL` 관측으로 결속한다. 계약이 없으면 gap이며 실제 체결 venue를 추정하지 않는다.
4. 자연 intraday cron이 작업본 validator를 소비해 `market_weakness_policy_review_hash_invalid`로 fallback했다. 기존 wrapper의 default scheduled 호출을 기존 strict release selector로 연결하며 잘못된 selection에서는 실패한다. 명시된 PROJECT_DIR operator/test 경로를 보존하고 cron/정책 값/guard는 바꾸지 않는다. 기존 final-refresh service의 ExecStart/WorkingDirectory와 import-root 환경도 서로 다른 release를 가리켰다. 배포 시 기존 마지막 drop-in의 네 source binding을 동일 reviewed root로 맞춘다. 새 unit/cron은 없고 실행 중 process의 source는 변경하거나 재시작하지 않는다. 미래 실행 source 선택만 배포 증거다.

Affected collection/attribution/market-response/hysteresis 계약187 PASS(9.12초), wrapper/release 소비12 PASS(6.55초)·기존 guard/observer/forward collector90 PASS(2.05초), compile/bash syntax/diff와 print-only 문서 parser를 검증했다. Evidence: `tmp/market-weakness-source-handoff-20260918/targeted-tests-final.log`, `validation.json`, `publication.json`, `deployment.json`. 기존 guard/후보 grid/holdout/floor/cost/safety는 변경하지 않았다. 광범위 trading suite·성능 benchmark·전체 장후 replay는 실행하지 않았다.

공식 Kiwoom gate: upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회2026-09-18 13:03:15 KST. `kiwoom/specs.py`, `_data/kiwoom_api_spec.json`의0B/0D/ka20003, core/realtime 및 Postman을 대사했다. 현 revision에 `kiwoom_docs`는 없다. Existing KRX/NXT/SOR item 의미를 유지하며 wire/parser/FID/auth/request를 수정하거나 API를 호출하지 않았다. 상세 `official-reference.json`.

## 제한 결과 갱신과 인계

9/17 raw는46file/3,789,352,920byte다. 기존 streaming producer를 private output에 한 번만 실행했다. 같은 raw 재계산은 하지 않고 cached 결과에서 기존 tuner/publisher/loader만 검증했다. Original as-of/source generation을 유지한 native successor를 canonical 날짜에 인계했다. 계산 이후 mutable `widget_signal_auto_trade_state.json`의 mtime이 변경돼 generation의 현재 재사용 검증은 false다. 이를 숨기거나 fingerprint를 다시 쓰지 않았다. 이 보고서는 해당 계산 as-of 증거이며 최신 live-state 재사용/PASS로 주장하지 않는다. Dated tuner는 immutable source snapshot의 실제 canonical SHA·date·authority를 검증한다. 승인 후보가 없는 carry의 갱신이며 새로운 경제성 승격이 아니다.

- Native attribution9/17: dynamic214symbol, widget201, episode1,081profile, anchor322(entry212/exit110), matched0, promotion candidate0. 운영 생성 성공과 source/economic 결손을 분리한다.
- Collection target9/18: active20symbol/24route 전부 선택, prospective4, 총24symbol/28item, prospective overflow190. Schema/authority/date loader=loaded. 대상 manifest 선택은 등록/수신 성공이 아니다. 기존9/17 registration receipt는19:50:21 작성이며 incomplete105630_AL/131290을 포함한다. 이를 과거 주간 horizon coverage로 소급하지 않는다.
- Hysteresis tuning9/17→policy9/18: immutable source snapshot/date/hash 검증, review=`current_policy_carry_forward_no_approved_candidate`;2/3 유지, hash `af75d4132a58f38402438a82bab6b7e26ecd55ad3b0a6464388a5ec5ad0aa597`. 직접 dated 소비의 실제 receipt는 `natural-and-version-evaluation.json`에 기록한다. Hash가 같은 fallback과 검증된 carry는 source/status로 구분한다.

## 자연 표본·독립 경제성·기존 후보

| 축 | 갱신 결과 | 해석 |
|---|---:|---|
| 9/17 시장/state source eligible anchor |85/85| 시장 조인 준비이며 독립 실행 경제성 준비가 아님 |
| 9/17 독립30분 CF eligible |0/85| required quantity·depth-backed entry/exit·30분 horizon 모두 결손 |
| 누적 deduplicated opportunity |1,323| clean baseline 이후 native primary key; conflict0 |
| 누적 독립30분 CF eligible / 제외 |11 /1,312| 유효율0.831444%; 제외를 no-edge로 읽지 않음 |
| 유효 날짜 / holdout 날짜 |2 /0|9/3·9/15 calibration만 존재 |
| KOSPI / KOSDAQ 유효 표본 |11 /0| 양시장 gate 미달 |
| Widget / episode 유효 표본 |6 /5| 각 owner floor 미달 |
| 기존 후보2/2·2/4·3/3 |calibration ΔEV 각0.0%p| 미선정; full/holdout ΔEV null, holdout 미평가 |
| Approved selected policy |null| source 부족 + calibration 차별성 없음; 검증 완료 no-edge 아님 |

85개 당일 anchor의 다중 exclusion: missing30m85, entry ask85, exit bid85, required quantity85, registration incomplete81, anchor window unobserved4. Prospective episode signal은 planned quantity를 명시하지 않는다. 후행 simulated fill의1주를 과거 signal 요청수량으로 복제하지 않는다. Native blocked/live decision producer는 요청수량을 이미 기록하므로 그 계약의 자연 표본을 우선 검증한다. Prospective 신호까지 독립 비교에 넣으려면 기존 research producer가 신호 시점에 고정된 planned quantity/leg/target 계약을 제공해야 한다. 그 전에는 제외하며 floor를 낮추지 않는다.

Attainability의39개 부족/추가50거래일 투영은 기존 저수율을 가정한 진단이다. 구조적 registration/quantity/horizon gap이 있어 달성 ETA는 null이다. 시간이 지나면 비용/완료 label·holdout은 성숙할 수 있지만 없는 과거 continuous depth는 시간이 해결하지 못한다.

## 실제 적용 버전별 성과

Model 기준 현행 CF EV−0.41349624%와 challenger calibration ΔEV0.0%p는 actual profit이 아니다. 누적 actual/control 비교1건의 skip incremental−0.35014535%p는 해당 과거 control 비교 진단이며 신규 적용 정책의 실현 순익/원화 PnL이 아니다. 해당 source는 여전히 sample floor 미달이다.

실제 적용은 관측 ID→immutable observation의 target/source_date·policy_hash·source/status→owner decision/episode lifecycle→COMPLETED+valid cost/profit로 결속해야 한다. 같은2/3 hash인 fallback과 dated carry의 적용 구간도 구분한다. Widget/episode 자체 execution-policy version만으로 hysteresis 이익에 귀속하지 않는다. Collection selection·consumer health·source release 선택만으로 자연 주문/실현 이익을 만들지 않는다.

현재 신규 수리 버전에 결속된 completed 실제 표본이 없으므로 rolling/cumulative 비용 차감 EV·원화 순익·p10/tail·노출/자본시간·model error는 null이다. 새로운 model ΔEV 역시 승인 후보가 없어 수익 개선치로 제공하지 않는다. 집계 원본/episode 중복 제거/현재 소비/버전 단위 disposition은 `natural-and-version-evaluation.json`을 따른다.

## 남은 owner·다음 행동·closure test

| Blocker / owner artifact | 다음 행동 | Closure test |
|---|---|---|
| Main PREOPEN `runtime_env_handoff_missing`; 기존 dated runtime manifest/validator | 기존 승인된 bundle/env source owner가 strict 인계를 닫은 후 정상 Main 시작 경로로 소비; env 수동 우회·임의 주문 금지 | exact-date strict PASS→실제 Main PID→동일 날짜 target manifest→0B/0D 등록 receipt·정확 item·연속 경로/누락 disposition |
| `scalp_micro_reversion_forward/trade_date=2026-09-18` 부재; 기존 Main callback observer | 기존 publisher/WS producer의 자연 실행 확인; 새 collector/timer를 만들지 않음 | dated partition·receipt·configured_at≤anchor·quantity/cost·depth/H30 보존, source eligible/blocked 분모 일치 |
| Prospective episode signal planned quantity 부재; 기존 expanded research 원천 | 신호 전 명시된 quantity/leg/target contract가 있을 때만 소비; retrospective fill proxy 금지 | unfilled/blocked 포함 native decision의 original quantity·target·route가 source SHA와 결속되고 depth capacity를 만족 |
| Holdout/KOSDAQ/sample 부족; 기존 hysteresis evaluator | 위 원천 유효 표본의 자연 성숙 후 기존2/2·2/4·3/3만 재검증 | 기존 calibration selection→독립 chronological holdout·양시장/owner/cost/tail/promotion gate 충족; 후보0 disposition 명시 |
| Actual applied-version completed 표본 부재; native observation/guard/ledger | 실제 적용 lineage가 있는 자연 완료 손익만 누적 | episode key 중복0·비용/venue/session/owner 일치→version별 rolling/cumulative EV/net/tail/exposure/error; actual/CF 분리 |
| 전체 final-refresh의 native economic source/expansion/threshold EV 선행 결손 | 해당 별도 현행 owner가 해결; 이번 단위 성공으로 전역 DONE 처리하지 않음 | 전역 strict handoff/controller finalization은 별도 원천·날짜 계약 모두 충족 |

Executable acceptance: [당일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `MarketWeaknessSourceHandoffNaturalEconomics0918`. 코드 closure/배포와 자연 표본/후보/실제 성과 closure를 분리한다.

## 자연 소비 재리뷰 보완

13:22:01 자연 collector에서 `exact_date_applied_policy`, source_date9/17·target9/18·applied를 확인했다. Notifier는 기존 fallback과 source 문자열이 다르다는 이유로 `intraday_hysteresis_policy_mismatch`를 반환했다. Native source 복구에 실제 consumer까지 이어지는 추가 결함이다. 기존 notifier에서 fallback→검증된 dated carry의 policy hash·횟수·최소 간격이 모두 동일한 경우만 출처 인계를 허용한다. 새 threshold/promotion·역방향 fallback·hash 불일치는 기존 차단을 유지한다. 기존 latch/streak를 다시 만들지 않고 원래 자연 관측으로 계속 진행한다.

Pending weak streak1→정상 두 번째 관측의 발동2, active latch→첫 recovery 후 release_pending/active 유지, 동일 횟수라도 carry가 아닌 promotion의 거부와 기존 threshold 변경 거부를 검증했다. Notifier/guard/dated publisher 계약66 PASS(1.85초), compile/diff/parser 및 병합 후 wrapper 계약을 확인한다. Source/선택 commit과 자연 최종 observer health는 `deployment-r2.json`, `natural-and-version-evaluation.json`을 따른다. Raw 재계산·수동 notifier 상태 변경·Main 재시작은 없다.
