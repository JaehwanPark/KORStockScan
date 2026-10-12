# 반전 신호 경로 경보 원천·분류 보완 — 2026-10-12

## 범위와 원인

사용자 제공 `machine_trace:reversal_signal_path_changed` 22건 알림에 대해 같은 날짜·정확한 attempt의 WS 사용 원천과 native rejection을 대조했다. 공유 `latest` 경로는 계속 갱신되므로 알림 발송 시각/불변 snapshot 없는 원래 22건의 집합을 현재 파일로 확정하지 않는다. 일 누적 직접 해당 오류 144건(09:03:02–12:54:06)의 별도 모집단은 주성 85, HPSP 20, 두산 22, 알테오젠 17건이다.

원 native 거부는 FIRST_UPTICK 신호 평가 전에 turn이 끝나거나 새 turn으로 바뀌어 ready 집합에서 원 신호가 제거된 결과다. 현재 source·native epoch·scope generation은 일치하고 first turn·ready membership만 불일치한다. 이는 broker 주문 실패 또는 Kiwoom API 결함 증거가 아니다. 외부 현재 가격으로 과거 신호를 복구하지 않는다.

감시기 분류는 `current_turn_id=None`이면서 현재 가격이 최초 확인가 미만인 경우만 정상 수명 종료로 인정했다. 다음 turn 또는 확인가 이상에서 후속 되돌림으로 종료된 신호도 원천결손에 남는 결함이다. 추가로 신규 trace의 일반 token 마스킹이 비밀정보가 아닌 native claim content digest를 가려 등록 proof 검증을 끊었다.

## 보완과 경계

- 기존 monitoring 소비자에서 검증된 source registration·snapshot·token·family/cell generation·route·clock 계약을 그대로 유지한다. 같은 lock에서 수집한 native predicates가 모두 일치하고 원 ready가 없으며, turn이 없거나 같은 native epoch에서 더 뒤의 관측된 sequence로 교체된 FIRST-only 신호만 기존 `reversal_first_signal_invalidated` 진단으로 분류한다. 원 native guard·기계 action·AI/provider·주문·5초 기한은 바꾸지 않는다.
- trace sanitizer의 정확한 rejection receipt 두 경로에서만 snapshot/generation/signal ID로 재계산한 SHA256과 일치하는 내부 claim digest를 보존한다. 임의 token, 잘못된 digest, 다른 경로/schema, 실제 자격정보의 기존 마스킹은 유지한다.
- 과거 두 claim token이 `[REDACTED]`인 행은 읽기용 사본에서 digest를 재계산한다. 재구성 결과가 당시 저장된 등록 proof SHA 및 모든 기존 검증과 일치할 때만 사용한다. 원 JSONL, 정책, live native registry/claim, 경제성·주문 결과는 수정하지 않는다. 재계산으로 검증되지 않는 행은 source gap으로 남긴다.
- 새 Python 파일을 만들지 않는다. 기존 report consumer는 `src/engine/monitoring`, trace writer는 `src/engine/scalping`, 회귀는 기존 `src/tests` 소유 위치를 따른다.

## 검증과 적용

v5/v6 native 실제 state로 하락·상승 후 되돌림·새 turn 교체를 재현하고, native guard 결과가 동일함을 확인한다. source/epoch/quote/clock/세대·증빙·native predicates 결손, foreign turn·미래 sequence, 임의 credential, 손상된 마스킹 proof는 해소 처리하지 않는다. 과거 144행 재판정에서 모두 동일 native 수명 종료로 확인했고 마스킹 8행도 원 proof 해시가 일치했다. 원 22건 모집단을 144건으로 바꿔 집계하지 않는다.

코드 리뷰·검사·배포·PID 및 자연 감시 결과는 [완료 근거](../../tmp/reversal-path-alert-followup-20261012/completion.json)에 분리 기록한다. 체크리스트는 후보 Git에 준비하고 기존 승인된 ordered 배포가 Main/supervisor 종료 후 발행한다. source-gap 경보의 자연 해제와 과거 원천 복구, 미관측 신규 AI·주문·경제성은 각각 별개다. 기존 일일 OPEN owner/검증 기준은 보존한다.

## 배포 인계 재검토

첫 후보 전환은 `13:01:48` 이전 PID 종료 후 인계에서 `pre_submit_delay_generation_changed`로 차단됐다. 제출지연 계약이 감시기 전체 파일도 결속하므로, 보고 전용 함수 수정에 대한 코드 호환성 연결이 필요했다. `13:05:26` 원 selector·체크리스트·정책 검증 후 직전 릴리스를 재기동했고 `13:06:08` PID `841700`의 소비 증빙을 확인했다. 실패 후보를 강제 기동하지 않았다.

- 인계기의 허용 AST 변화에 감시기의 `_reversal_lifecycle_diagnostic` 함수만 추가한다. 제출지연 anchor/qualification/selection, 나머지 함수와 모듈 레벨 코드, 원본 계약 SHA·Git·현재 코드 byte 검증은 유지한다.
- ordered 배포는 기존 PID/정책 검증 직후, startup hold·종료 요청 이전에 후보 제출지연 코드 차이 검사를 수행한다. 인계 후 검사를 대체하지 않으며 selector/정책 파일을 변경하지 않는다. 부적합 후보는 실행 중 Main을 유지한 상태에서 preflight 실패로 종료한다.
- candidate의 정책 준비, 원본 PREOPEN/장후 세대·보유정책·보조판정 reader·실제 PID 소비 검증을 최종 릴리스에서 다시 수행한다. 첫 실패와 복구는 완료 영수증에 숨기지 않고 보존한다.
