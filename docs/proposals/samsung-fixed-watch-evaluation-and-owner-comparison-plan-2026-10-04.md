# 삼성전자 고정감시 평가·Main/Widget 대조 실행계획

## 1. 목적과 범위

사용자의 `진행하고 검증하라` 지시에 따라 고정감시 평가 단위 설계, 기존 Main/Widget 진입·종료·비용 대조, 선정 후보 고정 및 이후 날짜 재생 준비를 수행한다. 위치는 기존 오프라인 연구 패키지 `src/engine/scalping`, 회귀는 `src/tests`다. 실정책 publisher/loader, 감시·주문·provider/API·수집·배포·재기동은 변경하지 않는다.

선행 근거는 [환경·수급 연구](../audits/samsung-environment-conditioned-pattern-research-review-2026-10-04.md), [기회 대사](../audits/samsung-opportunity-contract-reconciliation-review-2026-10-04.md), [기존 종료 연구](../audits/samsung-policy-episode-replay-research-review-2026-10-04.md)다. 이 자료·코드·manifest를 수정하지 않고 hash를 검증한다. 일반 시간 종료/고정폭 trailing 탐색은 반복하지 않는다.

## 2. 평가 단위 계약

1. 관측, 원래 native 기회, 가격 연구 episode, 실제 보유 episode를 별도 분모로 유지한다. `005930/KRX/KRX_REGULAR/MAIN_FIXED_WATCH` 원native가 있는 행만 전용 모집단이다. 다른 origin의 삼성전자 학습 후보는 전용 후보로 재표시하지 않는다.
2. 가격 episode에는 최초로 관측한 원watch identity·epoch와 신호/종료 시간을 붙인다. 원watch 확인 전 신호와 불일치 epoch는 연결하지 않는다. 가격 episode ID는 native identity를 대체하지 않는다. 종료가 검열되면 이후 진입을 보유중으로 보류한다.
3. 날짜 전체와 같은 admission은 하나의 fold에 둔다. episode 승률과 날짜별 승률 평균을 함께 표시한다. 원native 수와 날짜 수를 독립 지원수로 보고하며 tick/반복 신호 수를 독립 지원수로 올리지 않는다. episode Wilson 값은 상관 미조정 진단값이며 운영 신뢰구간으로 사용하지 않는다. 하루마다 재설정하는 CF와 실제 overnight/flat 상태도 구분한다.
4. 원target/stop binary는 원래 비용·label 계약 그대로, 가격 CF는 ask 진입/bid 종료·유효 prefix 및 명시된 비용 계약으로 계산한다. 미도달·검열·결손은 실패나 손익0으로 대체하지 않는다.
5. 현재 generic publisher의30/10 요건은 변경하지 않는다. 전용 계약 제안은 `비중첩 episode + 원watch/date cluster`를 지원 단위로 기록하고 전체 이후 날짜 cluster에서 같은 scope의 고정 후보와 parent를 비교한다. 선정은 원native 승률 개선·지원조정 비교이며 성공 보존 veto를 두지 않는다. episode 수로30/10을 대체하지 않는다. 실제 producer/consumer 등록과 cluster 지원량 계약, 비용 후 rolling/cumulative/version 검증은 운영 승격의 별도 gate다. 이번 출력은 등록된 publisher가 아니며 공식 policy candidate는 null이다.

## 3. Main/Widget 대조

- 원Widget BUY/SELL full fill, terminal, 같은 custody, 정책 hash·세션·target bps·cost provenance를 exact 대사한다. 매도금액에 적용하는 비용을 진입금액 대비 비율로 계산한다. broker 정산 손익이 없으면 `체결 기반 설정비용 추정`으로 표기한다.
- 실제 Widget 거래와 연구 Main 판정의 시간 겹침·origin/세션을 먼저 확인한다. 동일 사건 비교가 불가능하면 이유를 표시하고 가격 차이를 인과적 진입 우위로 주장하지 않는다.
- 정규장 연구 모집단 밖의 원projection도 같은 날짜·삼성전자·Widget 청산 전으로 한정해 확인한다. 발견한 Main 장전2건은 원capture canonical hash에 exact 연결하고, 당시 ask와 동일 Widget 체결 종료가격의 point 진단으로 진입가격·비용 차이를 분리한다. 전체 prefix/실제 Main 주문·손익 또는 정규장 학습 표본으로 승격하지 않는다.
- 같은 Main 판정 시점의 실행 가능한 ask에 연구 Main barrier와 해당 날짜 Widget 정규장 native target 수식을 적용한다. Widget target 미도달을20분 강제 청산으로 만들지 않는다. 이 비교는 가격 수식 대조이며 실제 Main 전체 holding/exit나 Widget 주문 queue/scale-in/guard를 재현하지 않는다.
- Widget target을 bid가 넘어도 resting limit보다 좋은 체결가를 가정하지 않는다. 당시 bid와 모델 target 종료가격을 따로 기록하며 실제 체결이라고 표시하지 않는다.
- 현재 Main 종료값은 exact-date bootstrap 설정 증거로만 표시하고 당시 PID 적용 증거와 구분한다. actual Widget 장전 target과 정규장 target을 섞지 않는다.

## 4. 후보 고정과 이후 재생

- 선행 학습에서 선정한 `parent_only|foreign=up|veto`, `parent_only|past_gap_180|program_change=down`을 고정한다. 원적용 모집단은 삼성전자 전체 origin이며 전용 fixed-watch 이식 결과를 별도로 계산한다.
- 학습9/29·9/30, 이미 탐색된10/2 진단, 이후10/4 이후 날짜를 구분한다. 다음 자료가 없으면 `waiting_new_source_date`다. 새 결과에 따라 후보를 재선정하는 코드는 두지 않는다.
- 재생 입력은 기존 원capture를 가리키는 sealed capsule와 projection·census·원native projection 경로/SHA/date/parent를 요구한다. 현재/당일 parent와 원bundle, 원판정/guard/label/cost/native, 실제 원capture canonical hash와 source clock/route/expiry, 독립 보관 stream의epoch를 대사한다. future/backdated clock, identity/trace/원source/parent/hash 불일치는 차단한다. source unknown은 parent 승계다. 출력은 새 `tmp` 연구 generation만 허용한다.
- `--prepare-date`는 기존 자동생성 원native projection, 같은 날짜 원capture, 삼성전자 보관 체결/호가 shard만 읽어 재생 capsule을 만든다. 원천이 없으면 대기 receipt만 쓰고 조회·수집하지 않는다. 이후 input을 같은 검증기로 확인한 뒤 고정 후보를 재생한다.
- 개별 canonical/provenance 불량 row는 식별 가능한 exclusion ledger로 분리하고 유효 행을 유지한다. 삼성전자 유효 표본이 없으면 `valid_empty_native_population` 또는 `source_quality_excluded_all`을 구분한다. 전역 parent/generation·원trace/clock·격리 실패는 재생 계약 결손으로 차단한다.
- 운영 승격은 별도 등록·승인 범위다. 후보의 승률·지원조정승률·coverage 및 비용 후 결과와 미확정 수를 제시하며, 연구 episode만으로 generic 지원수를 충족했다고 표시하지 않는다.

## 5. 검증과 종료

리뷰→수정→재리뷰→표적 pytest/compile/diff 후 cold/warm 재생을 실행한다. 실제 source의 prefix mask 동일성, 원capture/선행 source·정책/인계 hash 보존, 원native/day와 episode 분모, custody·세션·비용, 고정 후보 이후 날짜 adapter의 정상/거부 경로를 검증한다. 문서 링크/owner와 print-only parser를 검증한다. 이후 날짜 자료 부재는 연구 준비 완료와 실제 성능 검증 대기를 별도 보고한다.

## 6. 고정 후보의 이후 날짜 실행

아래 명령은 연구 receipt만 생성한다. 기존 같은 output이 있으면 다른 새 generation 경로를 사용한다. parent가 바뀌면 재계획을 요구하며 새 후보 탐색을 실행하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_fixed_watch_evaluation_research --frozen tmp/samsung-fixed-watch-evaluation-20261004/accepted-cold/frozen-candidates.json --prepare-date 2026-10-06 --output tmp/samsung-fixed-watch-evaluation-20261004/later-20261006
```

원천 생성 이후 같은 명령을 새 generation에서 실행하면 capsule 생성→canonical/native/epoch 대사→후보 고정 재생을 진행한다.10/6 기존 Main/Episode/Widget/PREOPEN owner와 운영 인계 절차를 변경하지 않는다.
