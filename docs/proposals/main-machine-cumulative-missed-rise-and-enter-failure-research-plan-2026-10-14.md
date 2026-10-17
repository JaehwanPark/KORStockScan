# Main 누적 놓친 상승·ENTER_NOW 실패 감소 연구 — 2026-10-14

## 요청과 범위

사용자 요청: 누적 원천으로 놓친 상승의 추가 포착과 기존 ENTER_NOW의 실패 감소를 명시적으로 함께 연구한다.
수동 연구 owner는 이 문서이며 기존 [10/13 연구](main-machine-missed-rise-and-enter-failure-joint-research-plan-2026-10-13.md)를 이어간다. 장후 자동 탐색·정책 등록·배포 실행 항목은 새로 만들지 않는다. 운영 인계는 [현재 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 기존 family owner를 유지한다.

## 기준 고정

- 완료된 원천 날짜: 2026-09-29~2026-10-13의 보유 8개 영업일. 진행 중인 10/14는 제외한다.
- 시장: PRE=`NXT/_NX`, REGULAR·AFTER=`SOR/_AL`. 삼성, 네 상시감시 종목, 일반 비삼성 가격 유형을 모두 유지한다.
- 기준 정책: 10/14 적용 포인터 `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`. 이전 연구의 P1 두 범위가 반영되어 있으므로 이전 기준 정책의 개선 숫자를 재사용하지 않는다.
- 실행 코드: 선택 릴리스 `main-io-residual-20261014-ff32b99b3`의 native detector와 label consumer를 해시로 고정한다. 선택 파일의 기록은 이번 연구의 PID 재확인 증거가 아니다.
- 10/12까지 21개 정규화 partition을 검증하고, 10/13의 기존 raw를 기존 source consumer로 격리 정규화한다. 품질 검증 불가 epoch는 제외하고 경로 단절을 보존한다.

## 세 가지 비교

| 축 | 평가 방식 | 함께 표시할 손익 교환 |
|---|---|---|
| A 추가 포착 | 현 정책 OR 수동 고정 A01~A09 | 추가 성공·손절·시간초과·미확정 |
| F 실패 감소 | 기존 확인 시점에 F01~F16 조건 적용 | 제거 실패, 함께 제거된 성공, 유지 성공, 미확정 |
| J 결합 | 정제된 기존 정책 OR 추가 패턴의 실제 확인점 합집합 | 다른 branch가 되살린 실패, 중복 제거, 최종 승률·성공 수 |

- 지난 연구의 고정 25개 가설을 재사용한다. 새 수치 그리드나 자동 패턴 생성은 하지 않는다.
- 10/8까지의 6일로 선택했던 방식은 비교용으로 남긴다. 주 결과는 고정 25가설을 전체 누적 기준으로 순위화하고, 10/12·10/13 및 날짜 하나씩 제외한 결과를 진단으로 표시한다. 이는 동일 데이터 내 탐색 결과이며 독립 성능 입증으로 부르지 않는다. 새 날짜 통과를 별도 수용 조건으로 만들지 않는다.
- 누적 비용 기준 승률이 비교 기준이다. 성공 100%·80% 보존, 최소 표본/날짜, EV 또는 추가 holdout을 탈락 gate로 도입하지 않는다. 높은 승률 후보와 성공 기회를 더 유지하는 후보를 같이 제시한다.
- branch 정제에서 해당 branch가 탈락해도 같은 확인점의 다른 branch가 허용하면 신호를 유지한다. 추가 조건 UNKNOWN은 정제에서 기존 신호 유지, 신규 패턴에서는 매칭 미성립이다.
- 운영 적용을 검토할 때 A는 별도 탐지 branch 추가, F는 지정 기존 branch의 확인 조건 교체로 구분한다. 좁은 F branch를 기존 branch 옆에 OR 추가하기만 하면 기존 실패가 계속 통과한다. 이미 정제된 branch를 다시 보완할 때는 현재 registry의 합성 지원 범위와 원 정의 lineage를 확인해야 한다.

## 라벨과 실판정 경계

- 확인 시점 실제 ask, 비용률 0.0023, 30분 이내 비용 후 +0.4% 선도달=`WIN`, -3% 선도달=`FAIL_STOP`, 충분한 30분 경로에서 둘 다 미도달=`FAIL_TIMEOUT`.
- 10분 이후를 포함하는 동일 item의 보유 완료 분봉을 기존 라벨 계약으로 보조한다. 가격·시간·원천 결손은 `UNRESOLVED`이며 실패 또는 0원으로 바꾸지 않는다.
- 현재 정책을 과거 가격에 재생한 확인점은 counterfactual 신호이다. 실제 과거 ENTER_NOW 발행 건수·주문·체결·실현 수익으로 부르지 않는다.
- 실제 장중 판정은 별도 원 trace를 중복 제거하고, 원 확인 시점·item·native namespace가 검증되는 경우만 후속 경로와 연결한다. 결손은 원인별 미연결로 남긴다.
- 반복 확인점은 독립 매매 표본이 아니다. 동일 목표 도달 시계 수와 날짜별 집중도를 함께 공개한다.
- `FAIL_TIMEOUT`은 목표 미달이며 하락 또는 실현손실과 동의어가 아니다. 연결된 실제 판정의 완전한 틱 경로는 30분 말미 체결가의 비용 차감 평가값도 나눠 표시한다. 이 값 역시 실제 체결·실현손익은 아니다.

## 실행·검증·종료

1. `tmp/main-machine-joint-research-20261014/`에 도구·원천 manifest·기준 정책·결과를 격리한다. 새 Python은 offline 연구 소유이며 운영 package를 변경하지 않는다.
2. 단일 저우선순위 프로세스, partition당 메모리 2GiB·CPU 480초·wall 600초로 순차 처리한다. API/provider/주문 요청은 0이다.
3. 코드와 원천 SHA, exact item/epoch/sequence/ask 연결, 라벨 선형 oracle, future suffix 불변성, UNKNOWN·OR 재허용 회귀를 검사한다. 체크포인트는 manifest·output 해시 일치 때만 재사용한다.
4. A/F/J 누적 결과, 날짜별 반전, 기존 정책에 이미 반영된 부분, 추가 구현 필요사항을 한국어 감사 문서에 기록한다.
5. 24개 partition 완료 또는 원천/자원 결손을 명시한 부분 결과로 종료한다. 표본 부족을 전체 가설 소진으로 표현하지 않는다. 운영 적용 여부는 연구 결과와 별도이다.

문서 변경 후 print-only parser를 실행한다. 외부 동기화는 사용자가 다음 표준 명령으로 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 실행 완료 기록

24개 partition·526만 행의 원천 검증과 누적 A/F/J 비교를 완료했다. 원천 결손·실제 캡처 대조와 돌파 knownness 결함 보완을 포함한 최종 결과는 [10/14 연구 결과](../audits/main-machine-cumulative-missed-rise-and-enter-failure-research-review-2026-10-14.md)에 기록했다. 최종 비교는 `tmp/main-machine-joint-research-20261014/corrected/cumulative-result.json`을 사용한다.
