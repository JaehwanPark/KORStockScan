# Native entry arm 완료 연결 수리 — 2026-10-15

## 범위와 원인

사용자 요청에 따른 코드 수리·반복 리뷰·표적 검증이다. 배포·선택본 변경·Main 재기동은 별도 세션에서 요청할 예정이므로 수행하지 않는다. 기준은 통합본 `3d43544e3bf2e6c3a326f924f373ac9337f6cb84`이며, 기존 재시작 signal epoch/내부 오류 분류 수리를 포함한다.

10:53:45 주성엔지니어링 요청 `analyze_target:036930:1792029225578:2f5acaa4`는 HTTP 경계에서 607ms가 남아 응답 처리 예약 250ms를 제외한 예산이 357ms였다. 첫 큐 방문→native 확보가 3035ms였다. 이전 signal 507의 PASS가 `real_weak_pullback_entry_block`으로 주문 없이 반환된 뒤에도 `entry_armed`가 남아 signal 509의 새 평가 경로를 가로막았다. 이후 source-quality 차단과 Main 방문 대기도 존재하므로 전체 지연을 arm 하나로 단정하지 않는다. 원 인과 자료는 `tmp/entry-timeout-105345-20261015/diagnosis.json`에 보존한다.

해당 timeout의 outbox는 `transmission_uncertain`이다. 기존 provider 호출/예약 초기화, 재전송, 원 native 마감 연장은 하지 않는다. kt00011 원 요청은 약 73ms에 성공했고 이번 수리 대상은 아니다.

## 구현과 보완 리뷰

- arm을 원 async 요청·평가·trace·native signal·PID/start ticks에 결속한다. 다른 요청의 완료가 후속 arm을 지울 수 없다. 재기동 또는 문맥 누락으로 결속이 유효하지 않은 arm은 과거 PASS의 재사용 권한이 되지 않는다.
- Main 완료 finally에서 같은 요청의 submit 함수가 `returned_false`이고 물리 주문 호출 0임을 확인한 경우에만 arm을 정리한다. 기존 완료→대기 native 재방문 연결이 다음 신호를 원래 5초 마감으로 확보한다.
- 주문 attempt·broker accepted·보유 수량·미체결 주문·initial quantity bundle·양수 지연 진입 의도·예외·불명확한 반환은 기존 custody를 보존한다. 확인과 arm 제거는 같은 ENTRY_LOCK에서 수행한다. 정리 예외가 나도 기존 async 정리/ack/revisit은 진행한다.
- 1차 리뷰에서 arm만 지우면 cooldown 중 저장된 BUY/PASS를 다시 사용할 수 있는 경로를 발견했다. 해당 평가의 종료 표시를 추가해 새 native가 없을 때 재사용을 막았다. 원 PASS와 원 마감은 그대로 보존하며, 후속 native의 식별자·마감은 새 원천에서만 온다.
- 후속 리뷰에서 복원된 arm의 deadline 누락·0/NaN·request/evaluation/trace 결속 불일치도 검사하도록 보완했다. 마감 조회 전에 유효성을 확인해 예외나 20초 arm TTL로의 잘못된 재사용을 방지한다. 손상된 원 근거를 새 마감으로 덮어쓰지 않는다.
- quote/source/account/order/quantity/cooldown/hard safety, 정책 수치, provider timeout/회로, WS/API 계약과 원천 생산자는 변경하지 않는다. 레거시 non-native arm 동작은 유지한다.

## 재기동 인계 계약

`sniper_state_handlers.py`는 기존 pre-submit delay/stop/holding 코드 계약에 포함된다. 정책 원본과 PREOPEN 영수증을 재작성하는 대신 `intraday_release_handoff.REVIEWED_NATIVE_ARM_COMPLETION_SOURCES`에 검토된 파일의 정확한 전후 SHA만 등록한다. 전 SHA는 원 PREOPEN `3d644d8495a2c257784d96cd01df831bfb6022f8`의 `b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500`, 후 SHA는 `930921a6e3b77fa1e4342d46f29e117cdf18301a8f24220736ebdb384e97af8c`이다. 다른 코드 변경, 원본 digest 변경, dirty candidate/verifier는 계속 거절한다.

배포 세션에서는 최종 통합 commit으로 candidate delay/stop/holding 검증을 다시 수행하고, 원 native family/auxiliary 등록·PREOPEN/source 해시를 유지한 기존 ordered handoff 절차를 사용한다. 현재 코드 검증을 새 PID 소비로 대체하지 않는다. 누락/변경 원천은 그대로 실패시키며 새 원천이나 성공 영수증을 합성하지 않는다.

## 검증과 남은 수용

- Main completion→submit observer→arm 정리→첫 native 재방문 통합 시험과 보호 경계, 재기동 식별자 누락/불일치, source 부재 때 PASS 재사용 금지를 검증했다.
- 진입/async bridge/기존 scale-in 회귀와 정책/기동/async coordinator 계약 총 2,402개 통과(29.50초). 컴파일 5개·diff·print-only parser가 통과했고 기존 자연 수용 owner가 1개임을 확인했다. 검토 범위의 미해결 결함은 없다.
- 실제 동결 정책의 candidate delay/stop/holding 검증, bootstrap 원천 해시 대조, 기존 선택본의 native 원천 838개 검증이 통과했다. native 계약 모듈 33개는 후보와 기존 선택본이 동일하다. 최종 commit 읽기 전용 대조·테스트·소스 SHA 증거는 `/home/ubuntu/KORStockScan/tmp/entry-arm-native-handoff-20261015/`에 보존한다. selector/bootstrap/current pointer는 변경하지 않는다. 새 후보의 handoff 영수증 발행·실제 PID 로딩은 배포 세션에서 수행한다.
- 원천 결손·stale·source-quality 차단과 외부 응답시간 때문에 발생할 수 있는 모든 timeout의 제거를 주장하지 않는다. 실제 배포·재기동·자연 provider 응답·주문/체결·비용 후 경제성은 미수행이며 다음 자연 수용은 당일 checklist `AuxiliaryCircuitRecoveryRepair1012`가 소유한다.
