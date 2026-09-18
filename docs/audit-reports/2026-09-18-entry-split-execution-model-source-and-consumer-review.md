# Entry split 실행 모델·원천·소비 계약 리뷰 — 2026-09-18

## 판단과 수행 범위

사용자는 [ES0–ES7 계획](../proposals/entry-split-order-plan-submitted-order-replay-and-economic-tuning-improvement-plan-2026-09-18.md)의 구현·반복 리뷰/수정/검증·commit/push·배포 및 제한 장후 재생성을 승인했다. 이 기록의 결과 거래일은9/17, 다음 사용자 예정 적용일은9/21이다. 휴장일9/18 자료를 생성한 것으로 재표시하지 않는다. 실행 owner는 현재 checklist의 `KiwoomCommonHealthOpportunityCostAcceptance0917` 하나를 유지한다.

**원천 보존·실행 오차 진단·검증되지 않은 승격 차단·동일 입력 재사용·Daily 소비 계약을 구현했다. 운영 청산/실제 비용/자본을 재현하는 경제성 모델과 독립 검증 계약은 아직 지원되지 않는다. 전체 계획의 경제성 구현 완료 또는 양수 후보 준비 완료로 발표하지 않는다.** Source gap은 유효 no-edge가 아니다.9/21 준비 정책은 부적격 bucket에서 `keep_original_order`, 활성 후보0이며 승인된 operator fallback과 주문/손절 guard를 유지한다.

Main/worker 재시작, 주문·취소·provider 호출, env/threshold/cap/lock override, cron/calendar/패키지 변경, 전체 장후 chain 재실행과 다음 PREOPEN의 조기 확정은 수행 범위가 아니다. 병행 scale-in 파일·정책·holdout을 보호한다. 작업본의 Python을 통째로 배포하지 않고 최신 main 기반 별도 managed release를 사용한다.

## 확인된 결함과 보완

| 경계 | 확인 및 보완 | 검증 |
| --- | --- | --- |
| producer→compact | atomic plan/block·four-arm·leg sent/fail/no-response·bundle failed가 기존 registry family에 누락됐다. 기존 dynamic entry family에 등록 | 실제 atomic owner 함수→runtime emitter→logger companion→native decoder→signed quartet 회귀 |
| compact 필드 | 제출 compact의40필드 제한으로 atomic/price/attempt 해시와 frozen seed가 빠질 수 있었다 | 낮은 빈도의 원자 단계는 원천을 보존하고 bundle에는 필수 계약을 기존 compact에 추가; 나머지 compact 기능 유지 |
| 원천 소비 | 과거 family partition만 읽으면 현재 producer가 발행하는 flat companion을 놓친다 | 작은 flat+partition 읽기·중복 제거, 날짜/변경 검출·최종 symlink 거부·전체 decoded64MiB 경계; 큰 raw는 읽지 않음 |
| 실제 주문 정답 | winner/COMPLETED 평균만으로 실행 정확도를 확인할 수 없다 | 기존 owner journal의 shared-lock·chain/hash 검증 read-only snapshot; Main BUY NEW inventory에 rejected/unbound/pending/no-fill/partial도 보존 |
| join/중복 | 주문번호 재사용, account 충돌, conflicting replay 뒤 정상 행 재유입, source wrapper 차이에 의한 가짜 충돌 | date+broker key, account/plan/qty/symbol/venue/session 결속, 영구 conflict quarantine, 의미 있는 제출 필드 비교 |
| 모델 오차 | 연구 allocation 뒤 arm이0으로 바뀌어 actual fill과 비교하면 잘못된 실패가 발생한다 | allocation 이전 incumbent 실행 arm과 최초/최종 modeled fill clock·VWAP 보존; 실제 filled_qty/amount는 cumulative 최종값 사용 |
| 허용 오차 | quote 연속성1.5초는 실제 체결 clock tolerance가 아니며 임의1tick을 모든 scope의 PASS 기준으로 쓰면 안 된다 | 오차를 진단값으로 보존; scope tolerance 미정이면 ready_for_validation이고 validated_scope/PASS는 아님 |
| 승격/소비 | 연구 quartet PASS 또는 작은 positive child만으로 기존 split·원자 quantity×leg 정책이 승격될 수 있다 | report/policy model/date/SHA 계약, Daily hold_runtime_scope, 원자 publisher 및 PREOPEN/runtime 공통 predicate에서 검증되지 않은 현행 split 거부 |
| 재계산 | 같은 원천을 매번 native/grid로 다시 계산하거나 cached alias 손상을 재사용할 수 있다 | compact content hash·journal revision·model source SHA·clean baseline·source quality·native generation·effective date·maturity 경계 precheck; unchanged이면 replay 전 반환; immutable report/policy와 current alias 검증 |
| 결과 인계 | source gap을 이전 negative-EV OFF envelope로 오인하거나 Daily가 과거 generation을 유지할 수 있다 | 해당 새 source/model gap에는 fresh OFF 결정을 만들지 않음. 기존 Daily 모듈의 한 family refresh로 immutable policy/hash/effective date 전달; 다른 세션 candidate 보존 |

새 production module/DB/service/collector/cron을 만들지 않았다. 기존 producer·replay·logger·registry·Daily·EV 모듈을 확장했다. Kiwoom protocol/request/parser/FID를 변경하지 않았으므로 upstream reference gate를 새로 호출하지 않았다.

## 실제 자료와 남은 계약

원본9/17 report as-of는 `2026-09-18T00:14:34+09:00`다. atomic 관측3/invalid3/valid0, native raw_plan0/unique0/completed0, four-arm0이다. 작은 과거 compact는 raw 원분모 전체의 부재 선언이 아니다. invalid3의 최초 blocker는 lossless 원천 없이 복원하지 않았으며 unknown으로 유지한다. 원본 cumulative state·generated_at·통계와 generation/holdout/order ledger는 보존한다.

검증한 owner journal1022 events에는 episode/widget 주문만 있고 Main BUY NEW가 없다. 이는 **해당 journal에서의0**이며 과거 전체 Main 제출/체결 census0이 아니다. 전체 실제 attempt 분모는 null이다. 기존312 outcome/223 pending/positive exact child3과 이 inventory를 합쳐 신규 real evidence로 만들지 않는다. 기존180초·±0.5%·0.23%/stress0.28%·reservation180 연구 모델은 supporting이며 운영 청산·정산·자본 재현이 아니다.

| 범위 | 상태·남은 closure |
| --- | --- |
| ES0 | 작고 검증 가능한 원천 inventory/보존식 완료. 과거 invalid3 상세 및 historical Main 전체 census는 미확정; 전수 raw 재스캔을 강행하지 않음 |
| ES1–ES2 | 실행 오차 section·producer/compact/decoder·authority gate 구현. Scope별 model tolerance/floor/rolling/holdout owner 계약 미정이므로 지원 PASS 없음 |
| ES3 | incumbent entry 오차 진단 가능 경로 구현. 실제 operating exit/cost/capital 재생·completed net residual 및 validated_scope는 미구현/미입증 |
| ES4 | 기존 quantity-fixed leg effect와4군·30/80%/EV0.10%/fill 감소≤5%·chronological holdout 유지. 운영 모델 오차를 반영한 robust paired lower bound는 null; positive 자동 승격 없음 |
| ES5 | 기존 source-date 결과를 subsection successor로 갱신하며 unchanged precheck에서 native/grid 생략. Revision 발생 시 해당 subsection 재평가; per-parent 선택적 market replay cache는 추가하지 않음 |
| ES6 | 모델 미지원 inactive 정책→Daily exact generation→PREOPEN/runtime common predicate 회귀.9/21 정책 준비와 실제 PREOPEN/PID 선택은 별개 |
| ES7 | 실제 PID·자연 적용·완료 비용·version별 rolling/cumulative EV는 OPEN. 모델 ΔEV 또는 배포를 실제 이익으로 계산하지 않음 |

다음 closure는 자연 valid frozen initial-entry plan→exact broker order→terminal fill/cancel의 결속, 당시 운영 exit/cost/budget의 재현 가능한 계약, 고정 scope tolerance/model version, 미사용 날짜 model validation과 별도 candidate holdout이다. 운영 모델 지원 자체를 구현/검증하기 전에는 표본 증가만으로 active가 되지 않는다. 필요한 helper/계약은 기존 owner에 추가하며 당시 AI/비결정적 exit를 actual SELL 복사로 대체하지 않는다. ETA=null이고 기존 owner는 OPEN이다.

## 검증·배포·결과 증거

`tmp/entry-split-model-validation-20260918/`가 exact source/test/push/selection/regeneration/consumer SHA receipts를 소유한다. 최종 targeted pytest, compile, diff check와 print-only parser를 통과한 변경만 commit/push/select한다. 새로운 in-scope defect가 없어지기까지 재리뷰했고, unsupported model과 미래 데이터 부재를 code PASS로 닫지 않았다.

- Core: `pytest-release-core.txt`, `pytest-last-consumers.txt` 및 `validation.json`의 마지막 실행 결과.
- 원본 보존: `predecessor-artifacts.json`, `original-entry-split-report.json`, `original-daily-report.json`.
- 최종 배포: `deployment.json`의 immutable release/root/full commit·push·router 확인. Selector 변경은 실제 PID 전환이 아님.
- 제한 결과 갱신: `regeneration.json`의 source9/17/prepared9/21 generation·정책·Daily·EV·summary·reuse·원본 cumulative hash·다른 세션 보존.
- 전체 장후 strict/summary/controller는 원래 실패 상태를 별도로 기록한다. Scoped PASS를 전체 chain DONE으로 대체하지 않는다.

생략한 작업은 전수5.7GB raw 읽기·전체 provider/trading suite·performance sweep·전체 chain/PREOPEN/기동/주문·외부 sync다. 잔여 위험과 미완료 경제성은 위 ES 상태를 따른다. 이 변경은 자연 원천 수집과 양수 정책/실제 성과를 증명하지 않는다.
