# 2026-10-13 장후 실패 단계 수리·재개 검토

사용자 지시: 실패한 지점부터 고쳐서 재실행. 원 source/publication은 `2026-10-13`, 다음 적용일은 `2026-10-14`다. 부모 실행본은 `main-rest-reduction-20261013` / `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`이며 작업본의 다른 I/O·REST 변경은 수리에 포함하지 않았다.

## 수정과 수용 경계

- 초기 수량 CLI의 heavy admission만 기존 dispatcher와 동일한 14,400초로 맞췄다. 두 compute slot·writer 순서·검증된 inherited descriptor·종료 회수는 유지한다. 수량·가격·정책 선정·주문·provider 로직은 변경하지 않았다. 60초보다 긴 정상 선행 heavy 작업 뒤 실제 슬롯 취득·해제를 확인하는 회귀를 추가했다.
- 같은 날짜의 joint 최초 등록은 `continuous_reversal_operating_comparison_v1`의 실제 machine/auxiliary, 승인 request와 frozen source receipts로 stage를 결속한다. 구 `source.json`·fixed-watch sidecar·call-freeze/provider-results를 합성하거나 복원하지 않는다. 승인·exact date·sealed body·48 cell/route·source byte hash·false runtime/order authority와 auxiliary 정책 소비 검증을 유지한다. Initial operator designation에 독립 경제성 비교 gate를 추가하지 않는다. 새 source 변경은 stage reuse를 무효화한다.
- `run_threshold_cycle_postclose.sh SOURCE_DATE --resume-from-initial-quantity`는 실제 native main 실패의 마지막 명령이 초기 수량일 때만 지원한다. 원 command metrics, producer-issued artifact reuse receipts·본문/Markdown SHA·5개 aftermarket code hash, 완료 prefix·정책 날짜·EOD·preflight·machine/delay/labels terminal을 검증한 뒤 START한다. 원 실패를 attempts에 보존하고 source-only scoped resume receipt를 새 main에 결속한다. 기존 prefix와 bot action을 생략하고 초기 수량부터 기존 하류를 실행한다. 일반 cron 동작은 유지한다.

## 리뷰·검증

구현→self review→보완→re-review를 수행했다. 입력이 변경됐거나 다른 명령이 실패했거나 원 main이 실행 중인 경우 재개를 거부한다. 등록 report의 authority/date 변조와 원천 변경이 실패하는지 확인했다. 실제 실패 machine 출력의 읽기 전용 validation은 issues 0이고, 기존 초기 수량 current 정책도 수정 코드에서 검증됐다. 이는 새 정책/PID/경제성 수용을 뜻하지 않는다.

- Admission·stage·wrapper 회귀: 117 PASS.
- Joint source/registration 회귀: 43 PASS 및 환경에서 누락됐던 frozen parent/source/evidence 사본을 격리된 fixture 영역에 공급한 native publication 회귀 1 PASS. 실제 provider/store 호출은 사용하지 않았다.
- Python compile, `bash -n`, `git diff --check`, 문서 print-only parser PASS. 기존 checklist owner 8개와 다른 사용자 편집은 유지한다.

코드 gate 범위에서 finding 0이다. 실제 재실행·새 stage terminal·summary/checklist/strict/controller·다음 PREOPEN/PID와 비용 후 성과는 각각 후속 증거로 기록한다. 설치 cron/서비스·bot 재기동·수동 env/lock/provider/threshold·주문 권한을 추가하지 않는다. 미래 05:35 최종화는 별도 예정 owner다.

## 공유 경로 보완과 실제 재개

Immutable release의 `data`는 canonical workspace를 가리키는 symlink다. 최초 수리본의 재개 validator가 lexical release 경로를 family inventory에 전달해 실제로 존재하는 delay ledger를 missing으로 판정했다. `data.resolve()` 후 기존 source validator에 전달하도록 보완하고 release alias 회귀를 추가했다. Admission·stage·wrapper 117개를 다시 통과했다. 수리 commit은 `ced94113652aa56261f5633bb3e372101992190d`, 선택·실제 postclose 실행 root는 `/home/ubuntu/KORStockScan-runtime-releases/postclose-failed-stage-recovery-20261013-v2-ced941136`이다. Main bot PID 소비 영수증으로 해석하지 않는다.

Dispatcher 수정으로 delay 초기 정책의 code contract가 바뀌었다. 원 generation의 `source_date_or_release_code_changed`를 우회하지 않고 영향받은 delay stage만 원 source/publication `2026-10-13`로 재생성했다. 승인된 joint 최초 등록의 다음 날짜 candidate도 같은 수리 commit에 재결속했으며 현재 runtime pointer·provider·주문 권한은 바꾸지 않았다. Machine stage는 22:30:59, delay는 22:56:08, auxiliary는 22:56:20에 `succeeded`, exit 0, issues 0으로 종료했다. Outcome labels의 원 성공은 검증된 재사용으로 보존했다.

Main은 23:01:44에 native run `bdb70729be21466b96816bb2f46f322c`로 초기 수량부터 재개됐다. 원 failed run `1f46324c3f4d4598a9a05aa295949abb`와 scoped resume proof를 새 상태에 결속했다. Proof byte SHA256은 `4eebee10a752de1adfd83bddc2377d228a711605eeb1690d80f3629f871ca31e`이다. 초기 수량 native command는 exit 0, wall 1.939초, completed initial trades 0, `carry_parent`로 통과했다. 비용 후 EV를 0으로 채우거나 새로운 edge를 주장하지 않는다. 기존 root 작업본의 다른 사용자 소스 변경은 수리 릴리스에 포함하지 않았다.

실패한 원 queue의 controller/tuning만 exact PID·start ticks·cwd 확인 후 종료했고, 새 native Main START 뒤 기존 release router로 수리 release의 controller/tuning을 재개했다. Bot restart나 lock inode 삭제는 없었다. Whole-chain strict·summary/controller·tuning의 최종 상태는 하류 실행 종료 뒤 별도 확인한다.

### 기존 활성 정책의 동일 코드 인계 복구

재개된 하류 `legacy_machine_report`는 새 release에 기존 활성 정책의 exact code handoff가 없어 `v4_contract_code_changed:reversal_path_runtime.py`로 23:03:31 실패했다. 이는 새로운 정책 원천 변화가 아니다. 원 `932bb3a…`의 승인된 `main_active_policy_code_handoff_v1` seal·권한·정확 날짜·current pointer·bundle·원 source SHA 784개를 검증했고, 수리 release의 정책 계약 파일 33개가 원 receipt와 byte 동일함을 확인했다. 새 source code 수정 없이 이 동일성만으로 수리 commit의 인계 metadata를 발행했다. 새 receipt의 `rebind_basis=byte_identical_approved_policy_code_and_frozen_sources`, `postclose_source_only_recovery=true`, `runtime_effect=false`, `policy_reselected=false`, `provider_called=false`, `actual_pid_consumed=false`다. 원 receipt와 원 selector 보존본을 source hashes에 추가해 786개를 결속했다.

Selector lock 안에서 current pointer와 selector byte CAS, 기존 native `validate_receipt`·handoff validator·`load_effective`를 통과했고 pointer/selector byte는 변하지 않았다. 원 활성 bundle `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`를 유지했다. 실패한 legacy stage만 같은 날짜/release로 재실행한다. 새로운 threshold·membership·runtime policy 선정 또는 bot 재기동 근거를 만들지 않는다.

### Native custody 설정 보완과 final handoff 재개

Legacy stage는 23:11:47에 exit 0·issues 0으로 끝났다. 청산 snapshot 4종은 wall 698.133초·exit 0, stop confirmation은 23:26:12에 exit 0·issues 0으로 끝났다. Main은 23:28:22에 `cancel_wait_summary_projection_generation_invalid`로 tower에서 실패했다. 재개 wrapper를 owned log로 직접 호출해 정상 release router의 `native_custody_environment` 전달을 빠뜨린 것이 원인이다. 기본 account identity에서 frozen checkpoint는 unknown이며 승인 profile을 기존 parser로 읽으면 원 cancel-wait의 current custody와 validation이 `incumbent_carry`·findings 0으로 일치한다. 원 보고서·registry·checkpoint·정책 값 변경은 필요하지 않았다.

Wrapper가 정상 router와 동일한 승인 account/journal 설정을 native parser로 읽도록 보완했다. 파일을 shell source하거나 수정하지 않으며 assignment는 인용된 export로 전달한다. 실제 native tower failure 뒤에만 `--resume-from-final-handoff`가 원 completed command metrics·이전 source-only proof·전체 active analysis stage·청산 snapshot·초기 수량 terminal을 검증하고 실패를 보존한다. 완료 계산·bot action을 생략하고 최초 영향 consumer인 summary부터 tower/checklist/strict와 실제 Main terminal을 다시 실행한다. 수량 terminal은 후속 정상 처리에 그대로 전달한다.

보완 self review·re-review finding 0. Admission·stage·wrapper 126 PASS, shell 문법·diff 검증 PASS다. 새 회귀는 다른 실패/실행 중/완료 근거 결손/이전 proof 변조/invalid stage·snapshot·quantity를 거부하고, 기존 profile 전달 및 assignment의 shell 치환 미실행을 확인한다. 분석·수량·정책 code contract는 변경하지 않아 완료된 delay/stop/legacy 계산을 다시 발행할 필요가 없다. 새 릴리스의 정확 코드/현재 정책 인계 및 다음 날짜 candidate binding은 별도 native 검증 뒤 기록한다.

최종 수리 commit은 `8e0bd25f704271b1a890061f9099d9149f55060d`, 실행 root는 `/home/ubuntu/KORStockScan-runtime-releases/postclose-failed-stage-recovery-20261013-v3-8e0bd25f7`이다. 기존 native `reversal_code_handoff.issue`가 원 승인 parity(불일치 0·confirmation 614), 동일한 정책 계약 파일 33개·원천 787개와 그대로인 현재 bundle을 검증해 인계를 발행했다. `policy_reselected=false`, `provider_called=false`, `actual_pid_consumed=false`다. 원 v2 selector와 대기 queue의 exact PID/start/cwd 종료 근거를 `data/runtime/postclose_recovery/2026-10-13/8e0bd25f704271b1a890061f9099d9149f55060d/`에 보존했다. 새 Main이나 bot restart를 실행하지 않았다.

승인된 joint 최초 등록의 다음 날짜 candidate를 native producer로 같은 source/publication에 재결속했고 bundle은 `2937d76dd1d2f08bfac005ee9d9339d4cbb3e34985efa9252a31cf30df73f638`이다. `actual_provider_calls=0`, `runtime_effect=false`이며 auxiliary stage도 새 출력 generation에서 exit 0·issues 0으로 검증했다. 23:45 관측에서는 final handoff 재개 전 stage/snapshot 해시 검증 중이고 승인된 custody 설정 전달을 실제 validator 프로세스에서 확인했다. 다음 Main START·terminal·strict/controller/준비 결과는 종료 후 추가한다.

### Entry-split 저장 서식과 strict 재개 보완

최종 handoff run `f343c03991b742f590431a3291bff03f`는 23:46:18에 START했다. 승인된 custody profile로 cancel-wait reconciliation과 tower가 일치했으나 23:48:42 family strict exit 2가 entry-split의 `semantic_unverified_large_source`와 해당 summary/checklist 결손을 거부했다. Native 보고서는 539,058,129 byte이며 512 MiB read bound(536,870,912 byte)를 넘었다. 내용이나 정책 generation 변조가 원인이라는 증거는 없다. 서식 공백만 제거한 계산 크기는 약 459,131,089 byte로 같은 기존 한도 안이다.

완료 prefix를 재계산하거나 native 한도를 늘리지 않고 wrapper의 report publication adapter를 보완했다. 전체 compacted JSON을 원 native report/policy generation으로 검증해 모든 값과 policy bytes를 유지하고 원본 bytes를 보존한다. 새 byte hash만 reuse receipt에 결속한다. 다음 정상 entry-split 발행도 같은 adapter를 사용한다. 1 MiB physical line·원파일 2배 한도·파일/정책/receipt CAS와 archive hash를 확인하고, compacted 파일이 여전히 기존 한도를 넘으면 거부한다. 이벤트/원천/가격/비용/경제성/null/정책 값을 제거하거나 바꾸지 않는다.

Final handoff guard는 실제 native strict exit 2도 수용하며 이전 scoped proof의 hash·source date·origin run/commit·완료 command와 최대 8단 ancestry를 검증한다. 원 계산의 ID를 새 실행 ID로 재라벨링하지 않는다. Storage/profile/ancestry 및 admission·stage·wrapper 회귀 129 PASS, shell 문법·diff 검증 PASS다. 10/14 현재 checklist 목적·강제 규칙도 확인했으며 source/publication은 10/13, effective date는 10/14로 보존한다. 새 bot·order·provider·threshold 권한을 추가하지 않는다.

추가 provenance 점검에서 23:06:49 native broker-cost source는 직접 wrapper 호출의 기본 local account alias로 기록됐다. Raw provider response는 보존하며 승인된 account/journal alias의 비용 근거로 승계하지 않는다. 현재 비용/terminal 부족과 계정 결속 결손은 `source_gap`이고 `actual_profit_verified=false`·EV null을 유지한다. 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`/cost producer가 원 provider/account binding과 다음 정상 수집을 수용해야 한다. 이 결손을 매매 수량/보호 가드 변경 또는 비용 후 성과로 바꾸지 않는다.

Storage 보완 release `375f2ae28c2077bd94c667d23e638a3a8d1d0f30`는 원 account/journal 설정과 같은 33개 정책 코드/원천을 유지한다. 자정 뒤에는 봉인된 10/13 코드 인계와 불변 source/pointer/code byte를 검증해 source-only 역사 읽기 인계를 10/14에 결속했고, native `reversal_code_handoff.issue`로 새 release 인계를 발행했다(원천 789개). 기존 policy source 10/12·target 10/13, current pointer·expiry·값을 변경하거나 실제 PID 소비를 만들지 않았다. 다음 적용일 10/14 candidate는 source/publication 10/13으로 native 재결속됐다.

실제 storage compaction은 원본 `d98df62a…`를 보존하고 539,058,129→459,131,089 byte로 완료됐다. 새 byte SHA는 `955eda70d4de631e4fcdd06fa8670c41b94ea2ecce1100b66591060cb62bd5fc`, native generation `f9224cfaead3cb85ea13f4376085a1d3bf11795f37f1051b0088c40828c364c3`와 policy byte SHA `fae051dc…`는 그대로다. Main run `8d5af5c07e064471b0388c8499409f81`는 00:14:18 START, summary `direct_evidence_complete`·blocking reasons 0·entry-split semantic companion verified=true까지 통과했다.

00:16:46 family strict는 `direct_checklist_task_projection_mismatch` 한 건으로 종료했다. 기대 ID 6개/실제 ID 5개 차이는 이미 생성된 `HoldingProfitExitSourceContractRepair`를 검증 regex가 DirectFamily 접두사만 세어 누락한 버그다. Generator의 owner를 삭제하지 않고 verifier가 기대 ID·전체 generated ID·DirectFamily owner를 검사하도록 보완했다. 다른 manual task는 투영 밖에 유지하고, missing/duplicate/unexpected generated owner 및 schedule/hash guard는 보존한다. 실제 holding `policy_binding_gap` OPEN과 비용 부재는 경제성/후속 계약 수용이며 이번 문서 검증 버그를 가리지 않는다. Verifier·wrapper·stage·admission 회귀 152 PASS, compile·diff checks PASS, self review/re-review finding 0이다.

현재 수리 code commit은 `5cffbc22a61995d8d0233ca95bb2c95915610ba7`, 실제 장후 실행 root는 `/home/ubuntu/KORStockScan-runtime-releases/postclose-failed-stage-recovery-20261013-v5-5cffbc22a`다. Native 현재 정책 code handoff는 동일 정책 코드 33개·원천 790개, policy reselected/PID consumed=false로 검증했다. 기존 source/publication 10/13·적용 10/14의 candidate는 native bundle `dc73a05f05c22467bd039d916bf72e391f07a47e93827bec994a0a062ab1c2a6`로 결속했고 auxiliary stage exit 0·issues 0이다. 원 source와 native 실패 ID/완료 command ancestry는 유지하며 final handoff 검증을 재개했다. 작업본의 다른 사용자 I/O/REST 변경, Main bot/PID, 주문·threshold·quantity·provider 권한은 추가하지 않았다.

## 최종 재실행 종결 — 10/14 00:51 KST

- Main native run `195effbea22446479f7ff97eef091f4b`: 00:35:34 START, 00:38:00 `succeeded` / `verified_main_completed`, exit 0. Scoped proof는 원 `8d5af5c07e064471b0388c8499409f81`에 결속돼 있고 이전 실패·완료 command ancestry는 보존됐다.
- Main precommit 및 machine/compact family strict PASS, 최종 whole-native-chain strict는 00:46:10 PASS·issues 0·`whole_native_chain_done_claimed=true`다. Controller에 결속된 [attempt](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-10-13/da12722b8fe14e19a1f5403e06f33c3f.json)의 원 byte SHA가 현재 controller receipt와 일치한다.
- 활성 stage 7개 모두 `succeeded`, issues 0. Summary handoff 00:42:56 terminal, controller JSON 00:48:28 `done`, `postclose_all_active_stages_complete=true`. 다음 준비를 포함한 controller wrapper는 00:51:00 DONE·exit 0이다. Codex 자동 workorder/push는 기본 OFF 그대로다.
- Tuning wrapper는 00:42:11 success·exit 0. JSONL/DuckDB shadow 대조 delta 0이며 3일 window의 submitted events 5와 당일 Main unique submit 0을 혼동하지 않는다. Full/partial fill 0을 실현 EV/순익 0으로 바꾸지 않는다.
- [Readiness](/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/prepared/2026-10-14/2026-10-13_616c562850e98b4d_5cffbc22a61995d8/readiness.json): `prepared_verified`, source 10/13, target 10/14, commit `5cffbc22a…`, 00:51:00.554772. 준비 manifest/env/verification이 존재하고 index→receipt byte SHA가 일치한다. Controller SHA `616c562850e98b4da4621a6411eecf445b392b674d1831c9050ad7713e50c889`, summary SHA `4684e3307359b15d0874c7859e3bebf1dba562706776529bbe40a65db202dfb3`, manifest content SHA `2e2e887ddeed5ac58960d8c5fdd546c5196cf187fec391375d3b3539f8305e56`이다. Native preparation의 최종 candidate는 `2b3ebdb1b36afbece5525f725d7ee2cad8280f4bd71dcbfa30d563c92650d301`이며 selected commit과 일치한다.

준비의 `actual_pid_consumed=false`, `runtime_effect=false`, `day_of_activation_required=true`다. 예정된 05:35 최종화·07:35 PREOPEN·실제 다음 Main PID/자연 submit/비용 후 성과는 실행 전이며 완료로 바꾸지 않는다. 비용 account binding source_gap, holding `policy_binding_gap`, 충분한 실제 비교 표본은 현재 10/14 owner의 OPEN으로 남는다. 운영 source/strict/controller 완료와 경제성/실제 소비를 구분한다. Broad trading suites, 신규 provider replay, 전체 wrapper 재실행, 매매 재기동·주문, 외부 Project/Calendar sync는 수행하지 않았다. 표적 152 PASS·compile·shell·diff·print-only parser와 문서 owner/authority/link 검증으로 코드·문서 gate를 닫는다.
