# 최종화 검증의 실시간 보유 투표 읽기 경합 수리 — 2026-10-15

17:49:32 cron_completion의 `postclose_finalization: strict_checklist_generation_stale`를 원인까지 추적했다. 현재3803938c7/PID2527556의 역사적 checklist 대체 검증이 `intraday_bootstrap_invalid:main_stop_confirmation_invalid`로 실패해 표면상 stale이 남았다. 17:36의 같은 내부 오류도 앞선 감사에서는 상세 원인 미확정으로 보존했다. 이번에는 현재 선택본의 읽기 전용 stop handoff를 반복해5번째 호출에서 정확히 `stop_vote_source_changed_during_read`를 재현했다. traceback은 `verify_vote_watch_binding`의 전체 파일 재검사다.

## 원인·범위

원10/14 정책은 incumbent carry이며 consumed vote source inventory는 비어 있다. 기존 reader는 원10/14 prefix와 이후 날짜 관측을 구분하지만, 오늘의 append writer와 잠금을 공유하지 않았고 파일별 검증 후에도 모든 실시간 파일 stat이 동시에 불변이어야 한다고 요구했다. 오늘의 정상 보유 투표가 그 사이 추가되면 원본 정책·체크리스트가 손상되지 않아도 전체 역사적 인계 검증을 거부했다. 일시 회복만으로 수리가 완료됐다고 보지 않는다.

수리는 기존 `automation/main_stop_postclose.py`의 carried source reader에 한정한다. 실제 작성자가 쓰는 `<position>.jsonl.lock`의 shared lock을 사용해 읽고, 이후 census 끝에서 같은 inode의 크기 증가가 확인되면 원 prefix와 모든 이후 날짜 행을 잠금 아래 한 번 더 검증한다. 전체 live 파일의 동시 정지를 요구하지 않고 파일별 검증 snapshot을 사용한다. 잠금을 생성하지 않으며 250ms 안에 확보하지 못하면 실패한다. 소비된 원천, full publication, 수치 selected 정책은 원래의 엄격한 불변 검증을 유지한다. 원본 변조·과거 날짜 삽입·다른 position/session·파일 교체·절삭·partial JSON·심볼릭 링크·비정상 lock은 통과시키지 않는다.

## 리뷰·검증

- 정상 append가 첫 읽기와 census 종료 사이에 발생하는 두 경우, 작성자 잠금 누락 한 경우에서 원 코드 실패를 결정적으로 재현했다. 과거 삽입/변조/교체6경우의 원 코드 거부도 보존했다.
- 수정 후 main stop150개와 finalization/cron/artifact/bootstrap/handoff/fixture 소비1,939개, 합계2,089개 PASS. 추가 시험은 native writer와 partial append 동시성, 잠금 없음·symlink·FIFO·busy·교체, 기존 full/consumed source 경계를 검증한다.
- 현재 원천의 읽기 전용 검사8회 PASS, 원 report SHA 불변. 이는 원천 reader 격리 검증이며 새 PID·전체 정책 소비·경제성 증명은 아니다.
- 자체 리뷰 후 census 마지막 검사를 lstat으로 보강해 symlink 교체도 실제 inode 비교에 반영했다. 재리뷰·최종 회귀·compile/diff/parser를 수행한다. 정확한 PREOPEN→후속 source SHA와 holding capability generation을 연결하고 독립 fixture를 요구한다.

기존 배포·재기동 승인 범위에서 후속 immutable release를 준비한다. 정책/임계값/수동 이관/계좌·주문·수량 안전장치, 원 finalization·strict/controller/summary·정책 보고서는 변경하지 않는다. 과거 보고서나 최종화를 다시 생성하지 않고 Telegram 알림도 수동 재발송하지 않는다. 실제 선택·PID 소비와 정규 artifact/cron 판정은 배포 후 별도로 기록한다. owner는 기존 `DirectFamilyPreopenPolicyHandoff`이며 중복 OPEN 항목을 만들지 않는다.

[경보 원본·직접 원인 재현·동시성 시험·현재 원천 검증](../../tmp/finalization-checklist-alert-20261015-1750/). 앞선 코드·원장·보유 경합 수리와 누적/보유 계약 통합을 모두 보존한다. 남은 원천 부족·기존 holding stale 및 장후 최종화 지연 경고의 수용은 기존 owner/Acceptance를 유지한다.
