# 9/11 위젯·에피소드 추천 승인 구현과 기동 준비

사용자는 추천사항 구현·배포와 다음 기동 준비, 결함이 없을 때까지 리뷰/수정을 명시적으로 요청했다. 자정 이후 원 source date는9/10, 준비 대상은9/11 아침/당일 예약이다. 이전 점검 뒤의 별도 실행 기록이며 [전수 점검](2026-09-11-full-recommendation-deployment-audit.md)의 당시 미구현 판정을 덮어쓰지 않는다.

## 적용 범위

현재18개 native 추천의 [승인 후속 원장](2026-09-11-widget-episode-approved-ledger.json)은 원67행의 subset이다. 구현3, 경제성 보류2, research-watch 보류7, 근거 차단2, 거절3, 관찰1로 전수 대사하고 누락0이다. 모든 추천을 적용한 것으로 보고하지 않는다.

| 적용 profile | 신규 신호 창 | 선택값 | 예약 preflight / live |
| --- | --- | --- | --- |
| 롯데케미칼 오후 기존 개선 | 14:25~14:34 | lookback15, drawdown0.5%, near-low0.05%, offsets−1/−2, target4 ticks | 14:20 / 14:24 |
| 롯데케미칼 정오 신규 | 13:15~13:34 | lookback45, drawdown0.75%, near-low0.75%, offsets0/−1, target2 ticks | 13:10 / 13:14 |
| LX세미콘 오전 신규 | 09:45~09:54 | lookback15, drawdown1.25%, near-low0.75%, offsets0/−1, target2 ticks | 09:40 / 09:44 |

세 profile은 원 producer의 calibration 양쪽·full·holdout·비용0.23%와 source quality 검증을 통과했다. 원 report SHA256 `c42fe91eb1c59bb9896775f223fade53b5998a8bd6b094c7d7aafb3bde284f73`, 승인 projection canonical SHA256 `4c46d6b7f4a72d38510230aac8c11cb900797412aa9506412e3ff428a09aff5b`를 보존했다. 롯데 오후 연구의 holdout HELD1은 미실현으로 보존하며 실현 순익에 합치지 않는다. 미래 신규 수익은 미관측이다.

영원무역 오전후반 calibration 후반 EV−0.000072%, 두산 정오 전반−0.003339%는 기존 preflight 경제성 gate 미달로 보류한다. widget7개는 source/sample/spread/volatility의 기존 implementation_review_ready=false, 거절3개는 holdout 실패,080220은 component 경제성/holdout 미완료,475560은 실행 증거 미완료다. 사용자 구현 승인 결손으로 다시 보류한 것이 아니며 원천을 합성하지 않는다.

## 리뷰·수정·검증

기존 role package의 profiles/policy_runtime/preflight와 low-price report consumer를 수정했다. 원래59개 profile은9/10까지 보존하고9/11부터61개/기존 quarantine3/실행 eligible58개다. 기존 보유 quantity·target·custody는 이전 policy를 유지하며 신규 profile은 두10주 leg와 기존 safety/weakness/timing-conflict를 따른다. 승인된 추가기능인 악화 보류와 WS 목표 상향·보조청산 pin은 유지한다.

초기 리뷰에서 새 symbol/window allowlist, launcher·제거 script, report 최초 운영일 연결 누락을 보완했다. 오래된 source candidate가 여러 revision을 넘을 때 승인 대상 외 actual 정책값을 보존하는지 재검증했다.9/8·9/9·9/10→9/11 전환, 과거 날짜 금지, 수량 보존, 증거/hash/음수 calibration 변조 차단, exact-date owner scope와 timer 연결을 검증했다. 관련389 tests PASS. 격리 fixture 결손은 원본 fixture만 복사했으며 canonical report 재실행/Provider/실주문은 없었다. 이번 변경과 직접 consumer 범위의 미해결 finding0이며 전체 저장소·미래 경제성 무결함 선언은 아니다.

LX세미콘은9/11부터 standing authority에 episode 소유권을 추가한다. 기존07:32 자동 owner-apply가 실제 broker/custody를 확인하고 미종결/모호한 소유는 원래 규칙으로 skip한다. 승인 artifact 설치가 실제 owner policy 발행이나 주문 성공을 의미하지 않는다.

## 배포 계획과 복구 경계

저가주 service/preflight template 두 개만90 drop-in으로 새 frozen `episode-recommendations-20260911`을 선택한다. 위젯과 삼성은 기존f9d53a9a/PID/pin을 유지한다. 새 타이머4개 설치와 롯데 오후 타이머2개 시각 갱신은 예정 기동을 준비하며 지금 매매 service를 기동하지 않는다. 공통 장후/PREOPEN은 기존939d90f6 수리에 profile 전환 및 최초 운영일 consumer만 추가한 검토 root를 선택해 다음 산출물 schema를 맞춘다. 메인 계산 리팩터링 미배포 항목은 이 machine 배포와 분리한다.

이전 release·원장·70/80 drop-in·timer/selector 백업을 보존한다. 철회는 진행 중 successor/기존 custody를 대사하고 새 entry만 닫는 기존 계약을 따른다. 신규 entry가 생긴 뒤 이전 코드로 즉시 되돌리거나 state를 지우지 않는다. 현재 장후source9/10 terminal과 V2.14 승인10개 코드 hash를 전환 전후 재검증한다.

## 실행 receipt

아래에 실제 선택 commit, 설치/검증 시각, 정책 pin 및 예약 확인 결과를 추가한다. 배포 성공과9/11 PREOPEN·PID·실제 신규 신호/주문·비용 차감 결과는 별도다. 기존9/11 MachineProfitStagnationStartupAcceptance0911 및 KRXDaily100NextDayStartupAcceptance0911이 자연 확인을 소유한다.
