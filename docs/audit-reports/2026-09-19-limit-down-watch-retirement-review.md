# Limit-down watch 축 폐기 및 검증 — 2026-09-19

사용자 지시: 전용 장후작업 축·런타임과 불필요한 누적 산출물 제거. 후속 사용자 지시로 재리뷰·수정보완·관련 커밋/푸시·immutable successor 배포까지 승인되었다. 봇 재시작·주문·조기 PREOPEN 실행은 포함하지 않는다. 초기 작업 시 9/19 체크리스트가 없어 9/21 준비 체크리스트에 폐기 범위를 기록했다. 최종 통합 중 다른 세션이 생성한 9/19 현행 objective/mandatory 규칙도 확인했으며 해당 세션의 OPEN owner를 보존했다.

## 제거 및 보존 경계

- 삭제: `scalping/limit_down_watch.py`, `monitoring/limit_down_watch_report.py`, `monitoring/limit_down_watch_research.py`, 전용 회귀 테스트 모듈.
- 제거: 전용 관찰 REG 요청/상태기계/회전 슬롯, WS 관찰 callback, radar 관찰 차단, 스캐너 후보 입력·가산점·승격/용량 이전·전용 필드 전달, PREOPEN 파일/hash/env loader와 정책 감사, 장후 실행 flag/호출/완료 marker 및 verifier/controller 전용 요구/재시도 사유.
- 제거: 전용 consumer가 사라진 `get_previous_limit_down_stocks_ka10017` API helper. 공유 REST continuation·정규화·WebSocket parser와 generic REG/REMOVE 흐름은 보존했다.
- 재활성 방지: 기존 `lifecycle.retirement`에 전용 report/family/stage와 env namespace를 등록했다. 과거 `true` env·선정 후보는 현재 권한을 얻지 못한다. 일반 스캐너는 과거 `LIMIT_DOWN_LIVE_UNLOCK` payload를 거부하며 broker leg와 추가매수도 차단한다.
- 보존: 공유 raw pipeline·DB·주문 owner/broker order/fill/terminal·완료 손익·custody 원장, 다른 전략/세션 변경, 공통 매수/수량/예산/청산/안전 guard. 과거 이미 보유한 position의 익일 보유 금지 안전 호환은 `retired_entry` 차단으로만 남겼다. 신규 관찰/정책/진입 런타임이 아니다.
- 관찰 예산은 전체 cap을 늘리지 않고 전용 슬롯을 없앴다. 16슬롯 기준 general 1·rising 15이며 기존 소규모 cap과 다른 scanner 예약은 유지한다.

## 리뷰·수정보완

전용 producer → 스캐너 → WS/radar → PREOPEN → broker leg → 완료 손익/overnight → wrapper/verifier/controller를 추적했다. 삭제 과정에서 누락된 일반 스캐너 초기화·저가 반등 예약 guard를 회귀 검증으로 발견해 복원했다. 제거된 WS callback을 patch하던 다른 collector 테스트는 해당 patch만 삭제하고 검증 목적은 보존했다. 폐기된 producer를 재실행하거나 양수 EV를 만들지 않았다.

공식 Kiwoom upstream 현재 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/decoders.py`, `kiwoom/realtime/schemas.py`, `examples/국내주식/종목정보/get_domestic_upper_lower_limit_stocks.py`를 확인했다. 현재 tree에 `kiwoom_docs`가 없어 packaged spec/core를 확인했고 sample은 보조 증거로만 사용했다. 프로토콜/요청/주문 의미를 새로 추정하지 않았다. 조회 시각·SHA·확인 파일 hash는 [공식 참조 증거](../../tmp/limit-down-retirement-20260919/official-reference.json)에 있다.

## 최종 successor 리뷰·검증

최신 원격 main `5dcf237ad`에서 격리 작업본을 만들고 전용 제거 변경만 이식했다. 공유 파일은 부분 변경으로 옮겨 다른 세션의 미커밋 변경과 독립 삼성/저가주 source pin을 보존했다. 기존 작업본의 1,007건 검증은 선행 증거이며, 배포 판정은 아래 successor 검증을 따른다. 다른 세션의 원격 compact 통합 `0e86f5d20`도 정상 rebase로 보존했다.

| 검증 | 결과 | 증거 |
| --- | --- | --- |
| 스캐너·예산·폐기 env/policy·주문 전 차단·custody·PREOPEN·WS/collector·wrapper/verifier/controller | 1,295 passed, 1 deselected | [최종 회귀](../../tmp/limit-down-retirement-20260919/tests-isolated-final.log) |
| 기존 PREOPEN smoke fixture 결함 대사 | 기준 main test에서도 동일 실패 | [기준 실패](../../tmp/limit-down-retirement-20260919/tests-baseline-wrapper.log) |
| Python compile, shell syntax, diff whitespace, print-only 문서 parser | PASS | [successor validation](../../tmp/limit-down-retirement-20260919/successor-validation.json) |

원격 compact 통합을 포함한 재검증은 **1,531 passed·5 failed·1 deselected**이며 [통합 회귀](../../tmp/limit-down-retirement-20260919/tests-successor-integrated.log)에 있다. 실패5건은 새 compact CLI/순서에 아직 맞지 않는 기존 wrapper 기대이고, 제외한 smoke1건을 포함하여 제거 전 `0e86f5d20`의 원본 wrapper·원본 test에서도 **동일6건 실패**를 재현했다([기준 검증](../../tmp/limit-down-retirement-20260919/tests-integrated-baseline-wrappers.log)). `CompactAIPostcloseIntegration0919`의 별도 fixture/실패 전파 회귀 owner로 구분하며 관련 없는 compact 구현을 되돌리거나 검증을 약화하지 않았다. 폐기 변경 검토 범위의 미해결 결함은 0건이며 전체 suite GREEN을 주장하지 않는다.

제외한 `test_preopen_wrapper_smoke_allows_operator_lock_runtime_env_without_source_report`는 기존 임시 project에 `automation.low_price_two_leg_policy_apply` module이 없어 실패한다. PREOPEN wrapper는 이번 diff에서 변경하지 않았다. 이 별도 fixture 결함을 전체 suite GREEN으로 보고하지 않으며 폐기 기능 복구나 운영 guard 완화로 해결하지 않았다. 재리뷰에서 전용 모듈과 함께 제거된 공유 test import를 복구하고, 폐기된 source의 추가매수 차단을 실제 consumer 함수로 검증했다. 검토 범위의 미해결 결함은 0건이다. 회귀 통과는 자연 거래나 EV 개선 증거가 아니다.

## 산출물 삭제 및 배포 구분

삭제 전 해당 파일의 열린 FD와 전용 실행 프로세스를 확인했다. 전용 report/candidate/CF/post-sim/real-attribution, sim/bounded-live 정책, runtime 상태, 전용 approval의 누적 파일 **279개·1,410,662 bytes**와 bytecode 3개를 삭제했다. 다른 전략의 공유 보고서/원천이나 immutable release는 삭제하지 않았다. 삭제 파일별 경로·크기·SHA는 [cleanup manifest](../../tmp/limit-down-retirement-20260919/cleanup.json)에 있다.

후속 배포는 검증된 코드 commit으로 새 immutable release를 생성하고 공통 router의 미래 호출 선택만 교체한다. 기존 선택 배포본·독립 systemd source pin·실행 프로세스는 수정하거나 재시작하지 않는다. 선택·route·PID 소비의 최종 증거는 배포 후 아래에 기록한다. 폐기된 보고서를 복구·재생성하지 않는다.
