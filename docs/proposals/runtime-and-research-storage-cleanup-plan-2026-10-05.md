# 운영·연구 자료 디스크 정리계획 — 2026-10-05

## 1. 범위와 현재 용량

이번 요청은 정리계획 수립이다. 삭제·압축·worktree 제거·Git ref 변경은 실행하지 않았다. [정책 적용·기동 계획](next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md)과 같은 보호 목록을 사용한다. 실행 owner는 [10/5 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)의 `VerifiedStorageCleanup1005`다.

10/5 실측 root 용량은154,894,188,544 bytes, 가용18,201,251,840 bytes(약 **16.95GiB /18.20GB**), `df -h` 표시는145G·사용128G·가용17G·89%다. 아래 `du` 값은 반올림한 사용량이며 행마다 포함 관계가 있으므로 합산하지 않는다. release는 공유 symlink를 따라가지 않은 값이다.

| 경로 | 사용량 | 우선 판단 |
| --- | ---: | --- |
| 작업 저장소 전체 |97GiB | data/tmp 중심. 전체 삭제 금지 |
| `data` |88GiB | 소유자·소비자·복구 가능 여부별 분류 필요 |
| `data/analytics` |30GiB | Parquet 분석 원천. 기본 보호 |
| `data/report` |16GiB | monitor snapshots2.3GiB, machine observation projection1.9GiB, opportunity census1.8GiB 등. 사용 중인 정책/연구 원천 보호 |
| `data/threshold_cycle` |9GiB | snapshots4.1GiB와 recovery archive644MiB 포함. 현행·rollback 세대 보호 |
| `data/runtime` |8.2GiB | machine research2.3GiB, WS monitor2.3GiB, two-leg expansion1.6GiB, sentinel cache1.6GiB. cache라는 이름만으로 삭제 불가 |
| `data/source_quality` |7.8GiB | raw_row_exclusion7.7GiB. 제외 판정 근거이므로 기본 보호 |
| `data/cache` |6.3GiB | 대부분 ka10080 보관 봉. 재생 결과와 비용/시간 경로 근거 확인 필요 |
| `data/pipeline_events` / `data/observations` |5.3GiB /3.3GiB | 원천 identity·순서·행동 대사의 근거. 검증 없는 삭제 금지 |
| 저장소 `tmp` |6.5GiB | 고유 연구 자료·hash manifest·배포 backup을 포함. 임시라는 이유로 삭제하지 않음 |
| runtime releases |3.5GiB | checkout backups638MiB, release seeds80MiB 포함. 전체가 회수 가능량은 아님 |
| 별도 worktrees |912MiB | 미통합 수정·Git 참조·실행 참조 대사 후 판정 |
| 시스템 `/tmp` |738MiB | 종료된 테스트 잔여부터 확인 |
| 저장소 logs / `.git` / `.venv` |약414MiB /318MiB /2.2GiB | 로그 원천은 보존 여부 검증. Git/가상환경 일괄 정리·패키지 제거 제외 |

현 등록 worktree는36개다.10/4에21개를 정리한 기록은 [이전 정리 결과](../audits/integrated-deployment-and-disk-cleanup-review-2026-10-04.md)에 있으며 추가21개를 삭제할 수 있다는 뜻이 아니다. 현재 가용량은 그때보다 줄었으므로 실행 직전에 다시 측정한다.

## 2. 우선 보호할 참조

| 보호 대상 | 이유·검증 |
| --- | --- |
| 선택 `integrated-source-review-20261004-9c0c0632` | Main selector·장후/장전 경로. 정책 적용 전까지 현재 운영 기준 |
| 이전 `postclose-tower-readiness-20261003-a17bd6d2` | selector previous 및 rollback |
| `postclose-winrate-readiness-20261003-e6d4d3b9` | Widget/Episode 설치 pin 및 실제 Widget/collector PID cwd |
| `integrated-20260922-2e1d935f9` | 이번 `/proc` 조회에서PID2729821/2729851/2729852 cwd 참조 확인. 오래됐거나 미등록이라는 이유로 제거 불가 |
| 새 배포 release·직전 rollback | 이후 전환 시 보호 집합에 먼저 추가. 전환 직후 기존 PID가 남을 수 있음 |
| `.checkout-backups`, `.release-seeds`, archive refs | 원 Git blob·고유 수정·배포 복구에 필요할 수 있음. 중복 입증 전 보호 |
| 미커밋/미통합 작업본 | 현재 연구 코드·문서·tests 전체. HEAD archive만으로 untracked/dirty bytes 복구 불가 |
| `tmp/non-samsung-final-policy-decision-20261005` 및 참조 폐쇄 전체 |63파일 frozen manifest, 후보/부모/입력/kernel/선행 연구 자료. 간접 참조까지 포함 |
| 삼성 연구와 장전 고정 계약의 입력 | 다음 날짜 검증·비교 부모·원 capture/가격 원천. 비삼성 연구 종료가 삼성 자료 삭제 허가가 아님 |
| 정책·custody/order/fill/terminal·source-quality·next PREOPEN receipts | 현행 소비·감사·기동/경제성 대사 근거 |

현재 PID 목록은 시점 관측이다. 실행 전에 `/proc/*/{cwd,cmdline,fd}`와 systemd `WorkingDirectory/ExecStart`·drop-in·timer·cron·selector·prepared/forward manifest를 다시 수집한다. release의 `data/docs/tmp/logs/.venv` symlink 실제 대상을 기록하고 공유 원본을 release 고유 데이터로 계산하지 않는다. 종료된 프로세스도 서비스가 다음에 참조하면 보호한다.

## 3. 정리 후보 검증 및 실행 순서

### S0. dry-run manifest

대상별 `path, realpath, kind, physical_bytes, mtime, git_HEAD, dirty/untracked, service_refs, pid/fd_refs, policy/research_refs, archive/restore_receipt, disposition, reason`을 작성한다. 분류는 `protected`, `verified_deletable`, `archive_first`, `unverified_keep`다. 전체 연구/정책 JSON·코드 경로의 직접·간접 참조를 먼저 모으고 후보를 대조한다. 용량 순서가 삭제 허가를 대신하지 않는다.

재측정 값은 `df`/allocated bytes와 apparent bytes를 구분한다. hardlink/symlink 중복, 열린 삭제 파일 때문에 논리 삭제량과 실제 가용량 증가가 다를 수 있다.

### S1. 종료된 테스트 잔여

- 실행 중 pytest/worker·lock·open FD와 무관하고 실패 재현/고유 로그를 보존한 fixture만 우선 정리한다.
- 재생성 가능한 Python/pytest cache는 중단된 writer와 참조를 확인한다. 작으므로 큰 회수량을 예상하지 않는다.
- 시스템 `/tmp` 전체, 다른 작업의 temp, 현재 virtualenv를 일괄 삭제하지 않는다.

### S2. 미참조 release/worktree

- 보호 집합 밖에서 service/PID/cron/rollback/manifest 참조가0이고 고유 source·logs·report가 없는 후보만 대상이다.
- 각 HEAD를 날짜별 `refs/archive/disk-cleanup-20261005/...`에 남기고, dirty/untracked가 있으면 먼저 byte/hash 및 복원 가능한 별도 사본을 검증한다. 보관물을 같은 삭제 후보 안에 두지 않는다.
- worktree는 Git 등록과 실제 경로를 함께 정리한다. 미등록 release는 같은 참조/고유 파일 검사를 별도로 통과해야 한다.
- `.checkout-backups`는 원본 blob/스냅샷을 대사해 실제 중복이 입증된 항목만 제거한다. release 디렉터리 전체를 날짜 glob으로 지우지 않는다.

### S3. 검증된 raw 중복·압축

- 기존 [압축 producer](../../src/engine/compress_db_backfilled_files.py), [micro-reversion 보존 owner](../../src/engine/scalping/micro_reversion/storage_maintenance.py)의 실제 dry-run/보존 계약을 확인한 뒤 범위가 일치하는 작업만 사용한다.
- Parquet/manifest/row count·기간/route·원본 logical SHA/size, gzip round-trip/integrity, downstream reader의 압축 입력 지원을 검증한다. writer/lock/FD가 있으면 보류한다.
- 이미 plain/gzip이 있는 경우 이름 일치가 아닌 해제 bytes 일치를 요구한다. checksum/행 수 불일치·`SKIPPED_UNVERIFIED`는 보존한다.
- frozen manifest가 원 경로의 bytes를 검증한다면 압축 대체도 변경이다. 동일 원천의 검증 가능한 보관/reader 호환 계약을 마련하기 전에는 plain을 제거하지 않는다.

### S4. 사용 종료된 연구 temp·snapshot·cache

- tmp의 큰 경로에는 삼성 pattern 약1.2GiB, opportunity contract 약800MiB, ENTER 미진입 분석 약711MiB, 과거 disk cleanup 약499MiB가 있다. 이들은 **검토 대상 크기**이며 삭제 승인 목록이 아니다.
- 연구가 닫혔어도 원본 후보/계산/재현/이후 검증에서 참조하는 유일 자료는 보존한다. 동일 내용을 가진 중복 사본만 hash·경로 소비자 대사 후 제거한다.
- tmp 경로를 정식 archive로 옮길 필요가 있으면 새 immutable manifest와 옛 경로 소비의 호환/복원 방식을 먼저 만든다. 기존 연구 receipt를 새 bytes에 맞춰 덮어쓰지 않는다.
- raw_row_exclusion·Parquet·가격 봉·pipeline·policy snapshot을 크기만 보고 삭제하지 않는다. 큰 구조적 감축이 필요하면 검증된 외부 보관/복원과 각 owner의 보존 계약을 별도 계획으로 다룬다.

### S5. 사후 확인

- 삭제/압축 성공·보류·실패 path와 이유, 실제 free-space 증가를 기록한다.
- selector/previous/모든 service pin/실제 PID/rollback/source manifest가 여전히 해석되는지 확인한다.
- 보호한63파일 frozen manifest 및 다음 PREOPEN/삼성 forward 입력을 재검증한다. 원래 존재하던 준비 실패와 새 변경을 구분한다.
- policy/source bytes가 바뀌는 정리는 새 prepared 세대 봉인 전에 마친다. 봉인 후 정리는 해당 manifest에 영향이 없는 대상으로 한정한다. collector history manifest가 이미 변한 현 상태에서 참조 파일을 추가로 제거하지 않는다.

## 4. 여유 용량 목표와 중단 기준

회수 가능량은 S0 검증 후 산출한다.3.5GiB release,6.5GiB tmp,88GiB data를 전부 회수 가능량으로 보고하지 않는다.

운영 준비에 필요한 여유는 `새 release/rollback 추가량 + 압축·archive 동시 존재 최대량 + 다음 장중/장후 쓰기 예상량 + 기존 저장장치 경보 여유`로 계산한다. 실행 직전 실측으로 산출하며 보호 원천을 지워 이 식을 억지로 맞추지 않는다. 우선 여유 **25GiB**를 관리 목표로 제안하되, 이는 새 매매 중단 임계치나 확보 보장이 아니다. 현재 대비 약8GiB 추가 여유가 필요하며 안전한 후보만으로 가능한지는 아직 미확정이다.

필요 여유가 확보되거나 검증된 후보가 소진되면 정리를 끝낸다. 미확인 원천까지 삭제 범위를 넓히지 않는다. 공간이 부족하면 회수 부족량·보호 이유·추가 보관/용량 확보 필요를 명시한다. 정리 작업 중 서비스 재기동, 주문 변경, 패키지 제거, source-quality 계약 완화는 수행하지 않는다.

## 5. 계획 검증

현재 수치·보호 release/PID·원천/연구 연결·실행 순서·중단 기준을 문서 리뷰하고, 링크·단일 OPEN owner·`git diff --check`·print-only backlog parser로 검증한다. 삭제 dry-run manifest와 파일별 복원 검증은 후속 정리 실행의 첫 산출물이다. 이번 계획 점검을 삭제 적격성 검사 완료로 표시하지 않는다.

## 10/5 실행 인계

최신 사용자 지시로 위 계획을 실행한다. 공용 판정/장후 생성 연결, 원천 복구 및 검증된 정리는 [실행 리뷰](../audits/machine-policy-cutover-and-storage-execution-review-2026-10-05.md)와 그 closure에 기록한다. 계획 작성 시점의 미실행 문구는 역사 상태다.10/6 실제 activation/PID와 자연 수용은 해당 당일 owner에서 확인한다. 기존 압축 캐시3개의 물리 SHA 보존 제한과6,550개 원 capture/행동 차이0을 분리해 공개했다.
