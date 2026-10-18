# 10/19 PREOPEN 경고 수리와 실행 검증

원천일은 2026-10-16, 적용 대상은 2026-10-19다. 사용자는 경고 수리·재생성·재기동을 지시했다. 최초 선택은 `958d35b2b03f0a37462c1c0121fc14c108e709b8`이며 Main/supervisor 부재를 확인했다. 기존 원 정책, 수동/퇴역 custody, 수량·threshold·provider·hard safety는 유지한다. 원 05:41 실패와 10/18 P5/P6 PASS는 각 당시 증거로 보존한다.

## 재현과 수리 범위

- 05:35 finalization은 controller/summary를 갱신한 뒤 cleanup에서 실패했다. 일반 캐시 탐색이 보존된 배포 격리 `work` 디렉터리(mode 000)에 진입했다. 준비 재생성은 후행 단계라 실행되지 않았으며 native 검증은 `prepared_source_or_release_changed`였다.
- 캐시 탐색은 `.venv/.git/data/logs/tmp/docs`를 소유권 경계에서 제외한다. 증거 내부 캐시·권한·원천을 보존하고, 일반 코드 범위 읽기 실패는 계속 cleanup 실패로 처리한다. 부분 탐색 결과로 삭제하지 않는다. 운영 계약은 [로그 보관](../operational-log-retention.md)을 따른다.
- 후속 release의 동일 정책 코드 인계는 선택된 predecessor의 native 검증을 통과한 immutable 원 준비 증거를 이어받는다. `previous_handoff`는 현재 선택 commit/family의 정식 경로만 허용하며 원 정책·원 코드 digest·전체 source·날짜·clean candidate를 재검증한다. 바뀐 controller/summary 경로에 과거 원문을 복원하지 않는다. 선택 경합·원천 변조·다른 family/정책/준비 원본은 거부한다. 이는 정책 발행·PREOPEN·PID 권한이 아니다.
- trailing 경고는 보고서 code contract와958 실제 계약의 불일치다. 기존 producer의 completion prefix→fact→quantity→holding suffix를 통해 현재 코드의 새 세대를 생성한 뒤 summary/strict/controller/준비와 연결한다.
- 초기 수량 경고의 기존 완료 모수13건은 비용/수량 결손으로 제외됐다. 운영 research cost index가 없음을 확인했다. 기존 공식 저장 자료를 native producer로 연결하며 배분 연구 비용을 canonical 실제 비용으로 바꾸지 않는다. 복구 불가 부분은 null/제외를 유지한다.
- 실제 재생성에서 `quantity_pipeline_record_partition_required`를 추가 재현했다. 첫 대형 행은 `strategy_owner_replay_seed_observed`/`record_id=null`이며 수량 거래 범위 밖이다. 64KiB 상한은 유지하고 대형 행 전체의 최상위 식별자를 구조적으로 확인한 뒤 범위 밖만 배제·계수한다. 범위 안 대형 행은 해당 거래의 경로에 명시적 source gap을 남겨 counterfactual/timeout 선택에서 제외한다. 원 완료 비용의 parent 관측은 별도로 유지한다. 식별자 누락·중복 키·잘린 구조는 계속 전체 실패다. 다음 행을 잃지 않는 Unicode/후행 식별자와 식별된 거래만 제외하는 회귀를 포함했다. 정상 fact/비용 의미·원천 hash·세대 CAS는 유지한다.
- 승인된 동일 정책 배포가 자정을 넘길 때 machine 후보의 native stopped rebind는 있지만 보조 overlay publisher는 미래 날짜만 허용하던 인계 결손을 확인했다. 당일07:35 이전·native 동일 정책 code-refresh proof·완료된 원천 controller·source-code handoff·선택 릴리스·Main/supervisor 부재·PREOPEN/live bootstrap 미생성·기존 CAS를 모두 요구하는 동일 세션 준비를 추가했다. 128개 binding/승인2 PRE 변경/rollback/원 연구 입력은 그대로 검증하며 장중 재선정 권한이 아니다. 원 준비 코드 쌍과 원76개 의존성을 보존하고 새 정확한 source generation을 별도 검증한다.

## 검증과 진행

캐시 탐색의 증거 보호·권한 거부·partial census 회귀 및 cleanup/finalization 98개 통과. 후속 정책 코드 인계·장전 준비·intraday 인계 2,646개 회귀가 통과했다. 추가 수량/당일 인계 보완 후 관련7모듈 최종2,967개와 원/발행/현재3세대 코드 변조 회귀3개가 통과했다. 이 수치는 중복이 있어 합산하지 않는다. 성공과 선택 경합·변조·다른 원본·07:35 이후·실행 PID·미완료 controller 거부를 검증했으며 Python compile, shell syntax, diff, print-only 문서 parser도 수행한다. 자기 리뷰→보완→재리뷰에서 이 변경 범위 미해결 지적0이다. 최종 native generation과 실제 배포/PID는 별도 검증한다.

기존12개 준비/정책/선택/보고서 및 원 snapshot11개 2,457,982,550bytes는 [작업 증거](../../tmp/preopen-alert-repair-20261019/)에 보존했다. 재생성·배포·실제 PID·자연 신호/비용 성과는 아직 완료로 표시하지 않는다. 기존 `DirectFamilyPreopenPolicyHandoff`, `OperationalLogRetentionRepair1016`, `InitialQuantityProducerConsumerRepair1010`, `HoldingProfitExitSourceContractRepair`의 Acceptance를 유지한다.

## 현재성 관측 분리와 마지막 검사 복구

`postclose_finalization --recover-closed-target --resume-final-detector`는 최종 detector만 실패한 가장 최근 native 시도에서 원 controller/strict/snapshot/cleanup 세대·실제 완료 시각·선택 release를 검증한다. 원 로그와 실패 보고서는 immutable receipt 폴더에 보존한다. cleanup 또는 policy/PREOPEN을 다시 발행하지 않으며 새 full detector와 동일 세대 검증이 통과해야 wrapper가 정식 DONE을 남긴다. 51개 회귀 및 compile/shell/diff/parser가 통과했다. 07:42:33 실제 cleanup 완료, 07:53:46 finalization/최종 detector DONE을 분리한다.

10/19 PREOPEN은07:50:46 완료됐고 Main PID274478의 선택894 소비는07:55:50 launcher 영수증으로 확인했다. 기동 observer는 기준일10/16 raw inode 교체를 발견하여 원 요약 cursor를 재사용하지 않았다. 원 요약/manifest를 보관한 정식 allow-bootstrap 재생성을 통해 현재 원천을 다시 읽고 검증한다. 과거 raw를 수정하거나 cursor만 옮기지 않는다.

all-scope trailing 원 보고서는 수량 수리 전 코드 계약84746d였고 현재894 계약은ddca6b다. 원 holding을 다시 쓰면 이미 확정된 PREOPEN·holding 정책 SHA를 깨뜨리므로 monitoring 소유 `main_trailing_currentness.py`에서 별도 native 전체 원천·partition·산술 재검증을 발행한다. health는 원 holding/report 세대, 동일 source/target/scope 및 parent policy, 현재 코드와 새 native report 결속만 관측한다. 원 계약 실패를 original_findings로 남기고 새 검증의 근거를 분리한다. 이 영수증은 bootstrap/정책 소비자에게 허용되지 않으며 원 source gap·비용 null·거래 성과 상태를 변경하지 않는다. module은 engine root 대신 monitoring 패키지에 두고 exact generation 변조/날짜/원천/권한/정책/scope 거부와 native producer failure를 회귀 검증한다.
