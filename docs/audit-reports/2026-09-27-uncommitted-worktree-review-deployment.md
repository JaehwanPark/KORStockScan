# 전체 미커밋 작업본 재검토·선택 릴리스 인계

실행일: 2026-09-27 KST. 사용자 지시의 S0 **이전** 배포 단계에 대한 증거 기록이다.

## 판정과 검토 범위

다른 세션의 [cap 깊이·후행 틱 replay 재리뷰](2026-09-27-initial-quantity-cap-depth-replay-review.md) 완료 후 작업공간의 추적 변경·미추적 source/test/docs를 선택 릴리스 `50ffc08ee976fb0cabb6cc23aae355ccfd8d7b02`와 바이트 단위로 대사했다. 당시에 42개 미커밋 경로가 있었고, 38개는 그 릴리스와 동일했다. 차이 4개는 `src/engine/scalping/avg_down_replay_capture.py`, `src/tests/test_sniper_entry_latency.py`, `src/engine/scalping/initial_quantity_policy.py`, `src/tests/test_initial_quantity_policy.py`였다. AVG_DOWN의 정책 snapshot 고정과 해당 회귀를 보존했다.

초기 수량 cap 후보 선택에서 같은 날짜들을 평가와 선택에 함께 쓰는 결손을 발견했다. 최신 `entry_date`를 독립 holdout으로 분리하고 그 이전 날짜만 train으로 사용하도록 수리했다. 최소 날짜/paired 모수, train·holdout 각각의 coverage, train 양의 순증분·가중 우위, holdout 및 각 날짜 비음수 증분을 선택 조건으로 적용했다. 전체 모수만 충분한 경우를 거절하는 회귀를 추가했다. 기존 활성 v2 정책값과 실주문 권한은 바꾸지 않았다.

## 검증·배포

| 단계 | 직접 확인 |
| --- | --- |
| 코드/검토 | 영향 회귀 299건 및 초기 수량/주문/장후 경로 239건 PASS; 불변 릴리스에서 cap 선택 표적 3건 PASS. Ruff·compile·`git diff --check`·`bash -n deploy/run_threshold_cycle_postclose.sh`·문서 print-only parser PASS. 기존 `test_sniper_scale_in.py` SELL fixture의 21건 실패는 선행 릴리스 리뷰에서 이미 확인한 별도 미해결 범위다. |
| 불변 source | `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-review-holdout-20260927`, commit `9a03c939aa1aff3830057d855ebbdbc955793f89`; 해당 worktree `src/deploy/restart.sh` clean. 이후 작업공간의 모든 미커밋 `src/deploy/restart.sh` 경로를 다시 비교했으며 차이 0개. |
| 선택 | release-set 잠금과 직전 `50ffc08e…` compare-and-swap 아래 `data/runtime/runtime_release_selection.json`을 19:07 KST에 `9a03c939…`로 전환. 이전 선택 백업 `tmp/runtime-release-selection-before-holdout-review-20260927.json`. 기존 초기 수량 current/policy SHA 유지. |
| 경로 | `bash deploy/run_runtime_release.sh --check-release-set`: PASS, main PID null, episode 122개 inactive·policy pin 366/366; `--check-cron`: 8 필수 target PASS. |

선택 릴리스는 **코드/경로 배포**다. 정상 9/28 PREOPEN·start, 실제 main PID의 해당 코드·정책 소비, 자연 주문/체결/terminal, 비용 후 성과는 발생 후 별도로 대사한다. 기존 SELL fixture 실패와 전체 장후 성능·자연 수용은 이 문서의 PASS 범위 밖이다. 서비스 재기동, 정책 pointer 변경, 실주문, 정규 장후작업은 이 인계에서 실행하지 않았다.
