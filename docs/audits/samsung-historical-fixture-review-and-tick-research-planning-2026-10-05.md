# 삼성 역사 입력 회귀 보완·연속 tick 연구계획 리뷰

작성일: 2026-10-05 KST. 범위는 사용자 요청의 추가연구계획 수립 및 잔여 결함 리뷰·수정보완이다.

## 1. 연구계획

[연속 tick 전환 연구계획](../proposals/samsung-continuous-tick-window-transition-research-plan-2026-10-05.md)을 작성했다. 기존 판정 capture 사이 간격 때문에 H2가 미식별인 경우를 대상으로, 원현재10tick에 대해 한 tick 이동한 이전 구간과 비중복 직전10tick을 비교하는 두 가설만 정의했다. 현재/직전 구간·as-of 시각·route·epoch·수량·원 TTL을 먼저 검사하고 식별률과 성능 개선을 별도로 판정한다.

최대 신규2개+대조3개로 끝내며, 원native·모집단·가격경로·원 비용/stop·이미 탐색한 날짜의 지위를 보존한다. 성공 보존율 veto를 추가하지 않는다. 한 날짜/한 사건 민감도와 상시감시 전용 효과를 별도로 보고한다. 이번 턴에서 신규 가설 재생이나 정책 선정을 실행하지 않았다.

## 2. 확인한 결함과 수정

원인은 [직전 리뷰](samsung-kernel-recovery-and-followup-assessment-2026-10-05.md)의57 PASS·1 FAIL이다. 역사 fixture가10/6의 mutable dated 경로에9/29~10/2 연구 당시 원본 SHA를 요구했다. 정식 지정으로 그 경로가 바뀌면 과거 정상 입력 재현까지 실패했다. 생산자/운영 loader가 새 정책을 거부한 문제가 아니라 **테스트 입력의 보관 방식 결함**이다.

수정은 [기존 테스트 모듈](../../src/tests/test_samsung_fixed_watch_evaluation_research.py)의 fixture에 한정했다.

- `data/runtime/mechanistic_entry_policy/policy_YYYY-MM-DD.json`으로 경로 범위를 제한했다.
- 현재 파일이 요구 SHA와 같으면 그 bytes, 다르면 publisher의 `sources/<요구 SHA>.json` 원본을 읽는다. 현재 파일이 없을 때도 해당 원본만 사용한다.
- 둘 다 정확히 일치하지 않으면 명시적으로 실패한다. expected SHA 교체, 임의 파일 탐색, 원 운영 정책 쓰기는 없다.
- 원본을 fixture 전용 디렉터리로 복사한 뒤 다시 SHA를 확인한다. 최초 snapshot 후 운영 포인터가 이동해도 같은 역사 입력을 재현한다.
- 다른 원천 경로는 기존 엄격한 hash 검사를 그대로 통과해야 한다. source 검증을 monkeypatch하거나 과거 검증 날짜를 새 holdout으로 바꾸지 않는다.

생산 코드/매매 전략/원 frozen/보관 원본/10/6 dated 정책을 변경하지 않았다. 기존 `validate_replay_input`의 canonical raw·trace·label·cost·native·epoch 검증을 실제로 통과시킨다.

## 3. 리뷰 반복과 회귀

첫 수정 후62개 회귀가 통과했다. 재리뷰에서 “현재 경로가 아직 원본과 같더라도 fixture는 고정 사본을 보관해야 한다”는 경쟁 조건을 추가 보완했다. 최종3개 관련 suite는 **72 PASS / 187.06초**다. 최종 테스트 목록·로그·보호 hash·문서 검증은 `tmp/samsung-tick-plan-review-20261005/`에 둔다.

검증 내용은 정확한 원본 archive 사용, archive 부재/변조 거부, 다른 경로 변경 거부, snapshot 자체 변조 거부, 이후 운영 포인터 변경과의 독립성 및 기존 실제160행 역사 intake이다. 삼성 compatibility·H2의 기존 회귀도 함께 통과했다. 검토한 수정 범위에서 미해결 코드 결함은 없다. API/주문·전체 거래 suite·신규 연구 전체 재생은 이 수정의 검증 범위가 아니다.

`py_compile`, `git diff --check`, 문서7개 로컬 링크 및 print-only parser를 검증했다. 추가연구·이후 날짜 검증·장전 인계는 각각 단일 OPEN owner로 파싱되며 이번 보완 항목은 완료 처리했다. 선택 release·current·10/6 dated 정책·10/6 체크리스트·prepared receipt의5개 물리 SHA는 보완 전후 동일하다. 외부 문서 동기화는 실행하지 않았다.

## 4. 배포 경계와 원 kernel 이력

과거 두 veto의 frozen은 테스트 파일 bytes도 봉인한다. 이번 테스트 수정본을 그 역사 bytes로 치환하지 않는다. 선택된 운영 release `3d0e5106`는 이전의 검토된 물리 코드·테스트와 기존 migration을 사용한다. 해당 release의 cwd에서 원 frozen 검증 PASS, H2 `waiting_new_source_date`,10/6 준비 verify PASS를 확인했다. [소비자 확인](../../tmp/samsung-tick-plan-review-20261005/selected-consumer-check.json).

작업본에서의 테스트 수정과 선택된 불변 release의 호환 증거를 구분한다. 고정 연구 CLI는 현재 승인 release 디렉터리를 cwd로 실행하고 `--root /home/ubuntu/KORStockScan`을 지정한다. 새 코드/테스트 세대를 실제 연구 소비자로 배포할 때는 그 물리 SHA에 맞춘 별도 호환 증빙을 먼저 준비해야 한다. 과거 migration의 `new_kernels`를 현재 workspace 값으로 덮어 운영 소비자를 깨뜨리지 않는다.

후속 신규 연구는 `SamsungContinuousTickWindowResearch`, 실제 새 날짜 검증은 기존 `SamsungFrozenCandidateValidation1006`가 소유한다. Main 당일 정책 소비·Widget/Episode의 기동 owner는 그대로다.
