# 2026-09-09 13:46 메인 우아한 재기동

판정: 사용자 `우아한 재기동` 지시에 따른 메인 재기동·기동 검증 완료. 전략 경제성·submit drought 해소 또는 적응형 청산 실거래 활성화를 의미하지 않는다.

## 실행 소스와 검증

앞선 시도에서 병행 세션의 브랜치/index 변경 때문에 재기동을 보류했다. 이번 실행 전에는 현재 브랜치 `main`, HEAD/local main/원격 `refs/heads/main`이 모두 `5bbee288fb30e1946ecbb58203be25dd12ec1fb4`로 일치했다. 이전 검증 커밋 `74de6880`과 최종 merge의 tree diff는 없고 `src/deploy` 미커밋 변경도 없었다. 자동 생성 report/cache와 mutex marker는 보존했으며 Git 정렬·reset·추가 commit/push를 실행하지 않았다.

13:49 최종 확인에서는 병행 세션의 `adaptive_exit/decision.py`, `models.py` 수정 및 신규 `source.py`가 보였다. 이는 재기동 후 작업 상태로 보존했으며 이번 검증·배포 완료 범위에 포함하지 않는다. startup `source_dirty=false` receipt를 현재 worktree까지 clean이라는 주장으로 확대하지 않는다. 추가 재기동은 실행하지 않았다. 13:49:12에도 PID412924 heartbeat와 5개 thread alive가 유지됐다.

`korstockscan-review-gate`로 커밋된 소스와 기존 Entry AI/adaptive-exit 리뷰의 범위, 직접 restart/authority handoff 계약을 확인했다. 재실행한 restart flag 및 Samsung handoff 회귀 **17 PASS**, `bash -n restart.sh src/run_bot.sh`와 `git diff --check` PASS다. 코드 수정은 없었다. 기존 전체 기능 테스트 횟수를 이번 실행 횟수에 합산하지 않는다.

## 재기동 receipt

| 항목 | KST 관측 |
| --- | --- |
| 요청·자체 종료 | 13:46:29 표준 `./restart.sh` 1회; 이전 PID310359가 flag 감지·자체 종료 |
| 신규 메인 | PID412924, 13:46:38 시작, source commit `5bbee288`, `source_dirty=false` |
| supervisor | PID12159 유지. launcher 로드 commit `2c9731fe`는 역사적 시작 provenance이며, 로드된 `run_bot.sh` SHA와 현재 파일 SHA가 동일하여 supervisor 교체 불필요 |
| exact-date 검증 | target 2026-09-09/PID412924, `status=pass`, `passed=true`, `pid_passed=true`, selected18, missing/mismatch/unverified/runtime-policy/dated-override 실패0 |
| 완료 | `restart.sh` exit0; Samsung prepare/commit 모두 `not_required: morning_owner_not_active`; restart.flag 소비 완료, 기존 PID 종료 및 singleton 확인 |
| 연결·진행 | 13:46:51 계좌 동기화 완료, 13:46:52 WS LOGIN ACK, 13:47:25 자연0B/0D 수신, 13:47:41 새 PID heartbeat·5개 thread alive |

직접 근거: `logs/bot_history.log`, `tmp/error_detector_heartbeat.json`, [exact-date verify](../../data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-09.json). 동적 산출물의 이후 갱신은 위 시각/PID와 구분한다. 현재 정책·provider·수량·cap·operator lock·안전 guard를 수동 변경하지 않았다. 강제 kill, 별도 bot 기동, 장후 체인 재실행은 하지 않았다.

## 재기동 전후 보존

13:46:18 / 13:47:07의 cached-token 기반 기존 read-only REST helper로 KRX/NXT 잔고 및 complete 미체결 snapshot을 대사했다. 보유는 005930 25주, 010140 10주, 015760/042660/181710 각20주로 동일하며 모든 종목의 registry 수량 대사는 balanced/external remainder0이다. main 보유0, widget/episode custody를 유지했다.

미체결 SELL7/BUY0의 주문번호·수량·체결량·잔량·route 및 exact owner 조회 결과가 동일했다. 순서 정규화된 holdings/orders JSON의 SHA256은 전후 모두 `81d6229dd807402121b2dad36435e9a805cc86e29ef40fde71e33e7f2b385ca7`다. **010140 SELL0001493/10주의 exact registry 주문 귀속 미대사1건은 이전부터 존재**하며 임의로 main에 귀속하거나 취소하지 않았다. 다른6건은 해당 episode에 결속됐다. 기존 [정오 배포 기록](./2026-09-09-midday-main-deployment-review.md)의 미대사와 같은 항목이다.

검사한 독립 위젯/collector·Samsung/low-price service12개의 MainPID·active/running 상태가 전후 동일했다. 이들 프로세스는 재기동하지 않았다. 다음6개 파일도 전후 SHA가 동일했다.

| 파일 | SHA256 |
| --- | --- |
| `data/runtime/order_owner_registry.jsonl` | `be3494e6d73e94dd877112a078cf9d424123bfebf6af2bbca82aca175495861a` |
| `data/runtime/symbol_owner_policy/owner_custody.env` | `4e5e742ae9cbbfeaea6dff1c1b8cd80b2aad1656d7a6fb3a78ac76d1a8b5f89c` |
| `data/runtime/symbol_owner_policy/symbol_owner_policy_2026-09-09.json` | `cb24152c69a8885dd518279909f2dc2e0d8f7488a62e26489431a9e3bc3ffc02` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.env` | `ed11902d30be836f5fd792ded90fd118f08442de9f7d903695a321829b7c35a3` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.json` | `a5f800eec8a17e3024e771bdb3e25d4238f35c4ea6e0aceac679da4120892129` |
| `src/run_bot.sh` | `32efc0cc145b78db658357812113e51cb88a643374cd070d9a48b5a2cb481c85` |

## 후속 경계

Entry AI 코드 배포와 실제 입력·판단 개선/비용 후 순이익 검증은 별도다. 자연 소비와 경제성은 [당일 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `AIDecisionActionOutcomeNaturalEvidence0908`, `EntryRecheckNaturalAttribution0907`에서 확인한다. 적응형 청산은 [기존 구현 리뷰](./2026-09-09-widget-episode-adaptive-exit-implementation-review.md)의 오프라인 부분 구현 상태 그대로이며 실거래 adapter/PREOPEN authority는 활성화하지 않았다. 새로운 중복 OPEN을 만들지 않았다.

문서 review·print-only parser PASS(36 tasks) 및 diff check PASS로 기록 정합성을 검증했다. 이번 재기동 범위의 미해결 finding은 없으며 기존 주문 귀속 미대사와 전략 자연 acceptance는 위와 같이 분리한다. Project/Calendar sync는 실행하지 않았으며 필요할 때 사용자만 아래 명령을 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
