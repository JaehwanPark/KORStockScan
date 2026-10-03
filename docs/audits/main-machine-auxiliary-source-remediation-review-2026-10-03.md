# Main 기계·보조 정책 원천 보완 및 격리 계산 리뷰 (2026-10-03)

## 판정

기존 변경은 `24a4658d`로 통합 배포하고 `6d72c44d` clean 기준선에서 보완을 시작했다. 신규 보완은 코드 결함 수리·계산 설명·lossless metadata 복구를 마쳤으며 **배포하지 않았다**. 재계산에서 새 기계·보조 정책은 선정되지 않았다. 전 비용/운영 모델 결손은 유지되며 자연 원천 없이 실매매 성능 개선을 주장하지 않는다.

소유 계획: [상세 계획](../proposals/main-machine-auxiliary-source-remediation-plan-2026-10-03.md). 격리 증거: `/home/ubuntu/KORStockScan/tmp/main-machine-auxiliary-source-remediation-20261003/`.

## 구현·리뷰·보완

1. `None/null/NaN/공백/비문자` promotion ID를 producer correlation과 calibration loader에서 제거한다. null placeholder만으로 exact join할 수 없다. 고정 관측은 native `watch_origin + watch_admission_id + watch_generation_id`를 사용하고 같은 admission의 재평가를 별도 기회로 늘리지 않는다.
2. 완료·후보 없음 checkpoint의 progress를 보존한다. input/선정 version/scope/domain·cursor/type/hash metadata가 맞아야 재개한다. identity contract version과 scope, validation kernel hash도 generation에 결속한다. 변경/결손은 새 검색이며 선정 전 holdout을 사용하지 않는다.
3. Winrate 정책은 동일 hurdle를 한 checks 객체로 계산하고 후보별 metrics·기존승자 보존·실패 이유를 발행한다. 기준값/선정 순서/학습·holdout 날짜는 변경하지 않았다.
4. 관측 probe는 예약 없이 conditional continuation·수량·기준 ask·시간·operating hash를 source-only 계약으로 기록한다. trace→aux projection까지 보존한다. 실행 orders는 계속 빈 목록이며 bundle reservation/stock/registry/실제 제출을 수행하지 않는다. 미래 fill-anchored residual 가격의 owner replay는 **unsupported**로 유지한다.
5. 리뷰 중 compact projection의 native watch metadata 유실을 추가 발견해 세 필드를 보존했다. 해당 원본 trace의 요청 ID, payload, stock, decision time, bundle, venue/session이 모두 일치하는 경우에만 격리 과거 metadata를 복구했다. stop·비용·계획을 현재 값으로 backfill하지 않았다.
6. warm cache가 새 watch 필드를 숨기는 결함도 보완했다. economic 계약은 유지하고 metadata version으로 현재 source cache를 점검한다. 같은 trace 파일 세대에서 exact join한 metadata만 보충하고 payload는 읽지 않는다. 충돌·세대 변경·64MiB scan budget 초과는 미복구로 남기며 stop/비용 결손을 유지한다. 보충할 행이 없는 source는 SHA를 그대로 유지해 기존 checkpoint/provider 재사용을 보존한다. 과거 cumulative projection을 자동으로 다시 봉인하는 권한은 추가하지 않았다.

첫 회귀에서 새 테스트 import 누락, checkpoint fixture의 실제 domain hash metadata 누락, lossful fixture의 label 의도를 수정했다. 조건부 계약의 deepcopy import도 보완 후 통과했다. 최종 계산 fingerprint 보완 도중 이미 실행 중인 실험과 source hash 차이를 발견해 그 결과를 `intermediate-*`로 격리하고, git archive+현재 변경을 봉인한 `reviewed-source-snapshot`에서 최종 재실행했다. mutable 중간 결과를 최종 수용에 쓰지 않았다.

Kiwoom 공식 HEAD는 재조회해 `953e5dbff123f437ab4d11a78a95191a685eb51f` 유지, specs/core/client/API spec/Postman 네 파일 SHA를 검증했다. 조회시각·경로·hash는 `official-recheck.json`에 기록했다. 새 관측 분기는 request/parser/route/continuation/실제 order call 의미를 변경하지 않는다. `kiwoom_docs` 부재와 미정 의미를 새로운 실행 권한으로 해석하지 않는다.

## 기계 결과

보존 cache는 3일 전체 3490행 중 KRX/REGULAR **2976행**이다. 이는 원 보고서의 전체 입력7069행과 다른 filtered cache 비교 실험이다. 기존 제외행은 복구한 것으로 표시하지 않는다. 압축 file SHA는 기존/수정 입력에서 모두 같고 원래 source receipt와 incumbent을 사용했다.

- v7 supported99, train59기회/71시도, holdout10기회/28시도, lineage 제외2877: 유지.
- native fixed-watch 31행은 가짜 promotion None 대신 실제 admission/generation으로 식별한다. 같은 관측의 반복 평가인 기존 분모를 바꾸지 않으므로 모수가 늘지는 않는다.
- 96개 search allocation, evaluated89, invalid6, deduplicated1, recovery-qualified candidate0: 유지. 정책 승계.
- 기존 코드 재개는 evaluated89지만 search_complete=false로 변했다. 수정 코드는 true/cursor96을 보존했다. 그 결과 다음 iterator의 재평가 할당은 **96→0**으로 검증했다. 후보를 새로 찾았거나 수익이 개선된 것은 아니다.
- Winrate accepted2975, train109선정/89승, holdout19선정/14승의 원 native baseline을 정확 재현했다. 후보8개 모두 train 적격 실패다. 후보 없음 때문에 최종 candidate holdout이 비는 것을 실제 원 holdout 표본0으로 해석하지 않는다.

### 후보별 실제 학습 계산

승률 단위는 %, EV는 CF net-path proxy %다. 실현 비용 후 EV가 아니다. 실패 항목의 수치 기준은 상세 계획과 `after-winrate.json.candidate_training_diagnostics`에 함께 있다.

| threshold bp | 선정 기회 | 승 시도 | 원시 승률 | 보정 승률 | CF net-path | 실패 hurdle |
|---|---:|---:|---:|---:|---:|---|
| 4.0 | 12 | 9 | 75.0000 | 51.2662 | -0.182742 | selected_opportunities_minimum_30, baseline_coverage_minimum_50pct, baseline_winners_retained_minimum_80pct, raw_win_rate_improves, support_adjusted_win_rate_improves_5pp |
| 11.3 | 25 | 21 | 84.0000 | 68.7521 | -0.080090 | selected_opportunities_minimum_30, baseline_coverage_minimum_50pct, baseline_winners_retained_minimum_80pct, support_adjusted_win_rate_improves_5pp |
| 15.56 | 37 | 32 | 86.4865 | 74.7364 | -0.051993 | baseline_coverage_minimum_50pct, baseline_winners_retained_minimum_80pct, support_adjusted_win_rate_improves_5pp |
| 21.8 | 50 | 45 | 90.0000 | 80.8462 | -0.012475 | baseline_coverage_minimum_50pct, baseline_winners_retained_minimum_80pct |
| 28.73 | 63 | 56 | 88.8889 | 80.7124 | -0.023930 | baseline_winners_retained_minimum_80pct |
| 33.44 | 75 | 64 | 85.3333 | 77.3882 | -0.063416 | baseline_winners_retained_minimum_80pct, support_adjusted_win_rate_improves_5pp |
| 41.69 | 88 | 75 | 85.2273 | 77.9589 | -0.064009 | support_adjusted_win_rate_improves_5pp |
| 52.76 | 100 | 82 | 82.0000 | 74.8648 | -0.098609 | support_adjusted_win_rate_improves_5pp |

## 보조판정 source 복구와 결과

원본 projection은 9/29 38행 + 9/30 6행 + 10/2 15행 =59행이다. 기존 진단 적격17/제외42를 먼저 재현했다. 정확 trace 59/59를 대조했고 conflict0, 고정 관측 metadata를 날짜별1/1/5행 복구했다. 새 독립 진단 적격은 **20행**(KRX19, 통합 AFTER1)이며 제외39는 path/cost25 + response11 + 반복기회3이다. 원본 trace·projection은 변경하지 않았다.

- KRX: train10/hold9, 성공4/3, 원시 승률36.8421%, 보정21.3729%, CF pass mean −0.172319%. 기존17행의41.1765%/−0.130053%와는 모수가 다르며 성능 하락/개선의 적용 비교로 쓰지 않는다.
- AFTER: hold1, train0, CF −0.271759%, 후보 변경0. 독립 학습 부족.
- 두 scope 모두 `incumbent_carry`, 정책/판정 changed_count0.
- **full-cost-valid0**, actual completed net-comparable0. 현재15행 writer plan0, stop11/semantic2/transport2 결손이 유지된다.
- 현재15행의 최초 producer blocker는 probe12/capacity2/guard1이다. capacity/guard를 완화하거나 이후의 계좌/호가를 과거 판정에 붙이지 않는다.
- 보조 모델 재호출0, broker 조회0. 원천 복구는 위 exact metadata뿐이며 새로운 정책 선정/실제 주문/경제적 성공이 아니다.
- warm-cache helper의 실제 retained-source 비교는 9/30 1행·10/2 5행 복구, 9/29 1행은 압축 archive의 물리 세대가 달라 미복구다. 위 격리 과거7행 대조와 구분한다. canonical 파일 SHA는 불변이며 `warm-native-metadata-comparison.json`에 남겼다.

## 성능과 검증

각 입력·코드 조합은 최종 비교에서 1회 측정했다. 원인별 계산 수치와 봉인 코드 hash가 현재 수학 kernel 파일과 일치한다. fixture의 속도 배율과 실제 계산 시간을 섞지 않는다.

| 계산 | 기존 초 | 수정 초 |
|---|---:|---:|
| Main 검색 | 135.41 | 137.58 |
| 완료 재개 | 8.83 | 8.80 |
| Winrate 계산 | 118.41 | 120.07 |
| 전체 wall | 278.72 | 283.20 |

전체 wall 약+1.6%, 최대 RSS 약1.59GiB로 유사하다. 단일 측정이며 속도 향상을 주장하지 않는다. 성능 수리 효과는 다음 동일 검색 재할당을 막는 데 있다. auxiliary native lineage streaming/재계산은4.57초다.

회귀: 영향6개 module **878 PASS**, writer/owner/atomic 관측 **256 PASS**, generation/hurdle 재리뷰 **336 PASS**, 최종 projection/identity/trace **218 PASS**, 관련 fingerprint/projection **7 PASS**. 이 숫자는 서로 중복되므로 합산하지 않는다. 마지막 입력/결과 비교 assertions PASS, AST/compile/diff 및 print-only parser를 확인한다. 불필요한 전체 trading suite·provider 호출·runtime wrapper·실제 주문은 실행하지 않았다.

추가 warm-cache 회귀 **109 PASS**는 기존 재사용·source upgrade와 exact join/충돌/세대 변경/scan budget/placeholder request ID를 함께 검증한다. 초기 import·부재 파일 경로 처리를 보완했고, metadata가 이미 충분한 source의 SHA를 바꾸지 않도록 수정했다. 최종 결과는 `final-warm-cache-tests.log`에 보존한다. AST/compile14개·local link·diff·print-only parser PASS이며 Main 최종 수학 kernel의 snapshot SHA도 현재 workspace와 일치한다.

## BLOCK 상승 패턴 탐색 추가 점검

사용자 지적에 따라 [유형별 진단](main-machine-block-pattern-search-diagnosis-2026-10-03.md)을 추가했다. 후보0은 상승0이 아니다. cache KRX BLOCK849시도 중 목표-first564, 학습 적격 BLOCK5/RECHECK33 성공 시도가 존재한다. 이번 recovery budget에는 새 selector 분기 후보가 없으며 전체 Cartesian domain도 미소진이다. 원천 제외와 유형·복합 blocker·시간 순서 탐색을 구분하는 후속 연구가 필요하다. 정책 탐색 로직/threshold는 이 진단에서 변경하지 않았다.

## 남는 결손과 다음 소유자

| 상태 | 소유자/증거 | 다음 행동과 완료 검사 |
|---|---|---|
| Main lineage2877 | machine capture→현재 v7 source acceptance | 진짜 native scanner admission/promotion source가 없으면 제외 유지. attempt/stock/date 조합을 가짜 기회로 쓰지 않는다. 다음 자연 producer 소비에서 exact metadata 확인 |
| 조건부 probe 재생 unsupported | entry split observation contract→strategy_owner_replay `deferred_probe_residual_qty != 0` | 미래 체결·잔여 가격의 정확 owner 의미가 없는 동안 경제 seed를 만들지 않는다. 현행 `DirectFamilySourceRepairMainMechanisticEntry`/`DirectFamilySourceRepairCompactAuxiliary`에 자연 원천 수용 인계 |
| stop/full cost/actual outcomes0 | source projection·owner model validation | retained native receipt가 없으면 EV null. 다음 frozen stop/비용/owner 모델·portfolio·독립 forward holdout까지 모은 후 full economic gate 검증. 현 자료를 같은 내용으로 반복 재생성하지 않음 |
| 10/6 준비 세대 불일치 | 배포 후 `next-preopen.verify-before-prepare.json` | 신규 보완 배포와 별개인 기존 source handoff 문제. 현행 `DirectFamilyPreopenPolicyHandoff`에서 summary/checklist→strict→controller 세대 재봉인 후 selected24 준비/전체 검증. 이전 PASS 재사용 금지 |

이번 배포는 기존24a4658d의 공통 routing/비활성 분석 pin에 한한다. 새 보완 코드·격리 결과는 **배포 대기**다. 다음 PREOPEN 준비 검증은 현재 `strict_checklist_generation_stale`/`source_generation_mismatch`로 실패하며, 이를 준비 완료나 실제 PID 소비로 표시하지 않는다. live policy/bootstrap/override541개 hash는 보존됐다.
