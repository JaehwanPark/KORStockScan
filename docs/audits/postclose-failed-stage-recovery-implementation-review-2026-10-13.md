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
