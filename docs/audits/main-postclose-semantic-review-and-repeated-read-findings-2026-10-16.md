# 10/15 장후 전체 의미 점검과 반복 원천 읽기 진단 — 2026-10-16

판단: **인계 경보는 복구됐지만 재발 구조는 해소되지 않았다. 장후 실행 종결과 준비본은 유효하며, 분석·경제성은 다수 결손을 포함한다.** 파일 생성·strict PASS·controller DONE을 경제성 성공이나 당일 PID 소비로 해석하지 않는다.

원천일 `2026-10-15`, 적용일 `2026-10-16`, 선택 commit `23a13aba62884a5d3a0d48a3f91ebff4262571f6`을 고정했다. 선택본은 `postclose-dated-cost-handoff-20261015-23a13aba6`이며 분석용 source-only 수리 범위다. 작업본의 다른 코드 변경을 선택본의 동작으로 간주하지 않았다. Plan Rebase §1–§8, 당일 체크리스트의 목적·필수 규칙, 장후 지침의 실행/분석/결손/소비 계약을 기준으로 검토했다.

이 문서는 읽기 전용 검토와 개선 제안이다. 코드·선택 release·정책·예약·거래 env/lock을 변경하거나 보고서를 재생성하지 않았다. 매매 재기동·provider 호출·주문·수동 알림 전송은 수행하지 않았다. 이미 봉인된 당일 체크리스트의 원 bytes와 OPEN ID 11개를 보존한다.

## 1. 증거와 현재 수용 경계

- [현재 작은 산출물 50개 identity/hash와 의미 발췌](../../tmp/postclose-semantic-review-20261016-0655/semantic-census.json). 큰 원천·보고서는 기존 native seal, manifest, 작은 projection으로 대사했다. 대용량 원문을 다시 해시·decode해 전수 점검했다고 주장하지 않는다.
- [분할진입의 bounded reader와 준비본의 현재 세대 검사](../../tmp/postclose-semantic-review-20261016-0655/bounded-consumer-checks.json). 준비본 검사는 `generation_only=True`이며 새로운 전체 native 검증을 수행한 결과가 아니다. 원 전체 검증의 실제 결과는 아래 복구 영수증이다.
- [최종화 복구와 독립 전체 검증](../../tmp/finalization-alert-recovery-20261016-0620/result.json), [원 정규 detector](../../tmp/finalization-alert-recovery-20261016-0620/native-final-detector-preserved.json), [종료 후 독립 검사](../../tmp/finalization-alert-recovery-20261016-0620/after-finalization-detector.json), [당시 복구 리뷰](main-postclose-finalization-generation-recovery-2026-10-16.md).

원 Main 실행은 `1829c12b73504caeac0d1708fc506880`, 정상 terminal은 10/15 22:58:20이다. scoped resume의 원 실행 `e286ad714ddd438e88dc3c83a2f3d5fe`와 완료 prefix 영수증을 보존한다. 이전 commit에서 수행한 원 작업을 현재 commit의 새 실행으로 바꾸어 표시하지 않는다.

06:28:16 전체 strict PASS → 06:32:24 controller DONE → 06:38:10 cleanup DONE → 06:41:49 prepared_verified → 06:42:04 finalization/final detector DONE이 확인됐다. 정규 detector와 별도 전체 검사 모두 FAIL 0·실제 경보 consumer 0건이다. controller SHA는 `5dd00a1d307d37972878872fe835dff4d1c8ba28a0c487edd9f56a348f6eca96`, summary SHA는 `df8d5d533c5c9d374bbd9152b2b7b5d636c7d487291464a4b0130937bc5cf19d`다. 준비본도 이 controller 세대에 결속돼 있다.

07:35 PREOPEN·07:55 Main 기동은 별도 예정 작업이다. 준비본의 `actual_pid_consumed=false`, `runtime_effect=false`는 정상적인 준비 상태이며 실제 기동·자연 제출·체결·비용 후 성과를 증명하지 않는다.

## 2. 인계 경보의 직접 원인과 남은 근본 문제

05:35 정기 최종화가 summary/checklist와 05:41:36 strict를 갱신한 뒤 `summary_handoff_refresh_failed`로 종료했다. controller와 prepared는 전일 세대를 유지했다. **새 summary/checklist와 이전 controller/prepared가 혼재한 것이 두 경보의 확인된 직접 원인**이다. 탐지기가 올바르게 계약 불일치를 알렸다.

약 600초 경과와 선택 wrapper의 `timeout` 경계는 시간 제한 중단과 일치한다. 다만 해당 분기는 원 자식 종료코드·실패 phase를 기록하지 않는다. 따라서 `exit 124`나 특정 signal이 원 실행에서 관측됐다고 단정할 수 없다. 원 중단의 정확한 종료 사유는 계측 결손이다.

복구는 같은 코드의 정규 경로로 새 controller와 prepared를 결속한 조치다. 제한 시간을 늘리거나 검증을 생략하지 않았다. 그러나 다음 두 구조는 그대로다.

1. 동일 원천을 summary·strict·strict currentness·terminal recheck·prepare에서 반복 읽는다. 복구 controller도 약 575초로 기존 600초 예산에 가까웠다.
2. 각 파일의 atomic replace는 있어도 summary → checklist → strict → controller → prepared 전체를 하나의 완료 세대로 게시하는 경계가 없다. 중단 시 일부 파일만 새 세대로 남는다.

따라서 **이번 장애 복구는 완료, 영구적인 재발 방지 수리는 미완료**다.

## 3. 반복 읽기 증거와 개선안

[복구 진행 계측](../../tmp/finalization-alert-recovery-20261016-0620/progress.jsonl)의 동일 PID 마지막 관측값이다. 종료까지의 전량이 아니라 하한이며, 부모·자식/스레드 수치를 합산하지 않았다. `rchar`는 프로세스가 요청한 읽기량, `read_bytes`는 커널의 storage 읽기 계수다.

| 작업 | PID / 마지막 관측 KST | rchar | read_bytes |
| --- | --- | ---: | ---: |
| controller | 2805754 / 06:31:47 | 123,533,260,449 B | 109,786,832,896 B |
| prepare | 2908869 / 06:41:13 | 43,589,105,081 B | 38,427,041,792 B |

선택본에서 확인한 경로는 다음과 같다. 아래 링크는 검토한 실제 선택 release의 코드다. 작업본과 같다는 뜻은 아니다.

- [controller](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/src/engine/automation/postclose_done_controller.py): summary와 checklist 생성 → `build_threshold_cycle_postclose_verification` → `current_strict_receipt_issues(require_whole_native_chain=True)`. 마지막 호출은 [strict verifier](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/src/engine/verify_threshold_cycle_postclose_chain.py)에서 전체 verification을 다시 만든다.
- [finalization wrapper](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/deploy/run_postclose_finalization.sh): controller 종료 후 `done_terminal_receipt_issues`를 통해 전체 strict currentness를 다시 확인한다. [next_preopen_readiness](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/src/engine/automation/next_preopen_readiness.py)의 `_source_receipts`도 이 경로를 호출하고 bootstrap을 검증한다.
- [delay verify_source](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/src/engine/scalping/pre_submit_delay_initial_policy.py): partition별 byte seal과 전체 ordered hash, cumulative prefix hash를 별도 패스로 계산한 뒤 historical raw/compact ledger까지 검사한다. 한 번의 full 검증 내부에도 중복 읽기가 있다.
- [기존 digest session](/home/ubuntu/KORStockScan-runtime-releases/postclose-dated-cost-handoff-20261015-23a13aba6/src/engine/infrastructure/validation_digest_session.py)은 observer/transition의 명시적 opt-in 경계다. 일반 postclose controller/finalization/prepare가 동일하게 보호된다는 주장은 성립하지 않는다.

기존 [I/O 계획](../proposals/main-io-contention-and-repeated-validation-remediation-plan-2026-10-13.md)의 IO1/§5.3 및 [추가 계획](../proposals/main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md)의 RIO1/RIO2와 연결되는 적용 범위 결손이다. 기존 구현 전체를 미완료로 다시 열지 않고 이번 postclose 경로만 추가 수용 대상으로 삼는 것이 적절하다.

| 우선순위 | 구체적 개선 | 유지해야 할 계약 / 완료 검사 |
| --- | --- | --- |
| P0 | 한 invocation의 full 검증 안에서 파일 digest를 공유하고 delay의 개별·전체·날짜 prefix hash를 한 스트림에서 계산 | 정렬 순서와 원 byte seal 유지. prefix 경계에서 hash state를 복사하며 개별 SHA의 결합으로 원문 concatenation SHA를 대체하지 않는다. 같은 입력의 원 verifier와 값·선택 parity 확인 |
| P0 | postclose 전용 명시적 digest session을 설계해 controller의 중복 strict 호출부터 적용 | PASS·선택 결과를 캐시하지 않는다. 날짜·코드·parent·inventory·resolved path·inode/size/mtime/ctime·현재 의미 검사는 매번 수행. 일반 CLI/PREOPEN/live 기본 full을 무조건 얕게 바꾸지 않는다 |
| P1 | 변경 없는 동일 입력의 summary/controller를 다시 발행할 필요를 검토하고, verified ancestry에서 실패한 consumer부터 재개 | 과거 PASS만으로 새 finalization을 성공 처리하지 않는다. 해당 owner의 현행 입력/완료 계약을 확인한 뒤 원 attempt와 새 attempt를 구분. 바뀐 원천·코드·날짜는 full 검증 |
| P1 | 불변 generation 디렉터리에 전체 산출물을 staging하고 완성 manifest/index를 마지막 CAS로 게시 | 소비자는 한 committed generation만 읽는다. 실패한 pending attempt는 별도 보존. 이전 세대도 현재 계약/expiry를 만족할 때만 사용하며 새 입력 실패를 이전 성공으로 숨기지 않는다 |
| P1 | wrapper에 실제 child rc, signal/timeout disposition, phase, elapsed/remaining budget, 읽기 계수를 기록 | 600초/원 cutoff 유지. interruption 시 failed/pending 영수증과 원 증거 보존. 자동 DONE 합성 금지 |

프로세스 간 공유는 private 소유권·비symlink·역할/날짜/code/boot/session·원 content digest와 현재 파일 identity를 결속하는 별도 검토가 필요하다. 첫 수리는 invocation 내 공유부터 하는 것이 범위가 작다. local metadata 검출을 관리자 변조에 대한 암호학적 보호로 설명하지 않는다.

현재 구현의 실제 절감 사례는 분할진입 bounded reader다. 이번 점검에서 큰 보고서 원문 읽기0B, 메타데이터18,606B, 약8.2ms로 원 native 검증 세대와 정책 결속을 확인했다. 해당 reader의 작은 계약 확인 비용이며 controller 전체의 같은 속도를 보장하거나 새 성능 개선을 구현한 결과는 아니다.

수용은 같은 frozen 입력의 의미/선택 parity, append·truncate·동일 크기 교체·삭제·late partition·gzip/plain alias·날짜/code 변경 검출, timeout/kill 직후 committed generation 일관성으로 판단한다. cold/warm 실제 단계 비용과 600초 내 충분한 여유도 확인해야 한다. 이 문서의 개선안은 아직 구현·성능 수용 결과가 아니다.

## 4. 전체 장후 의미 대사

아래 35행은 논리 작업/소비 계약을 빠짐없이 나눈 것이다. 독립 프로세스 35개나 경제 연구 35개를 뜻하지 않는다. 등록된 7단계는 모두 succeeded지만 각 단계 안에 유효 진단·부족 표본·원천 결손·정상 skip이 함께 있다. 수치의 owner/window와 실제/CF를 혼합하지 않는다.

| # | 작업 / 원 산출물 | 실행·분석 판단 | 결손의 의미 / 최종 소비·다음 종결 검사 |
| ---: | --- | --- | --- |
| 1 | EOD `update_kospi` | completed_with_warnings, 실패 step 0; DB latest 10/15·2,622행 | 대상2,626 중 OHLCV 부족4종목은 결손 보존. 전체 종목 완전 수신이 아니다. 정확 일자 EOD gate는 충족 |
| 2 | 20:50 archive | EOD를 기다린 뒤20:56:32 DONE | 보고서13개는 unverified/protected 보존 skip. 파일13개를 검증·압축했다는 뜻이 아니다 |
| 3 | source-quality preflight/final | final warning; 이벤트400,751·수치 일관성0·hard contract gap0·격리8행, tuning_allowed=true | unknown-token 경고와 machine-attempt conservation gap은 진단 경고로 보존. 경고만으로 전체 입력을 막거나 원천 완전성을 주장하지 않음 |
| 4 | rising missed intraday feedback | pass, consumer no_actionable_source_rows | 실행형 BBO/turn-point 연구의 후보0·수용 floor 미충족. 이 producer의 무조치가 모든 Main 제출 기회 부재를 증명하지 않음 |
| 5 | market breadth/weakness context | source_quality ok·표본65·errors0 | 시장 맥락 진단. 독립 panic 매매나 정책 조정 권한 없음 |
| 6 | broker cost source | observed; ka10076 13행·ka10170 5행·kt00015 0행 | 공식 원천 수집 성공과 개별 완료 비용 배분은 별개. snapshot의 실제 비용 연결 count0을 보완하지 못함 |
| 7 | strategy-position fact sync | succeeded·consumer_ready; facts7·COMPLETED3 | **유효 경제성 완료0/3**; unassessed1·actual_cost_unallocated2. `warning_count=0`은 비용 후 PnL 완성을 뜻하지 않음. 원 journal/주문/비용 owner가 정확 완료별 비용 결속 |
| 8 | scale-in split | skipped_no_actual_fill | 적용 가능한 실제 fill0의 정상 skip/N/A. retired AVG_DOWN/PYRAMID producer 재가동 사유 아님 |
| 9 | entry split 및 bounded projection | native report/policy 결속 유효; 분석 source_gap·paired/candidate0 | operating paired source·완료 receipt·clean population 결손. `DirectFamilySourceRepairEntrySplit`; exact plan→custody→terminal/cost→paired model/holdout 보완. 원래 주문 유지 |
| 10 | cancel-wait | 산출물 유효·분석 source_gap/model_unvalidated·paired0 | 현재 custody unknown, checkpoint 이후 dispatch 연속성 없음; 9/29·9/30·10/1 결손. known open0만으로 flat/무제출을 확정할 수 없음. `DirectFamilySourceRepairEntryCancelWait`의 원 ledger 대사 후 종결 |
| 11 | initial quantity refresh | complete_source_only, evaluation carry_parent/no_winners | 독립 post-apply 날짜<3, 각 유형 완료0/요구30. 기존 부모 비율 유지. 과거 PID receipt를10/16 소비로 사용하지 않음. 이미 승인된 최초 채택에 이 refresh floor를 새로 부과하지 않음 |
| 12 | pipeline verbosity | v2_shadow_parity_pass; 같은 완료 window의 이벤트/identity 보존 | 실제 raw_reduction_bytes0·latency 미측정·raw suppression false. 잠재 절감 약296MB는 실현된 절감이 아님. 원 raw 권위 보존 |
| 13 | WS freshness | 정상 finalize·scanner attach success56 | exact BBO join0·경제 후보0. WS 연결 성공과 실행형 호가/경제 원천 완전성을 구분 |
| 14 | lookup attention | 비교 비용 계약은 존재 | actual completed0·거래일0·actual applied version 적용 전 N/A, EV/net null. 공통 비용 상수는 broker 비용 후 성과 아님 |
| 15 | rising classifier prior | valid_empty·valid_empty source13·후보 템플릿6 | paired0·source day0, incumbent 유지. 템플릿6을 신규 경제 후보6으로 세지 않음 |
| 16 | postclose_exit/trade_review | 4종 snapshot manifest 결속; completed projection2 | trade_review 약2.02GB·projection 약97.6MB는 재적재하지 않고 dependency receipt 확인. 실제 비용 source count0, completed2는 source/window가 다른 fact COMPLETED3과 즉시 동일시할 수 없음 |
| 17 | post-sell feedback | 2건 평가·minute-source pass2; MISSED_UPSIDE1/GOOD_EXIT1 | 사후 경로 진단이다. 완료 거래의 비용 후 이익 개선 또는 exit 정책 승격 증거로 전용하지 않음 |
| 18 | missed-entry counterfactual | 1,785건 평가; missed384/avoided636/neutral765 | 실제 제출·실현 PnL 아님. 실행형 probe29개는 전부 source gap(원 fill 계약3·receipt26), economic eligible0. 미래 대기로 원 receipt 결손을 치유할 수 없음 |
| 19 | holding exit population | partitioned_source_verified; canonical Main completed2 | completed population complete=false·snapshot missing/unverified·forward path 결손. Main/manual/retired custody 구분 보존. `HoldingProfitExitSourceContractRepair` |
| 20 | mechanical trailing market tuning | partitioned research hold, eligible evaluation complete | raw census complete=false, 모집단474·경제 eligible/common0. 평가를 끝낸 범위와 완전 원천을 구분. source_gap을 no-edge로 바꾸지 않음 |
| 21 | all-scope trailing | status complete·scope20,832·30 partitions 평가 | 공통 평가 source_gap·population474·eligible0/common0, raw census false. 큰 연구표의 완료가 20,832개 경제 수용을 뜻하지 않음. 재생 가능한 원 경로/완료 비용 owner 보완 |
| 22 | holding path vote / next policy | 12개 셀 verified_incumbent_carried | strict replay population0·12개 모두 source_gap_no_replayable_signal; numeric experiment_not_armed. 원 부모 유지가 새 vote 수치 선택이나 이익 개선은 아님 |
| 23 | Main stop confirmation | published_policy·부모 carry | owner/session9개 모두 source_gap·연구의 allowed_runtime_apply=false. 기존 hard stop을 보존한 정책 발행이며 신규 stop 최적화 성공 아님 |
| 24 | Main cumulative machine | operator 지정 고정 비교/등록 완료; 아래 별도 의미 결함 참조 | 128 runtime scope 중 등록22개, 그중 선택 변경15·carry7; 나머지106 유지. 최초 승인 채택을 EV/실현 이익으로 다시 막지 않음.10/16 PREOPEN/PID 소비는 별도 |
| 25 | compact auxiliary | compatible_current_contract_carry·128 ready/consumed0/gap0 | expected request0·provider call0, comparison_complete=false. 검증된 호환 부모 승계이며 새로운 paired 보조 실험을 실행한 것이 아님 |
| 26 | legacy full machine report | top main_mechanistic_entry_full_evaluation_complete | 내부 source_gap; natural5,325 중 다른 cohort793+receipt/identity invalid4,532, paired0. 호환 보고서 생성 완료일 뿐 전량 유효 평가 아님. 새 operator 지정 v6 채택을 이 legacy 결손으로 다시 차단하지 않음 |
| 27 | outcome labels | mature160·partial123·pending1 | **284개 모두 label contract source_gap, primary eligible0**. pending1은09:58 결정의 reference_price/request/context 결손이고10분 종료시각을 이미 지남. 단순 maturity 대기나 다음날 가격으로 고칠 수 없음 |
| 28 | microstructure machine/auxiliary evaluation | evaluable_descriptive_counterfactual·검증 capture11,599·중복0 | 설명형 CF 진단은 가능. 원 paired operating/완료 비용 후 EV와 다르며 legacy study retired·runtime false 유지 |
| 29 | tuning monitoring / storage parity | 5개 step exit0·JSONL/DuckDB10개 지표 all_match | 제출41·full fill1·partial fill9는 해당 window의 이벤트 지표. unique attempt·전체 completed census·비용 유효성을 대신하지 않음. 다른 보고서 분모와 무리하게 합산하지 않음 |
| 30 | approval summary / next checklist | direct9/9 complete·현재 해시/당일 owner 인계 유효 | 경제 상태 selected1/insufficient1/N/A5/gap2. validated_edge0·candidate0은 이 summary의 EV 집계이며 Main 등록22개 부재를 뜻하지 않음. 두 family의 blocked는 전역 기동 block이 아님 |
| 31 | strict / controller | whole_native_chain PASS·controller DONE·7단계 succeeded | 실행/계약 종결을 확인. 원천 결손과 적용 전 소비를 성공 경제성으로 바꾸지 않음. 새 보고 의미 결함은 아래 owner에 기록 |
| 32 | final storage cleanup |06:38:10 DONE·maintenance failure0·purge0 | 보호 자료 보존. 경제성 결손 자료 삭제·재작성으로 정리하지 않음 |
| 33 | finalization / full detector |06:42:04 DONE·정규/별도 검사 FAIL0·경보 consumer0 | 두 경보의 현재 해제 수용. 반복 I/O와 중단 원자성은 해결되지 않았음 |
| 34 | next preopen prepared | prepared_verified·bootstrap native PASS, 이번 현재 세대 검사 pass/findings0 | 원천10/15·적용10/16·동일 selector/controller 결속. 실제 PREOPEN/PID 소비 false 정상.07:35/07:55 소비 영수증으로만 후속 종결 |
| 35 | optional Main weakness night | night10/15·6시도/예약360초, 마지막 source10/8 completed_with_source_gaps |10/15 관측 파일은 존재하지만 해당 일 연구 산출물 없음. source10/8 native observation0·binding invalid91 등, phase notification_pending·eligible candidate0·알림 deferred_migration_or_comparison. `MainMarketWeaknessPostcloseObservation1008`의 날짜별 source repair→migration/누적→알림 disposition 수용 미완료.06:30 창 종료 뒤 단순 대기는 당일 연구를 완성하지 않음. strict/PREOPEN 비차단 유지 |

스윙 실매매/연구, episode/widget, 독립 panic 매매, IPO, ADM/LDM, 독립 AVG_DOWN/PYRAMID producer 등 OFF/retired 경로의 산출물 부재는 실패로 세지 않는다. 관측·사후 분석에 남은 과거 이름으로 실행 권한이 복원되지는 않는다.

## 5. 새로 확인한 보고 의미 결함

**Main machine 자체의 비교 완료와 machine+auxiliary 공동 완료가 summary에서 혼합된다.**

선택 정책이 실제 참조하는 불변 machine component `d82808f30533e56a97a55828f05cd61bb0f74ae0e9817da0296023ec2901b365`는 `comparison_complete=true`, `adoption_basis=operator_designated_fixed_manual_variants`다. auxiliary component `a56dc941957849261785ee499046185cba24664ff045548e33fcf2060b8fffc3`는 비교 미완료다. canonical 최신 보고서와 실제 선택된 불변 component를 구분해 대사했다.

그러나 summary의 `main_mechanistic_entry.economic_evidence.comparison_complete=false`다. 선택본 `runtime_approval_summary.py`는 먼저 공동 handoff 값을 넣고, `_reversal_comparison_disposition`은 `operator_designated_fixed_manual_variants`의 완료 분기에서 `{}`를 반환한다. 결과적으로 실제 machine component의 true가 summary에 반영되지 않는다. `cumulative_winrate_selected`/candidate1도 이 경우 자동 비교 승격의 개수나 비용 후 이익을 의미하지 않는다.

이는 **현재 준비 정책이 잘못됐다는 증거가 아니라 보고 의미 계약의 결함**이다. 권장 수리는 machine 비교 완료, auxiliary 비교 완료, 공동 완료, 지정 최초 등록/자동 비교 선택을 별도 필드로 보존하고 실제 component의 상태를 반영하는 것이다. accepted operator 지정 채택에 새 경제성 gate를 추가하지 않는다.

현재 실행 owner는 [당일 체크리스트](../checklists/2026-10-16-stage2-todo-checklist.md)의 `DirectFamilyPreopenPolicyHandoff`, 원 producer는 `continuous_reversal_postclose`다. 수리 범위는 summary producer/직접 consumer의 표현과 동일 날짜·정책 해시 결속이다. machine true/aux false/공동 false fixture, operator 지정/비교 선택/부모 carry/source gap의 각 표현, summary→checklist 해시 일치가 종결 검사다. 이번 읽기 전용 검토에서는 봉인 summary/checklist를 바꾸지 않았다. 변경할 경우 기존 인계 owner가 새 strict/controller/prepared 세대를 정상적으로 발행해야 하며 이전 PASS를 현재로 재사용할 수 없다.

문서 지도에도 차이가 있다. [9/5 장후 inventory](../audit-reports/2026-09-05-postclose-work-inventory.md)는 당시 current checklist를10/11로 연결하고 finalization05:00을 기재한다. 현재05:35 예약 및10/16 checklist의 근거가 아니다. 장후 지침의 과거 episode 관련 세부 절도 현재 Main-only/retirement 규칙으로 해석해야 한다. baseline/runbook 수정은 이번 요청 범위에 포함하지 않았으며, 과거 문서만으로 OFF 작업을 복원하지 않았다.

## 6. 후속 판단과 검증

우선순위는 인계 경로 반복 읽기/완성 세대 게시 개선, 완료 거래의 실제 비용 배분, split/cancel-wait의 원 ledger/모델 결손, holding 재생/비용 원천, optional weakness의 날짜별 migration이다. 같은 손상 입력을 재실행하는 것으로 사라지지 않는 결손은 해당 owner에서 원 증거 존재 여부와 수리 가능성을 먼저 판단한다. 원 증거가 없으면 null/U/source_gap으로 남긴다. 정상적인 valid-empty·적용 전 준비·승인된 부모 carry에 새 거래/경제성 요구를 붙이지 않는다.

검증 범위는 선택본의 관련 producer/consumer 코드 읽기, 35개 논리 계약 대사, 작은 원 산출물 identity/hash, 분할진입 native bounded reader, 준비본 generation-only currentness, 문서 링크/owner/authority 및 print-only parser다. 문서 링크·35행 고유성·OPEN ID11개 고유성·원 checklist hash 보존·`git diff --check`·print-only parser를 확인한다. 이번에는 Python/shell 구현을 바꾸지 않아 pytest·compile·bash 검사와 대규모 보고 재생성은 생략한다. 원 복구의 표적35개 PASS와 전체 native 검증은 해당 원 영수증의 과거 실행으로만 인용한다.

잔여 한계: 대용량 원천은 producer가 봉인한 native receipt/projection을 근거로 검토했으며 전체 원문을 새로 재생하지 않았다. 현 준비의 유효성과 향후 자연 기동/주문/비용 후 성과는 별개다. 인계 경보의 재발 방지 코드 수리와 위 보고 의미 결함은 미구현으로 남는다.
