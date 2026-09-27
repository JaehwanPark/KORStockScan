# 장중 생산자–장후 소비자 S6 수리 보고서 — S5-FIN-02

실행일: 2026-09-27 KST. 범위: [S5 보고서](./2026-09-27-intraday-postclose-handoff-S5.md)의 `S5-FIN-02` 압축 후 stage 원천 재검증 한 묶음. 이 문서는 작업본 코드 수리와 read-only 검증의 기록이며 선택 릴리스·PID·자연 장후 실행 수용 증거가 아니다.

## 결정·원천 연결

`deploy/run_logs_rotation_cleanup_cron.sh`가 `storage_maintenance.maintain_report_artifact_storage`의 exact-AI root로 두 경로를 등록한다. 9/26 보관 영수증 [`micro_reversion_storage_maintenance.4EuOQN.json`](../../tmp/micro_reversion_storage_maintenance.4EuOQN.json)의 두 action은 각각 `compress_exact_ai_jsonl`/`compress_exact_ai_json`, `applied=true`이며 exact-AI 하위 상태는 `pass`, 실패 0이다. 보관 작업 전체의 `partial_failure`를 전체 성공으로 바꾸지 않는다. stage reader는 원래 논리 경로를 유지한 채 해제 내용으로 비교한다.

| 논리 원천 → 최초 stage 소비 | 원천일 | 생산자 영수증·현재 직접 검증의 해제 크기/SHA-256 | 현재 물리 보관본 SHA-256 | stage 영수증 결속 |
| --- | --- | --- | --- | --- |
| `data/ai_decision_payloads/ai_decision_payloads_2026-09-23.jsonl` → `outcome_labels.input_sources.payloads`, `collector_recommendation.input_sources.payloads` | 2026-09-23 | 145,422,345 byte / `ff8b6f0a195481c66fe0d10f3b35668d27032e2daa90531bb770af96e085a99f` | `.jsonl.gz`: `a57d5fcd0d8cb64427cc2f8d6f9138a795b0aab8789c8324a74331b402df5877` | 원래 path와 해제 SHA 유지 |
| `data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-09-23.json` → `outcome_labels.sources.ai_decision_outcome_labels`, `collector_recommendation.input_sources.labels` | 2026-09-23 | 8,418,067 byte / `aeb6dd2a173ea38d902b61972a8ed85243814280808f98fcad2a58b03d31d691` | `.json.gz`: `2d566ac5a5a4f519aa4b97b23d5922041f92abf1afdd87079d3d7165ae91ebcb` | 원래 path와 해제 SHA 유지 |

독립 생산자 검증은 exact basename·파일 내 거래일·schema·원본/압축본 일치·안정된 물리 세대를 검사하고 `logical_path`, `trade_date`, `decoded_content_sha256`, `decoded_content_bytes`, 물리 SHA/크기를 기록한다. 소비자인 `postclose_summary_handoff._stage_sources`는 이 검증을 압축된 두 exact-AI 원천에 적용한다. 성공한 원본과 정상 `.gz`는 기존 stage receipt의 `path`/`sha256` 형태와 값을 그대로 재현한다. `outcome_labels` 출력 검사도 검증된 압축 JSON을 읽는다. 미압축 경로의 기존 처리, 명시적 OFF·실패 terminal의 우선 판정, 빈 `labels=[]`의 유효 판정은 유지한다.

## 실패 재현 → 수리 → 재검토

- **수리 전 실패:** 실제 압축 생산자를 쓰는 새 회귀 `test_exact_ai_storage_compression_preserves_stage_generation`은 원본 제거 후 `_stage_sources`가 `sha256=None`을 반환하여 실패했다. 당시 두 stage의 같은 논리 세대가 `output_generation_changed`/`input_generation_changed`로 잘못 분류됐다.
- **수리:** [`storage_maintenance.py`](../../src/engine/scalping/micro_reversion/storage_maintenance.py)의 생산자 검증을 재사용 가능한 exact-AI 논리 세대 계약으로 묶고, [`postclose_summary_handoff.py`](../../src/engine/automation/postclose_summary_handoff.py)의 해당 두 원천만 압축 대응했다. 압축본을 원본 경로의 새로운 stage receipt로 재발행하거나 과거 terminal을 수정하지 않았다.
- **부정 회귀:** payload/label 각각 손상 gzip, 파일 안의 다른 날짜, 다른 내용, 원천 부재를 stage에서 거절한다. producer는 손상·다른 날짜·부재를 별도로 거절하며, 유효하지만 변경된 내용은 다른 SHA로 판별한다. 원본과 `.gz`가 함께 있고 같으면 인정하고, 서로 다르면 거절한다. 실패·OFF terminal 상태 판정은 압축 원천 손상보다 우선한다.
- **실제 자료 read-only 재검증:** 9/23 두 `.gz`의 해제 크기/SHA가 위 보관 영수증과 일치했다. 현재 작업본에서 `stage_receipt_issues(data/report, 2026-09-23, outcome_labels)`와 `collector_recommendation`은 각각 `[]`였다. 두 호출은 약 2.44초/2.06초였으며 payload 해제·schema/날짜 검증 비용을 포함한다. 이는 현재 두 receipt의 원천 결속 검사 결과이며 다른 13 stage, strict/controller, PREOPEN의 통과가 아니다.

자가 코드리뷰에서 gzip 손상, 이중 표현 불일치, 원천일 불일치, 읽는 중 세대 변경, 상태 우선순위와 JSON 객체 아닌 출력의 실패 처리를 재검토했다. 발견한 압축 JSON의 객체형 미보장과 생산자 계약 중복 필드를 보완한 뒤 해당 경로와 diff를 재검토했다. **이 묶음의 미해결 코드 결함 0**이며 전체 장후 체인의 OPEN 결손과는 분리한다.

## 검증·권한·다음 인계

| 검사 | 결과 |
| --- | --- |
| 새 재현 회귀(수리 전) | 1 failed: 압축 후 논리 SHA `None` |
| 두 영향 테스트 파일 전체 | 167 passed. 두 stage, valid-empty, 실패/OFF, 손상·날짜·내용·부재·이중 표현 회귀 포함 |
| 세 변경 Python 파일 `py_compile`; `git diff --check` | 통과 |
| wrapper `bash -n`·wrapper 계약 | wrapper 수정 없음. 설치 cron·선택 릴리스는 변경하지 않음 |
| 문서 링크·공백; print-only backlog parser | 통과; 미완료 parsed 31건, 외부 동기화 없음 |

선택 릴리스는 `integrated-workspace-20260927-fcc57536` (`fcc57536b08577320c6a59067b5463fb4a90a7c9`)이고 selector의 `actual_pid_consumed=false`다. 본 수리는 **미배포 작업본**이다. 기존 SOR→KRX 작업본 네 파일과 S1–S5 보고서는 보존했다. 실주문·정책·서비스·provider·threshold·정규 장후·PREOPEN은 변경하거나 실행하지 않았다.

**S7 인계:** 승인된 별도 범위에서 같은 clean 원천으로 전체 stage 호출 횟수에 따른 해제/검증 비용과 cold/warm chain 성능을 측정한다. **S8 인계:** 별도 릴리스 선택, 자연 terminal→strict/controller→다음 PREOPEN→PID 영수증이 필요하다. `S1-COM-01-A` scanner 압축 reader와 `S5-FIN-01/03/04/05`는 이 묶음에 포함되지 않으며 기존 owner·닫힘 검사를 유지한다.
