# 기계 진입 판정의 후행창·실제 사례·전수 필드 연관 진단

기준일: 2026-09-24 KST. 대상은 clean baseline(2026-06-05) 이후 저장된 **main 기계 진입 관측 중 원래 경로 labeler로 연결할 수 있는 전 기간**이다. 이 문서는 읽기 전용 진단 결과이며 정책, 임계치, 주문, 선택 release/PID를 변경하지 않는다. 계산에 사용한 판정·labeler 파일의 SHA-256은 장후 release `postclose-whole-recovery-20260924-v3`와 작업본에서 일치한다(`entry_setup_evidence.py` `2080b022…`, `entry_strategy_policy.py` `a79f7c59…`, `ai_decision_quality.py` `ca950af2…`). 실제 다음 장전 소비와 운영 손익은 별개다.

## 1. “얼마 뒤 올랐는가”의 현재 규칙

| 층위 | 고정 관측창·판정 | 해석 |
| --- | --- | --- |
| 후행 관측 | 판정 시각 이후 1·3·5·10·20·30·60분. entry의 대표 경로는 **10분**. 마지막 관측과 창 끝의 차이가 90초를 넘으면 그 창은 미성숙/원천 결손으로 남는다. | 날짜별 최적 시점을 사후 선택하지 않는다. [상수와 stage별 대표창](../../src/engine/scalping/ai_decision_quality.py), [mature_outcome_labels](../../src/engine/scalping/ai_decision_quality.py). |
| 단순 경로 | 기준 가격 대비 +0.30%와 -0.70%의 첫 도달 순서를 기록한다. | 비용이 +0.30%를 넘을 수 있어 수익성 판정으로 대체하지 않는다. |
| 비용 포함 품질 경로 | 원래 시점의 `executable_ask`를 기준으로 **왕복 보수 비용 + 순이익 0.10%**를 목표, -0.70%를 고정 CF 손절로 놓고 고가/저가 첫 도달 순서를 판단한다. 목표/손절이 같은 초 봉이면 `same_bar_ambiguous`; 둘 다 없으면 `neither_hit`로 검열한다. | 목표가 먼저여도 실제 매수·매도 체결은 증명되지 않는다. [계산식과 label 분기](../../src/engine/scalping/ai_decision_quality.py). |
| 빠른 이익 분류 | 3분 이내 목표 도달, 손절 근접도가 80% 미만, 관측 간격 최대 90초, 목표 전 중립 체류 비율이 50% 미만이어야 `CLEAN_FAST_PROFIT`이 된다. 30·60·180·300초 checkpoint도 남긴다. | 늦은 이익, 깊은 역행 후 이익, 횡보 후 이익을 따로 둔다. |
| 기계 사례 분류 | `BLOCK/RECHECK`와 `CLEAN_FAST_PROFIT`의 교집합은 `missed_opportunity_candidate`; 다른 이익 경로는 지연·역행·횡보 후보, 손절 우선은 회피 후보로 기록한다. | **확정 오판률이 아니다.** 실제 bid/수량/청산·자본/AI/최종 guard와 비용 후 paired operating 경제성이 추가로 필요하다. [사례 분류](../../src/engine/scalping/ai_action_outcome_calibration.py). |

따라서 질문의 “일정시간 뒤 가격 상승”은 필요할 수 있는 관측 하나지만 오판의 충분조건이 아니다. 최종 판정은 사전 입력의 상태·위험 fact·돌파 확인·미시 흐름·유동성 임계치를 먼저 적용한다. `BLOCK`에 구조 무효 fact가 있으면 후행 상승만으로 그 구조 규칙을 해제할 수 없다. [기계 core와 최종 분기](../../src/engine/scalping/entry_setup_evidence.py).

## 2. 전 기간 분모

| 모집단 | 날짜 | 행 수 | `BLOCK` / `RECHECK` / `ENTER_NOW` | 비용 포함 목표 우선 / 손절 우선 | `BLOCK/RECHECK` 목표 우선 |
| --- | --- | ---: | ---: | ---: | ---: |
| 원 기계 캡처 | 9/13~9/23 저장 파일 | 23,837 | 평가 전 원천 | 평가 전 원천 | 평가 전 원천 |
| 해시·setup 계약 검증 캡처 | 9/14·15·16·17·21·22·23 | 17,509 | 10,496 / 6,780 / 233 | 후행 미결속 | 후행 미결속 |
| 경로 진단 가능 | 9/14·15·16·21·22·23 | 3,078 | 1,923 / 1,116 / 39 | 898 / 2,180 | 883 / 3,039 (29.1%) |
| 현재 구조·원천 계약까지 통과한 KRX 정규장 | 9/22 222, 9/23 129 | 351 | 107 / 230 / 14 | 229 / 122 | 221 / 337 (65.6%) |

23,837→3,078의 캡처 무효 6,328, 비용 결손 3,475, 경로/비용 결손 10,951 등은 loader의 **서로 중첩될 수 있는 단계별 계수**이며 단순 합산 제외분모가 아니다. 9/17의 검증된 캡처 3,342건도 스캔했으나 이 loader에서 비용·경로가 모두 유효한 machine 사례는 0건이었다. 해당 날짜를 손절·수익 0으로 넣지 않았다. 10분 관측 행이 10개 미만인 사례는 전체 93건, 엄격군 21건이다. 현재 구조 계약을 통과한 351건은 [9/23 장후 보고서](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-23.json)의 `current_structure_eligible_count`와 일치한다. 이전 paired replay는 원천/경로가 검열되어 이 분석의 유효 outcome으로 합치지 않았다. 원래 machine-only 캡처가 시작되기 전 날짜도 기계 판정 정확도 표본으로 소급하지 않았다.

엄격군과 전체 진단군의 목표 선도율 차이는 구조 계약·날짜·source selection의 차이를 포함한다. 9/23 `machine_full_evaluation`의 운영 paired 비교 수는 **0**, operating population은 unbound, full-cost 실제 손익은 null이다. 엄격군 두 날짜만으로 독립 forward holdout이나 정책 정확도/수익 개선을 주장하지 않는다.

### 시장 3구간과 새 유형 후보

**이전 판의 유형 해석을 철회한다.** `setup_family`·`structure_phase`, 가격 tick·유동성 band, 거래소별 scope 및 9/23 연구 트리의 leaf를 종목 유형으로 정의한 표와 결론은 폐기한다. 분석의 고정 시장층은 **PREMARKET / REGULAR / 통합 AFTERMARKET** 세 가지다. 실제 `venue/session`은 비용·원천·주문 경로의 정확한 결속 키로만 보존하며, 시장층 안에서 거래소를 다시 유형으로 나누지 않는다. 구조 phase 등 기존 기계 입력은 연관 진단에 남기되 새 유형의 이름으로 선결정하지 않는다.

| 고정 시장층 | 원래 session의 묶음 | 경로·비용 진단 가능 / 목표 우선 | 9/23 full evaluation 원 모집단 / 현재 구조 적격 |
| --- | --- | ---: | ---: |
| PREMARKET | `PREMARKET_KRX_LIKE`, `NXT_PREMARKET` | 257 / 21 | 255 / 25 |
| REGULAR | `KRX_REGULAR`, `NXT_REGULAR_OVERLAP`, `NXT_REGULAR` | 2,387 / 781 | 2,165 / 351 |
| 통합 AFTERMARKET | `KRX_NXT_AFTERMARKET`, `NXT_AFTERMARKET` | 434 / 96 | 436 / 100 |

첫 숫자는 이 감사의 9/14~23 중 6일 경로 진단군이고, 뒤 숫자는 [9/23 장후 보고서](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-23.json)의 서로 다른 full evaluation 분모다. AFTERMARKET의 436건은 통합 scope 434건과 NXT 단독 2건을 합친 값이며, 적격 100건은 모두 통합 scope다. 기존 [엄격 필드별 TSV](./2026-09-24-machine-judgement-field-association-strict-policy-input.tsv) 351건은 REGULAR의 KRX만을 포함한다. PREMARKET·AFTERMARKET의 엄격 조건부 연관까지 계산한 것처럼 읽지 않는다. 9/28 발행 정책의 승계 여부와 실제 다음 장전 PID 소비도 이 진단과 별개다.

새 유형 요소는 이미 판정 전에 관측된 명확한 fact를 우선 탐색한다. 다음은 **비용 포함 CF 목표 첫 도달/해당 값이 있는 진단 행**이며 실제 매매 정확도나 독립 검증 성과가 아니다. `bars_since_* == 0`은 캡처된 완료 봉의 20분 또는 세션 내 고점/저점이고, 52주 신고가·신저가가 아니다. `day_high 근접`은 수집 필드 `distance_from_day_high_pct >= -0.5`다.

| 후보 fact | PREMARKET | REGULAR | AFTERMARKET | 해석 |
| --- | ---: | ---: | ---: | --- |
| 완료 봉 20분 고점 갱신 / 비갱신 | 7/33 · 9/168 | 147/496 · 479/1,414 | 13/45 · 76/299 | 현재 정책의 구조 입력과 중복될 수 있다. |
| 완료 봉 20분 저점 갱신 / 비갱신 | 0/24 · 16/177 | 45/148 · 581/1,762 | 17/50 · 72/294 | PREMARKET 24건의 0은 CF 관측값이며 정책 효과 0의 증거가 아니다. |
| 당일 고점 0.5% 이내 / 그 밖 | 6/21 · 15/236 | 89/220 · 692/2,167 | 4/38 · 92/396 | 시장층마다 방향이 달라 보이나 날짜·중복·원천 차이가 남아 있다. |

기존 [전수 필드 연관 TSV](./2026-09-24-machine-judgement-field-association-all-diagnostic.tsv)의 주요 사전 수집값도 **각 시장층의 원래 유효 행만**으로 다시 계산했다. 아래 숫자는 `net_target_first`(1) 대 `exact_stop_first`(0)의 Spearman 상관과 유효 짝 수다. 동일 종목의 반복 시도와 날짜·원천 차이를 제거하지 않은 탐색 통계다.

| 판정 전 수집값 | PREMARKET | REGULAR | 통합 AFTERMARKET |
| --- | ---: | ---: | ---: |
| `features.spread_bp` | -.449 (257) | -.459 (2,387) | -.550 (434) |
| `features.fillability_score` | +.055 (257) | +.213 (2,387) | +.503 (434) |
| `features.curr_vs_micro_vwap_bp` | +.048 (257) | -.008 (2,387) | +.003 (434) |
| `features.curr_vs_ma5_bp` | +.096 (257) | -.029 (2,387) | +.024 (434) |
| 완료 봉의 이전 10분 수익률 | +.127 (185) | -.076 (1,975) | -.004 (367) |
| `current.execution_strength` | +.329 (257) | +.057 (2,387) | -.189 (434) |
| `current.buy_ratio` | +.329 (257) | +.084 (2,387) | -.224 (434) |

스프레드의 방향은 세 시장층에서 같지만 이미 판정·체결 가능성 계약과 연결되어 독립적인 상황 유형 증거는 아니다. 체결강도·매수비율의 시장층 간 방향 차이는 층을 합친 단일 기준의 위험을 보여줄 뿐이다. PREMARKET 목표 선도는 21건뿐이므로 이 표만으로 세부 상황 분기를 고정하지 않는다. 운영 paired 0건은 최초 과거자료 기반 정책안 작성의 장애가 아니라 적용 후 실제 수익을 아직 평가할 수 없다는 뜻이다.

API 식별이 더 명확한 후보는 다음과 같이 원천 시각을 구분한다.

- 기존 [`ka10099` 날짜별 자격 ledger](../../src/database/models.py)의 `audit_info`, `stock_state`, `order_warning`은 [기존 producer](../../src/utils/kiwoom_utils.py)가 원문과 source hash를 보존한다. 공식 [`ka10099` 스펙](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)의 `auditInfo`·`state`·`orderWarning`에 대응한다. **동일 거래일의 저장 시각은 20:05**이므로 오전 진입 행에는 연결하지 않았다. 판정 시각 이전의 최신 ledger만 연결했을 때 투자주의·경고·환기 등 `audit_info != 정상` 또는 `order_warning != 0`인 행은 REGULAR 35/109, AFTERMARKET 0/25, PREMARKET 0건이다. 원천이 결속되지 않은 행은 각각 REGULAR 575, AFTERMARKET 10, PREMARKET 19건으로 별도 남겼다. 이 값은 전일 이후 변경된 **당일 경보 상태**가 아니며, `orderWarning` 코드 5의 공식 설명도 명확하지 않아 원문을 임의 재명명하지 않는다.
- 공식 [`ka10016` 신고저가요청 스펙](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)은 신고가/신저가, 고저/종가 기준, 5~250일 기간, 거래소 조건을 요청 입력으로 둔다. 현재 machine 캡처와 연결된 **판정 이전 `ka10016` 응답 영수증은 확인되지 않았다**. 따라서 위 20분 고저점과 공식 신고가를 합치거나 현재 API를 호출해 과거 9/14~23 값을 채울 수 없다. 신규 source-only 관측을 설계한다면 요청 조건·응답 시각·continuation·raw hash·종목별 누락/중복을 보존하고 판정 이전 영수증만 연결해야 한다.

공식 upstream은 2026-09-24에 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`로 확인했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없어 packaged spec과 Postman `ka10016/ka10099`를 대조했다. API 호출·응답 parser·매매 정책은 이번 분석에서 변경하지 않았다. 현재의 단변량 교차율은 상황 분류안 작성에 사용할 수 있지만 판정 임계치의 효과나 실제 수익을 단독으로 확정하지 않는다. 최초 후보는 각 시장층의 과거 사전값·결측률·날짜/종목 분리·비용 포함 CF paired 효과로 평가하고, 운영 paired는 적용 이후의 검증에 사용한다.

#### 52주 신고저가 재조회와 상황 유형 후보 재검토

여기서 **유형은 영구적인 종목 속성이 아니라 진입 시점의 상황 유형**이다. 신고저가도 전일 고저점이 아닌 **직전 250거래일 고저점 대비 진입 시점 돌파**로 정의한 약 52주 대용 지표다. 공식 `ka10016`의 최대 입력 `dt=250`과 비교기간 경계가 정확히 같다는 뜻은 아니다. `ka10016`의 `dt=250`은 비교 기간이지 과거 판정시각 지정값이 아니므로, 지금 그 API를 조회하더라도 얻는 명단을 9/14~23의 판정 당시 명단으로 소급 결속할 수 없다. 대신 기존 `get_daily_ohlcv_ka10081_df`를 날짜별 `base_dt`로 **294개 종목·판정일 조합에 읽기 전용 호출**했다. [재조회 요약·250일 고저점·원천 bar hash](./2026-09-24-machine-judgement-52week-asof-chart-source.tsv)는 281개 조합에서 판정일 **이전** 250거래일을 확보했고, 13개 조합은 단기 상장·과거 이력 결손 등 사유를 단정하지 않은 채 `insufficient_history`로 남겼다. API 오류는 0건이었다. 조회 시각은 과거 판정 뒤이므로 이 결과는 `ka10016`의 당시 영수증이 아니라 **사후 재구성 진단**이다. 현재 스캐너의 `ka10016`은 20일 신고가 상위 최대 60개를 후보 보강에 사용하지만, 그 명단의 부재를 52주 신고가 부정으로 쓰지 않는다.

진입 시점의 `current.price`와 캡처된 **완료 봉만**을 전일 이전 250거래일 고저점과 비교하고 판정일 완성 일봉은 배제했다. 전체 경로 진단 3,078행 중 2,887행이 250일 이력에 연결됐다. 52주 고점 돌파 후보는 REGULAR 13행/4개 종목·날짜(목표 우선 5), AFTERMARKET 16행/2개 종목·날짜(목표 우선 0), PREMARKET 0행이다. 52주 저점 돌파 후보는 세 구간 모두 0행이다. 남은 191행은 `unknown`이며 비돌파로 채우지 않는다. 완료 봉은 최대 최근 20개만 담겨 있어 이전 당일 전 구간의 첫 돌파를 증명하지 못하고, `ka10081` 일봉과 NXT가 섞인 시점의 완전한 통합시장 가격 계약도 같다고 보장하지 않는다. 사후 재조회 일봉의 수정·권리 반영이 당시 수신값과 같았는지도 확인할 수 없다. **6개 종목·날짜의 신고가와 0개의 신저가만으로 상황 유형·임계치를 만들 근거가 없어 이 축의 추가 조회·정책화는 중단한다.**

신고저가 대신 기존 전수 TSV에서 결측이 적고 판정 전인 수치값 99개(`features`·`current`·완료 봉 `structure`)를 REGULAR의 여섯 날짜에 다시 대입했다. 날짜마다 후행 목표 우선과의 순위상관 부호가 같은 것은 6개뿐이며, 그중 `low_rebound_pct`와 `session_low_rebound_pct`는 같은 파생값이다. 남은 중복 제거 후보는 스프레드, 당일 등락률, 장중 가격 범위, 세션 저점 대비 반등폭이다. 당일 등락률의 날짜별 상관은 여섯 날짜 모두 음수(−.098~−.283), 엄격 KRX 351행에서도 −.265다. 첫 3일의 중앙값 **+11.895%**를 탐색용 경계로 고정해 뒤 3일의 REGULAR 621행에 적용하면 낮은 쪽 272/396, 높은 쪽 114/225가 목표 우선이다. 앞 3일에 없던 종목만 보면 187/276 대 91/158이다. 이들은 반복 시도와 source generation이 섞인 **비용 포함 CF 경로**다. 스프레드·날짜별로 묶으면 장중 가격 범위의 음의 방향도 18개 비교 중 12개만 유지된다.

### 과거 데이터로 만드는 최초 진입 상황 정책안

최초 정책안은 **과거의 판정 전 입력과 비용 포함 후행경로만으로 작성**한다. 운영 paired나 실현 손익은 최초 생성의 선행 조건이 아니다. 현재 감사 근거로 작성한 첫 상황 분류안은 다음과 같다. 이는 진입 시점의 상태이며 종목의 영구 속성이 아니다.

| 시장층 | 최초 상황 분류안 | 현재 근거와 처리 |
| --- | --- | --- |
| PREMARKET | 단일 기준 상황 | 목표 우선 21/257건으로 세부 분기를 제안하지 않는다. |
| REGULAR | `current.fluctuation_pct < +11.895%`: 낮은 상승 확장; `>= +11.895%`: 높은 상승 확장; 미관측: 분류 불명 | 경계는 앞 3일 중앙값으로만 정했고 뒤 3일 621행에서 목표 우선 272/396 대 114/225였다. 엄격 원천 계약을 통과한 KRX는 9/22~23의 351행뿐이므로 이 교차율을 곧바로 정책 수익률로 쓰지 않는다. |
| 통합 AFTERMARKET | 단일 기준 상황 | 목표 우선 96/434건이며 이 감사에서는 독립적인 세부 분기를 확정하지 않는다. |

분류안의 `높은 상승 확장`은 관측·평가할 **상황 이름**이며 자동 `BLOCK` 지시가 아니다. 기존 기계 로직은 이미 `current.fluctuation_pct`를 `overextension_runup_pct`(기본 15%)와 결속해 보되, 구조·VWAP·MA5·tape 조건도 함께 요구한다. 따라서 +11.895% 분류 경계를 기존 15% 차단 임계치로 곧바로 대체하거나 단변량 목표 우선율을 손익 개선으로 간주하지 않는다. 현 전략 selector의 분기 입력 8개에는 `fluctuation_pct`가 없으므로 **이 분류안 자체는 아직 실행 가능한 selector 정책이 아니다**. 기존 `overextension_runup_pct` 후보는 현재 전체 모집단 평가기로 역사적 검증할 수 있지만, 분류안별 서로 다른 정책을 시험하려면 기존 selector의 입력·unknown fallback·학습 분모·직접 소비 계약을 먼저 연결해야 한다. 이것은 구현할 수 있는 경로 문제이지 운영 paired 0건 때문에 정책안을 만들 수 없다는 뜻이 아니다.

**최초 생성과 적용의 판정 순서:** (1) 위 분류안을 과거 시점의 원천·비용·경로에서 정의하고, 현재 지원되는 기존 좌표의 후보와 incumbent를 만든다. (2) 동일 기회 전체 모집단에서 날짜순 train/holdout, 서로 겹치지 않는 opportunity, 원천 적격·제외 분모, 기존 `ENTER_NOW` 변화, 비용 포함 후보 대 incumbent의 paired 차이와 tail guard를 대사한다. 이는 **과거 CF paired**이며 운영 paired를 요구하지 않는다. 상황별 별도 좌표는 selector 경로를 연결한 후 같은 역사적 평가를 한다. (3) 기존 발행 검증을 통과한 후보만 다음 거래일 정책으로 발행하고 PREOPEN·실제 PID 소비를 별도로 확인한다. 통과 후보가 없으면 현 초기 정책을 승계한다. (4) 적용 후 자연 발생한 주문·체결·청산·실현 비용/손익의 운영 paired로 실제 효과와 후속 임계치 조정을 평가한다. 현재 문서의 6일 탐색 분모와 엄격 2일 분모만으로 (2)의 통과 또는 새 정책 발행을 주장하지 않는다.

현재 구조·원천·비용 계약을 통과한 전체 과거 행에 대한 **최초 버전의 실제 선택과 후보 대 기준 정책 비교**는 [시장 3구간 초기 정책 판정](./2026-09-24-main-entry-three-market-initial-policy-v1-decision.md)에 기록했다. 그 판정은 상황 라벨을 남기되 유형별 새 행동 규칙은 미선정하고 기존 정책을 유지한다.

후속 사용자 지시의 **승률 단독 목적**으로 다시 선택한 상황 경계와 판정 규칙은 [승률 단독 초기 정책안](./2026-09-24-main-entry-three-market-win-rate-only-initial-policy-v1.md)에 별도로 기록했다. 이 정책안은 비용 중심 판정의 승격 상태나 현재 런타임 정책을 소급 변경하지 않는다.

## 3. 원천 행으로 검산한 사례

두 사례 모두 9/23 KRX 정규장 원래 캡처의 `executable_ask`와 파이프라인의 같은 종목·venue·session 후행 가격 관측을 사용했다. 가격 관측은 pipeline event를 초 단위 OHLC로 집계한 CF 경로이며 실행 가능한 매도호가나 실제 청산가가 아니다.

| 단계 | `096770` BLOCK, 캡처 `79b86fb24108…` | `356680` RECHECK, 캡처 `d7195ad2bcc1…` |
| --- | --- | --- |
| 판정 시점·기준 ask | 09:15:56.068989, 148,600원 | 09:26:48.816234, 19,650원 (`current.price` 19,640원과 구분) |
| 기계 입력 | `setup_state=INVALID`; `hard_blocker:large_sell_print_present`가 `STRUCTURE_INVALIDATED/BLOCKING`. 스프레드 6.73bp < 100bp, fillability 72 > 15, ask/bid 1.872 < 5이지만 구조 무효가 우선. | `setup_state=WAIT_CONFIRMATION`; `trigger_confirmation_missing`, `local_breakout.recheck_required=true`. 스프레드 5.09bp < 100bp, fillability 100 > 15, ask/bid 0.519 < 5여도 확인 부족으로 RECHECK. |
| 왕복 보수 비용 | 매수 수수료 .015% + 매도 수수료 .015% + 세금 .200% + 슬리피지 .03365% = **.26365%** | 같은 수수료·세금 .230% + 슬리피지 .02545% = **.25545%** |
| CF 목표·손절 가격 | 목표 148,600 × (1 + .36365%) = **149,140.38원**; 손절 148,600 × .993 = **147,559.80원** | 목표 19,650 × (1 + .35545%) = **19,719.85원**; 손절 19,650 × .993 = **19,512.45원** |
| 관측 첫 도달 | 09:17:38에 149,200원으로 목표 우선(101.93초). 09:19:03에 147,200원으로 손절 경계도 이후 관측. | 09:26:50에 19,790원으로 목표 우선(1.18초). 09:29:48에 19,420원으로 손절 경계도 이후 관측. |
| label·10분 끝 관측 | `CLEAN_FAST_PROFIT`/`missed_opportunity_candidate`. 09:25:48 관측 149,500원, 기준 대비 +.60565%. | 같은 진단 label. 09:36:25 관측 19,160원, 기준 대비 **-2.49364%**. |

두 건 모두 목표 선도 CF지만 `096770`은 구조 무효 규칙의 사후 수익 기회 검토 대상이고, `356680`은 1초대 목표 관측 뒤 큰 하락까지 있었던 확인 대기 사례다. 고가 도달만으로 +0.10% 실현 손익을 계산하거나 `BLOCK/RECHECK` 임계치를 낮출 수 없다. 특히 두 번째 사례의 10분 경로는 가격 관측 9개뿐이다. 원본 캡처는 [9/23 payload JSONL](../../data/ai_decision_payloads/ai_decision_payloads_2026-09-23.jsonl), 경로 원본은 [9/23 pipeline events](../../data/pipeline_events/pipeline_events_2026-09-23.jsonl.gz), 비용·label은 위 장후 보고서의 `hierarchical_entry_quality.machine_decision_case_table`에서 대사했다.

## 4. 모든 연결 가능 필드의 값·연관값

- [검증된 전체 캡처 17,509건의 판정 연관 TSV](./2026-09-24-machine-judgement-all-verified-capture-action-association.tsv): 9/17을 포함한 7일의 안정된 스칼라/배열 요약/범주형 fact 경로 2,704개, `ENTER_NOW` 연관 계산 가능 1,918개. 후행 label이 없는 행도 판정과의 연관에는 포함하지만 결과 정확도 열은 만들지 않는다. 수치형 `action_*_assoc`는 해당 action indicator와의 **point-biserial Pearson 상관**, 범주형은 **Cramér’s V**다. 해시·setup 계약 검증을 통과한 캡처 분모이며, 별도 source-quality·비용·후행 조건을 통과한 정책 학습 분모는 아니다. 불안정한 배열의 개별 index는 이 표에서 제외하고 아래 경로 진단군의 필드 목록에 값·결측 현황을 남겼다.
- [전체 경로 진단군 9,042필드 TSV](./2026-09-24-machine-judgement-field-association-all-diagnostic.tsv): 후행 목표 선도 연관값 1,430필드. 9/14~9/23의 유효 6일을 모두 포함한다.
- [엄격 정책 입력군 4,868필드 TSV](./2026-09-24-machine-judgement-field-association-strict-policy-input.tsv): 후행 목표 선도 연관값 652필드. 현재 구조 계약의 9/22~23 KRX 정규장 351건이다.

각 행은 캡처 시점 `setup_evidence`, 원래 `exact_payload`, 후행 기준용 `label_context`, 적용 임계치와 판정 결과의 스칼라 필드 경로다. `field_role`은 기계 입력·수집 원천·후행 기준·정책 좌표·판정 출력의 경계를 표시한다. `values`는 수치형의 min/q10/median/q90/max 또는 범주형의 상위 빈도, `n_present`/`missing_pct`는 전체 분모 기준이다. `outcome_target_first_r`은 비용 포함 목표 우선=1, 고정 CF 손절 우선=0과의 연관이다. 수치형은 **Spearman 순위상관**(부호 있음), 범주형은 **Cramér’s V**(0 이상, 방향 없음)이다. `action_enter_r`·`action_block_r`·`action_recheck_r`은 각 판정 indicator와의 연관이다. `nonentry_avoidance_proxy_r`은 `BLOCK/RECHECK`에서 손절 우선=1의 조건부 연관, `entry_target_proxy_r`은 `ENTER_NOW`에서 목표 우선=1의 조건부 연관이다. 이는 실제 체결 정확도 열이 아니며 엄격군 `ENTER_NOW` 14건은 최소 짝 20건 미만이라 연관값이 null이다. `end_return_1m`~`60m`은 수치형이면 각 종가 수익률과의 순위상관, 범주형이면 양/음 수익률과의 V다. 각 horizon과 조건부 진단의 유효 짝 수를 함께 기록했다.

배열의 고정 index는 원천값과 결측률을 남기되 날짜·길이별로 서로 다른 과거 시점을 가리킬 수 있어 연관값을 비웠다. 수치 배열의 길이·최솟값·최댓값·평균·마지막 값, 범주형 fact의 포함 여부는 의미가 고정된 파생 단위로 계산했다. 식별자/시각 143(엄격군 125), 판정 출력 63(47), 전부 결측 36(42), 불안정 배열 위치 6,763(3,362)는 예측 연관값에서 제외했다. 값이 있지만 상수·표본 20 미만·범주 30개 초과 등으로 계산하지 못한 항목도 null과 `association_status`를 남겼다. cache token류 값은 배포 TSV에서 가렸다.

| 필드·해석 범위 | 전체 3,078건 목표 선도 연관 | 엄격 351건 목표 선도 연관 | 엄격군 `ENTER_NOW` 연관 |
| --- | ---: | ---: | ---: |
| `payload.features.spread_bp` (수집 원천, 유동성 입력으로 전달) | -.503 | -.137 | +.064 |
| `payload.features.fillability_score` (수집 원천, 유동성 입력으로 전달) | +.237 | +.114 | -.036 |
| `payload.features.curr_vs_micro_vwap_bp` (수집 원천) | +.009 | **-.339** | +.199 |
| `payload.features.curr_vs_ma5_bp` (수집 원천) | -.003 | **-.307** | +.200 |
| `payload.entry_candle_context.structure.returns_pct.10` (수집 원천) | -.023 (n=2,527) | **-.365** (n=327) | +.190 |
| `payload.current.execution_strength` (수집 원천) | +.044 | +.014 | +.094 |
| `setup.setup_state` (범주형 V, 판정 입력) | .162 | .186 | .532 |

엄격군의 `curr_vs_micro_vwap_bp` 상관은 9/22 -.252, 9/23 -.466; `curr_vs_ma5_bp`는 -.224/-.438; 과거 10분 수익률은 -.391/-.347이었다. 다만 두 날짜·반복 시도·같은 종목·정책/원천 세대의 결합 효과를 제거한 인과 추정이 아니다. `curr_vs_micro_vwap_bp`와 10분 **종가** 수익률의 엄격군 상관은 각각 -.006, 과거 10분 수익률은 -.097로, 목표 **첫 도달**과 창 끝 수익률도 다른 질문이다. 이 수치를 기준으로 임계치 변경 또는 신규 변수 채택을 승인할 수 없다.

최종 기계 core·전략 selector·setup builder의 직접 읽기 목록에 없는 수집 필드도 버리지 않고 계산했다. 예를 들어 `payload.current.execution_strength`의 목표 선도 순위상관은 전체 +.044/엄격군 +.014(엄격군 중앙값 103.38), `payload.current.buy_ratio`는 +.048/+.083(중앙값 50.83)이다. 후행 label과 무관하게 검증 캡처 17,509건 전체에서 두 필드의 `ENTER_NOW`와의 Pearson 상관은 각각 +.090, +.049다. `execution_strength`는 별도 reversal 관측 문맥에서 사용되지만 이 기계 판정 입력으로 직접 읽히지 않는다. 이 둘의 작은 단변량 연관을 “무효한 데이터”나 “추가하면 이익”으로 해석할 수 없다. 다른 수집 필드의 upstream 간접 사용 여부도 별도 함수 경로까지 확인해야 한다.

특히 `watch_age_sec`는 수집 원천 `payload.entry_timing_context.watch_age_sec`에 엄격군 351건 모두 있으나, `setup.entry_timing_observation_v1.watch_age_sec` 및 선택기의 `setup.strategy_selection.features.watch_age_sec`에는 **351건 모두 null**이다. 예시 캡처는 원천 promotion age 514.1251초를 보유하지만 `first_watch_price_time_not_bound`/`promotion_is_not_first_watch_evidence` 때문에 첫 관측 기반 watch age를 기계 입력으로 승격하지 않는다. 9/23 `machine_policy` 연구 artifact의 KRX root split은 fillability와 price이며 watch age split은 없다. 이 연구 artifact를 실제 runtime 소비 정책으로 간주하지 않는다. 결손값을 임의 보간해 상관이나 정책 후보로 사용하지 않는다.

### `결손`·`null`·`0`의 처분

이 표기들은 **일괄 수리 목록이 아니다**. 필드별 필수성·생산 계약·해당 scope의 자연 발생 여부·실제 소비 위치로 나눠야 한다.

| 관측 상태 | 처분과 종결 조건 |
| --- | --- |
| 필수 원천/receipt/identity/비용·후행 경로의 계약 불일치 | 해당 행·날짜를 격리하고 producer→consumer 원천 계약을 추적한다. 9/17의 유효 경로 0, full evaluation의 `source_contract_invalid` 등은 결손 원인을 조사할 대상이다. 동일 원천으로 재검증해 회복 가능성을 확인하되, 회복 불가 과거값을 0으로 채우지 않는다. |
| 운영 paired 0·operating EV/순익 `null` | 실제 실행·종료·bid·비용·자본의 동일 기회 결속이 없어 **적용 후 실현 경제성 판정이 열리지 않은 상태**다. 과거 CF로 최초 정책안을 생성하는 데 이 값이 필요하지는 않다. 결속 producer/consumer와 다음 자연 영수증의 closure test는 후속 운영 검증용이다. 계산 오류라고 단정하거나 EV=0으로 쓰지 않는다. |
| 선택 기능에 입력될 수 있지만 의미상 관측 불가 | 첫 watch age는 promotion age와 다른 계약이므로 현재 null이 맞다. 향후 실제 first-watch 시각·가격을 신뢰 가능하게 생산할 때만 새 분기 후보로 평가한다. 다른 100% null 문맥 필드도 필수 계약인지, 정상 시 기록되지 않는 `missing_reason`·broker 식별자인지 개별 확인한다. |
| 연관 통계 `null` | `no_observed_value`, 상수, 짝 수 20 미만, 식별자/시각, 고유 범주 과다, 위치 의미가 변하는 배열 index 등은 통계가 정의되지 않거나 비교 부적합하다는 뜻이다. 원천값은 남기고 상태·분모를 표기한다. 무조건 producer 수리나 상관 0으로 처리하지 않는다. |
| 후보/승격/변경 0 또는 scope 표본 0 | 승격문턱 미충족에 따른 incumbent carry, 지원 범위·자연 후보 부재, 혹은 source gap을 각각 구분한다. 정책 후보 0은 경제적 효과 0이 아니다. scope에 원천이 기대됐는데 수집이 누락된 경우에만 owner 계약을 연다. |
| 관측 수치값 `0` | 0이 유효한 단위값인지 원천·단위·기준시각으로 확인한다. 유효 0은 그대로 쓰고, 미관측의 대체 0은 격리한다. |

엄격 TSV의 `no_observed_value` 42개 경로에는 broker/청산 식별자와 선택적 `missing_reason`, 미결속 market·sector 상대값, first-watch 값이 함께 있다. 그 42개를 모두 같은 결함으로 세지 않는다. 9/17의 0건, 9/23의 운영 paired 0, `ENTER_NOW` 14건으로 인한 조건부 상관 null도 서로 다른 원인이다.

**이번 원천 수리 판정:** 9/23의 [compact 운영 projection](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-23.source.json)은 74행 전부 제외됐다. `terminal_path_not_evaluable` 55, `exact_stop_distance_missing_or_invalid` 12, 자연 AI 응답 semantic/transport 결손 5/2다. 원래 [outcome label](../../data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-09-23.json)의 compact attempt identity는 74행 모두 연결되지만, 10분 완전 terminal 경로 또는 원래 stop 거리가 없는 행을 실현 비용·손절 0으로 복원할 수 없다. 현재 producer는 이들을 `source_gap`/exclusion으로 남기며, 다른 기계 경로 행을 동일 attempt인 양 대체할 수도 없다. 과거 원천의 소급 수리 대신 다음 자연 판정에서 원래 시각의 stop·비용·완전 후행경로를 생산·결속하는 owner 수용이 필요하다. `source_contract_invalid`는 유효 행을 오염시키지 않도록 이미 행별 격리한다. 즉시 고칠 수 있는 결함은 **stage 성공만 보던 의미 감시의 누락**으로 확인했다.

[기존 `artifact_freshness` 감시기](../../src/engine/error_detectors/artifact_freshness.py)에 정확 원천일 보고서의 hash·scope별 구조 적격/운영 paired·source-contract 제외와 compact projection의 전량 제외를 읽기 전용 `warning`으로 기록하는 검사를 추가했다. 현 9/23 원천에 적용하면 `machine_operating_paired_unbound`, `machine_operating_economics_incomplete`, `machine_source_contract_exclusions`, `machine_current_structure_empty`, `compact_operating_rows_all_excluded`가 탐지된다. 제외 계수는 full population과 분모가 달라 더하지 않는다. 이 감시기 코드의 작업본 검증은 **설치된 장후 unit/release나 기존 영수증이 새 코드를 소비했다는 증거가 아니다**. 새 자연일 원천 복구와 배포·PID 소비는 별도로 확인해야 한다.

9/23 원천일로 전체 detector를 읽기 전용 호출해도 위 `machine_result_semantics.status=warning`이 세부 결과에 전달된다. 호출 전체의 `severity=fail`은 이 수리와 별개인 historical bootstrap의 명시적 `POSTCLOSE_PREPARED_EFFECTIVE_DATE` 환경값 부재 때문이다. 선택된 runtime release의 감시기 파일 hash는 현 작업본과 달라 기존 9/23 terminal에 새 경고가 있었다고 소급 주장하지 않는다.

## 5. 판정과 정책에 대한 결론

1. 지금 얻은 정확도 대용치는 **왕복 예상 비용을 반영한 첫 경계 도달 CF**다. 실제 bid 체결, 전량/부분 수량, stop/exit, 동시 자본, AI·최종 guard를 동일 기회에 결속한 운영 비교가 0건이므로 진짜 `BLOCK/RECHECK` 오판률·비용 후 EV·정책 개선량은 **null**이다.
2. **같은 main 기계 캡처에 결속된** 수집 원천의 계산 가능 스칼라 값은 TSV에 포함했다. `payload` 필드는 최종 판정 함수가 직접 참조하지 않는 항목까지 포함하지만 일부는 upstream `build_entry_setup_evidence`나 전략 selector의 입력일 수 있다. 따라서 이 표의 `payload`를 전부 “미사용”이라고 단정하지 않는다. 실제 직접 사용 여부는 producer→setup→selector→core 경로별로 추적하고, 현재 판정 입력과 수집 원천의 연관값을 함께 비교해야 한다. 별도 owner인 widget/episode/holding-exit 및 정확한 broker fill·청산은 같은 기계 시점의 predecision 값으로 결속되지 않아 이 TSV의 상관 분모에 넣지 않았다. 이들의 미산출 연관값은 0이 아니다.
3. **최초 정책안 생성·후보 선별은 과거 데이터로 진행한다.** 판정 당시의 as-of 원천·비용·후행경로를 같은 기회에 묶고, source-valid 전체 모집단을 시간순 train/holdout으로 분리해 기존 정책과 비용 포함 CF paired 효과·tail을 비교한다. 날짜·종목/episode 중복과 원천 결손을 분리하고 source gap과 100% null 필드를 0으로 치환하지 않는다. 운영 paired 0건을 이 단계의 탈락 사유로 쓰지 않는다.
4. **모든 필드의 값·연관값은 최초 상황 분류안의 후보 지도**다. 시장층을 PREMARKET/REGULAR/통합 AFTERMARKET으로 고정하고, 판정 전에 확인된 수치·fact만 사용한다. 이 감사에서 52주 신고저가는 근거 부족으로 제외했고, REGULAR의 상승 확장 분류안은 §2에 명시했다. 유효한 과거 as-of 영수증이 없는 값은 `unknown`으로 두며 정상/비해당으로 간주하지 않는다. 과거 비용 포함 CF에서 반복성과 후보 대 incumbent 효과가 확인되면 기존 발행 검증으로 넘긴다. 후행 outcome·판정 출력·식별자·결손 보간값은 사전 분류나 판정 입력이 될 수 없다. **실제 운영 paired는 발행·소비 뒤의 효과 측정과 추가 조정 근거**다.

이 감사의 통계량은 관측적 탐색 결과다. 여러 필드를 동시에 훑었으므로 큰 절댓값 자체를 유의성, 인과, 수익성으로 읽지 않는다.
