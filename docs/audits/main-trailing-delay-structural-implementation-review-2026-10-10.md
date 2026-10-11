# 트레일링·제출 지연 정책 생성 구조 — 구현·반복 리뷰

대상: [P1–P5 구조 보완계획](../proposals/main-trailing-delay-policy-generation-structural-remediation-plan-2026-10-10.md). **검토 범위의 코드 결함을 수정하고 영향 시험을 통과했으며, 후속 승인으로 운영 장후 재생성·정식 발행·배포·10/12 준비를 완료했다. Main 자연 기동·새 경제 성과는 미관측이다.** 최초 수량·손절 퇴역·의미적 감시기 계획과 다른 미커밋 문서는 변경하지 않았다.

## 구현과 소비 경로

| 단계 | 구현 | 실제 소비·거절 검사 |
| --- | --- | --- |
| P1 | 실제 entry 요청의 prompt/model/options/schema/projector/normalizer identity, compose의 effective PASS, 원 기계 부모 전달 | Main provenance → 두 anchor → 문자열 로그 projection → 초기/분할 지연 정책 → Prepared lookup. 60/240건 + 결손 한 건, 누락 부모는 승격하지 않음 |
| P2 | 기존 request/prompt/payload 원문 참조, native BUY 세대/PID coverage, pre-signal 투표 재생, 16MiB segment rollover | 실제 evidence writer → ledger/완료 adapter → 공통 replay. 원문 변경·ledger 결손·미관측 coverage는 검열, 관측된 INSUFFICIENT는 기존 runtime 의미 유지 |
| P3 | 원 pin과 연구 assignment 분리, 의미/학습 generation hash 분리 | 60/240건의 AI-required 집계에서 과거 pin에 미래 frozen hash를 요구하지 않음. resident/분할 train generation 일치, 기존 pin bytes 유지 |
| P4 | 기본 적격 전역 split + 후보–부모별 pair, raw census/eligible evaluation 분리, 대용량 typed bridge | 미지원 B가 정상 A의 split/metric을 지우지 않음. 기존 selector에 후보 전달, 독립 verifier가 minimal checkpoint의 집계/분류를 재계산 |
| P5 | 일반 악화 진단과 기존 손실 악화 guard 분리, horizon별 pair 선정 | +10→+9는 일반 악화, 후보 순손익 -1의 악화는 기존 guard. 30초 241건/+10bp와 180초 240건/+40bp에서 긴 후보도 비교, holdout 재선정 없음 |

새 source adapter의 소유 위치는 [src/engine/ai/holding_vote_replay_source.py](../../src/engine/ai/holding_vote_replay_source.py)다. 실제 AI 원천의 참조·동등성 검증을 담당하고 provider 실행 권한은 없다. 기존 automation/scalping/lifecycle 역할을 유지하며 engine root에 새 모듈을 만들지 않았다. 새 회귀는 [test_trailing_delay_structural_generability.py](../../src/tests/test_trailing_delay_structural_generability.py)에 있다.

## 리뷰에서 추가로 찾고 수정한 결함

1. 분할·JSON 재개 후 horizon 통계의 정수 key가 문자열로 변해 정책 해시가 불일치했다. 저장 key를 고정하고 구 알고리즘·구 projection 계약은 역사적 의미로 검증한다.
2. 실제 logger의 문자열 변환과 비동기 carrier의 중첩 Mapping 고정을 처리했다. identity는 canonical JSON, 새 anchor는 버전 3으로 전달한다. 기존 버전 2 의미를 바꾸지 않았다.
3. holding worker가 frozen stock에만 coverage를 기록하는 결함을 수정했다. lock 안에서 현재 position/native BUY generation을 다시 대조하고 source receipt만 live stock에 넘긴다.
4. native BUY identity leg에는 시각이 없었다. accepted BUY/ADD consumer의 position clock을 사용하고, 재기동된 과거 보유의 coverage를 과거로 합성하지 않는다. 문자열 store failure도 coverage 결손으로 처리한다.
5. 192개 tail과 전체 연구 ledger를 분리했다. stable lock·immutable segment·fsync로 rollover하고 signal window 전체 투표를 shared memory admission 후 읽는다. 늦게 persisted된 투표는 crossing에 사용하지 않는다.
6. 동일 plain/gzip 복제본의 내용이 같으면 하나의 요청으로 인덱싱한다. 내용이 다른 alias, stale index와 변경된 원문은 계속 거절한다.
7. hash가 재봉인된 잘못된 집계도 거절하도록 독립 verifier에서 완전한 minimal checkpoint의 split·pair metric·typed 연구를 재계산한다. 원문 AI/quote 원장을 복제하지 않는다.
8. `classifier_generation_sha256`를 고정 train의 원 context/outcome/점수와 frozen classifier에 결속했다. holdout 자료를 학습 세대로 포함하지 않는다.

## 검증 결과와 한계

- 통합 영향 시험: **606 passed / 135.38초**. entry·AI transport·관측·지연·holding vote·전수/분할 연구·assembler·독립 verifier·기존 selector·모듈 위치를 검사했다. [로그](../../tmp/trailing-delay-structural-implementation-20261010/final-integration-tests.log).
- alias/normalizer identity 보완 후: **215 passed / 124.51초**. [재리뷰 로그](../../tmp/trailing-delay-structural-implementation-20261010/final-rereview-tests.log).
- 최종 train generation 보완 후: **71 passed / 26.80초**. [최종 영향 로그](../../tmp/trailing-delay-structural-implementation-20261010/final-generation-tests.log). 세 실행은 서로 겹치는 시험이며 합산 표본으로 해석하지 않는다.
- 변경 Python 25개 compile·`git diff --check` PASS, 4문서 로컬 링크 81개 결손 0. print-only parser OPEN 25개이며 두 구현 owner와 10/12 자연 PREOPEN owner가 각각 한 개다. source/deploy 1,107개 중 이번 변경 23개만 달라졌고 Rebase·봉인 checklist·선택 릴리스 파일의 hash 불변을 확인했다. [최종 검증](../../tmp/trailing-delay-structural-implementation-20261010/final-validation.json). 외부 Project/Calendar sync는 실행하지 않았다.

외부 provider/계좌/주문 경계는 동결하고 내부 producer/normalizer/검증/선정 함수를 실행했다. 경제 수치와 60/240건은 synthetic 조건 시험이다. 개별 selector unit의 원천 verifier 격리는 별도 genuine verifier의 성공·위조 거절 시험으로 보완했다. 실제 누적 수익·새 정책 채택·자연 청산 증거로 사용하지 않는다.

[동일 성공 작업 성능 측정](../../tmp/trailing-delay-structural-implementation-20261010/performance.json)은 240 train/60 holdout·4 horizon, 240행/2후보, 31 quote/4후보를 3회 대조했다. 논리 결과 동일, 원 AI 호출 0, 외부 집계 증거 7,863 bytes다. 기존 0건 검열 시간을 기준으로 사용하지 않았다. 작은 입력의 외부 집계는 디스크 index 비용 때문에 resident보다 느리므로 전체 속도 향상으로 보고하지 않는다. 이 측정은 제한된 성공 경로의 비용 확인이며 장중 tail·burst/slow writer·전체 장후 성능 수용을 대체하지 않는다. 추가 거대 비교 원장은 만들지 않았다.

## 코드 검증 종료 당시의 운영 상태 (후속 실행 전 기록)

선택 릴리스는 작업 시작 때의 `main-trailing-delay-residual-20261010-v6`이며 이번 source 수리는 작업트리에 있다. 10/12 봉인 checklist·Plan Rebase·선택 릴리스 파일을 보존했다. 기존 v6 발행/PREOPEN PASS는 그 릴리스의 역사적 증거이며 이번 코드의 설치/소비 증거가 아니다.

`MainAllScopeTrailingReplay`와 `PreSubmitDelaySituationImplementation1010`는 동일 stable ID로 OPEN을 유지한다. 정상 자료의 자연 수집, 실제 적격 표본/성과, 전체 성능, 정식 successor 발행/strict/finalization/PREOPEN과 현재 PID 소비는 후속 확인이다. 불복구 과거 행은 제외하고 성과가 없는 후보는 부모/0초를 유지한다. 코드 수리로 양수 정책·수익을 보장하지 않는다. EOD·기계/보조 원본·운영 committed pointer는 변경하지 않았다.

## 후속 승인에 따른 운영 재생성·배포

사용자의 `운영장후 재생성 및 배포승인`에 따라 source **2026-10-08**, publication **2026-10-10**, effective **2026-10-12**로 고정했다. 최초 수량·손절·의미적 감시기 작업은 포함하지 않았다. 검증된 Python 25개 bytes가 불변 릴리스와 일치하며, 별도 Git index/commit-tree로 기존 HEAD와 다른 작업 문서를 보존했다.

- 릴리스: `main-trailing-delay-structural-20261010-v1` / `c66488df8d428ecda57ee3c052c630c3e68f74b2`. [빌드·포함/제외 목록](../../tmp/trailing-delay-structural-deployment-20261010/residual-release-build.json). 새 릴리스의 영향 계약 시험 **114 passed / 12.58초**. [로그](../../tmp/trailing-delay-structural-deployment-20261010/release-closure-tests.log). 처음 시험 경로 지정에 없던 파일을 넣은 실행은 시험 0건으로 종료했고, 실제 존재하는 suite로 교정한 결과만 수용했다.
- 실제 누적 source 재생성과 독립 verifier를 실행했다. scope 20,832, 조사 population 7, 적격 경제 비교 0으로 **12 cell 모두 부모 계승**이다. [실제 누적 원천 결과](../../tmp/trailing-delay-structural-deployment-20261010/actual-source-research.json). 과거 결손은 excluded/censored로 남기고 새 AI 투표·fill·수익을 합성하지 않았다.
- 지연 native stage는 `qualified_anchor_candidate_paired_chronological_split_v3` / `pre_submit_delay_sharded_evidence_v3`로 발행했다. commit 31, qualified PASS 29, P0 6, 가격쌍 21, 부모 미검증 29, native 미검증 5로 **default 0초**를 유지한다. exact-date 가족 원장은 `valid_empty`, matched 0이며 이 수치와 누적 가격 비교 수치를 혼합하지 않는다. [가족 원장 결과](../../tmp/trailing-delay-structural-deployment-20261010/prepared-delay-ledger-result.json), [native 지연 terminal](../../tmp/trailing-delay-structural-deployment-20261010/formal-pre_submit_delay.json).
- 정상 원천/형식으로 후보가 생성되는 지원 조건 회귀는 앞선 코드 검증에 있고, 이번 과거 누적 자료는 새 양수 후보의 실제 선정 근거가 아니다. 앞으로 P1/P2의 새 producer가 수집하는 원 부모/요청/coverage가 필요한 자료를 누적해야 한다.
- 같은 source의 EOD와 원 Main 기계·보조 정책은 원 bytes를 보존했다. 해당 독립 stage는 기존 managed immutable release의 code/output/input/prerequisite를 검증해 재사용했고 새 계산·AI 호출을 주장하지 않았다. 원 봉인 10/12 checklist는 transition의 `before_snapshot`으로 보존하고 native summary의 정식 successor만 갱신했다.
- 가족 원장·holding snapshot·trailing/지연 정책·release selection·summary/checklist/strict/controller·PREOPEN을 하나의 CAS 복구 세트로 발행했다. [transition](../../data/runtime/research_release_transition/trailing_delay_structural_20261010_v1/transition.json)은 `verified`, 41개 metadata entry다. 실제 source 재생성은 publishing lock 진입 전에 수행했으며 broker/provider/AI 호출 0, 주문/취소 0이다.
- 운영 finalization wrapper가 실제 controller→strict→정리→PREOPEN→최종 detector를 수행하고 **2026-10-10 23:33:47 KST DONE**을 남겼다. 최신 chain `a7fd245536f4e6f40ce3462ee2af2808ae8378e14c73f77ff2a1f07aac5c826b`와 snapshot을 재검증해 issues `[]`, PREOPEN **current_full_contract=pass**다. [최종 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-structural-readiness.json). 설치 cron 8경로와 selected release-set 검증 PASS.
- 웹 PID `227302` / ubuntu / 새 release cwd·commit / HTTP 200을 확인했다. [웹 소비 증빙](../../tmp/trailing-delay-structural-deployment-20261010/web-consumption.json). Main은 계속 중지 상태이며, 10/12 **07:35 PREOPEN·07:55 자연 기동**은 future_due다. bootstrap 준비가 실제 PID의 소비나 자연 주문/청산 성과를 뜻하지 않는다.
- 최종 detector는 `fail` 0이며 기존 20:50 회차와 같은 warning을 기록했다: 지연 재생성의 workorder 시간창, KOSPI `completed_with_warnings`, 과거 auth 8005의 dry-run 경고, 과거 log 분리. detector가 finalization 조상 안에서 실행되는 동안의 `pending_self_audit`도 PASS로 합성하지 않았다. 종료 후 native DONE/current generation 검증으로 최종화 수용을 확인한다. 이 독립 warning을 숨기거나 restart.flag를 생성하지 않았다.

실자료 cold 111.25초/CPU 72.11초, warm 31.17초/CPU 22.89초, Python RSS 최대 165,196KiB(+parent 3,088KiB)로 선언된 예산 이내다. cold는 가족 원장 봉인과 동시 실행했으므로 이전 단독 81.81초 대비 같은 조건의 성능 회귀/향상으로 해석하지 않는다. warm과 기존 단독 31.26초도 한 회차의 관측이며 통계적 개선을 주장하지 않는다. 전체 장중 tail/burst·자연 청산 성능은 아직 미측정이다. 새 대형 AI 비교 원장을 복제하지 않았고 이 작업의 task evidence는 약 1.3MiB다.

두 구현 stable ID는 이번 코드 수리·승인된 정식 인계 범위로 완료한다. 자연 PID 소비는 10/12 기존 `DirectFamilyPreopenPolicyHandoff`에서 확인한다. 실제 새 원천/후보 성과와 전체 운영 성능은 아직 미측정인 별도 수용이며, 07:35~08:05 장전 owner의 완료만으로 수용했다고 보고하지 않는다. 최초 수량·손절·의미적 감시기 계획의 OPEN을 대신 닫지 않는다.
