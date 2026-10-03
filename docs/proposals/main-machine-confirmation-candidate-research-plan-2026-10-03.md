# 기계 정책 확인 조건 후보 후속 연구 — 2026-10-03

## 범위와 판정 기준

- 실행 소유자: 오늘 checklist의 `MachineConfirmationCandidateResearch1003`.
- 9/29~10/2 보유 원천의 native 99시도, 학습 59기회·후단 10기회를 그대로 사용한다. 7,069개 관측에 native ID를 합성하지 않는다.
- 순위는 현재 `machine_admission_rank`의 비용 결합 target-first 승률·지원수·기존 성공 보존이다. 고정 horizon CF 평균이 음수라는 이유만으로 기계 후보를 탈락시키지 않는다. 경로 EV와 최악 손실도 별도 기록한다.
- 후단 날짜는 이미 여러 연구에서 사용했다. 이번 학습 내 선택의 누수 방지와 새 독립 검증의 부재를 모두 명시한다.
- 새 원천 수집, provider/broker 호출, live 정책 발행, 배포, 재기동은 수행하지 않는다.

## 선행 발견과 가설

기존 전략 v2 임계값 탐색에서 회수0이었지만 실제 코드에는 `group_trigger`로 trigger/volume 확인 부족을 해소하는 유형별 경로가 있다. 현재 validator는 strategy와 legacy hierarchy 동시 사용을 금지한다. 따라서 현재 등록된 VWAP veto 후보와 **미등록 확인 경로 결합 후보**를 분리한다. 후자는 기존 커널을 재사용한 오프라인 가설이며 운영 정책으로 발행할 수 없다.

1. **C1 등록 경로 재확인:** 동일 native 원천으로 현재 winrate 보고서 생성 함수를 호출해 실제 학습 분모·후보·승격 장애를 확인한다. canonical 경로에는 쓰지 않는다.
2. **C2 의미 확인 결합:** parent strategy로 원천을 재생한 뒤 기존 hierarchy group-trigger 커널을 제한적으로 적용한다. parent `RECHECK` 중 micro-price/trigger 확인 대기만 대상이다. parent BLOCK, ENTER, local breakout 대기는 그대로 둔다. 현재 가격 반응·순매수·유동성 및 다른 모든 risk disposition을 그대로 검사하며 VWAP veto도 재적용한다.
3. **C3 유형 분기:** 학습의 관측된 flow family와 phase/liquidity/volatility 단일·2축 조합으로만 정의한다. UNKNOWN은 분기에 사용하지 않는다. 양의 outcome을 보고 조건을 생성하지 않는다. 최저 micro 임계값은 parent 값보다 완화하지 않는다.
4. **C4 선택·진단:** 후보 정의·원천·커널 SHA를 계산 전 봉인한다. 학습에서 회수 성공이 있는 후보를 현재 recovery 순위로 한 개 고정하고 후단 성능·실제 gate 오류를 계산한다. 후단 성능으로 다른 후보를 재선정하지 않는다. 종목 하나 제외 재선정과 9/29→9/30 순차 진단을 덧붙인다.
5. **C5 한계 분리:** 비용·원천 결손, action 변화0, 성공 보존, 지원수 미달, schema/커널 미등록, 독립 후단 재사용을 별도 보고한다. 기존 커널 결합으로 판단이 바뀌어도 주문 가능성·실현 수익은 입증하지 않는다.

## 구현 위치·완료 조건

- `src/engine/scalping/entry_policy_confirmation_research.py`: 기존 연구 모듈과 같은 오프라인 소유권. live import/caller 추가 금지. 출력은 workspace `tmp` 아래 새 디렉터리만 허용한다.
- `src/tests/test_entry_policy_confirmation_research.py`: parent guard 유지, 잘못된 micro/source, train-only 정의/선택, 출력 경계 검증.
- 후보 JSON/행동 변경 증거/학습·후단 metrics/등록 gate/시간·RSS 및 source hash를 `tmp/machine-confirmation-candidate-research-20261003`에 저장한다.
- 구현→자체리뷰→수정→재리뷰→표적 pytest/compile/diff→실제 격리 계산→audit→문서 parser 순서로 닫는다. 기존 작업본과 541개 정책 파일 hash를 보존한다.
- 보조 AI는 별도 [생산자·소비자 개선 계획](auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md)만 작성한다. 자연 수용 소유자는 10/6 checklist에 남긴다.

## C6. 1차 결과에 따른 사후 탐색 확장

`run-01`의102개 유형 결합은 모두 행동 변화0이었다. 추가 사실 추적에서 양의 micro 가격·매수 흐름이 있어도 `liquidity_adverse`, `micro_continuation_unconfirmed`, `no_supported_setup`이 남았다. 첫 결과와 코드를 별도로 보존하고 아래 한 가지 의미 가설만 추가한다.

- 기존 group-trigger 허용 fact인 trigger/volume 확인 부족에 더해, `micro_continuation_unconfirmed`와 `no_supported_setup`을 **관측된 flow family + 현재의 유효한 양의 micro 가격/매수 흐름**으로 대신 확인하는 미등록 가설을 비교한다. 원래 fact를 삭제하거나 READY로 위조하지 않고 연구 판정에 대체 근거와 원래 risk 목록을 함께 남긴다.
- core BLOCK, local breakout 대기, liquidity 위험과 임계값, source guard, parent micro recipe, VWAP veto는 유지한다. numeric threshold를 완화하지 않는다.
- 가설 정의는 추가 실행 전에 봉인하지만, 이미 본 데이터로 연구 방향을 정했으므로 사후 탐색이다. 10/2 결과도 반복 사용되며 독립 승격 근거가 아니다.
- 등록 커널이 아닌 자체 확인 규칙이 포함된 점을 후보 schema·review evidence에 명시한다. 후보가 수치상 좋아도 정식 validator 오류를 우회하지 않는다.
