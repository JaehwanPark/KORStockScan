# 9/22 메인 기계판정 학습·장중 적용 보완 리뷰

범위: [기계정책 보완 계획](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md)의 M1–M6. 사용자 승인: 구현·반복 리뷰·커밋/푸시·배포·장중 정책 적용·장후 재계산. AI VETO/PASS 최적화, widget/episode 정책 및 주문/수량/보유 가드는 이번 변경에 포함하지 않는다.

## 코드 리뷰와 검증

- M1: 82좌표 registry 계약, control4/single20/local_joint24/selector_leaf32/broad_joint16, predecision blocker·미탐색 좌표·지원 source 우선. 승률 → 평균 비용 후 경로 EV → 회복값 → 기회 수 → 단순 정책. 음수 EV 허용.
- M2: train best/visited/cursor/군별 진척/domain/selector/budget version checkpoint, 후보가 있어도96회 전에 holdout에 접근하지 않음. 부모 tree/unknown/source fallback 승계와 유효 후보 중복 제거.
- M3: AI join 없이 기계 capture+기존 비용/가격경로만 읽는 loader. 원천 누락은 행별 부모 fallback, 손상된 봉·metadata는 개별 제외. 완성봉 producer→AI 축약 우회→기계 raw→재생 연결. 시가총액은 기존 수집기의 별도 시점 snapshot, historical legacy Marcap 소급 사용 없음.
- M4: 부적격 고득점 scope가 적격 scope를 막지 않음. scope별 parent CAS 검증 후 다중 scope atomic generation, AI component 보존.
- M5: attempt bundle pin, 제출 전 세대 검증/recheck, PID/start ticks/leaf/임계치 capture, 날짜 변경 carry, machine-only rollback.
- M6: 정규 장후·수동 wrapper의 독립 machine stage와 terminal receipt 연결. 전체 legacy 보고서의 중복 immediate activation 제거.

대상 pytest648건 PASS(로그: `tmp/main-machine-repair-20260922/targeted-tests.log`), Python compile·두 wrapper bash 문법·diff 검증 통과. 기존 `test_openai_scalping_analyze_target_returns_feature_audit_fields` 1건은 이번 diff를 제거한 HEAD 코드에서도 `computed_not_sent`/`not_attempted` 관측 문구 불일치로 실패함을 별도로 확인했다(`baseline-audit-field-test.log`). 이 기존 보조 관측 테스트를 제외한 변경 범위 검증이다. 실제 provider/주문 테스트는 실행하지 않았다.

리뷰 중 보완: 부분 결손 때문에 전체 좌표를 동결하는 로직 제거, AI mismatch 행 제외 연결 제거, 기존 tree의 unknown/결손 fallback 보존, AI formatter의 완성봉 제거 경로 보완, primitive 손상 row 사전 격리, 동일 input 중단 재개 시 탐색 순서 고정. 예비 계산은 train checkpoint에서 중지해 검증되지 않은 후보를 적용하지 않았다.

## 공식 원천 확인

2026-09-22 KST 확인 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`. `kiwoom_docs`는 현재 upstream tree에 없음. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`의 ka10001 요청/응답을 대조했다. POST `/api/dostk/stkinfo`, api-id ka10001, 종목별 stk_cd 및 기존 continuation/오류 처리 유지. `mac` 공식 단위는 억원이며 새로운 snapshot만 ×100,000,000 KRW로 변환한다. 같은 응답의 보고 시총을 사용하고 가격/상장주식수를 사후 혼합하지 않는다. 실제 API 호출 추가, 주문·인증·WS 변경 없음. 시각과 확인 항목은 `tmp/main-machine-repair-20260922/official-reference.json`에 보존.

## 최종 계산·배포·소비

최종 코드 고정 후 기계 전용 회차를 실행한다. 원천 cutoff/학습 cutoff는2026-09-21이며 이후 날짜의 미관측 holdout을 성공으로 표시하지 않는다. 후보·승률·평균 비용 반영 EV·군별 탐색·scope 적용·현재 bundle·실제 PID 소비 결과는 완료 후 아래에 기록한다. 현재 이 절은 완료 영수증이 아니다.
