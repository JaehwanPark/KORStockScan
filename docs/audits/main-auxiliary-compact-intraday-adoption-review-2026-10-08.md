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
| scanner outer drain이 fixed-watch 완료를 폐기할 수 있음 | 생성 시 확정한 generation kind로 native 완료를 기존 Main handler에 남김; cooldown 중에도 원 요청만 수집 | 실제 outer drain 분기→기존 commit, 원 상태 변경 시 거절, 단일 소비·bounded 완료 알림 보존 |
| async 연결로 고정감시에 scanner 전용 2초 transport 제한 유입 | fixed-watch는 기존 canonical quote age/설정 한도를 사용 | 정상 2.5초·만료 3.5초·미관측/미래 시각 검사; scanner 제한 유지 |

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

- 최종 불변 릴리스 관련 통합 회귀: **664 passed, 7 deselected** (`final-v3-immutable-tests.txt`). 제외한 7건은 이미 삭제된 `entry_adverse_flow`를 import하는 구형 shared-rebound 검사이며, 이번 변경으로 복원하지 않는다.
- 별도 Main 호출 계약 **11 passed**. 추가 native/async **130 passed**와 전체 진입·부정 응답 검사는 최종 664건에 포함되므로 합산하지 않는다.
- Python compile·공백 검사 통과. print-only 문서 parser 21건, 현재 Main owner 1개. 외부 Project/Calendar 동기화 미실행.
- codec 250회 로컬 검사: p50 **0.439ms**, p95 **0.457ms**, 최대 **0.561ms**. codec 비용 측정이며 전체 장중 루프나 실제 provider 속도 개선을 뜻하지 않는다.
- 원 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689` 유지.
- 전환 manifest `8bd235a2e78d19f863cc77d44c03bfb24653858ebedbc792e3c84ebd9ee91e3c`.
- 실행 증빙: `data/report/auxiliary_compact_adoption/2026-10-08/`. 다음 영업일은 저장소 달력 기준 **2026-10-12**.

## 배포·자연 소비

15:15:23 KST에 첫 검증 릴리스 `main-aux-compact-20261008-v1`로 재기동했다(PID 232463). 15:15:25 bootstrap PASS, 15:20 자연 오류 감시 `no_alert`, 상시감시 5종목을 확인했다. 기존 15:10 정규장 신규 진입 cutoff 때문에 평가 시 기록되는 auxiliary 소비는 미관측이었다. 이를 정책 실패나 소비 성공으로 대체하지 않고, 기동 시 기존 reader 검증을 추가했다.

발행 전 재리뷰에서 [기존 PID 진단](main-pid-206123-post-warmup-latency-rest-ws-monitoring-2026-10-08.md)의 두 직접 결함도 확인하여 위 caller 연결과 native 종료 분리만 함께 수정했다. 별도 B3~B6 성능계획 전체를 구현한 것은 아니다. 83개 직접 회귀와 11개 기존 Main 호출 계약이 통과했으며 최종 통합/불변 릴리스 재검증 후 정책을 발행한다. PRE 자연 요청과 이후 장후/다음 기동은 시점이 도래하기 전에는 완료로 표시하지 않는다.

15:31:05 두 번째 릴리스 `main-aux-compact-20261008-v2`의 bootstrap도 통과했으나, 15:31:14 다른 작업의 checklist 변경 후 `intraday_preserved_generation_changed`가 발생했고 15:31:32 기동 reader는 이를 정확히 거절했다. 당시 보조 overlay는 발행하지 않았다. 원 체크리스트 수정·기존 봉인/소비 영수증은 보존하며 마지막 릴리스는 최신 문서 바이트로 새 정식 인계를 생성한다.

후속 async 검증 **130 passed**. 더 넓게 실행한 scanner 종목 부착 검사 2건은 `SymbolOwnerPolicyError`로 실패했고, 수정 전 불변 v1 릴리스의 동일 두 검사에서도 같은 실패를 재현했다(`preexisting-scanner-test-baseline.txt`). 현재 변경의 회귀로 처리하거나 owner 보호를 해제하지 않는다. 전체 저장소 모든 검사 무결함을 주장하지 않는다.

### 최종 배포·발행 결과

- 최종 릴리스 `main-aux-compact-20261008-v3`, 코드 commit `dc769a09c052df06b265c7d9ce196428caae20ec`. 15:42 KST 재기동, Main **PID 241227**. 사용자 지정 15시 이후 조건 준수.
- **15:42:26 bootstrap PASS**, 15:43:05 실제 PID의 기존 128경로 reader 소비 확인. 기계 `consumed_exact`, 128 contract/48 operating scopes, 상시감시 5종목 유지.
- **15:43:19.344688 KST** 네 scope 단일 발행. overlay `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626`. 4개 변경/124개 기존 binding 보존을 원 PID baseline과 대조했다.
- 15:44:19 최종 handoff **PASS / findings 0**, selector와 Main cwd/commit 일치. Gunicorn PID 241341, 같은 최종 release, HTTP **200**. 최신 checklist SHA `ca53931ef8e47bfab9d387460a17b1993a00355f24e91b9b6a4f3ccc3afadaf2`를 봉인했다. 기존 영수증을 덮거나 문서 변경을 무시하도록 검증기를 완화하지 않았다.
- 15:44 기준 신규 overlay의 **실제 PID 평가 소비 및 첫 자연 AI 요청은 미관측**이다. 기동 시 읽은 기존 binding과 발행 후 새 binding 소비를 구분한다. 현재 15:10~16:00 진입 cutoff를 유지하며, 다음 실제 평가에서 hot reader가 소비한다. 강제 신호·주문·추가 재기동으로 관측을 만들지 않는다.
- 다음 장후/다음 영업일(10/12) 승계는 코드·회귀로 확인했고 실제 장후/다음 PID 소비는 아직 시점 미도래다. EOD/완료 장후를 재실행하지 않았다.
- 실행 증거: `data/report/auxiliary_compact_adoption/2026-10-08/deployment-observation.json`, `final-pid-baseline-consumed.json`, `publication.json`, `compact-v3-handoff_prepare.txt`, `compact-v3-restart.txt`. 연구 추가 호출 0·대형 원장 복제 0.
- 15:45:00 heartbeat에서 감시 **5** 확인. 15:45:07 자동 full detector는 최종 release를 소비했고 artifact/process/log 검사는 PASS, Telegram `no_alert`였다. `strict_checklist_generation_stale` 없음. cron에는 기존 `log_rotation_cleanup`/`postclose_finalization`의 06:50 이후 복구 이력 warning만 남아 있어 전체 severity를 무조건 green으로 표시하지 않는다(`final-natural-health.json`).
