# 2026-10-17 Stage2 To-Do Checklist

## 오늘 목적

- 사용자 명시 지시의 비상시감시 호가·기회 전달 개선을 격리 작업본에서 구현하고 리뷰·수정·표적 검증으로 닫는다.
- 누적 보조판정 연구를 추가 600회 범위에서 실행하고 문구·입력 효과와 범위별 채택 후보를 분리한다.
- 후속 승인 600회를 누적 2,000회 상한에 연결하고, 입력 사실 역할·위험 표현 가능성의 통제 비교를 수행한다.
- 연구 입력의 운영 계약을 구현하고, 잔여103회 안에서 같은 RVP 입력의 실패 차단 문구를 실제 비교한다.
- 추가47회를 누적2,047회 상한에 연결해 기존50점에서 실제 현행과 최종 조합을 직접 비교하고 채택·인계 준비를 확정한다.

## 오늘 강제 규칙

- 기존 동시 작업과 원천·판정·정책 영수증을 보존한다. 코드는 선택 릴리스 기준 격리 작업본에서 검증한다.
- 코드 완료, 정책 등록·배포·재기동·PID 소비, 자연 제출·체결·비용 성과를 각각 확인한다. 개별 구현 완료만으로 운영 활성화를 주장하지 않으며 별도 승인된 배포 항목의 권한·증빙을 적용한다.
- 원 신호 5초·Main/manual custody·수량·provider·broker 및 hard safety 계약을 유지한다. 새 시간상한 선정에는 해당 원천·단계별 비교와 적용 계약이 필요하다.
- 문서 검증은 print-only parser만 사용한다. 외부 Project/Calendar 동기화는 사용자가 수행한다.

## 실행 항목

- [x] `[PostAuxiliaryPriorityDeployment1017] 제출병목 수리 통합 배포와 다음 영업일 기동 준비` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 배포·재기동 승인 및 다음 영업일 정상가동 점검 지시, [우선 수리 검증](../audits/main-post-auxiliary-priority-repair-review-2026-10-17.md).
  - 범위: 선택57d4d4664 위의 d942ba69b 수리와 필요한 정확 코드 인계를 clean release로 통합한다. 원 current/정책값·128연결·이미 승인된 두PRE 보조정책과 수동/custody·원5초/AI TTL·실패 이력을 보존한다. 추가50점 위험 입력 연구는 운영 적용하지 않는다.
  - Acceptance: source-exact delay/holding/stop 인계, native 기계 parity, 변경 family의 네트워크 차단 fixture, source10/16 summary/strict/controller와10/19 prepared full verify·보조 reader/미래 overlay 연속성·cron8개·전체 health 검증. strict_checklist_generation_stale를 직접 점검하고 원 세대를 보존한다. 현재 비영업일 정지/기동 가능 여부, 다음 정규 PREOPEN/실제 PID 소비와 자연 주문·경제성은 구분한다.
  - 완료: [배포·기동 준비 검증](../audits/main-post-auxiliary-deployment-and-next-session-readiness-2026-10-17.md). c5aeda844 실제 배포·선택 후 native full PASS,128범위/76,800행/598신호 parity mismatch0. 미래 bundleb521dfd93016·기존 두PRE overlay7a5d69b3059f 인계, 나머지126범위/rollback/current·원6OPEN 보존, 최종10/19 current_full_contract findings0. cron8개·전체7detector 계약/FAIL0·strict/controller 세대 issue0이며 기존 원천/과거 연구로그 경고는 유지한다. 토요일 PID 부재로 강제 재기동하지 않았고 실제10/19 PREOPEN/PID는 기존 DirectFamilyPreopenPolicyHandoff에서 확인한다. 새provider/주문0·원장복제0, 원 실패와UUID별 증빙 보존.

- [x] `[PostAuxiliaryKnownUnsentRepair1017] 미전송 최초 주문 의도·PASS 소비 상태 및 실제 전송 분류 수리` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 "우선순위 진행바람", [전체 가드 감사 G171/G174](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md).
  - 범위: 선택 `57d4d4664` 기준 격리 작업본에서 알려진 0회 전송의 Main/owner/bundle/PASS 상태를 멱등 종결한다. 불확실 전송·실제 broker 주문은 기존 수탁을 유지하고 같은 PASS 자동 재전송이나 원5초 연장을 만들지 않는다.
  - Acceptance: 로컬 veto·intent 이후 만료·context 생성 실패·인증/전송 불확실·재기동 복구·위조된 응답의 0회 주장에 대한 표적 회귀, producer/consumer 리뷰·수정·재리뷰. 운영 선택·정책·기동 변경은 구현 종료와 구분한다.
  - 완료: [우선 수리 검증](../audits/main-post-auxiliary-priority-repair-review-2026-10-17.md). 코드 d942ba69b의 미전송 상태/owner/bundle/재시작 경계 수리,528PASS·추가13/14/24표적 회귀·독립 리뷰 완료. 기존 원천/실패를 유지했으며 운영 배포·PID 소비는 수행하지 않았다.


- [x] `[PostAuxiliaryRiskContextResearch1017] 실패 위험 표현의 별도 입력 계약과 동일50점 비교` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 우선순위 진행 및 추가100회 승인(동일50쌍 비교), [전체 가드 감사 보조 의미 결함](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md).
  - 범위: 기존2,047회 사용·승인 체인·원 입력/응답/membership/라벨을 보존하고 총상한2,147회로 연결한다. 새 research-only version에서 해당 확인점까지 관측된 위험 사실을 표현하며 기존 RVP 코드 SHA·운영128연결을 보존한다. 정확 요청이 같은 control은 재사용하고 실제 신규 호출만 차감한다.
  - Acceptance: 후보/입력·분모·비교명세를 호출 전에 동결, 원천·위험 binding·기존 입력 불변·ASCII prompt·미래 정보 부재 검증, 동일50점의 TP/FP/FN/TN 및 비용후0.4%/30분/soft−3% 누적 기준 비교. 기존 표본 재사용을 독립 holdout이라 하지 않는다. 연구 성과와 운영 정책 발행을 분리한다.
  - 완료: [우선 수리·실제 비교 검토](../audits/main-post-auxiliary-priority-repair-review-2026-10-17.md). 연구입력176PASS/runner8PASS, cached50·new50·공통유효50·오류0·raw100응답 독립검산 완료. 누적2097/2147(추가50미사용), 원2047attempt 보존. RVP대조 TP32/FP12→후보TP29/FP10, PASS승률72.73→74.36%이나WIN보존84.21→76.32%, 두PRE외30점승률58.62→56.52%. 입력bytes+93.4%·토큰증가/빈어휘표본0/기존표본재사용 한계를 기록했다. 운영128연결·selector·PID 변경 및 추가 호출 없음.


- [x] `[PostAuxiliaryFinalSendClock1017] 최종 AI 유효기간과 가격 변경 미전송 종료 보완` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 우선순위 진행, [전체 가드 감사 G172/G173](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md).
  - 범위: 적용되는 기존 AI expiry를 최초 물리 전송·허용된 인증 재시도 직전에 재확인하고, 가격 변경은 명확한 미전송으로 종료한다. 자동 재가격·가격 추격·새 주문·TTL 변경 권한을 추가하지 않으며 후속leg·SELL에 최초 진입 TTL을 전파하지 않는다.
  - Acceptance: fresh quote/원5초 안에서도 AI만료 차단, 인증 지연·clock 역행·deadline 누락/변조, 가격 변경/동시intent/실제 전송 불확실 음성 회귀와 미전송 상태 대사.
  - 완료: [우선 수리 검증](../audits/main-post-auxiliary-priority-repair-review-2026-10-17.md). 코드 d942ba69b에서 기존 AI 실제 만료시각/원 monotonic 기준을 최종 전송 및 인증 재시도에 결속했다. 가격 변경은 미전송 종결이며 자동 재가격·TTL 연장·후속leg/SELL 변경은 없다. 영향 회귀 및 독립 리뷰 완료, 운영 미배포.


- [x] `[PostAuxiliaryScopedFunnel1017] 상시감시·스캐너 제출 분모와 미관측 상태 분리` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 우선순위 진행, [전체 가드 감사 평가 구조](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md).
  - 범위: 기존 scanner funnel 호환성을 보존하고 scope를 명시한다. fixed-watch native 신원·원 evaluation/trace 기반 집합과 전체 합집합을 구분하고 PASS 반환/Main 인수/adapter 호출/물리 전송/접수를 따로 전달한다. 종목·시각 추정 join이나 실제 비용 결손의0대체를 하지 않는다.
  - Acceptance: 재시도·scope충돌·신원결손·returned-only·로컬0회·실제접수·미관측 fixture, producer=분류+사유별제외+미관측 보존식, 최종 표시 consumer의 잘못된 전체0 해석 방지. 대용량 원장 재생·복제를 만들지 않는다.
  - 완료: [우선 수리 검증](../audits/main-post-auxiliary-priority-repair-review-2026-10-17.md). 코드 d942ba69b와 최종1051PASS·독립 원천 대사 완료. frozen14464행 PASS176/record155/명시인수134/접수15, scanner1 PID결손·신원결손551행·전송미관측 보존. 원장 복제/운영 보고서 재생성/배포 없음.


- [x] `[AuxiliaryNextSessionDeployment1017] 검증된 보조 입력·프롬프트 두 PRE 경로 배포와 다음 영업일 준비` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 배포·재기동 승인 및 다음 영업일 정상가동 점검 지시, [직접 비교 연구](../audits/main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md).
  - 범위: 원 10/16 연구·실패·정책·prepared 증빙을 보존하고, 두산/알테오젠 PRE/NXT 두 범위만 10/19 정확 부모와 검증된 입력 계약에 결속한다. 현재 Main/보조 pointer·다른126범위·원장·2,047회 차감을 유지한다. 검증된 코드·준비본의 통합 배포와 정상 기동 권한을 포함하며 주말 PREOPEN 또는 실제 날짜 우회는 금지한다.
  - Acceptance: 코드리뷰·수정·표적/영향 회귀, clean release·native code handoff·128범위 기계 parity·보조 reader/registry/source closure·미래 overlay·전체 next_preopen 준비 검증과 cron/선택 점검. strict/checklist 세대 원본을 보존하고 최종 해시 정합을 확인한다. actual PID 소비·장전 활성화·자연 호출·주문·성과는 관찰 시점과 증빙을 분리한다.
  - 완료: [최종 배포 검증](../audits/main-auxiliary-next-session-deployment-review-2026-10-17.md). 최종57d4d4664 배포·선택, 10/19 bundle327ab8912d3d/두PRE overlayba9243476f61 발행 및 current_full_contract PASS. 원128연결 중 두범위만 변경·기존current 불변, 최종128범위/1,559의존성·cron8개·strict/controller 세대 검사 PASS. health FAIL0이며 기존 수량비용/trailing원천·과거연구로그 경고는 보존했다. Main은 토요일 자연 정지로 actual_pid_consumed=false, 원19일6OPEN·07:35 PREOPEN→07:55 Main의 실제 소비는 DirectFamilyPreopenPolicyHandoff에서 확인한다. 새provider호출0·누적2,047/2,047회·원 실패와복구증빙 보존.


- [x] `[AuxiliaryDirectCurrentCombined1017] 실제 현행 대 최종 입력·문구 조합 직접 비교` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 추가 승인·진행 지시, [운영 입력·프롬프트 후속 연구](../audits/main-auxiliary-runtime-input-and-failure-screen-followup-review-2026-10-17.md).
  - 범위: 기존 차감1,997회와 모든 응답·실패·승인 체인을 유지하고 상한2,000→2,047회로 연결한다. 직전 동결50점·단일후보·라벨을 유지하며 후보50개 정확 요청/응답을 재사용하고 실제 현행 입력/프롬프트만 신규50회 호출한다. 새 표본·문구 선발이나 독립 holdout으로 부르지 않는다.
  - Acceptance: actual ask·비용0.23% 한 번·30분·net+0.4%·soft−3% 선도달 없음 라벨, 동일 확인점의 현행/최종 조합 직접 PASS 승률 우선/동률TP. 원천/요청/응답·cached50/new50·불확실·차감·시장/유형/경로 분모를 독립 대사한다. 두 PRE/NXT 준비 후보의 채택 판단과 운영 계약에 맞는 증빙·정확 부모/대상일/코드 인계 검토를 완료하고 코드리뷰·수정·검증 후 배포 지시를 대기한다. 실제 정책 발행·선택 변경·배포·재기동은 실행하지 않는다.
  - 완료: [실제 현행 직접 비교·native 수리 검토](../audits/main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md). 새 현행50호출·후보50응답 정확 재사용, 누적2,047/2,047회·미확정0. 전체20/30승→32/44승, PRE17/23승→29/35승; 두산/알테오젠 PRE/NXT3/3→8/8·1/1→7/7만 후보 확정. 실패12점 전부PASS·두 경로20점 모두WIN/2개 원천 구간 한계를 공개했다. 격리 HEAD `108c75f91`, source/read-closure·cold/warm·원장 무관쓰기 cache 수리 후 마지막47PASS·compile/diff·독립 리뷰 완료. actual50pair/100raw응답 검증 및 old/new128bindings 격리 준비PASS, 원실패ce83와 원증빙·registry/정책/selector 불변 보존. 10/16 부모 준비이며10/19 정확 code handoff/PREOPEN/PID 소비는 미증명이다. 실제 발행·배포·재기동은 지시 대기다.


- [x] `[AuxiliaryRuntimeInputFailureScreen1017] 보조판정 운영 입력 계약 구현·실패 차단 후속 비교` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 다음 액션 실행 지시, [완료된 RVP 연구](../audits/main-auxiliary-risk-role-contract-research-review-2026-10-17.md).
  - 범위: 기존 사실과 동결 RVP 변환에 동일한 opt-in 운영 입력 계약, registry·wire·응답·cache·provider identity·정책 인계 검증을 구현한다. 입력 원형·기존 정책과 hard safety는 유지한다. 적용 우선 후보는 비삼성 PRE·확장 패턴이며 AFTER는 별도 평가하고 REGULAR·삼성은 현행을 유지한다. 시장과 유형의 교집합 효과를 각각의 합계로 대신하지 않는다.
  - 연구: 직전 후보의 STOP6/TIMEOUT28 오통과·WIN34 오차단을 개발 진단으로만 사용하고 단일 새 프롬프트를 동결한다. 현재1,897/2,000회 차감을 보존하고 잔여103회 안에서 기존 노출을 제외한 정확 확인점 최대50개의 동일 RVP 입력 paired 비교를 진행한다. 정답을 보지 않는 시장/유형 표집과 원 응답·오류·차감·원천 구간 중복을 기록한다.
  - Acceptance: PASS 승률 우선/동률TP, 실제 ask·비용0.23%·30분·net+0.4%·soft−3% 라벨 고정, 요청·논리 입력·schema parity, 원 정책/연구 원장 비변경, 코드리뷰·수정·표적 검증·독립 분석·정책 인계 준비까지 완료한다. 정책 발행·선택 변경·배포·재기동은 실행하지 않는다.
  - 완료: [운영 입력·후속 연구 검토](../audits/main-auxiliary-runtime-input-and-failure-screen-followup-review-2026-10-17.md). 격리 커밋`ee0af6b48`, 표적·회귀155PASS 및 독립 코드리뷰 완료. 기존175점·새50점의 provider 입력/응답 parity, 격리된10/16 incumbent old/new reader128bindings/readiness 일치를 확인했다. 새50점 같은 RVP 입력의 prompt 비교는 PRE25/31승→29/35승(TP+4/FP불변), AFTER4/9승→3/9승으로 실패 차단 미개선을 그대로 기록했다. 두산·알테오젠 PRE/NXT 후보2개를 report에만 준비했고 모두WIN인20점·2개 원천 구간 집중과 raw현행→combined 미측정 경계를 공개했다. 신규100응답·미확정0, 누적1,997/2,000회·잔여3, 원장 참조 압축875,191B. 실제 정책 발행·선택 변경·배포·재기동·PID 소비는 없으며 배포일 정확 부모/비교/코드 인계는 별도다.

- [x] `[AuxiliaryRiskRoleResearch1017] 보조판정 사실 역할·위험 인용 계약 후속 연구` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 추가 호출 승인·다음 연구 실행 지시, [직전 연구와 오류 진단](../audits/main-cumulative-auxiliary-discriminative-research-review-2026-10-17.md).
  - 범위: 기존 1,363회 차감·영수증 보존, 1,400→2,000회 증액. 실제 현행 prompt/model/wire를 고정하고 spread 사실 역할·인용 가능성·현재 가격 진행의 인용을 별도 연구 계약에서 비교한다. 실제 운영 projector·정책·봇 상태는 변경하지 않는다.
  - Acceptance: 비용0.23%·30분·비용 후+0.4%·soft−3% 라벨, 동일 확인점 비교·원 응답·실패/예산 보존, PASS 승률 우선/동률TP. 기존 연구 key를 효과 평가에서 제외하고 과거 관찰 구간 중복·표본 가중·시장/유형 분모를 공개한다. 무조작·동일 payload는 정확 재사용하고 새 입력은 운영 발행에 사용하지 않는다. 연구 코드 리뷰·표적 검증·실제 호출·독립 회계 후 결과를 기록한다.
  - 완료: [후속 연구 검토](../audits/main-auxiliary-risk-role-contract-research-review-2026-10-17.md). 최초 과거 시도 목록 결함을 수정해467개 노출 key를 제외하고 선발25점·최종150점으로 수리했다. 최초 결과·선정·실패·차감을 보존한 회복 비교이며 미관찰 holdout으로 부르지 않는다. 최종 현행61/97승(62.9%)→ROLE_VOCAB_PATH73/107승(68.2%), TP순12개 증가·FP순2개 감소다. 비삼성 PRE 개선·REGULAR 악화·삼성 REGULAR표본0을 분리했다. 신규534응답(원408+수리126), 누적1,897/2,000회·잔여103회·새 미확정0개, 기존17요청 재사용. 표적49PASS·compile/diff·독립 코드/분석 재리뷰 완료, 격리 커밋`2b3ddbb4d`. 참조 압축 구간4,884,631B이며 공유 pack 전체를 배타 증가량으로 세지 않는다. 정책 발행·배포·재기동·PID 소비는 수행하지 않았다.

- [x] `[AuxiliaryDiscriminativeResearch1017] 누적 보조판정 문구·인과 입력 실제 비교 연구` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 상세 연구 정의 및 실행 지시, [연구 계획](../proposals/main-auxiliary-prompt-research-and-intraday-adoption-plan-2026-10-08.md), [직전 누적 결과](../audits/main-cumulative-auxiliary-research-implementation-review-2026-10-16.md).
  - 범위: 유효 누적 원천·실제 현행 프롬프트 고정, 기존 연구와 구간을 분리한 문구 비교·입력 2×2·최종 평가. 기존 800회 사용량을 보존하고 신규 600회로 누적 1,400회 상한을 연결한다.
  - Acceptance: 비용 0.23%·30분·비용 후 +0.4%·soft −3% 선도달 라벨, 동일 입력 paired 호출·원 응답·실패 예약 보존, PASS 승률 우선/동률 TP, 범위별 분모·미확정·반복 구간·예산·원장 증가량 공개. 입력 실험은 운영 호환성과 분리하고 정책 발행·배포·재기동은 실행하지 않는다.
  - 완료: [실행 연구 검토](../audits/main-cumulative-auxiliary-discriminative-research-review-2026-10-17.md). 실제 새 응답 545개·발송 전 실패 18개 차감 보존, 누적 1,363/1,400회. 최종 150쌍 전부 유효, E2 PASS 승률 14/109(12.8%)→17/113(15.0%), TP 순3개·FP 순1개 증가. 정규장 승리 회복과 PRE/AFTER 악화를 분리했고 새 입력은 미선정했다. 원천·동결 membership·요청·예산 대사 및 표적 코드 검증 완료. 원장 참조 압축 구간 약5MB이며 공유 DB의 사전 크기 부재로 배타적 신규 증가량은 미확정이다. 정책 발행·배포·재기동·실제 PID 소비는 수행하지 않았다.
  - 후속 진단: 기존/확장 입력의 spread 위험 역할 차이와 FN20·FP96의 실제 근거를 보존했다. 입력 역할 차이의 인과 효과는 미검증이며 이번 최종 후보·운영 입력은 바꾸지 않았다. 격리 소스 커밋 `3bac6258e`.

- [x] `[NonfixedQuoteOpportunityDelivery1017] 비상시 호가·원천 전달·전송 직전 검증 구현` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 구현·반복 코드리뷰 지시, [최종 보완계획](../proposals/nonfixed-quote-freshness-and-opportunity-delivery-remediation-plan-2026-10-17.md), [사전점검](../audits/nonfixed-quote-remediation-contract-preflight-review-2026-10-17.md).
  - 범위: canonical 설정 조회·source-wait 경합·exact 0D wake·quote-only bounded 재계산·원천/정책 시각 영수증·Main 최초 진입/분할 leg0 물리 전송 직전 검증.
  - 완료 기준: 생산자→소비자·결손·경합·원 기한·중복·auth retry·미전송/불확실·후속 leg/SELL 비전파를 리뷰·보완하고 표적 pytest·compile·문서 링크·parser·diff 검사를 통과한다. 선택 정책/운영 환경/배포/기동/실주문은 별도 권한이다.
  - 완료: [구현 리뷰](../audits/nonfixed-quote-opportunity-delivery-implementation-review-2026-10-17.md). 통합1,610 PASS, 기존 node1개는 선택 부모의 같은 실패를 직접 재현해 별도 보존. Python21개 compile/name 검사·로컬 링크·parser·diff 검증. 새 age 상한 미선정, 정책/선택/배포/재기동/PID/자연 주문/체결/성과는 별도다.

- [x] `[NonfixedQuoteDeploymentIsolatedPolicy1017] 비상시 호가 수리 배포 및 격리 정책 검증` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 명시 배포·격리 프로세스 정책 읽기/스키마/코드 호환성 검증 지시, [배포 검증 기록](../audits/nonfixed-quote-deployment-and-isolated-policy-review-2026-10-17.md).
  - 범위: 원 정책/장후/PREOPEN 영수증을 보존하고 exact code handoff·네트워크 차단 격리 검증 뒤 다음 정규 기동용 선택을 갱신한다. 새 TTL 선정은 필수가 아니다. 운영 봇의 주말 기동·당일 PREOPEN 우회·수치 재선정·실주문은 포함하지 않는다.
  - Acceptance: 새 코드의 원 128범위 native parity, 원 prepared 정책의 정확한 해시·reader·지연/보유/손절 코드 인계, current full preparation 검증 및 선택 CAS. 원 active pointer/env 불변·실제 PID 소비 false를 각각 확인한다.

  - 완료: `a41ebc84f` 다음 정규 기동용 배포, 격리 read/schema/code·128범위 parity·사후 current_full_contract PASS. 기존 env/정책·원 6개 OPEN·actual_pid_consumed=false 보존. [최종 배포 검증](../audits/nonfixed-quote-deployment-and-isolated-policy-review-2026-10-17.md).

- [x] `[InitialQuantityResearchRepair1017] 최초 수량 연구 입력·비용 대사와 전체 거래 EV 선정 수리` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 다음액션 실행 및 익절 가중 후보 생성·전체 거래 비용 후 EV 최종 선정 확정, [수량 후속 연구 계약](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#7-2026-10-17-후속-연구-실행-계약).
  - 범위: 최신 선택 코드 기준 격리 작업본에서 IQ171–IQ175의 재현 여부·원천 세대를 고정하고 남은 날짜/입력 보존 및 v3 선정기를 수정한다. 비용·capture는 거래/attempt별 검증 복구·역사 결손·추가 원천 대기를 구별한다.
  - Acceptance: bounded 원천/fact 및 실제 이벤트 모수 대사, 전체 거래 EV·순이익 선정·원금/비용/부분체결·독립 holdout·v2/v3 stage 호환 회귀, 적격 fixture 성능·실제 source-gap 구분, 코드리뷰·수정·재리뷰와 print-only 문서 검증. 새 정책의 경제성·PREOPEN/PID 자연 소비는 별도 영수증으로 확인한다.
  - 완료: `c4467c424` 격리 구현·독립 리뷰·수정·회귀900개와 보완 의미감시71개 PASS, 입력3일·compact112/112·실제 lineage8발행/1유예/10leg PASS. v3 전체 거래 EV 선정과 구 v2 reader 호환, 전수 fixture 결과 동등·캐시·성능 예산을 검증했다. [최종 실행·배포 검토](../audits/initial-quantity-research-execution-review-2026-10-17.md).
  - 배포: 10/19 다음 정규 기동용 선택·준비본 발행, native current_full_contract·strict/controller·release/cron/PREOPEN/start 경로 대사 PASS. 기존 정책값·승인 보조2개·원 OPEN6개 유지, 재시작/주문0·actual_pid_consumed=false다. fact16/완료13/보유3·비용 적격0의 정확 비용/귀속 결손은 InitialQuantityProducerConsumerRepair1010, 실제 PREOPEN/PID는 DirectFamilyPreopenPolicyHandoff가 계속 소유한다.


- [x] `[PreSubmitDelaySituationResearch1017] 매수 지연 선정 근거·재점검 연결·단기 관측 연구 구현` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 연구 방향·다음 액션 구체화 및 실행 지시, [연구 계약](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md#후속-상황-연구단기-관측-실행--2026-10-17).
  - 범위: 선택c5 기준 격리 구현·독립 리뷰·원10/16 봉인 자료 재분석, exact 재점검/종결 연결, 버전별1/3/5초 관측·원native 기준가·의미감시·bounded evidence 읽기. 현재0초·원 정책/원장·보조 입력/응답을 보존한다.
  - Acceptance: 3.2초 지연 관측·P0 시각·미래/과거 호가 혼합·회차예산·만료/예외/불확실·과거 projection hash·후보별pair/고정split/fallback·원천/출력 한도 반례를 검증하고 원문 bytes와 분모를 대사한다.
  - 완료: [구현 검토](../audits/pre-submit-delay-situation-research-implementation-review-2026-10-17.md). 원287기준점/P0238/실행기준286쌍·231cell을 확인했다. price_ready99cell의 양수0, signal_ready양수2는 같은8기회의 중복 유형이다. 코드 완료·연구 생성과 정식 배포/다음 자연 단기 관측·재점검/경제성은 별도다. 실제10/19 PREOPEN/PID 소비는 기존 DirectFamilyPreopenPolicyHandoff가 소유한다.
