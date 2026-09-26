# 2026-09-25 스캘핑 익절 기계판정 메인 릴리스 선택 영수증

2026-09-25 18:29 KST에 사용자 승인 범위로 M1 익절 강약 기계판정·이벤트 시각 첫 crossing·장후 3수익축/분류기 연구 코드를 불변 릴리스에 고정하고 메인 selector를 전환했다. 메인 bot 재시작, 임계값 수동 변경, 실주문, 독립 위젯/에피소드 소유자 전환은 수행하지 않았다.

| 항목 | 확인 결과 |
| --- | --- |
| 선택 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/scalp-trailing-mechanical-20260925-6c82414c` |
| 선택 Git commit | `6c82414ce2d2b511d7299b1fc86173714db83dfa` |
| 이전 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/scalp-trailing-full-review-20260925-f6f34986` / `f6f34986acec47e549082a3490ce1cf14bf9ac51` |
| 선택 영수증 | `data/runtime/runtime_release_selection.json`, 이전 내용 `tmp/runtime-release-selection-before-scalp-mechanical-20260925.json` |
| 공유 경로 | `data`, `docs`, `logs`, `tmp`, `.venv`, `restart.flag`는 canonical workspace를 가리킴 |
| 소스 일치 | 변경된 source 21파일의 workspace/release SHA256 일치, release `src/deploy/restart.sh` 청결 |
| 전환 전·후 release-set | 둘 다 `passed`; 전환 후 선택 root/commit은 위 값. 독립 unit policy pin 실패 0건 |
| 메인 PID | 없음, `not_attested`. 실제 PID 소비·자연 수익성은 미확인 |

코드 검토와 계산 근거는 [구현 검토](2026-09-25-scalp-trailing-mechanical-strength-implementation-review.md)에 기록했다. 영향 범위 pytest 526건 통과, 변경 전 HEAD에서도 재현되는 NXT 주문 영수증 2건은 이 배포의 회귀 실패로 분류하지 않았다. 합성 완료 포지션 80건에서 event-time 첫 약폭 crossing을 재생했고 원천 결손 0건이었다. 실제 로그 I/O가 포함된 fast loop 성능과 자연 완료 포지션 비용 후 EV는 이후 관측 항목이다.

`bash deploy/run_runtime_release.sh restart --print-plan`은 새 root/commit으로 라우팅됐다. 이 명령은 경로 확인일 뿐 프로세스를 시작하지 않았다. 다음 실제 메인 기동 때 bootstrap의 기계판정 기준선 영수증, 정확 날짜 PREOPEN/런처 정책 검증, PID의 코드·정책 소비를 별도 확인해야 한다. 자연 0B/0D와 완료 체결·비용 표본이 없으므로 임계값 최적화 후보나 경제성 개선 승인은 하지 않았다.

현재 날짜 `docs/checklists/2026-09-25-stage2-todo-checklist.md`가 없어 당일 executable OPEN owner와 연결하지 못했다. 미래 2026-09-28 checklist를 대체 owner로 사용하지 않았다. 전환 시 장후 wrapper와 메인 bot은 실행 중이지 않았으며, 이전 selector와 릴리스는 되돌리기용으로 보존했다.
