# 9월 이전 미사용 파일형 원천 삭제 실행·코드 리뷰 — 2026-10-07

사용자의 “계획대로 점검하여 디스크공간을 확보하라” 지시에 따라 [삭제 계획](../proposals/pre-september-source-data-permanent-deletion-plan-2026-10-07.md)의 `delete_unused_raw`를 실행했다. **미사용 원천 정리는 완료했다. 현재 reader가 읽는 원천은 보존했으며 전체 D1 reader 개편·배포 완료를 주장하지 않는다.** DB·실주문·provider·정책·PID에는 변경을 가하지 않았다.

## 실제 공간과 삭제 결과

10/7 10:27:34 KST 최종 관측: 여유 공간 **14.625 → 32.412GiB**, 실제 증가 **17.787GiB**. `df -h`는 **15G → 33G / 사용률 90% → 78%**다. 삭제 할당량 20.507GiB에서 새로 보존한 archive의 nonraw 2.430GiB와 실행 중 다른 파일 쓰기의 영향을 구분한다. 실제 여유 증가를 삭제 할당량과 동일하게 표시하지 않았다.

| 집합 | 삭제 파일 | 삭제 할당량 GiB | 판단 근거 |
|---|---:|---:|---|
| 8월 analytics Parquet | 53 | 8.897 | 7,132,536행의 실제 emitted_at/ts/signal_date 판독; 저장 partition은 기간 증거에서 제외 |
| 미사용 혼합 분봉 cache | 882 | 3.830 | bars digest·timestamp 전수 확인; 끝 날짜 9/7~9/28 세대는 현행 9/29 refresh 시작 조건에서 open 전에 제외 |
| 8월 raw exclusion gzip 사본 | 19 | 2.890 | 실제 emitted_at 전수·KST clock·gzip 전체 CRC 확인; manifest는 보존 |
| 기존 pre-August raw archive | 1 | 4.162 | 기존 archive/manifest SHA와 12,325개 member bytes/hash 확인; raw 4,213개 제거, nonraw 8,112개 보존 |
| 퇴역 위젯 분봉 cache | 1,933 | 0.047 | 실제 bar timestamp 전수 확인 |
| 퇴역 위젯 상시관측 raw | 114 | 0.053 | observed_at_kst 및 actual_order_submitted=false/runtime_effect=false 확인 |
| 과거 sentinel raw cache | 40 | 0.179 | 실제 emitted_at 전수; 현행 exact-date reader와 구분 |
| 과거 pipeline summary 원천 | 60 | 0.448 | first_seen/last_seen 실제 시각 전수; 현재 family의 9/29+ 창 확인; manifest metadata는 보존 |
| **합계** | **3,102** | **20.507** | inode 중복 집계 0; 삭제 확정 후보 잔존 0 |

분봉 cache에는 9월 이전 19,720,433행과 9월 이후 4,873,972행이 있었다. 필요한 현재 cache를 필터링/재작성한 것이 아니라 **현행 reader가 열지 않는 세대 전체**를 삭제했다. 현재 9월 이후 연속 반전 누적 원천·라벨·12+12 정책은 보존했다. 모든 9월 이후 파일을 무조건 보존했다는 의미가 아니다.

## 구현·리뷰·회귀

소유 위치는 [단발 삭제 CLI](../../src/engine/automation/source_data_retirement.py)이며 engine root에 새 모듈을 만들지 않았다. 자동 예약·purge 규칙·시장 원천 reader·거래 경로와 연결하지 않았다. [회귀](../../src/tests/test_source_data_retirement.py)는 manifest 변조, 9/1 경계/current source, 미해결 clock, 파일 변경, inode/hardlink/symlink, 열린 FD, 보존 파일 손상, reader 전환 미완료, archive nonraw 보존 누락/변조, consumer 변경, DB가 raw 폴더 안에 있는 경우와 journal 재사용을 검사한다.

최초 구현/검토 후 동시 apply 방지 lock, consumer hash 재검증, 삭제 직전 경로 identity 재확인, archive preservation schema/member census 및 raw 파일 확장자 제한을 보완했다. 최종 재리뷰에서 이 단발 CLI의 검토 범위 내 미해결 결함은 0이다. **17 pytest PASS**, 관련 Python compile 및 `git diff --check` PASS. 초기 기타 원천 검증 worker의 exit 143은 삭제 근거로 사용하지 않았다. family별 분리·bounded record 크기·상수 크기 clock 집계로 다시 검증해 해당 2,147개 원천의 최종 manifest를 완성했다.

삭제는 파일별 identity/hash를 다시 확인한 후 durable intent → unlink → terminal journal 순서로 처리했다. 원본/복구용 새 raw archive·backup 및 복원 테스트는 만들지 않았다. 기존 raw archive의 nonraw는 `KORStockScan-storage-archives/pre-august-data-20261006/preserved-nonraw/`에 원래 상대 경로와 내용으로 보존했으며, 사용자가 이미 삭제한 옛 모델 backup을 현재 운영 경로에 복원하지 않았다.

## 보존·현재 소비 검증

- 사전 보존 대상 3,101개 hash 재확인, 유실 0. 현재/부모 initial quantity 정책·parent-current·연결 stage/replay/candidate/following-bars의 원래 bytes/hash를 유지했다.
- 원본 raw·network·외부 mutation을 차단한 initial quantity native 검증은 **PASS**, 실제 data read 8파일·raw 0. Replay 387행 중 9월 이전 347행도 유지했다.
- 현재 Main PID **777785**, start_ticks **95520219**, cwd **episode-startup-observability-20261007-v4/src** 유지. 현재 PID bootstrap **pass / findings=[]**. 정책·운영자 잠금·모델 parameter·기계/보조 정책과 선택 릴리스의 hash가 유지됐다.
- 기존 장후 finalization chain `fb84848e3085e3b6f4938e23a8f708b954dc61968320eeb5115dfc4150e63693`, snapshot `cd83b048db1745630e0fcea8e0ddf3f8fcde8f45d6af04f8bb4826f853d36158` 유지. 장후/PREOPEN/현재 체크리스트를 새 세대로 재작성하지 않았다.
- DB 후보/SQL/maintenance/연결 0, broker/order/provider/AI 호출 0, threshold 변경·배포·재기동 0. FD 접근 거부 PID는 `unobservable`이며 전체 PID open FD census 성공으로 주장하지 않는다. 현재 reader/code/source hash와 native 검증은 별도로 확인했다.

## 남은 원천과 종료 조건

Post-sell raw 144파일 / **6.223MiB**는 별도 보존했다. 102개 실제 원천은 현재 `holding_exit_observation_report._load_post_sell_rows()`가 6/5 이후 창에서 직접 읽으므로 `delete_after_reader_fix`다. 실제 존재 날짜 합집합과 target/census/producer 누락을 구분하는 D1 구현·리뷰·실제 보고서 consumer 전환이 종료 조건이다. 42개 sim 원천은 역사 custody/feedback의 동적 직접 reader를 확정하지 않아 `needs_consumer_classification`으로 남겼다. 이 보존을 이미 삭제한 다른 class의 공통 차단 조건으로 확대하지 않았다.

`tmp/widget-retirement-execution-20261006/widget-dedicated-data-before.tar.gz` **53.656MiB**는 manual custody·운영 설정·정책·보고서와 response cache가 섞여 있어 보존했다. Raw-only archive로 단정하지 않았으며, 필요한 nonraw/현재 원천의 보존 계약을 먼저 확정하는 것이 해당 archive의 종료 조건이다. 따라서 **모든 조사 범위의 raw backup 잔존 0**, **모든 역사 reader의 생산 차단**, **전체 계획 구현 완료**를 주장하지 않는다.

삭제한 raw 집합은 현재 Git 추적 파일이 아니므로 정상 checkout/export로 재유입되지 않는다. 현재 writer의 날짜 선택·9/29 refresh 조건도 유지했다. Git 과거 객체/원격 사본을 파기하거나 DB/EOD 저장 창을 변경하지 않았다. 단발 승인 실행의 기록 owner는 계획 §7과 아래 실행 manifest이며 정규 reader/예약 자동화로 등록하지 않았다.

## 근거

- [최종 실제 파일/공간/보존/남은 class 결과](../../data/report/pre_september_source_retirement/2026-10-07/execution-result.json).
- [사전 보호 hash·PID·filesystem census](../../data/report/pre_september_source_retirement/2026-10-07/before.json).
- [Archive nonraw 보존 및 전체 member byte verification](../../data/report/pre_september_source_retirement/2026-10-07/archive-nonraw-preservation.json).
- [초기 수량 raw 차단 native 결과](../../data/report/pre_september_source_retirement/2026-10-07/initial-quantity-after.json), [현재 PID/bootstrap·finalization](../../data/report/pre_september_source_retirement/2026-10-07/native-consumers-after.json).
- [남은 직접 reader 원천·class·다음 작업](../../data/report/pre_september_source_retirement/2026-10-07/retained-reader-dependent-raw.json).

각 집합의 sealed manifest·durable 삭제 journal과 SHA는 최종 결과의 `groups`에 기록했다. 새 운영 정책/전략 경제성/PID 적용을 승인하는 증거로 사용하지 않는다.

## 후속 통합 리뷰의 추가 보완

10/7 전체 미커밋 통합 리뷰에서 FD census 불완전 시 삭제 허용, unlink 후 directory fsync 실패의 잘못된 미삭제 집계, manifest 교체 시 summary hash 불일치를 추가로 재현·수정했다. 삭제 CLI 회귀는 21 PASS이며 이전 sealed 삭제 결과는 다시 쓰지 않았다. 이번 보완에서는 운영 파일 삭제를 실행하지 않았다. [통합 리뷰](integrated-uncommitted-workspace-review-deployment-2026-10-07.md)에 결함·보완·최종 배포 증거를 구분한다.
