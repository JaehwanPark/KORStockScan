# 2026-09-09 정오 전체 커밋·main 반영·우아한 재기동

## 판정과 권한

사용자의 `전체 커밋&푸시&main 병합 후 우아한 재기동` 요청을 실행했다. 메인 봇의 배포·재기동 검증은 완료했다. 현재 정책의 경제성, submit drought 해소 또는 독립 매매기계 전체의 효과 검증을 완료했다는 의미는 아니다.

시작 브랜치는 이미 `main`이었다. 원격 변경을 fetch한 결과 local ahead3/behind0이어서 별도 가상 merge commit을 만들지 않고, 전체 변경63개 파일을 `9b64f868136adddc26328e64246b0e9b4f3b2543`으로 커밋해 기존3개 커밋과 함께 non-force push했다. 원격 `refs/heads/main`의 동일 SHA 및 ahead0/behind0을 확인한 다음 표준 [restart.sh](../../restart.sh)를1회 실행했다.

일반 Git 추적 범위의 코드·테스트·문서·당일 report/cache snapshot을 포함했다. ignored 원천/비밀 설정은 강제 추가하지 않았다. `data/pipeline_event_summaries/pipeline_event_producer_summary_manifest_2026-09-09.lock`은 실행 중 생성되는 임시 mutex marker라 커밋하지도 삭제하지도 않았다. 정기 producer가 이후 갱신하는 report/cache를 source-dirty 또는 배포 실패로 해석하지 않는다.

## 배포 전 review gate

`korstockscan-review-gate`에 따라 producer/consumer·source-only 권한·AI 입력 투영·현금 cap·재기동 owner 계약과 기존 수정 리뷰를 확인하고 통합 검증했다. 관련35개 모듈 **1,960 tests PASS**, 변경 Python41개 compile, `bash -n restart.sh src/run_bot.sh`, diff check 및 print-only 문서 parser PASS(36 tasks)다. 기존 pandas Copy-on-Write deprecation warning1건은 실패와 분리한다.

최초 형식 검사에서 기존4개 파일을 Black26.5.1로 정리했고 AST 동일성을 확인했다. 그중 `canary_monitor.py`의 바이트 변화로 frozen-baseline compatibility 테스트1건이 실패하여, 원래 측정 receipt와 두 AST pin을 보존한 채 reviewed replacement byte hash만 갱신했다. 위1,960 PASS는 이 보완 이후 전체 재실행 결과이며 반복 실행 횟수를 합산하지 않았다.

초기 원격 [Black 실행](https://github.com/JaehwanPark/KORStockScan/actions/runs/34306727569)은 `machine_entry_timing_tuning.py` 함수 선언 한 줄의 wrapping 때문에 실패했다. 로컬 캐시를 사용하는 전체 검사는 PASS였으나 `--no-cache --check --diff`로 원격 실패를 재현했다. 해당1개 선언을 형식만 정리하고 AST 동일성·compile·직접 timing58 tests 및 캐시 없는 전체 Black911 files PASS로 보완했다. 후속 커밋은 이 형식·검증 기록·자연 report snapshot이며 매매 알고리즘 변경이나 두 번째 재기동을 필요로 하지 않는다. 원격 최종 상태는 후속 main HEAD의 Black receipt를 기준으로 판정한다.

## 재기동·현재 PID receipt

| 항목 | KST 관측 결과 |
| --- | --- |
| 이전 main | PID190811, 10:44:51 시작, source commit15a8a4ed |
| 요청 소비 | 12:20:46 restart flag 발행, 12:20:47 기존 main이 감지·자체 종료 |
| 새 main | PID310359, 12:20:56 시작, runtime commit9b64f868, source_dirty=false |
| 표준 실행 | `restart.sh` exit0, 기존 PID 종료 후 새 PID 생성; forced kill/직접 bot 기동 없음 |
| supervisor | PID12159 유지. 로드된 launcher와 현재 `src/run_bot.sh` SHA256 일치 |
| exact-date verify | target9/9, PID310359, status=pass, passed/pid_passed=true, selected18, runtime-policy/dated-override/unverified fail0 |
| WS | 12:21:16 LOGIN ACK, 이후 자연0B·0D 첫 수신 확인 |
| 진행 | 12:21:38 main heartbeat와 telegram/crisis/sniper/scanner/error threads alive 확인 |
| Samsung morning handoff | prepare/commit 모두 `not_required: morning_owner_not_active`; 별도 machine 권한 발급 없음 |
| 독립 owner | 확인한 위젯/collector·low-price10개 running unit의 MainPID·active/running 불변; 별도 재기동 없음 |

직접 근거는 `logs/bot_history.log`, `tmp/error_detector_heartbeat.json`, [당일 runtime verifier](../../data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-09.json)다. 동적 파일은 이후 정상 owner가 갱신하므로 이 기록의 시각/PID와 구분한다.

## 계좌·주문·정책 보존

기존 read-only helper와 cached token으로 12:18:23 및12:21:42에 KRX/NXT 잔고와 complete 미체결 snapshot을 대사했다. 인증 신규 발행·주문·취소·수동 원장 변경은 실행하지 않았다.

- 보유6종목: 005930 25주, 010140 10주, 015760/035720/042660/181710 각20주. 모두 registry quantity와 일치하고 external remainder0이다. 005930은 widget custody, 나머지는 각 독립 episode custody이며 main 보유0이다.
- 미체결 매도9건/매수0건의 주문번호·수량·잔량·route가 동일하다. snapshot SHA256은 전후 모두 `80ffc619fbce235594b760bb045b050d3fa2f65d7b334f0314dfe98f3b00814b`다.
- **기존 미대사:** 010140 SELL0001493/10주의 exact 주문번호는 registry에 없다. 과거부터 존재한 상태이며 main 또는 다른 자동 target으로 추정하지 않고 그대로 보존했다. 다른8개 주문은 exact episode position과 결속된다. 수량 대사 성공을 이1건의 주문 귀속 완료로 확대하지 않는다. 기존 [오전 재기동 기록](./2026-09-09-graceful-main-restart-review.md) 및 당일 custody acceptance를 유지한다.
- 다음6개 파일은 전후 hash가 동일했다. 모든 운영 파일의 전수 무변경을 주장하지 않는다.

| 파일 | SHA256 |
| --- | --- |
| `data/runtime/order_owner_registry.jsonl` | `f89094837dcb948fd22bed7e296e2076798639441983b385ea201d44f379a62c` |
| `data/runtime/symbol_owner_policy/owner_custody.env` | `4e5e742ae9cbbfeaea6dff1c1b8cd80b2aad1656d7a6fb3a78ac76d1a8b5f89c` |
| `data/runtime/symbol_owner_policy/symbol_owner_policy_2026-09-09.json` | `cb24152c69a8885dd518279909f2dc2e0d8f7488a62e26489431a9e3bc3ffc02` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.env` | `ed11902d30be836f5fd792ded90fd118f08442de9f7d903695a321829b7c35a3` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.json` | `a5f800eec8a17e3024e771bdb3e25d4238f35c4ea6e0aceac679da4120892129` |
| `src/run_bot.sh` | `32efc0cc145b78db658357812113e51cb88a643374cd070d9a48b5a2cb481c85` |

## 새 코드의 자연 소비와 남은 경계

재기동 후 읽은 마지막1,800 event line 범위에서 새 source fetch census10건과 candidate-pool census1건, 총11건이 `decode_receipt`의 권한/hash/보존식 검증을 통과했다. 최초 fetch12:21:11, pool12:21:30, 같은 `SCANSRC-1788924069506882239`에 결속됐으며 pool output287건이다. 새 PID의 hook·자연 계측은 확인했으나, 전체 시장 포착률 정상·실제 submit 증가·비용 차감 수익 증가의 근거로 전용하지 않는다.

장후 보고서·다음 PREOPEN 선택, 새 cash-capacity 진단과 실제 AI payload 소비, 비용 후 EV는 [당일 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `ScannerLookupAttentionNaturalEvidence0908`, `EntryRecheckNaturalAttribution0907`, `AIDecisionActionOutcomeNaturalEvidence0908` 등에서 이어간다. 새 중복 OPEN이나 추가 승인 floor를 만들지 않았다. 정책값·provider route·order/quantity/hard safety·operator lock을 수동 변경하지 않았다.

GitHub의 loose-object gc 경고는 fetch/commit/push 실패가 아니었다. 증거 손실 가능성이 있는 prune/gc 정리는 이번 배포에 포함하지 않았다. 외부 Project/Calendar sync는 실행하지 않았으며 필요한 경우 사용자만 아래 표준 명령을 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
