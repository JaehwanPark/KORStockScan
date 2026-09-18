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
