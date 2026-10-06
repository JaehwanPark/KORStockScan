# 연속 반전 기계·보조 구현과 전체 장후 재생성 검토 — 2026-10-06

사용자가 통합 구현·반복 리뷰·최종 배포·EOD 제외 장후 전체 재실행·10/7 정상기동 준비를 승인했다. 원천/발행일은 10/6, effective는 10/7이다. 기존 workspace의 다른 수정·삭제는 이번 release에서 제외한다. 현재 실행 owner는 10/7 체크리스트의 기존 두 stable ID다.

## 구현과 연구 승계

연속 정규화 가격의 모든 하락→첫 상승을 공통 kernel에서 추출한다. 기계는 진입 ask 기준 비용 0.23%를 한 번 차감한 +0.4%/−3% 선후와 30분만 라벨에 사용한다. 미확정 row는 제외하며 같은 item 완료봉 보완에서도 선후/시각이 모호하면 제외한다. 누적 raw 승률의 12셀 선택을 native dated bundle에 넣고 PREOPEN은 동일 bundle hash를 활성화한다. 프리/애프터 0표본은 동일 유형 정규 payload와 hash를 그대로 승계하고 로컬 승률은 null이다. 정규도 0이면 검증된 이전 정규 부모를 승계하며, 확인 가능한 부모도 없으면 명시 실패로 남긴다.

보조는 연구 입력의 offline 설명을 운영의 중립적 관측 설명으로 교체한 실제 다섯 후보를 다시 호출했다. 총 2,232회 시도, 응답 ID 2,231개. 정확한 최종 요청 1,860개 중 응답 1,859개·timeout 1개이며, 교체 전 C 요청 372개는 구 hash로 보존·비교에서 제외한다. 최종 공통 기계 적격 비교 334개; 기계 선택 밖 37개와 timeout 1개를 제외한다. 원 PASS 누적 승률로 선택하며 응답 오류를 PASS로 고치지 않는다. 선택 셀의 PASS 계약 오류는 0개다. 표는 같은 자료에서 고른 연구 성과이며 독립/실현 승률이 아니다.

| 셀 | 기계 조건 | 기계 승/유효 | 보조 후보 | 실제 PASS 승/전체 PASS |
| --- | --- | ---: | --- | ---: |
| samsung\|PRE\|ALL | DROP_GE_1_0 | 2/2 | reversal_complete_source_v7 | 1/1 |
| samsung\|REGULAR\|ALL | DD5_GE_1_2 | 13/13 | reversal_fact_roles_v2 | 10/10 |
| samsung\|AFTER\|ALL | DD5_GE_0_4 | 207/686 | existing_wording | 4/8 |
| other\|PRE\|LT_20000 | DD5_0_8_VOL_UP | 709/870 | reversal_citation_v6 | 16/19 |
| other\|PRE\|20000_TO_100000 | DD5_0_8_VOL_UP | 500/712 | reversal_complete_source_v7 | 12/20 |
| other\|PRE\|GE_100000 | DD5_GE_1_2 | 76/76 | reversal_fact_roles_v2 | 23/23 |
| other\|REGULAR\|LT_20000 | DD5_0_8_REBOUND_LE_0_3 | 69610/85860 | reversal_complete_source_v7 | 16/19 |
| other\|REGULAR\|20000_TO_100000 | DD5_GE_1_2 | 20762/23796 | existing_wording | 10/10 |
| other\|REGULAR\|GE_100000 | DD5_0_8_VOL_UP | 1413/1915 | reversal_entry_geometry_v5 | 11/13 |
| other\|AFTER\|LT_20000 | DROP_0_4_REBOUND_LE_0_3 | 281/429 | reversal_citation_v6 | 7/12 |
| other\|AFTER\|20000_TO_100000 | DD5_0_8_REBOUND_LE_0_3 | 143/175 | reversal_citation_v6 | 17/21 |
| other\|AFTER\|GE_100000 | DD5_GE_0_4 | 221/405 | reversal_fact_roles_v2 | 17/28 |

## 리뷰·검증

발견·수리: SOR 관측 경로 누락, 새로운 typed fact 목록의 구 문자열 바인딩 오류, 필수 호가 결손에서 RECHECK 대신 예외 발생, 조용한 거래의 10틱 이력 손실, 버퍼 잘림으로 3개 연구 지점의 VWAP이 null이 되는 결함, per-cell 프롬프트 metadata와 실제 추론 설정 불일치, 구 장후 writer의 새 정책 역덮어쓰기, 이전 부모/스냅샷 손상에 대한 loader 재검증을 보완했다. provider/model 경로·주문·잔고·수량·자본/custody/manual/retirement·신선도/충돌·hard safety는 유지한다. 횟수 quota만 영구 None이며 간격·중복·timeout/외부 rate limit은 유지한다.

372개 동결 입력을 실시간 접두 방식으로 재생한 필수/선택 입력 수치 전부 일치, 해당 종목 원천의 반전 701,638개와 batch 모집단 전부 일치했다. 실제 엔진 다섯 보조 arm 모두 연구와 같은 입력·prompt·schema를 전송하고 PASS가 normal BUY 후보로 연결되는 fixture를 확인했다. 실제 주문은 생성하지 않는다. 당시 원 리뷰 527 PASS, 최종 운영/원천 485 PASS, stage/strict/bootstrap/wrapper 449 PASS, loader/registry/router/quota 280 PASS. 중복 실행을 포함한 수치이며 이들을 고유 테스트 수로 합산하지 않는다. 최종 추가 회귀·compile/정적 검사·diff/parser 결과는 실행 manifest에 고정한다. Kiwoom 요청/프로토콜/parser/FID mapping은 변경하지 않았고 기존 정규화 envelope의 후행 소비 hook만 추가했다.

## 운영 실행 계약

`THRESHOLD_CYCLE_REGENERATION_SCOPE=all_except_eod`는 기존 report-step 재사용을 끄고 새 generation ID를 status와 stage에 기록한다. 날짜 status를 삭제하지 않고 원 실패·중단·이전 성공 attempt를 보존한다. 전수 가격·완료봉·실제 AI 응답은 동일 hash cache 입력이며 새 계산/최종 consumer를 구 terminal로 대체하지 않는다. EOD updater는 실행하지 않고 원 정확일 terminal/hash를 비교한다. 새 두 단계 명령은 `scalping.continuous_reversal_postclose --mode machine/auxiliary`, 새 보조 의존성은 자체 반전 라벨을 포함한 `main_machine_policy`다. 기존 outcome_labels는 기존 거래/진단 consumer용으로 전체 실행에 포함한다. `legacy_machine_report`는 report-only 실행하며 새 native bundle을 덮어쓰지 않는다.

최종 release에서 main wrapper, 독립 machine refresh/tuning/archive, 등록 13 stage(OFF는 새 OFF receipt), summary/tower/checklist/strict/controller/finalization/cleanup/final detector와 prepared bootstrap을 새로 확인한다. 동일 stage를 동시 중복 dispatch하지 않는다. controller 자동 wrapper rerun은 수동 전체 run과 충돌하지 않게 해당 실행에서 끈다. native two-worker/자원 guard는 유지한다. 최종 checklist bytes 뒤 strict→controller→prepared 순으로 봉인한다. 07:35/07:55 예약 이전에는 PREOPEN/실제 PID 성공을 주장하지 않는다.

새 family의 `main_machine_policy`는 Main wrapper만 생성한다. 독립 machine group은 이를 다시 쓰지 않고 capacity/attribution/timing/weakness/allocation/legacy approval을 생성한다. 별도 group의 재계산이 보조 bundle의 기계 부모 hash를 바꾸는 결함을 제거했다. 실제 CLI 날짜 파싱을 포함한 회귀 173 PASS. 보조 stage와 native loader는 최종 실제 응답 JSONL의 byte hash도 함께 검증한다. 반전 원천 manifest·보조 연구 보고서·call freeze를 stage 출력 custody에 추가해 응답/선택 이후 변경을 stale로 검출한다.

## 현재 상태

현재 selected release는 prepared 순서 보완을 포함한 v9 `0d4e5d2a4004e89a20ea14eb05c720d812e5bb27`이다. 이 보완의 immutable 회귀 240 PASS, 기존 34개 source/deploy 불변 및 소유 파일 총 36개 hash/clean·cron 8개·기존 episode 186개 pin PASS다. 기계·보조 정책을 생성한 v8 `0e067426`의 관련 immutable 회귀 683 PASS·삼성 source-custody 34 PASS와 전체 재생성 기록은 이력으로 보존한다. source/publication 10/6·effective 10/7 generation `continuous-reversal-20261006-0e067426-20261007T035415`의 Main native는 03:54:16~04:14:46 성공했다. 기계·보조 scoped, 실제 최종 prompt consumer와 Main seal issues=[]를 확인했고 누적 승률 선택의 12+12셀·정책 bundle은 v9에서도 불변이다. 격리 PREOPEN 활성화/재실행·native parent CAS·actual pointer 불변 PASS, 독립 최종 갱신·archive·3 Parquet/압축 검증/대조 완료도 보존한다. v9의 마지막 정식 owned-log closed-target finalization은 07:03:11~07:05:03 완료했고 whole_native_chain strict/controller issues=[]·cleanup/DONE·최종 detector 7개 실행/fail 0을 확인했다. 새 prepared는 07:05:00 생성됐고 current_full_contract/require_today 검증 PASS·findings=[]다. 독립 cron consumer의 generation issues=[]이며 예정 종료 이후 복구는 recovered_late 경고로 보존한다. 앞선 06:34 복구의 정식 로그 인계 누락과 07:00 fail의 보완은 마지막 절을 따른다. 최종 detector에서 prepared 경고는 사라졌으며 기존 report-only 원천 경고는 남는다. 실제 07:35 PREOPEN/07:55 Main PID 소비는 아직 future-due이며 주문을 생성하지 않았다. 과거 실패·중단과 원천·실제 요청/응답·부모 snapshot은 보존한다.

## 최초 전체 실행에서 발견한 장후 결함

00:27:59 release `94153da8` 전체 재실행은 00:30:15 주문분할 보고서의 `execution_partition_decoded_byte_budget_exceeded`로 실패했다. 원 실패 terminal을 보존한다. 217개 작은 native shard가 총 84,971,567바이트여서 구 합계 64MiB 하한에 걸렸다. per-file 64MiB와 producer census/identity/date/중간변경 검증은 유지하고 합계 decoded IO만 명시적 256MiB로 보완했다. 198개 회귀 PASS 및 실제 295개 원천 이벤트의 stage별 count/identity와 producer census 완전 일치(ready, raw 미재조회)를 확인했다. 변경은 새 reviewed release로 배포하며 실행 중 v1을 편집하지 않는다.

00:40:27 release `879d324f` 재생성은 새 기계·보조 발행을 완료했으나 구 진단 보고서가 `entry_admission_recipe_contract_invalid`로 실패했다. 실제 source 10/6 부모는 이전 `pullback_p60_v0` 계약이며, 구 진단 후보가 threshold/version을 바꾼 뒤 recipe의 부모 hash를 갱신하지 않은 결함이다. 구 recipe 입력을 먼저 검증하고, 후보 생성 후 동일 recipe 조건으로 새 부모 hash를 결속하도록 수정했다. 손상된 원 recipe를 자동 수리하지 않는다. 251개 회귀와 실제 incumbent의 일반/발행 후보 계약 PASS. 새 반전 family의 채택·실시간 조건에는 이 구 recipe/EV/refinement를 추가하지 않는다. v2의 Main/tuning 그룹은 00:53:14 중단·잔여 0으로 보존하고 보완 immutable release에서 전체를 다시 생성한다.

추가 재리뷰에서 구 진단의 `--report-only`를 명시적 CLI로 분리했다. 이 경로는 publisher/activator를 호출하지 않으며 발행·즉시 활성화 인자와 동시에 사용할 수 없다. 전체 재생성에서는 기존 진단 report cache도 재사용하지 않는다. 다음 원천일의 현역 반전 bundle을 과거 전략으로 해석하지 않고 그 bundle이 보존한 정확 시장별 compatibility 정책으로만 구 진단을 수행한다. 새 family의 단일 발행 권한과 연구 모집단은 유지한다.

## v3 배포와 PREOPEN 격리 검증

당시 v3 선택 release는 `e39b98c0ea1b569cadb52207df4611e87dc5213a`였다. workspace의 소유 변경은 `1c688b95`에 분리 커밋했고, 27개 코드 파일 hash가 최종 immutable release와 같다. 해당 release의 추가 회귀 399 PASS와 미해결 범위 결함 0을 `final-code-review.json`에 기록한다. 누적 raw fraction 선택을 독립 재계산하고 native bundle `d0227b256b4b770e95b43eabbc858bcac1269a3df81df7b21416b8b8af13a246`의 기계·보조 각 12셀 및 원 연구 보고서·실제 응답 바이트 결속을 다시 확인했다.

실제 PREOPEN 활성화 함수와 native loader를 격리된 data namespace에서 10/7 07:35 시계로 실행했다. 첫 활성화 `activated`, 두 번째 `already_active`, native parent CAS·기계 12셀·보조 12셀·원천 검증 PASS다. 실제 current pointer는 바꾸지 않았으며 실제 PID 소비·주문은 발생하지 않았다. `isolated-preopen-rehearsal.json`은 내일 예정 소비의 코드 검증이고 자연 기동 영수증은 아니다. 설치된 Main PREOPEN은 07:35, 정상 시작은 07:55이며 최종 release pin을 확인했다.

## v3 장후 진단 재사용 결함 보완

v3의 legacy diagnostic은 01:01:24부터 반복 계산했다. 중단 없이 읽은 CPython 실행 프레임이 `_mechanistic_policy_rows`→구 strategy/recipe 검증에 위치했다. 후보 recipe 부모 hash를 올바르게 갱신한 보완이 기존 action-only 재사용 키까지 매번 바꿔, 실제 source의 동작 동등 80개 grid를 80번 평가하는 성능 회귀가 있었다. 검증된 recipe의 부모 결속 metadata만 offline action 키에서 제외하고 recipe 조건·strategy·veto·hierarchy·version은 유지한다. 원 후보 hash/판정 영수증·후속 독립 경제 진단은 그대로이며 운영 판정에는 캐시를 추가하지 않는다.

실제 10/6 부모의 80개 후보 키는 보완 뒤 1개다. recipe 유무×veto 유무의 전체 보고서·입력 동일성 및 손상 recipe의 fail-closed 회귀 6 PASS, 관련 전체 402 PASS. 원 v3 실패/중단·계산 기록을 보존하고 이 보완을 새 immutable release로 배포해 전체를 다시 생성한다. CPU PMU 표본 수집은 환경 미지원으로 수행하지 못했으며, native 프로세스의 함수명·파일 위치만 읽었다.

## 최종 v4 연구 승계 검증

최종 source의 27개 소유 파일이 workspace `a7cfc9a2`와 일치한다. 최종 bundle `0cecc5193564b27439471b84defb18196d938bf62f8fec12fba541bb164f541e`의 기계·보조 각 12셀 선택을 누적 raw fraction로 독립 재계산했다. source/publication 10/6·effective 10/7이며 위 표의 최종 선택·실제 응답 원문과 전부 일치한다. 선택된 원 PASS의 계약 오류 0, 새 발행에서 실제 AI 요청 0(정확 요청·응답 cache 재사용)이다. 연구 원문 호출 2,232회와 최종 비교 334점의 근거는 바뀌지 않는다.

이번 bundle을 새로운 격리 namespace에서 실제 PREOPEN 활성화·native loader로 다시 검증했다. 07:35 모의 시계에서 첫 활성화/재실행·native parent CAS·12+12셀·원천 hash PASS이며 실제 current pointer는 불변이다. `research-native-parity.json`, `isolated-preopen-rehearsal.json`, `final-code-review.json`, `deployment-receipt.json`이 최종 v4를 결속한다. 전체 terminal/prepared와 예정 자연 소비는 별도 영수증으로 마감한다.

## v4 최종 인계 결함과 v5 보완

v4의 native producer는 완료했으나 tower 미생성과 자동 체크리스트 projection 불일치로 Main terminal은 실패했다. 새 반전 family의 source/effective/publication 날짜를 구 evaluation 필드로 찾던 summary가 잘못된 `policy_missing` 및 legacy 진단을 선택했고, checklist validator는 새 `cumulative_winrate_selected`/`verified` 상태를 거부했다. 새 family의 실제 machine/auxiliary 보고서와 native bundle을 직접 연결하고 검증한 12셀을 승률 연구 상태로 인계한다. 경제적 우위·즉시 적용 권한은 이 상태에서 주장하지 않는다. 최종 wrapper가 summary→tower→checklist→strict 순서로 생성한다. 검증된 정확일 family에 한해 기존 수동 통합 owner 두 개를 한 번씩 보존하며 중복·자동영역 drift는 여전히 거부한다.

실제 원천에서 bounded consumer 재생·strict `pass`, issues=[]를 확인했다(`v5-real-source-strict-review.json`). 이 검토는 Main terminal 봉인이나 운영 활성화가 아니다. 관련 회귀 512 PASS, Python compile/소스 lint/shell syntax/diff 검증 PASS 뒤 최종 immutable release를 만들고 전체를 다시 생성한다. 원 실패 status·v4 summary/checklist·실행 이력은 보존한다.

최종 v5는 `53fdecfab8545073b057c4ecc023cad9e6953dbb`이다. immutable 512 PASS, source/deploy 30개 hash 일치·clean, cron 8개/release-set/기존 episode 186 pin PASS 뒤 03:00:51 source/publication 10/6, effective 10/7 전체 generation `continuous-reversal-20261006-53fdecfa-20261007T030051`을 시작했다. Main/archive/독립 machine/tuning은 별도 실행 owner이며 EOD hash는 그대로다.

## v5 독립 삼성 구 연구 실패 영수증 경로 보완

독립 machine의 필수 6단계와 summary는 성공했으나 선택적 삼성 frozen 연구가 봉인된 9/29 capture gzip hash 변경을 거부했다. 공유 data ancestor alias를 generation-safe writer에 그대로 넘겨 실패 영수증 저장마저 `Not a directory: data`로 가린 adapter 결함을 수리했다. data mount alias만 canonical로 바꾸고 하위 symlink·원천/후보 봉인은 그대로 검사한다. 구 frozen 연구의 source gap은 sealed 실패로 보존하고 새 연속 반전 정책의 표본·채택·기동 gate에 포함하지 않는다. 원 frozen/hash는 재작성하지 않는다. 전체 작업은 이 보완을 포함한 v6에서 다시 실행한다. 관련 sidecar·연구 소비 회귀를 별도로 확인했다. unrelated 기존 semantic coverage의 episode kernel tamper assertion은 현행 verify-kernel 경계와 불일치하여 통과를 주장하지 않는다. 기존 test 파일 lint 4개는 변경 밖 경고로 보존한다.

최종 v6 immutable 검증은 장후 인계 512 PASS와 삼성 sidecar/consumer 34 PASS이며 소유 source/deploy 32개 hash가 workspace와 일치한다. cron 8개와 기존 독립 episode 186 pin을 보존했다. 전체 generation은 `continuous-reversal-20261006-36585af0-20261007T030906`이고 실제 Main PID는 아직 기동하지 않았다.

## 최종 v6 재실행의 잠금 경합 해소

첫 v6 Main은 새 기계/보조를 생성한 후 스냅샷 wrapper의 `lock_busy` skip을 정확히 stale generation으로 거부했다. 원인은 v5 중단 때 부모 PGID를 벗어난 timeout/스냅샷 자식 두 개가 남은 실행 정리 결손이었다. v5/v6의 명시 generation ID로 `/proc`을 전수 조사해 관련 group만 종료하고 생존 프로세스 0을 확인했다. 잠금 파일이나 원천·실행 status는 삭제하지 않았다. 같은 최종 코드에서 03:13:53 전체를 새 generation `continuous-reversal-20261006-36585af0-20261007T031353`으로 다시 실행했다. 이전 실패·중단·경합 영수증은 별도 보존한다.

## 최종 오류 탐지 consumer의 새 family 승계

기계/보조 연구 producer와 direct summary는 정상이었으나 오류 탐지기의 보조 semantic consumer가 새 보고서를 구 paired economics schema로 읽어 `auxiliary_stage_report_contract_invalid`를 보고했다. 기계 semantic 역시 새 family의 단일 판정 기준 대신 구 diagnostic을 먼저 읽던 경계를 보완했다. 최종 detector는 실제 새 연구 보고서·native bundle·12셀·actual-response custody·source/effective date·완료 stage와 표준 alias hash를 직접 검사한다. pending은 미관측이며, missing/failed/corrupt는 계속 source_invalid다. 구 경제/holdout 판정은 새 family에 추가하지 않는다. 실제 두 family는 `cumulative_winrate_selected`, findings=[]다. 관련 정상/손상/누락/실패/진행 중 회귀와 기존 artifact suite 185 PASS를 확인했고 final v7에 포함해 전체를 다시 실행한다.

## v7 최종 compact 소비 순서와 v8 보완

v7는 모든 producer와 스냅샷을 새로 완료하고 기계 scoped 검증 issues=[]를 얻었으나, compact verifier가 읽을 `main_ai_prompt_consumer_2026-10-06.json`을 Main wrapper가 생성하지 않아 마지막 인계가 실패했다. consumer를 수동 검토 생성하면 scoped 검증은 통과했지만, 구 optimizer EV/cohort 상태를 먼저 읽는 CLI는 exit 2를 반환했다. 새 family는 native bundle/실제 연구 보고서를 먼저 검증하고 `ready_continuous_reversal_handoff` 영수증을 발행하도록 전환했다. prior submitted cohort는 not-applicable, 미분류 수는 unknown이며 EV·holdout·표본 하한을 재도입하지 않는다. provider/활성화/주문/PID는 false다. Main wrapper가 최종 summary/checklist 후 이 consumer를 먼저 생성한 뒤 compact 검증한다. 실제 CLI exit 0·compact scoped pass와 관련 producer/legacy consumer/실행 순서 회귀를 확인했다. 원 Main 실패는 보존하고 최종 v8에서 전체를 다시 생성한다.

## 최종 장후 경고의 범위

최종 detector는 7개를 모두 실행하고 fail 0, warning 상태로 완료했다. 새 Main 기계·보조 semantic은 누적 raw 승률 선택과 source/effective/native/실제 응답 hash를 검증했고 findings=[]다. 기존 episode report의 `episode_native_source_gap`·`episode_capture_invalid_events`, report-only 삼성 동결 후보의 `samsung_forward_execution_failed`, 구 workorder 미생성·원 EOD completed_with_warnings·변하지 않은 역사 로그가 경고로 남았다. 이 경고를 새 반전 정책의 실패 또는 원천 결손의 0손익으로 바꾸지 않는다. 기존 에피소드의 정책 pin/예약기동 owner는 보존하며 새 정책 연구에는 결손 원천을 포함하지 않는다. 최종화 작업이 자기 detector를 기다리는 `pending_self_audit`는 native 종결 후 DONE으로 확인한다.

## 최종 종결 영수증 — 10/7 04:22

| 항목 | 실제 결과 |
|---|---|
| Main native | 03:54:16~04:14:46 succeeded; run `471741271c024386a8384a110d8d5482` |
| 등록 stage | 13개: 활성 11 succeeded·퇴역/OFF 2 off, 동일 generation |
| 독립 최종 갱신 | native exit 0, Main 기계 부모/bundle SHA 불변 |
| archive / tuning | 새 DONE / 3 Parquet·검증된 압축·shadow 대조 5단계 success |
| 최종 strict / controller | whole_native_chain pass, issues=[] / done |
| finalization / cleanup / detector | 04:22:07 DONE / DONE / 7개 실행, fail 0·기존 원천 경고 보존 |
| 10/7 준비 | prepared_verified; require_today 검증 pass, findings=[] |
| 연구 승계 | machine 12셀·actual AI auxiliary 12셀, 독립 raw fraction 재선택 일치 |
| 정리 후 원천/코드 | EOD 불변·재실행 없음; 110 동결 원천+호출/응답 로그 2개 불변; 34 source/deploy hash 일치 |
| 남은 자연 소비 | 07:32 owner / 07:35 Main PREOPEN / 07:55 정상 Main PID, future_due |

04:22 종결 당시 bundle SHA는 `bf15fc240560605b7fe08796941288d9ef28a5f7c8d2cbf47692787b894f4a98`, 체크리스트 SHA는 `ee7d1ba223448108b11c3fa438cc31b58ded7bae817895d240852358ce2df731`이다. 이후 05:00 예약 최종화와 아래 경고 보완의 owner 기록을 반영한 새 체크리스트로 다시 봉인했다. 보조 통합 owner는 완료해 Main owner로 인계했고 Main owner는 예약 소비 확인을 위해 PREOPEN OPEN으로 유지한다. 새 prepared 이후 체크리스트 bytes는 수동 변경하지 않는다. 실제 정책 current pointer·Main PID 활성화·주문·체결은 만들지 않았다.

실행 근거: [최종 종결](../../data/report/continuous_reversal/2026-10-06/final-completion.json), [전체 재생성](../../data/report/continuous_reversal/2026-10-06/full-regeneration-execution.json), [연구/운영 12셀 일치](../../data/report/continuous_reversal/2026-10-06/research-native-parity.json), [PREOPEN 격리 검증](../../data/report/continuous_reversal/2026-10-06/isolated-preopen-rehearsal.json), [정리 후 원천 보존](../../data/report/continuous_reversal/2026-10-06/final-integrity.json), [최종 native log](../../data/report/continuous_reversal/2026-10-06/finalization-v8-20261007.log).

검증 범위는 변경된 producer/consumer·wrapper·policy/loader·quota·source-custody 계약이다. 전체 프로젝트 회귀 통과나 향후 자연 판정/제출/실현 손익 개선을 주장하지 않는다. 기존 episode assertion 불일치와 원천 경고의 경계는 위에 보존했다.

## 05:01 경고 intake와 prepared 순서 결함 보완

예약 최종화는 05:00:01 시작해 새 controller `19d55b8515db312c32630a5296b5efd45b6922d300d73010718560973061a732`를 발행했다. 05:01:46 최종 detector가 읽은 prepared는 04:22 이전 controller에 결속돼 `prepared_source_or_release_changed`였다. 05:01:50 같은 예약 run의 prepared_verified/DONE이 이어졌으며, 06:24 직접 `next_preopen_readiness --verify --target-date 2026-10-07 --require-today`는 current_full_contract PASS·findings=[]다. 원 경고·원 terminal은 보존한다.

원인은 consumer 실행 순서다. 새 prepared 검증을 cleanup 뒤 detector 앞에 두고 prepare/session/cutoff 실패에서도 진단 detector를 실행하되 DONE을 금지했다. happy path에서 detector가 실제 현재 controller와 일치하는 prepared를 읽는 실행 회귀, 준비 실패와 탐지 실패의 DONE 금지, 기존 source/hash/schema/날짜 안전 회귀 240 PASS를 새 immutable `0d4e5d2a4004e89a20ea14eb05c720d812e5bb27`에서 확인했다. 변경은 기존 finalization wrapper와 그 테스트뿐이다. 계보·policies·주문·provider·원천 guard 완화나 AI 호출은 없다.

에피소드 두 경고는 실제 report-only 결손이다. 31개 source_gap: durable_profile_observation_missing_or_invalid 27개·durable_state_generation_mismatch 4개. capture 1,203개(유효 648·계보 invalid 555)를 기록하고 부적격 연구 입력을 제외한다. 다른 종목군 Main 전수 반전의 연구 승계·정책 준비 실패로 전역 확장하지 않는다. 현역 episode의 기존 186개 policy pin은 그대로이며, 과거 관측을 소급 생성하지 않는다. 새 관측의 계보 수용은 기존 EpisodeCaptureSequence1006 owner에 인계한다.

v9 native 복구는 06:34:08 DONE이다. 06:34:05 prepared 생성 뒤 최종 detector가 같은 controller/selection 결속을 검증했고 `next_preopen_prepared_contract_invalid`는 없다. whole_native_chain strict pass·issues=[]와 현재 세대/최종 detector report hash를 다시 대조했다. 기계·보조 각 12셀 및 bundle·EOD 원본·동결 원천 110개·실제 호출/응답 로그 2개는 불변이다. 기존 episode 두 경고와 별도 구 삼성 동결 연구의 source 변경 실패는 보존하며 이를 Main 신규 정책의 준비 실패로 바꾸지 않는다. 원 Main 학습·EOD는 재실행하지 않았다. 최종 근거는 [경고 보완 종결 영수증](../../data/report/continuous_reversal/2026-10-06/prepared-alert-repair-20261007.json)과 [v9 native 로그](../../data/report/continuous_reversal/2026-10-06/prepared-alert-recovery-20261007.log)다. 07:35/07:55 자연 소비의 수용은 기존 Main PREOPEN OPEN에서 확인한다.


## 07:00 finalization cron 소비 실패와 원인

07:00:03 `cron_completion`은 정식 `logs/postclose_finalization_cron.log`의 05:01:50 DONE chain `48d6bd04...`를 읽었다. 현재 chain `8a4926eb...`는 06:34 audit 복구 로그와 정확히 일치하고 준비 전체 계약은 PASS다. controller/정책의 이후 변경이 아니라, 앞선 수동 복구를 정식 owned logger로 실행하지 않은 작업 인계 누락이다. 06:34 자기 child detector의 `pending_self_audit`를 독립 cron 소비 완료로 확대해 보고한 종결 범위도 바로잡는다.

07:00 원 실패 보고서는 [보존 사본](../../data/report/continuous_reversal/2026-10-06/error-detection-070003-before-finalization-log-repair.json)으로 고정했다. reviewed v9의 native 정확일 복구를 정식 owned logger에서 실행하고 현재 generation/원천 보존/독립 last consumer/장전 준비를 재검증한다. 새 코드 배포나 Main/EOD 재생성은 필요하지 않으며 늦은 복구 자체는 경고로 보존한다. [점검·복구 영수증](../../data/report/continuous_reversal/2026-10-06/finalization-log-handoff-alert-20261007.json)을 따른다.


07:05:03 정식 owned-log 복구 exit 0/DONE, 07:05:00 prepared_verified를 확인했다. 정식 최신 DONE의 chain `429bfb8a5747d9c30fcc5974342aed3fa36c7084c650dbae8e5d6c7239dbe280`과 snapshot `cd83b048db1745630e0fcea8e0ddf3f8fcde8f45d6af04f8bb4826f853d36158`는 현재와 일치한다. native child detector 7개/fail 0과 run/report SHA를 대조했다. 자기 ancestor 환경·실행이 없는 독립 [실제 cron 소비 결과](../../data/report/continuous_reversal/2026-10-06/finalization-cron-consumer-after-0700-repair-20261007.json)는 warning/`recovered_late`, generation issues=[]다. 예정 06:50 이후 복구라는 경고는 삭제하거나 PASS로 바꾸지 않는다. 현재 준비의 current_full_contract/require_today는 PASS·findings=[]다.

이번 보완은 정식 호출·로그 인계와 관련 문서뿐이며 새 코드 변경/배포·provider 호출·Main 학습·EOD·bot 기동·주문은 없다. 따라서 코드 pytest를 반복하지 않았고 native 실제 실행·현재 source/strict/prepared hash·독립 consumer·문서 parser/link/owner를 검증했다. v9 코드 36개, 기계/보조 12+12셀 bundle, EOD, 동결 원천 110개와 실제 호출/응답 로그 2개는 SHA 불변이다. 원 07:00 report는 당시 실패 이력이며 다음 자연 detector 보고서와 구분한다. 정식 복구 구간은 [원 로그의 보존 사본](../../data/report/continuous_reversal/2026-10-06/finalization-owned-recovery-20261007.log)으로 남겼다. 새 prepared 이후 체크리스트 bytes를 수동 변경하지 않는다. 07:35 PREOPEN/07:55 실제 Main PID 소비는 기존 OPEN의 후속 수용이다.


07:07:14 동일 selected v9에서 현재 시각의 독립 [full 읽기 전용 재검증](../../data/report/continuous_reversal/2026-10-06/finalization-full-readonly-after-0700-repair-20261007.json)을 실행했다. initialized/expected/completed 7개, fail 0·runtime mutation none·operational mutation 0이다. cron의 최종화는 recovered_late/세대 결함 없음이며 전체 severity는 warning이다. 이 실행은 dry_run으로 filesystem maintenance나 notifier를 호출하지 않고 별도 review 보고서에만 저장했다. 원 07:00 canonical report는 그 시각의 실패 이력으로 보존하고 다음 예약 full detector가 새로 발행하도록 둔다.
