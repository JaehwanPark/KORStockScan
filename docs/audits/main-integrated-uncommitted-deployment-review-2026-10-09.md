# Main 미커밋 통합 리뷰·배포 — 2026-10-09

사용자가 전체 미커밋 변경의 코드리뷰·수정보완 및 완료 후 통합 배포를 승인했다. 기존 네 병목 계획과 이미 복구 배포된 장후 변경을 함께 대조한다. 작업본 HEAD/index·기존 변경은 보존하고, 별도 불변 Git 릴리스로 배포한다. 현재 10/9 체크리스트는 존재하지 않는다. 10/8 장후 원천일과 운영 달력상 다음 적용일 10/12를 유지하며 과거 문서를 오늘 owner로 대체하지 않는다.

## 리뷰 범위와 보완

- PASS 결과의 원 판정·신호·제한시간을 유지하여 Main 정상 제출 경로에서 한 번만 소비한다. 최종 broker/가격/수량/custody/manual guard는 유지한다.
- 계좌 조회는 유효한 평가 수요에 묶고, trace 중복 색인은 기존 원장을 복제하지 않는 bounded 준비와 증분 확인을 사용한다.
- 수정주가 완료봉은 공용 불변 revision으로 재사용하며 forming 수신시각은 갱신하지 않는다. 수정주가와 WS 원가격 동등성이 입증되지 않은 범위는 REST를 유지한다.
- 비상시감시의 관측과 실제 claim을 분리하고, 물리 구독 해제 확인 전 슬롯을 반환하지 않는다. 정확 원 신호의 남은 예산 안에서만 Main에 인계한다.
- 장후 변경은 보조비교의 이중 날짜 예산 원자적 이전, 변경 없는 prompt 입력 버전 결속, Main 종료 후 summary 순서, 생존 필수 원천 census, 기계/보조별 carry·부분 선정 표시를 검토했다. 이전 v5 배포 코드와 해당 변경 파일이 동일함을 확인했다.
- 추가 finding 1: 비상시감시 attach의 monotonic deadline이 종목 상태에 남아 다른 신호의 새 평가까지 만료시킬 수 있었다. deadline을 원 claim token에 결속하고 종료된 token만 제거한다. 후속 token의 상태를 지우지 않는 반례를 검증했다.
- 추가 finding 2: 완료봉 저장 시 가격 0·OHLC 역전 입력을 수용할 수 있었다. 저장 전 양수 가격·범위 관계를 검증하며 실패 입력이 기존 검증 revision을 교체하지 못하도록 회귀를 추가했다.

검토 범위에서 위 두 finding을 수정하고 재리뷰했다. 정책 패턴·보조 arm·호출 cap·주문 안전조건 변경과 신규 provider 호출은 없다. 에피소드·위젯 자동 경로는 복원하지 않는다.

## 검증 근거

- 통합 32개 suite: **1,394 PASS**, 112.76초. 추가 보완 후 영향 경로 **277 PASS**, 7.78초. 두 결과는 겹치는 검사이며 합산하지 않는다. pandas 설정 폐기 예정·멀티스레드 fork 관련 기존 경고 2개는 별도다.
- 원 결과: `/tmp/main-integrated-review-20261009.txt`, `/tmp/main-review-fixes-20261009.txt`.
- 현재 10/8 controller 전체 계약의 읽기 전용 재검증은 issues=[]다. 현행 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`의 loader 검증이 통과했다. 새로운 적용/PID 소비로 해석하지 않는다.
- Kiwoom 공식 저장소 HEAD를 10/9 재조회해 이전 검토 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`와 동일함을 확인했다. 실제 프로토콜 검토 경로·범위 및 합성 성능 측정은 [이전 구현 리뷰](main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)를 따른다. 이번 추가 수정은 프로토콜 필드·호출을 변경하지 않는다.

## 배포와 후속 소비

통합 release의 code/import/회귀와 retired-source guard를 검증한 뒤 공통 deployment/selection lock 아래 선택한다. 실행 중 Main·장후 worker가 없음을 확인한다. Main은 지금 수동 기동하지 않고 다음 예약기동 대상으로 준비한다. 배포본 web pin과 web process는 따로 대사한다. 원 10/8 장후 terminal·정책·10/12 checklist를 보존하고 새 release에 결속된 isolated PREOPEN 준비만 재생성한다. 기존 prepared PASS는 새 release의 증빙으로 재사용하지 않는다.

배포 최종 영수증과 PREOPEN 전체 검증 결과는 아래에 기록한다. 실제 10/12 PID 소비·자연 실행·실장 성능/비용 후 성과는 미도래다. 현재 날짜의 checklist 부재와 보존된 장후 원천 결손은 배포 성공으로 닫지 않는다.

## 최종 배포·준비 대사

- 선택 릴리스: `main-integrated-bottlenecks-20261009-v1`, commit `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`. 이전 선택은 `postclose-main-census-recovery-20261008-v5` / `4e13ecf5a16e993571b4081afd53f7ec93c8aab5`이며 복구 사본을 보존했다. 작업본 HEAD `270e870340502e8a0b15eb547b90239d258343a6`와 기존 index/미커밋 변경은 그대로다.
- 불변 릴리스 추가 검사 **250 PASS**, 9.43초. 변경 source/test 47개 해시 일치, runtime source clean, 퇴역 guard, 기존 controller 전체 계약·현행 정책 loader 재검증 PASS. 첫 포장 검사는 새 worktree의 index 미초기화를 검출했으며 그 worktree의 index만 HEAD로 초기화한 뒤 source clean을 재검증했다. 운영 선택 전에 해결했다.
- 설치 예약 **8개 routing PASS**, release-set 검사 PASS. 현재 Main·장후 계산 worker는 없고 새 Main PID 소비는 `false`다. 다음 운영일의 07:35 PREOPEN·07:55 Main 예약을 유지한다.
- 웹 `korstockscan-gunicorn.service`의 root/commit pin을 새 릴리스로 갱신하고 재기동했다. `ubuntu`, PID **513314**, 실제 `/proc/PID/cwd` 일치, HTTP **200**. 최초 일반 권한의 `/proc` 조회 거부는 privileged 읽기 전용 조회로 대사했으며 unobservable을 PASS로 간주하지 않았다.
- 10/8 원천→10/12 isolated PREOPEN을 새 선택 commit으로 생성했다. **prepared_verified / 전체 재검증 pass / findings=[] / actual_pid_consumed=false**. 기존 Main terminal·summary·정책·10/12 checklist를 재작성하지 않았다. `strict_checklist_generation_stale`를 포함한 현재 controller 전체 계약 finding은 0이다. EOD·보조 비교·연구를 재실행하지 않았다.
- Python compile 47개 및 diff 검사 PASS. print-only parser는 20항목·다음 적용일 `DirectFamilyPreopenPolicyHandoff` owner 1개·경고 0이다. 10/12 handoff가 incumbent carry를 표시하므로 이전 날짜 Main 수리 OPEN을 임의 복제하지 않았다. 외부 Project/Calendar sync는 실행하지 않았다.

배포 근거: [build](../../data/report/main_integrated_deployment/2026-10-09/build.json), [불변 source·policy/controller 검증](../../data/report/main_integrated_deployment/2026-10-09/isolated-check.json), [새 준비](../../data/report/main_integrated_deployment/2026-10-09/prepared.json), [준비 전체 재검증](../../data/report/main_integrated_deployment/2026-10-09/prepared-verification.json), [웹 소비](../../data/report/main_integrated_deployment/2026-10-09/web-consumption.json), [예약 routing](../../data/report/main_integrated_deployment/2026-10-09/cron-routing.json), [release-set](../../data/report/main_integrated_deployment/2026-10-09/release-set.json).

검토한 코드 범위의 미해결 finding 0으로 종료한다. 자연 신호의 PASS→제출 지연, WS/REST 절감과 실제 주문·체결·비용 후 성과는 이번 야간 코드 배포로 입증하지 않는다. 기존 장후의 cancel-wait/entry-split/원 입력 label 등 원천 결손은 [장후 복구 리뷰](postclose-result-recovery-review-2026-10-08.md)의 owner·closure를 유지한다.

## 전체 미커밋 작업본 재대조·불필요 작업본 정리

후속 사용자 지시로 작업본 전수 리뷰·통합 배포 상태 검증과 불필요 작업본 삭제를 수행했다. 현재 canonical 미커밋 source/test 47개는 선택된 `f36b306cb`와 모두 동일하다. untracked까지 포함한 private-index tree를 비교한 실제 차이는 이 문서의 배포 결과 13행뿐이며 runtime 차이는 0이다. 이미 검증된 통합 릴리스를 유지하며 동일 코드의 재배포·재기동·정책 발행은 반복하지 않았다. 전체 작업 스냅샷은 `8808581ba8e2517c57f38c45b4c787be379f31a3` / `refs/archive/disk-cleanup-20261009/integrated-workspace`로 보존했다. canonical HEAD/index와 작업 파일은 그대로다.

별도 `aux-prompt-research-20261008`, `aux-prompt-research-v6-20261008`의 미커밋 변경도 현행 reader/tuner/research와 대조했다. 초기 연구 구현은 현행에 포함되고 이후의 입력 버전·compact wire·계보·예산 보호 보완이 유지된다. research 관련 4개 suite **43 PASS**이며 새 provider 호출은 없다. 연구 원 작업 스냅샷은 각각 `c2f656be81af97582348923a294724d9318fda98`, `5c4991fa1c7a7efa3466015db17882871f63fec7`의 별도 보존 참조에 남겼다. 물리 파일 2,221개·2,237개를 Git blob과 대조했고 고유 tmp 스크립트/로그 8개는 해시를 검증하여 evidence의 `research-residue`로 보존했다. 공유 config/venv symlink의 대상은 삭제하지 않았다.

| 삭제 구분 | 개수 | 검증·보존 |
| --- | ---: | --- |
| 미사용 런타임 릴리스 | 18 | core source clean, Git HEAD 보존 참조, 공유 mount와 프로세스/설치/정책 참조 대사 |
| 완료 연구 작업본 | 2 | 미커밋 working tree 별도 보존, 고유 자료 8개 분리·해시 일치 |
| 중복 체크아웃 백업 | 3 | 2,673개 파일의 mode/Git blob 일치, 원 commit 보존 |

물리 삭제량은 **1,911,820,288 bytes (1.78 GiB)**다. 디스크 표시 사용률은 **76%→75%**이며 실제 filesystem 여유 공간 차이는 최종 영수증에 별도로 남긴다. 작업본은 canonical 외 26개에서 6개로 줄었다. 현재 통합본, 직전 장후 v5, 성공 Main terminal의 v4, 이전 Main/설치 web source, 원 기동 근거와 명시 rollback 사본을 보존했다. 숨김 과거 snapshot/seed는 이번에 재현·참조 검증이 끝나지 않아 `SKIPPED_UNVERIFIED`로 남겼으며 raw/주문/custody 자료 삭제로 범위를 확대하지 않았다.

현재 manifest와 운영 참조를 구분해 조사했다. 과거 selector/PID 이력에 이름만 남은 13개도 즉시 삭제하지 않고 원 경로를 quarantine으로 이동한 뒤 현재 정책 loader와 **10/12 PREOPEN 전체 계약**을 새 프로세스에서 재검증했다. 세 묶음 모두 원 경로 부재 상태에서 PASS/findings=[]를 확인한 뒤, deployment/selection lock 안에서 PID cwd/cmdline/fd·symlink·Git archive 참조를 재확인하고 삭제했다. 원 historical 영수증은 수정하지 않는다. 큰 raw/report 전수를 재스캔하거나 무관한 증빙 결손을 정상으로 만들지 않았다.

근거: [전수 작업 스냅샷](../../data/report/main_integrated_deployment/2026-10-09/all-worktree-integration-snapshot.json), [참조 census](../../data/report/main_integrated_deployment/2026-10-09/worktree-reference-census.json), [백업 2,673개 대사](../../data/report/main_integrated_deployment/2026-10-09/checkout-backup-validation.json), [연구 작업 보존](../../data/report/main_integrated_deployment/2026-10-09/research-working-copy-archive.json), [1차 삭제](../../data/report/main_integrated_deployment/2026-10-09/cleanup-manifest.json), [구 배포 정리](../../data/report/main_integrated_deployment/2026-10-09/cleanup-superseded-manifest.json), [연구 작업본 정리](../../data/report/main_integrated_deployment/2026-10-09/cleanup-research-manifest.json).

01:03 KST [삭제 후 최종 검증](../../data/report/main_integrated_deployment/2026-10-09/cleanup-final-verification.json)은 PASS다. 삭제·quarantine 경로 23개 부재, Git 보존 참조와 연구 고유 자료 8개 해시, canonical/릴리스 source 47개 해시를 다시 대사했다. 첫 삭제 직전 대비 filesystem 여유 공간은 **1,915,944,960 bytes 증가**했으며, 다른 프로세스의 동시 기록 때문에 대상 파일 할당량과 구분한다. 현재 정책 loader와 10/12 PREOPEN 전체 계약 findings=[]이며 설치 예약 8개·release-set 검사도 PASS다. 웹은 active이고 이번 정리로 Main을 기동하지 않았다.

종료 시 diff 검사와 print-only parser가 통과했다. 별도 작업으로 갱신 중인 10/9 holding-profit-exit 계획 문서는 canonical에 보존하며 그 계획의 기능 구현을 이번 배포에 포함했다고 해석하지 않는다. 본 cleanup 기록과 이후 문서 편집은 앞서 보존한 작업 스냅샷 이후의 변경이다.
