# 9/8 전체 변경 병합·우아한 재기동 검증

사용자 지시: `전체 커밋&푸시&main 병합 후 우아한 재기동`. 실행·관찰 기준: 2026-09-08 12:31~12:33 KST. 범위는 검증된 작업 트리의 원격 반영과 메인 봇 표준 재기동이며 위젯·에피소드의 독립 주문 owner, 실효 정책, 수량·가격·threshold·provider·hard safety는 변경하지 않았다.

## 판정

커밋·푸시·main fast-forward 및 메인 봇 재기동을 완료했다. 실행 소스 커밋은 `b27a67dcf2bc00bb2c552b55be6ff25fda07f389`, 새 PID는 `682672`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`다. 당일 runtime env/PID 검증 PASS, 기존 PID 종료·단일 main·WS LOGIN/0B/0D·REST 잔고/미체결 응답과 owner 보존을 확인했다. 이는 배포·기동 수용이며 장후 자연 generation 또는 EV/순이익 개선 완료가 아니다.

## 통합 검토와 Git

- 직전 #74/#89 검증과 함께 현재 main에 병합된 WS ingress snapshot 보완·BUY Funnel/Entry recheck, 직접 producer/consumer, restart race/Samsung authority handoff를 재검증했다. **22개 테스트 파일 1,606 passed (29.89s)**, 기존 pandas Copy-on-Write deprecation warning 1개다. 패키지를 설치·업그레이드하지 않았다.
- 전체 Black 검사 893개 파일 변경 불필요, staged Python compile, `restart.sh`/`src/run_bot.sh`/postclose wrapper `bash -n`, staged/worktree diff 검사, 문서 print-only parser(32개) 통과. 검토 범위 미해결 코드 finding 0.
- 코드·문서·당시 보고서/캐시 snapshot 26개 파일을 `codex/ws-quality-release-20260908`에서 위 커밋으로 생성·push한 뒤 main을 동일 커밋으로 fast-forward하고 `origin/main` push를 확인했다. 장중 자동 갱신 보고서는 checkout/stash로 덮어쓰지 않았다.
- 원격 [브랜치 Black CI](https://github.com/JaehwanPark/KORStockScan/actions/runs/34183514775)와 [main Black CI](https://github.com/JaehwanPark/KORStockScan/actions/runs/34183575368) 모두 success를 확인한 후 재기동했다.
- 운영 계좌·registry·policy 경로를 담은 미추적 `data/runtime/symbol_owner_policy/owner_custody.env`는 로컬 운영 설정으로 그대로 보존하고 원격 커밋에서 제외했다. ignored runtime/raw/env/token도 강제 추가하지 않았다. 자연 운영 파일은 커밋 뒤 다시 바뀔 수 있으며 코드 source dirty와 구분한다.

## 우아한 재기동과 정책 보존

| 항목 | 확인 결과 |
| --- | --- |
| 표준 실행 | `./restart.sh` 1회, exit 0 |
| 종료·기동 | 12:31:20 restart flag 요청/기존 PID 감지 → 기존 PID461794 종료 → 12:31:29 새 source receipt/PID682672 |
| supervisor | PID20215 유지. loaded/current launcher SHA256 `648b3cd86264d72d46b9c7ee8e8d175072a3f646ebe70425f73afc95b919cf1b` 동일 |
| 실행 코드 | 기존 `f67a7ec7` → `b27a67dc`; 새 PID source dirty=false |
| 당일 verify | status=pass, pid_passed=true, selected20, pid_missing/pid_mismatches/findings 모두 빈 배열, runtime-policy/dated-override/unverified-family fail 0 |
| verify artifact | `data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-08.json`, SHA256 `482284b10ca143df83a3b68f7cd9984950e4eafd2ce33e480c16cbbb18cc9d07` |
| 삼성 오전 handoff | 서비스가 정상 종료 상태이므로 prepare/commit 모두 `not_required / morning_owner_not_active`. authority를 새로 만들거나 종료된 owner를 기동하지 않음 |
| 단일 실행 | 새 main 1개, 기존 `/proc/461794` 부재, restart flag/임시 handoff plan 정상 소비 |

당일 threshold runtime env SHA256 `f529bb62dd1c75579d2506017d479629aa41595b648805f3b4954795800ee6bc`, owner env SHA256 `f56acd661eb83f07285fb56bf445c71ef2ad58fffdf39bedf58675320137a516`, symbol-owner policy SHA256 `d66f33b524fbba316ee32a8260527e8c2eb7ef1349dc6c929976e2236cea3f07`은 재기동 전후 동일했다. 신규 PREOPEN 후보 적용·수동 env/lock 변경·provider 변경을 수행하지 않았다.

## Broker·독립 owner 대사

재기동 직전 12:31:06.409090과 직후 12:31:46.820631의 KRX/NXT strict 잔고와 전시장 미체결을 기존 cached token만 사용하는 읽기 경로로 조회했다. 보조 조회에서는 신규 token 발급·auth refresh를 금지했고 주문·취소 API를 실행하지 않았다.

| Owner | 보유 전/후 | 미체결 전/후 |
| --- | --- | --- |
| widget_auto_trade:005930:2026-09-08 | 삼성전자10주 / 동일 | target SELL0038063, 주문10/체결0/잔량10 / 동일 |
| episode:samsung_heavy_morning:010140:2026-09-08 | 삼성중공업10주 / 동일 | target SELL0018672, 주문10/체결0/잔량10 / 동일 |
| main/기타 | main 보유0, 미체결 BUY0 / 동일 | 다른 주문 생성·흡수 없음 |

- 두 snapshot의 `as_of`만 제외한 정렬 JSON이 완전히 동일하고 SHA256은 `dc4c250f78bfd92a06cd9a6def16057fc6c33faef89abe7f1a59d3a664115400`이다. 정확한 local 비교 근거는 `/tmp/ws-quality-release-20260908-broker-immediate-before.json`, `/tmp/ws-quality-release-20260908-broker-after.json`이다.
- order owner registry는300행, SHA256 `ba69c77de047954df02a126bad7e86949e83d46fc3e1ef4d08ccc49a6b26a91e`로 전후 동일했다. 주문번호 owner 충돌0이며 수량·custody 이동이나 신규 주문 receipt가 추가되지 않았다.
- 위젯 실매매 PID21846과 삼성중공업 episode PID453121은 전후 동일하고 active/running이다. 독립 매매 service·collector를 중단/재기동하지 않았다.

## 기동 후 자연 확인과 남은 경계

- 12:31:42 메인 잔고/DB 동기화 완료, 12:31:44 WS 연결·LOGIN ACK, 12:31:48 이후0B/0D 첫 데이터 수신을 확인했다. 12:31:59 snapshot은 신규 registration receipt와23종목, received types0B/0D/0F/0w를 보존했다.
- 12:32:12 heartbeat는 새 PID682672이며 기록된 telegram/crisis/sniper/scanner/error detector worker 모두 alive=true다. 메인/WS/scanner/order 관련 error log에는 재기동 이후 새 오류가 없었다.
- 신규 micro collector는12:32:04 trade680/depth856에서12:32:44 trade2400/depth3466으로 증가했다. 후자는 `healthy_observer_canary`, callback p95=0.099671ms/p99=0.116226ms, trade/depth queue-full·worker/writer 오류와 stale exchange rejection0, trade/depth writer alive2/2다. snapshot 시점 main WS TCP Recv-Q도0이었다. 짧은 자연 관측이며 장마감까지의 처리성능이나 순이익 개선량으로 외삽하지 않는다.
- 1,606개 통합 검증·배포·PID 소비는 닫았으나 과거 ingress loss/원천 결손 복원, Main AI Provider hold, source-quality final audit·WS finalize의 다음 자연 장후 generation, 실제 submit/fill/terminal·비용 EV는 기존 체크리스트 owner에서 계속 확인한다. 경제성 미관측을 이유로 새 주문·재생성·재기동을 추가하지 않는다.
- Git의 기존 loose-object GC 경고는 commit/push를 차단하지 않았다. 이번 작업에서 git prune·강제 history 정리·force push는 하지 않았다. 외부 Project/Calendar sync도 실행하지 않았다.

이 실행 기록과 이후 자연 보고서 snapshot을 보존하는 후속 커밋은 문서/데이터만의 변경이다. 실행 코드 커밋과 문서 기록 커밋의 차이는 소스 미반영이나 추가 재기동 필요성을 뜻하지 않는다.
