# 연속 반전 기계·보조 구현과 전체 장후 재생성 검토 — 2026-10-06

사용자가 통합 구현·반복 리뷰·최종 배포·EOD 제외 장후 전체 재실행·10/7 정상기동 준비를 승인했다. 원천/발행일은 10/6, effective는 10/7이다. 기존 workspace의 다른 수정·삭제는 이번 release에서 제외한다. 현재 실행 owner는 10/7 체크리스트의 기존 두 stable ID다.

## 구현과 연구 승계

연속 정규화 가격의 모든 하락→첫 상승을 공통 kernel에서 추출한다. 기계는 진입 ask 기준 비용 0.23%를 한 번 차감한 +0.4%/−3% 선후와 30분만 라벨에 사용한다. 미확정 row는 제외하며 같은 item 완료봉 보완에서도 선후/시각이 모호하면 제외한다. 누적 raw 승률의 12셀 선택을 native dated bundle에 넣고 PREOPEN은 동일 bundle hash를 활성화한다. 프리/애프터 0표본은 동일 유형 정규 payload와 hash를 그대로 승계하고 로컬 승률은 null이다. 정규도 0이면 검증된 이전 정규 부모를 승계하며, 확인 가능한 부모도 없으면 명시 실패로 남긴다.

보조는 연구 입력의 offline 설명을 운영의 중립적 관측 설명으로 교체한 실제 다섯 후보를 다시 호출했다. 총 2,232회 시도, 응답 ID 2,231개. 정확한 최종 요청 1,860개 중 응답 1,859개·timeout 1개이며, 교체 전 C 요청 372개는 구 hash로 보존·비교에서 제외한다. 최종 공통 기계 적격 비교 334개; 기계 선택 밖 37개와 timeout 1개를 제외한다. 원 PASS 누적 승률로 선택하며 응답 오류를 PASS로 고치지 않는다. 선택 셀의 PASS 계약 오류는 0개다. 표는 같은 자료에서 고른 연구 성과이며 독립/실현 승률이 아니다.

| 셀 | 기계 조건 | 기계 승/유효 | 보조 후보 | 실제 PASS 승/전체 PASS |
| --- | --- | ---: | --- | ---: |
| samsung|PRE|ALL | DROP_GE_1_0 | 2/2 | reversal_complete_source_v7 | 1/1 |
| samsung|REGULAR|ALL | DD5_GE_1_2 | 13/13 | reversal_fact_roles_v2 | 10/10 |
| samsung|AFTER|ALL | DD5_GE_0_4 | 207/686 | existing_wording | 4/8 |
| other|PRE|LT_20000 | DD5_0_8_VOL_UP | 709/870 | reversal_citation_v6 | 16/19 |
| other|PRE|20000_TO_100000 | DD5_0_8_VOL_UP | 500/712 | reversal_complete_source_v7 | 12/20 |
| other|PRE|GE_100000 | DD5_GE_1_2 | 76/76 | reversal_fact_roles_v2 | 23/23 |
| other|REGULAR|LT_20000 | DD5_0_8_REBOUND_LE_0_3 | 69610/85860 | reversal_complete_source_v7 | 16/19 |
| other|REGULAR|20000_TO_100000 | DD5_GE_1_2 | 20762/23796 | existing_wording | 10/10 |
| other|REGULAR|GE_100000 | DD5_0_8_VOL_UP | 1413/1915 | reversal_entry_geometry_v5 | 11/13 |
| other|AFTER|LT_20000 | DROP_0_4_REBOUND_LE_0_3 | 281/429 | reversal_citation_v6 | 7/12 |
| other|AFTER|20000_TO_100000 | DD5_0_8_REBOUND_LE_0_3 | 143/175 | reversal_citation_v6 | 17/21 |
| other|AFTER|GE_100000 | DD5_GE_0_4 | 221/405 | reversal_fact_roles_v2 | 17/28 |

## 리뷰·검증

발견·수리: SOR 관측 경로 누락, 새로운 typed fact 목록의 구 문자열 바인딩 오류, 필수 호가 결손에서 RECHECK 대신 예외 발생, 조용한 거래의 10틱 이력 손실, 버퍼 잘림으로 3개 연구 지점의 VWAP이 null이 되는 결함, per-cell 프롬프트 metadata와 실제 추론 설정 불일치, 구 장후 writer의 새 정책 역덮어쓰기, 이전 부모/스냅샷 손상에 대한 loader 재검증을 보완했다. provider/model 경로·주문·잔고·수량·자본/custody/manual/retirement·신선도/충돌·hard safety는 유지한다. 횟수 quota만 영구 None이며 간격·중복·timeout/외부 rate limit은 유지한다.

372개 동결 입력을 실시간 접두 방식으로 재생한 필수/선택 입력 수치 전부 일치, 해당 종목 원천의 반전 701,638개와 batch 모집단 전부 일치했다. 실제 엔진 다섯 보조 arm 모두 연구와 같은 입력·prompt·schema를 전송하고 PASS가 normal BUY 후보로 연결되는 fixture를 확인했다. 실제 주문은 생성하지 않는다. 당시 원 리뷰 527 PASS, 최종 운영/원천 485 PASS, stage/strict/bootstrap/wrapper 449 PASS, loader/registry/router/quota 280 PASS. 중복 실행을 포함한 수치이며 이들을 고유 테스트 수로 합산하지 않는다. 최종 추가 회귀·compile/정적 검사·diff/parser 결과는 실행 manifest에 고정한다. Kiwoom 요청/프로토콜/parser/FID mapping은 변경하지 않았고 기존 정규화 envelope의 후행 소비 hook만 추가했다.

## 운영 실행 계약

`THRESHOLD_CYCLE_REGENERATION_SCOPE=all_except_eod`는 기존 report-step 재사용을 끄고 새 generation ID를 status와 stage에 기록한다. 날짜 status를 삭제하지 않고 원 실패·중단·이전 성공 attempt를 보존한다. 전수 가격·완료봉·실제 AI 응답은 동일 hash cache 입력이며 새 계산/최종 consumer를 구 terminal로 대체하지 않는다. EOD updater는 실행하지 않고 원 정확일 terminal/hash를 비교한다. 새 두 단계 명령은 `scalping.continuous_reversal_postclose --mode machine/auxiliary`, 새 보조 의존성은 자체 반전 라벨을 포함한 `main_machine_policy`다. 기존 outcome_labels는 기존 거래/진단 consumer용으로 전체 실행에 포함한다. `legacy_machine_report`는 report-only 실행하며 새 native bundle을 덮어쓰지 않는다.

최종 release에서 main wrapper, 독립 machine refresh/tuning/archive, 등록 13 stage(OFF는 새 OFF receipt), summary/tower/checklist/strict/controller/finalization/cleanup/final detector와 prepared bootstrap을 새로 확인한다. 동일 stage를 동시 중복 dispatch하지 않는다. controller 자동 wrapper rerun은 수동 전체 run과 충돌하지 않게 해당 실행에서 끈다. native two-worker/자원 guard는 유지한다. 최종 checklist bytes 뒤 strict→controller→prepared 순으로 봉인한다. 07:35/07:55 예약 이전에는 PREOPEN/실제 PID 성공을 주장하지 않는다.

새 family의 `main_machine_policy`는 Main wrapper만 생성한다. 독립 machine group은 이를 다시 쓰지 않고 capacity/attribution/timing/weakness/allocation/legacy approval을 생성한다. 별도 group의 재계산이 보조 bundle의 기계 부모 hash를 바꾸는 결함을 제거했다. 실제 CLI 날짜 파싱을 포함한 회귀 173 PASS. 보조 stage와 native loader는 최종 실제 응답 JSONL의 byte hash도 함께 검증한다. 반전 원천 manifest·보조 연구 보고서·call freeze를 stage 출력 custody에 추가해 응답/선택 이후 변경을 stale로 검출한다.

## 현재 상태

코드/연구 검증 완료 후 release 선택과 전체 재실행을 이어간다. 배포·최신 terminal·prepared receipt·실제 예약 소비는 서로 다른 증거이며 결과가 생긴 뒤 아래 실행 영수증에 추가한다. 실행 기록: `data/report/continuous_reversal/2026-10-06/`; 원천/요청/응답/라벨과 부모 스냅샷을 보존한다.


## 최초 전체 실행에서 발견한 장후 결함

00:27:59 release `94153da8` 전체 재실행은 00:30:15 주문분할 보고서의 `execution_partition_decoded_byte_budget_exceeded`로 실패했다. 원 실패 terminal을 보존한다. 217개 작은 native shard가 총 84,971,567바이트여서 구 합계 64MiB 하한에 걸렸다. per-file 64MiB와 producer census/identity/date/중간변경 검증은 유지하고 합계 decoded IO만 명시적 256MiB로 보완했다. 198개 회귀 PASS 및 실제 295개 원천 이벤트의 stage별 count/identity와 producer census 완전 일치(ready, raw 미재조회)를 확인했다. 변경은 새 reviewed release로 배포하며 실행 중 v1을 편집하지 않는다.

00:40:27 release `879d324f` 재생성은 새 기계·보조 발행을 완료했으나 구 진단 보고서가 `entry_admission_recipe_contract_invalid`로 실패했다. 실제 source 10/6 부모는 이전 `pullback_p60_v0` 계약이며, 구 진단 후보가 threshold/version을 바꾼 뒤 recipe의 부모 hash를 갱신하지 않은 결함이다. 구 recipe 입력을 먼저 검증하고, 후보 생성 후 동일 recipe 조건으로 새 부모 hash를 결속하도록 수정했다. 손상된 원 recipe를 자동 수리하지 않는다. 251개 회귀와 실제 incumbent의 일반/발행 후보 계약 PASS. 새 반전 family의 채택·실시간 조건에는 이 구 recipe/EV/refinement를 추가하지 않는다. v2의 Main/tuning 그룹은 00:53:14 중단·잔여 0으로 보존하고 보완 immutable release에서 전체를 다시 생성한다.

추가 재리뷰에서 구 진단의 `--report-only`를 명시적 CLI로 분리했다. 이 경로는 publisher/activator를 호출하지 않으며 발행·즉시 활성화 인자와 동시에 사용할 수 없다. 전체 재생성에서는 기존 진단 report cache도 재사용하지 않는다. 다음 원천일의 현역 반전 bundle을 과거 전략으로 해석하지 않고 그 bundle이 보존한 정확 시장별 compatibility 정책으로만 구 진단을 수행한다. 새 family의 단일 발행 권한과 연구 모집단은 유지한다.
