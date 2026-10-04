# Entry setup family/state 원천 수리·별도 역사 복구 소비 리뷰

## 1. 처분

사용자 다음액션 지시와 [수리계획](../proposals/entry-setup-family-state-source-repair-plan-2026-10-04.md)을 실행했다. producer의 family/state 결함을 고쳤고, 10/2 08:33 관측의 별도 복구 receipt를 실제 uncached 장후 consumer에서 격리 소비했다. **기본 관측5→복구포함6, 기존5개 행 불변, 원watch2개 불변, 복구 판정RECHECK 유지**다.

복구는 운영 후보 확보가 아니다. 아래 가격 결과는 기존 완료 분봉의 경로 CF이며 주문·체결·실현 손익 증거가 아니다. 정책·원archive·기존projection·선행연구 generation을 변경하지 않았다. 배포·재기동은 실행하지 않았다.

## 2. 원천·정책·producer 정합성

- 원archive: `data/ai_decision_payloads/ai_decision_payloads_2026-10-02.jsonl`의 실제318행, `2026-10-02T08:33:18.566416+09:00`.
- canonical trace: `99fdbcdb09830ca95bf617f143c20c09161c37d43ae209a0d86fcdb0564374d1`.
- 원bundle: `6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87`.
- exact parent: `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE`, SHA `656cfd8e824f3135c8a5c7f47ece789a9c1837f53e72355d298fa2602f05b011`.
- 원canonical/raw hash 정상. 단일 검증 오류는 `entry_setup_family_state_inconsistent`였다.

| 항목 | 원capture | 수정 producer 재계산 |
| --- | --- | --- |
| family | NO_VALID_SETUP | NO_VALID_SETUP |
| setup/execution state | WAIT_CONFIRMATION | UNCONFIRMED |
| recheck grammar | DISCOVERY + TRIGGER | SETUP_DISCOVERY_RECHECK |
| local-breakout 확인 요청 | true | true |
| 최종 machine | RECHECK / local_breakout_confirmation_required | 동일 |
| validator | family/state 오류1개 | 오류0개 |

실제 재계산은 `setup_state`, `execution_readiness_state`, `recheck_reasons`, `evidence_sha256`의 **4필드만** 변경했다. 원raw 입력·구조phase·micro·liquidity·risk·identity·원정책의 threshold는 불변이다. strict validator는 완화하지 않았다.

같은 branch가 MICRO_RECOVERY에 TRIGGER reason을 추가해 그family의 단일 MICRO grammar를 깨뜨리던 경우도 고쳤다. supported family는 WAIT/TRIGGER를 유지하며 INVALID/INSUFFICIENT와 hard BLOCK 우선순위를 보존한다. local-breakout 확인 전 ENTER 승격은 허용하지 않는다.

## 3. 별도 복구 receipt와 마지막 소비자

새 helper `src/engine/scalping/entry_setup_source_repair.py`는 원capture canonical/raw, 원bundle exact parent, 실제archive physical SHA/행번호, 현재6개 kernel, 재계산 evidence/판정/4필드 변화, 오프라인 권한을 묶는다. 추가 오류·불일치·변조·stale kernel·새ENTER 및 실주문/provider 원천을 거부한다. 행번호를 바꾸고 receipt를 재hash하는 경우도 실제 원문 대조로 거부한다.

`ai_action_outcome_calibration._load_machine_observation_rows_uncached`에 명시적 `source_setup_repairs` 인자를 추가했다. independent/no-fetcher 경로만 허용하며 복구 proof를 row에 남긴다. 원capture와 그identity는 새 working evidence와 별개로 유지된다. **public cached loader는 repair 인자를 전달하지 않는다.** 기존 malformed capture의 기본 제외 계약도 유지된다.

이번 actual CLI intake는9/29·9/30·10/2, 삼성전자 장전 scope만 대상으로 했다. 보유 자료를 read-only로 읽고 결과는 새 `tmp` generation에 썼다. 기존 file/정책 writer나 API/provider를 호출하지 않았다. 정상원capture 선정5개와 복구포함6개를 같은 label/cost owner로 비교해 기존5개 행의 dictionary 전체 일치를 검증했다.

### 3.1 가격 cache 분모 보완

최초 `cold/warm`은 부분군6개의 manifest로 전체 관측용 완료 가격 cache를 조회해서 가격을 재사용하지 못했다. 그 generation의 null 결과는 격리 adapter의 분모 효과다. **최종 증거는 `final-cold/final-warm`**이며 초기출력은 폐기된 진단 generation으로 보관한다.

최종 CLI adapter는 원전체 유효 canonical을 재현하고 기존 cache owner 검증을 통과한 배치를 소비한다.9/30 원분모2,065개,10/2 원분모2,309개 및 각 원manifest/content hash를 확인했다. 각 배치에서 삼성전자 exact `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE|005930_NX` 완료 가격50행만 가져왔다. `_AL`이나 다른venue/session을 섞지 않았다. 두batch의 상태는 `verified_cache_reused_partial_source_gap`; 전체batch의 deferred-route 결손은 남아 있다.

원전체batch 검증 후 부분군을 소비하는 **CLI 전용 report-only adapter**다. 원cache 재봉인/운영 population 증빙 대체는0이다. 이검증을 운영 캐시 장애나 모든route 정상의 증거로 사용하지 않는다. 전체pipeline의 probe counters도 이번2watch의 거래/기회 수로 해석하지 않는다.

## 4. 복구 관측의 비용·가격 결과

| 결과 | 값/해석 |
| --- | --- |
| 원capture 비용 | null 유지 |
| 장후 비용 owner | 기존exact NXT 경제성 원천·source-bound estimate |
| 설정 왕복 비용 | 0.23% |
| 가격 마찰 포함 실행비용 추정 | 0.32075%=0.015%매수+0.015%매도+0.2%세금+0.09075%마찰 |
| broker 대사 비용 | null, 실현 경제성 미입증 |
| 경로 target | 순edge0.1%+비용0.32075%=gross0.42075% |
| stop 거리 | 기존−0.7%, 변경0 |
| 3분 경로 | 3관측·MFE0%·MAE−0.181488%; target/stop 미도달 |
| 10분 경로 | 10관측·MFE+0.181488%·MAE−0.181488%; target/stop 미도달 |
| binary label | neither_hit / CENSORED_OR_SOURCE_GAP, 적격false |

비용null을 0으로 채우지 않았다. 기존원천 owner가 계산한 비용 추정과 원capture의 null 및 broker 대사 결손을 구분했다.10분 최대상승+0.181488%는 이row의 gross target+0.42075%를 충족하지 못한다. 미도달은 손실/실패0으로 바꾸지 않으며 확정된승률·PnL을 만들지 않는다.20/30/60분의 이 장전 scope 결과도 pending/source-gap이다.

복구 후 기존08:13 target-first1건과08:36 stop-first1건은 유지되며, 추가 관측은 새로운 target-first를 만들지 않는다. native는9/30과10/2의 같은 MAIN_FIXED_WATCH admission/generation2개다. 관측6개를 독립기회6개로 늘려 세지 않는다.

## 5. 리뷰·수정보완·검증

리뷰 보완: unsupported family state 오염 제거, MICRO reason 중복 방지, 원scope/identity/raw/parent/판정 불변 검사, archive 실제행 대조, stale/변조 receipt 거부, provider/AI join 경로 제한, 원전체가격cache 분모 검증 후exactroute subset 소비, 기존5개 행 불변 검증이다. 마지막 실제 소비까지 확인했고 리뷰 범위 내 미해결 구현 결함은0이다.

최종 표적4suite **446 tests PASS**, compile PASS, diff PASS. 신규receipt/consumer/가격adapter 회귀25개를 포함한다. 독립 두 최종실행의 result bytes 및 모든검증hash 일치를 확인한다. 원천 의존22개 physical seal을 각 실행 전후 검증한다.

선행180 source/kernel seal 중 승인된 production2개(`entry_setup_evidence.py`, `ai_action_outcome_calibration.py`)는 before snapshot과 old/new ledger를 남겼다. **나머지178개 source/kernel과98개 정책/handoff는 보존**한다. test 수정도 before snapshot에서 추적한다. 과거closure는 당시kernel의 역사receipt이며 새코드의180seal PASS로 표시하지 않는다. 원10/3 dirty checklist·10/6 checklist의hash를 보존한다.

근거: [최종result](../../tmp/entry-setup-source-repair-20261004/final-cold/result.json), [재실행](../../tmp/entry-setup-source-repair-20261004/final-warm/result.json), [현재 closure](../../tmp/entry-setup-source-repair-20261004/validation/closure.json), [before baseline](../../tmp/entry-setup-source-repair-20261004/baseline.json). 문서link/owner 및 print-only parser로 현재소유자 `EntrySetupSourceRepair1004`를 닫고, 기존future OPEN owner24개를 유지한다.

Kiwoom 요청/응답 parser·FID·continuation·인증·주문 protocol 변경0으로 upstream reference gate는 이번수리에서 적용되지 않는다. 전체매매suite·정책 발행·장후 자동화·배포/PREOPEN/PID·자연기동·실현 경제성 검증은 이번원천수리 scope에 포함하지 않았다.

## 6. 후속 경계

source grammar와 격리 역사복구 소비는 완료했다. default 장후 생산에 이receipt를 자동등록하지 않았으며, 이번복구를 근거로 신규policy를 발행하지 않았다. 작업본 변경과 live 적용은 별도다. 이후 연구는 **원watch/조건을 고정한 추가 독립날짜 검증**이 소유하며, 기존 `SamsungFrozenCandidateValidation1006`을 새장전 후보의 owner로 확대하지 않는다. 기존원천에서 확인하지 못한 비용후 성공을 복구 성공으로 대체하지 않는다.
