# Entry-split 검증 projection·Main 신호 전달 구현 리뷰 — 2026-10-14

사용자는 [보완계획](../proposals/entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md)의 리뷰·구현·반복 수정과 완료 후 배포·Main 재기동을 승인했다. 현재 소비 릴리스 `f8dc4431d0b3cc2cb84610979ec4f3440d3e8e46`에서 격리해 구현했으며, 기본 작업공간의 다른 미커밋 변경은 보존한다. 이 문서의 코드 수용과 실제 배포·PID·자연 성능은 별도 증거다.

## 1. 구현과 발견한 결함의 수정

- 기존 native report/policy validator를 bounded worker에서 실행하고 작은 projection/receipt/최종 atomic manifest를 발행한다. managed data root의 정확한 family/date alias·불변 generation·정책을 대사한다. source byte SHA와 semantic generation을 구분하고 source identity/ctime·fd·부모 경로·code/role·작은 내용 해시를 결속한다.
- 512MiB 초과 원본은 임시 사본에서 JSON 문자열 밖의 연속 ASCII 공백을 한 개로 줄여 검증한다. 원 공백을 전부 지우면 `1 2`가 `12`로 치유되는 반례를 찾아 보완했다. duplicate key/nonfinite/truncated/잘못된 토큰은 실패하며 alias와 불변 원본의 full native 의미를 순차 검증한다. 원 파일/정책 bytes는 변경하지 않는다.
- worker는 부모 wall timeout, 자식 주소공간/CPU, 입력/출력·디스크 예산을 사용한다. 부모가 임시 디렉터리를 소유해 강제 시간 종료 후 잔류를 정리한다. 같은 검증 세대는 이미 검증된 receipt를 재사용하고, 원천·작은 산출물·검증 코드 변경은 무효화한다.
- `submission_bottleneck_monitor`는 verified projection만으로 큰 보고서를 관측한다. 작은 기존 보고서는 기존 native 검증을 유지하고 큰 파일의 proof 결손에서 full parse로 fallback하지 않는다. bootstrap PASS와 별개로 미검증 축은 partial이다.
- 검증 뒤 정책을 다시 읽던 경합과 summary의 선행 정책 SHA 읽기를 제거했다. reader의 정확한 작은 policy snapshot과 SHA를 사용한다. row/holdout의 scalar/count/collection·null을 정규화하고 source_gap·비활성 후보·기존 설치·PID 미입증을 보존한다. summary의 장후 full byte SHA 읽기는 유지되며 warm monitor 절감으로 보고하지 않는다.
- Main의 ready hint를 정렬 시점에 소모하던 경로를 실제 방문 토큰 ACK로 바꿨다. 동시 발생한 새 토큰은 보존한다. 이미 방문한 WATCHING의 새 신호는 같은 pass에서 한 번 재편입하며 COMMIT/HOLDING/EXIT 보호 위치와 혼합 순환·기존 accounting 모집단·native 단일 claim/lease·원5초를 유지한다.
- 기존 배치 진단에 bounded phase 이력256개와 최대32개 구간, 미관측/잘림 상태, 실제 remaining/reserve/override 및 capture/executor/SDK 시간과 실제 future settlement를 기록한다. 선택적 observation이 없는 settlement 반례도 보완했다. provider/주문·thread·quota를 추가하지 않는다.
- compact 등록 요청의 동일 논리 schema 중복 생성을2회에서1회로 줄였다. schema equality와 provider 전 계약 검사는 보존하고 outgoing wire 동등성과 변조 차단을 확인했다.

## 2. 원 owner·정책·권한 보존

`entry_split_order_plan.py`의 파일 전체 hash는 과거 probe 가격 커널에 결속돼 있다. 발행 hook를 그 파일에 넣으면 과거 재생을 불필요하게 무효화하므로 native 파일은 현행 release와 byte 동일하게 유지했다. SHA256은 `ed738295a7de91c3972c8360b655d222b26f69e4d1976b2ef27c2c0f0e660c5c`다. 기존 장후 wrapper의 정상 생산/최종 handoff 복구 지점에 bounded 검증 발행을 연결했고 trusted data mount를 한 번 canonical 경로로 해석한다. 기존 정상 publication의 서식 처리와 새 source 불변 migration은 다른 단계다.

기존 기계 bundle·128scope membership·현재 auxiliary common-support overlay·모델/프롬프트·원 native5초·bootstrap 원 정책/PREOPEN/env·Main/manual custody와 매매 가드를 보존한다. projection은 report-only이며 runtime policy가 아니다. code handoff는 정확한 원 PREOPEN→후보 source pair로만 허용한다. 기존 `DirectFamilySourceRepairEntrySplit`, `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`, `DirectFamilyPreopenPolicyHandoff`에 수용을 연결하며 새 경제성/성공 보존 gate를 만들지 않는다.

## 3. 반복 리뷰와 표적 검증

독립 리뷰와 자기 리뷰로 primitive 토큰 치유, 반복 발행 충돌, timeout 임시파일 잔류, 원본/정책 경합, 숫자 집계 누락, source kernel 전체 hash 부작용, 공유 mount 해석, 배포 전 정책 확인·문서 CAS·code gate 근거 고정을 점검하고 수정했다. 현행 native 모듈·원 정책과 후보 변경을 함께 검토했다.

표적 검증 로그는 `/home/ubuntu/KORStockScan/tmp/entry-proof-latency-evidence-20261014`의 `latency-integration-tests.log`, `projection-integration-tests.log`, `deployment-tests.log`에 고정하며 마지막 source hash와 결과는 `final-gate.json`에 결속한다. 지연7suite579개, projection/native/소비자/wrapper6suite567개, deployment/router/bootstrap/readiness/detector6suite1072개가 통과했다. 마지막 metadata read 경합 반례2개와 원 생산자 증빙을 포함해 `projection-final-tests.log`에서567개를 재검증했다. Python compile, `bash -n`, diff 검사가 통과했다. 문서 로컬 링크66개·기존 owner4개의 단일 소유와 AUTO bytes 보존을 확인했고 print-only parser는25항목을 파싱했다. 성공 시험의 중복 실행 수를 고유 시험으로 합산하지 않는다.

3회 교차 비교는 같은 workload에서 helper 추가 비용 약14µs/pass를 보였다. 기존 registered 준비 출력은 같았고 schema 생성 횟수는2→1이었다. 약0.717초 전체 전처리 감소나 전체 Main p95 개선을 입증한 결과는 아니다. 13:36 시도의3.105초 내부 원인은 기존 기록으로 미식별이며 새 phase 증거로 후속 수용한다. `provider_total_ms=765`는 서버 처리시간으로 해석하지 않는다.

## 4. 실제 이관·배포 수용의 증거

검토한 코드 범위의 미해결 결함이 없는 상태에서만 실제438MiB alias/514MiB 불변 원본의 bounded cold 검증을 수행한다. native 검증·값/byte 불변·peak RSS/wall/read bytes·작은 projection 크기·새 프로세스 warm full read0를 기록한다. 원 경제성 source_gap·candidate inactive·기존 incumbent 설치는 그대로 보고한다. 자원 실패나 native 불일치에는 원 데이터를 보존하고 기술 검증을 PASS로 만들지 않는다.

승인된 배포는 reviewed immutable candidate에서 delay/stop/holding-vote preflight와 active code handoff를 검증한 뒤 기존 ordered transition을 사용한다. release-set/detector/Sentinel 잠금·문서 CAS·원 정책 hash를 대사하고 graceful drain→선택/문서 발행→native 준비→정규 기동→singleton successor PID/start/cwd 실제 소비를 확인한다. 기존 보조 overlay 발행은 반복하지 않는다. 실제 결과 owner는 `data/report/entry_split_latency_deployment/2026-10-14/deployment-result.json`과 해당 `data/runtime/release_transitions/2026-10-14/<commit>/status.json`이다. 회귀·기동 수용으로 자연 신호/경제 성과를 주장하지 않는다.

배포 이후의 정상 예약 관측에서 size-limit 해소와 원 상태·새 PID의 실제 기계/보조 시도 및 지연을 확인한다. 자연 표본 부재는 pending이며 실주문이나 provider replay를 시험 목적으로 만들지 않는다.

## 5. 실제 이관·기동과 routed mount 추가 반례

첫 구현4e21d783e의 실제 검증은 alias/immutable full native PASS,66.66초/peak1,884,928KiB, projection7,017B, fresh process warm13.528/13.576/13.549ms·fullreportread0이었다.14:24:53 실제PID547164/start1938099/cwd entry-proof-latency-20261014-4e21d783e/src와 정책 소비를 검증하고 보호 정책11개 hash를 보존했다. 증거는 `data/report/entry_split_latency_deployment/2026-10-14`와 해당 첫 transition receipt다.

14:25 예약 실행에서 first source-only consumer의 `release/data` raw 경로가 managed canonical 경로와 달라 `managed_source_path:report_alias`가 발생했다. 이 실패를 기술적 검증 완료로 합치지 않는다. consumer의 trusted data mount만 초기에 resolve하는 최소 수정과 실제 migrated native proof+release/data symlink를 통한 whole consumer 반례2개를 추가했다. 수정 전2실패, 수정 후 관련 suite·코드 인계 source pair를 검증한다. 자식 symlink/data root 탈출 검사는 유지한다. 이 추가 수리는 monitor/H exact pair/시험/문서만 변경하며 helper/native report/policy/Main 기계·보조 로직은 첫 검증 bytes 그대로다.

두 번째 코드 gate·배포/PID·정상 예약 관측 증거는 `data/report/entry_split_latency_pathfix_deployment/2026-10-14`와 `tmp/entry-proof-pathfix-evidence-20261014`가 소유한다. 첫 배포의 frozen evidence는 수정하지 않는다. 전체 Main 자연 지연 목표/경제성 source_gap은 별도 수용이다.

## 6. 재기동 진단 순서 추가 수리

14:36:49 최초 detector가 launcher 최종 record-pid/consumed보다 먼저 실행되어 historical checklist의 소비 검증을 거부했다. 재검증 issues=[]는 원 최종화 증거의 유효성만 입증하며 순서 수리의 완료가 아니다. source-only 재생성 없이 첫 full sweep의 정확한 native PID/start/manifest/consumed/selector 영수증 장벽, 시작부터150초 한도·heartbeat·실패 노출, 선택된 immutable router의 최종 record-pid로 수리한다.

이전 Sentinel의 partial은 ordered publish가 캡처한 dated artifact bytes/mtime/원 신원과 정확히 일치할 때만 다음 정상 예약 실행의 제한된 대기로 분류한다. 현재 세대 partial·실패·stale/잘못된 결속은 유지하고, 발행 전후 generation 변경은 deferred다. observer generation metadata는 감시 전용이며 매매/정책/과거 DONE 권한을 만들지 않는다.

두 번째 릴리스08dbea37c/PID574420의 첫 자연 예약은14:40:01→14:41:59, entry-split 검증/세대 일치·원본 읽기0·메타18,581B·26.804ms였다. 전역 partial의 scanner 미식별/trace deadline 결손을 이 수용에 합치지 않는다. 세 번째 수리의 리뷰·시험·배포·첫 진단·후속 예약 증거 owner는 `tmp/startup-observer-order-evidence-20261014` 및 `data/report/startup_observer_order_deployment/2026-10-14`다. 이전 frozen 증거는 보존한다.

교차 리뷰는 final record-pid 직후와 ordered attest complete 사이의 추가 경합을 발견했다. 이번 배포의 첫 PID만 complete/pass·successor identity까지 같은150초 한도에서 대기하고, 완료된 과거 transition이 이후 같은 릴리스 기동을 막지 않도록 구분한다. 기존08dbea에서도 재현된 coverage 실패는 제거된 옛 workorder Markdown 감시 선언이 남은 원인으로 확인했으며 현행 runner JSON·performance workorder는 유지한다. FIFO/파일 교체·duplicate/nonfinite·bounded metadata 읽기와 과거 보고서의 정확 신원·경고/실패 경계를 반례로 재검증한다.

## 7. 40357 실패 기록과 실제 CLI 수리

40357의 final launcher가 사용한 `--workspace`가 parser에 없어 exit2,15:12:11 attestation timeout이 발생했다. 모의 Python wrapper 시험이 실제 parser를 실행하지 않아 놓친 범위 내 결함이다. 원 status/hold·첫 health(startup failed)·15:15 자연 Sentinel은 `data/report/startup_observer_order_deployment/2026-10-14`에 실패/partial로 보존한다. 원 PID의 native H/verify PASS와 ordered 실패를 구분한다.

후속 수리는 실제 -I subprocess/managed clean Git release/child PID positive 및 입력 거부 반례, record-only 명시 workspace 계약, 검증된 native PID 메타데이터 복구와 정확한 failed owned hold의 원자 소유권 인계를 검증한다. 모든 일반 native/source/정책 guard를 유지하며 원 terminal을 성공으로 수정하지 않는다. 새 배포 증거는 `data/report/startup_router_cli_repair_deployment/2026-10-14`에 별도로 남긴다.

## 8. 새 경보 대사와 진단 원인 분리

945 배포/PID/첫 health 순서는 PASS이나 전체 원천 검증은 별도다.15:37:02 health가 읽은 run970642의 age646.7초와 이전 generation이 semantic partial 선행 반환에 가려졌다. 이후 runb807은 현재 generation이며 upstream as_of15:35:12와 latest_event15:08:54의 차이로 관측불가다. 이전에 수용된 source_as_of15:15를 현재 입력 시각으로 해석하지 않는다. probe의145개 세션 generation 대기는 평가 모집단에서 제외됐으며 무신호 완전성은 미입증이다. 원 source gaps·partial은 유지한다.

후속 수리는 artifact 진단만 변경하며 freshness/generation/semantic/source blocker를 같은 bounded 보고서 snapshot에서 드러낸다. 일반 stale·실제 결손 partial 실패·권한/경제성을 보존하며 아래 승인된 두 pending 예외만 분리한다. 독립 리뷰와 반례 검증 뒤 `data/report/observer_alert_dimensions_deployment/2026-10-14`에서 새 배포/첫 health/자연 예약을 수용한다. 실제 split warm full report0과 전체 observer cold11.60GB→다음 warm full digest0/3.84초는 서로 다른 측정이다.

사용자는15:40 재경보 후 충분한 대기 시간 또는 지연 원인 해소로 반복 오류를 끝내도록 명시했다. 같은 승인 범위에서 두 경계를 보완한다. (1) ordered 완료 당시600초 안이었던 정확한 captured predecessor는 첫 정상5분 slot+기존 전체 wrapper180초까지 WARNING/pending을 유지할 수 있다. 대기 중 과거 파일이600초를 넘겼다는 사실·원 partial/실패 이력은 보존한다. 이미 완료 시점에 stale였던 자료, bytes/신원 변경, 명시적 생산 실패·기한 초과·현행 보고서에는 이 유예를 적용하지 않는다. 현재/일반 보고서와 매매 원천 stale 기준은 변경하지 않는다. (2) 새 보고서의 partial은 fresh upstream·필수 reader 정상 완료·정책/분할/지연 native 증빙을 재검증한다. 판정 표본 부재, 원 계약에 결속된 SOURCE_INVALID/필수 특징 보호 판정, 정상 BLOCK/RECHECK 및 요청·응답·화면 계약이 정확한 CAUTION/VETO, Main의 정확한 거절 또는 처리 종료가 확인된 PASS는 observation_pending WARNING으로 구분할 수 있다. 원 source gap·partial/unobservable·미검증은 보존하며 valid_empty/PASS/복구를 합성하지 않는다. 미확인 PASS 소비·실패/모순 제출·실제 계약 충돌·읽기/생산 실패·세대/시각 오류는 FAIL이다. 현재 건강 cohort는 단일 as_of의 최근600초·현재 PID/start를 machine/lineage/Main 증빙에 동일하게 적용한다. 기존30분/allPID 모집단과 과거 미확인/실패는 별도로 보존하며 과거 성공을 만들지 않는다. 자연 보고서와 detector에서 새로운 출력·기존 오류의 비재발을 확인한 뒤 수용한다.

## 9. 애프터마켓 주성 조합 입력의 실제 생산 결함 수리

16:05 관측의 path_auxiliary_feature_input_conflict10건은 실제 계약 오류로 유지했다. 이후 같은036930 AFTER 조합에서29건까지 늘어 원 trace ID/attempt/원문 SHA를 보존했다. 요청·원 machine payload 발행 전 예외라 과거 개별 숫자를 복구했다고 주장하지 않는다. 같은 joint 정의의 deterministic State 입력에서 UNKNOWN/TRUE 두 확인 경우 모두 source DD0.5484460694698434와 보존된 원 FIRST DD0.6363636363636349의 불일치로 동일 오류를 재현했다.

원인은 J.compose가 원 확인 event의 top-level DD/volume를 보존하고 refinement의 rolling branch_features만 교체하는데, 상속 source projector가 DD/volume까지 rolling feature에서 읽은 것이다. reversal_extended_state.State._source의 composed 전용 override에서 validate_composed와 원 event top/base 일치를 확인한 후 두 source facts만 원 확인 정의로 맞춘다. 원 event/refinement/proof·매칭 조건·validator의 strict equality·prompt/모델·정책 membership과 원5초는 보존한다. noncomposed source bytes는 기존과 동일하다.

해당 native 모듈1개만 바뀌므로 이전128scope 근거를 그대로 수용하지 않는다. 기준945/수리 candidate를 같은76,800행에 새로 재생해128scope·621hits·동일 signal SHA를 확인하고 runner/원본·후보 source hash/결과를 결속한다. source-only 수리의 새 code handoff는 이 정확한 old/new 모듈과 fresh parity를 검증한 뒤 기존 정의/bundle/pointer를 보존해 발행한다. C.issue의 source_semantics_repair 계약을 사용하며 새 정책·원천 과거 채움·추가 경제 gate를 만들지 않는다. 새 PID의 자연 주성 입력 생성/기존 conflict 비재발과 detector 결과를 별도로 확인한다.

최종 source 동결 후 관련15 suite 통합2,034개가41.21초에 통과했다. compile·bash 문법·diff 검사와 현재 owner4개/문서 링크70개/print-only parser25항목 검증을 닫는다. 기동·순서·observer 세대/현재600초 cohort·과거30분/allPID 이력 보존·실제 입력 충돌/미확인 소비 FAIL 반례를 포함하며 시험의 중복 합산은 하지 않는다. 배포 후 자연 예약과 새 PID의 원천 충돌 비재발은 별도 receipt로 수용한다.

## 10. 자연 수용 실패로 발견한 startup CAS 경합

다섯 번째 b0d795c1c는 정책/기동 배포 PASS와 달리 첫 진단 수용이 실패했다. 원 보고서와 startup-acceptance.json은 data/report/observer_alert_dimensions_deployment/2026-10-14와 별도 원 tmp 증거에 보존한다. 원인은 최종 영수증 교체 중의 읽기 충돌을 영구 실패로 처리해 ordered 완료 전에 full sweep을 실행한 것이다. 정확한 CAS 읽기 경합만 기존 원150초 내 pending/retry로 취급하며 실제 영수증 오류와 기한 실패를 유지한다. observer/거래 정책과 모든 native kernel은 변경하지 않는다. 후속 배포·첫 진단·정규 예약 수용은 data/report/startup_receipt_race_deployment/2026-10-14에 별도로 남긴다.

다섯 번째 정규 보고서의 남은 path conflict3건은 새 PID 출생 전108초 이상 앞선 과거 행이었다. 원tail은 현 PID 생애 전체를 포함했으나 고정10분 경계만 검사해 partial이었다. 현재 native birth의 보수적 하한·전체 수명 읽기 증빙으로 정확한 현재 cohort를 검증하고 원 과거/allPID/10분 partial을 별도 보존한다. 초기 수신 대기와 검증된 native confirmation pending은 UNKNOWN 그대로 WARNING이며 no-match/PASS로 승격하지 않는다. 기동 후 미확인 신원·현재 구간 미완전·실제 오류/잘못된 증빙은 FAIL이다. 이 실제 반례까지 포함해 여섯 번째 리뷰·시험·자연 예약으로 수용한다.

최신16:56 자연 보고서에서 현재 source/machine issues는 없지만 clean bounded 읽기·AI 결과/소비 미검증까지 artifact 실패로 묶인 경계를 추가 보완한다. 엄격한 검증 경로와 별개로, 유효한 발행/세대/시각/actor/native/정책/schema/count 및 실제 오류0을 확인한 제한 관측은 WARNING/pending이다. source quality·미확인 PASS·invalid/timeout·원 uncovered 범위는 유지하며 full coverage/PASS/복구/매매 권한을 만들지 않는다. 잘못된 읽기/신원/정책/실제 issues는 FAIL이다. 이 최종 기준은 앞선 엄격 경로의 미검증 결과를 artifact FAIL로만 취급하던 기준을 보완한다.

최종 여섯 번째 source 동결 후8suite 통합1,731개가12.16초에 통과했다. Python compile·bash 문법·diff 검사와70개 문서 링크/기존4owner/print-only parser25항목을 확인한다. 원150초의 실제 영수증 교체 경합, native birth/현재 수명, complete/clean bounded 관측과 AI invalid/timeout/미확인 PASS의 경고 경계 및 변조·손상·실제 계약 오류 hard FAIL 반례를 포함한다. 이 기술 검증은 전체 원천·AI 응답·Main 소비·경제 성과의 완료가 아니며, 첫 진단과 자연 정규 예약의 실제 결과를 별도로 수용한다.

## 11. 실제 생산 main 순서에서 발견한 projection 불일치

f25의 첫 진단은 ordered 완료 후 시작하고 process PASS였지만 첫 정규 보고서에 observer_observation_health_projection_mismatch가 남았다. 생산 main이 generation 봉인 전에 건강을 계산한 것이 원인이다. 이를 숨기지 않고 원 실패 보고서를 보존한다. 건강 계산은 notify와 마지막 generation 재확인 이후의 최종 발행 dict에서 한 번 수행한다. 실제 main 발행 경로 회귀와 선언값/재계산 equality, notify 뒤 두 번째 seal 시각, 세대 변경 미발행을 검증한다. 원 typed/native source/생애/개수/정책 검사와33 native kernel, 원5초·매매 권한은 보존한다. 새 배포·자연 수용은 data/report/observer_publication_order_deployment/2026-10-14에서 별도로 기록한다.

최종 일곱 번째 source 동결 후8suite 통합1,736개가13.99초에 통과했다. 실제 main 발행 순서·알림 후 최종 세대·건강 선언값과 재계산 일치·세대 변경 미발행을 포함한다. Python compile·bash 문법·diff 검사를 통과했으며 매매 정책/native kernel과 원5초는 변경하지 않았다. 배포와 자연 정규 보고서·후속 detector 수용은 별도 증거로 확인한다.
