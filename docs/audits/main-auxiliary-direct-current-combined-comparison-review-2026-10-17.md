# 실제 현행 대 보조 입력·문구 최종 조합 직접 비교 — 2026-10-17

사용자의 추가 승인·진행 지시에 따라 호출 상한을47회 늘려 누적2,047회로 연결하고 직접50쌍 비교를 완료했다. 전체 PASS 승률은20/30승(66.67%)→32/44승(72.73%), PRE는17/23승(73.91%)→29/35승(82.86%)이다. 실행 owner는 [오늘 체크리스트](../checklists/2026-10-17-stage2-todo-checklist.md)의 `AuxiliaryDirectCurrentCombined1017`이다. 코드리뷰·수리와 원응답100건의 격리 운영 연결 검증을 완료했다. 정책 발행·선택 변경·배포·재기동은 실행하지 않았으며 배포 지시 대기 상태다.

## 1. 비교와 원천 고정

[직전 후속 연구](main-auxiliary-runtime-input-and-failure-screen-followup-review-2026-10-17.md)는 RVP 입력을 양쪽에 고정하고 문구만 비교했다. 이번에는 같은 동결50점에서 실제 incumbent의 원 입력·실제 prompt와 RVP+동결 suffix의 최종 조합을 직접 비교한다. 앞선 두 연구의 개선 폭을 더해 최종 효과로 제시하지 않는다.

새 표본·문구·위험 조건을 선정하지 않았다.50점은 PRE40/AFTER10, 기존25/확장25로 직전과 동일하다. 사전에 준비한 채택 검토 범위는 두산034020 PRE/2만~10만원/NXT와 알테오젠196170 PRE/10만원 이상/NXT의2경로다. 나머지 경로도 직접 결과를 모두 공개하되 결과를 보고 유리한 새로운 조합으로 분모를 재구성하지 않는다. 표본과 결과가 과거 연구에서 관찰됐음을 명시하고 신규 독립 holdout으로 부르지 않는다.

확인 ask·비용0.0023 한 번·1,800초·net+0.4%·net soft−3% 선도달 없음의 원 라벨을 유지한다. WIN/FAIL_STOP/FAIL_TIMEOUT만 비교하고 미확정·결손을 실패나0으로 바꾸지 않는다. 공통 유효 집합의 PASS 승률 우선, 동률이면 TP이며 EV·최소 표본·승리 보존율 문턱을 추가하지 않는다.

호출 전 protocol SHA는 `34a65c5455b237984412ded1c598c0887f77c702a2980a2c128d7e864926a4ca`다. 원 snapshot·current registry·raw 현행 요청 hash와 후보 request ID·요청 hash·result object·원 record hash·provider response ID를50점 모두 동결했다. 후보는 같은 정확 요청이므로 기존50개 응답을 재사용하고, 기존 원장에 없던 raw 현행50개만 실제 호출한다. 원응답을 새 identity에 복사하거나 native 권한으로 다시 표시하지 않는다.

근거: [직접 비교 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/protocol.json), [호출 전 예산 경계](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/budget-boundary.json).

## 2. 승인·예산·사전 코드리뷰

기존1,997회 사용·과거 미발송 실패18개·전체 승인 chain·동일 budget key를 보존했다. 상한2,000→2,047회로 추가47회를 연결해 실제 남은50회를 사용한다. 새 승인 SHA는 `65eb2b52dc2127f16b0444ee8f8bbde4b5444cc7905fc5c031e2d4c3d2c8b45d`다. 연구 한도 확장은 정기 장후·장중 운영 호출 한도나 provider/모델을 변경하지 않는다.

funding 코드·선행 누락/변조·idempotence·마지막 한도 이후 미호출·기존 차감 보존을 검증했다. 신규17개·기존 next-study16개33PASS와 독립 funding 전체83PASS는 중복을 합산하지 않는다. 실제 funding 작성 전에 source review를 닫았으며 compile/diff 검사도 통과했다.

사전 driver 리뷰에서 이전 protocol/campaign/results/analysis/population 연결 guard를 보강했다. 독립 분석의 최초 예산 경계가 승인 파일mtime에 의존하던 결함도 provider 호출 전에 수정했다. 원 protocol/driver를 덮지 않고 별도 immutable sidecar에 기존1,997개 attempt ID 목록·digest·보조 시각·protocol/funding hash를 봉인했다. 종료 대사는 이전 ID 전체 보존과 새 ID 차집합으로 수행하며 파일 copy/touch에 의존하지 않는다. sidecar SHA는 `0836acd119f74adf213c8fc89debb6b79bcb0952b12c62bfdd6e08e78f60c522`다.

## 3. 실제 결과·채택 판단·운영 증빙 연결

50쌍 모두 공통 유효하게 종료했다. 현행과 최종 조합을 **이번 같은50점에서 직접** 비교했으며 앞선 상대 비교의 점수를 합산하지 않았다.

| 범위 | 확인점 | 실제 raw 현행 | RVP+동결 suffix | TP/FP 변화 |
|---|---:|---:|---:|---|
| 전체 | 50 | 20/30승 = 66.67% | 32/44승 = 72.73% | TP+12·FP+2 |
| 비삼성 PRE | 40 | 17/23승 = 73.91% | 29/35승 = 82.86% | TP+12·FP불변 |
| 비삼성 AFTER | 10 | 3/7승 = 42.86% | 3/9승 = 33.33% | TP불변·FP+2 |

전체 confusion은 현행TP20/FP10/FN18/TN2, 후보TP32/FP12/FN6/TN0이다. 승리14점 PASS를 회복하고2점을 잃었다. TIMEOUT2점을 추가 PASS했으며, 후보는 전체 실패12점(STOP3·TIMEOUT9)을 모두 PASS했다. PRE 실패6점 역시 양쪽 모두 PASS다. 이번 개선은 승리 오차단 감소이며 실패 차단 개선으로 표현하지 않는다. 기계 단독38/50승(76%)·PRE34/40승(85%)은 진단으로 유지하고 추가 채택 문턱·자동 보조 우회 권한으로 사용하지 않는다.

| 사전 지정 채택 검토 범위 | 확인점 | 현행 | 최종 조합 | 판단 |
|---|---:|---:|---:|---|
| 두산034020 PRE/2만~10만원/NXT | 10 | 3/3승 | 8/8승 | 승률100% 동률·TP+5, 채택 후보 확정 |
| 알테오젠196170 PRE/10만원 이상/NXT | 10 | 1/1승 | 7/7승 | 승률100% 동률·TP+6, 채택 후보 확정 |

두 경로20점은 모두WIN이며2개5분 원천 구간·6개 승리 목표 시각에 집중됐다. 정확 native/input/요청 identity가 고유하다는 사실과 독립 사건 수를 구분한다. 전체50점은26개5분 구간·23개 승리 목표 시각·3개 STOP 시각이다. 새 독립 미래 holdout이나 누적 모집단 전체 효과로 일반화하지 않는다. 이 한계 공개는 별도 최소 표본 채택 문턱을 추가하는 것이 아니다.

기타 비상시 PRE/2만원 미만/SOR도5/6승→6/7승으로 개선됐지만 사전에 고정한 준비 후보2경로와 분리해 진단으로 남긴다. AFTER·REGULAR·삼성과 기존 PRE의 나머지 경로를 이번 조합으로 일괄 전환하지 않는다. [채택 판단 보고서](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/adoption-report.json)는2경로만 포함한다. 이는 정책 발행 완료 표시가 아니다.

독립 대사는 기존1,997개 예산 attempt ID 보존, 차집합50개가 모두 현행 역할, 기존 후보50개 request ID/전체 요청 hash/result object/원 record hash/provider ID 불변, 후보 재전송0을 검증했다. 누적2,047/2,047회·미확정0이며 기존 실패18개도 보존했다. 새 현행50응답의 지연 중앙1,098ms·p95 1,864ms·토큰 합계106,341개다. 후보 재사용을 포함한 고유 참조455개 object의 압축 구간939,990B·논리2,430,118B를 대사했으며 공유 pack 전체18,609,281B를 배타적 신규 증가량으로 세지 않는다.

결과: [직접 비교 독립 분석](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/independent-analysis.json), SHA `305d6638535a4b0885107f971ed7383c8cd984dd8f5b3b25062e41d684262a12`. source·라벨·요청·응답·원본 hash·cached/new 귀속·모델·비용·시간·scope별 분모를 독립 재리뷰했고 검토 범위의 분석 결함은 없다.

## 4. 운영 증빙 연결과 배포 준비

기존 publisher는 offline 입력 변환의 실제 응답을 별도 production registry로 연결하는 일반 계약이 없었다. 요청 메타데이터를 바꾸거나 원응답을 새 request ID로 import하거나 native flag를 덧붙이는 방식은 사용하지 않는다. 원 요청·원 provider receipt·raw response·정답을 유지하면서 모델에 실제 전달된 payload와 production 입력/스키마/문구/옵션·decode의 정확한 동등성을 검증하는 별도 transition을 구현하고 리뷰에서 발견한 결함을 수정했다.


코드 owner는 기존 scalping 정책·장후·보조판정 패키지에 있는 `reversal_auxiliary_input_transition.py`다. 새 engine-root 모듈이나 별도 live publisher를 만들지 않았다. `reversal_auxiliary_transition.prepare/validate_manifest`가 새 연구 보고서 schema만 분기하며 기존 compact 전환은 유지한다. 새 준비 작업은 원 shared ledger를 readonly로 열고, 원 evaluator의 함수 본문에 요청 단위 Store/write adapter를 제공해 결과를 재계산한다. 원 evaluator 전역을 patch하거나 원 연구 결과 파일을 덮지 않는다. 승인 chain·source scope·source partition/ordinal·native snapshot·승패 라벨·원 request ID·response object·실제 provider raw bytes를 이어서 검증한다.

운영 registry 정의는 manifest에만 넣고 실제 등록은 하지 않는다. 나중의 발행은 기존 보조 publisher의 명시 authority, Main/보조 두 lock, 정확 부모·대상일·현행128binding CAS 이후에만 정의를 등록하고 overlay를 발행한다. BLOCK/RECHECK를 ENTER로 바꾸거나 기계 manifest·수량·주문·원 신호5초·provider·hard safety를 수정하는 경로는 없다. 결과 비교는 이번 raw현행 대 combined50점이며 이전 두 상대 비교를 합산하지 않는다.

리뷰에서 source chain의 불완전 연결, descriptor가 seal 전 본문으로 저장되는 원 ledger 형식, 원 라벨과 분석을 함께 재봉인하는 변조, 역사 원천·호환성 receipt·frozen reader·symlink 경로의 cache 의존성 누락을 보완했다. 읽지 않는 `previous_overlay` 연혁 전체를 새 필수 조건으로 만들지는 않는다. 최신 분석/채택 보고서 alias가 정당하게 갱신돼도 과거 준비 근거가 변하지 않도록 immutable history를 참조하고 기존 원 JSON bytes도 별도로 보존했다. 최종 채택 보고서 content SHA는 `2e9acf1b248bf1e97941fd5c2dba16cc28e5d2e4de87f0d3a91d24854a535a90`다.

장중 검증마다50점을 다시 평가하던 성능 결함도 수정했다. 파일·코드·원 pack이 같으면 검증 cache를 사용한다. 공용 SQLite/WAL만 달라지면 선택한100request,4campaign descriptor/owner와 실제 읽은 object metadata의 fingerprint를 readonly transaction에서 대조한다. 무관한 INSERT는 full replay나 판정 차단을 유발하지 않는다. transaction 중 global DB가 바뀌면 새 signature에 과거 snapshot을 귀속하지 않고 다음 판정에서 다시 짧게 대조한다. 선택 증빙이 달라지면 차단하며 발행 lock 안에서는 cache 변경 시 무거운 재계산 없이 준비를 다시 요구한다. 최종 실제100request·512object·4campaign 대조는5회1.86~2.56ms였다. 이는 메타데이터 대조 시간이며 전체 장중 판정 지연이 아니다.

미래의 무관한 예산 사용이나 증액 때문에 cold 재검증 결과가 달라지지 않도록, manifest에는 안정적인 semantic evaluation SHA와 원 frozen resolution SHA를 넣고 현재 used-budget/native metadata에서 파생한 임시 resolution SHA를 넣지 않는다. 원 historical resolution bytes와 기존 차감은 그대로 보존한다. 실제 SQLite 임시 Store로 무관 INSERT, 선택 request/owner/object 변조·누락, 동시 WAL commit/read snapshot을 확인했고 신규31개·기존 compact transition15개 **46PASS**, Python compile/diff 검사를 통과했다. funding83PASS와 겹치는 검증은 합산하지 않는다.


첫 실제50점 통합 준비에서 단위 검증으로 놓친 cold/warm 차이를 발견했다. 최초 commit `ecdede14380732f02c2ab58d0e7c114d1bb4a6b3`의 manifest `ce83b1c8d58bd574045ebe5bdb67bc1cfc0d67c7de7b36a7532b7269d5b7cc1a`는 cold 재생성과 같았지만, warm 재생성에서 canonical inherited registry `f2e63db…`의 원 parent `239f253c388d0b76a545ae502473cd3d7bd833cd70c82c687f78e5878137195a` 한 개가 read closure에서 빠져 재검증에 실패했다. 현재 overlay가 해당 binding을 덮어써 inherited cache-hit 때 nested parent를 다시 읽지 않았기 때문이다. source·승패·50쌍의 판정 결과 차이는 없었다. 실패 manifest·고유 started/terminal 영수증·cold/warm 진단 파일을 보존했고 원본과 v2 reader receipt를 수정하지 않았다. canonical source의 실제 registry parent closure를 항상 명시 검증하도록 수리하고 재현 회귀를 추가했다. 최종 `108c75f91d3f8567707319454914130972412260`에서 신규32개·기존15개 **47PASS**, compile/diff 검사를 통과했다. 실제 registry·policy·선택·provider·봇 변경은 없었다.


## 5. 최종 실제 준비 검증과 남은 배포 경계

최종 격리 source HEAD는 `108c75f91d3f8567707319454914130972412260`이며 선행 `ecdede143`·`ee0af6b48`의 운영 입력/registry/SDK 연결을 포함한다. 선택 릴리스 `a41ebc84f`의 후손 작업본이며 선택 릴리스에는 새 production-input 계약이 아직 없다. 후속 배포는 마지막29줄 수정만 이식하는 것이 아니라 이 선행 구현과 현재 선택본의 전체 차이를 함께 통합·검증해야 한다. 추적 파일은 clean이며 기존 `.venv`·`logs`·`tmp` symlink는 커밋하지 않았다.

보완 중 관련7개 파일 통합 **248PASS**와 마지막 source 보완의 **47PASS**는 중복을 합산하지 않는다. 통합 검증 도중 뒤의 좁은 J cache 수리가 있었으므로, 최종 J/X는 별도47PASS와 아래 실제 재검증으로 닫았다. funding83PASS 역시 중복 분모다. 별도 source/응답/분석/adapter 코드리뷰를 수행했으며 검토 범위의 미해결 결함은 없다.

[기존 reader의 격리 호환성 결과](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/reader-handoff-isolation-v2/result.json)는 정확 부모 `8809c82e…`·10/16 as-of에서 old/new **128binding**, registry23개, 격리 compatibility receipt2개를 확인했다. result content SHA는 `57bf2d3ae949ecdfd87db617b003b0b52f49915e966992ceb3291ac370e1ee53`다. 원 native27경로 hash와 A.verify_bound_sources를 검증했으며 실제 DATA의 compatibility receipt는 생성하지 않았다. 마지막 수리는 J만 바꾸고 기존 reader의5개 hash는 유지했으므로 이 원 v2 영수증을 다시 발행하거나 수정하지 않고 재검증했다.

[최종 native 준비 결과](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/native-preparation-result.json)의 content SHA는 `4c72896000dcde1cfe0b8f5e6632d72a047b7d3583b3872c358af9cfb27db084`, manifest는 `fcf1ab63f5a1569c6469d3886669e772b483c857d5a25d99d7e53385992e1e07`다. 실제50쌍·원 provider 응답100건을 readonly로 재검증했고 사전2개 PRE/NXT scope만 changes에 담았다. 기존128binding과 rollback2개를 그대로 연결했으며 원 registry와 상속 정의를 포함한6개 정의는332,814B manifest에만 내장했다. 원장/원응답 DB 복제는 없고 source70개와 원래 symlink 관측 경로37개를 검증한다.

격리 prepare3.888초, transition 검증 cache만 비운 재검증2.770초, 전체 재생성을 금지한 warm20회 약9.95~10.15ms·중앙약10ms였다. 이미 prepare가 reader/hash/OS cache를 데운 뒤의 transition-cache cold 측정이며 전체 봇 cold 기동 시간으로 부르지 않는다. [별도 새 Python 프로세스의 독립 재검증](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/independent-native-validation.json)에서도 cold3.817초와 full replay 금지 warm약9.92ms·cached_only 검증이 통과했다. provider 호출0회이며 누적 연구 차감은2,047/2,047회 그대로다. 시작/종료 실제 source173개 hash와 실제/격리 registry 목록이 같고 current overlay도8185…로 유지됐다. 첫 실패와 최종 성공의 고유 attempt 영수증을 각각 보존했다.

이 준비의 `bundle_target_date`와 `operating_day`는 모두 **2026-10-16**이다. 다음 영업일 **2026-10-19 PREOPEN·정확 정책/코드 handoff·PID 소비를 입증한 것은 아니다.** 선택a41의 원current8809를 standalone loader에서 target16/19로 읽은 시도는 `v4_contract_code_changed:continuous_reversal_policy_v3.py`로 unavailable이었으며 [별도 실패 원문](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/direct-current-combined-20261017/selected-release-native-incumbent-check.json)을 보존했다. 이 원current 부모용 a41 code-handoff receipt도 없음을 확인했다. 이는 정확 배포/부트스트랩 문맥 밖의 historical bundle 직접 읽기 결과이며 기존 선택본의 별도 next-session 준비/PID 장애로 단정하지 않는다.

배포 지시를 받으면 그때의 selector·부모·대상일·코드를 다시 고정하고 runtime release routing의 clean candidate/active-policy/native code handoff와 정확 PREOPEN을 먼저 검증한다. 부모나 binding이 달라지면 이번 historical manifest를 그대로 발행하지 않는다. 원 연구/라벨/응답을 보존한 채 변경 문맥의 요청 동등성·근거를 다시 준비하고 기존 publisher의 authority·두 lock·CAS로 이어야 한다. 실제 정책 발행·registry 등록·선택 변경·배포·재기동·PID 소비·주문·경제 성과는 이번 완료에 포함하지 않는다.
