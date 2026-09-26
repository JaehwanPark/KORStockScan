# 2026-09-25 스캘핑 익절 강약 기계판정 구현 검토

## 판단

M1 기계판정, fast/normal 익절 소비, 3시장 3수익축 정책·bootstrap, 장후 직접 원천 재생 및 분류기 민감도 보고를 코드에 연결했다. 이 기록은 코드 검토와 합성 실행 증거다. 선택 릴리스 설치, 실제 PID 소비, 자연 완료 포지션의 비용 후 성과를 증명하지 않는다.

검토에서 WS 알림 반복이 넓은 호가 REST 재확인을 증폭하는 결손, 익절 arm 이전 분류 상태 미갱신, 원천 만료 후 강 상태 부활, 장후 분류기 후보 계산 누락, 0B 방향 출처 검증 누락을 발견하여 수정했다. 재검토 결과 새 후보는 보고 전용이며 구 4축 영수증은 새 익절 bootstrap에서 거절된다. 75점 scalar의 soft-stop 소비는 보존된다.

## 계획 대비 재점검

| 계획 단계 | 코드·합성 결과 | 판단 |
| --- | --- | --- |
| R0 원천 계약 | 기존 0B/0D route·epoch·순번·수신시각의 bounded 이력, 공식 부호 원천 및 0D 최우선 가격·잔량 대사 | 구현. 과거 329건은 새 직접 경로의 수익성 증거가 아님 |
| R1 판정·소비 | fast/normal의 TP 폭 선택은 M1, 손절 score는 별도. 재시작·만료는 `UNKNOWN`→약폭. 0D batch를 event-time peak·bid·강약으로 재생하여 첫 crossing과 폭을 latch | 합성 batch 첫 약폭 crossing 및 이후 strong 전환 회귀 통과 |
| R2 장후·bootstrap | 3시장 9값 영수증, 구 4축 거절, 직접 완료·비용 모수, 3수익축 및 분류기×폭 보고 전용 재생, sentinel/summary 전달 | raw 0B 가격·0D 호가·first crossing 대사 및 80건 합성 재생 통과 |
| R3 릴리스 | 선택 릴리스 설치·실제 PID 소비 및 전환 영수증 | 이 기록 시점에 미실행. 별도 배포 영수증으로 확인 필요 |
| R4/R5 자연 경제성·후속 조정 | 자연 M1 완료·체결·비용 표본과 독립 holdout 필요 | 적용 후 관측 대상. 초기 전환 선행 게이트로 사용하지 않음 |

## 공식 원천과 실행 증거

- 키움 공식 저장소 `Kiwoom-Securities/Kiwoom-REST-API` commit `953e5dbff123f437ab4d11a78a95191a685eb51f`를 2026-09-25 16:53 KST에 확인했다. 이 revision에는 `kiwoom_docs`가 없었다. `kiwoom/_data/kiwoom_api_spec.json`의 0B/0D 정의와 `kiwoom/realtime/decoders.py`를 확인했다. 0B FID15의 부호, 0D FID41/51 가격·61/71 잔량·121/125 합계, 로컬 `docs/kiwoom-api-data-contract.md`를 대조했다. 신규 구독이나 API 요청은 추가하지 않았다.
- 관련 보고서·bootstrap·리뷰·WS/시세 회귀: 133 + 297 + fast 감시 69건 통과. fast 감시의 NXT 주문 영수증 2건 실패는 변경 전 `HEAD` 별도 worktree에서도 같은 `pending_submit_integrated_venue_context_invalid`로 재현했다. 이 작업 범위에서 주문 영수증 검증을 완화하지 않았다.
- 합성 완료 포지션 80건의 새 장후 재생: wall 0.824초, CPU 0.824초, 최대 RSS 42.5 MiB, 원천 결손 0건, 분류기·폭 연구 시나리오 210개. 같은 입력의 구 4축은 새 정책 세대와 맞지 않아 80건 모두 원천 결손으로 분리되므로 속도 비교 기준으로 쓰지 않는다. 분류기 120행 bounded 이력 1,000회 재계산: p50 0.577ms, p99 0.587ms, 최대 0.613ms. 이 수치는 합성 계산이며 실제 fast loop, lock 경합, API/주문 지연이나 자연 비용 후 EV가 아니다.
- 후속 합성 fast pre-arm 1,000회: wall/CPU 각 0.119초, p50 0.077ms, p99 0.123ms, 최대 35.899ms, 프로세스 최대 RSS 150.7 MiB, 추가 REST 호출 0회. 이 수치는 수정 전 고정 0D snapshot 반복이며 변경 후 실행시간으로 쓰지 않는다.
- 수정 후 새 0D 2,000건을 두 스레드·서로 다른 포지션으로 생성하여 공통 lock 아래 분류·event replay를 실행했다. 로그 기록은 성공 반환으로 모의했다. wall 1.067초, CPU 1.075초, p50 1.103ms, p99 1.356ms, 최대 4.757ms, RSS 144.4 MiB, event gap 0건, 추가 API 요청 0건이다. 실제 구조화 로그 쓰기와 전체 fast loop·주문 지연은 포함하지 않는다.
- 수정 후 fast pre-arm 진입점 전체를 신뢰 가능한 신규 0D/0B 1,000쌍으로 반복했다. 시세·구조화 로그·REST를 모의한 동일 조건에서 wall/CPU 0.933초, p50 0.938ms, p99 1.003ms, 최대 1.103ms, RSS 139.0 MiB, event gap 0건, REST 호출 0건이었다. 실제 I/O와 주문 경로의 지연 상한은 아니다.
- 수정 후 첫 약폭 crossing→같은 batch에서 strong 전환한 합성 완료 포지션 80건: wall/CPU 0.942초, RSS 41.4 MiB, `mechanical_direct` 80건, 원천 결손 0건, `UNKNOWN/WEAK/STRONG` 노출 각 80건. 분류기 연구 후보는 보고 전용이며 최신 독립 날짜가 없는 이 데이터로 수익 우위를 판정하지 않는다. 원천 0B 가격·first crossing timestamp 변조는 각각 source gap으로 거절했다.
- 관련 경로 회귀 526건 통과. 별도 2건의 NXT 주문 영수증 테스트는 변경 전 clean HEAD worktree에서도 재현된 `pending_submit_integrated_venue_context_invalid` 실패로 분리했다. 이 작업에서 주문 안전 계약을 완화하지 않았다.
- 수정 Python 파일의 `py_compile`, `git diff --check`, 문서 print-only parser가 통과했다.

## 릴리스 경계와 잔여 관측

- bounded 이력의 새 0D를 빠짐없이 event-time 순서로 재생하고 그 시각까지의 0B 가격으로 peak를 갱신한다. 분류·재생은 동일 포지션 lock 안에서 수행한다. 알림 병합 시 첫 crossing을 이전 weak 폭으로 latch하며 normal도 같은 latch를 소비한다. 누락·역전·현재 평가시각보다 오래된 중간 호가는 `classifier_event_time_gap`으로 장후 후보에서 격리한다. 이때 live는 현재 유효 호가의 기존 TP 경로를 계속 평가한다.
- 분류기는 새 메시지당 최대 120개 bounded 이력을 다시 훑는다. 따라서 입력 이력 크기에는 상한이 있지만 전체 fast loop, 실제 로그 I/O, lock 대기 꼬리와 자연 장후 성과의 검증은 별도 운영 영수증이 필요하다. 위 모의 수치는 이 경계를 넘는 성능 보증이 아니다.
- 2026-09-25 일일 checklist 파일이 없어 현 날짜의 executable OPEN owner를 확인하거나 변경 항목을 현재 checklist에 연결하지 못했다. 미래 2026-09-28 checklist를 오늘 owner로 대체하지 않는다.

이 코드 검토는 live PID 소비나 자연 비용 후 EV를 뜻하지 않는다.
