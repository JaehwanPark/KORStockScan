# 장중 생산자–장후 소비자 S6 수리 보고서 — S5-FIN-04 다음 PREOPEN 원천 pointer·세대 결속

실행일: 2026-09-27 KST. 인계: [S5 전체 체인](./2026-09-27-intraday-postclose-handoff-S5.md) `S5-FIN-04`, [S6 세 번째 묶음](./2026-09-27-intraday-postclose-handoff-S6-S5-FIN-03.md). 이 묶음은 장후 summary의 미래 pointer와 bootstrap 생산자·첫 장후 reader를 수리했다. 실제 9/28 정규 PREOPEN이나 PID 검증은 실행하지 않았다.

## 결정과 실제 원천 재현

9/23 [runtime summary](../../data/report/runtime_approval_summary/runtime_approval_summary_2026-09-23.json)의 byte SHA는 `ecd8024afbd75025c2d9204cf8452bee806b285d084f280d620db79837aecea0`이다. `preopen_consumption_receipt`는 source date 9/23, apply date 9/28과 두 미래 파일의 절대 경로를 기록하지만, 당시 byte SHA와 현재 파일이 다르다.

| 생산자 → artifact → 첫 소비자 | 9/23 pointer / 현재 관측 | 수리 후 판정 |
| --- | --- | --- |
| 장후 `runtime_approval_summary` → `preopen_consumption_receipt` → `postclose_summary_handoff`의 미래 marker·검증 | manifest SHA `1c74ce0726fed2033a93cb5d8171af4604e49a91d296181c2dcd068584b4c0ba` → 현재 `18272d0efdce028431b932c416a65ed3218c8bcfc2b8da24be86d10a4bbc01bb`; verify SHA `b120705549ba1b3d85f4c25c2670dc9684c98b230488eaa208ded2283cbfdbf4` → 현재 `65a11f793744bb2fb7f868b13dc8a9c21b9538492595171b25ff8cdcf42c44f8` | 같은 세대 아님. 명시적 전이 영수증도 없으므로 `stale` |
| bootstrap manifest·env → source-only verify → 다음 PREOPEN loader | 현재 manifest 논리 SHA `7ca35bc5eb3bc09ee120967c26c13b1cd708e219e8d98abaa0a17ff470544d90`, env byte SHA `bb5c41fa6240c2d78777684a8c6303d958e571ae55119ec72e00fb93fed1c4cc`; verify `pass`, `pid=null`, `pid_passed=null` | 파일 검증과 PID 소비는 별도. 실제 PID·정규 9/28 PREOPEN status 미관측 |
| release selector → manifest 선택 release → 세대 전이 생산자 | 현재 selector byte SHA `d0a342e3ea16007225cc14796df40c0ad3ff53fbcb056cfacaddb642c605639f`, commit `fcc57536b08577320c6a59067b5463fb4a90a7c9`; manifest 선택 commit `e946f97e1bc571e8b43344f618d2215b2b00b7fd` | 선택 release 불일치. 현재 파일로 전이 영수증을 발행할 수 없으며 `future_transition_selected_release_mismatch` 유지 |

실제 자료는 읽기만 했다. 새 reader의 `inspect_future_handoff`는 `stale`과 위 release 불일치를 반환하며, 장후 직접 소비자 `verify_summary_handoff`는 `postclose_summary_handoff:future_preopen_generation_stale`을 기록한다. 과거 bootstrap `pass`나 파일 존재를 PREOPEN 완료·PID 소비로 읽지 않는다. 9/23 capacity 실패, allocation 보류, summary 실패와 기존 strict/checklist 세대 결손도 그대로다.

## 수리한 세대 계약

| 경계 | 구현과 닫힘 검사 |
| --- | --- |
| 장후 summary 생산자 | 미래 manifest·verify가 없으면 경로/source/apply date와 null SHA를 `pending`으로 기록한다. 존재할 때는 byte SHA, manifest 논리 SHA, env SHA, 선택 release commit과 selector 파일 SHA, PID receipt 필드를 분리한다. bootstrap의 `source_incumbent_target_date`는 장후 source date와 다른 독립 날짜이며 apply date 이전 유효 날짜로 검사한다. |
| 미래 marker·장후 첫 reader | marker v2는 원래 pointer SHA를 보존하고 `actual_pid_consumed=false`를 명시한다. reader는 날짜·절대 경로·manifest self-hash·env SHA·verify→manifest 논리 SHA·선택 release/selector SHA를 재검증한다. 현재 byte 세대 일치 또는 원래 summary byte SHA에 결속된 명시적 전이 영수증만 수용한다. 누락 둘 다와 null pointer는 `pending`, 일부 누락·변조·선택 변경은 `stale`, 실패 verify는 `rejected`, 명시적 source `OFF`는 `off`, `selected_families=[]`는 검증된 `valid_empty`로 분리한다. |
| bootstrap 생산자 → PREOPEN CLI 첫 소비 | source-only `--write`의 verify `pass` 뒤, 원 summary SHA·기존 pointer SHA·새 manifest/verify byte SHA·논리 SHA·env SHA·selector SHA/commit·정책 receipt digest를 담은 content-addressed 전이 영수증을 배타적으로 기록한다. 같은 적용일을 가리키는 장후 summary가 여러 개면 각각 전이한다. 실패한 세대 연결은 CLI exit 1로 전파해 다음 PREOPEN 단계가 정상 완료로 진행하지 못하게 한다. 명시적 `OFF`는 전이를 건너뛰고 성공/실패와 구분한다. summary 부재는 `not_applicable`이다. `run_threshold_cycle_preopen.sh`의 기존 순서와 인자는 바꾸지 않았다. |

전이 영수증의 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_pid_consumed=false`다. 새 manifest·verify가 실제로 생성되더라도 영수증은 과거 장후 요약의 원래 byte SHA와 pointer를 남긴다. 뒤이은 재생성·재시도는 다른 경로의 불변 영수증을 요구한다. PID가 적힌 verify도 이 reader에서는 `pid_receipt_present`와 `actual_pid_consumed=false`로 분리하며, 정규 서비스 PID/env·정책 SHA의 자연 수용은 S8이다.

## 실패 회귀 → 구현 → 자가 리뷰·재검증

처음 작성한 전이 fixture는 함수 부재로 실패했다. 이어 실제 계약을 닮은 fixture에서 manifest incumbent date를 9/19, 장후 source date를 9/23으로 분리하자 잘못된 날짜 동등성 검사 때문에 전이가 거절됐다. 독립 날짜 검사를 고쳐 통과시켰다. 리뷰 중 여러 source summary 가운데 최신 하나만 전이하던 결손과, `OFF`를 실패로 뭉개던 결손을 발견해 각각 회귀 실패를 만든 뒤 보완했다. 또 source-only bootstrap verify는 `pass`인데 전이 발행이 `blocked`여도 CLI가 exit 0인 결손을 실패 회귀로 재현하고 exit 1로 수정했다. release selector가 같은 commit을 가리켜도 `release_root`가 상대 경로면 summary가 `verified`로 보이던 결손도 실패 회귀 후 거절하도록 고쳤다.

fixture는 미래 파일 부재 `pending` → 무영수증 재생성 `stale` → 동일 source/manifest/verify/selector 전이 수용 → verify 재작성 시 `stale` → 새 전이 영수증 수용 및 옛 영수증 보존, 두 source summary 동시 전이, 잘못된 날짜·선택 변경·실패 verify 거절, 명시적 `OFF`, 검증된 빈 선택, PID 없는 verify와 PID receipt의 자연 소비 미승격을 검사한다. `verify_summary_handoff`의 직접 reader도 stale issue 발생/동세대 해소를 검사한다. 재리뷰에서 현재 릴리스 선택 불일치가 실제 자료의 전이 발행을 막는 것을 확인했다. 이 묶음의 미해결 구현 결함은 0건이다.

| 검증 | 결과 |
| --- | --- |
| 영향 pytest: runtime summary, bootstrap, summary handoff, 다음 체크리스트, strict verifier, controller, finalizer, wrapper 계약 | **245 passed** |
| 변경 Python 파일 `py_compile` | 통과 |
| wrapper `bash -n`·계약 | wrapper 변경 없음. 기존 wrapper 계약 pytest 포함; `bash -n deploy/run_threshold_cycle_preopen.sh` 통과 |
| 문서 링크·owner·권한, print-only backlog parser | 연결된 S5·S6 문서 존재; parser 통과, 외부 sync 없음 |
| `git diff --check` | 통과 |

## 남은 위험·인계

이 수리는 미배포 작업본이다. 현재 선택 release는 수정된 bootstrap/reader를 포함한다는 증거가 없고, 실제 manifest의 선택 commit도 현재 selector와 다르다. 따라서 실제 9/23→9/28 pointer는 **OPEN/stale**이며 전이 영수증을 작성하지 않았다. 실제 9/28 정규 PREOPEN의 새 bootstrap·전이, 서비스 기동 뒤 PID/env·정책 hash와 자연 주문·성과는 S8에서 별도 증거로 수용한다. 장후 전체 terminal·strict·controller 자연 수용 및 성능은 S7/S8에 남는다. `S5-FIN-05` postclose_exit/detector와 `S1-COM-01-A` scanner 압축 reader는 별도 묶음이다. 앞선 S6 압축·capacity·strict 수리와 SOR→KRX 작업본 변경은 보존했다. 현재 KST 9/27 일일 체크리스트 파일은 없고 9/28 체크리스트만 있으므로, 9/28 항목을 9/27 현재 실행 owner로 대체하지 않았다.

실주문·정책·서비스·provider·threshold·배포를 변경하지 않았고 정규 장후작업·PREOPEN을 실행하지 않았다.
