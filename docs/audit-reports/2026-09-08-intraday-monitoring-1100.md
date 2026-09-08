# 2026-09-08 11:00 장중 모니터링

관찰 시작 10:39:51 KST. 요청 종료 11:00 KST. 아래 중간 시각의 receipt는 해당 snapshot이며 마지막 관찰은 후단에 기록한다. 대상 거래일 9/8, 전일 장후 source-date 9/7을 분리한다.

판정: 메인 submit drought와 micro 원천 신선도 결손이 남아 있어 전체 정상·경제성 성공으로 닫지 않는다. 독립 위젯의 실제 목표 체결과 에피소드 보유·목표 주문은 별도로 대사했다. 임계값 완화, 주문·취소, env/lock 변경, 재기동은 수행하지 않았다.

| 영역 | 직접 근거와 판정 | 후속 owner/조건 |
| --- | --- | --- |
| PREOPEN/main | PID461794, 09:27:19 시작. 저장된 당일 verify PASS/PID 일치, selected20. manifest env 중 override/AI 별도 owner를 제외한147키 재비교 mismatch0. canonical retirement15키 모두 PID에서 false. startup source f67a7ec7과 이후 작업트리 변경을 구분 | 기존 당일 runtime verify 완료 기록을 재사용. 정책 소비와 수익 효과는 별개 |
| 전일 요약 | 9/7 tower의 source7개 실제 SHA256 일치. 9/8 00:27:43 verifier warning/controller done receipt. 전일 성공을 당일 runtime 효과로 해석하지 않음 | PostcloseRecoverySourceAcceptance0908. 전일 wrapper나 Provider 재실행 없음 |
| 메인 KRX funnel | 10:50 sentinel SUBMIT_DROUGHT_CRITICAL. exact84=terminal77+pending7, submitted0, 미분류 terminal0. stage별 unique AI34/budget50/latency7은 각각의 분모이며 단순 직렬 전환율이 아님 | EntryRecheckNaturalAttribution0907 및 기존 drought workorder. source/AI/latency 최초 차단과 exact submit/fill/terminal 확인 |
| Scanner discovery | 09:15 census early_evidence_hold_sample, insufficient_evidence_scanner_recall. official master lookup·cadence·executable BBO/resolved/right-censor 기준 미충족. 독립 benchmark와 scanner 자체 분모 구분 | 기존 census12:00 자연 slot. scanner 정상 포착률·미관측 종목 EV를 주장하지 않음 |
| Post-promotion | 10:35 WS report attach/handoff466/466, heavy eligible223 중 미평가1. discovery와 다른 분모. 6개 source workorder는 defer_evidence | ScannerLookupAttentionNaturalEvidence0908 및 해당 source owner. 실제 full-fill EV와 marginal CF 분리 |
| Pruned observer | persisted audit schedule6148/observation600 events. 최근 local active8, pending8, daily scheduled320/1200, captured212/request-gap100, worker/receipt 오류0. event수와 unique episode수는 다름 | 관측된 hook 정상. resolved20·coverage95%·right-censor≤20% 전에는 선택/실주문 근거 불가. 전수 prune EV 외삽 금지 |
| Micro | 10:41 이후 유효 trade9263/depth7635 정체. 10:53:11 rejection666154, tail exchange→local receive 약187초, local receive→검사4~7ms. 10:44/10:54 main WS TCP Recv-Q 약0.12~0.32MB. 내부 미소비 backlog가 있어 외부 지연만으로 단정 불가 | MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908. 정확한 지연 발생 함수/구간은 미확정. source-only 진단 계속 필요 |
| Micro 저장/guard | writer3/3, trade/depth worker·writer 오류0, queue/drop0, disk 최소10.596GB. canary stop=false는 유효 source 회복이 아님. rejected64행 tail은 전수 exclusion 증거가 아님 | freshness guard와 Provider replay hold 유지. 과거 결손 합성/0EV 보간 금지 |
| AI | 10:44까지 일간 trace54. provider 미호출 preflight 차단23과 실제 transport timeout2를 구분. 관찰 중 10:41:52 entry_price Bedrock, 10:42:03 analyze_target OpenAI parse/semantic 정상, canonical context applied_exact | 현재 stale 입력 차단 유지. source-only metadata 종결을 Provider 비교·R3 승격으로 보고하지 않음 |
| Main holding/exit/smoothing | main submit/holding 없음. probe/residual/scale-in/exit·post-sell 및 smoothing의 실효 표본 없음. 독립 machine 보유를 main HOLD denominator에 넣지 않음 | valid-empty main holding. 정상 코드/설정과 경제성 미관측 분리 |
| Limit-down | 당일 manager heartbeat 갱신, candidate/slot0, source-only authority, 0B+0D 요구 유지 | healthy_no_natural_sample. ordered 자연 수용조건은 미완료, 실주문 권한 없음 |
| Widget005930 | buy0025036 10주274250 → target0025043 10주276500, 10:45:01 전량 체결. episode 닫힘/completed_entry_count1. 10:47:41 다음 신호는 기존20분 cooldown으로 차단 | 독립 위젯 owner 확인. 실제 수수료·세금 미대사로 realized_pnl=null/unreconciled_exact_cost. 단일 완료를 튜닝 개선량으로 주장하지 않음 |
| 승인 Widget080220 | exact-date policy/eligible 및 trader21846 유지. 현재 주문 표본 없음. 다른 research 후보에 권한 확대 없음 | WidgetEpisodeRecommendationApplyAcceptance0908. 원본65행과 승인 projection26행 중복 합산 없음 |
| NHN late morning | PID540578. 두10주 leg 중 target0032876은10:39:22 완료, target0032762는10주 유지. 전체 episode TARGET_OPEN | 부분 leg 완료와 전체 completed EV 분리. 동일 owner/custody로 목표 체결 대기 |
| 삼성중공업 morning | PID453121. 10주 target0018672 유지. 다른 leg0018068은09:29 유효기간 종료 취소 후 잔량0 기록 | 기존 보유 target 유지. 강제 시간청산 없음 |
| SD/SK late morning | SD545995, SK에터닉스552107, SK텔레콤552180. 예정 기동 후 READY/새 분봉 평가, 주문0 | 유효 자연 신호 대기. 미래 NHN13:25/13:29, SD14:10/14:14는 not_yet_due |
| 퇴역/자원 | ADM/LDM/greenfield canonical15 OFF, main/widget 중복 PID 미관측. 전체 CPU 약32~48%, 가용메모리 약4GB, iowait 약3.7% | not_applicable_retired_or_deprioritized. sim 성과/표본 모집은 열지 않음. 모든 프로세스의 broker 무호출을 전수 증명한 것은 아님 |

Broker 읽기 전용 조회는 기존 cached-token helper와 공통 rate gate를 사용했다. 10:42:43 KRX/NXT 잔고 검증 성공, 005930/010140/181710 각10주와 해당 매도3건을 확인했다. 당시 임시 출력의 주문번호 필드명이 잘못되어 번호가 null로 투영된 것은 점검 스크립트의 표시 문제이며 production parser 결함으로 분류하지 않는다. 최종 조회는 정식 ord_no 필드로 대사한다. owner registry는 intent별 최신 누적 체결을 사용하여 반복 receipt를 중복 체결로 세지 않았다.

부족 ledger는 기존 당일 OPEN owner의 범위를 재사용한다.

| shortage_id / 기존 owner | 분모·required/current/deficit | 최초 결손 / 상태 / ETA | acceptance |
| --- | --- | --- | --- |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908 | 새 유효 exact timestamp/route 원천 지속 유입; 10:41 이후 증가0. 고정 경제 floor를 이 진단에 추가하지 않음 | before_observer_enqueue freshness. blocked_missing_evidence: local backlog는 확인했으나 정확한 원인·회복률 미확정, finite ETA 없음 | guard 내 신규 수집 증가·정확한 loss 범위 또는 다음 clean date; through-close 연속성 |
| EntryRecheckNaturalAttribution0907 | KRX exact attempts84, submits0. 진단 보존식 deficit0, 실효 경제 floor/ETA는 미확정 | latency/authority 이후 submit 고갈. 단순 시간 해결형으로 분류 불가 | 기존 최근3거래일/controller/PREOPEN/PID와 실제 fill/terminal/net EV 연결 |
| EntryRecheckNaturalAttribution0907 / 외부 census 선행 | 최신 census KRX resolved8/20(부족12), coverage19/23=82.61%/95%; 09:15 source와10:35 promotion 분모 분리 | source/master/cadence·경제 label 결손, blocked_missing_evidence. 12:00은 관측 slot이며 floor 도달 ETA가 아님 | 같은 venue/session의 공식 master·SLA·유효 unique episode·선언 floor |
| WidgetEpisodeRecommendationApplyAcceptance0908 | widget005930 완료1은 확인; 승인080220 자연 주문0, NHN1leg 완료/1leg 보유. 미래 신규 window 아직 미도래 | 승인080220 효과 blocked_missing_evidence; 미래 machine pending_declared_window. 실현비용 미대사 | 승인 원본/projection/ID/당일 policy/PID/신호와 exact custody·비용 연결 |

검증 범위: write/backfill 없는 observation_source_quality_audit는52336 persisted events/74 stages PASS, hard-gap·unknown·exclusion0이었다. 이 검사는 enqueue 이전 micro loss를 포함하지 않으므로 전체 source-quality PASS로 확대하지 않는다. 거래 로직 보완의 확정 원인은 이번 snapshot에서 입증되지 않았다. 기존 OPEN ingress loss를 새 코드 수리 완료로 바꾸지 않았다. 이번 변경은 관찰 보고와 기존 checklist 근거 보충이며 문서 review gate·링크·print-only parser·diff 검증으로 닫는다.

근거: [당일 checklist](../checklists/2026-09-08-stage2-todo-checklist.md), [장중 지시문](../intraday-monitoring-task-instructions.md), [이전 due 작업](2026-09-08-intraday-due-work-execution.md). Canonical runtime/report 파일은 계속 갱신되므로 본문의 as-of와 마지막 보존 snapshot을 함께 사용한다.

마지막 관찰: **2026-09-08 11:00:09 KST**. [보존 snapshot/대사 evidence](2026-09-08-intraday-monitoring-1100-evidence.json).

- Main PID461794 유지. 마지막 완성 sentinel은10:55:03, exact86=terminal79+pending7, submitted0, 미분류0. 아직 생성 중인11:00 report를 성공 근거로 앞당기지 않았다.
- Micro11:00:05: 유효9263/7635 그대로, rejection723420, 최신 tail 지연198174~198837ms, TCP Recv-Q300593bytes. canary stop=false/worker·writer 오류0와 source 유효성 결손을 분리한다. 자연 회복·정확한 병목 수리는 미완료다.
- Broker10:57:33: KRX/NXT 완전 대사 성공. 010140/181710 각10주와 매도0018672/0032762 각10주만 존재. intent 최신 누적 체결 원장도 같은 owner별10주, 주문번호 owner collision0. 005930 위젯 완료 수량은 잔고에서 사라졌다. broker 대사는11:00 동시 조회가 아닌 해당 시각 snapshot이다.
- SK에터닉스10:56:04/SK텔레콤10:56:01 NO_TRADE, 두 unit Result success/exit0. SD는10:59 분봉까지 평가하며 READY/position0. NHN/삼성중공업 목표 보유는 그대로다.
- 문서 검토·근거 보충·재검토 후 링크 결손0, print-only parser PASS, 보충한 기존 OPEN ID 각각1회 파싱, git diff --check PASS. 거래 코드 변경·재기동·정책/주문 변경·비싼 report 재생성·외부 sync는 수행하지 않았다. 신규 단위테스트는 문서 변경 범위에 불필요하며, 미해결 micro 운영 결손을 review finding0으로 덮지 않는다.
