# Kiwoom 8005 과거 로그 재탐지 보완 — 2026-10-12

## 판정과 원천

07:00:13 경보의 원문은 `kiwoom_utils_info.log`의 **2026-10-09 22:36:36 ka10080 인증8005** 한 건이다. 당시 Main은07:55 기동 전 비가동이었다. 감시기 fresh는 미소비 file offset 기준이었고 Main identity가 없으면 과거 로그 시각을 분리하지 않았다. 따라서 읽지 않은 금요일 오류가 월요일 새 장애로 오인돼 token cache 무효화와 빈 restart.flag가 생성됐다. [원 경보 원문](../../tmp/auth-8005-history-repair-20261012/alert-0700-excerpt.txt), [정정 전 감시 상태](../../tmp/auth-8005-history-repair-20261012/auth-state-before-correction.json)를 보존한다.

## 보완·원상 영향 정리

[auth detector](../../src/engine/error_detectors/kiwoom_auth_8005_restart.py)는 KST 당일00:00 및 유효한 서버 boot 경계보다 이전인 timestamped row를 historical evidence로 분리하고 원 samples를 남긴다. boot 한 초 전 경계를 사용해 같은 초 startup 오류를 숨기지 않는다. 역사 row만 있으면 PASS이며 token invalidation·restart flag·일일 횟수 소모를 하지 않는다. 현재 오류·시각 미상 행·동일 요청 retry/handoff·PID 이전·cooldown/cap의 기존 계약은 유지한다. 분리는 bounded scan에서 선형으로 수행하며 Kiwoom HTTP/WS request·retry·인증 발급 프로토콜은 변경하지 않는다.

07:21:23에 기존 detector lock과 Main restart guard lock을 함께 잡고 live Main 없음, flag의07:00:13 mtime/inode·빈 bytes, 감시기의count1/원 last_restart_ts와07:20:07 auth PASS를 대사했다. 그 오탐 flag만 철회하고 부당 차감1회를0회로 정정했다. 파일 offsets와 원 last_restart_ts 및 원 실패 경보를 보존하며 정정 receipt를 남겼다. [정정 근거](../../tmp/auth-8005-history-repair-20261012/false-request-withdrawal.json). 과거 token은 복원하거나 수동 발급하지 않는다. 당일 발급은 기존 정상 scanner/Main 시작 owner가 수행한다. 봇 조기 기동/재기동·주문은 실행하지 않았다.

## 공식 원천·리뷰·검증

공식 Kiwoom upstream HEAD는 `953e5dbff123f437ab4d11a78a95191a685eb51f`이며 이번 변경 전에 재조회했다. `kiwoom_docs`가 없는 tree임을 확인했고 `kiwoom/core/auth.py`의 OAuth2 발급·캐시·인증 실패 복구, `kiwoom/core/client.py`, `kiwoom/specs.py`를 대조했다. [조회 시각·경로](../../tmp/auth-8005-history-repair-20261012/official-reference.json)에 기록했다. 공식 request를 실행하거나 SDK를 설치하지 않았다.

workspace 관련 회귀174 passed. 실제09일 원문/no-PID·preboot row·역사/현재 혼합·KST day/boot 경계와 기존 정상 retry·cap/cooldown·runtime PID 계약을 검증했다. 새 불변 release는 `auth-history-guard-20261012-v1` / `5f9309222d837baf7227edcc8b4b60ff85bdfef1`이며 배포/정식 인계와 자연 인증 결과는 후속 근거로 구분한다. [작업 근거](../../tmp/auth-8005-history-repair-20261012/).

## 실제 배포·정식 인계 결과

- workspace와 불변 release에서 각각174 passed다. 동일 묶음이므로 합산하지 않는다. 실제 선택 코드에09일 원문을 미소비 상태로 격리 재생해 historical1/PASS와 flag/invalidation false를 확인했다. [선택 코드 원문 재생](../../tmp/auth-8005-history-repair-20261012/selected-code-original-row-replay.json). runtime/test2개 파일의 workspace/release SHA가 검토본과 동일하다.
- [CAS 인계](../../data/runtime/research_release_transition/auth_historical_replay_repair_20261012_v1/transition.json)는 verified이며 원 source10/8·publication10/11·effective10/12를 유지했다. summary/checklist→strict/controller→PREOPEN을 새 release에 결속했고 native 최종화는 **07:30:26 KST DONE, exit0**이다. [최종 준비](../../tmp/auth-8005-history-repair-20261012/final-readiness.json)는07:31:25 기준 current_full_contract PASS·finalization issues0·필수 cron8개 및 release-set PASS다. 수동 복구가06:50 마감 뒤여서 recovered_late warning을 보존하며05:35 자연 완료로 바꾸지 않는다.
- 최종 native 인증 감시는07:30:25 PASS, operational_mutations=[]이다. 원 EOD·기계/보조·최초수량·holding/stop/trailing/delay 정책값과05:35 실제 cron은 그대로다.07:35 PREOPEN·07:55 Main은 새 root/commit을 소비하도록 준비됐으며 실제 Main PID는 아직 미관측이다.
- [토큰 metadata 점검 근거](../../tmp/auth-8005-history-repair-20261012/token-cache-metadata-only.json)는 기존 스캐너 시작 경로가12일07:20:06에 갱신한 당일 cache를 확인한다. token/appkey/secret 내용은 출력·백업하지 않았으며 수동 OAuth·provider·주문·봇 재기동은0이다. 당일 cache 존재를 Main의 실제 REST/WS 소비 성공으로 확대하지 않는다.
- 문서와 print-only parser, 기존 DirectFamilyPreopenPolicyHandoff 단일 owner를 대사했다. 외부 Project/Calendar sync는 실행하지 않는다.
