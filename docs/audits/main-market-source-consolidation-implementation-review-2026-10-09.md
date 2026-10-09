# Main 공통 시장원천 전환 구현·리뷰

2026-10-09 KST. Owner: `MainMarketSourceConsolidation1009`.

MS0–MS5의 코드 전환을 구현하고 생산자·직접 reader·정책 pin·반복 실행을 리뷰했다. 검토 범위의 미해결 코드 결함은 없다. **T8 전체 성능 수용은 부분 검증이며 MS6 운영 적용 근거로 사용할 수 없다.** 배포·재기동·정책 발행·실제 장후 재생성·데이터 삭제는 수행하지 않았다.

## 구현과 결함 보완

| 경로 | 보완 | 검증 |
|---|---|---|
| Main 공통 helper | 저장 partition/session helper를 `src/trading/market/session_contract.py`로 이동. 전 분의 시각·timezone wall-clock 경계 동등성 유지. Main v4/v5/v6 contract pin에 포함 | 09:00/15:30/자정·모든 분 비교, 공통 파일 변조 시 fail closed |
| boot/구독 생애 | 퇴역 collection-target boot producer, pinned/demotion, deferred 등록 가지 제거. 옛 command·feedback REG는 wire 호출 없이 거절 | KRX/NXT/SOR, 재접속, 실패 REMOVE, cap, exact probe borrowed/adopted/removing, 후행 관측 보호 회귀 |
| Main 원천 writer | 기본 raw 모드에서는 `MultiHorizonShockDetector`를 만들거나 호출하지 않음. legacy detector injection은 archive fixture에만 보존 | 기본 raw close, 0B/0D 단일 writer, legacy archive fixture 별도 검증 |
| 원천 영수증 | `main_market_source_v1`, raw close/error·수집 epoch 범위 검증. legacy reference/detector 지표는 null. 닫힌 영수증을 `closed/`에 보존 | 최신 boot 교체·재접속 세그먼트·원천 손실·미지원 계약·원 날짜·정확한 ingress quarantine 반례 |
| 식별자와 clock | 기존 per-packet tick의 native epoch/route sequence를 사용. collector sequence를 native identity로 대체하지 않음. 0B receive-session은 worker에서 파생 | 세 route·0B/0D namespace 분리. `_AL` 저장 SOR와 실제 execution venue UNKNOWN 유지 |
| writer 성능 | batch JSON을 한 번 인코딩하고 같은 bytes로 용량 검사·append. partial write, fsync, nofollow·maintenance lock 유지 | 인코딩 1회·동일 bytes·queue full·close timeout·writer restart·압축/보존 회귀 |
| 직접 reader | canary와 native reader 및 direct freezer를 함께 이관. 신원·clock·epoch·미지원 row는 식별하여 제외하며 정상 구간을 보존 | Main closed raw가 reference 없이 native reader에서 소비됨. 원천 결손을 승률 0으로 바꾸지 않음 |
| 장후 세대 | frozen `source.json`과 물리 partition hash를 검증하여 재개. 새 입력은 별도 명시 세대·lock. 선택 path/hash를 run 및 정책의 `source_receipts`에 연결 | 동시 재개, hash 변조, 명시 세대 결손·경로 이탈·압축 alias 충돌 거절. 기본 세대로 fallback 없음 |
| 재사용 | 같은 fingerprint의 정규화 파생·mask·snapshot을 기존 공유 Store에서 재사용 | 두 번째 operating replay의 observe/snapshot 호출 0, 동일 proposal metrics, Provider request 0 |

추가 리뷰에서 `_send_reg` 가변 인자 wrapper에 source guard를 잘못 배치한 오류, native route-key namespace 오해, 전역 EventBus 테스트 누수, 새 `encoded` 인자를 받지 못한 오류 주입 fixture, archive canary의 오래된 dependency pin을 발견하여 보완했다. canary pin은 guard를 완화하지 않고 새 측정 영수증과 작업 시작/선택 릴리스에 동일한 storage dependency의 직접 hash로 검증한다. 과거 측정 파일은 수정하지 않았다.

확장 회귀에서는 역사적 V1/V2 handoff가 V3 이후의 `routes` 구조를 가정하는 오류를 수리했다. 옛 시장 cell 수는 유지하고 미정의 operating route 수는 null로 남긴다. epoch 영수증의 손상된 배열도 reader 전체를 중단시키지 않고 해당 epoch를 제외한다. 옛 collection-target 양성 테스트는 명시 archive fixture에서만 역사적 owner 조건을 고정하여 재현하고, 현재 모드의 episode/widget 제외·과거 row 보존/등록 0은 별도로 검증한다. 유효 publication을 누적 비교 승리로 간주하던 옛 감시기 테스트 기대값도 실제 계약에 맞췄다. production retirement guard나 감시기 자체는 완화하지 않았다.

새 engine-root Python module은 만들지 않았다. 회귀는 기존 `src/tests` 소유 테스트에 추가했다. `collection_targets.py`와 detector/registry의 역사적 재현 helper는 현재 production import/caller가 없으며 archive 자료 검증용으로 보존했다. Main의 raw writer, 완료봉, depth, compression, master, cost, Provider budget과 manual/retired custody를 이름만으로 삭제하지 않았다.

운영 runbook에는 Main source 생애·명시 세대 재개를 반영하고, 실제 삭제된 21:15 final-refresh 설치와 collection-target 자동 보강의 실행 안내를 제거했다. 옛 절차를 읽어 퇴역 consumer를 재설치하거나 그 경제성 gate를 Main 원천 검증에 전용하지 않는다. 다른 HP/MW 변경과 현행 Main 정책 안내는 보존했다.

## 공식 Kiwoom 확인

수정 전에 공식 `Kiwoom-Securities/Kiwoom-REST-API` revision `953e5dbff123f437ab4d11a78a95191a685eb51f`를 `2026-10-09T13:52:18.697010+09:00`에 조회했다. 확인 범위는 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 0B/0D, `kiwoom/core/client.py`, `core/auth.py`, `core/ws_client.py`, `kiwoom/realtime/{packets,schemas,decoders,stream,events}.py`, Postman collection이다. 이 revision에는 `kiwoom_docs`가 없어 부재를 기록했다.

REG refresh 1/0, REMOVE, REAL/LOGIN/PING, real/demo endpoint, KRX/plain·NXT/_NX·SOR/_AL, 체결/호가 시각·가격·수량 FID를 대조했다. wire 형식·FID parser·auth/account/order/continuation·실제 체결 venue 추정은 변경하지 않았다. SDK/specs는 자료 확인에만 사용했으며 증권사/API·Provider 실제 호출은 0이다.

## 성능 측정의 범위와 제한

[정확한 코드·설정·반복 측정 영수증](../audit-reports/2026-10-09-main-market-source-latency-validation.json.txt). 원본 작업 시작 bytes를 별도 고정하고 같은 host/입력/queue/batch/disk guard로 시나리오별 baseline/candidate 각 3회 실행했다. 추가 반복은 발견한 callback 중복 검증·route frame 복사·worker로 옮길 파생 계산을 수정한 뒤에만 수행했다. 측정에는 실제 주문·Provider·운영 원장 복제가 없다.

| 시나리오 | collector+writer CPU 중앙값 감소 | WS queue+exit shell+writer CPU 중앙값 감소 |
|---|---:|---:|
| 정상 혼합 | 30.1% | 24.4% |
| burst | 40.0% | 30.8% |
| 느린 fsync | 41.6% | 31.5% |

각 run의 0B 1,600행·0D 800행은 모두 durable count와 일치하며 drop/worker error 0이다. batch 인코딩은 2,400회 감소했다. 별도 0B canary는 3회·각 2,000 callback에서 내부 p95 최대 0.024954ms, p99 최대 0.034428ms로 **기존 1ms/2ms 및 최소 1,000회 guard를 유지**했다. 이 결과의 PASS 범위는 collector 0B 절대 guard뿐이다.

정상 WS callback p95 중앙값은 0B 0.0592→0.0495ms, 0D 0.0934→0.0817ms였고 저장 batch p95는 29.75→16.30ms였다. 필수 provenance 필드 때문에 첫 정상 collector run의 0B raw bytes는 1,408,528→1,651,728 bytes로 증가했다. 이를 디스크 write bytes 감소로 주장하지 않는다. 압축·보존·상한은 유지했고 행 샘플링으로 부하를 줄이지 않았다.

burst·느린 fsync의 일부 p95/p99/max와 diagnostic snapshot 편차는 계획 §7.3 상대 기준을 전부 통과하지 못했다. 이를 CPU 개선으로 상쇄하지 않았다. 또한 실제 Main scanner warm loop·native signal→Main claim·PID 청산 반응은 관측하지 않았으며, exit shell/evaluator의 coalescing 표본 수를 전체 수신 표본 수로 대체하지 않는다. **G5 성능 수용은 미완료**다. owner는 현재 checklist의 동일 stable ID이며, 다음 조치는 해당 부하의 경합/tail 및 같은 신호 단위 측정 보완, 종료 조건은 §7.3/T8 통과다. 재측정을 좋을 때까지 반복하거나 guard·TTL·cap을 완화하지 않는다.

## 코드 검증과 운영 경계

- 최종 통합 표적 회귀: **1,425건 통과, 실패 0**. WS/route·probe·Main 감시·exit·collector/canary/storage·native/source·v1–v6 연결/장후 공유 Store 경로를 함께 실행했다. 발견한 archive pin·옛 owner fixture·handoff 구조·감시기 기대값 결함을 보완한 뒤 재실행한 결과다. 기존 pandas 경고와 fork 테스트의 multithread 경고 2건은 남았다.
- 변경 Python 35파일 compile 및 `git diff --check` 통과. 계획/체크리스트/본 리뷰의 상대 링크 81개·fence·공백 검증 통과. print-only parser exit 0, backlog 23건 중 현재 stable owner 1개를 확인했다. 본 작업의 wrapper 수정은 없어 `bash -n`은 실행하지 않았으며 기존 미커밋 wrapper를 보존했다.
- 의미·안전: 기존 13개 패턴의 native 확인/ask·원 5초 TTL·독립 정책·미채택 probe 격리·Main exit wake·주문/수량/route/cap guard 보존. 승리 label·비용·경제성 gate는 변경하지 않았다.
- 비용의 실제 source gap(HP2)은 유지한다. 새 master/economic 데이터나 Provider 예산을 생성·대체하지 않았다.
- MS6은 미실행이다. 신규 코드 pin으로 운영하려면 기존 정식 code binding/handoff와 해당 준비 검증을 사용한다. 초기 정책에 별도의 승률/EV 승인 gate를 추가하지 않으며, 오래된 pin을 무시하지 않는다.
- 선택 릴리스·정책·봉인된 10/12 checklist·Plan Rebase·기존 HP/MW 미커밋 변경을 보존한다. 자연 세션·장후 마지막 consumer/PID/economics는 코드 테스트로 대체하지 않는다.

작업 시작 영수증 58파일 중 54개는 최종 byte hash가 동일하며, 변경된 4개는 이번 owner의 계획·10/9 checklist·runbook·Main helper import가 추가된 state handler다. HEAD/selector/10/12 checklist/Rebase는 동일하다. 선택 릴리스는 `main-market-weakness-20261009-v1` 그대로이며 이 구현의 PID 소비는 없다. 테스트·문서·보존 manifest는 `tmp/main-market-source-consolidation-20261009/`에 있으며 운영 원장/시장 raw를 복제하지 않았다. 외부 sync·실제 Provider/API 호출·수동 장후 실행·배포/재기동·삭제는 생략했다.
