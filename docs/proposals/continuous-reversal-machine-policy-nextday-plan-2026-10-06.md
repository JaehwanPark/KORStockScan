# 연속 반전 기계·보조정책 전환 및 EOD 제외 장후 전체 재생성·10/7 준비 계획

작성일: 2026-10-06 KST. 원천일: `2026-10-06`. 적용 목표일: **2026-10-07(수), 다음 영업일**. 현재 상태: **운영 통합·v9 배포·EOD 제외 전체 장후 재생성·07:35 PREOPEN 완료 / owner 서비스 수리 후 07:49 native 적용 완료 / 07:55 정상 Main PID 및 정책 환경 소비 검증 완료**. 구현 이력은 §10, 준비·cron 소비 경고 보완은 §12~§13, owner 수리는 §14를 따른다.

## 1. 결정과 이번 작업의 범위

사용자의 “장후작업을 중단하고 완료한 연구를 반영할 계획” 지시에 따라 현재 장후 실행을 중단했다. 다음 기계정책은 **기존 기계판정 행이 아니라 연속 가격의 모든 하락→첫 상승 지점**에서 학습·집계한다. 삼성은 시장 3개, 비삼성은 시장 3개 × 가격대 3개, 총 **12개 셀**을 같은 계약으로 확정한다.

선택 지표는 **누적 승률 하나**다. 손익 크기·EV·손익비·Wilson 보정 점수·기존 제출 성공 보존율·최소 표본 수·최소 관찰 일수·별도 holdout 통과를 새 정책 채택 문턱으로 사용하지 않는다. 날짜별 성적·표본 집중·결손 제외 수는 사실 그대로 공개한다. 원천·미래정보 방지·정책 일치 검증은 계산 정확성을 위한 조건이며 성과 문턱이 아니다.

추가 지시에 따라 **계획 수정에 앞서 보조 입력·프롬프트를 보완하고 실제 AI 비교를 완료**했다. 기존 118개와 추가 254개, 372개 반전 지점에 추가 1,742회 호출했다. 운영 AI 횟수 한도의 영구 해제 코드도 반영했다. [보완 연구·코드 검토](../audits/auxiliary-reversal-phase-repair-and-call-quota-review-2026-10-06.md)가 이번 계획의 새 근거다.

계획의 최종 범위는 **기계/보조 장후 로직 전환 → reviewed immutable release 최종 배포 → EOD를 제외한 10/6의 활성 장후작업 전체 재생성 → 10/7 정상기동 준비**다. 이전의 “기계 단계만 재생성·보조는 호환만 유지” 범위는 폐기한다. 표본이 없는 시장 셀은 같은 종목군·유형의 정규장 정책을 그대로 승계한다. 계획 작성 당시에는 실행 전이었으며 후속 승인으로 구현·발행·배포·장후 재생성을 완료했다. 준비 영수증과 다음날 실제 PID 소비는 구분한다.

## 2. 장후 중단 결과와 보존할 상태

| 대상 | 확인 결과 | 처리 |
| --- | --- | --- |
| 주 장후 wrapper | 20:59:55 `failed`, exit 1 | 이미 종료. 원 실패 보존 |
| `main_machine_policy` 별도 단계 | 21:29:59 `succeeded`, `incumbent_carried` | 기존 로직의 완료이며 새 연구 반영 아님. 원 산출물 보존 |
| `summary_handoff` | 21:21:41 `failed` | 이전 controller의 `running` 표시는 낡은 스냅샷. 실제 terminal을 우선 |
| 장후 controller | PGID 385251, wrapper PID 385265, Python PID 385428 | 해당 실행 그룹에 SIGTERM |
| 장후 tuning monitoring | PGID 385250, wrapper PID 385258, 대기 자식 포함 | 해당 실행 그룹에 SIGTERM |
| 중단 확인 | **22:03:45.798 KST**, 두 그룹 잔여 프로세스 0 | 현재 실행 중단 완료 |

근거: [중단 영수증](../../data/report/postclose_operator_stop/2026-10-06/operator-stop-receipt.json), [원 상태 스냅샷](../../data/report/postclose_operator_stop/2026-10-06/planning-state-snapshot.json). cron·timer·정책·기존 runtime selector는 수정하지 않았다. 중단 시점에 살아 있는 Main 거래 프로세스는 관측하지 못했으며, 이 중단 명령이 Main을 종료한 것으로 기록하지 않는다. 파일에 남은 `running`을 성공으로 덮어쓰거나 잠금 파일을 임의 삭제하지 않는다.

선택 release는 `main-submit-drought-20261006-fbfc9dd6`다. selector의 과거 PID receipt는 현재 PID 존재 증거가 아니다. 재개 전에 별도 worker와 예약 작업이 다시 생겼는지 확인하고, 동시 writer가 없을 때 새 세대로 실행한다. 현재 중단은 모든 미래 예약의 영구 비활성화가 아니다.

## 3. 고정할 원천·승패·선택 계약

기준은 [전수 재분석](../audits/continuous-price-reversal-zero-base-research-2026-10-06.md)과 [최종 JSON](../../tmp/continuous-reversal-zero-base-20261006/reviewed-selected-summary.json)이다. 9/21·9/22·9/23·9/28·9/29·9/30·10/2·10/6의 8일, 8,706,868개 기록, 선택 경로의 반전 1,495,955개 중 판정 가능 763,496개를 사용했다. 미확정 732,459개는 제외했다. 오래된 기계판정별 비교 수치는 이 초기 정책의 순위 입력이 아니다.

- **원천:** 동결된 연속 체결·호가와 같은 종목/거래 경로의 완성 분봉 보완. 사건 참조 파일이나 기존 ENTER/BLOCK/RECHECK 캡처가 모집단을 제한하지 않는다. 8일 전체 사용은 이번 초기 연구 계약이다. 종전 9/29 이후 장후 producer 경계를 그대로 복사하여 이 연구의 앞 날짜를 조용히 누락하지 않는다. 6/5 clean baseline 이전 자료는 포함하지 않는다.
- **반전:** 정상 체결의 엄격한 하락 뒤 첫 엄격한 상승. 동일 가격 반복은 방향을 바꾸지 않는다. 후보 추출에 최소 낙폭·거래량·기계 결과를 선행 적용하지 않는다. 각 후보 ID는 날짜/종목/경로/epoch/sequence에 결속한다.
- **진입·목표:** 첫 상승 시점 매도호가를 기준으로 비용 후 +0.4%, 소프트손절 −3.0%, 각 후보의 고유한 1,800초. 연구 비용은 0.23% 1회이며 목표 가격은 `ask × 1.004 / 0.9977`, 손절은 `ask × 0.97 / 0.9977`. 실제 주문 가격 소유자는 기존 가격 resolver다.
- **라벨:** 목표 선도달은 WIN, 손절 선도달 또는 온전한 30분 목표 미도달은 FAIL. 조기 확정은 나머지 30분을 기다리지 않는다. 결손·순서 불명은 보완 후 미확정이면 분모 제외. 60분 후행 회복은 별도 기록한다.
- **경로:** 일자/종목/시장별 유효 가격 관측수가 가장 많은 경로를 연구 주 집계로 선택했고 동률만 SOR→NXT→KRX였다. 이는 사후 원천 중복 제거다. 실시간 라우터가 미래의 종일 관측수를 알아야 하는 조건으로 옮기지 않는다. 운영에서는 현재 정상 경로를 결속하고, 경로 전환 시 해당 경로의 과거 상태를 별도로 재구성한다.
- **분모:** 이번 수치는 반전 시점별 승률이다. 동일 패킷 재전송만 ID로 중복 제거하며 서로 다른 반전을 30분 묶음으로 합치지 않는다. 독립된 주문/파동 수와 같다고 표시하지 않는다. 실제 주문 중복 억제는 기존 intent/custody guard가 담당한다.
- **선택:** 각 셀에서 연구의 13개 고정 후보를 `wins / (wins + stop_fail + timeout_fail)` 원분수로 비교한다. 반올림된 표시값으로 순위를 정하지 않는다. 동률은 조건 수가 적은 후보, 그다음 동결된 연구 `RULES` 순서를 사용한다. 0개 판정 가능은 승률 0이 아니라 비교 불가다. 표본 수·EV로 다시 순위를 뒤집지 않는다.

처음에는 12셀 동시 발행으로 구 정책과 섞이지 않게 한다. 누적 원천이 추가되면 동일한 계약으로 매일 승리/실패/미확정을 합산하고 셀별 최고 승률을 다시 고른다. 캐시 키에는 원천·코드·비용·목표/손절·시간창·경로·특징 정의·정책 버전을 모두 포함한다.

## 4. 다음 영업일에 확정할 12셀 초기안

공통으로 **첫 상승 확인**이 필요하다. `DD5`는 확인 틱 이전 최대 300초에 관측된 정상 고점 대비 저점 낙폭이며 5분을 채우도록 기다리지 않는다. `DROP`은 바로 직전 연속 하락 구간의 고점 대비 저점 낙폭이다. `REBOUND`는 저점 대비 첫 상승 체결가격의 반등폭이다. `VOL`은 최근 60초 체결수량 / 직전 60초 체결수량이다. VOL이 필요한 셀에서만 해당 수량 원천을 요구한다.

| 셀 | 조건 | 승리/판정 가능 | 승률 | 미확정 제외 |
| --- | --- | ---: | ---: | ---: |
| 삼성 프리 | DROP ≥1.0% | 2/2 | 100.0% | 0 |
| 삼성 정규 | DD5 ≥1.2% | 13/13 | 100.0% | 467 |
| 삼성 애프터 | DD5 ≥0.4% | 207/686 | 30.2% | 276 |
| 비삼성 프리·2만원 미만 | DD5 ≥0.8%, VOL ≥1 | 709/870 | 81.5% | 397 |
| 비삼성 프리·2만~10만원 미만 | DD5 ≥0.8%, VOL ≥1 | 500/712 | 70.2% | 1,112 |
| 비삼성 프리·10만원 이상 | DD5 ≥1.2% | 76/76 | 100.0% | 74 |
| 비삼성 정규·2만원 미만 | DD5 ≥0.8%, REBOUND ≤0.3% | 69,610/85,860 | 81.1% | 37,244 |
| 비삼성 정규·2만~10만원 미만 | DD5 ≥1.2% | 20,762/23,796 | 87.2% | 14,185 |
| 비삼성 정규·10만원 이상 | DD5 ≥0.8%, VOL ≥1 | 1,413/1,915 | 73.8% | 1,831 |
| 비삼성 애프터·2만원 미만 | DROP ≥0.4%, REBOUND ≤0.3% | 281/429 | 65.5% | 315 |
| 비삼성 애프터·2만~10만원 미만 | DD5 ≥0.8%, REBOUND ≤0.3% | 143/175 | 81.7% | 379 |
| 비삼성 애프터·10만원 이상 | DD5 ≥0.4% | 221/405 | 54.6% | 354 |

**삼성 정규 0.8%/75.2%는 연구에서 설명한 넓은 후보였고, 최고 누적 승률만으로 확정하면 1.2%/100%가 우선이다.** 13개 승리는 2개 최초 목표 시각에 집중돼 있고 467개가 미확정이다. 프리 DROP 1.0%의 2개 승리도 한 목표 시각에 모인다. 이를 안정적 100% 실거래 승률로 설명하지 않는다. 삼성 프리의 DD5 1.2%도 109/109로 동률이지만 고정 동률 규칙상 DROP 1.0%가 먼저다. 삼성 애프터는 최고 후보도 30.2%라는 사실을 공개하며 임의의 50% 최저 승률 조건은 추가하지 않는다.

비삼성 가격대는 확인 시점 체결가격으로 결정한다. 20,000원은 중간, 100,000원은 높은 가격대다. 연구에 포함된 1,096종목 전체를 새 감시/주문 대상으로 등록하지 않는다. 현재 Main 신규진입 적격 종목에 이 분류를 적용한다. 종목명·섹터·시총 등 새 분류를 내일 정책 선행 과제로 추가하지 않는다.

## 5. 실시간 판정: 관측은 항상, 진입은 첫 상승에서

| 현재 사실 | 기계 출력 | 다음 처리 |
| --- | --- | --- |
| 정상 가격, 해당 낙폭 상태에 들어왔으나 아직 첫 상승 전 | RECHECK | 새 체결마다 상태 갱신 |
| 첫 상승 + 해당 셀 조건 충족 + 현재 필수 입력 유효 | ENTER_NOW | 반전 ID/정책 SHA/수치/진입 참고 호가를 고정해 §6의 새 보조 계약으로 전달 |
| 정상 가격이나 해당 셀 패턴 불충족 | BLOCK | 이번 진입 후보만 제외. 다음 하락→상승 탐색 계속 |
| 필요한 현재 가격/호가/순서/경로 결손 | 기존 source-invalid/RECHECK 계약으로 신규진입 보류 | 결손 이유 별도 기록, 정상 원천 회복 시 상태 재구성 |
| 주문/계좌/custody/퇴역/수동 veto 등 차단 | 기존 guard 결과 | 반전 탐지 상태와 제출 차단 이유를 별도로 보존 |

반전 state 갱신은 기계 평가나 provider 호출 주기와 분리한다. 기존 BLOCK/RECHECK, 기계 cooldown, 목표 매수가 미도달 때문에 원천의 첫 상승이 사라지지 않아야 한다. callback에는 정규화 입력을 소비하는 가벼운 상태 갱신만 둔다. 디스크 재생·장후 집계·provider 호출을 WS 수신 경로에서 실행하지 않는다.

연구와 운영이 같은 순수 탐지/특징 함수를 사용한다. 새 후보에 예전 `buy_pressure ≥60`, VWAP 회복, legacy READY, 다수 긍정 window를 추가 AND 조건으로 붙이지 않는다. 이번 조건에서 정한 VOL/REBOUND만 해당 셀에서 평가한다. 첫 상승 뒤 provider 응답을 기다리는 동안 가격/호가가 바뀌면 현재 source/가격 guard로 다시 확인하며, 오래된 저점 가격을 주문 가능 가격으로 간주하지 않는다.

실시간 freshness/호가/주문 안전 기준은 현재 owner를 유지한다. 연구의 5초 수용이나 quote age 미기록 허용을 운영 freshness 완화로 옮기지 않는다. 연구상 성공·실시간 원천 부적격·후단 차단을 서로 다른 결과로 기록한다. 이는 연구 승률을 실제 제출 승률로 바꾸어 주장하지 않기 위한 구분이다.

Main에 편입된 fixed-watch 종목도 같은 12셀 owner를 읽도록 전환한다. 이전 삼성/두산/신규 고정감시 초기 전략과 새 조건을 동시에 AND하지 않는다. 정책 버전 교체 목록에 Main 전략 override의 대체 범위를 명시하고, manual veto·기존 보유/청산·native episode pin과 퇴역 제외는 별도 보존한다.

연구의 `SOR` 원천 이름과 runtime의 cohort 이름은 같지 않다. [현재 scope 계약](../../src/engine/scalping/entry_setup_scalping_rollout.py)은 프리의 `NXT|NXT_PREMARKET`/`PREMARKET_KRX_LIKE` 계열, 정규의 `KRX|KRX_REGULAR`/`NXT|KRX_REGULAR`/`NXT_REGULAR_OVERLAP`/`NXT_REGULAR` 계열, 애프터의 `NXT|NXT_AFTERMARKET`/`KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET`를 구분한다. 구현에서는 source venue/session과 runtime cohort를 별도 필드로 결속해 시장 셀을 선택한다. 같은 시장은 같은 조건값을 공유하되 한 경로 가격을 다른 경로 체결로 위장하지 않는다. 미등록 alias는 명시 오류로 남기고 기존 NXT 종목 적격성과 세션/거래 경로 guard를 유지한다.

## 6. 보조판정 정책 확정과 장후 학습 전환

### 6.1 우선 반영할 보완 결과

기존 재분류 C는 원 수치를 보존했지만 첫 상승 틱을 포함한 누적 매도/VWAP 지표를 전부 “반전 직전”으로 설명했다. [순수 입력·프롬프트·schema 구현](../../src/engine/scalping/reversal_auxiliary_contract.py)은 첫 상승 시점, 해당 시점까지 누적된 약세, 아직 관측할 수 없는 후속 경로를 구분한다. 매도 우세·VWAP 미회복·음의 누적 모멘텀·거래량 미증가를 자동 VETO로 취급하지 않는다. 첫 상승 이후 재하락을 실제 관측한 것처럼 만들어서도 안 된다.

G(V6)는 시점 구분·매도호가 기준 목표 거리·근거 인용을 보완했다. 372개에서 C 160/222승(72.1%) → G **175/236승(74.2%)**, 승리 PASS 160→175, 실패 PASS 62→61이다. 약한 매수수량 비중과 VWAP 미회복이 겹친 105개에서는 C 51/55승 → G **61/65승(93.8%)**으로 실패 PASS 4개를 유지하면서 승리 10개를 회복했다. 이 특징은 보조의 해석 개선 근거이며 기계 진입에 새 AND 조건을 붙이는 근거가 아니다.

H(V7)는 완전 원천 요청의 SOURCE_QUALITY_GAP/INSUFFICIENT enum을 제거해 결손을 호출 전 구분한다. 전체 162/222승(73.0%)으로 G보다 낫지 않았으므로 최신 버전이라는 이유로 전 시장에 강제 채택하지 않는다. G/H 각각의 모순 NONPASS 1개는 검증 실패로 보존하며 PASS로 자동 보정하지 않는다. 주 승률은 AI 원응답 PASS, 응답 호환성은 별도 기술 지표다. 추가 254개만의 G 승률은 C보다 소폭 낮았고 삼성 애프터 개선도 없었다는 사실을 유지한다.

### 6.2 초기 12셀 선택과 정규장 승계

기계 초기안과 동일한 셀/조건을 충족한 AI 비교점은 **335개**다. 삼성 프리 2개, 정규 13개, 삼성 애프터와 비삼성 9셀은 각각 32개다. 기존 보조 연구의 삼성 프리 DD5 1.2%/정규 DD5 0.8% 성적을 새 프리 DROP 1.0%/정규 DD5 1.2%에 잘못 붙이지 않는다.

아래는 실제 연구 응답으로 만든 **발행 전 초기 선택표**다. A=기존 문구의 동일 지점 실제 재호출, C=문맥 역할 재분류, F=진입가격 기준, G/H=이번 보완 버전이다. 기계 채택 조건과 동일하게 **누적 원 PASS 승률**을 먼저 비교한다. 보조의 동률만 승리 PASS 회복 수, 다시 동률이면 H→G→F→C→A 순서로 정한다. 표본 하한·손익 크기·EV·보정 승률·기존 제출 통과 유지율은 추가하지 않는다. 동률 규칙은 이번 탐색 분석에서 정한 것이며 독립 사전검증으로 표현하지 않는다.

| 종목군 | 시장 | 가격대 | 비교 지점 | 초기 선택 | 원 PASS 승률 |
| --- | --- | --- | ---: | --- | ---: |
| 삼성 | PRE | ALL | 2 | H(V7) | 1/1 (100.0%) |
| 삼성 | REGULAR | ALL | 13 | G(V6) | 11/11 (100.0%) |
| 삼성 | AFTER | ALL | 32 | A | 1/1 (100.0%) |
| 비삼성 | PRE | LT_20000 | 32 | H(V7) | 13/15 (86.7%) |
| 비삼성 | PRE | 20000_TO_100000 | 32 | G(V6) | 13/23 (56.5%) |
| 비삼성 | PRE | GE_100000 | 32 | H(V7) | 19/19 (100.0%) |
| 비삼성 | REGULAR | LT_20000 | 32 | C | 18/22 (81.8%) |
| 비삼성 | REGULAR | 20000_TO_100000 | 32 | A | 6/6 (100.0%) |
| 비삼성 | REGULAR | GE_100000 | 32 | A | 3/3 (100.0%) |
| 비삼성 | AFTER | LT_20000 | 32 | C | 7/12 (58.3%) |
| 비삼성 | AFTER | 20000_TO_100000 | 32 | A | 7/8 (87.5%) |
| 비삼성 | AFTER | GE_100000 | 32 | G(V6) | 11/17 (64.7%) |

표본 1개의 100%도 그대로 공개한다. 승률 우선 선택이 통과를 매우 적게 남길 수 있다는 사실을 숨기지 않고, 높은 PASS 수를 이유로 더 낮은 승률 후보로 교체하지 않는다. 원 반전 중 해당 기계 조건을 만족한 점, AI 호출점, 실제 PASS, 실제 제출은 각각 다른 분모다.

**무표본 승계는 다음과 같이 고정한다.** 정규장 정책을 먼저 확정한 뒤, 프리/애프터에 유효 비교 표본이 0이면 같은 종목군·같은 가격대의 정규장 `prompt + input-role mapping + schema + validator + decision parameters`를 값 변경 없이 복사한다. 삼성은 삼성 정규, 비삼성은 같은 가격대 정규를 승계한다. target market/effective date/receipt identity만 목적 셀의 metadata로 두고 `inherited_from=REGULAR`, 부모 hash와 `NO_LOCAL_SAMPLE`을 남긴다. 로컬 승률은 null이며 정규장 승률을 로컬 실적으로 표시하지 않는다. 다른 시장에 그대로 적용해도 그 시장의 원천/경로/주문 guard는 유지한다.

표본은 있지만 PASS가 0인 후보는 `NO_PASS_DENOMINATOR`로 기록한다. 0승/N과 0/0을 혼동하지 않는다. 해당 셀 전체가 비교 가능한 PASS 분모를 갖지 못하면 정규장 부모를 승계하고 이유를 별도 남긴다. 정규장도 무표본이면 동일 유형의 마지막 검증된 정규장 payload를 carry한다. 그 부모조차 없으면 기존 Main 공통 정규장 incumbent payload를 초기 부모로 명시 지정·검증한다. 검증할 실제 부모 자체가 없으면 부모 결손으로 보고하며 임의 정책을 합성하지 않는다. 빈 파일이나 임의 0% 정책으로 셀을 채우지 않는다. 기계정책의 미래 무표본 셀에도 같은 정규장 승계 순서를 적용한다.

### 6.3 연구 코드에서 정기 장후 producer로 이관

1. 공통 반전 kernel의 **전수 반전 목록**을 누적 원천으로 삼는다. 기존 기계 ENTER_NOW + `provider_called=true` trace만 읽던 `compact_auxiliary_paired_replay.prepare`를 새 family에서 대체한다. 현재 8개 원천일을 포함하고 이후 적격 날짜를 누적한다. 미래 라벨은 입력과 별도 저장한다.
2. `reversal_auxiliary_contract.py`를 as-of 입력 adapter·프롬프트 registry·검증기의 공통 owner로 사용한다. 구현된 파일은 실제 연구와 실시간이 공유하는 운영 입력·영문 프롬프트·schema 계약이다. 실시간에서는 실제 기계 반전 receipt와 같은 facts/hash를 받으며 READY/ENTER_NOW를 무조건 합성하지 않는다. 연구 안내의 offline 문구를 운영용으로 바꾸는 경우 새 prompt hash로 실제 호출 비교를 다시 수행한다. 바뀐 프롬프트에 이번 연구 hash/점수를 그대로 복사하지 않는다.
3. A/C 등 선택된 이전 연구안도 잘못된 시점 설명/legacy READY 중복 요구가 남지 않게 운영 계약으로 이관한다. 문구/역할/schema가 달라지면 각 셀의 **같은 고정 지점**에 새 실제 호출을 하고 누적 원 PASS 승률로 표를 다시 확정한다. 이는 기존 제출 보존이나 독립 holdout 성과 문턱이 아니라 실제 배포할 바이트에 대한 측정이다. 바뀌지 않은 정확한 요청/응답만 cache로 재사용한다.
4. 최종 선택은 `compact_auxiliary_paired_replay.py`와 `entry_setup_paired_replay_batch.py`의 새 continuous-reversal 분기에 넣는다. 기존 20/20 표본·holdout 일수·EV/stress EV·구 prompt 방향 선정 조건을 이 family 뒤에 다시 AND하지 않는다. 그 외 family의 계약은 건드리지 않는다.
5. 셀별 `machine_parent_sha`, reversal ID/feature/source/label/cost hash, input/prompt/schema/model/response ID, raw/validated verdict, WIN/FAIL/exclusion, 비교 분모를 보존한다. 정책 writer는 12셀을 단일 dated bundle로 발행하고 reader는 시장/가격대별 선택과 승계 부모를 검증한다. source/모델/문구/hash가 바뀐 결과를 동일 누적으로 조용히 합산하지 않는다.
6. `main_auxiliary_policy`의 새 의존성은 동일 generation의 `main_machine_policy`와 반전 `outcome_labels`다. `legacy_machine_report --activate-now`가 기계 정책을 덮어쓰거나 AI 단계와 순환 의존을 만들지 않게 report 소비로 정리한다. summary→strict→controller는 machine/auxiliary 두 terminal의 같은 parent를 검증한다.

### 6.4 호출한도 영구 해제와 계수

운영 `HotPathAISymbolBudget()`의 기본 total/group cap은 `None`이다. 예전 60초당 총 4회/그룹 2회 env를 다시 읽어 quota를 되살리지 않는다. 변경은 임시 env override가 아니라 버전 관리 코드의 영구 기본값이며 종료일이 없다. 과거 replay가 명시적으로 유한 값을 복원하는 기능은 감사용으로 보존한다. 최종 release와 다음 PID가 이 코드를 소비했는지 확인한다.

오프라인 연구와 새 장후 보조 호출도 횟수·일일 비용·parent 수 quota 없이 실행한다. 이전 390회 ledger는 감사 원본으로 보존하고 새 무제한 호출 명세/계수로 이동한다. 호출 전 영속 예약·중복 request ID 방지·실제 응답/토큰 기록은 계속한다. 이번 추가 호출 1,742회가 그 계약의 실제 실행 근거다. 구 postclose 호출 지점의 390회/130 parent 제한과 `max_new`에 의한 quota 중단도 새 분기에서 제거한다. 작업을 여러 checkpoint로 나누는 것은 허용하되 누적 호출 수 때문에 미처리 지점을 버리지 않는다. provider의 외부 속도 제한, timeout/오류 재시도와 동일 요청 중복 방지, broker/order cap은 이 변경의 대상이 아니다.

## 7. 구현 위치와 제거할 구 정책 병목

| 변경 지점 | 현재 확인한 구조 | 계획한 변경·완료 기준 |
| --- | --- | --- |
| 공통 반전 kernel | 연구 `extract/analyze/refine_features`에 분리 | `src/engine/scalping/` 안 공통 순수 상태/특징 모듈로 이관. 새 engine root 파일 금지. 접두 구간 불변성·첫 상승·epoch/sequence reset 동일 |
| 정규화 가격 소비 | `micro_reversion/forward_collector.py`가 정상/격리 stream 기록 | 기존 정규화 envelope에서 Main 반전 상태를 공급. 관측용 collector에 주문 권한을 부여하지 않음. 경로별 독립 상태·세션 전환 검증 |
| 장후 연구 producer | `ai_action_outcome_calibration.py --winrate-policy-only` 및 기계 관측 loader | 새 버전에서 연속 stream 전수 모집단·공통 kernel·같은 경로 분봉 보완·12셀 누적 집계를 사용. 기존 기계판정은 마지막 누락 대조만 수행 |
| 선택·승격 계약 | `entry_strategy_policy.py`의 보정 승률과 10/3 표본 조건 등 | 새 `continuous_reversal_winrate_v1`에 누적 원승률 비교 적용. 연구/발행/activation validator 모두 같은 계약을 읽게 해 뒤에서 옛 문턱이 재등장하지 않음. 다른 family 계약은 유지 |
| 기계 실행 | `entry_setup_evidence.py`, `entry_strategy_policy.py`, `sniper_state_handlers.py` | 새 정책 version을 인식하는 독립 분기로 12셀을 선택. 미래 라벨을 읽지 않으며 구 전략 조건과 중복 판정하지 않음 |
| 정책 writer/loader | `mechanistic_entry_runtime_policy.py`, `entry_designated_policy.py`, Main fixed-watch resolver | 12셀·시장/경로 mapping·원천/특징/비용 SHA를 한 dated bundle로 검증. 기존 지정 정책의 보존 분기가 새 선택을 몰래 덮어쓰지 않음 |
| 보조 AI 계약·장후 학습 | 구 compact trace 모집단·prompt/EV selector | §6의 as-of 역할/목표 거리/인용 계약과 실제 AI 누적 PASS 승률 선택을 producer→prompt→validator→publisher→runtime에 함께 연결. 무표본은 동일 유형 정규장 승계 |
| 호출 quota | 운영 shared counter와 오프라인 capped ledger/max_new | 운영 기본 cap=None 코드 완료. 새 장후 producer도 무제한 호출 명세+계수로 전환. 만료/이전 env에 의한 재활성화 없음 |
| 장후 dispatcher·전체 재생성 | `postclose_summary_handoff.py`의 구 recipe와 wrapper 자동 recovery/reuse | 새 machine/aux/label dependency·code hash를 결속하고 §8의 `all_except_eod` 새 세대를 지원. 날짜/파일 존재만으로 옛 성공을 reuse하지 않음 |
| 후행 구 writer | `legacy_machine_report` 명령의 `--activate-now` | 새 기계 bundle을 옛 전략으로 다시 쓰지 못하게 조정. 보고서가 필요하면 새 최종 정책을 읽는 report 소비로 전환하고 활성화는 단일 writer가 소유 |
| 최종 인계 | summary→tower→checklist→strict→controller/finalization→PREOPEN | 새 source/kernel/policy 해시가 같은 세대인지 검증. bootstrap 검증과 다음 Main PID 소비를 별도 기록 |

현재 파일 경로: [dispatcher](../../src/engine/automation/postclose_summary_handoff.py), [기계 producer](../../src/engine/scalping/ai_action_outcome_calibration.py), [선택 계약](../../src/engine/scalping/entry_strategy_policy.py), [bundle owner](../../src/engine/scalping/mechanistic_entry_runtime_policy.py), [판정](../../src/engine/scalping/entry_setup_evidence.py), [정규화 stream](../../src/engine/scalping/micro_reversion/forward_collector.py), [fixed-watch 연구](../../src/engine/monitoring/main_fixed_watch_policy_research.py).

Kiwoom 요청·FID·응답 parser를 바꾸는 계획이 아니다. 추가 보완이 필요하면 기존 완성봉 소비자를 사용하고, 프로토콜 수정이 필요해지는 경우에만 공식 reference gate를 적용한다. 연구 보완 시 다른 경로 봉 혼합·부분 봉 미래 혼입·동일 봉 양 선 선후 추측을 금지한다.

## 8. 실행 순서와 다음 영업일 준비 시각

아래는 구현 착수 시 목표 시간이다. 완료 영수증 없는 단계를 시간 경과로 통과시키지 않는다. **source date=10/6, policy publication 기준일=10/6, effective date=10/7**을 자정 이후에도 고정한다. 실제 파일 작성 시각 `generated_at`은 사실대로 남긴다. wrapper의 `THRESHOLD_CYCLE_POLICY_PUBLICATION_DATE`→`POSTCLOSE_POLICY_PUBLICATION_DATE`/`POSTCLOSE_PREPARED_EFFECTIVE_DATE`와 직접 dispatcher 경로가 같은 날짜를 소비하게 하여 10/8 정책이 생성되지 않게 한다.

| 단계 | 목표 시각 KST | 작업 | 완료 영수증 |
| --- | --- | --- | --- |
| P0 | 10/6 22:03 완료 | 기존 장후 중단·실패/정책 보존 | 원 중단 receipt. 실행 재개 직전 writer 재확인 |
| R | 이번 보완 완료 | 보조 실제 AI 추가 1,742회·372점 비교·운영 quota 제거 코드 | 연구 보고서/원문 response ID·대상 검증. 배포는 미완료 |
| P1 | 10/7 00:30 목표 | 공통 kernel·12셀 machine/aux schema·누적 승률·정규장 승계·장후 producer/consumer·무제한 계수 통합 | review/fix/re-review, targeted tests, wrapper/parser/직접 소비 검증 |
| P2 | 01:30 목표 | 동결 반전 수치 재현·실시간 접두 재생·운영용 정확 prompt 실제 호출과 12셀 최종 확정 | 연구/운영용 바이트 구분, final machine+aux matrix, parent/cost/source hash |
| P3 | 02:00 목표 | **전환된 기계·보조 장후코드 최종 배포** | immutable release·code manifest·selector/router 및 모든 예정 wrapper root 확인, rollback snapshot |
| P4 | 04:30 목표 | **EOD 제외 오늘의 활성 장후작업 전체 새 세대 생성** | 아래 inventory 전 항목의 새 run/terminal/output/dependency hash. EOD 원본 hash 보존 |
| P5 | 06:30 목표, 종료 상한 **06:50** | 문서/추천 인계 마감→strict→controller/finalization→cleanup/final detector→10/7 준비 검증 | 현재 최종 checklist hash의 strict PASS, 전체 장후 complete와 exact-date prepared 확인 |
| P6 | 예약 07:32 owner / 07:35 Main PREOPEN | exact 10/7 machine+aux 12셀·승계·episode 기존 owner pin·호출 quota loader 검증 | PREOPEN verify, prepared와 예약 소비 구분 |
| P7 | 예약 07:55 Main 시작, 08:00 프리 | 정상 기동의 실제 code/policy 소비 확인 | singleton PID/root·두 policy SHA·quota=None·fresh source. 자연 판정/주문/체결은 별도 |

다음 영업일은 `src.utils.market_day`로 확인한 10/7이다. 07:35/07:55는 앞선 계획 작성 시 설치 cron에서 확인한 시각이며 P3에서 다시 대사한다. Native episode 정책을 Main 반전 정책으로 교체하지 않고 별도 승인된 기존 owner 정책·퇴역 목록을 보존한다.

### 8.1 EOD 제외 전체 재생성 계약

**일부 영향 단계만 복구한다는 이전 방침을 이번 계획에서는 사용하지 않는다.** 사용자 지시대로 EOD를 제외한 현재 활성 장후 owner를 전부 같은 final release/source date/generation으로 실행해 새 terminal과 출력 manifest를 만든다. OFF/퇴역된 Widget·generic Daily/EV/selector·panic 재생성·retired AI 연구를 “전체”라는 이유로 복원하지 않는다.

현 wrapper는 EOD를 시작하는 것이 아니라 `wait_for_eod_terminal`로 기다린다. **EOD 제외는 이 검증 gate를 끄는 것이 아니다.** 10/6 EOD 성공 terminal·DB 날짜/원천 snapshot을 읽어 고정하고 KOSPI EOD updater는 호출하지 않는다. 원 receipt/hash는 재생성 완료 때까지 비교하며 바뀌면 세대 충돌로 기록한다. EOD를 성공했다고 가짜 terminal을 만들지 않는다.

현재 자동 recovery가 이전 terminal/checkpoint를 재사용할 수 있으므로, 구현 때 `all_except_eod`라는 **명시적 전체 재생성 모드와 generation manifest를 추가**한다. 구현한 환경 계약은 `THRESHOLD_CYCLE_REGENERATION_SCOPE=all_except_eod`, `POSTCLOSE_REGENERATION_SCOPE=all_except_eod`, `POSTCLOSE_REGENERATION_ID`이며, source/publication 10/6·effective 10/7을 별도로 전달한다. 기존 성공 cache를 우회하고 새 run/terminal을 기록하는 계약과 실행 manifest를 최종 release에서 검증했다. 공유 날짜 status를 무작정 삭제해 cache miss를 만들지 않는다. 원 실패/중단/이전 성공은 immutable attempt history로 남긴다. 정확하게 일치하는 raw snapshot·완성봉·실제 AI 응답은 계산 재현의 입력으로 읽을 수 있지만, 구 report/terminal을 새 실행 성공으로 표지만 바꾸지 않는다.

| 재생성 대상 | 기존 실행 owner | 새 세대 완료 기준 |
| --- | --- | --- |
| 주 장후 전체 | `deploy/run_threshold_cycle_postclose.sh` | 원천 품질/preflight·완료 거래 사실/경제 reference·취소 대기·holding vote·initial quantity·현재 활성 embedded 진단/보고까지 전체 inventory와 새 출력 manifest. 신규 machine/aux 외의 원 정책 권한 보존 |
| 기계·라벨·보조 | `postclose_summary_handoff.py`의 `main_machine_policy`, `outcome_labels`, `main_auxiliary_policy`, `legacy_machine_report` | 새 반전 모집단·단일 라벨·실제 AI 누적·같은 dated 부모. legacy writer의 역덮어쓰기 제거 |
| 나머지 등록 단계 | `pre_submit_delay`, `machine_attribution`, `machine_timing`, `market_weakness`, `research_capacity`, `legacy_policy_approval`, `episode_policy`, `research_allocation` | 활성 단계는 원 의존순서로 다시 실행. 별도 승인으로 OFF인 단계는 같은 세대의 explicit OFF 검증, 복원 금지 |
| 독립 기계 refresh | `deploy/run_machine_microstructure_final_refresh.sh` / machine_group | 새 registry/같은 release를 사용하고 wrapper에서 실행한 동일 stage를 동시 중복 dispatch하지 않음 |
| tuning monitoring | `deploy/run_tuning_monitoring_postclose.sh` | 새 main predecessor terminal·Parquet/DuckDB 원천·검증/인계 재생성 |
| DB archive | `deploy/run_dashboard_db_archive_cron.sh` | 10/6 EOD 원본 읽기 검증 후 새 archive 실행/검증 receipt. 이 wrapper의 날짜는 위치 인자가 아닌 `TARGET_DATE=2026-10-06` 계약임에 주의 |
| summary·추천·tower·checklist | 현 summary/intake/tower/checklist owner | 새 family 출력 전부 결속, 처리한 추천의 인계 재수렴, stable ID 중복 없음. 외부 Project/Calendar sync 제외 |
| strict·DONE controller | `verify_threshold_cycle_postclose_chain --date 2026-10-06 --compact-summary-only --require-summary-handoff`, `deploy/run_postclose_done_controller.sh` | 새 최종 checklist/summary/policy generation, stale PASS 사용 금지. controller의 구 wrapper 자동 복구와 새 전체 run이 충돌하지 않음 |
| 최종화·정리·최종 detector | `deploy/run_postclose_finalization.sh 2026-10-06` 및 native cleanup/detector owner | 새 predecessor 완료→cleanup→정확 source date의 final detector terminal. 이번 원천/AI 영수증 보호 manifest 선행 |
| 다음날 준비 | runtime bootstrap/기계·보조 loader 및 예정 PREOPEN owner | 10/7 12셀·정규장 승계 부모·단일 generation·최종 release pin. episode 기존 pin/퇴역 상태 보존 |

P3 전 현재 writer/PID/lock/예약 future run을 대사한다. 구 worker가 쓰는 코드와 산출물을 도중 교체하지 않는다. P4의 모든 owner는 승인된 final release에서 시작한다. 이미 배포한 파일을 실행 중 수정하지 않는다. 원천 보존 manifest에는 전수 가격 stream·라벨·새 AI 입력/원문/계수·선택표·rollback 부모를 넣고, archive/cleanup이 연구 근거를 제거하지 않게 한다.

### 8.2 준비 종결의 의미

`postclose_all_active_stages_complete=true`와 `next_session_policy_ready=true`를 **각각** 확인한다. 전자는 오늘의 EOD 제외 재생성 inventory와 최신 terminal, 후자는 10/7 bootstrap의 machine/aux/기존 episode loader와 정확한 부모 hash 검증이다. 문서 확정 후 strict→controller→prepared 순서로 고정하여 나중에 checklist bytes를 바꿔 즉시 stale로 만들지 않는다. 변경이 생기면 영향받은 마지막 인계를 새 세대로 다시 검증한다.

P5까지 준비를 완료해도 07:55 실제 PID가 뜨기 전에는 “정상기동 완료”라고 쓰지 않는다. P7은 정상 예약 소비의 최종 확인이며 성과 입증용 주문을 만들지 않는다.

## 9. 검증·종결·실패 시 처리

**연구/실시간 동일성:** 모든 반전을 누락 없이 추출, 같은 가격 반복 처리, 첫 상승의 접두 구간 불변성, 확인 틱의 과거 고점 혼입 금지, 각 후보 독립 30분, 정확한 30분 목표 접촉, stop-first, 결손/같은 봉 선후 불명 제외, 완료 분봉 경계, 동일 packet 중복, epoch/경로/세션 전환을 검사한다. 비삼성 가격대 경계와 삼성 우선 분류도 검사한다. 기존 연구 21개 테스트를 토대로 구현 경계 회귀를 추가한다.

**새 선택의 일관성:** 기계 raw win fraction와 보조 raw PASS win fraction의 각 12셀 matrix가 연구/발행/loader에서 같아야 한다. 프리/애프터 무표본→같은 유형 정규장 payload/hash 동일 승계, 정규장도 무표본인 부모 carry, 0승/N과 0/0 구분을 회귀로 확인한다. 보조 input/prompt/schema 변경 시 실제 호출 cache miss와 미래 라벨 불포함도 검사한다. 일부 함수에 Wilson·holdout 10/3·EV·기존 ENTER 유지 조건이 남아 있지 않아야 한다. 원천 결손을 0원/실패로 메우지 않는다. n=0의 undefined와 실제 0승을 구분한다.

**실행 경로:** 동결 삼성 09:05:01 반전은 DD5 ≥1.2% 후보가 되고 같은 시점의 미래 데이터 없이 판정된다. BLOCK/RECHECK 이후에도 다음 반전이 포착된다. 비삼성 각 9셀의 양성/음성 사례가 Main 소비자까지 연결된다. 주문 경로는 fixture로 검증하며 실제 주문을 만들지 않는다. 보조 연구/최종 prompt 비교의 실제 provider 호출은 이번에 승인된 무제한 연구 범위에서 수행하고, 코드 unit test는 mock으로 분리한다. 기존 order/source/custody/manual/retirement guard가 유지되는지 확인한다.

**운영 인계:** 구 release에 새 파일만 덮어쓰기 금지. parent/CAS와 새 dated bundle의 정확한 hash, 모든 consumer의 단일 policy generation, 자정 이후 effective date, stale cache/구 stage terminal 거부, 중단 뒤 잔여 writer 부재, 원 실패 보존을 확인한다. 문서 owner를 최종 확정한 뒤 strict를 실행하여 checklist 변경으로 검증이 즉시 낡지 않게 한다.

06:50까지 필요한 기술 검증이 끝나지 않으면 새 정책을 적용 완료라고 보고하지 않는다. 검증된 incumbent carry가 정확한 날짜·기존 owner 계약으로 가능한지 별도 확인하고, 없으면 해당 신규진입 경로를 준비 실패로 남긴다. 과거 날짜 정책을 조용히 최신으로 표시하지 않는다. rollback은 parent bundle+release+소비 계약을 함께 복구하며 퇴역 owner를 되살리지 않는다. 손절/수량/주문가격/provider 경로·모델은 바꾸지 않는다. 별도 명시 승인된 AI 호출 횟수·연구 비용 quota 해제는 §6.4대로 적용하며 이를 broker cap 해제로 확대하지 않는다.

## 10. 소유·현재 완료 상태

통합 실행 owner는 현재 체크리스트의 **`DirectFamilySourceRepairMainMechanisticEntry`**를 재사용한다. 기존 **`DirectFamilySourceRepairCompactAuxiliary`**는 §6의 보조 producer/consumer 통합을 소유하고 결과를 통합 owner에 인계한다. 두 owner가 전체 wrapper를 중복 실행하지 않으며 기존 보조 OPEN에 남은 EV/holdout 종결 조건은 새 반전 family에서 제거한다. 기존 10/2 원천 결손 기록은 이력으로 보존하고 현재 종결 기준은 이 문서 P1~P7(기계·보조 전환/최종 배포/EOD 제외 전체 장후 재생성/준비/실제 소비)로 갱신한다. `MainSubmitDroughtPathAcceptance1006`는 기존 평가·증거 전달 수리의 자연 수용을 계속 소유하며 새 정책 발행 owner로 복제하지 않는다.

10/7 구현 결과: 기계·보조 장후/실시간 공통 kernel과 운영용 입력·프롬프트·schema, 영구 무제한 AI 횟수 정책을 전체 재생성 release `0e067426`에 배포했다. 관련 immutable 회귀 683 PASS·삼성 source-custody 34 PASS이며, 실제 AI 2,232회 시도의 원 응답과 누적 승률 재계산 결과에 기계 12셀·보조 12셀 모두 일치한다. 무표본 셀의 동일 유형 정규장 payload/hash 승계와 격리 PREOPEN 활성화·parent CAS·중복 활성화 검증도 통과했다. 03:54:15 시작한 source/publication 10/6·effective 10/7 EOD 제외 전체 generation의 Main native는 04:14:46 성공했고 최종 prompt consumer·기계/보조 scoped·Main seal issues=[]다. 독립 단계 최종 갱신·archive·3 Parquet/압축 검증/대조를 완료했으며 whole 13 stage strict/controller issues=[]다. cleanup·최종 detector 완료 및 10/7 exact-date prepared_verified를 확인했다. 최종 checklist bytes에서 strict/controller/finalization/cleanup/detector를 다시 봉인했고 04:22:07 prepared_verified, 04:22:42 현재 세대 재검증 PASS를 확인했다. EOD 원본과 연구 원천 110개·실제 호출/응답 로그 2개는 정리 후에도 SHA 불변이다. 07:35 PREOPEN과 07:55 실제 PID 소비는 예약 기동 이후의 별도 acceptance다. 원 실패·중단·보완과 최종 실행 근거는 [구현·실행 검토](../audits/continuous-reversal-implementation-postclose-execution-review-2026-10-06.md)에 기록한다. 기존 기준 문서 Rebase/README/AGENTS는 이 구현 기록으로 덮어쓰지 않는다.

최초 기계 전용 계획 검증은 [이전 계획 검증 영수증](../../tmp/continuous-reversal-nextday-plan-20261006/plan-validation.json)에 기록한다. 계획용 matrix는 [비활성 정책 초안](../../tmp/continuous-reversal-nextday-plan-20261006/policy-plan.json)에 보존한다. 둘 다 운영 policy 디렉터리의 발행물이 아니다.

이번 보완의 문서·코드·실제 호출 검증은 [새 최종 검증](../../tmp/auxiliary-reversal-phase-repair-20261006/final-validation.json), 보조 초기 선택은 [실제 AI 집계](../../tmp/auxiliary-reversal-phase-repair-20261006/actual-ai-summary.json)를 따른다. 이전 planning JSON을 새 통합 운영 정책으로 승격하지 않는다.


## 11. 구현 시 확정한 운영 계약

`THRESHOLD_CYCLE_REGENERATION_SCOPE=all_except_eod`는 기존 report-step 재사용을 끄고 새 generation ID를 status와 stage에 기록한다. 날짜 status를 삭제하지 않고 원 실패·중단·이전 성공 attempt를 보존한다. 전수 가격·완료봉·실제 AI 응답은 동일 hash cache 입력이며 새 계산/최종 consumer를 구 terminal로 대체하지 않는다. EOD updater는 실행하지 않고 원 정확일 terminal/hash를 비교한다. 새 두 단계 명령은 `scalping.continuous_reversal_postclose --mode machine/auxiliary`, 새 보조 의존성은 자체 반전 라벨을 포함한 `main_machine_policy`다. 기존 outcome_labels는 기존 거래/진단 consumer용으로 전체 실행에 포함한다. `legacy_machine_report`는 report-only 실행하며 새 native bundle을 덮어쓰지 않는다.

최종 release에서 main wrapper, 독립 machine refresh/tuning/archive, 등록 13 stage(OFF는 새 OFF receipt), summary/tower/checklist/strict/controller/finalization/cleanup/final detector와 prepared bootstrap을 새로 확인한다. 동일 stage를 동시 중복 dispatch하지 않는다. controller 자동 wrapper rerun은 수동 전체 run과 충돌하지 않게 해당 실행에서 끈다. native two-worker/자원 guard는 유지한다. 최종 checklist bytes 뒤 strict→controller→prepared 순으로 봉인한다. 07:35/07:55 예약 이전에는 PREOPEN/실제 PID 성공을 주장하지 않는다.

기계정책 writer는 Main wrapper 하나다. 독립 machine group은 새 family의 `main_machine_policy`를 재생성하지 않고 기존 독립 분석을 생성한다. 보조 단계·native loader는 source manifest와 최종 실제 AI 응답의 byte hash를 함께 검증한다. 프리/애프터 무표본은 동일 정규 payload/hash를 승계하며 정규 자체 무표본은 검증된 이전 동일 scope 정규 부모만 승계한다. 검증 가능한 정규 부모가 전혀 없으면 명시 실패로 남긴다.


운영용 실제 재비교와 최종 12셀은 [구현·실행 검토](../audits/continuous-reversal-implementation-postclose-execution-review-2026-10-06.md)를 따른다. §6의 초기 offline 선택표는 원 연구 이력이며 운영용 다른 문구에 그 성과/hash를 붙이지 않는다. 실시간/장후 동일 kernel의 접두 재생 372점·701,638개 반전은 일치했다. 현재 실행 owner는 [10/7 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md)이다.

새 family의 최종 summary는 실제 `continuous_reversal/<source>/machine.json`·`auxiliary.json` 및 정확한 native 12셀 bundle을 소비한다. `cumulative_winrate_selected` 상태의 유효한 영수증은 PREOPEN 인계로 투영하며 구 EV/holdout 통과와 혼동하지 않는다. Main wrapper가 필요한 tower를 최종 checklist 전에 생성하고, 검증기는 기존 수동 통합 owner 두 개의 예약 소비 업무를 보존한다.

## 12. 10/7 예약 최종화 prepared 세대 경고 보완

05:01:46 detector는 새 controller와 아직 갱신 전인 04:22 prepared를 대조해 `prepared_source_or_release_changed`를 보고했다. 05:01:50 정기 최종화가 새 prepared를 발행했고 06:24 현재 전체 준비 검증은 PASS다. 최종화 순서를 **controller/strict→cleanup→동일 원천/적용일 prepared 생성·검증→최종 detector→최종 generation 재검증/DONE**으로 보완했다. 준비 실패·탐지 실패는 DONE을 발행하지 않으며, 실제 stale/corrupt receipt 검사는 그대로다. 기존 source/publication 10/6·effective 10/7 policy와 반전 kernel/12셀은 변경하지 않는다. 관련 wrapper/준비/탐지 회귀 240 PASS를 immutable release `0d4e5d2a4004e89a20ea14eb05c720d812e5bb27`에서 확인했다. 정상 Main PREOPEN/시작은 07:35/07:55로 유지한다. Main 전체 학습이나 EOD를 다시 실행하지 않고 이미 닫힌 10/6의 native finalization만 복구하여 새 준비를 봉인한다.


최종 v9 인계는 06:34:08 완료했다. 새 prepared는 06:34:05에 발행됐고 현재 전체 계약 검증은 PASS·findings=[]다. 최종 detector 7개/fail 0, whole_native_chain strict/controller pass, 최종 generation/report hash 대조를 확인했다. 기계·보조 정책 bundle과 각 12셀·EOD·동결 원천 110개·호출/응답 로그 2개는 불변이다. 기존 episode 원천 결손과 구 삼성 동결 연구 실패는 report-only 경고로 보존한다. 07:35 PREOPEN 및 07:55 실제 Main PID 소비는 기존 owner의 OPEN으로 남으며 정상 예약 기동에서 확인한다. [보완 종결 영수증](../../data/report/continuous_reversal/2026-10-06/prepared-alert-repair-20261007.json)을 따른다.


## 13. 07:00 최종화 cron 로그의 마지막 소비 보완

06:34 수동 복구 출력은 별도 audit 로그에만 남았고 정식 `logs/postclose_finalization_cron.log`에는 05:01 이전 chain이 남았다. 07:00 탐지의 `finalization_chain_generation_changed`는 이 마지막 소비 인계 누락이다. 현재 controller/prepared는 유효하고 06:34 audit chain은 현재 세대와 일치한다. 코드·정책 변경 없이 reviewed v9의 `run_with_owned_log.sh --owner postclose_finalization_cron --log <workspace>/logs/postclose_finalization_cron.log <release>/deploy/run_postclose_finalization.sh 2026-10-06 --recover-closed-target`로 native 복구한다. scope는 정확일 finalization이며 Main 학습·EOD·주문·bot 기동을 동반하지 않는다.

종결은 별도 audit DONE만으로 판단하지 않는다. 정식 cron 로그의 최신 exact source/effective-date DONE과 현재 chain/snapshot hash, child detector run/report hash, prepared 전체 계약 및 자기 ancestor가 없는 독립 cron consumer를 모두 대조한다. 늦은 복구의 `recovered_late` 경고는 보존하고 generation fail과 구분한다. 원 로그/07:00 실패 보고서를 보존하며 성공 marker를 수동 복사하거나 stale 검사를 우회하지 않는다.


정식 owned logger 복구는 07:03:11~07:05:03 완료했다. 새 prepared는 07:05:00에 생성됐고 현재 전체 계약 PASS·findings=[]다. 자기 ancestor가 없는 독립 CronCompletionDetector의 현재 실제 판정은 `recovered_late` 경고, generation issues=[]이며 07:00의 generation fail은 해소됐다. 정식 최신 DONE과 현재 chain/snapshot·실제 child detector run/report hash를 대조했고 final detector 7개/fail 0이다. v9 source 36개·기계/보조 bundle·EOD·동결 원천 110개·호출/응답 로그 2개는 불변이다. 원 06:34 audit 복구와 07:00 실패 영수증은 역사로 보존한다. [최종 인계 보완 영수증](../../data/report/continuous_reversal/2026-10-06/finalization-log-handoff-alert-20261007.json)을 따른다. 07:35/07:55 실제 소비는 예정 owner에 남는다.


07:07:14 현재 시각의 독립 full 읽기 전용 탐지도 7개 모두 실행해 fail 0·runtime mutation none을 확인했다. 전체 severity는 기존 경고와 recovered_late를 포함한 warning이다. [독립 full 보고서](../../data/report/continuous_reversal/2026-10-06/finalization-full-readonly-after-0700-repair-20261007.json)는 07:00 원 실패 및 native source-date child 보고서와 별도이며 예정 자연 탐지 실행으로 표시하지 않는다.


## 14. 07:32 owner 적용 실패의 취소 ACK 분류 수리

07:35 episode applied_missing 경고 이후 적용파일 31profile 및 Main PREOPEN 07:35:10 succeeded를 확인했다. 그러나 별도 07:32 owner auto-apply는 owner_registry_retirement_not_flat로 실패했다. 검증된 원장에는 두산 9/7·9/9의 ORDER_BOUND/CANCEL 3개만 남고 episode NEW 미체결·잔여 수량·unbound는 각각 0이었다. 열린 노출 집계가 CANCEL을 NEW처럼 센 결함을 수리한다. CANCEL만 제외하고 NEW·AMEND·불명확 action·현재 broker 수량/미체결·미확정 intent·custody guard는 보존한다. 역사 원장 행을 terminal로 재작성하지 않는다.

리뷰/회귀 163 PASS를 기본 작업본 및 별도 owner immutable 470ddc06dfb072e1b0b0994da06f0b498714129d에서 확인했다. 기존 owner 511664f3를 부모로 해당 검사/테스트만 변경한다. Main selector/PREOPEN v9와 기계·보조 bundle, 기존 episode 186 policy pin은 유지하고 auto-apply 서비스의 code pin만 배포한다. 기존 standing authority 07:32~07:54 안에서 quiescent/fresh broker/동일 request·scope·원 activation 검증을 거친 native apply로 재개한다. 이 실행의 외부 API는 기존 read-only broker inventory/open-order 확인이며 주문이나 수동 custody 재분류를 하지 않는다.

소유권은 기존 DoosanEpisodeToMainFixedWatch와 Main 통합 owner의 PREOPEN 자연 수용에 이어진다. 현재 checklist의 완료/OPEN 및 봉인 bytes를 바꾸지 않고 [복구 영수증](../../data/report/continuous_reversal/2026-10-06/startup-owner-cancel-ack-repair-20261007.json)에 code pin·fresh snapshot·native result와 실제 소비를 각각 남긴다. 구 삼성 동결 후보 실패는 source hash 변경의 report-only 이력으로 유지하며 새 Main 반전 정책의 실패로 표시하지 않는다.
### 07:45 후속 marker 검사 보완

07:45 native 재시도는 15개 종목의 소유권을 적용했지만 `policy_applied_marker_migration_pending`으로 종료했다. 승인된 Main 전용 초기 종목 036930·196170·403870은 앞단에서 범위 표식 없이 허용하면서, 후속 단계는 episode 범위 표식을 필수로 요구한 불일치였다. 기존 manual veto는 추가·삭제하지 않는다. 승인된 fixed-watch 종목이며 소유권 집합이 정확히 `main_scalping`·`manual_operator`인 경우에만 신규 범위 표식을 요구하지 않으며, 남아 있는 legacy 표식 검사는 유지한다.

작업 소스 `d3e19363`을 전용 owner 배포본 `208a9069d91bdbdb50c850ff709a24bdb6eb12bf`에 반영했다. 기존 취소 ACK 수리와 함께 작업본·독립 배포본 모두 165개 회귀가 통과했다. 현재 Main bootstrap은 변경 없이 PASS다. 기존 정책 적용 영수증을 검증하는 native idempotent 경로로 marker 완료만 재시도하며 정책을 다시 적용하거나 주문을 생성하지 않는다. 성공 판정은 서비스 exit 0, 현재 날짜의 native `applied` 영수증, Main bootstrap의 재검증을 모두 요구한다.

07:49:54 service exit 0으로 완료했다. 현재 native `applied`·15종목·범위 전환 완료, marker 재시도의 기존 정책 영수증 불변, Main exact-date PREOPEN/bootstrap PASS를 확인했다. episode applied 31profile은 현재 정상이고 개별 기동은 아직 future_due다. 독립 v9 full 읽기 전용 검사는 7개 실행/fail 0/운영 mutation 0이다. 구 삼성 동결 연구의 원천 hash 변경 실패와 구 episode 원천 결손·늦은 최종화 복구 경고는 보존한다. 수리 배포본의 최초 실행은 공유 `.venv` alias 준비 누락으로 exit 127을 반환했으며, checkout assets를 보존하고 data/logs/tmp/.venv 결속을 확인한 뒤 immutable 회귀를 다시 통과하고 성공했다. Main v9·정책·실제 예정 기동은 그대로이며, 07:55 PID 소비는 별도 수용이다.

07:55:02 예약 정상 기동은 Main PID `665299`/selected v9/clean source다. native 07:55:03 PID 소비 및 독립 재검증은 PASS, mismatch·정책 실패 0이며 WS 로그인은 07:55:18에 확인했다. 현재 native bundle `bf15fc240560605b7fe08796941288d9ef28a5f7c8d2cbf47692787b894f4a98`, 기계·보조 12+12셀, 누적 원승률·30분/+0.4%/soft −3% 계약이 유지된다. selected v9의 실제 운영 생성자 기본 total/group cap은 None이며 기존 횟수 env를 다시 읽지 않는다. release-set은 PID 결속 및 episode 186pin PASS이고 개별 episode 기동은 future_due다. 아직 자연 반전 판정·제출·체결·손익 또는 기능적 운영 건강 전수를 검증한 것은 아니다.
