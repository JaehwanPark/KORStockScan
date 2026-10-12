# 준비·전달 보완 후 잔여 병목·패턴 연구 리뷰 — 2026-10-12

## 최종 판정 — 10/13 07:00:37 복구 종료

**계획 보완·구현·신규6정의 등록·리뷰/수정 반복·승인 배포 완료.** 현재 불변 릴리스는 `main-residual-reviewed-20261013-v6` / `2223ac9e948cdbf79bf2ed1e1b6c4c5d7f069df6`다. Main은 원 EOD stop 이후 OFF이며 수동 기동하지 않았다. 기존32+신규6=38정의/128scope의 target13 candidate는 `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`, successor registry는 `4f6fcab1e40f45f84ad7c2614214366a8ec9c268d8fcfa5bdbd7530164c020c2`다.

- [현재 코드 gate](../../tmp/postclose-monitor-20261012/main-repair/current-release-review-gate-v6.json): 통합 선행1,952건 및 후속259·격리29·의미 감시275건 모두 PASS, 수는 겹치므로 합산하지 않는다. 현재53 source/test 해시·compile PASS·검토 범위의 미해결 code finding0이다. 4family의 현재 코드 fixture도 verified다.
- 전체 controller는 **06:56:33 done**, strict attempt `7d31d9768fc84ad5a5091a3c09af8809`이다. 활성7stage source/output/prerequisite issues0,4family current generation verified, cancel-wait의 summary/tower/checklist3 consumer verified다. [현재 전체 계약](../../tmp/postclose-monitor-20261012/main-repair/current-readiness-final-v6.json).
- 마지막 복구 최종화는 **07:00:37 실제 DONE**, cleanup·source12 full detector7/7·chain/snapshot/report 해시를 대사해 marker issues0이다. [최종화 검증](../../tmp/postclose-monitor-20261012/main-repair/finalization-verified-v6.json). 정규06:50 이후 복구이며 환경의 마감값을 바꾸지 않았다. 예정 상한 초과를 정상 시간 내 종료로 보고하지 않는다.
- cleanup 후 target13 `current_full_contract PASS·findings0`, 실제 PID 소비=false다. PREOPEN07:35/Main07:55의 설치 경로·release set은 verified이고 마지막 실제 PID/정책·인증/WS·정상 신호 수용은13 checklist의 기존 소유자가 확인한다. 기동 준비 PASS는 실제 기동/PID/성과의 증거가 아니다.
- 최종 의미 감시의 cancel-wait·stop·정책 생성 미해결 경고는0이다. 잔여 경고는 EOD `completed_with_warnings`(3종목 가격 결손),06:50 이후 복구, detector 실행 당시 살아 있는 최종화 ancestor의 self-audit 대기, 과거 로그 이력이다. 대형 미식별 원천1,403행·미확정 비용/결과는 source gap/null을 보존한다. 실제 경제성·전체 Main+장후 결합 성능을 이 결과로 주장하지 않는다.

복구 호출의 수탁 환경 누락 및 rising-missed의 적용일 기본값14 선택은 호출 결함으로 기록하고 각각 정규 환경 로더와 명시 publication12/effective13으로 바로잡았다. 잘못 만든14 정책/체크리스트는 [가역 감사 보존](../../tmp/postclose-monitor-20261012/main-repair/incorrect-effective14/archive-receipt.json)으로 현재 실행 소유자에서 제외했다. 원천일12·적용일13과 기존 주문/수탁/threshold/provider guard는 유지했다. 아래 시점별 진행/PASS는 역사 기록이다.

## 최종 의미 감시의 공유 데이터 경로 보완

v5 복구 최종화는06:20:39 cleanup·최종 detector까지 실제 DONE이고 세대 해시/13 준비 전체 계약을 통과했다. 다만 최종 artifact 감시가 릴리스의 공유 data 경로 문자열을 물리 원천 경로와 비교하여 cancel-wait·rising-missed·stop에 거짓 경고를 남겼다. 실제 원천과 현재 prepared 검증은 통과한 상태다. 데이터 독자는 물리 data 경로, 코드 세대 독자는 선택 release 경로를 유지하도록 보완하고 원본/공유 mount의 실제 consumer 회귀를 추가했다. 작업본275건 PASS 후 불변v6에서 동일 검증을 수행한다. 아래v4/v5 영수증은 각 시점의 기록이며 마지막 v6 최종화·준비·의미 경고 대사를 완료한 뒤 최종 판정을 기록한다.

06:09 복구 호출은 정규 라우터의 승인 수탁 환경을 전달하지 않아 `cancel_wait_current_custody_not_reconciled`로 거절됐다. 이는 호출 결함이며 계정/원장 값 변경이 아니다. `native_custody_environment`를 그대로 적용한06:15 재실행에서 같은 원 checkpoint·원장 대사는 findings0/verified_empty였다. 수탁 guard를 완화하거나 새 broker 사실을 만들지 않았다.

## 05:35 실제 최종화에서 발견한 후속 원천 정합성 수리

정규 최종화는05:35:01 시작해 controller05:36:01 done·cleanup 완료 후 `next_preopen_preparation_failed`로 멈췄다. 직접 이유는 `stop_vote_source_set_changed`다. cleanup이10/8 AI payload/prompt/request의 gzip 사본을 만들면서 보존된 원본과 같은 논리 원천을 두 번 발견했고, stop 감시의 파일 집합 hash가 바뀌었다. 이전 준비 PASS를 이번 최종화의 성공으로 재사용하지 않았다.

보유 투표 source adapter와 stop 감시기에 정규 원본 우선·원본 부재 시 압축본 선택을 함께 적용했다. 기존 request index의 실제 소비 경로와 watch의 선택 기준이 같으며 원본 변경/삭제·새 gzip-only 원천·외부 symlink는 계속 세대 재검증한다. threshold/provider/주문·수탁·budget/deadline 변경은 없다. 수정은 작업본과 불변v5 각각259건 PASS, 격리 재생29건 PASS·compile·diff PASS를 확인했다. v5 `1e24f044810c2b4e2074663a9c3e223ddef4d6c2`를 승인 CAS로 선택했고 Main 재기동은0이다. [v5 선택](../../tmp/postclose-monitor-20261012/main-repair/selection-v5.json), [영향 회귀](../../tmp/postclose-monitor-20261012/main-repair/immutable-cleanup-source-watch-regression-v5.log), [격리 재생](../../tmp/postclose-monitor-20261012/main-repair/immutable-replay-boundary-regression-v5.log). 현재 영향 스냅샷/stop·코드 결속·최종화를 복구 중이며 아래v4 PASS는 그 이전의 역사 영수증이다.

## 2026-10-13 후속 승인 구현 진행

사용자의 후속 구현·신규 패턴 등록·배포 승인에 따라 두 계획을 코드와 대조해 보완하고 구현했다. 아래 본문의 문서/연구만 수행했다는 표시는 10/12 당시 기록이며, 새 배포·준비·PID 수용과 구분한다. 통합 검증과 승인 배포를 완료했고, 마지막 인계 수리까지 포함한 불변 릴리스 `main-residual-reviewed-20261013-v4` / `ca8f298d7cf6ce0c427169a604b29f7c2fd51d73`를 native CAS로 선택했다. Main은 원 EOD stop 이후 OFF이며 수동 재기동하지 않았다. 현재 하류 인계와 13 준비를 재검증하며 05:35 최종화 감시를 유지한다.

- P0-A: 같은 시장 이름의 대소문자 비교, raw capture/revision 보존, call-local binding 실패 이유와 submit caller의 첫 terminal을 구현했다. 제공된 현재 provenance가 빈 경우 이전 stock PASS를 빌리지 않는다. sizing·quote·quantity·broker·custody guard는 각 owner가 계속 검증한다.
- P0-B/P1: entry typed deadline timeout과 공통 provider 실패를 분리했다. 기존5회·원5초·30/60/120/240/300초 대기, 새 적격 신호의 단일 generation lease, 미정산 future·늦은 응답·401/403/unknown 차단을 검증한다. 429 Retry-After의 더 긴 제한도 유지한다. heartbeat의 같은 PID/start receipt를 health에서 관측하며 reset/restart 권한은 없다.
- R1/R2/R4: ANY_MATCH 최소시간과 전체 branch 입력시간을 분리하고 long2 순환을 보완했다. 실제 depth item의 route/suffix·epoch/sequence를 이력에 보존하고 중복/결손을 계수한다. DB/native/target 편입 첫 실패의 receipt를 기존 cleanup/ACK 흐름에 연결했다. trace 준비 오류의 errno/파일명도 bounded 진단에 보존한다.
- 새 source/test는 기존 `src/engine/ai`, `src/engine/scalping`, `src/tests` 역할 경계에 두었다. 새 engine-root 모듈·별도 timer/worker·provider 연구 호출은 없다. 기존 장후 수리16파일과 다른 사용자 작업본을 보존한다.
- 공식 Kiwoom upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 현재 조회해 SDK/spec·0D item/FID·realtime/core/Postman과 대조했다. `kiwoom_docs` 부재를 기록했고 wire/FID/가격·수량 단위·시간·REG/REMOVE/auth/recovery는 변경하지 않았다. [조회 영수증](../../tmp/postclose-monitor-20261012/main-repair/kiwoom-official-reference.json).

### 신규 정의와 실제 합집합 비교

frozen 12파티션·636,041가격 행 중 적용4scope의182,699행을 기존과 candidate native State로 재생했다. 기존 branch의 같은-tick 출력 변화와 후보 정의 불일치는 **0건**이며 신규 typed signal165개를 확인했다. [native 검증](../../tmp/postclose-monitor-20261012/main-repair/native-parity.json). 추가 정의6개를 explicit 등록하고 native 기계/보조 owner가 발행했다. 04:12:46 기계 stage와 04:13:52 보조 stage가 succeeded·issues0으로 종료했다. 보조 stage를 현재 v4에서 다시 실행해 04:34:32 정상 종료했고 후보 bundle `8e0bd9516bffd59212dde4f5cadf904858ea18f81bcedc716e14a27861f571b9`의 release binding도 현재 commit으로 결속했다. 모든 수치는 과거 확인점이며 실주문·독립 거래·새 날짜 수익이 아니다.

| 범위 | 실제 scope OR 확정 승률 | 추가 WIN / FAIL / UNRESOLVED |
|---|---|---|
| 알테오젠 PRE NXT 고가 | 394/473 → 404/483 | 10 / 0 / 118 |
| 일반 AFTER SOR 저가 | 10/50 → 12/54 | 2 / 2 / 2 |
| 일반 PRE NXT 고가 H3 OR H14 | 6/6 → 10/10 | 4 / 0 / 10 |
| 일반 PRE NXT 저가 H6 OR H14 | 155/229 → 163/239 | 8 / 2 / 4 |

H14의 실제 조건은 DD0.4~1.2%이며 설명에 맞춰 다른 숫자로 바꾸지 않았다. FIRST hold는 native 원 anchor 가격 이상 유지 후 최초 실제 수신 확인점이고, source 단절·하회·확인 tick의 quote 결손은 거절한다. 동일 확인점의 복수 branch는 하나의 canonical opportunity다. base registry/기존 정의는 보존하고 successor registry에만 추가한다. 지정 초기 등록에 별도 EV/일수/미래 WIN gate를 만들지 않는다.

### 리뷰 중 추가 보완

확대 sizing 검증에서 기존 배포본에서도 `/proc/self/stat`의 미기록 파일 읽기로12건 실패하는 것을 재현했다. 격리 정책 재생이 진단 모듈을 sandbox 안에서 처음 import하던 결함이다. 관측 모듈을 먼저 초기화하고 telemetry만 비활성화하여 frozen 거래 입력·RecordedServices의 미기록 read/write/network/DB 거절을 유지했다. SCANNER의 실제 fresh WS 경로와 NXT/SOR fixture의 독립 REST 결손을 구분하도록 시험의 오래된 기대값도 정정했다. 원천 결손을 완성 quote·실제 fill로 바꾸지 않는다.

### 검증·등록·배포 영수증

- 통합 변경은 작업본과 불변 릴리스에서 각각 **1,194건 PASS**다. 이후 공통 provider 실패 우선순위 보완205건, M terminal의 selection_basis 결손 및 진단 실패의 원 finalize 결과 격리239건, 요약→체크리스트 연결110건을 영향 범위별로 다시 검증했다. 이 수들은 겹치므로 합산하지 않는다. [통합 검증](../../tmp/postclose-monitor-20261012/main-repair/immutable-regression.log), [후속239건](../../tmp/postclose-monitor-20261012/main-repair/immutable-v3-regression.log), [최종 인계110건](../../tmp/postclose-monitor-20261012/main-repair/immutable-summary-regression-v4.log).
- 원천이9/9라도 stop 정책의 native 코드 결속이 실패하면 summary는 incomplete다. checklist reader가 이를 파일 census 불일치로 거절하던 결함을 수정했다. blocker가 남은 complete는 여전히 거절하고 runtime apply=false를 유지한다.
- 신규 등록 receipt `ba0f5632fed0d99a4fb11b3333e28c0b04866f7dbf2def99e75074e78aa347a5`, successor registry `4f6fcab1e40f45f84ad7c2614214366a8ec9c268d8fcfa5bdbd7530164c020c2`다. 기존32+신규6의38개 정의·128scope를 다음 기동 후보로 결속했다. [등록 원본](../../data/runtime/mechanistic_entry_policy/residual-registration.json). 이전106요청/40완료/66계획은 별도 역사 비교 세대로 보존했고 새 provider 요청은0이다.
- 배포 CAS verified, 선택 commit `ca8f298d7cf6ce0c427169a604b29f7c2fd51d73`, 실제13 PID 소비=false. [릴리스 source 해시](../../tmp/postclose-monitor-20261012/main-repair/release-build-v4.json), [선택 영수증](../../tmp/postclose-monitor-20261012/main-repair/selection-v4.json). workspace HEAD/index와 다른 사용자 파일은 보존했다. 새 source/test는 역할 패키지에 두고 기존 engine-root reader만 수정했다.
- 현재4family fixture163건 PASS를 같은 코드 generation에 결속했다. [fixture](../../tmp/postclose-monitor-20261012/current-fixtures-main-v3/generation-fixture-validation.json). 장전/장중 자연 수용은13 checklist의 `DirectFamilyPreopenPolicyHandoff`, `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`로 각1개 현행 owner다. 신호 미발생·회로 미발동은 pending이며 테스트 성공으로 닫지 않는다.

최종 선택 v4에 후속 수정50 source/test와 관련30 test 파일을 결합해 **1,952건 PASS·실패0·compile50건 PASS**를 확인했다. 경고1건은 기존 pandas_ta의 Pandas4Warning이다. [현재 배포본 통합 회귀](../../tmp/postclose-monitor-20261012/main-repair/immutable-combined-regression-v4.log), [현재 코드 gate](../../tmp/postclose-monitor-20261012/main-repair/current-release-review-gate-v4.json). 검토 범위의 미해결 코드 finding0이며 자연 PID·경제·결합 성능은 이 gate에 포함하지 않는다.

### 최신 native 인계와 다음 기동 준비

활성7 stage의 현재 source/output/prerequisite 검증 issues는 모두0이다. 원천일12의 전체 controller는 **10/13 04:35:57 `done`**, whole-native-chain strict PASS다. [인계 영수증](../../tmp/postclose-monitor-20261012/main-repair/native-core-handoff-v4.json). 검증 attempt는 `13e01ccb390d477e8b206727f857c0d9`이며 이전23:26 PASS를 최신 배포의 증거로 쓰지 않았다.

10/13 준비는 v4 selected commit·등록38정의·새 후보 bundle에서 `prepared_verified`로 다시 생성됐고 **current_full_contract PASS·findings0·actual_pid_consumed=false**다. [준비 전체 재검증](../../tmp/postclose-monitor-20261012/main-repair/prepared-current-contract-v4.json). 설치 cron·release set·PREOPEN07:35/Main07:55/finalize05:35 routing은 각 native print-only 검사로 확인했다. 실제05:35 cleanup·최종 detector terminal은 아직 미도래이며 [현재 감시](../../tmp/postclose-monitor-20261012/finalization-main-v4-waiting-state.json)에 별도로 남긴다.

최종화 종료 후의 영수증과 준비 전체 계약을 이어서 재확인한다. 실제07:35/07:55와 경제성은 미래 수용이며 현재 단계에서 완료로 표시하지 않는다.

## 1. 결정

[상세 보완계획](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md)을 작성·리뷰하고 기존 누적 원천의 수동 가설 연구를 실행했다. **우선 보완은 mixed branch의 장기 슬롯 배정, 0D 이력의 거래경로 메타데이터, probe→Main 편입 실패의 상세 증빙**이다. 계획·격리 연구만 수행했으며 운영 코드/정책·배포·재기동은 변경하지 않았다.

기계 ENTER_NOW 부족을 전체 경로의 원인으로 고정하지 않는다. 18:30 실제 재기동 이후 상시 ENTER_NOW122와 worker PASS31이 있으며 비상시는 source 부족과 편입 종료가 별도 병목이다. 같은 프로세스·단계·시각과 원 기록의 집계이며 실주문/독립 거래·실현 수익 건수가 아니다.

## 2. 현재 실행과 확인한 결함

[18:30 예약 실행](../../tmp/main-machine-status-20261012-1830/result/snapshot.json)은 18:30:00.683 KST에 `native-readiness-20261012-v2` / `cf650549e7a07ed470cd95a500af43336d31232c` / PID1215171·start4182334를 확인했다. 수집 전후 selector/PID 안정, 로컬 집계 source gap 없음, service exit0다. 이 수집 성공은 거래 원천 715건이 정상으로 회복됐다는 뜻이 아니다.

| 발견 | 근거 | 보완/구분 |
|---|---|---|
| legacy0초+rolling60/120초인 mixed scope가 long 배정을 받지 못함 | [실제 queue 격리 재현](../../tmp/main-machine-remediation-research-20261012/mixed-residence-reproduction.json): 5개 모두60초·long0 | any-match admission과 branch coverage에 필요한 long 기회를 분리. 슬롯5/long2 유지 |
| exact 0D quote는 존재하는데 수신 count0 | [생산자 형식 재현](../../tmp/main-machine-remediation-research-20261012/depth-metadata-reproduction.json): route없는 history count0, 합성 정상 metadata count1 | WS depth builder/append→probe counter의 `market_route` 계약 결손. source/API 미수신으로 오표시하지 않음 |
| probe ENTER9 중 Main 편입 거절7 | [exact capture 인계](../../tmp/main-machine-remediation-research-20261012/probe-enter-main-handoff-trace.json): committed2/generic finalize 실패7 | native/target/DB 중간 실패 조건의 receipt를 보존. DB 장애/주문 실패라고 단정하지 않음 |
| 잠정 PASS3은 모두 Main 정상 소비 후 guard 종료 | [17:15 exact 진단](../../tmp/main-machine-remediation-research-20261012/exact-residual-diagnosis.json): `commit_allowed`3 → weak pullback2/sizing contract1 | 이 세 건의 PASS 소비는 연결됨. 뒤 guard와 경제성은 별도 owner |
| 비상시 source715/838 | route snapshot370·0B 없음182·0B age157·기타6 | quiet·정확 REG/수신·native publish·stale 시계를 결속해 첫 단절 점검 |

17:15의 window 부족5는 모두 원60초 lease이고 legacy minimum0과 long branch60/120이 공존한다. 다만 terminal의 continuous coverage는 source stale로 unknown인 경우도 있어, 그 다섯 건을 슬롯 배정 하나의 원인으로 설명하지 않았다. native FALSE 표시2도 0D count 증빙이 없어 기존 no-match verifier를 통과하지 못했다. 현재값을 과거 history로 채워 성공 처리하지 않는다.

## 3. 연구 원천·계산·반례

- 9/29·30, 10/2·6·7·8의 **12개 PRE NXT/AFTER SOR 파티션·636,041개 가격 행**. 모든 해당 보유 종목을 처리하고 삼성·다른 fixed4·일반 종목/가격대·route/market을 구분했다. 9/29 이전 자료는 연구 순위에 합산하지 않았다. REGULAR은 이번 연구에 포함하지 않았다.
- 현재 적용 bundle `f7c1454a71b284a25c40a157ea4f42f390ecc5c21f362d76f497c49bf41ec2b1`의 실제 branch payload로 isolated native State를 재생했다. 이전 연구의 incumbent bit로 current baseline을 대신하지 않았다. 모두 pure instance이며 live `_STATES/_CLAIMS`, Provider·order consumer를 변경하지 않았다.
- 실제 확인 ask부터1800초·cost.0023·순 목표+.4%/soft−3%의 native label과 같은 item 완료 분봉을 사용했다. WIN/STOP/완전 TIMEOUT/UNRESOLVED를 분리하고 10분 이후 원 가격 자료도 해당 계약 안에서 소비했다. 선행 source epoch/sequence 단절은 신호에서 이어붙이지 않았다.
- 최초6가설, flow/volume/BUY 특징의 고정6보완, 가격 경로만 쓰는 고정4후속, 총16개다. [단계2](../../tmp/main-machine-remediation-research-20261012/phase2/result.json), [단계3](../../tmp/main-machine-remediation-research-20261012/phase3/result.json). 그 단계의 뒤 날짜에 새 WIN이 없다는 상태와 실제 승률 악화는 다르므로 최종 선별을 누적 목적에 맞췄다. 성공100%/80% 보존·추가 일수/EV gate는 사용하지 않았다.
- [특징 적격성](../../tmp/main-machine-remediation-research-20261012/phase2/feature-eligibility.json): H5 root에서9,038개가 ret/VWAP 등 unknown으로 제외됐고 그중1,735개에 WIN 라벨이 있다. 이 수는 조건 match나 독립 거래가 아니다. 특징 결손을 패턴 부재로 혼동하지 않도록 별도 공개했다. 가격 경로 가설은 해당 선택 특징을 요구하지 않는 새 정의이며 기존 execution source/guard를 느슨하게 하지 않았다.

현재 baseline source_date도10/8이고 연구가 여러 차례 같은 자료를 봤으므로 이를 미관측 독립 미래 검증이라 부르지 않는다. 후행 분할은 재생 비교이며, 선정 후 미래 실적과 실제 AI·Main 소비·손익은 미입증이다.

## 4. 등록 제안

[최종 등록 제안 JSON](../../tmp/main-machine-remediation-research-20261012/cumulative-registration-proposals.json)에 **6개 후보/4개 scope**와 정의·원 결과 hash·parent bundle·단독/기준/OR/추가 W/F/U·목표 시각 집중·뒤 날짜 상태를 보존했다.

| scope | 후보 | 기존 → OR 누적 | 추가 W/F/U |
|---|---|---|---|
| 알테오젠 PRE NXT 고가 | H9 얕은 반전1초+BUY60 | 394/473 → 404/483 | 10/0/118 |
| 일반 AFTER SOR 저가 | H6 DOWN 반전3초 | 10/50 → 12/54 | 2/2/2 |
| 일반 PRE NXT 고가 | H3 상승구조 고점돌파 | 6/6 → 8/8 | 2/0/10 |
| 같은 PRE 고가 | H14 가격 반전1초 | 6/6 → 8/8 | 2/0/0 |
| 일반 PRE NXT 저가 | H6 DOWN 반전3초 | 155/229 → 156/230 | 1/0/0 |
| 같은 PRE 저가 | H14 가격 반전1초 | 155/229 → 162/238 | 7/2/4 |

H3/H14와 H6/H14는 각각 같은 scope에서 겹칠 수 있으므로 후보 수·추가 WIN을 합산하지 않는다. 실제 OR portfolio는 구현의 정확 확인점 합집합으로 비교한다. 표본/목표 시각 집중이 크며 등록 제안은 장후 선택·PID 소비·실행 수익이 아니다. 다음 날짜의 무신호를 추가 채택 실패/대기일 조건으로 만들지 않는다.

삼성의 이번 PRE/AFTER 후속 가설에는 추가 확정 WIN이 없다. 이는 두 시장·해당 날짜·해당 정의의 결과이며, 삼성 전체 상승/REGULAR 기회 부재나 실제 손실을 뜻하지 않는다. 이번16가설의 종료와 다른 연구 가능성은 별도다.

## 5. 리뷰·검증·권한

- mixed descriptor min과 actual queue 할당, depth builder/reader 형식, incomplete/normal-FALSE의 source 증빙을 검토해 상세계획을 보완했다.
- 10/8의 valid-empty를 후보 탈락으로 쓰던 조건을 재검토하고 누적 승률·추가 기회로 최종 제안을 작성했다. 원 단계 결과는 보존했고 새 제안에 결과 hash·선별 기준을 기록했다. 독립 미래 성과나 새로운 raw로 포장하지 않았다.
- 표적 pytest13건·compile·current native family validator PASS. [라벨 재계산](../../tmp/main-machine-remediation-research-20261012/validation.json)120개(WIN40/STOP20/TIMEOUT20/U40) 불일치0, frozen source/code/cache SHA와 exact item/epoch/sequence/ask identity를 확인했다. 1차 test 파일명 충돌은 importlib collection으로 해결했으며 실행 회귀는 모두 통과했다.
- 실행은 temp offline 도구만, 한 계산 thread/nice19/주소공간2GiB·CPU480초 상한이다. 가격·API 수집 확대, provider 연구 호출, runtime policy/registry·bot/주문·수량·custody·hard safety·episode/widget 경계의 변경은0이다. 타 세션 작업본과 sealed checklist를 수정하지 않았다.
- 문서 로컬 링크29개·owner/authority·공백, print-only parser19항목, 임시 Python compile·`git diff --check`와 원천/code/cache 해시35개를 확인해 리뷰를 닫았다. 당일 sealed checklist 원 해시는 유지했다. full Main/장후 동시 성능·실주문·실현 PnL 검증은 이번 결과가 아니다.

다음 구현 순서는 **R1 mixed 배정·R2 depth metadata·R4 Main 편입 receipt → exact root parity/후보 등록·scope OR 비교 → 기존 선택/지정·소비/자연 점검**이다. Root FIRST_PRICE_HOLD가 미지원이면 연구 계약과 같은 구현을 먼저 준비한다. 지정 초기 채택에 새 경제성/일수 gate를 추가하지 않는다.
