# 메인 전략 임계치 즉시 적용 구현 리뷰 — 2026-09-21

사용자 범위: 계획 구현, 반복 리뷰·수정, 장후 재생성, 커밋·푸시·배포·기동. 후속 지시로 다음 PREOPEN 대기를 제거한다. 이 기록은 실주문이나 자연 수익 증거가 아니다.

## 구현 경계

- 기존 fact producer·calibration·publisher·loader를 확장한다. 신규 Python owner는 `src/engine/scalping/entry_strategy_policy.py` 하나이며 순수 전략 registry/selector 계약을 소유한다. 별도 DB/report family/daemon/cron 및 engine-root 모듈은 추가하지 않는다.
- 82개 전략 좌표를 등록했다. 가격/tick·유동성·변동성·수익률/시간·검증된 as-of 시총에 따라 하나의 정책 내부 profile을 고른다. 시총 미지원은 parent이며 최신 DB 값을 과거로 소급하지 않는다.
- 당시 원시 입력에서 전략 사실·risk/action을 재계산한다. 완료봉 원시는 별도 hash로 보존하고 future/forming/coverage 손상을 거부한다. 원시 재생 증거는 보조 AI compact 입력에서 제외한다.
- 후보 탐색은 유한 joint domain과 train에서 정한 유형 경계를 함께 순회한다. cursor/domain hash, 미완료 여부, 원천 미지원 좌표를 기록한다. 소규모 완전열거와 세 축 동시 변경이 필요한 실제 kernel fixture로 검증한다. 96개 기본 batch를 전역 최적이라고 주장하지 않는다.
- 승격은 동일 기회 비용·운영경로 검증, train 고유기회10/holdout 변경 고유기회3, 날짜 분리, 양수 순익·paired 개선 및 기존 catastrophic guard를 요구한다. 새 정책에 10bp·5종목/5일·실체결 선행 floor를 추가하지 않는다. 후보 AI 입력/owner replay 미지원은 null/source gap이다.
- 적격 후보는 immutable generation·parent CAS·fsync/원자 current 선택을 통해 즉시 적용한다. 날짜별 handoff와 current를 분리하고 current를 다음 적격 정책까지 승계한다. 실패 후보는 current를 유지하고 손상된 active는 진입 차단한다. 초기진입 v2 임계치는 보유 추가매수 owner에 적용하지 않는다.
- 기존 postclose 명령에 `--activate-now`를 연결했다. summary/verifier는 dated handoff와 current 유효성을 따로 표시하며, 로드만으로 PID 소비를 주장하지 않는다.

## 반복 리뷰·검증

- 보호된 source/order/custody 조건과 v1 의미 보존, raw/hash 일치, 유형 UNKNOWN·그래프 순환, 3축 상호작용, 작은 양수 EV의 승격, 날짜 승계·잘못된 후보·손상된 current, provider 원시 중복을 확인했다.
- 수정: rate의 `_sec` 접미사를 시간 하한으로 오인한 registry bounds, raw 결손 한 행이 전체를 막던 경로, source-invalid 경로에 잘못 위치한 rebuilt setup 인계, active 손상 후 legacy AI fallback, 보유 owner에 v2 profile이 전달되는 경로, provider raw 중복을 보완했다.
- 배포 기준 source `90dd032e34efb36fb0ace5d9022fc7bcecb1eaf6` 위 별도 체크아웃에서 관련 11개 suite 955 PASS. 후속 행별 제외/경계 보완의 targeted 검사199 PASS. 추가 검증 및 최종 commit/release 영수증은 아래 실행 결과에 기록한다.
- 작업공간의 다른 수정은 stage하지 않는다. Kiwoom 요청/response/FID/auth/order protocol은 변경하지 않는다. 외부 sync·검증용 주문·후보 AI PASS 합성은 실행하지 않는다.

## 원천 지원 및 열린 완료 조건

- 대량매도 event 이후 회복 tick의 순서를 입증하는 원천은 아직 지원하지 않는다. 과거 boolean을 지워서 진입시키지 않으며 이 축을 전수 튜닝 완료로 보고하지 않는다.
- 시총 known-at·단위·기업행사 provenance가 없는 입력은 UNKNOWN parent다. 완료봉 전체 원시 또는 micro window가 없는 역사 입력의 관련 좌표는 유지하고 미지원 목록을 남긴다.
- BLOCK/RECHECK가 새로운 ENTER_NOW가 되는 후보에는 그 변경된 사실을 소비한 auxiliary/실행/비용 replay가 필요하다. 기존 PASS를 다른 candidate에 재표시하지 않는다. 이 결손이 남으면 정책 선정/경제성 완료가 아니다.
- 전체 계획 P0–P6·모든 시장 유형의 자연 적용·비용 후 실성과를 이 코드 리뷰로 일괄 완료 처리하지 않는다. 기존 `DirectFamilySourceRepairMainMechanisticEntry` OPEN owner를 유지한다.

## 실행 결과

장후 평가·커밋·배포·실제 PID 소비 결과 확인 중.
