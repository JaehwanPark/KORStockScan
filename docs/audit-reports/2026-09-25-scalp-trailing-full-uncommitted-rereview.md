# 2026-09-25 전체 미커밋 변경 재검토 및 릴리스 선택

## 결정과 범위

사용자가 승인한 전체 미커밋 소스·문서 25개를 다시 검토했다. 기계식 익절 강약 분류기, 첫 crossing, 3수익축 장후 재생, bootstrap, fast 감시, 보고서 소비자와 배포 문서가 범위다. [기존 구현 검토](2026-09-25-scalp-trailing-mechanical-strength-implementation-review.md)와 [첫 선택 영수증](2026-09-25-scalp-trailing-mechanical-strength-deployment.md)은 이전 단계의 기록이다. 이번 재검토의 새 릴리스 선택 결과는 아래에 기록한다.

## 재검토에서 수정한 결함

1. 분류기 상태가 symbol/transport epoch만 보고 유지되어 동일 종목의 route 또는 시장 전환 뒤에도 이전 STRONG 상태가 남을 수 있었다. position별 상태에 route와 시장을 묶고 전환 때 UNKNOWN 기준선부터 다시 쌓도록 수정했다. 런타임 로그·첫 crossing 신원과 장후 raw journal 재생도 같은 segment를 소비한다.
2. 전환 기준선에서 새 quote 시각을 보존하지 않아 다음 0D를 거짓 시각 단절로 분류할 수 있었다. 기준선 시각을 갱신하고, 청산 가능 시간이 아닌 시장의 입력 전이는 직접 TP 후보 경로에서 제외했다. 비청산 시간의 분류기 관측은 별도 journal에 남는다.
3. 연속된 두 0D가 같은 수신 밀리초를 가질 때 시퀀스가 정상이어도 이벤트 재생이 결손으로 처리했다. 단조 시각과 연속 시퀀스를 허용하고 동일 밀리초 회귀를 추가했다.
4. 복합축 상호작용 수식에 기준 정책의 비용 후 변화량을 명시적으로 포함시켰다. 후보·단일축·기준선은 같은 공통 비교 ID로 평가한다. 이 값은 보고 전용이며 자동 실거래 적용권이 없다.

## 검증과 잔여 경계

- 영향 범위 pytest: 512건 통과, 기존 NXT pending-submit context 테스트 2건 제외. 제외된 두 건은 변경 전 HEAD에서도 `pending_submit_integrated_venue_context_invalid`로 실패하며 주문 안전 차단을 약화하지 않았다.
- Python compile과 `git diff --check` 통과. 문서 backlog print-only parser는 26건을 읽었고 외부 Project/Calendar 동기화는 실행하지 않았다.
- 기존 합성 완료 포지션 80건 계산은 0.957초 wall / 0.951초 CPU / 41.5 MiB RSS, 원천 결손 0건이었다. 이 수치는 실거래 I/O와 자연 비용 후 EV를 증명하지 않는다.
- 현재 날짜의 `docs/checklists/2026-09-25-stage2-todo-checklist.md`가 없어 당일 executable OPEN owner 확인은 불가능했다. 미래 9/28 checklist를 오늘의 owner로 대체하지 않았다.
- 배포는 메인 selector와 예약된 메인 코드 경로에만 적용한다. 현재 메인 PID는 없으며 새 PID 소비, 9/28 정확 날짜 PREOPEN 정책 재생성, 자연 0B/0D 및 체결 완료 경제성은 별도 확인 대상이다. 기존 9/28 bootstrap은 이전 schema로 작성되어 새 코드의 read-only 검증에서 `scalp_trailing_mechanical_policy_receipt_missing`을 반환한다. 예정된 9/28 PREOPEN 생성·검증에서 새 영수증으로 교체해야 한다.

## 릴리스 선택 영수증

| 항목 | 값 |
| --- | --- |
| 선택 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/scalp-trailing-full-rereview-20260925-6060f5d0` |
| 선택 commit | `6060f5d0424193cdf747248224af1f9aac2ee90a` |
| 이전 릴리스 | `scalp-trailing-mechanical-20260925-6c82414c` / `6c82414ce2d2b511d7299b1fc86173714db83dfa` |
| selector 영수증 | `data/runtime/runtime_release_selection.json`, 이전 내용 `tmp/runtime-release-selection-before-scalp-full-rereview-20260925.json` |
| 선택 검증 | 전환 전·후 release-set `passed`, 독립 unit policy pin 실패 0건, `src/deploy/restart.sh` 청결, workspace/release 변경 소스 21개 SHA256 일치, cron 라우팅 확인 |
| 실제 PID 소비 | 없음; 다음 메인 기동의 별도 영수증 필요 |

되돌릴 때는 보존한 이전 selector와 릴리스를 같은 release-set 게이트로 검증한 후 선택한다. 선택 파일의 commit 문자열만 바꾸어서는 승인 상태가 복원되지 않는다.
