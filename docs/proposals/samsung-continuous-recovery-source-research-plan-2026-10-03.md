# 삼성전자 연속 회복 패턴과 보유 원천 소비 연구계획

Owner: `SamsungContinuousRecoverySourceResearch1003` (2026-10-03 checklist).
근거: [원천 소비 탐색](../../tmp/samsung-source-consumption-exploration-20261003/findings.md), [기존 대상 분리계획](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md).

## 1. 목적과 범위

사용자 지시로 기존 원천에서 삼성전자에 특화된 추가 가설을 검증한다. KRX 정규장005930을 대상으로9/29·9/30·10/2를 사용한다. NXT 장전 위젯의 실현 거래는 custody/시점 참고이며 정규장 Main 성공 표본으로 합산하지 않는다. 세 날짜는 모두 이미 탐색한 자료이므로 시간순 후단 결과도 탐색 검증이다.

기존보다 높은 비용 결합 목표-first 승률을 우선한다. 성공100%·80% 보존은 탈락 조건이 아니다. 기존 성공 제외·손실 회피·선택량·coverage·미도달·순가격 경로·원천 결손을 별도로 보고한다. Main guard가 허용하는 행동 비교와 전체 시장 가격 신호의 결과를 구분한다.

이번 범위는 계획·독립 연구 코드·보유 원천 재계산·리뷰/검증이다. 정식 정책 발행·공통 판정 변경·원천 수집 확대·외부 API/provider 호출·배포·재기동을 포함하지 않는다.10/6 현재 정책/PREOPEN owner를 유지한다.

## 2. 위치와 산출물

- 연구 producer: `src/engine/scalping/samsung_continuous_recovery_research.py`. 기존 Main 오프라인 연구와 같은 소유 경계이며 runtime import/publisher 연결은 없다. engine root 신규 모듈을 만들지 않는다.
- 표적 회귀: `src/tests/test_samsung_continuous_recovery_research.py`.
- 고정 입력·feature projection·후보·결과: `tmp/samsung-continuous-recovery-research-20261003/`.
- 최종 분석과 한계: `docs/audits/samsung-continuous-recovery-source-research-review-2026-10-03.md`.

## 3. R0 — 원천 봉인과 순서 검증

1. 삼성전자 Main 원본519개를 exact scope로 추출하고 현재 parent SHA `d94fecaf…`로 재생한다. 이전 tmp의 연구 특징만 재사용해 누락을 반복하지 않는다. 원천3개 SHA·결정 trace·정책·route·native admission을 보존한다.
2. 완료봉의 동일 `005930_AL` route, 날짜, 완료 상태, OHLC와 연속성을 검증한다. 보유 Main raw capture의 완료 OHLCV가 같은 봉과 일치하면 거래량을 복원하고 첫 capture 시각을 남긴다. 나중에 기록된 과거 완료봉을 이용한 분 단위 재구성은 당시 Main 입력 영수증과 구분한다. 값이 충돌한 봉은 volume 결손이다.
3. 종일 보관된 `scalp_micro_reversion_forward`의 normalized market/depth stream을 조사한다. producer manifest는 증분 byte count일 수 있으므로 파일 실측과 SHA를 함께 봉인한다. 동일 item/venue/session, epoch, series sequence, local receive/exchange clock, path eligibility를 검사한다. 미래 depth와 다른 epoch를 join하지 않는다.
4. 위젯의 완료봉/관측은 원천 route가 Main AL과 다르면 수치 결합하지 않는다. 위젯 신호 시점·소유권·품질 상태는 비교 문맥으로 보존한다. 실제 주문 receipt와 미래 고점 touch를 합치지 않는다.

## 4. R1 — 과거 정보만 사용하는 setup 구간

완료봉의 pivot low를 오른쪽2개 봉이 끝난 뒤에만 확정한다. 확정된 지지선·당시 과거20분 저항·확인 시각을 고정한다. 이후 재시험·지지선 위 회복·저항 회복·무효화를 순서대로 기록한다. 지지선 하향 이탈, 저항 도달 또는 최대30분 경과로 구간을 닫고, 그 뒤에 확인된 새 pivot으로 재개한다. 장중 원천 단절·날짜 변경에서 초기화한다.

episode는 연구용 ID이며 원본 native admission에 역연결한다. 한 구간 안에서는 후보별 최초 적격 신호만 택하고, 결과가 결손이라고 다음 좋은 신호로 바꾸지 않는다.10분 결과창의 겹침도 제거한다. 날짜를 잘라 독립 거래일/정식 지원수를 늘리지 않는다. 미래 원천을 변경해도 과거 feature와 episode ID가 변하지 않는 회귀로 검증한다.

## 5. R2 — 특징 복원과 단계별 비교

- **가격:** 지지선 재시험, 위로 회복, 고점 대비 눌림, 범위 내 위치, 저점 상승, 저항까지 거리.
- **거래량:** 같은 route 완료봉의 하락/반등 거래량 비율. 원천이 없거나 서로 다르면 null. 독립 시장 stream의 과거 거래량 비율은 별도 특징이다.
- **Main 체결:** 압력·순공격매수·가격 반응·틱 가속·같은 가격 흡수·프로그램 변화. freshness/trusted count와 대량 매도 위험을 분리하여 유효한 부정적 값을 남긴다. 실행 guard는 변경하지 않는다.
- **연속 시장:** 지난10/30/60초 매수 비중, 최근 매도량과 앞 구간 비교, 거래량 변화, 현재 가격의 저점 회복, 과거 대량 매도 뒤 회복, bid 회복·depth 변화. 대량 매도는 현재 사건 전에 존재한 최근60개 거래량의95분위와 중앙값3배 중 큰 값으로 정의하고 최소20개 과거 거래를 요구한다. 이후 회복 조건은 사건 발생 뒤의 관측만 사용한다.

분봉 재구성과 Main exact 판정 각각에 가격만/거래량 추가/복원 체결 추가/연속 시장 추가의 ablation을 둔다. 초 단위 원천이 끊긴 경우 순서 가설만 평가 불가로 남긴다. 다른 가격·분봉 가설을 함께 탈락시키지 않는다.

## 6. R3 — 비용·학습·후단 비교

- 같은 날짜/route의 원천 비용 계약을 보존한다. 분 단위 가상 시작점은 수수료·세금0.23%와 사전에 정한 보수적 가격 마찰0.10%의 연구 비용0.33%를 사용하며 실제 체결 비용으로 표시하지 않는다. Main 시점은 당시 source-bound 비용을 사용한다.
- primary 결과는10분 안의 비용+0.1% 목표와 gross−0.7% stop의 선도달이다. 미도달은 binary null이며10분 종료 가격의 별도 CF도 표시한다. 동일 봉 두 경계 도달·원천 단절은 제외한다. 초 단위 경로와 분봉 경로를 혼합해 유리한 결과를 골라 쓰지 않는다.
- 학습9/29→후단9/30, 학습9/29~30→후단10/2의 두 fold를 실행한다. 첫 fold 선정 조건을10/2에도 그대로 유지하는 검증을 병기한다. 후보와 수치 경계는 학습의 과거 특징에서만 만들고 후단은 재선정에 쓰지 않는다.
- 후보 문법은 고정 가격 기본조건에 위 특징을 최대2개 추가하는 조합으로 제한한다. 같은 특징의 중복 경계는 가장 강한 조건으로 정규화한다. 고유 행동이 같은 후보는 단순한 조건을 먼저 남긴다. 최소 연구 학습 지원3개를 적용하고 Wilson 하한→원 승률→지원수→단순성으로 고정한다. 이 연구 지원수는 정식 승격 기준을 대체하지 않는다. 승률 계산 가능 표본과 미평가 표본을 함께 보고하며 기존 성공 보존을 veto로 사용하지 않는다.
- 전체 시장 신호에서는 동일 분모의 지지선 회복 기본조건과 비교한다. Main에서는 현재 parent ENTER에 대한 필터와 기존 soft-confirmation guard 안의 회수를 각각 비교한다. 나머지 hard/source/liquidity/local-breakout 제약 때문에 연결할 수 없는 가격 신호는 원인과 함께 남긴다.

## 7. R4 — 리뷰·완료 기준

구현→자체 리뷰→수정→재리뷰→표적 pytest/compile/diff·문서 링크/owner/print-only parser를 수행한다. 시간 누출, route/epoch 혼합, 단절·null의0 변환, 후단 재선정, 반복 관측 분모, source-quality와 adverse 혼합을 중점 검사한다.

완료는 재현 가능한 원천 census, 고정 가설/후보, 단계별 후단 결과, Main 연결 가능성과 추가 원천 필요 여부를 갖춘 연구 리뷰다. 새 정책 후보가 없다는 이유만으로 작업을 미완료로 두지 않으며 가격 진단의 성공을 정책 선정으로 표시하지 않는다. 결과가 양호한 연구 후보는 고정 조건과 추가 검증 항목을 명시한다. 실제 배포/정책 변경은 이번 연구 결과와 별도다.

## 8. 실행 결과

R0–R4를 실행하고 [최종 연구 리뷰](../audits/samsung-continuous-recovery-source-research-review-2026-10-03.md)에 결론·검증을 기록했다. 최종 원천/계산은 `source-02`/`run-02`다. 체결489,445·호가334,124행과 Main519판정을 연결했고,24개 비교와 새 특징을 요구하는16개 보충 비교를 수행했다. 추가 정보의 후단 우위는 미입증이며 Main09:43의 기존 성공 사례를 재확인했다. 새로운 수집에 앞서 보유 stream의 사건 직후 시점을 연구할 수 있다는 근거를 확보했다. 정식 정책과 실제 매매 변경은 없다.
