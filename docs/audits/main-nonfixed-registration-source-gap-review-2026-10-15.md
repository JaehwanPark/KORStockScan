# 비상시 7건의 등록·첫 수신·exact 원천 연결 리뷰 — 2026-10-15

## 결정과 범위

사용자 “다음 우선순위 실행”에 따라 직전 감시에서 확인한 등록 timeout 3건과 `route_snapshot_missing` 4건을 추적했다. 운영본 `451b6c1ec84fafa563d95381e95c814ac2b2b18b`, PID `2276473`/start `10594101`의 원 로그와 독립 lease 결과를 결속했다. VI 원천 결속은 제외했다.

기한 내 REG 전송이 완료됐어도 비동기 future 완료 통지가 늦으면 관측을 종료하는 연결 결함 1건을 재현해 수정했다. 늦은 전송이나 원천 부재를 정상 완료로 바꾸지 않는다. 코드 검증과 배포·자연 복구·주문·경제성은 분리한다.

## 7건의 결론

| 종목 | 원 결과 | 등록·수신 근거 | 조치 |
| --- | --- | --- | --- |
| 하나금융지주 `086790` | 14:28:28 등록 timeout | 원 예약 14:28:20.824, REG 전송 로그 14:28:21, 첫 0B 및 future 완료 로그 14:28:28, 정확한 동일 lease 정리 14:28:29 | 전송 완료와 future 완료를 구분하는 연결 수리 대상. 유효한 0B/0D 쌍이나 기계 타점까지 소급 인정하지 않는다. |
| 기업은행 `024110` | 14:28:28 등록 timeout | 실제 REG 14:28:28, future 완료 14:28:29로 원 3초 대기를 넘겼으며 동일 lease가 정리됐다. | 원 timeout·늦은 완료 뒤 exact cleanup 유지. |
| 농심 `004370` | 14:28:28 등록 timeout | 실제 REG와 future 완료가 14:28:28로 원 3초 대기를 넘겼고 동일 lease가 정리됐다. | 원 timeout·늦은 완료 뒤 exact cleanup 유지. |
| 화인베스틸 `133820` | 14:28:42 exact 원천 부재 | 14:28:32 REG 및 local 등록 완료. 원 관측창에서 쓸 수 있는 exact 0B/0D 쌍이 확인되지 않았다. | 등록 실패로 분류하지 않는다. 원천 준비 전 기계/AI 진행 차단 유지. |
| 하이퍼코퍼레이션 `065650` | 14:31:37 exact 원천 부재 | 14:31:26 REG 완료. 14:31:36 종료 경계에 code-level 0D 첫 수신 로그가 있으나 exact 0B/0D 쌍은 확인되지 않았다. | 일부 수신을 source-ready로 바꾸지 않는다. reader 결함은 입증되지 않았다. |
| 삼화왕관 `004450` | 14:33:49 exact 원천 부재 | 14:33:39 REG 완료. 원 관측창에서 exact 쌍 미확인. | 원천 대기 종료 유지. |
| 대구백화점 `006370` | 14:46:50 exact 원천 부재 | 14:46:40 REG 완료. 원 관측창에서 exact 쌍 미확인. | 원천 대기 종료 유지. |

[동결된 7건 인과·lease 대사](../../tmp/nonfixed-registration-source-review-20261015-1500/seven-case-causal-review.json), [등록·첫 수신 원 로그](../../tmp/nonfixed-registration-source-review-20261015-1500/seven-cases-log.txt), [원 pipeline 결과](../../tmp/nonfixed-registration-source-review-20261015-1500/seven-cases-pipeline.json)를 보존했다. 로그는 초 단위이며 첫 수신 로그는 code-level이라 exact 쌍의 증거와 다르다. 비동기 통지가 늦어진 내부 CPU/스케줄링 원인은 확정하지 않는다. 7건을 모두 코드 결함으로 세지 않는다.

## 구현과 안전 경계

`src/engine/scalping/zero_base_probe.py`의 기존 등록 future timeout 분기에서 원래의 3초 이내 local 전송 영수증을 한 번 확인한다. 현재 같은 item·lease·transport epoch·0B/0D 등록·관측 전용 소유권과 연결 상태가 모두 유효하고 원 residence deadline 전일 때만 기존 exact 원천 검사로 진행한다. 로컬 확인은 nonblocking lock을 쓰며 lock 경합·영수증 손상·이전 세대·늦은 전송·adopt/remove·연결 종료·lease 만료는 원 timeout과 늦은 future 뒤 cleanup으로 돌아간다.

회복 가능한 것은 local 완료 통지의 연결뿐이다. 실제 broker ACK나 시장 수신을 합성하지 않으며 receipt에 `local_sent_registry_not_broker_ack`를 명시한다. 원 3초 전송 예산·원 150초 lease·native 신호 마감·stale/conflict·가격·계좌·주문·수량·cooldown·provider·cap을 유지한다. 새 REG/REMOVE 요청, 재연결, 추가 provider 호출이나 운영 설정 변경을 만들지 않는다. future 완료 뒤의 중복 cleanup으로 관측을 조기 종료하지 않도록 cleanup 소유권도 검증했다.

위치는 기존 scalping probe owner 모듈과 기존 `src/tests/test_zero_base_probe.py`다. 새 engine-root 모듈이나 중복 구현을 만들지 않았다. 실제 선택본을 기준으로 격리 작업 트리 `/home/ubuntu/KORStockScan-worktrees/nonfixed-registration-receipt-20261015`에서 수리했고, workspace의 다른 연구·익절 변경은 포함하지 않았다.

## 공식 계약 확인

[공식 Kiwoom 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)의 현재 main SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`를 구현 전에 조회했다. 조회 시각·원 파일 hash는 [upstream manifest](../../tmp/nonfixed-registration-source-review-20261015-1500/official/upstream-manifest.json)에 있다. `kiwoom/realtime/packets.py`, `stream.py`, `kiwoom/core/ws_client.py`, `client.py`, `kiwoom/specs.py`, packaged `0B/0D` spec과 PRD/MOCK Postman을 대사했다. URL·REG/REMOVE·refresh=1·item suffix·0B/0D 및 기존 로그인/수신 경계를 확인했으며 wire·FID·응답 parser·인증·계좌 호출은 변경하지 않았다. 이 revision에 `kiwoom_docs`는 없으므로 SDK/packaged spec 이상의 broker ACK·무수신·VI 의미를 추정하지 않았다.

## 리뷰·검증과 남은 수용

- [수정 전 재현](../../tmp/nonfixed-registration-source-review-20261015-1500/reproduction.log): 원 선택본에서 이미 전송된 동일 lease가 `ws_registration_timeout`으로 끝나 source wait에 도달하지 못했다.
- [최종 표적 검증](../../tmp/nonfixed-registration-source-review-20261015-1500/targeted-validation-round2.log): probe·실제 WS lease/reader·queue·dispatch runtime·Main attach 342개 통과. 기존 pandas 경고 1건이다. 첫 확장 호출의 존재하지 않는 테스트 경로는 정정했으며 무실행을 PASS로 세지 않았다.
- 첫 리뷰의 fixture 중복 future 완료 설정을 고쳤다. 재리뷰에서는 timeout 뒤 새 lock 대기를 만들지 않도록 nonblocking 확인으로 보완하고, bool/손상 epoch·다른 lease/종목·부족한 type·늦은/future 전송·adopt/remove·stop·만료를 fail-closed로 확인했다.
- 변경 Python compile·`git diff --check`·문서 링크·print-only parser와 기존 단일 OPEN owner를 확인한다. 최종 hash·검증 결과는 [리뷰 manifest](../../tmp/nonfixed-registration-source-review-20261015-1500/review-result.json)가 소유한다.
- 리뷰 범위의 미해결 구현 결함 0건이다. 과거 7건에서 제출됐을 것이라는 반사실 성공이나 수익을 만들지 않는다. 실제 프로세스 배포·재기동·실주문·신규 broker/provider 호출·외부 sync는 실행하지 않았다.

자연 수용 owner는 기존 `NonfixedDispatchReadinessReview1012`다. 검증본의 별도 적용 후 같은 lease의 기한 내 REG→지연 future→원 exact 0B/0D 검사→원 native 마감·cleanup→실제 Main 편입 또는 직접 대기 사유를 확인한다. 유효 기계 타점 이후의 AI·제출은 `AuxiliaryCircuitRecoveryRepair1012`에서 별도로 대사한다. 늦은 전송 2건·원천 부족 4건과 장기 슬롯 대기는 이번 연결 수리의 성공으로 닫지 않는다.
