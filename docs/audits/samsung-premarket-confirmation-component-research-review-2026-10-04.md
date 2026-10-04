# 삼성전자 장전 확인 조건 분해 연구 결과

## 1. 판단

[상세 실행계획](../proposals/samsung-premarket-confirmation-component-research-plan-2026-10-04.md)의 원천 대사·확인 원인 분석·9가설 재생·리뷰/보완/회귀를 완료했다. 연구 구현은 [전용 consumer](../../src/engine/scalping/samsung_premarket_confirmation_research.py), [회귀](../../src/tests/test_samsung_premarket_confirmation_research.py)다.

**기존 데이터에 상승 기회가 없었던 것이 아니다.** 10/2 08:13에는 가격 변화0%의 매수 우세 입력이 있었고, 동일 원ask274,500원·비용0.23%·고정20분 barrier에서08:19:37.593 bid275,500원에 net+0.134299% 목표를 확인했다. 그러나 그 조건을 다른 날짜에 적용한 원Main 관측은 손실이었다. 이번 가설군에서 운영 적용을 뒷받침하는 반복 성과는 확보하지 못했다. 공식 policy candidate와 학습 선정 후보는 null이며 정책/수집/매매/배포/기동 변경은0이다.

이 결과는 기존 Widget 체결·65분 보유의 성과와 별도 가격 경로 진단이다. Main 실제 주문/실현PnL이나 기존 정책 대비 운영 승률 개선을 증명하지 않는다. 전체 가능한 연구 가설이 소진됐다는 주장은 하지 않는다.

## 2. 실제 소비 원천과 제외

| 날짜 | canonical 장전 capture | 유효 원projection | 원watch cluster | NXT 체결 | NXT 호가 | grid / 유효 feature |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9/29 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| 9/30 | 3 | 3 | 1 | 18,794 | 17,840 | 2,725 / 2,692 |
| 10/2 | 3 | 2 | 1 | 22,449 | 18,552 | 2,850 / 2,835 |
| 합계 | 6 | 5 | 2 | 41,243 | 36,392 | 5,575 / 5,527 |

- `_NX/NXT_PREMARKET`만 가격 소비했다. 9/29 다른 route의 원천을 이 route의 관측으로 채우지 않았다. 그날 archive·projection의 해당 Main capture0건과 가격 partition의0건을 대사했다. 이것은 삼성전자 전체 하루 데이터 부재라는 뜻이 아니다.
- 원projection5건은 canonical hash·quote/current/features·원watch identity를 검증하고, 장전 scope parent `656cfd8e824f3135c8a5c7f47ece789a9c1837f53e72355d298fa2602f05b011`로 원action/reason을 모두 재현했다. 정규장 parent를 사용하지 않았다. 최종 연구 consumer의 유효 projection 제외0건이다.
- 기존 normalized frame5575개를 모두 읽었고, decision 이전10체결/quote join이 부족한48개는 feature 결손으로 분리했다. 유효0값을 결손으로 대체하지 않았다. 시세 grid5527개를 native 기회5527개로 세지 않았다.
- Main 원native는 날짜별 watch1개씩 총2개다. 원parent ENTER는0이며 기존 Main 승률은 null이다. 연속 가격 실험의 soft-only 기준을 기존 Main 정책으로 표시하지 않았다.

### 2.1 새로 확인한 producer 결함

10/2 **08:33:18.566416** canonical capture는 원archive에 있지만 projection에는 없다. source assessment는 `RECHECK / local_breakout_confirmation_required`였다. 원setup은 `NO_VALID_SETUP / WAIT_CONFIRMATION`; validator가 `entry_setup_family_state_inconsistent`를 반환했다. canonical hash는 유효하며 원source quality는 `fresh_consistent`, 완성봉33개였다. 원천 미수집 때문에 사라진 행이 아니다.

소유 경로는 `entry_setup_evidence.build_entry_setup_evidence`의 local-breakout state 변경과 `validate_entry_setup_evidence` family/state 검사, 이어 `ai_action_outcome_calibration._load_machine_observation_rows_uncached`의 invalid capture 제외다. 후단은 해당 source 오류를 제외한 것으로 확인했다. 원live producer의 결함은 이번 오프라인 module 수정과 구분한다.

다음 코드 보완은 **유효한 family/state 조합을 유지하면서 local-breakout recheck를 보존**해야 한다. 미지원 setup에 새 family/확인 fact를 만들어 ENTER를 허용하는 수리는 금지한다. closure는 이 exact capture 재생→validator 오류0→local-breakout guard 유지→projection에 합당한 RECHECK 포함, 그리고 기존 BLOCK/ENTER/UNCONFIRMED 분기의 회귀다. 이번 연구에서 live producer와 원projection을 수정하지 않았다. 이1건을 복구해도 동일10/2 watch이므로 독립 cluster는 늘지 않는다.

봉인된 원capture의 잘못된 state를 덮어쓰지 않는다. 과거 행의 수용에는 원payload/parent에서 재구성한 **별도 repair receipt**와 원validation 오류를 함께 보존하는 소비 계약이 필요하다. 현재 producer의 prospective 보완만으로 원archive가 정상화됐다고 주장하거나, malformed source 전부를 허용하는 예외를 두지 않는다.

## 3. 확인 조건의 상세 원인

원parent 재생 중 exact-analysis 입력을 관측한 [확인 chain receipt](../../tmp/samsung-premarket-confirmation-20261004/validation/confirmation-chain-inputs.json)로 아래 값들을 확인했다. 관측 hook은 별도 연구 interpreter에서만 사용했고 원source/kernel 파일 hash를 보존했다.

| 판정 시각 | 실제 확인 원인 | delta /10틱 가격 변화 | 완성봉·liquidity | 동일 가격20분 CF |
| --- | --- | --- | --- | --- |
| 9/30 08:04 | adverse tape와 large-sell hard blocker | −28 / +0.181% | 4 / supportive | −0.411159%; guard 유지·전가설 진입0 |
| 9/30 08:08 | early continuation의 trigger 미확인 | +35 / 0% | 8 / supportive | −0.591664%; neither |
| 9/30 08:13 | range에서 liquidity가 mixed여서 micro setup 미성립 | +41 / +0.181% | 13 / mixed, fillability49 | −0.591011%; neither |
| 10/2 08:13 | distribution에서 지원 setup 없음, 가격 변화0 | +30 / 0% | 13 / supportive | +0.134299%; target-first |
| 10/2 08:36 | range의 micro flow/price는 양수이나 확인 grammar가 WAIT 유지 | +62 / +0.182% | 36 / supportive | 주모델 검열;10초 gap 민감도에서 stop-first −0.955953% |

핵심 구분:

1. **10/2 08:13:** fresh 입력은 충분히 존재했다. `distribution`에는 일반 continuation/recovery family가 없고, `MICRO_RECOVERY`는 `range_or_no_setup + 신뢰 flow/양수 가격 + supportive liquidity`에서만 만들어진다. 따라서 가격 부호만 완화하면 현live policy가 자동 ENTER로 바뀐다는 결론은 아니다. 연구 가설은 soft confirmation grammar 자체를 대체하는 미등록 mask다.
2. **10/2 08:36:** 매수 우세·가격 상승은 이미 소비했으며 `MICRO_RECOVERY / WAIT_CONFIRMATION`을 만든다. `micro_continuation_unconfirmed`는 별도 원source가 없다는 메시지가 아니다. 해당 parent grammar가 추가 확인 상태를 유지한 것이다. 원cost-bound path의 stop-first 값은−1.02075%였다. 주quote gap1.5초 모델에서는 terminal 이전 연속성 결손으로 net=null이며, gap10초 민감도만08:45:44.694의 bid273,500원 stop를 관측했다. 두 값을 혼합하지 않았다.
3. **9/30 08:13:** 10틱 가격 변화가 양수라도 setup이 없을 수 있다. 원liquidity `mixed / would_fill_now=false`가 family 조건을 충족하지 않았다. 현재 hard liquidity 최솟값15 통과와 setup의 supportive 상태는 서로 다른 조건이다.
4. 원scope 비용은 각행0.32025~0.32105%로 보존했다. 위CF0.23%는 보관호가 ask/bid로 직접 계산하는 별도 고정 연구 비용이다. 이 수익률을 broker 정산 손익이나 원native outcome으로 치환하지 않았다.

## 4. 9가설의 Main 대조

원guard가 soft confirmation만인 행에서 공통 envelope를 유지했다. same-stamp 가격/비용/exit 결과는 모든 mask가 공유한다. raw risk·source·liquidity·local-breakout·원parent situation veto는 해제하지 않았다.

| 가설 | 9/30 선택관측 / 첫 원watch binary | 10/2 첫 원watch 선택 | 10/2 원binary 결과 |
| --- | --- | --- | --- |
| soft_only_bound | 2 / 미확정 | 08:13 | target-first; 선정 제외 상한 |
| positive_micro | 1 / 미확정 | 08:36 | stop-first |
| nonnegative_price | 2 / 미확정 | 08:13 | target-first |
| bid_rise_5 | 0 / 없음 | 없음 | 미선택 |
| bid_hold_5 | 1 / 미확정 | 08:36 | stop-first |
| bid_hold_15 | 1 / 미확정 | 08:36 | stop-first |
| nonnegative_bid_hold_5 | 2 / 미확정 | 08:13 | target-first |
| trade_backed_1 | 0 / 없음 | 08:13 | target-first |
| trade_backed_refill_half | 0 / 없음 | 08:36 | stop-first |

10/2 한watch의 먼저 선택된 판정만 cluster 성과로 계산했다. 같은watch 두관측을 성공/실패 각각 독립 표본으로 더하지 않았다. 9/30 미도달은 binary 실패0으로 만들지 않았으나, 가격CF의 실제20분 bid 종료는 별도로 손실을 계산했다.

**기존 입력에서 추가로 소비할 근거는 존재한다.** 08:13 ask 소진 체결근거100%·refill100%, 08:36은96.77%·refill0%였다. 단순 체결근거 조건은 둘 다 허용하지만 refill≤50%를 추가하면 앞선 성공을 버리고 뒤 손실을 먼저 선택한다. 낮은 refill을 무조건 좋은 확인으로 취급할 근거를 얻지 못했다. 과거5/15초 bid 변화도 해당 판정에서0이었고, bid 상승을 요구하면 둘 다 제외한다.

이 한 날짜의 첫 판정 교체는 **연구 단서**다. 기존 성공100%/80% 보존 veto 때문이 아니라, 학습 원watch의 확정 binary가0이고 새날짜 독립 검증이 없어서 운영 정책으로 선정하지 않았다. 정식 Main 비교 승률은 parent ENTER0 때문에 식별되지 않는다.

## 5. 연속 가격 실험과 선정 처분

3일의9가설×기본/10초 gap 모델을 재생했다. 실제 원Main setup을 만들지 않은 market-only proxy 실험이다. 캡처1초 feature와 보관시세에서 재구성한 fixed-ask depletion proxy는 별도 의미로 표시했다. 모든 후보는 같은 signal의 같은 label을 공유하고, 최초 검열 모델 보유는 뒤 신호를 보류한다. 하루 재설정은 연구 가정이며 실제 계좌 flat 증거가 아니다.

| 주모델 학습군 | 모델진입 / 확정 / 검열 | 양수 CF 비율 | target/stop binary | 평균 확정CF |
| --- | --- | --- | --- | --- |
| soft-only 기준, 비음수 가격, 비음수+bid 유지, 체결근거2가설 | 3 / 2 / 1 | 1/2=50% | target1 / stop0 | −0.229017% |
| 양수 가격, bid 상승/5초·15초 유지 | 2 / 1 / 1 | 0/1=0% | 0 | −0.048841% |

9/29 해당route0건을 손익0으로 더하지 않았다. 학습 binary의 최대는1이며 계획의 연구 선정 최소3을 충족하지 못했다. 알려진 평균 CF도 개선 정책을 지지하지 않는다. **9가설 모두 학습 미선정**, 고정 registry의10/2 진단만 실행했다. 후단 결과로 후보를 재선정하지 않았다.

10/2 주모델의 bid-rise만1진입/1확정·CF−0.23%; 나머지8가설은4진입/3확정/1검열, 확정양수1/3=33.33%, target1/stop1의 조건부binary 승률50%, 평균CF−0.470886%였다.10초 gap 민감도는 대부분5진입/4확정/1검열·양수1/4=25%, target1/stop2·조건부33.33%, 평균CF−0.592153%로 개선되지 않았다. 민감도는 선정에 사용하지 않았다.

여기서 조건부 target/stop 승률과 알려진 시간종료까지 포함한 양수CF 비율은 별개다. 시간종료 손실을 target/stop 실패로 재표시하지 않았다. overlapping signal5527개를 독립 거래5527개로 보고하지 않았다.

## 6. 리뷰·수정보완·검증

보완 사항:

- 원parent situation veto를 legacy projection에서 누락하지 않고 원policy로 재검사했다.
- soft-only 상한조차 stale quote·신뢰 micro source 결손을 해제하지 않도록 했다.
- 날짜별 첫watch 선택을 고정해 뒤쪽 성공 관측으로 바꾸는 편향을 차단했다.
- 학습 선정 receipt를10/2 가격 label 평가 전에 저장했다. 연구 threshold/exit/gap registry를 후단에 맞춰 조정하지 않았다.
- 별도stream의 같은 수신clock에는 순서 증명이 없으므로 anchor 호가와 같은clock의 체결을 이후 ask 소진의 BUY 근거로 세지 않았다. 해당회귀를 추가하고 최종두실행에서 지표 불변을 확인했다.
- 전수 원archive census로 projection 밖08:33 source 오류를 확인했다.
- 초기연구 consumer가 fixed-watch의 사용하지 않는 scanner null string을 native 충돌로 해석하던 결함을 고쳤다. 최초 `accepted-cold` 출력은 잘못2건을 제외한 **폐기된 연구 generation**이며, `reviewed-cold/warm`은 추가clock 보완 이전 기록이다. 최종 근거는 `final-cold/warm`만 사용한다. 원capture/원projection은 변경하지 않았다.

최종 표적 회귀51개 PASS, compile·diff PASS. 앞선 관련2suite87개 PASS는 초기 구현 검증이고 최종51개에는 위수정을 포함한다. 두최종 재생의4파일 `frozen-experiment/frozen-selection/episodes/result` bytes 일치. 실제2유효일×2prefix 미래 mask 비교4개 일치. 9/29 빈원천에는 형식적인 미래 mask PASS를 만들지 않았다.

선행176source/kernel hash 및98policy/handoff hash를 시작/끝 보존했고, 신규 코드/test/plan·선행closure를 더한180seal을 검증했다.10/3dirty checklist·10/6checklist의 원hash를 보존했다. 최종 closure는 [검증 receipt](../../tmp/samsung-premarket-confirmation-20261004/validation/closure.json), 결과는 [result](../../tmp/samsung-premarket-confirmation-20261004/final-cold/result.json), [episode](../../tmp/samsung-premarket-confirmation-20261004/final-cold/episodes.json), [가격 gap 민감도](../../tmp/samsung-premarket-confirmation-20261004/validation/captured-gap-sensitivity.json)다.

이번 module/테스트/문서의 리뷰 후 미해결 결함은0이다. §2.1의 기존 live producer 결함은 발견된 별도 잔여로 보고하며 전체코드 무결함을 주장하지 않는다. 전체매매suite·API/provider·장후 자동화·정책 발행·PREOPEN/PID·실현 경제성 검증은 이번 오프라인 범위에서 실행하지 않았다. Kiwoom protocol 요청/응답 parser/FID/continuation 변경0이다.

## 7. 다음 행동과 연구 경계

1. 우선 producer의 family/state 정합성 결함을 해당 owner의 변경 범위로 보완하고, 위exact source 재생·guard 보존 검증을 닫는다. 새 API 원천이 필요한 수리가 아니다. 복구 관측1개를 독립 기회 증가로 주장하지 않는다.
2. 장전 연구 단서는 **completed-bar distribution과 intrabar 매수 흡수의 불일치**, **가격 상승 없이 체결이 ask 소진을 뒷받침하는 상태**다. 현3일의 학습 원watch binary0 때문에 그 단서를 새 정책으로 만드는 검증은 이번 자료만으로 끝낼 수 없다. 같은2watch에 조건을 더 붙여 단일 성공만 고르는 정책을 발표하지 않는다.
3. 자동생성될 이후 날짜의 기존 고정2후보 검증은 기존 `SamsungFrozenCandidateValidation1006` owner에 남긴다. 그owner가 새 장전 확인 후보까지 검증한다고 확대해 표시하지 않는다. 새 장전 후보의 독립 검증은 조건·원scope·first-watch 분모·cost·등록 consumer를 별도로 고정하는 후속 계약이 필요하다.

이번 유한9확인 가설군은 결과와 처분을 기록하고 종료했다. 결론은 추가 외부 원천을 요구하는 것이 아니라, 이미 존재하는 producer 정합성·확인 grammar의 소비 방식과 독립 검증을 우선하자는 것이다.
