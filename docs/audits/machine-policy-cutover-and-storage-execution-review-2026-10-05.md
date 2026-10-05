# 기계 정책 연결·기동 준비 및 저장공간 정리 실행 리뷰 — 2026-10-05

## 실행 범위

사용자의 두 계획 실행 지시에 따라 공용 후보 판정, 장후 자동 생성·dated publisher 연결, 현재 원천 결손 복구, 검증된 통합 배포와10/6 준비, 복원 가능한 중복 사본 정리를 수행한다. 원천일은10/2, 발행일은10/5, 준비 유효일은10/6이다. 휴일 Main 실행이나10/6 PID·PREOPEN receipt를 미리 만들지 않는다.

## 구현·리뷰

`entry_admission_recipe.py`는 비삼성 `KRX|KRX_REGULAR`의 고정 `pullback_p60_v0`를 공용으로 평가한다. 원 raw hash, 부모 BLOCK, source/invalidation/liquidity/micro/situation guard와 미해소 위험을 보존하고 열거된 soft confirmation fact만 별도 상쇄 ledger로 해소한다. 연구 adapter와 live evaluator가 같은 함수를 소비한다. holding/add legacy projection에서는 이 entry recipe를 제외한다.

`entry_admission_analysis.py`는 기존 ENTER/BLOCK/RECHECK를 삼성/비삼성으로 분리한다. 당시 capture cutoff·원 비용·원 stop·정확한 세션과 완료 가격을 결합해10분 결과를 계산하고 미도달만60분으로 보완한다. 공백·부분 첫 봉·동일 봉 양쪽 도달·마감 검열·비용/stop 결손은 미확정이다. 비삼성 최초 신호 사건과 군집 비교, 실제 native 자격 지표를 분리한다.

`main_machine_policy`는 명시적 recipe CLI로 이 보고서를 소비한다. 후보1개·삼성 제외·부모 CAS·날짜·source/kernel/hash·native train/holdout·coverage·승률 개선을 검증한 뒤 기존 dated owner에서 stage한다. 성공100%/80% 보존 gate는 없다. 이미 사용한10/2까지는 탐색 자료이며 이후 미소비 날짜만 새 holdout이 된다. 기존 전략 publisher가 새 admission component를 제거하는 충돌은 거절한다. AI·주문·수량·custody·격리의 기존 guard를 유지한다.

리뷰에서 시간/cutoff 검증, float 비용 비교, 판정 정책 해시 연결, 레거시 감사 호환, 캐시 이전 세대 보존을 보완했다. 최종 통합 표적17suite **1,033 PASS**, 후속 cache/생성기/위치3suite **241 PASS**를 확인했다. 후속 숫자는 앞 검사와 겹치므로 합산하지 않는다. 최종 추가 composer 검사·compile/diff/parser와 불변 release 검사는 아래 실행 기록에 남긴다. 전체 코드베이스와 미래 자연 기동의 무결함을 선언하는 검사는 아니다.

## 원천 복구·정책 결과

- collector history 변동은 표시용 sentinel 파일1개의 logical bytes 증가였다. 경제성 입력 추가/삭제/변경0이며 해당 stage를 실제 재생성해 `history_generation_changed`를 해소했다.
- Episode 후보는 재작성된 감사 보고서를 과거 해시로 참조했다. 현재 final 원천 감사 검증 후 실제 tuning을 다시 계산했고, 정책 mutation0으로 기존 정책을 승계한다. 새 후보가 JSON/Markdown/final dependency 사본을 content-addressed 경로에 참조하도록 했다. 기존 소비된 후보/receipt는 변경하지 않는다.
-10/6 격리 Episode 정책은61개 profile 모두 schema/source 유효다. 경제성 격리3개를 유지해58개가 정책 자격 범위다. 이는 당일 Main 활성·custody/open order·profile preflight/PID를 대체하지 않는다.
- 비삼성 관측6,550개와 최초 신호460개를 소비했다. 삼성519개는 후보 선택과 분리한 상속 진단이다. 실제 native/provenance와 가격·비용·stop 조건을 통과한 비삼성 평가는124개다.
- native 학습의 부모 선택32기회·17승, 승률53.125%; 고정 후보 선택3기회·1승, 승률33.333%였다. 후보는30기회 floor·50% coverage·raw/지원조정 개선을 통과하지 못했고 새 날짜 holdout도 없다.10/6 신규 선택을 강제하지 않으며 삼성·비삼성 모두 적격 incumbent를 승계한다. 관측 연구의 군집 개선과 이 native 부분집합을 혼합하지 않는다.

## 원천 보존의 확인 범위

기존 dirty 작업본·수정 전7개 코드/문서·소형 frozen 원본46개를 별도 보관했다. 첫 재계산에서 canonical projection gzip3개가 새 세대로 교체됐다. **이3개의 종전 압축 바이트는 별도 보관되지 않았으므로 원63파일의 현 경로 SHA가 전부 유지됐다고 주장할 수 없다.** 역사 frozen manifest는 수정하지 않았다.

원 capture/기존 연구 보고서/코드는 유지됐다. 새 계산과 기존 연구의 비삼성6,550개 전체에 대해 trace·날짜·종목·판정시각·raw SHA·부모/후보 행동을 대사해 차이0을 확인했다. 현재 projection도 SHA별로 보관했다. 이후 cache 교체는 이전 gzip을 immutable `generations/<sha>.json.gz`에 먼저 고정하고 압축 round-trip/source/kernel 검사를 유지한다. 과거 압축파일의 물리 receipt와 원 capture/연구 결과의 재현 확인은 구분한다.

## 저장공간 정리

service/PID/FD/selector/rollback/정책·연구 참조를 점검한36개 worktree에는 현재 삭제 적격 대상0이었다. raw dry-run도116개 postclose 보호·검증 부족2개를 남겼다. 이들을 정리 목표 때문에 삭제하지 않았다.

checkout backup8개에서 Git blob 및 archive ref로 정확히 복원되는8,032파일을 검증 후 삭제했다. 고유16파일은 보존했다. 실측 정리 창의 가용량 증가667,475,968 bytes다. 종료된 pytest fixture는 lock/PID/FD 부재와 재현 가능성을 확인해 정리하고 최신2개를 보존했다. 총 가용량은 동시 재계산·cache archive 쓰기 영향을 포함하므로 개별 apparent 삭제량과 구분한다.25GiB 관리 목표는 보호 자료 삭제로 강제하지 않는다.

## 배포·최종 준비

진행 중인 계산과 코드 리뷰를 닫은 뒤 검증된 commit을 불변 release로 봉인한다. Main selector와 영향 있는 inactive 장후 service pin을 전환하고, byte 변경이 없는 독립 Widget/Episode consumer pin·실제 PID는 유지한다. 최종 source/checklist를 고정한 뒤 선택 release 물리 경로에서 summary→strict `--require-summary-handoff`→controller→10/6 prepared 및 `current_full_contract`를 다시 검증한다.

최종 commit/release·준비 상태·timer/pin/PID·실제 디스크는 [실행 closure](../../tmp/policy-cutover-and-storage-execution-20261005/closure.json)에 기록한다.10/6 실제 소비/자연 관측/실현 경제성은 기존 당일 owner에서 확인한다.

## 근거

- [intake](../../tmp/policy-cutover-and-storage-execution-20261005/intake.json), [기존 코드/원본 archive](../../tmp/policy-cutover-and-storage-execution-20261005/frozen-original-archive.json)
- [collector 변동 대사](../../tmp/policy-cutover-and-storage-execution-20261005/collector-history-diff.json), [새 생성기 초기 결과](../../tmp/policy-cutover-and-storage-execution-20261005/recalculation-initial.json)
- [6,550개 원 capture/행동 대사](../../tmp/policy-cutover-and-storage-execution-20261005/historical-capture-parity.json), [Episode 검증](../../tmp/policy-cutover-and-storage-execution-20261005/episode-source-review.json)
- [통합 회귀](../../tmp/policy-cutover-and-storage-execution-20261005/final-targeted-tests.log), [cache 보존 회귀](../../tmp/policy-cutover-and-storage-execution-20261005/cache-preservation-tests-v2.log)
- [storage census](../../tmp/policy-cutover-and-storage-execution-20261005/cleanup-census.json), [Git 복원 검증](../../tmp/policy-cutover-and-storage-execution-20261005/checkout-backup-restore-verification.json), [중복 삭제 결과](../../tmp/policy-cutover-and-storage-execution-20261005/checkout-backup-cleanup-result.json), [pytest 정리](../../tmp/policy-cutover-and-storage-execution-20261005/pytest-cleanup-result.json)
