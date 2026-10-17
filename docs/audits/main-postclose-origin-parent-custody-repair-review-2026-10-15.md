# 10/15 장후 origin 부모 검증 복구 검토

운영은 source15의 Main·7개 stage·전체 controller·tuning이 정상 종결됐고, target16 준비본의 `current_full_contract` 검증도 PASS다. 직접 분석 근거9/9와 경제성 원천 결손2·표본 부족1을 분리한다. 최종 전체 오류 탐지는 제출병목 observer의 유예/부분 관측 때문에 FAIL1개가 남으며, 기존 자연 수용 owner가 이를 소유한다. 실제05:35 최종화·07:35 PREOPEN·07:55 PID는 아직 미도래다.

대상 source/publication은 `2026-10-15`, 다음 적용일은 `2026-10-16`이다. EOD는20:56:31 `completed_with_warnings`, 당일DB2,622행·수집 대상2,626개·원천 부족4개로 종결됐다. 원본과 미수신 종목의 과거 이력을 보존한다.

## 결함과 수리

`main_machine_policy`의 원 실행 `c093f14ab2c24ec89a2ce67d67c37679`은21:03:10 `command_exit:1`로 실패했다. 승인된 누적 등록 `c15491190e72…`의 origin `cfa070c1e…`가 현재 selector와 다른 상황에서 `active_policy_code_reader_root_changed`가 발생했다. 현재 선택본 `77eaf86fe…`는 같은 부모 `1f069c6894b5…`를 엄격 검증하지만, 봉인된 origin을 현재 live reader로 다시 실행하면 실패했다. 다음날 activation도 같은 검증 함수를 소비하므로 장후 성공만으로 수리를 닫지 않는다.

기존 `continuous_reversal_policy_v6._attested_activation_parent` 안에서만, 이 displacement 또는 명시적 v4/v5/v6 코드 변경 오류에 한해 origin의 원래 dated 코드 인계 영수증을 다시 검증한다. 원 origin의 Git commit·clean source, 요청 날짜, current pointer SHA, 원 generation/bundle, 승인·봉인·정책 비재선정·provider 미호출, 전체 원천 및 코드 해시·코드 membership과 검증 중 교체를 확인한다. 일반 원천 오류는 우회하지 않는다. live loader, 등록안, 부모/보조 membership, provider, 주문·수량·보유·안전조건은 수정하지 않는다.

실제 origin의 보존 영수증은 원천847개·코드37개 해시가 일치했다. 수리한 실제 누적 부모 로더는 원 등록안·포인터를 변경하지 않고 동일 부모를 반환했다. 38가설의 기존 승인 등록과 미등록 추가12가설은 별개로 보존한다.

## 검증

- 원 코드에서 현재 reader displacement 실패를 재현했다.
- 날짜 변경·원천/코드/부모/승인/날짜/포인터/봉인/membership/중복 hash 충돌·영수증 결손 거부 회귀와 관련 원천·정책·누적 등록·PREOPEN 검사310개가 통과했다. 첫 실행의1건은 격리 작업본 `.venv` 링크 부재였으며 프로젝트 환경 연결 후 해당 실제 subprocess 검사가 통과했다.
- 현재 선택본과 수리본의 고정 workload는128 scope·76,800행·607개 신호이며 signal SHA `72a8e589d1c1288f684d16c8aa66bcf5d1787671358ce7063551627fef0e2d0d`가 일치했다. 코드 변경은 해당 v6 부모 검증 파일 하나다.
- Python compile·`git diff --check` 통과. 문서/owner는 print-only parser로 확인한다. Kiwoom wire 변경, 패키지 변경, provider 호출·주문·매매 재기동은 수행하지 않는다.

근거는 [EOD 대사](../../tmp/postclose-monitor-20261015/eod-review.json), [검사 원본](../../tmp/postclose-monitor-20261015/parent-custody-tests.log), [subprocess 재검사](../../tmp/postclose-monitor-20261015/parent-custody-subprocess-recheck.log), [신규 동일성 대조](../../tmp/postclose-monitor-20261015/parent-custody-native-parity-provenance.json)다. 이 검토는 코드 수리와 읽기 검증이며, 배포·장후 terminal·10/16 prepared/PREOPEN/PID·실현 성과를 대신하지 않는다. 운영 후속은 기존 `CumulativePolicyAdoptionDeployment1015`와 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

## 비용 세대와 최종 checklist 인계 수리

부모 검증을 복구한 실행 `e286ad714ddd438e88dc3c83a2f3d5fe`에서 분석·정책6개 stage가 모두 성공했다. 승인된38가설은 next-session 후보 `a09735ace81a…`에 반영됐으며128 scope 중22개 등록 범위가 일치한다(15개 변경·7개 승계). 원 현재 포인터는 유지됐다.

그러나22:13:49 checklist 생성이 `initial_quantity_refresh_stage_invalid`로 실패했다. 원 수량 generation `b6cf05ed0edd…`의 엄격 검증은 `quantity_fact_cost_generation_changed`를 반환했다. 공식 holding 비용 수집이 이미 fact와 수량이 비용 세대를 결속한 뒤 실행돼 생긴 선후행 오류다. 비용 결손을0으로 바꾸거나 검증을 느슨하게 하지 않는다.

기존 비용 수집을 fact 생성 앞으로 이동하고 호출 수·명령·timeout·경고/unknown 의미를 보존한다. 최종 resume의 허용 실패 지점에 checklist 생성 실패만 추가하며, 원 native 명령 증명·6개 stage·snapshot·현재 수량 영수증 검증은 그대로 유지한다. 복구는 현재 비용으로 fact와 직접 downstream·수량을 다시 결속하고 최종 handoff를 재개한다. 원 수량·원 실패·정책/보조 원천과 기존 승인 membership을 보존한다. wrapper 회귀·`bash -n`·print-only parser로 이 보완을 검증하며, Kiwoom 요청/응답·provider·매매 프로세스·주문/수량 guard를 변경하지 않는다.

직접 소비자 fact·scale-in·entry split·entry cancel·initial quantity를 비용 세대에 맞춰 순차 재생성했다. 수량 generation `b59af1a1566d…`는 strict 검증과 exit snapshot 검증을 통과했고 `carry_parent`를 유지했다. 완료 거래 근거가 없어 성과를0으로 대체하지 않는다. 기존6개 stage 영수증은 원 코드와 source로 다시 검증됐다.

추가로 다음날 요청16일이 부모 적용일15일과 다른 실제 origin 읽기를 검사했다. 보존 영수증은 부모의 원 적용일로 검증하고 요청일보다 미래인 부모·포인터 적용일 불일치·비정규 날짜는 거부한다. 실제 cfa origin에서 요청16일/부모15일의 동일 부모 읽기가 통과했다. 원 부모 날짜나 current pointer는 변경하지 않았다. 날짜 회귀·wrapper·PREOPEN 관련227개 검사와 shell 구문 검증이 통과했다. 새 고정 workload 대조는 [날짜 보완 동일성 증거](../../tmp/postclose-monitor-20261015/future-parent-native-parity-provenance.json), 검사 로그는 [227개 검사](../../tmp/postclose-monitor-20261015/future-parent-and-cost-handoff-tests.log)로 별도 보존해 기존 배포 영수증의 해시를 바꾸지 않는다.

## 운영 복구와 논리 작업 점검

source/publication15·effective16을 유지한다. 검토 코드 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`를 Main 정지 상태에서 선택했다. 기존 후보 `a09735ace81a…`의 원 generation을 보존하고 native identical-code-refresh로 `8809c82e36ba…`를 발행했다. machine payload/backend/membership·보조 cell·manifest·부모·날짜는 동일하고 코드/영수증 해시만 native 계약대로 재결속됐다. active pointer는15일 부모 그대로이며 추가12가설은 등록하지 않았다. [후보 대조](../../tmp/postclose-monitor-20261015/dated-cost-candidate-parity-review.json), [원천854·코드37 인계](../../tmp/postclose-monitor-20261015/dated-cost-native-handoff-review.json), [선택 영수증](../../tmp/postclose-monitor-20261015/dated-cost-release-selection.json)을 보존한다.

Main 재개 run `1829c12b73504caeac0d1708fc506880`은 원 실패 `e286ad714ddd438e88dc3c83a2f3d5fe`의 native prefix·6개 stage·exit snapshot·새 수량을 검증해 최종 handoff부터 실행했고22:58:20 `succeeded`/strict PASS(issue0)로 종료했다. 원 실패/status/명령과 최종 resume proof를 보존했다. 구618 release에서 대기하던 controller는23:00:28 새 정책/stop/delay contract를 검증하지 못해 `blocked_independent_producer`로 종결됐다. 이를 기존 정책의 결함으로 바꾸지 않고, 원 실패를 보존한 뒤 현재 선택본의 controller만 재실행했다. Main 전체나6개 연구 stage를 다시 실행하지 않았다.

아래는 운영 terminal과 분석 의미를 분리한 점검이다. 자료는 모두 source15이며 누적 비교 창이 다른 경우 명시했다. 최종 controller/준비 결과는 다음 절의 실제 종결 영수증으로 추가한다.

| 논리 작업/owner | 실행·분모/의도한 결과 | 분석·결손 판정 | 직접 소비와 다음 경계 |
| --- | --- | --- | --- |
| EOD update |20:56:31 completed_with_warnings; target2626=success2622+unreceived4, 제외86 |4개 OHLCV 부족; 과거 이력 보존 |DB exact15·native EOD gate PASS |
| 시장 breadth |65개 관측, source quality ok |유효 운영 진단; 수익 아님 |market-weakness 원천/보고 |
| rising feedback |exit0·당일 report 생성 |embedded turn-point replay의 master binding 무효; 후보0을 valid-empty로 해석 금지 |기존 source-quality owner, 원 master/route 결속 후 분석 가능; ETA null |
| 원천 audit preflight/final |400751 event·114 stage, hard contract gap0, 결함8행 제외 |warning·tuning 허용; machine attempt conservation warning 보존 |적격 행만 연구/summary 소비; unknown token은 전체 차단 사유 아님 |
| outcome labels |stage succeeded; mature160·partial123·pending1 |유효 원천/미성숙 분리 |committed label hash→machine/auxiliary |
| Main machine |6495834 원천행·4530343 적격행·26개 pre-refresh partition 제외 |원 비교 완료, 실제 거래/PnL 아님; 지정 초기38가설의 승인 반영은 별도 권한 |128 scope·등록22개(15변경/7승계)→candidate8809 |
| legacy machine/full evaluation |exit0·main full evaluation complete |후보0; 원 비교/정책 선택 receipt 보존, 실현 EV 아님 |stage→direct summary/strict |
| compact auxiliary |128 planned/new_ready·contract gap0·expected request0·actual provider0 |compatible_current_contract_carry; 비교 완료 false·PID 소비0 |기존 prompt/verdict/membership 보존→dated candidate/reader |
| 공식 holding 비용 |기존 producer exit0, 뒤늦은 비용 세대 결함 확인 |비용 결손 null 유지; wire/호출수 변경 없음 |wrapper 비용→fact 순서 수리 |
| position fact |현재 비용으로 native 재생성 exit0 |source generation 재결속, 원 fact 별도 보존 |scale-in/entry split/cancel/수량 |
| scale-in split |재생성 exit0·actual fill0 |skipped_no_actual_fill·incumbent_unsplit, EV null |effective16 incumbent 보존 |
| entry split |재생성 exit0·real4/full3/partial1; bounded projection verified |recommended0·source gap operating_paired_source_missing; 진단 EV를 승격 근거로 사용 금지 |report/policy native receipt→summary/bootstrap |
| entry cancel wait |재생성 exit0·등록7·completed candidate0 |source_gap bounded_reconciliation_metadata_required; unclassified3·미확인 custody/count null |기존90/120/600/1200·enabled 보존; 원 정산/비용/holdout 필요 |
| initial quantity |새b59 generation strict PASS·carry_parent·eligible completed0 |원 비용 세대 불일치 복구, 성과0 아님 |final resume/checklist/bootstrap의 현재 영수증 |
| pre-submit delay |stage succeeded·committed0a8a9ed5041d… |initial_baseline_immediate; 수익 개선 주장 없음 |source15·effective16 원 baseline 정책 |
| Main stop/holding numeric vote |stage succeeded·published_policy |원 stop provenance와 separate holding-vote parent carry; actual_profit_verified=false |기존 protect/stop·custody 보존, committed16 소비 |
| pipeline verbosity |v2_shadow_parity_pass; raw/producer293348, common293347 |유효 count/identity 진단; suppression 미승인 |동일 완료 watermark→summary; 다음 자연일 parity |
| WS freshness/lookup |599252 통합 event·source-only 지시5개 |운영 진단 생성; hotset/prune master 미확인으로 economics source_verified=false |기존 lookup projection/summary; 새 cap/주문 권한 없음 |
| rising classifier prior |valid_empty·paired0·13개 valid_empty source |변경 모집단 없음, incumbent_preserved; EV null |effective16 기존 정책 |
| exit monitor snapshot |postclose_exit manifest strict PASS |현재 종료 관측/owner 자료; 원 HOLD 결손을 합성하지 않음 |quantity/checklist/final resume |
| runtime summary |required9/available9·direct_evidence_complete |economic mixed; split/cancel source gap, sample 부족 별도 |native checklist/strict/controller |
| next checklist |Main 재개에서 생성 exit0 |source15 producer hash 결속; OPEN natural acceptance 유지 |target16 current parsed owner |
| tower |현행 direct_tower predicate에 따른 native 분기 |별도 경제성/retired common tuning을 새 gate로 복원하지 않음 |direct summary/checklist 계약 |
| Main strict |run1829·PASS·issue0 |family/direct closure; whole-chain DONE은 별도 |controller/summary_handoff |
| controller/summary_handoff |구618 실패 보존; selected23 최종23:30:42 DONE |whole_native_chain strict PASS·issue0; 새 문서 계약 수용 |source15→effective16 prepared_verified |
| tuning Parquet/DuckDB |23:01:02 success;5개 작업 exit0 |10/13~15 비교10지표 모두 일치; 실현 PnL 개선 아님 |shadow_diff_summary all_match=true |
| dashboard archive |20:56:32 DONE;verified0/compressed0·미검증13 skip |미완결 원천 보호; 압축0은 실패 아님 |원 source bytes 보존 |
| 제출병목 observer |Sentinel checkpoint 재개 발행 성공; full observer25초 뒤 native75 유예 |current10m 무관측·Main 정지; 검증 deadline·partial/unobservable 보존, detector FAIL |NonfixedDispatchReadinessReview1012의 다음 자연 PID/source·원130/40/180초·연속3슬롯 수용; 임의 신호 생성 금지 |
| 시장약세 야간 advisory |21:40/22:40/23:40 regular_postclose_or_eod_active 유예 |valid defer; 전날14일 계산을15일 성공으로 사용 금지 |다음 설치00:40 슬롯, startup gate 아님 |
| 다음 최종화 |설치05:35; inventory의05:00 표기와 drift |not_yet_due, 조기 실행하지 않음 |source15 controller→cleanup→final detector |
| PREOPEN/실제 기동 |설치07:35/07:55 |미래 not_yet_due; prepared/선택은 actual PID 아님 |원 DirectFamilyPreopenPolicyHandoff/CumulativePolicyAdoptionDeployment1015 |
| OFF/퇴역/조건부 |Swing OFF·episode/widget/IPO/PYRAMID 전용 owner 퇴역 |not_applicable; 복구 대상 아님 |Main/manual custody·원 journal 보존 |

설치 routing8개가 검증됐고 operator startup hold/restart.flag는 없다. 공유 mount와 선택 source clean을 native router가 검증했다. 디스크 가용37GiB, managed release92개로 탐색 상한256 이내다. 매매 process/supervisor를 기동하지 않았고 env/lock/provider/threshold/주문을 수동 변경하지 않았다. 미래 기동·체결·순익은 아직 관측되지 않았다.

## 다음 체크리스트 owner 인계 보완

최초 전체 controller는23:11:17 DONE, target16 준비는 `prepared_verified`로 종결됐다. 그러나 자동 생성한16일 문서에15일의 미종결 ID7개가 없어 원 Acceptance와 이력을 인계했다. 미래 문서의 OPEN은11개이고 exact16 parser에서 ID 중복이 없다. 원 문서의 수동5개는 완료 체크 대신 이관 이력으로 남겼다. 원 AUTO의 날짜별 이력은 보존하고 이번 복구 진행 메모만 AUTO 밖으로 옮겼다. 표준 parser에서도 누적 정책의 owner가16일 문서 한 곳으로 선택된다.

초기 인계에서 항목 뒤의 과거 AUTO/취소대기 handoff 경계까지 복사해 `cancel_wait_checklist_block_invalid`가 발생했다. [원 실패 로그](../../tmp/postclose-monitor-20261015/open-owner-final-reclosure.log)와 잘못 복사된 문서 원본은 보존했다. 복사 범위를 각 항목의 들여쓴 본문으로 제한하고, AUTO·cancel-wait 블록 각1개·표준 sync 명령1개·OPEN11개/ID 유일성·기존 native `upsert_checklist_handoff` 수용과 print-only parser를 검증했다. 원 정책·원천·다른 수동 내용은 바꾸지 않았다. [문서 계약 보완](../../tmp/postclose-monitor-20261015/open-owner-document-contract-correction-review.json), [이관 owner 대조](../../tmp/postclose-monitor-20261015/next-checklist-open-owner-transfer-review.json)를 보존한다. 아래 최종 종결은 문서 보완 뒤 새로 결속한 결과이며 앞선 PASS를 재사용한 주장이 아니다.

## 최종 문서 세대의 종결

보완 뒤 native 전체 controller는23:30:42 `done`으로 종료했다. 최신 strict는 `verification_scope=whole_native_chain`, `whole_native_chain_done_claimed=true`, issue0이다. 7개 stage와 Main run1829·원 source15가 같은 종결에 결속됐다. [최종 재실행 결과](../../tmp/postclose-monitor-20261015/open-owner-corrected-final-reclosure-result.json)를 보존한다.

target16 준비는23:34:21 `prepared_verified`, 선택 commit23a13aba6, source15·target16·actual_pid_consumed=false다. immutable readiness는 `data/runtime/policy_bootstrap/prepared/2026-10-16/2026-10-15_52c36c34716b97b1_23a13aba62884a5d/readiness.json`이며, 이전 준비 generation은 보존했다. 현재 원천 전체를 소비하는 별도 최종 verify와 non-mutating source-date detector 결과는 아래 후속 검증에 기록한다. 준비 영수증과 summary의 발행 당시 future-pending snapshot을 실제 PREOPEN/PID로 재라벨링하지 않는다.

직접 근거는9/9 complete다. 경제성 분류는 원천 결손2·표본 부족1·진단/N/A5·누적 승률 선정1이며, 실제 비용 후 실현 순익 개선을 입증한 수가 아니다. 별도 rising replay와 WS 추정 경제성의 master/source 결손도 표에 보존했다. 운영 종결과 초기 승인 등록·유효한 승계, 실제 PID·자연 성과는 각각 별도다. [정책/수동 통제5개 해시 보존](../../tmp/postclose-monitor-20261015/protected-policy-custody-final-review.json), [PREOPEN 계획](../../tmp/postclose-monitor-20261015/next-preopen-routing-plan.json), [기동 계획](../../tmp/postclose-monitor-20261015/next-start-routing-plan.json)은 다음날 예약이23 release를 소비하도록 준비됐음을 보이며 기동 실행은 아니다.

최종 [전체 준비 소비 검증](../../tmp/postclose-monitor-20261015/final-readiness-full-verify.json)은 source15·target16·commit23에 대해 `current_full_contract` PASS, findings0, actual_pid_consumed=false다. 독립 진단 복구 뒤 [봉인 재검증](../../tmp/postclose-monitor-20261015/post-diagnostic-prepared-seal-verification.json)도 PASS다. prepared receipt를 실제 장전 활성화나 신규 PID로 바꾸지 않았다.

마지막 [읽기 전용 전수 detector](../../tmp/postclose-monitor-20261015/final-postdiagnostic-detector.json)는7개 초기화 성공·운영 mutation0이며 전체 FAIL이다. 실패 owner는 `submission_bottleneck_monitor`의 execution deferred/semantic partial이고, holding-exit 최근/과거 로그는 별도 warning이다. auth·process·resource·lock은 PASS다. 정상 기동 준비와 관측 완전성을 같은 GREEN으로 합치지 않는다.

해당 보고서의 원본을 보존하고 기존 Sentinel의 cache/summary·130초 예산으로 재생성했다. 최초 시도는124 timeout이지만 원2,754,456,831바이트 전체와 적격156,211행 checkpoint가 저장됐다. 그 checkpoint의 같은 예산 재개는 정상 발행됐고 `SUBMIT_DROUGHT_CRITICAL` 진단을 유지했다. 원 raw·정책 준비 입력은 바뀌지 않았다. [source 복구 기록](../../tmp/postclose-monitor-20261015/final-sentinel-recovery-review.json), [재개 로그](../../tmp/postclose-monitor-20261015/final-sentinel-checkpoint-resume.log)를 보존한다. 이후 전체 observer는 원40초 예산 중25초 뒤 선행 validation deadline으로75 유예됐고, 현재10분 창의 자연 신호0·Main 정지를 완전 관측으로 만들지 않았다. [실제 consumer 영수증](../../tmp/postclose-monitor-20261015/final-full-observer-refresh.log)을 보존한다. 수동 재생성·캐시 준비를 자연 슬롯 성공으로 세지 않으며, 기존 `NonfixedDispatchReadinessReview1012`의 다음 실제 actor/source·원130/40/180초·정규 연속3슬롯 Acceptance와 `DirectFamilyPreopenPolicyHandoff`의 실제 PREOPEN/PID는 OPEN이다. 새 budget/provider/threshold/기동 권한이나 합성 신호를 만들지 않았다.

추가 소스 변경이 없는 문서 인계 보완은 native 계약·parser·링크·diff 검사로 검증했다. 관련227개 Python 회귀·compile과 wrapper shell/68개 경계 검사는 기존 수리 증거를 유지하며 거래 전역 suite나 추가 provider 호출은 수행하지 않았다. 향후05:35 최종화/cleanup/final detector와07:35/07:55의 실제 성공은 예약 도래 후의 별도 영수증이 필요하다.

전체 observer75 원 영수증을 유지한 채 마지막 native source-only 관측은 `completed/partial`로 기록했다. 실제 selector·이 부분 관측·원 Main/전체 controller terminal을 `data/runtime/postclose_recovery/2026-10-15/monitor-close-168fe078e9404d5f8a131f41a43a7a7d`에 원 bytes로 보관했다. 새 배포/전환/DONE을 합성하지 않았다. [닫힌 날짜 보존 검증](../../tmp/postclose-monitor-20261015/closed-day-observation-preservation-review.json)은 기존 reader의 다음 날짜 계약에 `historical_generation_verified`로 연결됨을 읽기 전용 사전 대조했으며 current/full coverage=false를 유지한다. 실제 다음날 실행 증거가 아니다. [마지막 detector](../../tmp/postclose-monitor-20261015/final-sourceonly-close-detector.json)의 부분 관측 FAIL은 그대로 남긴다. 전체 결과와 향후 경계는 [최종 결과 JSON](../../tmp/postclose-monitor-20261015/final-results.json)에 기록했다.
