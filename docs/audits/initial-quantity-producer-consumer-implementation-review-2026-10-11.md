# 최초 수량 생산자/소비자 구현·반복 리뷰 — 2026-10-11

Owner: `InitialQuantityProducerConsumerRepair1010` / [현재 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md).
범위: [Q0–Q8](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md). 운영 인계는 아래 별도 영수증으로 확정한다.

현재 결과: 추가 재리뷰 6개 결함 보완·검토 범위 finding0, `initial-quantity-repair-20261011-v2` 배포와 source10/8→target10/12 장후 인계/PREOPEN 완료. 실제 인증/PID·자연 주문/경제성은 내일 기동 이후의 별도 수용이다.

## 10/11 추가 재리뷰

사용자의 추가 코드리뷰·보완·배포 요청으로 다음 신규 결함을 보완했다. 앞선 v1 완료 근거는 아래에 역사적 근거로 보존한다. 이번 증거 디렉터리는 `tmp/initial-quantity-rereview-20261011/`이며 운영 배포·PREOPEN은 후속 최종 영수증으로 구분한다.

| 신규 결함 | 보완·종료 시험 |
| --- | --- |
| capture queue/clock 결손의 후보 소비 누락 | 정확 attempt+plan의 종료 증거를 cap 및 cap×shape×T 공통 모델이 읽는다. 알려진 거부·잘못된 시계/계수는 `source_gap`으로 제외한다. 다른 시도의 기록·legacy 종료 증거 부재는 새로운 전역 차단이 아니다. verified actual-fill incumbent control은 보존한다. |
| 잘못된 수집 시계를 정상 종료로 표시 | NaN/bool/역행/잘못된 종료 범위를 명시적 시계 결손으로 기록한다. 유효 관측 시각이 없으면 한 trace를 보존하고 실제 시각으로 종료 증거를 남긴다. 첫 주문 시작+1200초와 후속 leg의 연장 금지는 그대로다. |
| 실행 캐시 index의 크기 검사 전 무제한 decode | symlink/크기 preflight와 최대 RECORD_BYTES+1 read를 JSON decode 전에 수행한다. 크기 증가 경쟁·손상은 새 namespace 재구축으로 처리하며 pin/raw는 덮어쓰지 않는다. |
| feature cache의 전이 reader 결속 누락 | policy/cache/cap receipt/type parser/JSONL reader bytes를 source-features-v3 키에 결속한다. helper만 바뀌어도 정상 cold 재생을 하고 동일 bytes에서는 warm 재사용한다. |
| native capture terminal의 datetime 직렬화 실패 | 보고서의 cap source 종료 시각을 ISO 문자열로 투영한다. native 종료 event→원천 join→report/hash→240개 조합 및 검증까지 회귀한다. |
| terminal 큐 접수 거부 후 trace 삭제 | 실패 시 하나의 bounded trace와 거부 계수를 보존하고 다음 정상 관측 pass에서 같은 시도의 terminal source만 재접수한다. 신규 주문/타이머/동기 저장/무손실 수집을 추가하지 않는다. |

영향 회귀402 passed(`impact-final-tests.txt`), 인계 회귀307 passed(`handoff-tests.txt`), 최종 신규 회귀51 passed(`new-regressions-final.txt`)를 확인했다. 묶음 간 중복 포함이며 합산 고유 건수는 아니다. 실제 원천 형식의 60거래 fixture에서 식별 가능한 결손 1개만 후보 비교에서 제외하고 나머지59개와 actual-fill control을 보존했다. 원천 결손을 modeled-no-fill/실현0원으로 추가하지 않는다. 현재 부모 정책·원 EOD·Main/manual/퇴역 수탁·기계/보조 정책·주문 API·hard safety는 변경하지 않았다.

추가 불변 릴리스 회귀146 passed(`release-tests.txt`). source bytes를 고정한 3회 교대 비교24개 측정(`performance-frozen-results.json`)은 이전 v1과 72거래/새 날짜96거래·전체240조합의 logical outcome SHA가 같았다. cold wall 이전8.065/8.057/8.091초→보완7.906/8.146/7.982초, warm4.567/4.565/4.584→4.533/4.614/4.572, cost-only4.587/4.593/4.594→4.563/4.644/4.593, 증분7.226/7.280/7.306→7.178/7.442/7.183이다. 기존 stage 예산 이내이며 변동폭 내 차이로 추가 성능 향상은 미입증이다. 아래 최초 기능 수리 기준 대비 캐시 개선 근거와 이 추가 수리의 비악화 비교를 구분한다. 측정 중 reader 수정이 포함된 첫 비교는 수용에서 제외했다. 이번 synthetic fixture는 측정 후 즉시 삭제했고 원본/운영 pin은 삭제하지 않았다.

장중 adapter는 정상1024/burst4096/느린 저장1024개씩 3회 교대했다(`hotpath-frozen-performance.json`). p99는 이전 약0.068–0.085ms·보완 약0.068–0.070ms이며 max의 스케줄링 편차도 보존했다. 수량 SHA·CANCEL/RECONCILE/SUBMIT/SKIP·deadline miss0은 같고 provider/주문0이다. 낮은 표본의 첫 p99와 동시 부하 값만으로 수용하지 않았다. 실제 거래 지연·수익 개선의 증거는 아니다.

추가 native 준비에서 초기수량의 동일 valid-empty 세대를 재검증했고 부모 유지다. observer의 source bytes 변경이 기존 트레일링 계약에 영향을 주어 해당 native 인계를 재생성했다. 82.188초/CPU71.410초/RSS158,204KiB, scope20,832·관측7·공통 비교0·12개 부모 유지다(`actual-source-research.json`). 초기수량 캐시 수리만으로 기존 트레일링 코드 결속이 유효하다고 간주하지 않았다.

최신 운영 결과는 다음과 같다.

- `initial-quantity-repair-20261011-v2`, commit `818e2f85c216336c9b927d9ae49aad35f0649af7`. 이전 선택 v1의 source와 이번 수정 전 bytes가 일치함을 확인한 뒤 검토한 source5개와 관련 기록만 승계했다. canonical HEAD·다른 미커밋을 reset/일괄 commit하지 않았다.
- `initial_quantity_rereview_20261011_v1` CAS transaction `verified`. 초기수량 동일 valid-empty 세대 재검증/`carry_parent`, 제출지연→summary/checklist→strict/controller→PREOPEN을 native 인계했다. 트레일링 initial policy 내용과 지연 cell reference/default는 동일하며 변경은 코드/보고서 결속이다(`timing-policy-semantic-comparison.json`). 원 EOD·현재 수량 policy·기계/보조 policy bytes를 보존했다.
- native finalization 실제 DONE `2026-10-11T08:52:58+0900`; chain `740c000a570a79e1c06a4a44792ed59d5cb866a3077b1f9b5fae5e5d1e77f33e`, snapshot `10c1a1f200a0dd294e303de7f440ccf4dfe5873c982a012b04046edd19ba6ebd`. 이전 v1 DONE을 최신 종료 증거로 재사용하지 않았다. 최신 marker issues0·PREOPEN `current_full_contract` PASS·findings0·cron8개/양쪽 예약/release-set PASS다.
- 최종 근거는 `tmp/initial-quantity-rereview-20261011/final-readiness.json`과 `data/report/initial_quantity_repair_deployment/2026-10-11/rereview-final-readiness.json`. 전체 publication process 관측 VmHWM1,046,348KiB는 isolated quantity benchmark와 다른 범위이며 전체 RSS 개선으로 주장하지 않는다.
- native detector는 fail0/warning4/운영 mutation0이다. workorder/KOSPI 원천 경고·실행 중 자기 finalization 대기·source-date 인증8005 dry-run·변경 없는 과거 로그다(`native-detector-summary.json`). 실제 DONE 뒤 marker 검사로 자기 대기를 닫았다. 다른 경고를 수리 완료나 실제 정상 인증으로 바꾸지 않았다.
- 10/12 PREOPEN07:35·Main07:55 준비를 확인했다. 현재 Sunday Main 정지·actual PID consumed=false를 유지하며 시험 주문/실제 AI 호출은0이다. 실제 인증/PID·큐의 durable append·자연 수탁/체결/취소·비용 후 경제성은 10/12 기존 OPEN `DirectFamilyPreopenPolicyHandoff`가 확인한다.

## 구현과 추가 리뷰

| 계약 | 구현·검증 |
| --- | --- |
| IQ-F1/F2, R2 | ORM NULL을 명시 저장하고 transaction 안에서 ID·NULL/실제 0·비용/세대 readback을 검증한다. 실제 broker 비용과 공통 비교 비용을 분리한다. 비용 세대 객체는 Text 컬럼에 canonical JSON으로 저장한다. 누적 날짜별 fact/status/비용 세대를 repeatable-read snapshot으로 봉인하고 발행 전 재검증한다. |
| IQ-F3/F4, R1/R4 | wire epoch를 엄격 정규화한다. 실제 런타임 leg builder와 probe 포함 slot을 사용한다. 수집은 실제 첫 주문 시작+1200초이며 후속 leg가 종료를 연장하지 않는다. sampled print·큐 접수·durable append·체결을 구분하고 terminal의 큐 거부/시계 증거를 보존한다. 완료 경제 모수에 무주문 시도를 0원으로 추가하지 않는다. |
| IQ-F5/F6/F7, R3 | 갱신은 max(clean baseline, 9/29, parent effective_from) 창이다. 유효 부분 체결/보수 무체결 결과를 부모 성과로 치환하지 않는다. 비용·부모 결속 결손 행과 뒤늦은 conflict를 제외한다. cap×shape×T 전체 grid에서 train 후보 한 개를 고정한 뒤 holdout은 그 후보만 검증한다. |
| IQ-D1, R5/R6 | 경제 표본과 archived PID 소비를 별도 판정한다. frozen v1 reader와 v2 실행/비용 reader를 분리한다. 같은 원천일의 정정은 불변 generation과 committed-stage CAS 참조로 발행하며 wrapper/summary/감시가 같은 참조를 읽는다. |
| R7/R8, P1–P8 | 기존 observation executor·공유 두 슬롯/64MiB resident/4GiB 저장 예산에 연결한다. 날짜별 원천·거래별 실행 캐시는 byte 검증하고 비용 정정 시 실행만 재사용한다. 후보 결과는 shard/stream 집계, 측정 시간은 최대4096개 진단 표본이다. 손상 캐시는 새 namespace로 재구축하고 원본/참조 중인 증거를 덮어쓰지 않는다. |

재리뷰에서 추가로 보완했다.

- 실제 비용 원천의 dict → DB Text → census 연결과 NULL 기본값 충돌.
- 기존 profile을 보존하는 `horizon=None` arm을 포함한 전체240개 조합과 actual/model 비교 기준.
- quote 원천 `krx_only/nxt_only/krx_nxt_integrated`와 주문 KRX/NXT/SOR·실제 체결 시장의 분리. 통합 SOR quote로 체결 시장/NXT listing 권한을 합성하지 않는다.
- 실제 quote route 이름을 uppercase KRX/NXT와 비교하던 cap capture 연결 결함. 4개 native route 사례와 KRX/NXT 혼합 체결 SOR 재생/다른 route 거부를 회귀했다.
- 무제한 N×후보 timing 배열과 거대 과거 snapshot의 무제한 decode. 수량 검증은4MiB 이내 native projection만 읽으며 크거나 부재인 원천은 날짜별 결손이다.
- 기존 테스트가 optional frozen-context 실패를 `{}`로 모의하던 결함. 실제 native 실패값 `None`으로 수정하고 실제 제출 분기를 검증했다.

원천 request/FID/REG/REMOVE·authentication·주문 API는 수정하지 않았다. local receipt의 source-only 결속을 수정했다. Main/manual 수탁, 퇴역 owner, 가격/현금/상한·stale/conflict·broker/terminal/hard safety를 보존했다.

## 검증

작업 증거: `/home/ubuntu/KORStockScan/tmp/initial-quantity-producer-consumer-repair-20261010/`.

- 시작 전122 passed. 영향 회귀659 passed (`final-impact-tests.txt`). 실제 제출·Main 공유 분기599 passed (`final-native-submit-tests.txt`). 마지막 bounded-source/발행/소비 영향 회귀362 passed (`final-source-guard-tests.txt`). 묶음별 숫자이며 중복 테스트를 고유 건수로 합산하지 않는다.
- 실제 비용 적격60거래/3날짜 양성 fixture는 갱신 후보 발행→stage reader 검증을 통과했다. 한 행 결손은 나머지59행을 보존한다. train 승자 실패 시 차순위 holdout 탐색이 없다.
- 현재 수량 정책은10/12 소비 검증 PASS. 이 정책을 새 우월성 요구로 중지하거나 재승인하지 않는다.
- 실제 ORM 경로에서 unknown NULL과 확인된 실제0원을 구별했다. 원본 wire 문자열, canonical 비용 세대 Text, restart/CAS/queue/terminal 및 late-conflict를 검증했다.

## 동일 결과 성능

`benchmark_final.py` / `run_performance_closed.py`, 세 번 교대 실행의 원값은 `performance-closed-results.json`이다. 같은72거래(새 날짜 추가96거래), 전체240조합, 실제 비용 적격·정확한 부모 결속과 native quote route를 사용한다. 기준본은 같은 기능 결과를 계산하면서 실행 캐시/검증 memo만 끈다. 모든 반복의 행별 logical outcome SHA가 같다. 실제 실현손익 개선 증거는 아니다.

| 모드 | 기준 wall 초 | 최적화 wall 초 | 기준 CPU 초 | 최적화 CPU 초 |
| --- | --- | --- | --- | --- |
| cold | 7.164/7.041/7.016 | 8.332/8.058/8.068 | 6.931/6.936/6.909 | 6.717/6.746/6.767 |
| warm | 6.875/6.849/6.820 | 4.584/4.577/4.618 | 6.874/6.849/6.820 | 4.584/4.576/4.618 |
| cost-only | 6.879/6.875/6.835 | 4.586/4.599/4.650 | 6.878/6.875/6.835 | 4.586/4.599/4.650 |
| new-source | 9.179/9.135/9.122 | 7.274/7.265/16.789 | 9.051/9.028/9.010 | 6.755/6.754/7.037 |

cold wall은 불변 캐시/fsync 때문에 증가하며 기존14400초 stage 예산 이내다. warm/cost-only CPU·wall은 약33% 감소한다. 새 원천 CPU는 약24% 감소한다. 마지막 new-source wall16.789초에는 동시 역사 원천 진단의 I/O 경합이 포함되므로 일괄 wall 개선으로 보고하지 않는다. 실행 case 수는 기준51840→cold34560/warm0/cost-only0, 추가 날짜69120→11520이다. warm0은 전체 shard bytes/원천/evaluation 검증을 생략한0건 실행이 아니다. 모든 row·조합은 검증·집계한다. 공유 resident claim·RSS·I/O·slot은 원값 파일에 보존했다.

`hotpath-performance.json`은 native allocator/선택 릴리스 및 수정 observer/bundle due를 동결 writer adapter로3회 정상·burst·느린 저장에 실행한 근거다. 수량 SHA·CANCEL/RECONCILE/SUBMIT/SKIP 의미가 같고 외부 주문/API는0이다. 느린 저장2ms에서 생산자 p99는2.125–2.131ms→0.087–0.094ms. 정상/버스트 최대0.204ms 이내이며 default 큐 작업을 보호한다. burst 거부는 명시적인 sampled-source 결손이고 무손실 관측이라고 보고하지 않는다. 실운영 주문 지연/자연 수익 측정은 아니다.

## 과거 자료·운영 경계

9/28 원 snapshot1.7GiB/sidecar65MiB, 9/30 원 snapshot269MiB/sidecar35MiB는 기존 자료다. 무제한 재생 진단은 RAM 증가로 중단했고 DB 변경은 없었다 (`native-intake-aborted.json`). 작은 native projection/원 비용 증거가 없는 과거 날짜는 제외하며 새 수량 reader가 이 때문에 운영 메모리를 소진하지 않는다. 48296/49013의 기존 DB0을 실제 경제성0이라고 인정하거나 비용을 추정 복원하지 않는다. 정확한 비용 원천 부재는 NULL 경제 결과·결손 사유로 소비한다. 역사 DB를 임의 수정하지 않으며 원 원장을 보존한다.

10/12 기동/PID·자연 주문/취소/종결·실현 경제성은 미래 수용이다. 배포/PREOPEN 준비와 분리한다. Main 봇을 시험 주문이나 Sunday 기동으로 자연 수용했다고 만들지 않는다.

## 운영 인계의 추가 검증·보완

첫 발행 시도에서 신규 bootstrap이 공통 logger/admission 변경에 따른 기존 트레일링 인계의 `code_contract` 불일치를 검출했다. 초기수량·제출지연·summary·controller만 갱신해서는 최종 consumer를 통과하지 못했다. `initial_quantity_repair_20261011_v1` 트랜잭션은 전체 메타데이터를 CAS로 원상 복구했고 기존 선택 commit `c66488df8d428ecda57ee3c052c630c3e68f74b2`의 10/12 `current_full_contract` 재검증 PASS를 확인했다. 부분 발행을 성공으로 처리하지 않았다 (`formal-publication-v1.log`, `rollback-readiness.log`).

보완 시도는 같은 source date 10/8의 기존 native holding/all-scope 생산자를 다시 실행해 코드 결속을 갱신한다. 20,832 scope·관측 모수7·공통 비교 모수0, 12개 cell 부모 유지이며 새로운 경제 우월성을 만들지 않았다. 실제 실행83.334초/CPU71.144초/RSS160,480KiB, 외부 provider/AI/주문 호출0이다 (`actual-source-research.json`). 정규 저장→typed trailing CAS→초기수량 successor→제출지연→summary/checklist→strict/controller→PREOPEN을 한 트랜잭션으로 인계한다. 다음 영업일 수용은 10/12 기존 OPEN `DirectFamilyPreopenPolicyHandoff`에 명시해 중복 owner를 만들지 않는다.

## 앞선 v1 운영 결과

- 선택 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-repair-20261011-v1`, commit `a0aec8e1608e810c4dae73f2b39bcf9439afd9f7`. 원 canonical HEAD/공유 미커밋과 다른 task의 변경을 reset하거나 임의 commit하지 않았다.
- `initial_quantity_repair_20261011_v2` CAS transaction은 `verified`. 수량 committed-stage는 `generations/422070d30713aad567ad2ce5c1054723afd4edf748e5cb254c547c9fd99df8e9/initial_quantity_refresh_stage_2026-10-08.json`, SHA `cd1e12ac85875c46f79fd064b8533a14732afe7068d06e0900f23d92fa8ac706`. 적격 경제 거래0·`carry_parent`; 현재 수량 policy/file SHA는 그대로다. 초기 생성에 새 refresh 우월성 gate를 적용하지 않았다.
- 코드 변경에 영향을 받은 트레일링/제출지연 인계를 native 생산자로 갱신하고 source10/8·publication10/11·effective10/12를 유지했다. 기계/보조 정책 SHA `04f13c0bbc438e28f8f97de86f0fa4d52e6ea73a35fc355123daa5b7b2ce5a27`와 원 EOD를 보존했다.
- native finalization이 `2026-10-11T01:30:12+0900`에 실제 `[DONE]`을 기록했다. cleanup/detector는 실제 child 영수증이다. chain SHA `ce568ba3f0c22bc7efb62799d40654ac89a4c800a4bcd9ea96c2ddc543d55539`, snapshot SHA `6de482de6f290d2c0c6c47e3c8bb498407bbd907a8f76f478e8aa436106920e3` (`logs/postclose_finalization_cron.log`). 최종 routing/cron/세대/PREOPEN의 재대사는 `final-readiness.json`과 운영 `data/report/initial_quantity_repair_deployment/2026-10-11/final-readiness.json`에 보존한다.
- 전체 인계 process의 중간 관측 peak RSS는1,059,932KiB였다 (`operational-handoff-process-sample.json`). 수량-only 성능 fixture의150–180MiB와 다른 범위이며 전체 장후 RSS 개선이라고 주장하지 않는다. sampled read/write·native 전체 실행과 isolated benchmark를 구분했다.
- 다음 영업일 예약은10/12 PREOPEN07:35·Main07:55다. 현재 새 Main PID 소비는false이며 Sunday 봇 기동·API/AI·시험 주문은 실행하지 않았다. 실제 PID/start ticks/cwd·정책 SHA, 첫 자연 주문부터1200초의 결속 수집·큐/체결/취소 terminal·실제 비용 후 성과는 10/12 기존 owner가 확인한다.
- 최종 현재 계약 재검증은 `prepared.status=pass`, `validation_scope=current_full_contract`, findings0·finalization marker issues0·cron/release-set/양쪽 예약 경로 PASS다. 감시기의 원천일10/8 recovery 보고에는 warning4가 남았다: 선택 산출물 workorder/KOSPI warning, 실행 중 자기 finalization의 detector 대기, source-date 인증8005 dry-run 경고, 변경 없는 과거 로그. fail은 없고 실제 runtime mutation0이다. 종료 후 marker 검증으로 자기 대기를 닫았으며 다른 원천/인증/로그 경고를 정상 인증 성공이나 수리 완료로 바꾸지 않았다. 새 기동의 실제 인증/PID/자연 종결은 여전히 미래 관측이다.
