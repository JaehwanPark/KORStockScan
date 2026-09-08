# 9/9 코드 재리뷰·위젯/에피소드 승인 추천 구현

기준 시각: `2026-09-09 00:29 KST`. 장후 원천 거래일은 `2026-09-08`, 신규 승인 profile의 effective date는 `2026-09-09`다.

## 판정

사용자의 `코드리뷰 후 수정보완, 결함이 없을 때까지 반복` 및 `위젯/에피소드 기계 추천사항 구현 승인`을 실행했다. `$korstockscan-review-gate`에 따라 아래 변경과 직접 producer/consumer를 재리뷰하고 보완했으며, 최종 해당 범위 미해결 finding은 0이다. 관련 **975 tests PASS**, compile 및 diff 검사 통과. 전체 저장소의 무관한 dirty 변경을 이번 승인·검증으로 포괄하지 않는다.

경제성 gate를 통과한 **기존 저가주 profile 2건을 구현**했고, widget080220의 기존 9/9 정책·로더를 다시 검증했다. 실제 low-price PREOPEN applied/PID 소비와 신규 실수익은 아직 관측 전이다. 원천 증거 차단 workorder와 보류 추천을 구현 완료로 바꾸지 않으므로 종합 상태는 **YELLOW**다.

## 반복 리뷰와 보완

| 발견 사항 | 보완·검증 | 남은 경계 |
| --- | --- | --- |
| BBO 보고서가 세션 종료 전 단축 수집 일정도 고정 10회로 요구 | 기존 collector가 발급한 exact scheduled count와 마지막 sample index를 소비. 6/9/10회, 문자열 receipt, 중복 event·mirror 회귀 통과 | 1,200초 경제성 horizon이나 시세 요청·수집량·runtime guard는 변경하지 않음 |
| mirror 결속 중 후행 metadata conflict 또는 명시적 null count가 가려질 수 있음 | 모든 conflict를 전달하고 null/잘못된 count·authority·terminal은 fail-closed. cache v15로 이전 요약 재사용 차단 | 과거 미완료 schedule은 합성하지 않음 |
| 새 profile revision 적용 시 승인 대상 밖의 기존 실제 보정 정책까지 baseline으로 초기화 | 9/8→9/9 전환에서 승인된 2개만 새 baseline을 사용하고 나머지는 검증된 actual runtime binding을 보존. 삼성중공업 보정값 보존 실패 회귀를 수정 후 재통과 | 기존 source-date·quantity·격리·operator/custody 계약 유지 |
| 추천 전수 대사의 sparse-first mirror가 후행 authority 충돌을 숨길 수 있음 | native inventory 검증 helper가 모든 mirror 위치·관측 필드를 대사. native ID 변조·누락·충돌을 차단하고 원본은 수정하지 않음 | 이 helper는 ID/증거 검증이지 승인 또는 실주문 consumer가 아님 |
| 다음 확인 5개 owner가 전일 OPEN에만 남아 현재-day parser에 전달되지 않음 | 동일 ID·Acceptance·과거 이력을 오늘 AUTO 블록 밖으로 이관하고 전일 OPEN은 비완료 이관 기록으로 변경 | 현재 5개 ID 각각 1개로 파싱, 모두 해당 window 전 `not_yet_due` |
| 새 preflight 필수 JSON evidence가 전역 ignore에 가려짐 | 필요한 날짜의 evidence·승인 ledger 2개 경로만 `.gitignore` 예외로 노출하고 원본 자료/비밀정보의 ignore는 유지 | 후속 커밋 시 필수 evidence 누락 방지. 이번 턴 커밋·푸시 없음 |

초기 확인 중 “저가주 추천 4건 누락”이라고 알린 내용은 잘못이었다. native ID 대사 결과 원본 61건 ledger에 4건 모두 `deferred`로 존재했다. 사용자에게 정정했으며 원본 분모·hash·행을 덮어쓰지 않았다.

검증 묶음은 low-price/profile revision, WS receipt/monitor, native identity, Micro, Pattern, controller, machine attribution/timing, wrapper의 **732개**, widget policy loader **7개**, 전일 profile revision·expanded research·widget research·workorder·checklist consumer **236개**다. Python compile, `git diff --check`, print-only checklist parser도 통과했다. broker API·Provider 재호출 및 실매매 테스트는 실행하지 않았다.

## 별도 승인 추천의 구현 결과

[승인 후속 원장](2026-09-09-widget-episode-approved-implementation-ledger.json)은 [원본 61건 원장](2026-09-08-implement-now-two-pass-ledger.json)의 같은 17개 widget/episode/followup 행에 대한 후속 판정이다. **61+17개로 합산하지 않는다.** 16개 native recommendation의 21개 원본/mirror 위치와 1개 followup을 재대사했다. 구현 요청4=구현2+기존 경제성 gate 보류2, 비구현13=기존 구현 검증1+관찰2+연구 보류7+거절3, 미분류0이다.

| 추천 owner | 결과 | 근거와 다음 소비 |
| --- | --- | --- |
| SK이터닉스 `sk_eternix_late_morning` | 9/9 revision 구현 | 10:45~10:54, lookback20, drawdown1.25%, near-low0.75%, offsets(0,-1), target4 ticks. 기존 10:40 preflight/10:44 live timer |
| TYM `tym_morning` | 9/9 revision 구현 | 09:10~09:59, lookback15, drawdown1.0%, near-low0.5%, offsets(-1,-2), target4 ticks. 기존 09:05 preflight/09:09 live timer |
| 영원무역 오전후반 / 두산에너빌리티 정오 | 구현 보류 | calibration 한쪽 EV가 각각 −0.001334% / −0.003339%. 사용자 승인을 기존 경제성 gate 면제로 해석하지 않음 |
| widget080220 | 기존 구현·9/9 loader 검증 완료 | 기존 자동 owner의 verified policy를 원본 연구/hash로 재구성하고 로더가 080220만 반환함을 확인. 추가 publish·재기동 없음 |
| widget006800/010140/475150 | 원본 reject 유지 | holdout 실패. 독립 episode의 475150 추천과 widget 권한을 혼합하지 않음 |
| collector 연구7개 / 저가주475560 관찰 / machine turnover 후속 | 보류·관찰 유지 | research_watch 또는 evidence accumulating. native ID·사용자 승인만으로 표본·source-quality·ingress 결손을 통과시키지 않음 |

승인 evidence는 [원천 보존 projection](2026-09-08-low-price-recommendation-apply-evidence.json)이다. 원본 연구의 byte SHA256 `220c1b35e2a92f9438803e20d92d6dc1675111bccf3dac9047e0110e87ab0861`, projection canonical SHA256 `beabcefb58b49050c16beb789a15f83fab8b35e11eb21082b2e9cc883c5b42ea`를 결속했다. 원본66거래일·비용0.23%·양쪽 calibration/holdout/full 검증을 보존하며 새 시세나 실체결 증거로 재라벨링하지 않는다.

전체 profile56/runtime eligible53/기존 quarantine3, profile당20주·10주씩 두 leg는 불변이다. 새 profile/timer를 설치하지 않았고 해당 기존 timer4개는 enabled/active·9/9 예정 시각으로 확인했다. 주문·취소·기존 보유 target·runtime env/lock·매매 process는 변경하지 않았다. KEPCO custody SHA256 `7b168c72466f8baa052c577c8523e1060e8138bed4da8f76518c1e657d5f7174`도 불변이다.

실제9/9 low-price applied 파일은 아직 없으며 **메모리상 정상 apply 경로 검증만** 실행했다. preview policy hash는 `36a38b1e3ad6015388966cff9e1606f55cebc78d478f6284871d80a23494f3df`, `candidate_validated_profile_revision_applied`, mutation0·validator PASS다. 이를 실제 publish/PID 소비로 보고하지 않는다. exact-date/hash/evidence 불일치는 신규 진입 fail-closed이며, 되돌림은 사용자 재검토 후 다음 PREOPEN에서 이전 revision을 선택하고 기존 보유 target은 당시 정책으로 보존한다.

변경은 현재 작업트리에 있으며 이번 턴 커밋·푸시·매매 process 재기동은 하지 않았다. 다음 정상 실행도 기존 배포/PREOPEN/provenance guard가 충족될 때만 실제 소비로 인정한다.

## 영향 산출물과 Pass 2

이전 WS/workorder/verifier/controller/ledger/checklist를 `/tmp/korstockscan-review-0909.i6HHQO`에 보존한 뒤 WS 최종 보고서만 source9/8로 재생성했다. 정상 일정232, bounded rejection15159, source-quality rejection657, 실제 미완료 schedule24 및 admission receipt gap1은 전후 동일하다. 단축 일정 판독 수리는 검증됐지만 해당 과거 결손25건은 계속 남으며 누락된 시세·체결·경제성을 생성하지 않았다.

일반 controller 계획이 이 fingerprint 결손에 EV까지 제안하는 것을 확인하고, 최소 재실행 계약에 따라 필요한 `workorder(max12) → runtime summary → 일반 verifier → tower → checklist → strict verifier`만 직접 순서대로 실행했다. 모두 exit0이며 EV·Daily·AI Provider·widget/episode 추천 producer는 재실행하지 않았다. 이후 정상 controller wrapper로 최종 strict 검증·terminal을 다시 확인했다.

최종 workorder generation은 `2026-09-08-f98290e4027e`. main44개 native ID/decision 및 나머지9개 source hash가 전과 같고, 별도 승인 구현 뒤 재-intake에서도 추가 eligible 항목0이다. main 구현 요청9개는 기존 검증1·원천 증거 차단8이며 별도 Pattern2개 증거 대기도 유지한다. 이들을 전부 구현했다고 주장하지 않는다.

**00:27:14 strict summary/drought PASS → controller JSON done/cron DONE**, 필수 산출물 누락·downstream 누락·stale downstream 각각0. verifier 전체 warning과 source/economic 잔여는 유지한다. AI follower는 기존 `terminal_ready:validated_blocked_candidate_without_exact_entry_control` checkpoint를 확인하고 SKIP했으며 새 Provider 실행이 아니다.

finalization의 동일 source-date predecessor7개를 읽기 전용으로 재검증해 모두 DONE을 확인했다. 수정은 진단/요약과 다음9/9 profile 코드에 한정돼 source9/8 cleanup/detector 계약을 무효화하지 않았다. 따라서 영향 없는 **9/8 cleanup22:53:19·detector22:53:21** receipt를 원래 시각으로 재사용했다. 새9/9 detector를 과거 날짜로 실행하거나 새로운 finalization 성공으로 보고하지 않는다. controller 로그는 기존 owned-log runner가 검증 압축 회전했으며 원본 근거를 보존했다.

## 다음 자연 수용 owner

[9/9 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 동일 `WidgetEpisodeRecommendationApplyAcceptance0908`이 기존 timer→exact-date PREOPEN/apply hash→PID→신호/valid-empty→독립 custody/terminal·비용 순익을 확인한다. Micro/AI/Pattern/Recovery의 이관4개도 원래 ID와 Acceptance를 유지한다. 코드 수리, 정책 선택, PID 소비, submit drought 해소와 순이익은 각각 별도 상태다.

외부 Project/Calendar sync는 실행하지 않았다. 체크리스트 문서 하단의 표준 명령은 사용자가 실행한다.
