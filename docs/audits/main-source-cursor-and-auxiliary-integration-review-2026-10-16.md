# 원천 감시 cursor·누적 보조연구 통합 검토 — 2026-10-16

사용자는 원천 경고 점검의 보완과 `7d62534e3` 연구 결과를 함께 코드리뷰·수정하고 배포·재기동하도록 승인했다. 본 문서는 배포 전 검토 기록이며 실제 전환·정책 발행·PID 결과는 별도 실행 증빙으로 확인한다.

## 범위와 리뷰 결과

- 선택 기준은 `601717805c1da3697c5730ecb2ab55b9ca9878e7`, Main PID334173/start20965797이다. 기본 dirty 작업본은 보존하고 `codex/auxiliary-cumulative-research-20261016`에서 연구 커밋 위에 수리했다.
- 이전 [누적 보조연구 검토](main-cumulative-auxiliary-research-implementation-review-2026-10-16.md)의 10개 원천일·확인점14,005·확정2,342/U11,663·실제 신규147회·평가67쌍·800/800회 기록은 보존한다. 전면 교체 비권고도 유지한다. 이번 승인으로 앞선 배포 대기 상태를 후속 실행할 수 있으나 과거 보고의 상태를 소급 수정하지 않는다.
- 코드 대상은 기존 `submission_bottleneck_monitor.pre_submit_delay_source_semantics`와 인접 회귀다. 연구의 nested fact/registry/prepare cache/날짜 coverage 수리도 통합한다. 신규 root 모듈·Kiwoom 요청/parser·REG/REMOVE/recovery 로직 변경은 없다.

## cursor 결함과 수리

기존 코드는 `emitted_at > as_of`인 행을 제외하면서 byte cursor는 개행 뒤로 이동했다. 다음 실행에서 해당 행을 재관측할 수 없어 raw117/summary118이 됐다. 생산자 원본118·summary118 및 정확 identity sum은 일치했다.

v3 cursor는 읽은 동일 날짜의 지원 event를 count/hash와 필요한 intent projection에 보존한다. 미래 행은 현재 intent 분석에서 제외하고, minute 비교는 기존 closed-minute/flush grace 뒤에만 수행한다. 새 as-of가 도달하면 보존한 행을 포함한다. 미래 행 뒤에 과거 시각 행이 있어도 byte 진행을 막거나 중복 집계하지 않는다. 원 cursor는 deep-copy하여 같은 입력 재실행이 호출자의 이전 상태를 바꾸지 않는다.

v2는 이미 행을 잃었을 수 있어 그대로 정상으로 승계하지 않는다. 기존 bounded raw 재관측·coverage 시작 경계로 이행하고 `raw_cursor_contract_migrated`를 기록한다. 전체2GB 원장 재생, 수동 cursor 삭제/초기화, 과거 incident의 복구 완료 처리는 하지 않는다. 기존 incident의 역사 결손은 보존한다.

회귀는 future/as-of 경계, 지원 stage와 delay quote, out-of-order 시각, 동일 cursor 재실행·입력 불변, 부분 행 뒤 append 완성, inode 교체, v2 이행을 포함한다. 실제 원본118행을 격리 replay하여 incremental/fresh 모두118 및 identity sum `3bb143cbaebf6115ad8fbbbadbcdaac8387572fdb883633158e2f97b0e055c6b`, mismatch0을 확인했다. fixture 시각을 실제 운영 감시의 정확 시작시각으로 주장하지 않는다.

## 보조후보의 발행 전 재검증

기존 평가 설정에는 native comparison 인계 표시가 없어 발행 gate를 그대로 통과할 수 없었다. gate를 완화하지 않고 같은 seed·모집단·현행/후보를 native-current 설정으로 재구성했다. 기존18쌍/3쌍의 확인점과 actual request ID가 모두 동일하고 원 응답을 exact 재사용함을 확인했다. 새 AI 호출0, 예산800/800 유지다. v2 compact registry는 자체 codec/schema/1024-token 설정을 그대로 사용하며 legacy native wrapper로 바꾸지 않는다.

적용 대상은 기존 승률 동률·TP 증가 기준의 다음 두 scope뿐이다. 다른 시장·가격대 또는 삼성으로 확장하지 않는다.

| scope | 현재 registry | 후보 registry | 비교 |
| --- | --- | --- | --- |
| `036930\|AFTER\|GE_100000\|SOR` | `0085eb9cc12424eb864d3ac096f7bc57b7f6190e64cd968f36fa138f394c77dc` | `61ac530e391d1347f67303abe37b67f1cbb40e4e3664ca068d9968e0e2b9a5d9` | 2쌍, TP1→2/FP0, 승률100% 유지 |
| `other_non_fixed\|PRE\|20000_TO_100000\|NXT` | `f2e63dbd719c34643e20a48ec53f5ec15118887460a14a22eb5e68643b89388e` | `ec913ae2518f10364d18c2ed254a22530ee9e89682ecd83b72e25d4b34362e20` | 3쌍, TP1→2/FP0, 승률100% 유지 |

발행은 새 선택 릴리스에서 native evaluation 재검증·부모 CAS·현행 scope binding 확인 후 기존 publisher로 수행한다. 기존 기계목록/신호/TTL/주문·보유·수동관리 가드는 유지한다. 발행·PID 소비·첫 자연 요청은 구분하며 오늘 PRE가 이미 끝났다는 점도 명시한다. 장후 승계는 기존 실제 유효 binding의 계보를 따른다.

## 남아 있는 종목별 수신 결손

003540/417860은 기존 exact lease의 local REG 완료·연결 단위 success와 종목 귀속 ACK를 구분한다. 19:45 WS snapshot에서도 두 종목의 수신 type과 quote/trade가 비어 있었다. 이전43개 결과는43개 lease이며 같은 lease의 결과 중복0이었다. 반복 로그를 API 장애나 반복 주문으로 세지 않는다.

이 자료만으로 거래소 무거래/구독 수용/전달 문제를 단정하거나 ACK·0B/0D·native 확인을 합성하지 않는다. 기존 bounded probe/회전 경로를 유지하고 새 PID의 같은 item/lease에서 실제 wire→정규화→native가 생겼는지 후속 확인한다. 미수신은 원천 결손으로 남으며 cursor 수리나 재기동 성공으로 종결하지 않는다. 실행 owner는 기존 `NonfixedDispatchReadinessReview1012`다.

## 검증과 배포 순서

- monitor/보조 튜닝·전환/ordered deploy/intraday handoff 회귀 **3,211 passed**. 앞선 연구 검증348건은 별도 이력이며 중복 실행을 유일 테스트 수로 합산하지 않는다.
- native 확인 parity는128 scope/76,800행/594 hits, 기존 배포본과 signal digest 동일·mismatch0이다. 바뀐 native contract 파일은 `reversal_cumulative_postclose.py`이며 후보 commit의 fresh code-handoff에 연결한다.
- actual118행 재현과 native adoption 재평가는 provider/order 호출0이다. 원 점검 보고·실패 attempt·원 trace/label/campaign은 보존한다.
- Python compile·diff·print-only parser를 확인한 clean candidate를 만든다. 현재 selector/PID/start, active-policy code handoff 및 delay/stop/holding 계약을 **Main 정지 전에** 검증한다. 원 정책/PREOPEN/strict/controller는 보존하고 정규 `ordered_intraday_deploy`를 사용한다.
- launch 후 정확 PID 소비, 기존 producer/lock을 통한 현재 observer, full detector를 확인한다. 두 보조 overlay는 명시한 평가를 재검증하여 발행하고 최종 binding/PID receipt를 확인한다. 수신 결손·관측 경계 pending·실현 경제성은 따로 보고한다.

정지 전 반복검토에서 첫c0fb7faab 후보의 delay code 검증이 `entry_consumer_unreviewed_change:src/engine/monitoring/submission_bottleneck_monitor.py`로 거부됐다. Main은 중지하지 않았다. 검증을 끄지 않고 기존 source-pair 경로에 원PREOPEN bytes→검토한 cursor bytes의 exact 두 해시만 추가했으며 before/after 변조·dirty verifier·원 digest 불일치 거부를 재검증한다. 첫 후보와 발급된 원 code-handoff는 실패 전 이력으로 보존한다.

Evidence: `/home/ubuntu/KORStockScan/tmp/source-gap-cursor-aux-integration-20261016/`, [원 점검](/home/ubuntu/KORStockScan/tmp/source-gap-alert-review-20261016-1923/report.md), [native 비교 인계](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/native-adoption-revalidation.json).
