# 구 episode 강제 종료·영구 OFF 실행 기록

## 승인과 실제 변경

2026-10-08 사용자 지시: 구 episode 서비스의 공유 원장 잠금을 강제 종료하여 병목을 해소하고, SK이터닉스·한화오션 체결 원장은 종료 제한으로 삼지 않는다. episode 기능은 영구 OFF, 기능 완전 폐기는 별도 계획이다. 기존 잔여 custody 때문에 서비스를 유지한다는 조건은 이번 정지에서 적용하지 않는다.

11:02:28 KST에 확인된 정확한 systemd 인스턴스를 먼저 runtime mask하고 stop job을 등록한 후 cgroup 전체에 SIGKILL을 전달했다.

| 서비스 profile | 종료 전 PID | 종료 후 |
| --- | --- | --- |
| `hanwha_ocean_late_morning` | 50309 | PID 없음, inactive, masked |
| `sk_eternix_late_morning` | 78161 | PID 없음, inactive, masked |

종료 직전 `/proc/locks`에서 공유 lock inode `1328610`의 WRITE holder는 78161, 대기는 50309였다. 두 프로세스의 cwd는 구 `episode-eight-retired-main-five-20261006-511664f3` 릴리스다. 종료 뒤 두 PID의 잠금은 0개다. `data/runtime/order_owner_registry.jsonl.lock`의 inode `1328610`을 유지했으며 lock 파일을 삭제하거나 새로운 inode로 교체하지 않았다.

11:03:47부터 모든 설치·로드된 low-price episode 및 삼성 one-share 전용 unit을 영구 차단했다.

- `/etc/systemd/system`의 **201개 unit 모두 `/dev/null` mask**: service 132개, timer 69개. 그중 기존 영구 mask 60개를 유지했고 141개를 새로 차단했다. 재리뷰에서 날짜가 지난 삼성 일회성 episode add-on service/timer 2개도 확인하여 포함했다.
- 타이머는 먼저 disable/stop했고 service를 정지했다. template, preflight, 자동 확장과 삼성 one-share가 포함된다.
- `/etc/korstockscan/episode-permanent-off` 운영자 OFF marker와 10개 기본 서비스/template의 `zzzz-episode-permanent-off.conf`를 설치했다. `ConditionPathExists=!/etc/korstockscan/episode-permanent-off`, `Restart=no`로 기존 installer가 기본 unit만 재설치하더라도 재기동되지 않게 했다. 영구 mask/OFF marker를 자동 해제하지 않는다.
- 기존 unit 정의는 실행 검색 경로 밖 `/etc/korstockscan/episode-off-units-20261008T110347+0900`에 보존했다. 기능 삭제나 자동 재활성화용 복구를 실행하지 않았다.
- systemd daemon reload 완료. system/user unit, ubuntu/root crontab 및 `/etc/cron.d`/crontab을 확인했다. 별도 episode live cron/user unit은 발견되지 않았다. Main 공통 장후 cron은 유지했다.

한화오션·SK이터닉스 기존 보유의 episode 자동 매도·취소·보호 관리는 중단됐다. 이 실행은 매도나 미체결 취소, 계좌 flat 확인, 소유권 이전이 아니다. 기존 원장·정책 자료는 삭제·수정하지 않았다.

## Main과 잠금 검증

- Main은 **PID 76094**, 기존 `main-loop-latency-20261008-v5/src` cwd로 계속 실행한다. Main release 전환·재기동·정책 교체·주문은 이번 작업에서 실행하지 않았다.
- 종료된 두 PID 재출현 없음, episode service/timer active 0, 영구 mask 누락 0. systemd의 빈 template slice는 프로세스나 실행 service가 아니므로 active service에 포함하지 않는다.
- 공유 원장 guard와 원장 내용은 보존한다. 종료로 커널이 프로세스 잠금을 해제한 것이며 원장 guard를 우회한 것이 아니다.

## 처리량 관측

동일 Main PID의 `logs/runtime_performance_info.log`에서 모든 완료 warm loop 누적 카운터의 차이를 비교했다. 재시작/표본 reset이 없고 retained limit 4096 미만이므로 표본 수·5초 초과 개수 차이를 구할 수 있다.

| 자연 관측 구간 KST | 완료 평가 | 5초 초과 |
| --- | --- | --- |
| 종료 전 11:01:21.682~11:02:23.311 (61.628초) | 18 | 3 |
| 종료 후 11:03:21.398~11:04:22.257 (60.859초) | 53 | 0 |

처리량은 이 구간에서 분당 약 17.5→52.3회로 증가했다. 시장 입력 부하가 통제된 실험은 아니므로 전체 성능의 인과 개선율이나 모든 지연 해소로 확대하지 않는다. 누적 p95는 정지 전 표본을 포함하므로 정지 후 전용 p95로 제시하지 않는다. 정책 준비 실패는 두 구간 모두 누적 0이다.

## 증빙·검토

`data/report/episode_permanent_off/2026-10-08/`의 `before-force-stop.json`, `force-stop-operations.json`, `unit-census.json`, `after-unit-verification.json`, `main-performance-observations.json`에 읽기 전후 증빙을 보존했다. root unit 조작 상세는 위 `/etc/korstockscan` 보존 디렉터리의 `operations.json`이다.

정지 전 service identity/ExecStop/Restart/cgroup을 확인하고 정확한 episode unit만 대상으로 했다. 종료 후 실제 PID, kernel lock, 설치 mask, loaded service/timer 상태, Main 지속 실행을 재확인했다. 주문 API·AI·장후 재실행을 하지 않았다. 애플리케이션 코드 변경이 없어 pytest/compile은 이 운영 변경의 검증으로 실행하지 않았으며, 문서 print-only parser·diff 검사를 수행했다. 전체 기능 삭제와 과거 원장 flat 대사는 완료했다고 표시하지 않는다.
