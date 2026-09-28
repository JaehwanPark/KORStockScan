# S7 후속 — `S5-FIN-02` 압축 AI 원천의 실제 stage 격리 실행

실행일: **2026-09-28 KST**. 인계: [S7 통합 보고서](2026-09-28-intraday-postclose-handoff-S7.md), [S6 압축 원천 수리](2026-09-27-intraday-postclose-handoff-S6.md). **판정: 두 실제 stage의 격리 실행·동세대 압축 원천 검사는 PASS, `collector_recommendation`의 과거 payload 입력 세대 결속은 S6 blocker.** 9/23 운영 영수증과 원천은 재작성하지 않았다. 이 결과는 전체 15 stage, 선택 릴리스의 장후 자연 실행, PID 소비나 경제성 수용이 아니다.

## 1. 고정한 코드·원천과 격리 gate

작업본 HEAD와 선택 릴리스 commit은 `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`이었다. 이 경로의 `postclose_summary_handoff.py`, `ai_decision_quality.py`, `storage_maintenance.py`, `widget_collector_expansion_recommendation.py`, `widget_mechanical_entry_replay.py`는 작업본과 선택 릴리스의 byte SHA가 각각 일치했다. 예를 들어 dispatcher SHA는 `cb3dc30103a3396fcbbc26a77ff813165dccac65f339bdd05a50a25dd83ac6cb`, label child는 `ca950af2f91f2605abe76fba5a3e20afb2af160719c0a018b9e02b7eeeb79e48`, collector child는 `16fc63e6b56e3424c732635ed00e1360533bbbdba11fc669b745a2e817c28fca`다. 작업본에는 범위 밖 미커밋 변경이 있다. 선택 포인터의 메인 PID 영수증은 이번 두 장후 child의 실행 증거가 아니다.

| 9/23 운영 원천·영수증 | 물리 SHA-256 / 크기 | 해제 내용 SHA-256 / 크기 또는 역할 |
| --- | --- | --- |
| `ai_decision_payloads_2026-09-23.jsonl.gz` | `a57d5fcd0d8cb64427cc2f8d6f9138a795b0aab8789c8324a74331b402df5877` / 26,117,706 byte | `ff8b6f0a195481c66fe0d10f3b35668d27032e2daa90531bb770af96e085a99f` / 145,422,345 byte; 비어 있지 않은 JSONL 2,131행 |
| `ai_decision_outcome_labels_2026-09-23.json.gz` | `2d566ac5a5a4f519aa4b97b23d5922041f92abf1afdd87079d3d7165ae91ebcb` / 417,546 byte | `aeb6dd2a173ea38d902b61972a8ed85243814280808f98fcad2a58b03d31d691` / 8,418,067 byte |
| 운영 `outcome_labels` terminal | `a7c184d99fd993b46119987edddf20bf8445c92713ffbccfbae97ff622292821` / 1,488 byte | 옛 run `be180aa8091e409e8cbb4340e45a4bfb`; 이 실행에서 재사용하지 않음 |
| 운영 `collector_recommendation` terminal | `9d6d9ebe432f935f105669143d87dac232b16e128ffc72ebd58b5a97ffe99305` / 2,228 byte | 옛 run `5daa81a888ac4e86ae72b9fef87f5387`; 이 실행에서 재사용하지 않음 |

실제 dispatch는 `postclose_summary_handoff.stage_commands`가 반환한 `ai_decision_quality --date 2026-09-23 --mode postclose --write`와 `widget_collector_expansion_recommendation --target-date 2026-09-23 --write --source-wait-sec 0`이다. 각각의 새 terminal은 복제 root의 `data/report/postclose_stage_terminal/2026-09-23/`에 썼다. 첫 child는 trace·payload·outcome·pipeline·promotion·source-quality 감사와 control/label 출력을, 둘째 child는 label·payload, clean baseline 이후 replay·payload 이력, sentinel 표시 원천과 연구 watch 설정을 읽는다. 둘째 child는 replay JSON/Markdown 및 recommendation JSON을 쓴다. stage dispatcher는 terminal JSON/log/lock과 `postclose_stage_slots` lock을 쓴다. `--notify`는 지정하지 않았고 Telegram 상태 파일은 쓰지 않았다.

검증 root `/tmp/kor_s7_fin02_juy8o9fN/{seed,repeat,historical}`에는 **선택 릴리스의 `src`를 복제**하고 필요한 원천을 복제했다. 릴리스의 `data`·`tmp` symlink와 운영 data root는 mount하지 않았다. Docker 실행에는 `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000`을 적용했고, 호스트 `/usr`와 `.venv`만 읽기 전용, 독립 root만 쓰기 가능으로 mount했다. 외부 IP 연결 probe는 `ENETUNREACH(101)`, 운영 릴리스 경로는 컨테이너 안에서 보이지 않았다. `unshare -n`은 호스트 권한으로 거절돼 사용하지 않았다. 계정 설정·토큰 파일은 복제하지 않았고 외부 호출·주문을 실행하지 않았다. child 로그의 설정 부재에 따른 기본 URL 경고는 **연결 성공을 뜻하지 않는다**. 측정된 socket send/receive는 0이며 label의 가격 원천은 `pipeline_fallback`이다. 실행 후 대용량 `seed`·`repeat` 복제본은 삭제했고 terminal·출력·시간 로그와 입력 SHA manifest만 `/tmp/kor_s7_fin02_juy8o9fN/evidence/`에 남겼다. 정리 뒤 `/tmp` 가용량은 약 16GB였다.

재현 명령 형태는 다음과 같다. 두 stage는 서로 다른 동일 입력 복제본에서 각각 실행했다. 직접 child 측정도 같은 격리 옵션과 별도 출력에서 수행했다.

```bash
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 1000:1000 --pids-limit 64 --memory 4g \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e KORSTOCKSCAN_WIDGET_EXPANSION_TELEGRAM_ENABLED=false \
  -v /usr:/usr:ro -v "$ISOLATED_ROOT":/home/ubuntu/KORStockScan:rw \
  -v /home/ubuntu/KORStockScan/.venv:/home/ubuntu/KORStockScan/.venv:ro \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m -w /home/ubuntu/KORStockScan \
  --entrypoint /usr/bin/time postgres:15 -v -o /home/ubuntu/KORStockScan/data/stage_time.txt \
  /home/ubuntu/KORStockScan/.venv/bin/python \
  -m src.engine.automation.postclose_summary_handoff \
  --stage outcome_labels --date 2026-09-23 --timeout-sec 1800
# 같은 옵션과 복제 root로 --stage collector_recommendation 실행.
```

## 2. 실제 실행·영수증·분모

복제 root의 첫 `outcome_labels`는 **새 run** `5508f988f75c4fa58fac48edc9403f33`, 반복본은 `27506e15a62c4a0596f15580ee25e358`로 각각 `succeeded(exit=0, cache_reused=false)`였다. 두 terminal의 payload 입력은 원본 논리 SHA `ff8b6f0a…`다. 첫 새 label의 논리 SHA는 `9a46b9a3b5b5a351757002f31d7d3655323ebb30b604aef6535bd87d6757a4e1`, 반복본은 `4a66ae1d2cda3c40d4a4dbf9225b6e21331b9fdcfc28135efb44f60b5ba70066`이다. 새 label을 **격리 root 안에서만** gzip으로 보관하고 원경로를 제거한 뒤에도 첫 stage의 `stage_receipt_issues=[]`였다. 첫 압축본 물리 SHA는 `2cac59124e79535ddaa2f10cc9b481b2b678fbb281803e885a28e9a7f06caa87`. 저장된 9/23 **원래** 두 `.gz`·terminal을 별도 historical root에서 저장 당시 코드 해시로 검사한 결과도 각각 `stage_receipt_issues=[]`였다.

두 새 label은 각 674행이며 `partial=106`, `pending=568`이다. `label_contract_status_counts.source_gap=674`, 진단 경제성 적격은 0이므로 부분·미성숙 label을 수익성 결과로 올리지 않는다. 비어 있지 않은 payload **2,131행**, outcome label **674행**, collector가 열거한 과거 payload **44파일**과 replay **33파일**은 서로 다른 단위다. 44파일의 물리 byte 합은 397,063,688이며 경로·크기·SHA를 정렬한 격리 manifest SHA는 `82a0fa46e7a4970021208706b7dd1206043ec19ab39a4bf29b5d5b9b9f9ca9e7`이다. stage 영수증에는 이 전체 이력 manifest가 없다. 정확한 원본·유효·제외·격리·미관측 **row** 분모는 과거 payload 전체에 대한 stage 계약에 없으므로 0으로 채우지 않는다.

첫 collector 시험 run `bf91724e773a40a0a838206523b4b238`에는 9/23 payload만 있어 `no_qualified_candidate`와 추천 0건이 **`succeeded`로 기록됐다**. 당시 출력 SHA는 `f8dacadceed2dca9565d63c5f63b79344b503a26b58029c20df94519d0da35a0`이다. 이는 유효한 전체 입력의 거래 기회 0이 아니다. 과거 payload 44파일을 채워 새 attempt로 실행하자 첫 run `151a5a83dc314e7caccb0858374d1680`, 반복 run `3a0f5cd889314359a39aabd3bdbc4163`이 각각 `succeeded(exit=0, cache_reused=false)`였고 선행 outcome terminal·label·9/23 payload의 같은 논리 SHA를 입력 영수증에 결속했다. 각 출력은 `recommendations_ready`, 추천 7건, 제외 사유 `already_active_widget=6`, `liquidity_feature_missing=14`, `outcome_quality_not_positive=425`, `sample_floor_not_met=142`, `tradability_floor_not_met=26`으로 같았다. 첫 출력 SHA는 `ac680268277cc155b35ce7d667f69692158a591a60e5d2e1342a99b981248b03`, 반복 출력 SHA는 `b39a37114cddce54fa898b8d3a6aca3f1c632bb13a2daa01641f89ae4a277e0c`이다. 보존 운영 보고서도 추천 7건이지만 새 계산의 SHA와 원천 세대가 달라 동일 결과로 승격하지 않는다. 이 추천은 source-only이며 collector·서비스 변경 권한이 없다.

| 측정 범위 | 측정 A wall / CPU(user+sys) | 측정 B wall / CPU(user+sys) | peak RSS KiB, A / B | GNU time I/O inputs·outputs, A / B |
| --- | --- | --- | --- | --- |
| `outcome_labels` 실제 stage 포함 wrapper | 67.88s / 58.84s | 58.74s / 58.44s | 1,025,800 / 1,033,544 | 1,203,472·17,000 / 1,027,232·16,944 |
| `collector_recommendation` **전체 이력** 실제 stage 포함 wrapper | 67.24s / 60.52s | 62.82s / 59.95s | 645,768 / 645,336 | 2,769,856·608 / 2,995,576·576 |
| 동일 root에서 별도 실행한 **실제 child만** | outcome 53.82s / 53.72s | collector 55.60s / 53.13s | 1,032,848 / 645,600 | 958,960·16,480 / 3,026,912·104 |
| 압축 원천 `stage_receipt_issues` 독립 재검증 | plain label일 때 2.35s / 2.28s | label 압축 후 2.41s / 2.34s | 56,700 / 63,076 | 26,896·0 / 36,888·0 |

직접 child 측정은 반복본의 완료 영수증을 별도 보관한 뒤 생성 출력을 제거하고 **동일 원천으로 다시 계산한 별도 probe**다. 따라서 위 wrapper 시간에서 직접 child 시간을 빼서 정확한 해제 비용이라고 주장하지 않는다. 독립 재검증 시간에는 Python 시작·schema·날짜·논리 SHA 검사도 포함된다. 두 실행의 외부 socket send/receive는 0이었다. OS page cache를 비우지 않았고 동시 시스템 부하가 있으므로 첫 회/반복을 엄격한 cold/warm 보증이나 성능 개선 판정으로 사용하지 않는다. 비교 가능한 S6 이전 코드의 같은 범위 성공 실행은 없으며, 구세대 9/23 계산과 새 계산은 `generated_at`·`outcome_as_of`와 label 내용이 달라 byte 출력 parity 대상이 아니다.

## 3. 결손·owner·닫힘 검사

| ID·판정 | 재현·영향 | owner와 닫힘 검사 |
| --- | --- | --- |
| `S7-FIN02-01` **S6 재수리 blocker** | `collector_recommendation` 직접 reader는 과거 payload 44파일을 읽고 출력의 `source.feature_paths`에도 열거하지만, stage `input_sources`에는 9/23 payload·label·선행 receipt만 있다. 격리 root에서 `ai_decision_payloads_2026-08-18.jsonl.gz` **7,474,877 byte**를 일시 숨겨도 `stage_receipt_issues`는 전후 모두 `[]`였다. 더 넓게 이력을 빼면 추천 7→0으로 바뀌면서도 stage는 `succeeded`였다. | `widget_collector_expansion_recommendation` 생산자와 `postclose_summary_handoff.stage_input_paths` 첫 영수증 reader의 S6 owner. clean baseline 이력의 날짜·경로·논리 SHA·원본/유효/격리/미관측 분모를 결속하고, 누락·변경·중복·late 이력을 `source_quality` 또는 stale로 거절하는 실패 회귀를 먼저 남긴다. 동일 세대 7건 수용·이력 하나 변경 후 구세대 거절로 닫는다. 9/23 운영 영수증에는 소급 삽입하지 않는다. |
| `S7-FIN02-02` **원천 품질 별도 확인** | 9/23 감사 manifest는 보존됐으나 `ai_decision_quality.source_label_input_receipt`의 `generation_stable=false`가 운영과 격리 실행에서 확인됐다. 압축 후 device/inode 세대 불일치가 포함된 상태에서 새 control은 `control_manifest_gap_fix_required`; label 674건 모두 진단 계약상 `source_gap`이다. stage `succeeded`만으로 원천 품질이나 경제성 적격을 주장할 수 없다. | `ai_decision_quality` source manifest 생산자·첫 materialization reader owner. 새 자연 source date에서 압축 전후 논리 SHA·날짜·manifest generation 및 label 분모를 동세대 검증한다. 같은 결손이 확인되면 S6에서 원인별 수리하고 진단 적격을 별도로 검사한다. 과거 9/23 영수증을 재작성하지 않는다. |
| `S7-FIN02-03` **비교 한계** | 첫·반복 실행은 복제 입력이 같지만 평가 시각이 다르고, 첫 불완전 이력 attempt는 유효 비교군이 아니다. 진행 중 작업본 checklist byte SHA가 바뀌어 작업본 전체 불변 freeze도 성립하지 않았다. | S7 검증 owner. 다음 비교는 코드·체크리스트·source snapshot을 시작/종료에 고정하고 동일 평가 시각 또는 시간 독립 결과 범위를 명시한다. 실제 child와 검증·압축 시간을 각각 측정한다. |

압축본 손상·다른 날짜·다른 내용·원천 부재, 양쪽 표현 충돌, 실패·OFF·유효한 빈 label의 계약 회귀는 `test_postclose_summary_handoff.py` 표적 **12 passed, 66 deselected**였다. 운영 값 수정 없이 원래 `.gz`의 논리 SHA와 옛 terminal을 독립 root에서 재검증했다. 이 fixture 통과는 `S7-FIN02-01`의 **과거 이력** 결속을 닫지 않는다.

## 4. 검증 범위와 인계

격리 실행 종료 시 운영 고정 파일 7개의 전후 SHA 중 두 AI `.gz`, 두 terminal, 운영 collector 보고서와 선택 포인터는 같았다. 그 시점의 작업본 HEAD·status 목록 SHA도 같았다. **본 작업이 수정하지 않은 체크리스트 SHA와 전체 `git diff` SHA는 검증 중 달라** 작업본 전체 불변을 선언하지 않는다. 이후 이 보고서가 새 미추적 파일로 추가됐다. 본 작업은 repository Python·wrapper·정책 파일을 수정하지 않았다. 자가 리뷰에서 불완전한 이력 실행의 추천 0건을 유효한 빈 결과로 승격하지 않았고, wrapper 성공·원천 품질·경제성·PID 경계를 재확인했다. 문서 링크 **2개 유효**, trailing whitespace **0**, print-only backlog parser **PASS(33 task)**, `git diff --check` **PASS**이며 새 미추적 문서의 `git diff --no-index --check`에도 공백 지적이 없었다. Python compile·wrapper `bash -n`은 소스·wrapper 변경이 없어 생략했다. 외부 Project/Calendar 동기화는 실행하지 않았다.

9/23 capacity 실패→allocation 보류, 구세대 strict/checklist, 전체 15 stage→summary→controller·finalizer·detector와 `S5-FIN-05`의 새 자연일 조건부 결손은 그대로 남는다. 다음 자연 source date의 allocation 격리 gate도 별도다. 이 보고서의 격리 PASS는 정규 장후작업·PREOPEN, 새 릴리스 선택, 실제 PID의 두 stage 코드 소비 또는 비용 조정 수익성을 증명하지 않는다. 실주문·취소·provider·threshold·정책·서비스·배포는 변경하거나 실행하지 않았다.
