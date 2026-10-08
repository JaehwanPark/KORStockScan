# Main 보조 compact 연구결과 운영 연결 실행 리뷰 — 2026-10-08

소유: 오늘 `DirectFamilySourceRepairMainMechanisticEntry`. [구현계획](../proposals/main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md)의 후속 구현 승인과 **15:00 KST 이후 배포·재기동** 조건을 따른다.

## 구현과 리뷰

| 확인한 결함/경계 | 보완 | 검증 |
| --- | --- | --- |
| reader 수정 시 기존 부모의 코드 해시 불일치 | 원 보고서/128 binding을 유지하고 원본 reader·새 reader·v1 요청 동등성을 별도 불변 증빙으로 연결 | 기존 128경로와 157쌍 요청 ID 보존 |
| 연구 전송 별칭과 논리 신호 ID 혼용 | 공통 codec/v2 registry, 논리 입력 유지, SDK 직전 wire 변환 | 실제 `analyze_target`→가짜 SDK 전체 경로와 실제 저장 요청 비교 |
| provider 응답과 해독 결과의 hash 혼용 | 원본 bytes/응답 ID/전송 projection을 outbox 응답에 저장, 별도 해독 영수증으로 연결 | 정상·미완료·잘림·거절·알 수 없는 별칭 분기; 잘못된 응답은 BUY 불가 |
| 프롬프트 문자열 hash와 JSON hash 혼용 | 논리 hash와 실제 전송 bytes hash를 별도 유지 | 전체 진입 경로의 request binding `matched` 확인 |
| 다중 평가 발행·재실행·복구 충돌 | 보조→기계 publisher lock, 단일 CAS, manifest 재실행 동일성, scope별 복구/철회 | CAS 충돌·변조·포인터 기록 직후 중단·다음 날짜 상속 후 복구 |
| 자정 후 원 거래일 overlay 누락과 준비 후 변경 | 거래일/부모별 최종 세대, 명시 원천일 binding, 다음 준비의 overlay dependency 검사 | 과거 거래일 조회·cold inheritance·준비 뒤 세대 변경 거절 |
| 구형/신형 요청의 이중 변환 | registry별 요청·해독 dispatch; 연구 원본 codec 고정 | 기존 연구와 혼합 reader 회귀 |
| 실제 일반 WATCHING caller의 coordinator 누락 | Main이 생성한 기존 coordinator를 wrapper/handler로 전달 | 실제 Main call 식과 wrapper 실행, 5개 고정감시 인자 전달·no-claim 미전송, 기존 native async commit/경로 변경 회귀 |
| 전송 직전 native claim 종료의 provider 실패 오분류 | `validate_active_claim`의 명시된 종료만 WAIT로 반환, provider 실패 횟수 증가/성공 reset 모두 금지 | 동일 native 종료 5회에도 원 실패 수 유지; 알 수 없는 예외·실제 provider 실패 5회 차단 유지 |
| 진입 금지 시간에는 PID policy 소비 기록도 지연됨 | Main 기동 시 기존 `prepare`를 호출해 실제 PID에서 정책 검증·소비 | 실제 기동 분기 실행 회귀; 신호 claim/provider/주문 생성 없음 |

새 codec/호환/전환 모듈은 `src/engine/scalping`에 둔다. 원 기계 kernel, v5/v6 policy와 native outbox의 고정 파일을 변경하지 않았다. 가격·수량·5초 confirmation TTL·provider 중복/불확실 예약·broker/custody·Main-only 퇴역 보호조건을 유지한다. 코드 변경은 새 prompt 생성이나 호출한도 해제가 아니다.

## 연구 재현과 대상

원 보고서: `data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/reports/f9ba2741499504163b7a68964839b482cc8a794c4cb5178fba8d7a2cc2798e7f.json`.

157쌍/314개 실제 응답과 원본 provider receipt를 재검증했다. 개선 네 scope의 14점에서 새 SDK 요청의 prompt/input bytes, schema, model, reasoning, token 설정이 연구와 일치한다. 비교 기준은 **동일 compact 전송 형식의 기존 문구**이며, 기존 native 512-token 경로보다 우수하다는 증거로 해석하지 않는다.

| 적용 대상 | 후보 | PASS 승리/전체 이전 → 이후 |
| --- | --- | --- |
| 삼성 AFTER / SOR | H5 | 2/3 → 3/4 |
| 비상시 종목 AFTER / 2만~10만원 / SOR | H5 | 3/4 → 3/3 |
| 비상시 종목 AFTER / 2만원 미만 / SOR | H5 | 3/4 → 1/1; 실패 1건과 승리 2건 모두 제외됨 |
| 비상시 종목 PRE / 2만~10만원 / NXT | H4 | 1/1 → 2/2 |

`other_non_fixed`의 기존 분류를 사용하며 다른 종목군·가격대·세션으로 확장하지 않는다. 추가 provider 호출 **0회**, 연구 한도 800/사용 653/잔여 147 유지, 정기 장후 100회 한도 유지, 원장 복제 **0개**. 공통 store의 기존 객체와 요청 ID를 참조한다. 원 연구 codec와 새 reader의 작은 코드 snapshot만 보존한다.

## 검증

- 관련 통합 회귀: **578 passed, 7 deselected**. 제외한 7건은 이미 삭제된 `entry_adverse_flow`를 import하는 구형 shared-rebound 검사이며, 이번 변경으로 복원하지 않는다.
- 추가 전체 진입/부정 응답·전환 계약 검사: **25 passed**. 마지막 reader 증빙 보강 후 불변 릴리스에서 재검증한다.
- Python compile 및 공백 검사 통과. 문서 parser와 불변 릴리스 결과는 아래 배포 기록에서 확정한다.
- codec 250회 로컬 검사: p50 **0.439ms**, p95 **0.457ms**, 최대 **0.561ms**. codec 비용 측정이며 전체 장중 루프나 실제 provider 속도 개선을 뜻하지 않는다.
- 원 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689` 유지.
- 전환 manifest `8bd235a2e78d19f863cc77d44c03bfb24653858ebedbc792e3c84ebd9ee91e3c`.
- 실행 증빙: `data/report/auxiliary_compact_adoption/2026-10-08/`. 다음 영업일은 저장소 달력 기준 **2026-10-12**.

## 배포·자연 소비

15:15:23 KST에 첫 검증 릴리스 `main-aux-compact-20261008-v1`로 재기동했다(PID 232463). 15:15:25 bootstrap PASS, 15:20 자연 오류 감시 `no_alert`, 상시감시 5종목을 확인했다. 기존 15:10 정규장 신규 진입 cutoff 때문에 평가 시 기록되는 auxiliary 소비는 미관측이었다. 이를 정책 실패나 소비 성공으로 대체하지 않고, 기동 시 기존 reader 검증을 추가했다.

발행 전 재리뷰에서 [기존 PID 진단](main-pid-206123-post-warmup-latency-rest-ws-monitoring-2026-10-08.md)의 두 직접 결함도 확인하여 위 caller 연결과 native 종료 분리만 함께 수정했다. 별도 B3~B6 성능계획 전체를 구현한 것은 아니다. 83개 직접 회귀와 11개 기존 Main 호출 계약이 통과했으며 최종 통합/불변 릴리스 재검증 후 정책을 발행한다. PRE 자연 요청과 이후 장후/다음 기동은 시점이 도래하기 전에는 완료로 표시하지 않는다.
