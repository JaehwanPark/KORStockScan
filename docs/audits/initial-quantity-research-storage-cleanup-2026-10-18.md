# 완료된 매수 수량 연구 임시자료 정리 — 2026-10-18

## 결정과 범위

- 사용자 지시: 연구가 종료되어 불필요한 데이터를 삭제한다.
- 이번 수량 연구에서 종료된 synthetic fixture, 재생성 가능한 cache, 깨끗한 baseline 작업본, Git 원본과 일치하는 checkout 사본을 대상으로 삼았다.
- 운영 정책·원천·주문/custody·고유 연구 자료·최종 및 실패 증거는 보존했다. 선택900/이전e122, 원7f ancestry, 실제 소비되는 보조정책 증명, 다음 정규10/19 준비본을 유지했다.
- Main 재시작·provider 호출·주문은 모두0이다. 이 정리는 실제 PID 소비나 경제성 수용을 뜻하지 않는다.

## 최초 인벤토리와 동시 작업 구분

최초 후보는8분류/55경로, 논리1,044,689,147B·할당931,147,776B였다. 중복 checkout2,667개 파일은 Git blob과 모두 일치했다. 삭제 전에 root 권한으로 프로세스 cwd/exe/FD/maps와 mount namespace, 선택/준비본/정책 참조를 확인했다.

동시 정리와 pytest 만료로 baseline 작업본·중복 checkout2곳·pytest1368/1369/1370이 먼저 없어졌다. 원본 인벤토리는 변경하지 않고 부재를 별도 기록한 뒤, 남은 cache49곳만 재검증했다. 다른 작업의 삭제량은 이번 직접 삭제량에 포함하지 않았다.

- baseline의 외부 삭제: `tmp/disk-cleanup-20261018/worktree-deletion-journal.jsonl` 및 `worktree-result.json`; 기존 archive ref가 e122를 보존한다.
- 두 checkout의 외부 삭제: `data/report/research_storage_cleanup/2026-10-18/attempts/224616/cache-deletion-journal.jsonl`.
- pytest는 동시 정리/기본 보관 만료와 부재를 확인했다. 최종 제거 주체를 파일별로 모두 확정하지 못했으므로 별도 회수 실적으로 주장하지 않는다.
- 원래 후보의 실제 이름·inode/stat을 기준으로 잔여 인벤토리를 고정했다. 새 경로를 삭제 범위에 추가하지 않았다.

## 직접 실행 결과

| 항목 | 결과 |
| --- | --- |
| 잔여 연구 작업본 cache | 23 + 26 = 49곳 삭제 |
| 파일 | 재생성 가능한711개 삭제 |
| 직접 삭제 논리량 | 53,594,554B |
| 직접 삭제 할당량 | 55,128,064B, 약52.6MiB |
| 정리 기록·helper 공간 | 최종 계측13,398,016B; 새 archive0B |
| 기록 공간 차감 후 보수적 회수 | 추가 metadata1MiB를 예약하고40,681,472B, 약38.8MiB |
| apply 구간 파일시스템 여유 변화 | +54,837,248B; 동시 작업/기록 쓰기 포함, 순회수량과 구분 |
| 전체 최초 후보 경로 | 모두 부재 확인; 외부 삭제 포함 |
| 보호 파일 | 122개 hash 동일 |
| 기존 dirty tracked 파일 | 33개 hash 동일 |
| 선택·이전 릴리스 | 900234d79 / e12256dec 유지 |
| 삭제 전후 root 프로세스 확인 | 참조·mount·권한누락0 |

모든 직접 삭제는 파일별 journal에 기록했다. 원본·잔여 인벤토리, 실행 helper, 검증 결과와 독립 리뷰는 보존하므로 기록 공간을 삭제 회수량에서 임의로 빼거나 filesystem 여유 변화를 전체 작업 성과로 합산하지 않는다.

## 리뷰·수정·검증

1. 최초 리뷰에서 보호 경로 census가 경로 목록이 아닌 개수라는 점을 수정했다. 원 census를 보존하고54개 명시적 경로와 기존 SHA를 가진 별도 projection을 만들었다.
2. root/자식 directory FD와 inode 확인, FD 기반 no-follow 파일 hash, unlink/rmdir 직전 동일성 확인, Git archive ref CAS를 보완했다.
3. 추가 파일·내용 변경·hardlink·상위 symlink·교체된 leaf/root·hash 도중 변경을 거절하고, FIFO/symlink 제거가 외부 원천을 훼손하지 않는 guard9개를 통과했다.
4. 독립 재리뷰 finding0. 고정 잔여49경로/711파일의 SHA/stat과 보호122파일을 다시 확인했다.
5. 실행 직전 선택/보호 hash·fresh root 프로세스 참조를 확인하고 release-set lock 안에서 정확한 잔여 경로만 삭제했다.
6. 실행 후 전체 최초 후보 부재, 직접49경로 journal, 보호 hash·선택/rollback·archive ref·동시 수정 보존을 확인했다.
7. Python compile·guard 검사·`git diff --check` 및 print-only 문서 parser를 수행했다. 런타임 코드가 바뀌지 않아 거래 회귀·보고서 재생성·provider/API 호출은 수행하지 않았다.

## 증거와 현재 owner

- [원본 인벤토리](../../data/report/quantity_research_cleanup/2026-10-18/readonly-inventory-20261017T225059Z.json)
- [동시 삭제 후 재설정](../../data/report/quantity_research_cleanup/2026-10-18/external-deletion-rebase.json)
- [고정 잔여 인벤토리](../../data/report/quantity_research_cleanup/2026-10-18/residual-inventory.json)
- [보호 경로](../../data/report/quantity_research_cleanup/2026-10-18/protected-reference-paths.json)
- [리뷰](../../data/report/quantity_research_cleanup/2026-10-18/review.json), [실행 결과](../../data/report/quantity_research_cleanup/2026-10-18/result.json), [삭제 journal](../../data/report/quantity_research_cleanup/2026-10-18/deletion-journal.jsonl), [사후 검증](../../data/report/quantity_research_cleanup/2026-10-18/verification.json).
- [삭제·기록 공간 분리 계측](../../data/report/quantity_research_cleanup/2026-10-18/storage-accounting.json). 다른 작업의 선행 삭제는 회수량에서 제외했다.
- 실행 owner: [10/18 체크리스트](../checklists/2026-10-18-stage2-todo-checklist.md)의 `InitialQuantityResearchCleanup1018` 완료. 기존10/19 PREOPEN/PID·정규 자연 생산·경제성 owner는 유지한다.

검증 범위의 정리는 완료됐다. 고유 연구 원천·운영/복구/직접 소비 증거는 계속 보존한다.
