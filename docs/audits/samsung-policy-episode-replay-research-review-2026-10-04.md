# 삼성전자 정책 직접 비교·연속 기회 재생 연구 리뷰

Owner: `SamsungPolicyEpisodeReplay1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
계획: [실행계획](../proposals/samsung-policy-episode-replay-research-plan-2026-10-04.md).

## 1. 종료 판정

계획 R1~R3, 8종 종료, 관측 간격·비용·진입 지연 민감도와 새로 소비한9/28 원천 검증을 실행했다. 현재 Main보다 나은 **운영 유효 정책은 미확보**다. 이번 봉인 자료와 비교 계약에서 구별되는 가설의 검증을 완료해 조건 탐색을 종료한다. 삼성전자 상승 패턴이 없거나 모든 연구 방법이 소진됐다는 판단은 아니다.

저점 회복·흡수 전환은 가격 연구 후보로 남았다. 그러나 후단 비교 가능한 기존 Main 결과가 없고, 같은 고정 감시의 반복 판정이 하루1 native 기회로 묶인다. 현재 승률 개선 publisher 계약으로 이 삼성전자 자료만 사용하면 학습 기회 상한16·후단1로 학습30·후단10 요건을 충족할 수 없다. 신호 조건의 숫자를 더 바꾸어도 이 상한은 늘어나지 않는다. 결손을 실패0 또는 손익0으로 대체하거나 사후 가격 episode를 native 지원으로 승격하지 않았다.

연구 producer/CLI·회귀·계획/리뷰 및 당일 owner를 작성했다. 실제 policy publisher·주문·원천 수집·API/provider·배포·재기동 호출은0이다. 기존98개 정책/인계 파일의 hash를 보존했다. 현재 정책 파일의 동일성 확인과 PID 소비·다음 영업일 기동 보장은 별개의 검증이며 이번 연구에서 후자를 주장하지 않는다.

## 2. 재현 원천과 정책

최종 자료는 `tmp/samsung-policy-episode-research-20261004/`의 `frozen-strict`, `frozen-gap3`, `frozen-gap10`, `frozen-prior-day`, `validation`이다. `run-01/run-02`, `strict-final/gap3-final/gap10-final`은 구현 중간 계산이며 최종 판정에 사용하지 않는다.

| 항목 | 실제 소비 / 대사 |
|---|---|
|9/29·9/30·10/2 retained 자료|5개 exact scope, 체결718,558·호가637,611·과거 frame100,603|
|추가9/28 자료|SOR_REGULAR 체결278,975·호가111,625·frame14,542. 새 수집 없음|
|합계|체결997,533·호가749,236·frame115,145. AL/NX의 같은 사건을 독립 지원으로 합산하지 않음|
|상태 조건|6가설 × 과거 창300/900초 × 확인5/15초 =24조건|
|가격 재생|24조건 × 8종 종료 × 비용2종 × cooldown2종 =768조건/scope/day. 15개 분할 × 관측 간격3모델 =34,560계산 조합, 추가9/28은768조합|
|captured 정책 adapter|24조건 × veto/soft_add/replace_soft =72조건. native와 trace를 별도로 평가|
|과거/후단 순서|9/29→9/30,9/29~30→10/2. 이미 반복 연구한 자료로 pristine holdout 아님|
|출력 권한|offline/report-only, native_promotion_support=false, official_policy_candidate=null|

현재 selector는 날짜 파일을 추정해 읽지 않고 `current.json → generations/<bundle hash>.json`으로 대사했다. 실제 adopted bundle은 `6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87`,10/6 staged bundle은 `3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99`다. 둘의 KRX_REGULAR machine parent는 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`로 동일하다. captured519개 setup을 이 parent로 재판정해 판정·guard가 기존 projection과 모두 일치했다.

비용은 날짜별 원래 economic reference와 KRX/NXT fee profile을 대사한 fee/tax/buffer0.23%다. ask 진입/bid 종료로 spread를 반영하고 추가 impact0인 관측 가격 CF로 표시한다. 비용0.33%는 같은 조건의 stress이며 최적화할 정책 knob가 아니다. actual fill/완료 손익으로 표시하지 않는다. trailing은 기존 pure formula의 bid peak·고정 width 민감도이며 실제 Main의 trade peak/strength/hard stop/order 전체 재현은 아니다.

## 3. 가격 왕복이 실제로 있었는가

유효 prefix에서 비용+순0.1%를 회복한 가격 움직임은 있었다. 다음 frame은 서로 겹치는1초 관측이므로 거래/독립 기회 수가 아니다. 사후 저점 ask→후속 bid 회복 사건도 미리 저점을 선택할 수 있었다는 의미가 아니며 학습 feature나 native 지원에 넣지 않았다.

|SOR_REGULAR 날짜|frame|20분 안에 비용+순0.1% 관측 frame|20분 종료창 확보 / 검열|순0.1% 회복 사후 비중첩 사건|최대 관측 net MFE|
|---|---:|---:|---:|---:|---:|
|9/28|14,542|444|36 /14,506|1|0.4986%|
|9/29|15,063|1,976|2,358 /12,705|8|1.2598%|
|9/30|18,097|2,586|8,574 /9,523|6|0.7011%|
|10/2|18,444|1,551|7,988 /10,456|4|1.4244%|

20分창을 확보하지 못해도 결손 **이전** 목표/stop이 관측됐다면 그 terminal은 인정했다. 반대로 목표 뒤까지 연결된 것처럼 invalid/epoch/sequence/gap을 뛰어넘지 않았다. 2/10/20/60분 census와 순0/0.1/0.4% 사건을 모두 출력했다. 사후 사건에는20분 제한이 없으므로20분 frame 수와 같은 분모가 아니다.

기타 scope도 별도로 검증했다. SOR_PREMARKET의 학습 선정 조건은 후단 비용 후 양수0건, SOR_AFTERMARKET은 엄격한 prefix에서 비용+순0.1% 관측 frame0이었다. NXT 두 scope는 학습 terminal 지원 부족으로 미선정이며9/29 파티션 부재는 source missing이다. 이것을 해당 시장 전체의 edge 부재로 확대하지 않는다. Widget10/2의08:19→09:24 실제 거래는 약65분의 세션 간 포지션이며 이 Main 정규장20분 연구와 동일 entry/exit 실험으로 취급하지 않았다.

## 4. 기존 Main 직접 대조

원래 full-cost target-first binary label을 그대로 사용했다. 아래 값은 실제 체결 승률이 아니다. trace 반복과 native 첫 admission의 분모를 분리했다.

|날짜|captured|native ID 보유 판정 / native 그룹|기존 ENTER trace: 승/확정·미확정|기존 ENTER native 첫 admission: 승/확정·미확정|
|---|---:|---:|---:|---:|
|9/29|313|15 /15|8/15·19|3/5·5|
|9/30|46|46 /1|0/1·0|0/1·0|
|10/2|160|160 /1|0/0·3|0/0·1|

9/29의 나머지298개 판정에 native metadata를 합성하지 않았다. 9/30·10/2는 같은 fixed-watch admission/generation을 반복 사용한다. 많은 체결 tick이나 판정 횟수가 곧 독립 native 지원수로 이어지지 않는다.

- Native 선택:9/29만 학습할 때 개선 조건0.9/29~30 학습에서는 `base_recovery:300:5:soft_add`가 원래3/6=50%보다3/5=60%로 높아 선택됐다. **같은9/30 native 그룹의 기존 확정 stop 대신 더 이른 미도달 판정이 첫 admission이 된 변화1건**이었다. 승수는3으로 같고 미확정은5→6이었다. 변경 trace와 원래 label을 `paired_training.changes`에 공개했다. 후단10/2는 양쪽1개 모두 미확정으로 승률 개선 입증 불가다.
- Trace 선택: `absorption_release:900:5:soft_add`는9/29~30의8/16=50%→9/17=52.9412%. 추가로 양성 trace1건을 찾았다. 그러나 native 지원 증가가 없고10/2 원래 ENTER3건 모두 미확정이어서 후단 개선을 계산할 수 없다.9/29→9/30 fold도 후단 양쪽0/1이었다.
- 기존 성공100%/80% 보존 veto는 없다. 학습에서 기존 승자를 제외하더라도 승률이 높으면 선택하는 회귀를 통과했다. 미확정 판정으로 분모가 줄어 생긴 겉보기 개선을 확정 성공으로 표시하지 않았다.

`native_first` 직접 대조는 연구 진단이다. 실제 `_winrate_opportunity_metrics`는 native 그룹 내부 확정 attempt의 평균을 다시 그룹 평균한다. 이 연구의 첫 admission 숫자를 정식 generator 출력으로 제시하지 않는다.

## 5. 진입·종료·재진입 연구 결과

6가설 모두 과거 상태의 순서와 첫 신호만 사용했다.8종 종료는 barrier,10/20분 time, trailing3종, 회복 상태 실패 soft exit, 과거 저항 도달이다. 기본 barrier는 순목표+0.1%·gross stop−0.7%·20분이다. time/soft exit에서 유효한 손실 종료를 승률 분모에 포함했다. 단순 목표/stop binary 승률은 별도 열에 보존했다.

### 5.1 학습에서 선택한 고정 조건

|학습→후단|가설·선택 종료|학습 비용 후 양수/확정|후단 비용 후 양수/확정·검열|후단 평균 net CF|
|---|---|---:|---:|---:|
|9/29→9/30|base_recovery300:15·state_failure|2/4|2/11·1|−0.4622%|
|9/29→9/30|absorption_release300:15·state_failure|2/3|1/3·1|−0.3505%|
|9/29~30→10/2|base_recovery300:5·barrier|3/4|2/2·1|+0.1353%|
|9/29~30→10/2|absorption_release300:5·barrier|2/3|2/2·1|+0.1356%|
|9/29~30→10/2|failed_breakdown300:5·state_failure|1/3|0/3·1|−0.5923%|
|9/29~30→10/2|range_return900:15·barrier|2/3|0/1·0|−0.9560%|

학습 base/absorption barrier 평균CF는 각각−0.1356%/−0.2271%였지만 평균CF 양수를 새로운 승률 선택 veto로 넣지 않았다. 연구의 기존Main 가격 재생에 대해 학습 양수 비율은 각각75%/66.7% 대33.3%였다. 후단10/2의 같은Main 가격 재생은 첫 포지션의 결과가 검열돼 후속admission을 차단하므로 baseline 비교 가능 수0이다. 두2/2는 같은 두 상승 구간을 겹쳐 관측했으므로 독립 성공4건으로 합산하지 않는다.2/2의Wilson 하한은42.50%, 미확정1건을 포함한 양수 비율 범위는66.7~100%다.

10/2 base는09:07:14.187→09:13:43.350,09:17:15.273→09:23:53.330에 종료하고 각net CF+0.1363%/+0.1343%. 세 번째09:28:48.124는 미해결이다. absorption은09:10:12.191→09:13:43.350,09:19:28.085→09:23:19.229에 종료하고 세 번째09:28:24.029는 미해결이다. 실제account/capacity/custody 및 주문 가능성은 재구성하지 않았다.

### 5.2 재진입·민감도·추가9/28

- 관측 종료+60초 후 재진입에서10/2 base/absorption은 각각 양수2건+검열1건. 기존20분 전체 예약은 양수1건+검열1건이었다. 종료 후 두 번째 회복을 연구상 회수할 가능성이 확인됐다. 종료를 모르면 보유 상태를 유지하며 후속 진입을 차단한다.
- 3초 관측 모델에서도 고정base/absorption의10/2는2/2·검열1.10초 모델에서는base에stop이 추가돼2/3·검열1, 평균−0.2280%. absorption은2/2·검열1을 유지했다. 과거 입력/신호와 원native label·mask는3모델 모두 완전히 일치하고 미래 경로의 관측 모델만 달라진다. gap 사이 미관측 가격을 보간하지 않았다.
- 비용0.33%에서는 양쪽10/2 양수1/확정1·검열1. target 필요 상승폭이 달라져 종료·재진입 구성도 바뀐다.+0.2195%는 더 긴 별도 관측terminal이며0.23% 결과에서 단순히0.10%를 차감한 비교가 아니다. stress에서 조건을 재선정하지 않았다.
- 고정regular fold6개 조건을 대상으로 후단일과9/28에서 지연0/250/1000ms·비용0.23/0.33을 계산했다.72평가 중 지연48개의metric은 대응 지연0과 일치했다. 원래source 문제·지원 부족을 해소하지 않았다.
- 새로 소비한9/28에서frozen base/absorption barrier는 각 첫1건이 검열돼 알려진terminal0. state_failure는 각각0/1·검열1, failed_breakdown은0/2·검열1, range_return은 신호0. 추가 안정성을 입증하지 못했다. 학습보다 앞선 날짜이므로chronological holdout으로 추가하거나 조건을 재선정하지 않았다.

### 5.3 전체6가설의 처분

|가설|9/29~30학습의 알려진terminal≥3조건 / Main비교지원≥3조건 / 승률개선조건|처분|
|---|---:|---|
|base_recovery|22 /11 /11|가격 후보 유지. 후단Main비교0, 확정2건,9/28검열,10초민감도에서loss 추가|
|absorption_release|20 /12 /12|가격 후보 유지. 후단Main비교0, 확정2건,9/28검열, native지원 부족|
|failed_breakdown|12 /4 /4|선택 후단0/3. 회복 실패soft exit가 손실화|
|higher_low_sequence|2 /2 /0|확정 지원을 확보한 조건도 기존Main 양수 비율을 상회하지 않아 미선정|
|pullback_resume|10 /8 /0|확정 지원을 확보한 조건도 기존Main 양수 비율을 상회하지 않아 미선정|
|range_return|12 /7 /7|선택 후단0/1, 추가 날짜 신호0|

가설별64조건의 학습 비교는baseline 비용에서 고정하고stress는 선정 대상에서 제외했다. 시간 종료·trailing·상태 실패·과거 저항의 추가 정보도 같은 모집단에서 평가했다. time/soft exit는 목표/stop 미도달 일부를 관측 종료로 만들지만 실제prefix 결손을 복구하지 못한다. soft exit의 음수 종료를binary에서 제외하면 조건부 목표 선도달율100%가 되는 조건도 있어 시간 종료 포함 양수 비율을 함께 공개했다.

## 6. 결손의 실측과 승격 상한

|SOR_REGULAR|invalid trade|invalid depth|유효하지만bid==ask인depth|trade gap>1.5초|depth gap>1.5초|
|---|---:|---:|---:|---:|---:|
|9/28|4,822|1,839|7,737|138|146|
|9/29|1,695|1,056|8,253|217|118|
|9/30|190|74|20,509|66|13|
|10/2|12|4|17,348|102|18|

이는prefix 중단/비실행가격 진단이며 원인이 중복될 수 있다. 각 검열 건수를 위 합계로 대체하지 않는다. invalid는 기존domain의clock/eligibility/accept/price 검증 결과이고 본 연구에서HTTP 장애 원인까지 특정한 수가 아니다. locked quote는domain 관측으로 보존하며 실행 가격으로 사용하지 않는다. 적은 결손도20분 경로를 여러 차례 분단하고 첫 미해결 보유 후 후속admission을 차단하므로 tick 총수와 평가 가능한 경로 수가 달라진다.

현재 `mechanistic_entry_runtime_policy._winrate_successor_hurdles_valid`는 `winrate_native_improvement_without_winner_retention_v3`, `native_scanner_or_fixed_watch_v2`, 학습30/후단10 selected opportunity, 기존보다 높은 승률·지원조정승률+5%p·coverage50% 등을 검증한다. 기존 성공100%/80% 보존 요건은 없다.30/10은 이번 연구의 진단상 최소3/3과 다른 기존publisher 요건이며 연구 결과에 맞춰 낮추지 않았다.

이 **봉인된Samsung captured자료만**의native 그룹은15/1/1, 가장 넓은 후보의 상한은 학습16·후단1이다. 실제source-valid/label-valid/guard 적격군은 더 작아진다. 결손identity를 신조하지 않는 한 이 특정 승격 경로에서 신호 탐색만으로 후보를 적격화할 수 없다. 전체 종목shared 생성기의 상한을 주장하지 않으며 별도generic strategy generator에도30/10이 적용된다고 추정하지 않는다. 새state adapter는runtime selector에 미등록이고 이번에 공식 생성기를 실행했다고 표시하지 않는다.

## 7. 코드리뷰·수정·검증

새producer는 기존 `src/engine/scalping`의offline 소유 범위에 두고live caller/engine root module을 추가하지 않았다. 기존domain을 읽으며Kiwoom request/parser/FID/recovery를 변경하지 않았다.

리뷰 후 다음을 보완하고 재계산했다.

1. current generation을dated file에서 추정하지 않고immutable bundle로 해석해selector receipt/activation/parent를 검증했다. dated staging 차이를PID 불일치로 오인하지 않는다.
2. time/trailing에서 먼저 끝난barrier 결과를 재사용하지 않고 필요한 유효 경로를 독립 검증했다. invalid/epoch/sequence/continuous loss 이후 미래 성공을 연결하지 않는다.
3. higher-low가 원래 저점과 같은 가격까지 돌아오면 상태를 초기화했다. 별도의 같은 저점은 새excursion을 관측한 뒤에만rearm한다.
4. past_ceiling의 과거 저항 결손은barrier fallback으로 대체하지 않고null로 표시했다. 새 비용이나 미래 최대값으로 학습 조건을 재선정하지 않는다.
5. native의 확정loss→미확정first-admission 변경을paired 상세에 추가해 분모 감소를 성공 증가와 구분했다.
6. prior-day용offline route 설정을finally에서 복원해 실패 시에도 원래 설정을 유지했다. oracle은locked/invalid를 뛰어넘어 연결하지 않고 새로운 유효segment로 나눈다.

표적 회귀158 PASS, compile·diff/문서validation은validation 기록에 저장한다. 원source/새kernel/test/계획131hash, prior-day 추가 포함142hash, 정책/인계98hash를 검증했다. strict 전체17JSON을 재실행해result의elapsed/hash만 제외하고 완전 일치, 나머지16JSON은content hash까지 일치했다. prior-day 결과는content hash `0c327900281753f1261f1ac4a00858c6b73dd1ca07bc35ee61388e7a9e02d005`까지 완전 일치했다. 실제source의prefix 재구성144비교, gap모델 간native/신호 불변성, 지연metric48비교를 검증했다.

최종 검증 정본은 `validation/closure.json`, 회귀 로그는 `validation/pytest.log`, 문서print-only 출력은 `validation/docs-parser.log`다. 거래suite 전체·provider·장후 전체 재생성·외부Project/Calendar sync는 이 변경에 필요하지 않아 실행하지 않았다. 검열·native지원·반복 이용한 검증일·관측 가격과 실제 체결 차이가 남으며 코드PASS로 이 제약의 해소를 주장하지 않는다.

## 8. 종료 이유와 후속 계약 보완

종료 이유는 `bounded_distinct_hypotheses_exhausted_under_sealed_source_and_native_contract`. R1가격 존재, R2현재Main 직접 비교, R3의6상태/8종료/재진입, 지연/비용/관측 간격/미사용9/28을 검증했다. 남은 양성 조건의 숫자를 같은3일에 다시 최적화해도 후단Main label과native지원 상한은 달라지지 않는다. 시장에 승리 패턴이 없다는 결론은 아니다.

base/absorption 룰·signal/exit 시각을 고정해 보존했다. 다음 의미 있는 개선은 원source의 **기회 단위와 소비 계약**이다. [Samsung 고정감시 구현계획](../proposals/samsung-fixed-watch-machine-auxiliary-implementation-plan-2026-10-03.md), [scope 분리계획](../proposals/main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)에 연결해 아래 계약 보완을 기록한다. runtime 기회ID/publisher 요건 변경은 실행하지 않는다.

|순서|owner producer→consumer / 작업|closure test|
|---|---|---|
|1|`main_fixed_watch`/원판정receipt→projection:9/29 native metadata 결손298건을 원admission/route/epoch/trace로exact join할 수 있는지inventory. 원owner를 복구하고 새promotion ID를 합성하지 않는다|원receipt·projection·group 대조표와exact join/ambiguous/unrecoverable 수. 복구 불가는null|
|2|실제entry/terminal/cancel/flat/custody receipt→episode boundary→postclose:같은watch admission의 재진입을 별도 검증episode로 다룰 수 있는 조건 정의. 기존receipt에서 종료·재적격화·실행guard가 증명된 구간만 연결|watch ID 보존. actual/sim/CF·중첩 보유·Main/Widget/manual 분리. 같은 상관cluster를 학습/후단에 걸치지 않는다. 단순 시각bucket/저점 주기를 독립native로 세지 않는다|
|3|scope별policy generator/validator:Samsung child selector, parent/child hash, venue/session, cost·hard safety·holdout/cluster 지원 계약 뒤 고정base/absorption 재평가|같은scope 기존Main 비교, 알려진/미확정 결과, 지원조정승률·source/cost·rollback/activation. 기존 성공 보존veto를 복원하지 않고 미성립이면incumbent carry|

이 후속은 요건 완화나 신규 수집 확대 계획이 아니다. 기존receipt로 기회 구간을 증명할 수 없으면unrecoverable로 종료하고unknown을 성공으로 바꾸지 않는다.10/6 Main·Episode·Widget/PREOPEN 기존owner를 보존한다.
