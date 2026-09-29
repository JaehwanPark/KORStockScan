# S6 `S7-FIN02-01` — collector 과거 입력 세대 결속

실행일: **2026-09-29 KST**. 인계: [S7 실제 stage 격리 보고서](2026-09-28-intraday-postclose-handoff-S7-S5-FIN-02-actual-stage-isolation.md), [AI 압축 원천 S6 보고서](2026-09-27-intraday-postclose-handoff-S6.md). 범위는 `widget_collector_expansion_recommendation` 생산자와 `postclose_summary_handoff`의 `collector_recommendation` 첫 영수증 reader다. **작업본 계약 수리 및 fixture 수용**이며 운영 9/23 보고서·영수증, 선택 릴리스, PID와 자연 경제성의 수용이 아니다.

## 재현과 원천 분모

- 수정 전 `test_collector_rejects_missing_prior_history_instead_of_valid_empty`는 8/18 payload가 없는데도 CLI가 **exit 0**으로 추천 0건을 기록해 실패했다(요구값 `SOURCE_NOT_READY_EXIT_CODE=42`). `test_collector_receipt_rejects_removed_historical_payload`도 기존 stage 영수증의 `stage_receipt_issues=[]`가 유지되어 실패했다. 두 실패 회귀를 먼저 남겼다.
- 9/23 원천을 **읽기 전용**으로 열거한 결과 payload **44 논리 파일 / 구조적 JSON 행 54,754**, replay **33 파일 / 구조적 row 5,542**였다. 현재 파일들의 새 manifest SHA-256은 `8d593c0d641da319d75107e6c17e4683dbdf7644c5c63f3387f44cdf33cb047e`이고, 보존된 9/23 collector 보고서 SHA-256은 `b8711c2e52f45e3f1ca7bce02242cda62602b66253b04cc221a8ebd01bd937ae`다. 그 보고서에는 추천 7건과 44/33 경로 목록이 있으나 **파일별 옛 논리 SHA는 없다**. 새 manifest는 현재 파일에 대한 검증 값이며 9/23 당시 세대를 소급 증명하지 않는다. 위 행 수는 서로 다른 구조적 단위이고 적격 후보·주문·경제성 표본이 아니다.
- 고정 원천의 한 예인 `ai_decision_payloads_2026-09-23.jsonl.gz` 물리 SHA-256은 `a57d5fcd0d8cb64427cc2f8d6f9138a795b0aab8789c8324a74331b402df5877`이다. 과거 gzip은 해제 논리 SHA로 묶고, 같은 내용의 미압축본과 공존해도 한 논리 파일로 센다.

재현 명령: `.venv/bin/python -m pytest -q src/tests/test_widget_collector_expansion_recommendation.py::test_collector_rejects_missing_prior_history_instead_of_valid_empty src/tests/test_postclose_summary_handoff.py::test_collector_receipt_rejects_removed_historical_payload`. 실제 자료 열거는 `history_input_manifest(DEFAULT_PAYLOAD_DIR, DEFAULT_REPLAY_DIR, through_date=date(2026, 9, 23))`와 `history_anchor_issues(DEFAULT_OUTPUT_DIR, date(2026, 9, 23), manifest)`를 읽기 전용으로 호출했다. 후자는 기존 경로 목록에 대해 `[]`였다.

## 생산자→첫 소비자 수리

`widget_collector_expansion_recommendation.py`는 clean-baseline 이후 실제 reader가 열거하는 payload와 replay에 대해 source date·논리 경로·해제 SHA-256·해제 byte·구조적 원본/유효/제외/격리/미관측 건수를 `collector_history_input_manifest_v1`에 남긴다. 미관측 모집단은 추정하지 않아 `null`이며, 이 숫자는 경제성 적격 행이 아니라 구조적 입력이다. 후보 단계의 제외 사유는 기존 `exclusion_counts`에 별도로 남는다. 파일 날짜·replay schema/권한, 손상, 미압축·gzip 충돌과 읽는 동안 변경을 검사한다. replay gzip은 현재 reader가 지원하지 않으므로 명시적으로 거절한다. sentinel 이름은 **표시 전용** 입력으로, research-watch 설정은 추천 상태/용량에 영향을 주는 입력으로 구분하여 hash 또는 명시적 부재를 기록한다. 비용 비교는 코드의 effective-date 계약을 사용하며 broker 실제 비용으로 승격하지 않는다.

생산자 CLI는 이전 보고서의 경로 목록 또는 새 manifest를 최소 기대 집합으로 사용한다. 이전에 알려진 파일 누락은 추천 0건 대신 exit 42로 끝난다. 새 manifest가 있는 이전 보고서라면 과거 날짜 파일의 내용 변경도 거절한다. 기존 9/23 보고서처럼 경로만 있는 세대는 **path-only anchor**로 취급하고 당시 내용 동일성은 주장하지 않는다. anchor가 전혀 없는 첫 실행은 `collector_history_anchor_missing`으로 막는다. 계산 전후 manifest를 비교하고, 실제 report의 `feature_paths`·`replay_paths`와 manifest 경로를 묶는다.

`postclose_summary_handoff.py`는 새 결과의 history manifest를 현재 파일에서 독립 재계산하고 stage terminal의 `history_input_generation_sha256`과 맞춘다. 누락·late·변경 이력, 빠진 manifest, 다른 reader 경로는 기존 `succeeded` 영수증을 stale 또는 실패로 판정한다. child가 exit 42를 반환하거나 history 검증이 실패하면 `source_gap`으로 보존하며, **완전한 입력에서만** `no_qualified_candidate`를 유효한 빈 결과로 수용한다. collector stage code hash에는 직접 replay·비용·identity·watch reader와 JSONL reader 코드도 결속했다. 운영 9/23 보고서와 영수증은 수정하지 않았다.

## 자가 리뷰·검증·남은 위험

자가 리뷰에서 생산자 목록과 실제 loader 목록의 일치, 압축 공존의 이중 집계, 구세대 재사용, source 변경 중 계산, sentinel 표시 전용 경계, 설정 파일의 결정 영향, source gap의 빈 후보 오인, stage 코드 세대, OFF·실패·valid-empty를 점검했다. 보완 후 범위 내 미해결 코드 결함은 0이다. 임시 fixture는 **동세대 추천 7건**, **동세대 valid-empty 0건**, 과거 파일 삭제·내용 변경·late 추가·빠진 manifest·gzip 충돌/날짜 오류를 검증했다. fixture의 7건은 9/23 운영 결과를 다시 실행한 값이 아니다.

- 영향 pytest: 두 파일 **106 passed, 1 deselected**. 제외된 `test_systemd_service_waits_for_postclose_label_contract`는 변경하지 않은 wrapper에 `--source-wait-sec 900` 문자열을 요구해 전체 실행에서는 **1 failed**다. `HEAD`의 동일 wrapper에도 그 문자열이 없어서 이번 수리의 회귀가 아니며 서비스 계약은 이 범위에서 변경하지 않았다.
- 변경 Python 4파일 `py_compile` 통과. `git diff --check` 통과. 신규 보고서의 상대 링크 2개·trailing whitespace 0, print-only backlog parser **exit 0·23 task**를 확인했다. Ruff 전체 대상에는 기존 58건이 남지만 현재 diff의 추가 줄 지적은 **0건**이다. wrapper를 수정하지 않아 `bash -n`/wrapper 계약 검사는 해당 없음이다. Project/Calendar 동기화는 실행하지 않았다.
- 작업본 HEAD `eb557c8e808fb46d321d96fadbbe359f8029bc91`, 읽기 당시 선택 릴리스 `e4117982fe34fe8bfc74a7468c6f049f25e7c149`는 서로 다르다. 이 수리는 작업본에만 있으며 선택 릴리스·PID 소비를 확인하거나 주장하지 않는다. 작업 시작 전부터 있던 다른 미커밋 변경은 보존했다.

**닫힘 검사와 인계:** S7에서 운영 입력·출력·lock·provider가 분리된 동일 절대경로 namespace에 현재 코드와 44 payload·33 replay를 고정하고, 첫 child의 manifest·stage receipt·추천 7건 및 파일 하나 변경 후 stale 거절을 재측정한다. 새 자연 source date에서는 이전 날짜 manifest와 당일 replay 생성 전후의 입력 세대·원본/유효/제외/격리/미관측을 확인한다. 9/23 옛 영수증은 새 manifest가 없으므로 현재 전체 이력 검증으로 승격하지 않는다. `S7-FIN02-02`의 label `generation_stable=false`와 674건 `source_gap`, 전체 15 stage·strict·controller·detector, 새 자연일 조건부 `S5-FIN-05`는 별도 owner다. 정규 장후작업·PREOPEN·배포·실주문·취소, 정책·수량·timeout·서비스·provider·threshold는 변경하거나 실행하지 않았다.
