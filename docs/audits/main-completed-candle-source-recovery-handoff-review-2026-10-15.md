# 완료봉 원천 복구와 새 기계 평가 연결 리뷰 — 2026-10-15

## 결정

사용자 지시 “다음작업”에 따라 완료봉 게시 후 기존 원천 복구가 새 기계 평가 요청까지 연결되는지 검증했다. VI 원천 결속은 제외했다. 상시 감시의 원천 복구 허용 분기가 필요한 새 native claim 선택 전에 반환하는 연결 결함 1건을 재현해 수정했다. 원천 결손 자체와 정상 신호 무효화를 모두 코드 결함으로 분류하지 않는다.

후속 코드 리뷰·수정보완·커밋 지시에 따라 exact 원천 검증과 native 조회의 item 불일치 1건을 추가 재현해 보완했다. 최종 변경은 두 연결 결함의 수리와 복구 parent 증거 보존이다. 아래 최초 250개 검증은 원 기록이며 최종 커밋 대상의 검증은 후속 리뷰 절이 소유한다.

실행 owner는 현재 체크리스트의 `AuxiliaryCircuitRecoveryRepair1012`다. 코드 검증 완료와 배포·PID 소비·자연 재평가·제출·체결·비용 후 성과를 구분하며 기존 OPEN을 유지한다.

## 동결된 자연 사례

| 대상·시도 | 확인된 흐름 | 판단 |
| --- | --- | --- |
| HPSP `403870`, `aims-e9cbca6dfde7dd691630` | 원천 검사 13:12:02.177070 → 필요한 13:11 봉 게시 13:12:02.662647 → Main commit 허용 13:12:02.784974 → 복구 pending 등록 13:12:02.837044. 원 lease는 13:13:32.191565까지이며 해당 구간의 새 dispatch는 0건이다. | 복구 연결 검증 대상이다. 이 기록만으로 유효한 후속 native 신호가 존재했다거나 제출 기회를 잃었다고 단정하지 않는다. 봉 게시만으로 다른 원천 blocker가 모두 해소됐다는 뜻도 아니다. |
| 주성 `036930`, `aims-146925129ae4f57b83ed` | 원천 검사 13:15:01.993196 → Main이 13:15:03.393360에 `reversal_signal_path_changed`로 거절 → 필요한 13:14 봉 게시 13:15:03.824852. | 원 신호 유효성 거절이다. Main이 수용하지 않은 결과에 복구 lease가 없는 것은 결함으로 보지 않는다. |

[자연 흐름·원본 행·입력 해시](../../tmp/completed-bar-source-recovery-verification-20261015-1358/natural-chain-verification.json)는 기존 12:58~13:20 감시 원본에서 추출했다. 새 장중 감시나 broker/provider 호출로 표본을 만들지 않았다. 이전 [분류 정정](../../tmp/submission-next-priority-vi-review-20261015-1325/scope-and-defect-classification.json)의 “확인된 코드 결함 0”은 당시 상태이며, 이번 재현으로 연결 결함 1건이 추가 확인됐다.

## 결함과 수정

`_resolve_watching_state_change_refresh`는 새 exact 0B·fresh 0D가 확인되면 `machine_source_fresh_retry`로 즉시 반환했다. 그러나 상시 감시의 `_resolve_scanner_async_entry_ai`는 별도의 유효 native claim이 필요하다. 이전 시도 종료 시 `_clear_scanner_async_identity`가 claim을 정리하므로, 복구 허용만으로 후단에 진입하면 claim 없는 신호 대기로 돌아갈 수 있었다.

수정은 상시 감시에서 복구가 허용된 경우 기존 native claim 선택·검증을 거친 뒤 평가 요청으로 연결하도록 제한했다. 새 유효 신호가 없으면 `machine_source_wait_native_signal`로 대기한다. 비상시 감시의 기존 원천 복구 경로와 원천 검증은 유지한다. 기계 판정·AI PASS·주문을 합성하지 않으며 이전 요청 신호를 재사용하지 않는다.

기존 완료 판정 냉각시간, 원 recovery lease·재시도 예산, exact item/route/transport epoch, 신호 원 epoch+5초 마감, DANGER·stale·가격·계좌·주문·수량 및 operator lock을 변경하지 않았다. 완료봉 게시 지연·허용 시점도 변경하지 않았다.

## 리뷰와 검증

- [수정 전 재현](../../tmp/completed-bar-source-recovery-verification-20261015-1358/reproduction.log): 새 원천 복구에서 native 선택에 도달하지 못하는 두 조건이 실패했다.
- [관련 회귀](../../tmp/completed-bar-source-recovery-verification-20261015-1358/targeted-validation.log): 원천 복구·async bridge·고정 감시 제출 원천·완료봉 producer/reader 250개 통과. 추가 회귀는 신호 있음/없음, 완료 판정 cooldown, stale 호가, 이전 요청 신호, 실제 async 요청 구성과 native 마감 만료를 검증한다.
- async 연결 fixture는 실제 요청 구성과 identity/deadline 검사를 실행하고 요청 admission에서 중단한다. claim 선택 결과는 fixture이며 worker·실제 기계/AI 호출·계좌·주문 전체 경로 재생을 완료한 증거는 아니다.
- [선택본 함수 대사](../../tmp/completed-bar-source-recovery-verification-20261015-1358/selected-consumer-comparison.json): 작업 시작 당시 workspace `c938ace0610aeec2e68dde9a024e0b82579a1c3b`와 운영 선택본 `bb4808c77087231b072efbd3ea12271fbb3889c6`의 관련 네 함수가 동일했다. handler 파일 전체의 동일성을 주장하지 않는다. [전체 파일 해시](../../tmp/completed-bar-source-recovery-verification-20261015-1358/source-comparison.json)를 별도로 보존한다.
- 자체 리뷰에서 생산자→복구 허용→native 선택→async 요청 및 Main 소비 경계를 재확인했다. 위 범위의 미해결 구현 결함 0건이다. Python compile·diff·문서 링크와 print-only parser 결과는 [최종 검증 manifest](../../tmp/completed-bar-source-recovery-verification-20261015-1358/output-manifest.json)가 소유한다.

## 후속 코드 리뷰와 수정보완

- 추가 결함: 복구 검사는 `get_exact_item_data`로 읽은 lease의 exact 0B/0D를 검증하지만, 이어지는 native 조회는 호출자의 기존 집계 `last_realtime_type_item['0B']`를 사용했다. 집계 item이 없거나 KRX/NXT를 가리키면 검증한 SOR 원천과 다른 key로 신호를 조회해 복구가 다시 대기로 끝날 수 있었다. [수정 전 재현](../../tmp/source-recovery-handoff-code-review-20261015/exact-item-reproduction.log)의 세 조건이 모두 실패했다.
- 보완: source recovery가 허용된 상시 감시에 한해 이미 검증한 lease item으로 native venue/item을 결정한다. 일반 감시의 기존 선택 경로는 유지한다. 신호 확보 후 반환에도 원 parent attempt/hash·source 시각을 보존한다. caller의 집계 데이터는 덮어쓰지 않는다.
- 재리뷰: exact read가 stale·다른 종목·읽기 오류이면 claim을 확보하지 않는다. 실제 후단의 symbol/route/generation/원 마감 검사, 이전 신호 재사용 차단, retry budget·cooldown과 미완료 async 소비를 확인했다. Kiwoom 요청·응답 parser·FID·등록 계약이나 안전 설정은 변경하지 않았다.
- 커밋 작업 트리: `/home/ubuntu/KORStockScan-worktrees/source-recovery-handoff-review-20261015`, branch `fix/source-recovery-handoff-review-20261015`, 기준 `c938ace0610aeec2e68dde9a024e0b82579a1c3b`. 공용 handler에 병행 중인 익절 수정과 다른 연구 변경은 포함하지 않는다.
- [최종 표적 검증](../../tmp/source-recovery-handoff-code-review-20261015/targeted-validation-round1.log): 위 네 suite 256개 통과. 최초 250개와 중복되는 확장 검증이며 합산하지 않는다. 변경 Python compile·diff·print-only parser·단일 OPEN owner와 링크 검증도 수행한다. [후속 리뷰 manifest](../../tmp/source-recovery-handoff-code-review-20261015/review-result.json)가 검증 소스 해시와 결과를 소유한다.
- 재리뷰 범위의 미해결 코드 결함은 0건이다. fixture는 신호 선택을 대체하고 async admission에서 중단하므로 실제 새 기계 평가·provider·주문 전체 경로 재생 또는 자연 복구 수용을 주장하지 않는다.

## 남은 실행과 종료 기준

이번 작업은 workspace 코드 수리·오프라인 검증이다. 배포/selector 변경·Main 재기동·실주문·실제 provider 호출·외부 sync는 실행하지 않았다. VI 원천 결속과 정상 신호 무효화·700ms stale 보호 완화는 구현 범위가 아니다.

검증본이 별도로 적용된 뒤 기존 owner에서 새 PID/code 소비, 원천 실패 시도→완료봉 게시·fresh 원천→새 유효 native claim→새 요청 identity와 원 마감→새 기계 평가→Main disposition을 대사한다. 적격 신호가 없으면 대기이며 자연 복구 성공으로 닫지 않는다. 제출은 기계·AI·모든 안전 검사를 통과한 실제 intent/send/fill/terminal 영수증으로 별도 확인한다.
