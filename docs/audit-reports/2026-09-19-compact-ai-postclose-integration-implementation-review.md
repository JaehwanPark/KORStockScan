# 2026-09-19 Compact AI 장후 통합 구현 리뷰

승인: 사용자의 통합 계획 구현·반복 리뷰/보완·커밋푸시·immutable 배포·제한 장후 재생성 지시. source9/17은 보존하며 publication9/19의 명시 successor를 사용한다. 주문·bot restart·조기 PREOPEN·provider/수량/비용/표본/안전 guard 변경·cron 복원은 수행하지 않는다.

## 구현·리뷰·보완

- 기존 calibration에 prepare/evaluate/finalize/handoff 공통 조정을 추가했다. quality source materialization은 최초 Daily 앞에 유지하고 prepare는 유효 control/labels를 소비한다. evaluate만 후보 실행을 허용하고 provisional 결과를 생성한다.
- 기존 main의 독립 compact execute를 공통 evaluate로 대체했다. 필수 WS 입력 뒤·최초 EV/runtime summary 전에 기존 machine+compact publisher를 단일 finalize로 호출한다. late handoff는 요약/checklist 재결속만 수행하고 provider/publisher를 호출하지 않는다. 부분 compact CLI도 공통 finalize를 소비하며 단독 wrapper는 같은 단계 조정을 사용한다.
- common lock→paired-day→publisher 순서를 유지한다. finalize는 source generation이 바뀌면 raw를 재조회하거나 후보를 호출하지 않고 재평가 요구로 차단한다. final publisher 직전 paired·labels·의존 stat 지문을 대조한다. 다음 PREOPEN freeze는 기존 publisher가 보존한다.
- 공유 data 실체 경로를 정규화해 release 경로 변경만으로 sealed raw를 전수 재스캔하지 않게 했다. 후보 입력뿐 아니라 issued candidate prompt/schema request identity와 reviewed 비용 receipt를 캐시에 결속한다. 다른 프롬프트/스키마 응답 또는 바뀐 비용을 재사용해 승격하지 않는다.
- 리뷰에서 scope 후보의 프롬프트 계약과 날짜별 response schema 지문을 분리했다. 날짜가 바뀌었다는 이유로 정상 holdout을 차단하지 않으며 동결된 프롬프트 변경은 provider 호출 전에 차단한다. 일부 응답·self comparison을 경제성 비교 완료로 기록하지 않는다.
- 원 배포본에서도 실패한 기존 fixture의 source date/terminal gate/정확한 scanner identity를 명시했다. 실제 source guard를 완화하지 않았다. 양수 후보/기존 보존의 native publisher→consumer→summary→strict 회귀를 통합 진입점에서 확인했다.

새 module/collector/DB/report family/독립 publisher를 추가하지 않았다. 기존 v6 및 운영 seed/replay·lossless census·독립 모델 검증 producer 지원은 그대로 재사용했고 확인된 회귀로 검증했다.9/17의 원 stop/plan/identity 결손과 timeout은 비가역적/실패 입력으로 남기며 자연 model holdout이 없는 상태를 코드로 합성하지 않는다.

## 검증

- 정책·compact·calibration·optimizer·consumer·summary·strict 영향7개 suite:550 passed.
- entry split/strategy owner의 operating/model/source/coverage/census 관련 회귀:54 passed,179 deselected.
- 마지막 source binding·self comparison/coverage 보완 후 compact/calibration:241 passed.
- Python compile, 변경 wrapper `bash -n`, `git diff --check`, print-only parser 통과.
- print-only parser에서 기존 자연 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`는9/21 한 곳이다.9/18 표시 변경은 이관 완료이며 자연 성과 완료가 아니다.9/19 통합 implementation owner를 새 current checklist에 기록했다.

## 제한 재생성·배포

소스 커밋·푸시·immutable release·선택 CAS 및 source9/17/publication9/19/effective9/21 제한 재생성 결과는 `tmp/compact-ai-integration-20260919/`의 실행 영수증과 아래 최종 closure에 기록한다. 광역 main/다른 worker·서비스는 재실행하지 않는다. 보고서 상태/source gap과 scoped 검증, 전체 chain DONE, 정책 선택, PID·자연 비용 후 성과를 구분한다.

## 자연 수용 결손과 다음 owner

현재 frozen 실제 compact screen21건은 stop10·timeout/semantic9·venue/session identity2로 모두 제외다. 실제 비교·후보 호출0, 비용 후 EV 및 일별 순익 Δ는 null이다. 선행 실제 모델 검증도 source gap/holdout missing이다. 이는 measured no-edge 또는 개선0이 아니다.

다음 owner는9/21 체크리스트의 기존 stable ID다. 기존 Main pre-AI observer→atomic plan/stop→lossless execution census→독립 운영 replay→실제 scope별 선행 모델 proof→compact 학습/forward holdout→정규 PREOPEN/PID→joint applied-version completed-cost 성과를 확인한다. 다음 자연 입력이 없으면 계속 source/sample 상태로 남으며 과거자료 반복 재생성이나 generic stop·현재 가격·broker fill 합성으로 닫지 않는다. CI0–CI4 코드/인계 closure와 CI5 자연 EV closure를 혼동하지 않는다.


## 최종 closure

- Source commit `0e86f5d20909221904478a1aa2ec21ea72003c78`을 main 및 review branch에 atomic push하고 관리 root `compact-ai-integrated-reviewed-20260919`를 selector CAS로 선택했다. root/HEAD·src/deploy clean·공유 data/docs/tmp/logs/.venv/restart.flag를 확인했다. router print-plan으로 future main 호출 경로를 확인했으며 bot/service/cron은 재시작·복원하지 않았다.
- prepare/evaluate는 각각1초 이내였고 기존 sealed source projection을 재사용했다. finalize는 candidate/model admission을 재확인하고 publication9/19→effective9/21 정책을 생성했다. late handoff는 재발행 없이 최종 summary/checklist를 결속했다. 독립 strict 명령 `--compact-summary-only --require-summary-handoff`는 exit0/PASS, issues[]다. whole_native_chain_done_claimed=false다.
- Bundle `833053c38872f05269cf1d0fd24c2d777d3133eb2f2a07163fa304633344f07b`; paired `99699f197de1f530d8f77d5363e95a31bebb6dfbc2196aa53c03e11b4b90be4e`. Calibration·optimizer·consumer19·정책21이 같은 proof를 소비한다. 기존 bundle015d의 machine 정책 및9개 scope의 machine/AI 전체를 비교해 unchanged를 확인했다. 보호 원 trace/payload의 inode/size/mtime도 unchanged다.
- 실제 결과는 screen21/excluded21/comparable0/provider0, 비용 후 EV·일별 순익 Δ null이다. economic_comparison_complete=false, candidate_improvement_proven=false, incumbent_preserved다. 선행 실제 모델 proof source_gap/holdout missing과9/17 irrecoverable stop/plan/identity·timeout은 기존 자연 owner의 OPEN acceptance다. 복구 불가능한 자료를 추가 재실행하지 않는다.
- 실제 PID 소비와 자연 적용·실현 순익 개선은 확인되지 않았다. scoped family PASS는 원 native chain의 외부 resource/다른 family·PREOPEN 결손을 해소하거나 DONE으로 덮지 않는다.
- 영수증: [validation](../../tmp/compact-ai-integration-20260919/validation.json), [regeneration](../../tmp/compact-ai-integration-20260919/regeneration.json), [deployment](../../tmp/compact-ai-integration-20260919/deployment.json), [strict](../../tmp/compact-ai-integration-20260919/strict.txt). 자연 owner는 다음9/21 체크리스트의 동일 stable ID 한 곳으로 parser 확인한다.

- Concurrent successor: 완료 기록 push 도중 다른 승인 세션이 `fcfd7b8e5` / `limit-down-retirement-reviewed-20260919-fcfd7b8e5`를 선택했다. source `0e86f5d20`의 descendant이며 compact 구현 3개 모듈과 paired wrapper는 동일하고 main wrapper 변경은 limit-down 폐기뿐이다. prepare/evaluate/finalize/handoff 호출을 실제 successor root에서 확인했다. 최신 선택을 되돌리지 않으며 미래 호출에 통합 구현이 포함됨을 확인했다. 실제 PID·자연 EV 수용 미완료는 동일하다.
