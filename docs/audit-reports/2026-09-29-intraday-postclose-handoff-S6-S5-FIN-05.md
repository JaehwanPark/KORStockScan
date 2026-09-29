# S6 `S5-FIN-05` — 9/28 postclose exit snapshot and final detector generation

실행일: **2026-09-29 KST**. 범위: [S5 보고서](2026-09-27-intraday-postclose-handoff-S5.md)의 `S5-FIN-05` 한 묶음. **판정: 9/28 최종화의 당시 실행 성공은 보존하지만, 이후 재생성된 현재 strict·controller 세대에 대해 07:11 DONE을 08:32 detector가 PASS로 읽은 결손을 재현하고 작업본 코드에서 차단했다.** 정규 장후·PREOPEN·배포·주문·취소는 실행하지 않았다.

## 원천과 시간축

| 경계 | 9/28 원천일 증거 | 판정 |
| --- | --- | --- |
| 등록 stage | `data/report/postclose_stage_terminal/2026-09-28/`의 15개 마지막 영수증은 각각 `succeeded`, `exit=0` | 저장된 stage terminal 상태. 이후 소비까지 자동 승격하지 않는다. |
| `postclose_exit` | `monitor_snapshot_manifest_2026-09-28_postclose_exit.json`, manifest SHA `4e13d990b3f87e43b71d4a0c2f35937b3ccbd252c5c31ac8029a74fc51415402` | profile·날짜·세 종류가 일치한다. |
| snapshot 3종 | trade review 원본 SHA `504f241c…`, post-sell gzip 해제 SHA `14483dae…`, holding observation 원본 SHA `2dfd6813…` | manifest의 세 논리 SHA와 모두 일치. 원본 2·압축본 1을 유효 원천으로 선택했다. |
| 공존본 | trade review `.json.gz` 해제 SHA `bad23955…`는 같은 이름의 현재 `.json` 및 manifest와 다름 | 압축본 1개는 이전 세대여서 제외. 원본이 있을 때 원본을 우선하며 이중 집계하지 않는다. 원본 삭제 뒤 이 압축본만 남으면 새 reader는 거절한다. |
| finalizer 당시 | 07:09:37 strict attempt `606c51…` SHA `cd5cde4f…`, summary SHA `5633ff97…`; 07:10:01 controller attempt `dbc347…` SHA `adaea0ce…`; 07:11:31 cleanup·detector 뒤 DONE | finalizer가 당시 fresh controller를 확인했다. detector run `cron-20260929T071129-1014922`는 07:11:30에 부모 finalizer를 `pending_self_audit`로 관측했다. |
| 이후 세대 | 08:25:54 strict attempt `5edd7f…` SHA `1c381e88…`, summary SHA `f21c522c…`; 08:26:18 controller attempt `5b4767…` SHA `58d28a07…` | main run ID `2d88fd4842234a28bf727307fbd3313a`는 같지만 strict의 논리 입력 세대가 다르다. |
| 다음 detector | 08:32:06 `error_detection_2026-09-28.json`, run `cron-20260929T083205-1136903` | `cron_completion`은 로그의 마지막 DONE으로 `postclose_finalization=pass`를 기록했다. 현재 strict·controller 세대와 07:11 DONE의 결속은 없었다. |

원본·유효·격리·미관측 단위는 **snapshot kind 3/3/0/0**이다. 별도의 공존 archive 후보 1개는 `trade_review` 현재 원본과 다른 논리 SHA라 제외했다. 15 stage, detector 7종, snapshot 3종은 서로 다른 분모다. 07:11의 detector 7/7 초기화와 08:32의 cron PASS를 현재 전체 체인 또는 경제성 PASS로 합치지 않는다.

## 재현과 수리

- 실패 회귀를 먼저 추가했다. `test_postclose_finalization_generation.py`는 이전 DONE에 새 strict summary 세대를 연결할 때 거절해야 하는 사례, legacy DONE을 detector가 PASS로 읽는 사례, 정상 gzip·원본/압축 공존·손상·다른 날짜·누락 attempt를 fixture로 고정했다. 구현 전 `ModuleNotFoundError`로 수리 계약이 없음을 확인했다.
- 생산자 `deploy/run_postclose_finalization.sh`는 9/28 이후 source date에서 fresh controller가 참조하는 whole-chain strict `generation_binding`과 `postclose_exit` 세 snapshot의 논리 세대를 캡처한다. cleanup·detector 뒤 다시 대사해 바뀌면 DONE을 내지 않는다. 성공한 정확 detector report의 date·fresh mtime·동적 등록 건수·`pending_self_audit`·run ID·SHA도 DONE marker에 남긴다.
- 첫 후속 reader `src/engine/error_detectors/cron_completion.py`는 마지막 DONE marker의 두 세대 SHA와 detector run ID·report SHA를 요구하고, 현재 controller/strict 및 세 snapshot의 원본 또는 gzip 해제 내용을 다시 확인한다. 세대가 바뀌거나 원천이 없으면 `postclose_finalization=fail`과 구체 사유를 기록한다. 과거 9/28 로그에는 새 필드가 없으므로 소급 성공 영수증을 만들지 않는다.
- `src/engine/automation/postclose_finalization_generation.py`는 archive를 논리 SHA로 검사한다. 원본과 압축본이 공존하면 원본만 유효 입력으로 선택하고 다른 압축본은 제외 상태로 분류한다. 날짜·owner 경로·attempt SHA가 다른 입력, 실패·누락·손상은 거절한다. source date가 맞는 빈 payload는 세대가 완전하면 유효 빈 입력으로 취급하며, 필수 profile 자체가 OFF/누락이면 성공 0으로 바꾸지 않는다.

수리 owner는 finalizer wrapper·postclose snapshot manifest 생산자·`cron_completion` 직접 reader다. 새 Python 모듈은 장후 자동화 원천 계약을 소유하므로 `src/engine/automation/`에 두었다. 기존 독립 작업본 변경은 보존했다.

## 리뷰·검증·남은 수용

- 자가 리뷰에서 선택 릴리스의 `data` symlink 경로와 manifest의 workspace 절대경로가 서로 다른 문자열이라는 결함을 발견해, 동일한 resolved owner 경로로 대사하도록 수정했다. gzip 손상과 다른 날짜, 공존 archive 제외도 보완해 재리뷰 범위 내 미해결 결함은 0이다.
- 표적 pytest **86 passed** (`test_postclose_finalization_generation.py`, `test_error_detector_cron_completion.py`, `test_postclose_finalization.py`, `test_threshold_cycle_wrappers.py`). Python compile, 대상 Ruff, `bash -n deploy/run_postclose_finalization.sh`, `git diff --check` 통과. print-only backlog parser 통과, 새 checklist owner `S5FIN05FinalDetectorGeneration0929`은 1개다. 운영 파일·lock·provider 경로를 쓰는 실행은 하지 않았다.
- 현재 선택 포인터 조회시 commit `2c9ca5794fc92ce560fea379c42d8837c197a5f3`; 이번 수리는 미커밋 작업본 코드다. 선택 릴리스·PID 소비와 다음 자연 source date의 finalizer→detector 수용은 미확인이다. snapshot 재검증은 대형 trade-review 원본을 streaming SHA로 읽으므로 실제 반복 비용은 S7에서 측정한다. 9/28의 서로 다른 strict summary 세대는 역사적 상태로 보존한다.
- 닫힘 검사: 별도 허가된 릴리스 이후 다음 자연 장후에서 snapshot 3종 논리 SHA·controller/strict 세대·cleanup·detector run ID가 결속된 DONE을 확인하고, 그 뒤 독립 detector의 동일 세대 PASS와 선택 릴리스/PID를 따로 확인한다. `S7-FIN02-01` collector의 완전 격리 입력 재측정, 전체 15 stage 성능과 비용 조정 경제성은 별도 owner다.
