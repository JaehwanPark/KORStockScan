# 2026-10-09 Stage2 To-Do Checklist

## 오늘 목적

- Main 보유청산·익절의 원천, 재생, 의미 감시 계약을 구현하고 반복 리뷰·표적 검증한다.
- Main 약세 관찰기의 기존 수리와 분리하여, 기존 자료 장후 연구 MW2–MW5를 구현·리뷰·검증한다.
- Main 공통 시장원천 활용과 마이크로 리버전 퇴역 잔재 제거를 구현·반복 리뷰하고 성능 수용을 별도로 검증한다.

## 오늘 강제 규칙

- 보유청산 요청은 후속 지시에 따라 공식 비용 원천 수집·소비 보완, 반복 코드리뷰·검증 및 미커밋 통합 배포까지 포함한다. 약세 관찰·연구는 후속 승인에 따라 기록 결함 수리·검증·배포·optional 예약 설치와 다음 예약기동 준비를 수행한다. Main 공통 시장원천은 사용자가 남은 G5 성능 항목을 설명받은 뒤 즉시 배포와 최종 릴리스 기준 다음 영업일 기동 점검을 지시했다. 성능 미완료 기록은 보존하되 이번 배포의 선행 차단으로 사용하지 않는다. 기존 정책과 새 코드의 연결·원천 무결성·PREOPEN 검증은 유지한다. 동일 정책의 코드 연결 갱신과 필요한 준비 인계 갱신을 수행하며 정책 재선정·휴장일 강제 봇 기동·원천 삭제·연구 재실행은 포함하지 않는다.
- 기존 하드스탑·보호·비상·주문·수량·freshness·Main/manual 소유권과 운영자 lock을 유지한다. 퇴역 episode/widget 자동 실행을 복원하지 않는다.
- 비용 미관측은 null과 원천 결손으로 남긴다. configured 비용을 실제 비용으로 대체하거나 원천 수리에 추가 경제성 승인 요건을 만들지 않는다.
- 후속 정책 평가에는 현행 policy-refresh 경계를 소비하며 10/12 checklist의 원 봉인본과 수동 OPEN을 보존한다. 승인된 release 변경에 필요한 자동 생성 구간과 준비 영수증은 정식 builder로 갱신·검증하며 당일 활성화를 앞당기지 않는다.
- Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다.

## 실행 항목

- [ ] `[MainMarketSourceConsolidation1009] Main 공통 시장원천 정리·퇴역 잔재 제거 성능 수용과 운영 인계` (`Due: 2026-10-09`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59; 후속 지시로 성능 미완료를 보존하며 배포·다음 영업일 기동 준비 점검`, `Track: RuntimeStability`)
  - Source: [상세 구현계획 MS0–MS6](../proposals/main-market-source-consolidation-and-micro-reversion-retirement-cleanup-implementation-plan-2026-10-09.md).
  - 이번 구현 범위: 생산자→Main 실시간/장후 소비자·정책 pin·생애 계약을 대조하여 MS0–MS5의 코드 전환·반복 리뷰·표적 검증을 수행했다. 공통 helper 이관, 퇴역 boot/feedback/deferred 구독 차단, 기본 raw writer의 detector/reference 계산 제거, 신/구 close 영수증 reader 이관, 명시 source 세대·물리 hash/정규화 재사용을 구현했다. [구현 리뷰](../audits/main-market-source-consolidation-implementation-review-2026-10-09.md). 기존 NS/H/HP/MW 미커밋 구현과 승인 범위를 보존하고 중복 owner를 만들지 않는다.
  - 수용: MS0–MS5의 직접 소비 명세, 공통 helper와 정책 code pin 동등성, 퇴역 명세 없는 Main 구독·단일 원천 저장, event-reference 소비 이전 후 불필요 계산 제거, 기존 장후의 동일 모집단·label·비용과 연결/결손 구분, T1–T8 및 문서 parser 검증을 닫는다. Main이 사용하는 비용·master·Provider 예산·완료봉·압축 원천 검증은 보존한다.
  - 구현 리뷰 보완: RV1–RV7의 Main probe 공유 observation-only 상태, 매도 후/비진입 후 exact route·기한, 생존 collector flag를 보존했다. 구 command는 wire 없이 거절하고 실제 `_send_reg_impl`에서 source를 검증한다. raw closed epoch·수신 clock·native/collector sequence namespace·압축 alias·source hash 변조를 반례 검증했다. 기존 frozen source·Provider 결과를 덮어쓰지 않으며 새로운 code binding은 기존 정식 handoff에 연결한다. prepared/PID·자연 strict→controller 소비는 MS6 미실행 사항이다.
  - 후속 코드 검증: writer 생성/registry 잠금 분리, percentile 단일 정렬, raw pre-event 틱 보관 제거와 순서/시각 검사 보존, 엄격한 역사적 정책 검증 및 미래 후보의 동일 정책 code refresh를 보완했다. 불변 후보 `main-market-source-20261009-review-v2`의 통합 영향 회귀 1,436건 통과·실패 0, 변경 Python 36파일 compile 통과. [후속 리뷰](../audits/main-market-source-consolidation-review-deployment-2026-10-09.md). 정책 재선정·Provider 호출 없이 원 payload/current/source를 보존하며 실제 발행은 미실행이다.
  - 성능 수용 OPEN: 각 3회·18,200행·200개 고유 exit fence에서 burst/느린 fsync의 필수 p95/p99/max 상대 기준은 통과했다. 정상 0D max의 후보 최악값 35.7422ms는 미통과이며 별도 진단에서 global GC 겹침을 재현했다. native→claim→machine은 199 claim/회·동일 결과 hash·새 만료 0과 상대 기준 통과다. 전체 Main loop 및 장후 cold/warm 전체 성능은 미관측이다. 다음 조치는 정상 0D tail와 전체 경로 성능 비교이며 종료 조건은 §7.3/T8/G5 통과다. CPU 개선이나 0B 절대 canary PASS로 대체하지 않고 guard·TTL·cap은 유지한다.
  - 후속 배포 완료(17:01 KST): 사용자가 G5 잔여를 보존하면서 즉시 배포하도록 명시했다. 검증된 commit `9d6cff39d0c9455386647612c18055d6825944d6`의 `main-market-source-20261009-v1`을 선택했다. 동일 정책 code binding, source 10/8 summary/strict/controller/finalization, 10/12 PREOPEN 전체 계약 검증을 통과했다. 앞선 미발행·준비 미실행 기록은 배포 전 상태다. 10/12 원 봉인본과 수동 구간을 보존하고 정식 builder의 자동 구간만 갱신했다. 예약은 07:35 PREOPEN·07:55 Main이며 실제 PID 소비는 false다. [배포·다음 영업일 준비 근거](../audits/main-market-source-authorized-deployment-and-next-preopen-readiness-2026-10-09.md). 자연 한 세션/PID/장후 소비와 G5 성능 수용은 후속 증거로 남긴다. 전략/Provider/상한 변경, 퇴역 실행 복원, 새 경제성 gate는 없다.
  - 배포 후 archive 경고 수리(21:14 KST): 휴장 EOD를 기다리는 archive와 21:00 감시 마감의 불일치를 수리했다. source calendar SKIP, 영업일 기본 90분 EOD 대기+압축 여유의 22:30 완료 마감, 22:35 최종 검사 및 즉시 FAIL 탐지를 작업본/불변 릴리스 각각 158건으로 검증했다. `main-archive-calendar-20261009-v1` (`9773aefb1fb8`) 선택 및 새 PREOPEN 전체 검증 PASS. 기존 archive 대기 PID만 종료하고 새 wrapper의 휴장 SKIP을 확인했다. 기계·보조 candidate/current bytes는 동일하며 Main을 기동하지 않았다. [수리·배포 근거](../audits/dashboard-archive-holiday-completion-repair-2026-10-09.md). G5와 자연 세션 수용은 앞선 OPEN을 유지한다.

- [ ] `[HoldingProfitExitSourceContractRepair] Main 보유청산 원천·재생·의미 감시 계약 보완` (`Due: 2026-10-09`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59`, `Track: RuntimeStability`)
  - Source: [구현계획](../proposals/main-holding-profit-exit-runtime-and-postclose-remediation-plan-2026-10-09.md)
  - 수용: HP0–HP5의 생산·저장·소비 연결 및 F1–F5·F7 표적 회귀, compile·diff·문서 parser 검증 후 반복 리뷰한다. 실제 비용 원천이 없으면 HP2 수집 완료를 선언하지 않고 부족 필드·후속 조건을 명시한다. 기존 초기 보유 AI 정책을 유지하고 HP6 후속 자동 최적화는 별도 범위로 남긴다.
  - 코드 완료: forward window·실제 비용 대사 소비/정정 세대·VETO live/replay·정책/PID 결속·signal별 진행/as-of·summary/checklist 연결 구현 및 반복 리뷰. 통합 회귀 1,846건, 마지막 비용 보완 후 관련 251건, PID 영수증 보완 후 관련 137건 통과. [구현 리뷰](../audits/holding-profit-exit-runtime-and-postclose-implementation-review-2026-10-09.md).
  - 초기 HP2 원천 검토(후속 보완 전): 공식 비용의 exact-execution 배분 의미가 미확정이고 실제 비용 파일이 없었다. 검증된 계좌 scope·Main owner·모든 BUY/ADD/SELL leg·거래일/route·원천 hash·명시 비용·revision/가용 시각을 생산하는 계약 확정 후 대사한다. 임의 일별 비용 배분·DB configured 값 교체·0 비용 보충은 금지한다. OPEN은 이 원천 후속 조건이며 코드 리뷰가 미완료라는 뜻이 아니다.
  - 초기 구현 회차의 운영 경계: 배포·재기동·장후 재생성·정책 발행 미실행. 초기 15셀·운영자 override·봉인된 10/12 checklist는 보존했다. 자연 비용 결손만으로 새 코드 결함 owner나 추가 초기정책 승인 gate를 만들지 않는다.
  - 후속 승인·원천 보완: 공식 `ka10076`·`kt00015`·`ka10170`을 추가 확인하고 bounded 수집→원자 원장→Main 전체 포지션 비용 대사→report/projection/manifest 연결을 구현했다. 실제 10/8 계좌 자료는 SK이터닉스 매수 20주·비용 130원이며 수동관리 보유라 Main 완료 손익으로 귀속하지 않는다. 초기 “수집 원천 없음” 기록은 현행 상태가 아니다. 부분/혼합 배분과 결제 대기는 null로 보존한다. 새 원천 구현의 코드리뷰·수정보완·통합 검증과 보유청산 포함 배포, source 10/8→10/12 준비 갱신을 아래와 같이 완료했다. [공식 검증](../../data/report/holding_profit_exit_deployment/2026-10-09/official-cost-followup-review.json).
  - 통합 배포·검증 완료(23:04 KST): 공식 원천 보완 및 테스트 HTTP/로그 격리를 반복 리뷰했다. 작업본 2,238건·최종 불변 릴리스 2,238건, 최종 hook 비용 회귀 30건·late-conftest smoke 1건 통과. `main-holding-profit-exit-20261009-v4` (`70945c531813`) 선택, source 10/8 summary/strict/controller/finalization과 10/12 PREOPEN current_full_contract PASS. 현재 활성 entry 포인터·정책 내용·수탁·초기 정책은 유지했다. 원천 수집과 검토 범위 코드 결함 보완은 완료이며 이 owner의 후속 비용 범위는 혼합/복수/익일 보유 배분 증빙이다. 자연 PID·청산·경제성은 완료로 선언하지 않는다. [최종 리뷰](../audits/holding-profit-exit-official-cost-source-integration-deployment-review-2026-10-09.md).

- [ ] `[MainMarketWeaknessPostcloseObservation1008] 약세 관찰 결함 수리·기존 자료 장후 연구 인계` (`Due: 2026-10-09`, `Slot: IMPLEMENTATION`, `TimeWindow: 09:00~23:59; 연구 실제 실행은 허용된 후속 배치의 야간 창`, `Track: RuntimeStability`)
  - Source: [구현계획 MW0–MW6](../proposals/main-market-weakness-observer-repair-and-postclose-research-implementation-plan-2026-10-08.md). [10/8 계획 owner](2026-10-08-stage2-todo-checklist.md)의 stable ID와 Acceptance를 인계한다. 과거 봉인과 미래 10/12 checklist는 보존한다.
  - 이번 범위: 앞선 MW0–MW1 코드 수리 종료 후 MW2–MW5 독립 장후 연구·optional 예약·관리자 outbox 구현과 반복 리뷰다. 추가 장중 hook·로깅·metadata·조회·계산·queue·thread·API/AI 호출을 만들지 않는다. 기존 보조 패턴연구·정책과 Main/manual 및 퇴역 경계를 보존한다. 앞선 회차는 코드까지 완료했다. 후속 수리·배포 승인에 따라 아래의 검증·선택 release·optional 설치·다음 기동 준비를 수행한다.
  - 코드 완료: 퇴역 실행 주장·상태 flag·legacy pending 모든 재전송 진입점·KST report 시각·정적 연구 계약을 수리했다. 관련 회귀 161건 통과 및 재리뷰. [코드 리뷰](../audits/main-market-weakness-observer-code-review-2026-10-09.md).
  - Acceptance 인계: MW1 회귀·재리뷰 선행과 selected observer 자연 소비를 분리한다. 실제 schema/라벨 선별 전 census, A/B/C/U·미래 join 금지·W/F/U 공통 분모·기계 단독/보조 PASS 이후 후보 분리, 1,000회 고정 안정성 진단·U/지연 민감도, 21:40~익일 05:40 최대 9회·합산 10분·자식 회수·동일 입력 delta 0을 검증한다. optional cron/stage는 기존 strict/PREOPEN·기동을 차단하지 않는다. 누적 수치 적격→현행 parent 확인→관리자 Telegram 의미 기반 중복 방지·receipt/정정 연결을 검증한다. 후보 없음·source gap·delivery uncertain을 성공/0으로 바꾸지 않으며 통계적 95% 보장·정책 자동 적용·주문 권한을 만들지 않는다.
  - MW2–MW5 첫 구현 회차: 실제 schema census·정확 label/ask 연결·A/B/C/U·저장 실제 AI 및 compact decoder·변경 partition/누적 cache·사전 고정 후보·1,000회 안정성/지연/U 민감도·사전 점검 포함 야간 예산/자식 회수·원자 outbox와 scope parent 재검증을 구현·반복 리뷰했다. 신규 97건 통과; 기존 live codec까지 확장 검증 397건 통과·아래 원천 결함 5건 실패. [구현 리뷰](../audits/main-market-weakness-postclose-research-implementation-review-2026-10-09.md).
  - 기록 결함 후속 수리: 기존 `ai_trace_dedup_preparation_pending` 5개 실패를 포함한 writer·동시 기록·codec 148개 회귀가 통과했다. 검증된 직전 구간의 mixed-row 인덱스를 이어가고 부분 JSONL·미검증 과거·파일 교체를 차단한다. 원장·추가 파일 재읽기·AI 호출을 늘리지 않았다. 정책·기록 형식·횟수는 유지하고, 자연 첫 기록 수용은 별도다.
  - 후속 배포 완료: 작업본/불변 릴리스 각각 572건 통과. `main-market-weakness-20261009-v1` (`7e1a826318e7`) 선택, ubuntu optional 야간 cron 1개 설치, 기존 필수 cron 8개 보존, 10/12 PREOPEN 준비와 source 10/8 finalization 원천 연결 PASS. 강제 봇 시작·연구 수동 재생성은 없고 실제 PID/자연 실행은 대기다. [후속 반복 리뷰·배포](../audits/main-market-weakness-review-deployment-2026-10-09.md). 배포/optional 설치와 실제 장후·알림/selected observer 소비/MW6 자연 수용은 구분한다. 미래 10/12 checklist·현재 정책을 보존하고 새 release 준비를 검증한다. 코드만으로 자연 정책 소비·수익 개선을 선언하지 않는다.
