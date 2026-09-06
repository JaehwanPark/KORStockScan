# Scalping ADM/LDM 정리 및 최종 리뷰

기준: 2026-09-06 KST. 사용자 지시: 권장 정리범위 실행, 코드리뷰·수정보완 반복, 장후작업 상세검토 목록 최신화.

## 1. 판정과 범위

Scalping ADM/LDM의 정책·프롬프트·장후 생성·PREOPEN 승격 경로를 폐기한다. 환경변수를 OFF로 바꾸는 것에 그치지 않고, 보관 산출물이나 상속 환경변수로 재활성화되는 경로를 차단했다. 최종 검증 결과는 §4에 기록한다.

| 구분 | 처리 | 유지되는 경계 |
| --- | --- | --- |
| Entry ADM / Holding·Exit ADM | prompt 주입·행동 bias·scale-in bias 무효화 | 원천 event identity와 기존 진입·보유·청산 판단 |
| Statistical action weight | daily embedded 생성·저장 제거 | 실제 완료 거래 EV와 전용 전략 검증 |
| LDM daily / rolling5d / rolling10d / MTD | producer·정책 권한 폐기 | candidate→submit→fill→terminal 원장 |
| Lifecycle AI context / attribution | 생성·주입·PREOPEN 자동 ON 제거 | Main AI의 독립 prompt/context 개선 경로 |
| Bucket discovery / parent refinement | daily·누적 실행 및 복구 workorder 제거 | 독립 source-quality 감사·원천자료 수집 |
| Runtime apply bridge / Greenfield | 후보 소비와 직접 env 활성화 차단 | 기존 전용 family 승인·broker/hard-safety |
| LDM sim scale-in approval | LDM 유래 승인과 fallback 소비 폐기 | sim의 다른 독립 기능·기존 operator 정책 |
| Scale-in incremental CF | LDM 전용 독립 실행만 제거 | AVG_DOWN의 증분 CF 및 frozen full-policy replay helper |
| Entry AI gate / intraday context probe | ADM 보고서 대신 원천 event 정규화 사용 | 실제 청산과 counterfactual 분리·정확한 ID 조인 |
| 일반 sim catalog / key lineage / conversion / gap audit | 폐기 source·seed·가설 제외 | rising-missed 독립 prior와 비폐기 원장·감사 |

신규 파일의 owner는 `src/engine/lifecycle/retirement.py`(공통 폐기 계약), `src/engine/scalping/entry_observation_source.py`(전용 진입 분석의 원천 정규화)다. `src/engine` root에 새 모듈을 추가하지 않았다. 기존 모듈의 공용 정규화·안전 보조함수는 보존했고, 공개 생성 진입점은 `retired`로 종결한다. 보관 raw/report/analytics는 삭제하지 않았다.

## 2. 리뷰에서 발견하고 보완한 사항

| 발견 사항 | 보완 및 검증 관점 |
| --- | --- |
| 이전 env·operator 설정으로 advisory 재활성화 가능 | constants 최종 OFF와 무권한 runtime adapter, PREOPEN writer의 폐기 namespace 제거·OFF 기록 |
| Greenfield가 constants 밖에서 env를 직접 읽음 | 활성 판정·평가·Telegram 경로를 무권한 no-op으로 고정; 파일 읽기 금지 반례 |
| 보관 bucket 승인·가설이 일반 sim catalog로 유입 | producer·PREOPEN·runtime catalog loader에서 제외; 비폐기 policy에 귀속된 seed만 유지 |
| 매트릭스 누락이 verifier/gap audit의 영구 FAIL·재생성 요청이 됨 | 필수 산출물·handoff·freshness 목록에서 제외; 폐기는 복구용 partial-profile OFF가 아님 |
| 폐기 OFF 값만으로 새 튜닝 후보가 ready로 표시됨 | OFF 안전값을 `runtime_change` 후보 판정에서 제외 |
| 검증기가 폐기 env ON을 내부 OFF 값으로 덮어 정상으로 보일 수 있음 | 원본 runtime manifest와 명시 PID의 ON을 finding으로 검출; 소비자 방어와 감사 판정을 분리 |
| Entry AI gate / probe가 삭제되는 보고서에 의존 | 원천 event helper로 전환; 실제 청산 outcome 별도 조인; 날짜별 raw scan을 real/CF 경로가 공유 |
| AVG_DOWN snapshot이 사용하지 않는 matrix 파일을 계속 수집 | 폐기 env/file/selector 제외; 현재 전용 정책·구현 fingerprint·캐시 무효화 입력 유지 |
| submit-drought 종결이 LDM의 중복 quote attribution을 요구 | Sentinel 원본 quote-refresh·unknown-root-cause·일관성 검증을 사용; 다른 handoff 검증 유지 |
| scalping 폐기 필터가 Swing 동명 경로에 전파될 위험 | namespace 경계를 분리하고 Swing/source-quality/독립 prior 회귀 유지 |

폐기 기능의 과거 승격·보고서 생성을 기대하던 테스트는 보관 입력을 주어도 재활성화되지 않는 계약으로 수정했다. 일반 표본 분리·AI 오류·승인 차단·안전 테스트는 비폐기 source fixture로 유지했다. 실패를 숨기는 skip/xfail은 추가하지 않았다.

## 3. 실제 원천자료 읽기 검증

2026-09-04 자료를 읽기 전용으로 확인했다. 매트릭스 보고서 생성, runtime apply, broker 호출 없이 확인한 결과다.

| 항목 | 결과 | 해석 |
| --- | ---: | --- |
| 정규화 관측 row | 538 | 매트릭스 보고서 없이 원천자료 확보 가능 |
| record_id 보유 row | 534 | 나머지 4행의 식별자를 임의 생성해 실거래에 붙이지 않음 |
| 유효 실제 청산 outcome | 1 | sim/미완료 손익을 실현 EV로 대체하지 않음 |
| 서로 다른 record_id의 정확한 조인 | 1 | 보완된 원천→실제 결과 연결 확인 |

이는 source 연결 검증이지 EV 개선이나 매수 확대 근거가 아니다. 폐기로 반복 생성·주입 비용을 줄이는 것은 구현상 확인했지만, 실제 장후 전체 소요시간 단축과 순이익 증가는 아직 측정하지 않았다. 새 코드의 full-policy fingerprint가 반영된 AVG_DOWN 자연 frame도 다음 거래일에 확인해야 한다.

## 4. 검증 결과

- 최종 통합 회귀: **3,036 passed**, 87.08초. 폐기 계약·producer/consumer·PREOPEN·검증기·원천품질·Samsung·AVG_DOWN·PYRAMID·panic·AI audit 및 기존 병행 recheck 변경의 관련 테스트를 포함한다. 전체 저장소의 모든 테스트를 실행한 것은 아니다.
- Python 문법/compile, Ruff, Black, wrapper Bash syntax, `git diff --check`: PASS.
- 체크리스트 parser: PASS, `AdmLdmRetirementNaturalEvidence0907` 파싱 확인. Project/Calendar sync는 실행하지 않았다.
- expensive report 재생성·전체 장후 체인 실행·bot 재기동·실거래는 하지 않았다.

판정: implementation → review → 보완 → 재리뷰 → targeted validation 반복을 종결했다. 현재 검토·검증한 변경 범위의 미해결 finding은 0건이다. 다음 자연 실행의 성과·실제 PID 소비는 아직 검증되지 않은 운영 확인이며 코드 PASS로 대체하지 않는다.

## 5. 운영 반영과 다음 확인

이번 변경은 코드·wrapper·문서 반영이다. 기존 다음-session env를 수동 재생성하지 않았고, 이미 기동된 PID에 적용됐다고 간주하지 않는다. 정상 PREOPEN 생성과 다음 정상 기동에서 폐기 계약을 소비한다. source 누락으로 기존 writer가 실행되지 않는 상황에서도 새 코드의 constants/no-op 방어는 유지되지만, 과거 ON env 파일을 정상 생성된 OFF 파일로 해석하지 않는다.

자연 확인 owner는 [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)의 `AdmLdmRetirementNaturalEvidence0907`이다. PREOPEN OFF·PID 무주입·폐기 산출물 누락 FAIL 없음·전용 분석 handoff를 확인한다. Institutional flow context의 독립 소비 실효성은 별도 후속 검토 대상이며 이번에 임의 삭제하지 않았다.

기존 작업의 dirty 변경은 보존했다. 특히 다른 작업의 recheck/lock 수정과 이번 ADM/LDM 정리를 혼동하지 않는다. 18개 operator lock 일괄해제·삭제, bot/provider/수량/cap 변경, broker·hard/protect/emergency guard 완화는 수행하지 않았다. 폐기된 정책을 재도입하려면 단순 env 전환이 아니라 별도 사용자 지시·새 owner/근거/롤백 계약이 필요하다.
