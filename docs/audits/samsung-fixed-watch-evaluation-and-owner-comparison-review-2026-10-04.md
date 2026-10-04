# 삼성전자 고정감시 평가·Main/Widget 대조 검증

## 1. 결론

[실행계획](../proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md)의 세 작업을 실행했다. 원watch/date와 가격 episode를 분리하는 평가기를 구현했고, 실제 Widget 체결·custody·정책·비용과 장전 Main 원판정을 대사했으며, 선행 두 후보를 고정한 이후 날짜 intake/replay를 준비했다. **새 운영 유효 정책은 확보하지 못했다.** 이후 날짜 성능은 자료 생성 전이므로 미검증이다. 실정책 발행·매매·API/provider·수집 확대·배포·재기동은0이다.

코드는 [offline 평가기](../../src/engine/scalping/samsung_fixed_watch_evaluation_research.py), 회귀는 [표적 테스트](../../src/tests/test_samsung_fixed_watch_evaluation_research.py)다. `src/engine` root나 live caller를 추가하지 않았다. 기존 normalized 관측·model capture·pure formula를 소비하며 Kiwoom request/response parser/FID/REG/인증/복구를 변경하지 않았다.

## 2. 평가 단위와 전용 이식 결과

전용 모집단은 `005930/KRX/KRX_REGULAR/MAIN_FIXED_WATCH` 원native가 있는206개 판정이다.9/30 46개,10/2 160개지만 원watch cluster는 날짜별1개다.9/29의313개는 scanner 또는 native 결손이며 전용 학습으로 바꾸지 않았다. 전체519개와 전용206개를 혼합하지 않았다.

|고정 후보|원선정 모집단의9/29~30 학습|고정감시 전용9/30 학습|전용10/2 원binary|
|---|---|---|---|
|기존 ENTER parent|3/6=50%|0/1=0%|3개 ENTER가 미도달로 binary null|
|foreign=up veto|2/3=66.67%, 원지원 날짜9/29만|선택0, 승률 null|선택0|
|과거180초 endpoint program_change=down|3/5=60%, 원지원 날짜9/29·30|0/1=0%, 기존과 동일|기존3개 ENTER 유지, 결과 null|

두 후보의 원선정 학습 metric을 exact 재생했다. 삼성전자 전체 origin에서의 개선을 전용 fixed-watch 개선으로 제시할 수 없다. 전용 binary 결과가 null인10/2는 실패0%도 성공100%도 아니다. 기존 성공100%/80% 보존 veto는 없다.

### 가격 연구 episode

원watch를 최초 관측한 뒤 같은 독립 보관 stream epoch에 있는 신호만 연결했다. 원native를 유지하고 별도 `research_episode_id`를 붙인다. actual Main closed episode 지원은 여전히0이고 Widget flat/terminal을 빌리지 않는다. 같은 admission/date는 하나의 fold이며 episode 수는 독립 native 수로 승격하지 않는다.

|고정 룰 / 같은 barrier 종료·비용0.23%|9/30 가격 episode|평균 가격 CF|10/2 가격 episode|
|---|---|---|---|
|기존 parent ENTER|1개 확정, 양수0|−1.14408%|최초1개 검열|
|base_recovery:300:5|3개 시도, 확정2·양수1·검열1|−0.40984%|최초1개 검열|
|absorption_release:300:5|3개 시도, 확정2·양수1·검열1|−0.41016%|최초1개 검열|

학습 가격 양수 비율50%는 기존0%보다 높지만 지원은9/30 하루·원watch1개다. 이를 충분한 운영 개선으로 판정하지 않는다.10/2는 원watch 확인 전 신호를 빼고 재생하면 최초 미해결 모델 보유가 이후 신호를 막는다. 이는 모델의 비중첩 계약이며 실제 broker가 계속 보유했다는 증거는 아니다. [선행 가격 연구](samsung-policy-episode-replay-research-review-2026-10-04.md)의2개 양수 구간이 사라졌거나 전부 실패했다는 뜻도 아니다. 당시 전일 전체 가격 실험과 이번 as-of watch 연결 실험은 분모가 다르다.

일별 양수 비율 평균과 episode Wilson 진단값을 함께 기록했다. 상관 미조정 episode Wilson을 운영 신뢰구간으로 사용하지 않는다. 현재 generic publisher30/10은 그대로이며 전용 `비중첩 episode + 원watch/date cluster` 계약은 등록 전 제안이다. 실제 producer/consumer 등록·cluster 지원량·비용 후 rolling/cumulative/version gate를 대신하지 않는다.

## 3. Widget 실제 거래와 비용

10/2 BUY 08:19:15→SELL 09:24:30, 약65.25분이다. 실제 NXT 체결, 최초 세션 `NXT_PREMARKET`,10주를275,500원에 사고277,000원에 팔았다. Widget 동일 custody의 양쪽 `ORDER_TERMINAL`, full filled quantity/notional, 같은 policy hash를 exact 대사했다.

- 체결금액 기준 gross 차익15,000원.
- 기록된 설정비용률0.23%를 매도금액2,770,000원에 적용하면6,371원.
- **설정비용 차감 추정 순손익8,629원, 수익률+0.313212%**다. broker 정산 비용·확정 net PnL receipt로 표시하지 않는다.
- 실제 장전 target40bps는 gross 목표이며 tick 올림으로277,000원이다. 정규장 설정은80bps다. 장전40bps를 정규장 후보에 이식하지 않았다.

원비용 계약은 `sell_notional_times_rate_once`, 설정 source hash `ef090d9d…`다. 원Widget policy hash는 `43c6a845…`다. 기록의 cost code SHA와 현재 코드 검증을 당시 PID 적용의 새 증거로 바꾸지 않는다.

## 4. 새로 연결한 장전 Main 두 판정

정규장 연구160건의 첫 판정은09:26:08이며 Widget 청산 뒤다. 전체 원projection에는 별도 `PREMARKET_KRX_LIKE` Main 판정2개가 있어 원capture canonical hash까지 연결했다.

|당시 Main 판정|원RECHECK 이유|당시 ask|동일 Widget 청산가격·동일 설정비용 point 진단|Widget 대비 진입가격 효과|
|---|---|---|---|---|
|08:13:59|SETUP_DISCOVERY_RECHECK; no_supported_setup/CONFIRMATION_MISSING|274,500원|+0.678652%|+0.365440%p|
|08:36:57|MICRO_PRICE_RESPONSE_RECHECK; micro_continuation_unconfirmed/CONFIRMATION_MISSING|275,500원|+0.313212%|0%p|

08:36은 Widget 실제 보유와 겹치며 매수 ask도 실제 Widget 매수가와 같다. 원Main은 신뢰 매수 flow/양의 가격반응·tape·유동성 기회를 보고도 micro 연속성 확인 부족으로 `RECHECK_DOMINANT`를 선택했다. 이2개 원판정의 actual order/fill 관측은false다. 이 증거 범위의 미진입 원인은 주문 체결 실패가 아니라 진입 판정·확인 경로다.

08:13의1,000원 가격 차이는 고정 종료가격에서+0.36544%p의 point 차이를 만든다. 전체 보유 경로의 stop/exit/guard·08:19 Main 입력을 재구성한 결과가 아니므로 “더 일찍 진입하면 실제로 이겼다” 또는 운영 패턴이라고 결론내리지 않는다. 두 판정을 정규장 후보 학습에 합산하지 않았다.

Main의 원보수비용은 각각0.32105%/0.32075%다. gross에서 그 추정비용을 차감하는 별도 point 값은+0.589697%/+0.223715%다. Widget의 동일 설정비용을 쓴 진입가격 비교와 이 비용 sensitivity를 분리했다. 더 작은 비용을 Main의 실제 비용으로 교체하지 않았다.

## 5. 정규장 동일 ask의 종료 수식 대조

11:01·11:34·13:04 원ENTER의 같은276,000원 ask에 연구 Main barrier(순목표+0.1%·gross stop−0.7%·20분)와 Widget 정규장80bps target278,500원을 적용했다. 수식만 대조하며 실제 Main 전체 holding/exit, Widget scale-in·target ratchet·guard/order queue를 재현하지 않는다.

- 앞의2개 Main 경로는 prefix가 약6.5분/5.2분에서 중단되어 검열이다.
- 13:04 Main20분 가격 종료는 bid275,000원으로 설정비용 후CF−0.591486%다. 실제 거래 손실이 아니다.
- Widget 목표는3개 모두 유효 prefix에서 관측되지 않았다.20분 강제 청산이나 손익0으로 만들지 않았다. **양쪽 확정 비교0개**로 종료 규칙 우열은 미확정이다.

target을 넘는 bid가 생겨도 Widget의 resting limit보다 좋은 체결가를 가정하지 않는다. Main exact-date bootstrap은 net trailing arm0.4%, weak/strong giveback0.4%/0.8%, `mechanical_strength_v2`지만 이 파일만으로 당시 PID의 소비를 확정하지 않는다. 이전 고정폭 trailing/time 탐색을 반복하지 않았다.

## 6. 이후 날짜 준비와 대기

`frozen-candidates.json`에는 원parent `d94fecaf…`, 두 selector/과거180초 간격, 원학습 결과,10/4 이후 날짜 제한, 재선정 OFF, dependency SHA를 봉인했다. 현재/당일 parent 및 원bundle이 바뀌면 재계획으로 차단한다.

기존 자동 생성 native projection·원capture·보관 체결/호가가 생기면 `--prepare-date`로 정규화 capsule 생성→원판정/guard/label/native/비용·canonical capture·독립 stream epoch 대사→고정 후보 재생을 수행할 수 있다. 개별 provenance 불량은 exclusion ledger로 격리한다. 신호 source unknown은 parent 승계다. 실제10/2 원천을 intake 정상 경로 테스트에 사용했지만, cutoff를 바꾼 **단위 검증 fixture**이며 새로운 held 검증으로 계산하지 않았다.

10/6 준비 CLI도 실행했다. 현재 필요한4개 경로가 없어 `waiting_new_source_date`; 수집·API 호출·후보 재선정0이다. 이후 source readiness와 경제성 수용은 별도이며 운영 승격은 하지 않는다. 실행 명령은 [계획§6](../proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md)에 고정했다.

## 7. 리뷰·보완·검증

초기 리뷰/회귀에서 optional contract의None 처리, frozen kernel 필수 binding, derived projection/capture만 신뢰하는 경로, 독립 stream epoch와 runtime epoch의 혼동, 가격 episode와 native/fold 혼합, 개별 불량의 전역 차단, Widget limit보다 좋은 가격을 가정할 위험을 보완했다. 원native/guard/label/cost와 canonical source를 직접 비교하도록 수정했다. 검열 뒤 재진입과 scope 밖의 후보 성과 이식도 회귀로 검증했다.

- 관련6개 suite284 tests PASS. 최종 resting-limit 보완 후 가격·scope·cost·custody·fold·대기 경로44 tests PASS; 새 회귀1개를 포함해 **285개 서로 다른 tests** 검증. compile/diff PASS.
- 실제3일 ×2prefix의 고정 후보 mask6개 비교 동일.
- 이후 날짜용 생성→intake→재생 전체 경로를 보관10/2 원천으로 별도 실행해160 native 행/160 canonical capture 및 선정 mask·metric 일치를 확인했다(38.87초). 원runtime frozen은 과거 cutoff override를 거부함을 별도로 확인했다. 이 실행은 과거 자료를 이용한 adapter 검증이며 새 날짜 성능 증거가 아니다.
- cold/warm `result.json`, `episodes.json`, `frozen-candidates.json`3파일 byte 동일.
- 원천/kernel/계획176 source seals, 기존 정책/인계98 및 선행source hash 보존.
- 문서 link·current owner·print-only parser 검증. 기존10/6 checklist와10/3 사용자 작업본 hash를 보존한다.
- 최종 reviewed scope의 미해결 코드 finding0. 원천 부재, formal publisher 미등록, 실제 Main closed episode0, 이후 날짜 성능 미검증은 코드 PASS와 별도다.

증거 root는 `tmp/samsung-fixed-watch-evaluation-20261004/`: `accepted-cold/`, `accepted-warm/`, `next-date-readiness/`, `validation/closure.json`이다. 정책 발행·실주문·전략 변경·배포/재기동 검증은 이번 범위에서 실행하지 않았다.

## 8. 다음 검증

고정 후보의 다음 자동 원천을 [오늘 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `SamsungFrozenCandidateValidation1006`에서 이어간다. 원source가 없으면 대기, 식별 가능한 개별 불량은 제외 ledger, parent/전역 계약 불일치면 재계획이다.10/6 기존 Main/Episode/Widget/PREOPEN owner는 그대로 유지한다.
