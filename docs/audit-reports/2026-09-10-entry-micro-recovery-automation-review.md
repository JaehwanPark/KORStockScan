# 9/10 초단기 회복·NXT·순수익 기준 보완 리뷰

## 판정 / 범위

사용자의 권장 실행·반복 코드리뷰 지시에 따라 기존 setup-risk owner 안에서 수정했다. 목표는 BUY 비율이 아니라 **전체 비용 후 작은 이익의 반복과 누적 순이익**이다. 새 standalone 매매기계, #81 retired bridge, Provider/model 변경, 수량/cap 확대, broker API 변경은 없다. 코드 closure와 새 Provider 판단/경제성/실제 PID 반영을 분리한다.

이 문서는 [08:47 KRX 적용 기록](2026-09-10-entry-prompt-bounded-apply-review.md)의 후속이다. 그때 설치한 v9 기반 V2.14 후보를 이번 v10 검증 근거로 재사용하지 않는다. 이번 작업은 새 activation 설치·재기동·Provider 호출·실주문을 실행하지 않았다.

## 수정과 연결

| 결함 / 병목 | 보완 | 권한 경계 |
| --- | --- | --- |
| `no_supported_setup`를 구조 훼손으로 단정 | `UNCONFIRMED`와 실제 `INVALID` 분리, risk schema/prompt/composer/adapter 연결 | 미확인은 WAIT/NO_EDGE, probe 없음. 실제 invalidation은 계속 차단 |
| 완성봉 이전 회복이 setup 밖으로 탈락 | `MICRO_RECOVERY`: 기존 source-qualified 공격매수 순량 + 실제 단기 가격 반응, executable liquidity 확인 | completed-bar phase는 그대로 배경으로 보존. 새 positive 회복도 WAIT/probe intent이며 full BUY 아님 |
| 후보를 인정해도 기존 VWAP 위치 조건에서 재차 탈락 | 새 micro family의 최신 feature producer→revalidation을 연결 | 일반 micro 조건은 그대로. fresh source·large-sell veto·1주·일일3회·residual/scale-in 금지 유지 |
| 미확인 WAIT의 긴 재관측 공백 | 승인된 정확한 activation/venue/session의 상태 변화에 한해 30초 관측창, parent당1회·stock state의 종목/당일 최대2회 재평가 | 순수 AI-WAIT anchor와 정확히 같은 cooldown만 대상. 기존 계좌/주문/보유/손실 cooldown은 해제하지 않음. 무한 슬롯 보존 아님 |
| NXT는 평가 후 live 후보 미발행 | 기존 평가 대상 `NXT/NXT_AFTERMARKET` 후보·PREOPEN 파일·resolver·adapter를 KRX와 분리, PREOPEN wrapper `--all-cohorts` | NXT 근거와 NXT scope/kill switch 필요. KRX 자료 전용 금지, 공유3회 cap을 venue별3회로 증액하지 않음 |
| execution-cost proxy가 전체 비용 순이익처럼 승격 가능 | 기존 verified action-neutral cost/master/path로 누적 `full_cost_economics` 생성·candidate 연결 | 수수료/세금 결손은 제외. 이미 비용 차감된 수익을 재차 차감하지 않음. CF를 실제 fill/PnL로 표시하지 않음 |

정책은 `entry_setup_evidence_policy_v10`, 기본 composer는 `entry_decision_composer_policy_v11`로 변경했다. V2.14/V2.15 family 이름을 재사용하되 evidence/prompt/schema hash가 달라져 기존 v9 결과는 새 후보를 승인할 수 없다. V2.15에서도 micro recovery를 기존 bounded-recovery 경로로 연결하며 V2.16은 계속 source-only다.

현재 ask 잔량 감소 자체를 BUY 신호로 승격하지 않았다. 취소/refill과 실제 공격매수 구분이 안 되는 자료를 synthetic positive로 만들지 않는다. 종목명 특례와 사후 고가를 사용한 정답 삽입도 없다.

## 확인된 효과 / 아직 입증되지 않은 효과

- 저장된 08:18 나우로보틱스 exact payload 재생: 기존 `INVALID/no_supported_setup` → `UNCONFIRMED/SETUP_DISCOVERY_RECHECK`, invalidation 없음, validator 오류0. 매수압력99.32%·순량1009지만 `price_change_10t_pct=0`이므로 즉시 probe 없음. PREMARKET_KRX_LIKE/SOR를 exact NXT로 바꾸지 않았다.
- 회귀 fixture: 같은 completed-bar range와 VWAP -95.97bp라도 fresh flow 및 양의 가격 반응이 있으면 micro WAIT/probe로 연결된다. 가격 반응0/음수/결손/NaN, stale/unknown source, adverse flow, large sell, 실제 distribution invalidation은 진입 근거가 되지 않는다.
- 순수익 fixture: 전체 비용 후 +0.03%인 10건/3종목도 별도 +1% 수익 문턱 없이 검증 가능하다. 그중 한 건 -0.5% 손실이면 전체 기대값이 음수가 되어 승격하지 않는다. 비용 미확인 자료는 0으로 채우지 않는다.
- 이는 코드 동작 검증이며 실제 적중률·체결 빈도·원화 순이익 개선 수치는 아니다. 새 exact payload의 Control/Candidate Provider replay, 이후 실제 submit/fill/terminal 및 비용후 결과가 필요하다. [OpenAI 평가 지침](https://developers.openai.com/api/docs/guides/evaluation-best-practices)에 맞춰 정상 사례와 부정 반례를 함께 검증하고, 출력 형식 성공만으로 품질 개선을 선언하지 않는다.

## 자동화와 적용 조건 판정

확인한 설치 cron은 평일21:05 paired replay, 평일07:35 PREOPEN이다. 기존 각 cohort 신규30요청·worker2·최대3 wrapper attempts와 검증된 checkpoint 재사용은 그대로다. 새 호출량 상한이나 무제한 재생을 만들지 않았다.

1. **자동인 부분:** 기존 exact source→cohort별 replay/누적→후보 발행→다음 유효 PREOPEN activation→런타임 resolver 선택. NXT 애프터마켓 발행/소비 누락을 보완했다. 07:35 handoff 이후 생성된 후보는 다음 거래일 대상으로 넘어간다.
2. **자동 강제 ON은 아님:** recheck ENABLED와 exact ALLOWED_SCOPES, 당일 apply date, 1주/probe-first/후단 resolver, operator veto, candidate/source hash가 모두 필요하다. PID가 새 코드를 읽는 배포는 후보 생성과 별개다. 이번에는 PID375167을 재기동하지 않았다.
3. **현재 미반영:** 09:15:38 PID375167 env는 configured V2.13 + 기존 KRX V2.14 activation 경로, recheck ON/`KRX|KRX_REGULAR`만 허용한다. 새 v10 micro 정책 및 NXT scope 적용 완료라고 표시하지 않는다.
4. **현재 경제성 근거 부족:** source9/9 v9 KRX30요청/누적80 arms/1 exposure, NXT30요청/157 arms/3 exposures. 두 cohort 모두 verified full-cost request0, `exact_cost_aware_label_artifact_missing`이다. 원본 artifact를 새 버전으로 재라벨하지 않았다.

조건의 엄격성은 다음처럼 구분한다.

- 잘못된 조건: setup 미발견=구조 무효, 완성봉 회복과 VWAP 복귀의 중복 필수화, 평가돼도 NXT 후보를 만들 수 없는 고정 KRX 구현. 이번 보완 대상이다.
- 유지할 조건: exact source/master/cost/date/hash, 실제 invalidation, account/order/freshness/safety, 단일 owner, operator veto. 빈번한 소액 수익 목표라도 생략하면 안 된다.
- 초기 탐색: 기존 **누적10 arms/3종목**이며 같은 일별 floor를 재요구하지 않는다. 실거래 완료나 사전 양수 순이익을 추가 요구하지 않는다. 1주/일일3회는 탐색 제한이지 최종 운영 목표가 아니다.
- 확대/성숙 탐색: 기존 exposure10/3와 risk 검증에 더해 검증된 full-cost net EV 및 동일 source Control 대비 net decision 개선을 확인한다. 기존 proxy EV를 전체 비용 순수익으로 대체 표기하지 않는다. 코드를 고치는 acceptance에 이 경제성 floor를 요구하지 않는다.
- 남은 자동화 의존성: recheck 자동 policy의 별도 drought-history/scope 선택 때문에 후보가 있어도 OFF일 수 있다. 이 의존성은 이번 구현에서 강제로 제거하지 않았다. 현재 KRX 당일 override는 자동으로 영구 연장하지 않으며 NXT scope도 임의 추가하지 않았다.

## 남은 acceptance / 종료 조건

기존 daily `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910`가 새 v10 exact 비용 label/replay/후보를, `RuntimeEnvIntradayObserve0910`가 정책/PID 소비와 자연 결과를 소유한다. 새 Provider 결과 전에는 이전 v9 승인을 v10에 전용하지 않는다. 동일 자료의 반복 재생이나 재기동으로 없는 label을 만들지 않는다.

장전 `PREMARKET_KRX_LIKE` 통합 SOR 및 NXT 정규장 전용 cohort는 이번 애프터마켓 연결과 별도다. 현재 batch가 실제 생성하는 NXT 애프터마켓만 연결했으며 **NXT 전 시간대 해소는 미완료**다. 정확한 venue/session control·시장 경로와 기존 owner별 승인을 확보한 뒤 확장해야 한다.

재리뷰에서 feature 전달 위치 누락을 찾아 실제 `_extract_buy_recovery_probe_features`→micro consumer 통합 테스트로 수정했다. 관측창 종료 후 불필요한 feature 재계산, 미확인 parent 및 보유/미체결 cooldown 해제 가능성도 보완했다. 최종 검증 결과는 아래에 기록한다.

후속 consumer 리뷰에서 candidate lifecycle observer의 KRX V2.14 adapter 단일 allowlist와 restart 시 KRX adapter 고정 복구도 확인했다. 등록된 V2.14/V2.15·KRX/NXT adapter 및 exact session을 검증하고 event에 원 adapter를 보존하도록 연결했다. 과거 원천에 adapter가 없거나 서로 충돌하면 추측하지 않는다. 또한 장후 마지막 검증기의 NXT 누락/hash 오류 차단과 source-only blocker의 파일 status/진단 status 불일치를 보완했다.

`WAIT/probe arm`은 평가상 즉시 exposure가 아니다. 이번 변경도 arm을 실제 fill로 바꾸지 않으며 micro-only arm 증가만으로 성숙 exposure floor가 통과되지는 않는다. 새 micro 경로의 실제 빈도·순이익 및 확대 가능성은 exact 후단/체결 표본으로 별도 확인해야 한다. 따라서 자동화 연결의 코드 리뷰 통과를 전 시간대의 완전 자율 튜닝 또는 순이익 최적화 완료로 해석하지 않는다.

## 2차 사용자 재리뷰: 도달성 / 중복 경제성 조건

아래는 최초 검증 후 다시 요청된 리뷰의 보완이며, 위의 proxy EV 동시 필수 조건 설명보다 우선한다. 과거 PID·정책 적용 기록과 최초 테스트 결과는 소급 변경하지 않는다.

| 확인된 결함 | 수정 / 검증 경계 |
| --- | --- |
| 종목의 전일 재평가 count/parent가 다음 날 사전 검사에 남음 | KST 당일·parent·2회 한도를 사전 검사/실제 consumer가 동일 helper로 판정. 전일2회와 같은 parent라도 새 유효 날짜는 새 budget이며 과거 activation/date는 차단 |
| 재평가 결과가 바뀌어도 미확인 setup 관측권이 잔류 | numeric/early-accel 등 기존 재평가 공통 state writer도 최신 결과로 lease를 교체. DROP/timeout/untrusted는 관측권 해제 |
| async dispatch 전에 재평가 flag 소비 | discovery의 30초 lease를 dispatch→pending→commit까지 유지. completed/rejected/timeout-window에서는 해제, 일반 AI cooldown으로 결과 소비가 재차 막히는 경로 방지 |
| 전체 비용 후 개선이 있어도 gross/proxy EV 및 모든 하위 기회 개수의 동시 개선 요구 | bounded 후보/성숙 탐색은 검증된 full-cost 누적 EV>0·동일 pool Control 대비 net delta>0, 표본10/3, source/identity/tail-risk를 사용. 과거 gross/proxy와 패턴별 개수는 진단으로 보존. 비용 결손·음수 순EV·tail/source 실패는 계속 차단 |
| 후보 gate를 고쳐도 optimizer가 옛 proxy 기준으로 연구 후보를 버림 | 검증된 같은 prompt/contract/cohort의 net-positive 결과를 새 exact parent에서 계속 평가. 고정 당일 선택·Provider budget·PREOPEN 독립 권한은 불변 |
| V2.14/15/16 프롬프트와 optimizer 등록 hash 불일치 | 기존 registry parity test가 재현한 결함. 현재 검토된 본문의 canonical hash 3개 갱신. 옛 보고서/승인 artifact의 hash·버전은 변경하지 않음 |
| WAIT arm 경제성의 공백 및 summary flag 과신 | `probe_arm_full_cost_diagnostic`을 누적 보고서→candidate 진단에 연결. WAIT 10건도 비용후 가설 EV를 볼 수 있지만 exposure0/승격불가를 그대로 유지. micro numeric 반응·hash·source-only authority 검증 보강 |

새 적용 판정 계약은 `exact_cumulative_full_cost_net_ev_v1`이며 PREOPEN와 PID resolver 모두 계약 없는 후보를 거부한다. 이것은 기존 승인 artifact를 새 기준으로 자동 재해석하는 변경이 아니다. `MICRO_RECOVERY`는 여전히 WAIT 기반 1주 탐색 경로다. 다른 READY family의 경제성을 micro의 실체결 성과로 전용하거나 WAIT arm을 BUY/fill로 바꾸지 않았다. **micro-only 표본 누적 → 일반 수량 확대의 자동 승격은 이번에도 완성됐다고 주장하지 않는다.** 그 단계에는 동일 activation/parent의 실제 recheck→submit→terminal 및 비용 귀속을 소비하는 별도 승격 계약이 필요하다. 기존 자연 acceptance owner에 남긴다.

기대효과는 놓친 재평가의 실행/소비 복구, 작은 순이익 후보의 중복 문턱 제거, 변경 프롬프트 결과의 optimizer 소비 복구다. 회귀 fixture의 비용후 +0.03%는 최소 +1% 문턱 없이 통과할 수 있고, 비용/손실 반례는 실패한다. 실제 거래 빈도·원화 순이익 증가율을 측정한 값은 아니다. 현재 exit/수량/latency/broker owner는 변경하지 않았으므로 entry 개선만으로 빠른 익절·전체 누적수익 최적화를 보증하지 않는다.

09:43 읽기 전용 확인에서 main PID375167(08:45:53 시작)은 유지됐다. 설치 cron은 여전히21:05 paired batch/07:35 auto-bounded PREOPEN이다. 자동화된 것은 새 보고서·후보·다음 PREOPEN activation 경로이며, 현재 실행 중인 Python process에 새 source를 hot reload하는 기능은 아니다. 새 v10 정책·활성화와 recheck scope가 검증되기 전 재기동만 하면 V2.13 fallback 위험이 그대로다. 이번 재리뷰에서 운영 Provider 호출·리포트 재생·activation/env·서비스·주문·커밋/푸시는 실행하지 않았다.

2차 최종 검증: **16개 모듈 2,267 PASS / 67.76초**, compile·두 wrapper `bash -n`·변경 Python 경로 Ruff·`git diff --check` PASS. 최초 2,164 및 중간 1,314건은 합산하지 않는다. `ai_decision_quality`, `entry_setup_evidence`, `entry_setup_live_policy`, `entry_setup_paired_replay_batch`, `ai_engine_openai_transport`, `sniper_scale_in`, `threshold_cycle_preopen_apply`, `entry_recheck_policy`, `entry_opportunity_recheck`, `threshold_cycle_wrappers`, `entry_candidate_lifecycle_state`, `state_handler_fast_signatures`, `scanner_async_entry_bridge`, `scanner_async_eval`, `main_ai_prompt_optimizer`, `main_ai_prompt_consumer`의 해당 test module을 한 번에 실행했다.

print-only backlog parser exit0/count28이며 후속은 위의 기존 두 OPEN ID에 기록했다. Project/Calendar 동기화 없음. `korstockscan-review-gate`에 따라 직접 producer/consumer·registry·부정 반례를 재검토했고, 이번 수정 범위의 미해결 코드 finding0이다. 테스트를 넓히면서 발견한 registry hash 결함도 수정 후 같은 통합 실행에서 통과했다. 이는 미구현된 micro-only 확대 승격 계약, NXT 다른 세션, 현재 운영 배포 및 실제 비용후 수익 검증까지 완료했다는 뜻이 아니다.

## 최초 검증 (2차 재리뷰 이전)

- 12개 관련 test module 통합 **2,164 PASS / 59.87초**. 이전 중간 실행 횟수는 합산하지 않는다. setup/schema/AI adapter, runtime/PREOPEN, recheck/cooldown, actual feature producer, 순수익 비교, candidate lifecycle/restart, 최종 wrapper handoff를 포함한다.
- Python compile, 두 wrapper `bash -n`, `git diff --check`, 변경 경로 Ruff PASS. `ai_engine_openai.py`의 기존 E402/E722 26개 lint 항목은 이번 변경과 무관하여 제외한 검사이며 전체 파일 lint-clean이라고 주장하지 않는다.
- print-only backlog parser exit0/count28, 두 기존 후속 ID가 당일 checklist에서 각각1회 검출된다. 별도 병행 세션의 변경/체크 완료 이력은 보존했다. Project/Calendar 외부 동기화는 실행하지 않았다.
- `korstockscan-review-gate`의 producer→consumer/권한/부정 반례 리뷰를 적용했고 **위 수정 범위의 미해결 구현 finding0**으로 닫았다. Provider 실재실행, 새 산출물 자연 생성, 경제성 및 새 PID 반영은 미수용이다. 다른 매매기계의 병행 수정까지 리뷰했다고 주장하지 않는다.
- **배포 주의:** 새 v10 코드만 재기동하면 기존 v9 candidate/activation은 stale로 거부되어 configured V2.13으로 fallback할 수 있다. 새 exact replay·candidate·effective-date activation을 먼저 검증하고 허용된 적용 순서에서 재기동해야 한다. 기존 승인 artifact를 v10으로 덮어쓰거나 hash만 바꾸지 않는다. 이번에는 커밋/푸시·runtime env·activation·서비스·주문 변경 없음.
