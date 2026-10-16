# 비상시 호가·기회 전달 구현 및 반복 리뷰 — 2026-10-17

## 1. 결정·범위

사용자의 구현·코드리뷰·수정보완 반복 지시로 [최종 계획](../proposals/nonfixed-quote-freshness-and-opportunity-delivery-remediation-plan-2026-10-17.md)을 구현한다. 선택 commit `7f2552aedde8fec6ef904a43105827907e50dfc8` 기준 격리 작업본 `/home/ubuntu/KORStockScan-worktrees/nonfixed-quote-implementation-20261017`, branch `codex/nonfixed-quote-implementation-20261017`을 사용한다. 현재 변경 상태·검증 영수증은 [구현 증거](../../tmp/nonfixed-quote-implementation-20261017/)에 보존한다. 코드 구현·반복 리뷰·표적 검증을 완료하고 배포 대기로 둔다.

오늘 체크리스트가 없었던 사실을 확인한 뒤 이번 명시 지시의 좁은 실행 owner만 [10/17 체크리스트](../checklists/2026-10-17-stage2-todo-checklist.md)에 만들었다. 과거 또는 10/19 작업을 오늘 권한으로 대체하지 않는다. 원 작업본의 동시 변경을 그대로 보존한다.

## 2. 구현과 소유 경계

- 설정: 접두사가 빠진 stale 회복 설정을 canonical owner와 통일하고 미래 transport 시각을 거부한다. 설정된 pre-AI 한도와 canonical 입력 3초, latency SAFE/CAUTION, refresh·consistency·transport 한도를 각각 기록한다. 수신 clock과 원 신호 lifetime은 별개다.
- 원천 대기: version-before-check, exact manager/item/transport 대기 등록과 알림 병합으로 lost wakeup을 제거한다. 최초 epoch 확인·정상 timeout·경합·정책/transport 교체에서도 원 기한을 지킨다.
- 0D: 공용 BBO·type timestamp·sequence·depth 반영 뒤 실제 대기자만 깨운다. WATCHING pending target은 기존 coordinator event/hint로 전달하고 native-ready 표본·가격 FSM 신호를 늘리지 않는다.
- 호가-only 회복: provider 미호출·미평가·호가만 결손인 원 기회에 새 exact packet·lease·유효한 기존 0B·원 5초/perf 기한을 요구한다. 한 번의 새 계산만 허용하고 기존 새 0B 회복 경로를 보존한다. 원 native event/ask와 현재 계산 ask·스프레드·가격 geometry를 버전 있는 증거로 분리한다.
- Main 소비: 검증된 native claim의 exact item/route/epoch 및 canonical quote를 확인한 경로는 상시·비상시 동일 원천 owner를 쓴다. 일반 scanner에는 기존 추가 transport bound가 남는다.
- 물리 전송: Main 최초 진입·초기 분할 leg0의 exact intent/수량/route/현재 machine·보조판정·정책·quote를 실제 POST와 허용된 auth 재시도 직전에 검사한다. 후속 leg·AVG_DOWN·SELL·보호/긴급·CANCEL·조회에는 최초 진입 의무를 전파하지 않는다. 미전송과 실제 auth 거절·응답 불확실을 구분한다.

영구 Python 신규 소유 위치는 `src/trading/entry`의 시간정책/전송 계약이며 기존 scalping·WS·Main·telemetry producer/consumer를 확장한다. `src/engine` root에 신규 모듈을 추가하지 않는다. 오프라인 비교 도구는 기존 연구 증거의 `tmp` 소유 위치다.

## 3. 반복 리뷰에서 보완한 경계

1. 최초 transport epoch가 없던 대기자는 epoch를 배운 뒤 즉시 등록·재검사하여 첫 0D 알림을 놓치지 않게 했다. 0D 통지는 일부 row 게시 뒤가 아니라 공용 snapshot 반영 뒤로 이동했다.
2. 시간 영수증에 존재하던 float/int·잘못된 env fallback 파서 차이를 실제 설정 owner로 통일했다. 설정 가능한 pre-AI 한도와 canonical 입력의 고정 3초도 분리했다.
3. native 소비의 item·epoch만 같고 route가 다른 경우도 거부한다. 실제 원 판정에 사용한 branch의 생존을 확인하고 다른 branch만 남은 상태로 원 판정을 승인하지 않는다.
4. 전송 검증 뒤 telemetry lock 대기가 원 deadline을 넘기는 결함을 결정적으로 재현했다. 마지막 lock 준비 뒤 실제 HTTP 직전 callback으로 검사하며 미전송이면 임시 계수를 회수한다.
5. 새 0D ask를 영수증에만 붙이고 root ask로 실제 요청을 만드는 누락을 보완했다. 현재 quote 조건·스프레드·실제 새 요청과 원 native 증거를 각 소비자가 검증한다.
6. 최초 실패와 pending 등록 사이의 packet도 즉시 재검사한다. 원 기회를 새 신호나 새 5초로 바꾸지 않는다.

## 4. 저장 호가의 시간정책 비교

[비교 도구](../../tmp/nonfixed-quote-implementation-20261017/compare_saved_quote_policies.py)와 [결과](../../tmp/nonfixed-quote-implementation-20261017/saved-quote-policy-comparison.json)는 10/15의 기존 16개 기회·64개 시나리오만 사용한다. 원 normalized SHA와 이전 278개 depth 행의 schema/epoch 검증을 결속했다. 미래 호가는 입력으로 쓰지 않고 이후 가격은 지연 시점 ask 기준 비용 후 목표/손절 라벨에만 사용한다.

| 확인점 이후 | 기존 0B 증빙, 700ms 이내 / 16 | 과거 수신 0B+0D 증빙, 700ms 이내 / 16 |
|---|---:|---:|
| 0초 | 16 | 16 |
| 1초 | 4 | 11 |
| 2초 | 3 | 5 |
| 3초 | 3 | 8 |

이 수치는 source-age band 확인이며 실제 submit 가능 수가 아니다. 1초·0B+0D 700ms의 비용-bound native 가격 라벨은 W3/STOP1/U7이고 1,000ms는 W3/STOP1/U12다. 기존 기회에서 quote 증거 수가 늘어난 것과 새 실현 이익을 혼동하지 않는다. 원천 단절은 U로 남기며 완료 분봉·실제 fill로 대체하지 않는다.

추가 [prefix 조건부 후보 비교](../../tmp/nonfixed-quote-implementation-20261017/prefix-conditioned-policy-comparison.json)는 결과를 사용하지 않고 과거 0D 간격·같은 epoch의 연속 sequence·직전 3개 동일 BBO·spread≤0.1%를 조건으로 `min(2000,max(700,ceil(1.5×과거 중간 수신간격ms)))`를 비교했다. 64개 시나리오는 안정·좁은 호가17, 변화/넓은 호가31, 증빙 부족16으로 분리됐다. 이번 prefix의 적격 후보 한도는 모두 700ms였고 같은 전달 방식의 기존 700ms 대비 추가 통과는 없었다. 이 후보를 운영 정책으로 발행하지 않는다.

새 시간상한은 선정하지 않았다. 원래 700ms·1,000/1,500/2,000ms를 같은 원천에서 비교했지만 실제 AI/Main/POST 시각·실행 가격/체결 증거가 없는 지연 시나리오다. 이는 700ms를 영구 고정하는 결론도 아니다. 현재 구현은 실제 source 전달을 보완하고 각 현재 time owner를 한 영수증으로 결속한다. 이후 조건부 시간정책은 이 구분을 유지한 증거로 평가한다.

## 5. 공식 Kiwoom 참조

변경 전에 공식 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 `2026-10-17T08:32:28.563052+09:00`에 다시 조회·고정했다. [조회 영수증](../../tmp/nonfixed-quote-implementation-20261017/official/upstream.json)에 SHA와 파일 hash를 남겼다. `kiwoom_docs`는 이 tree에 없다. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/{decoders,events,schemas,packets,stream}.py`, packaged 0B/0D·kt10000, PRD/MOCK Postman을 확인했다. [공식 spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)의 기존 endpoint/header/body/FID/route 및 real/demo 계약을 유지한다.

## 6. 최종 검증과 인계

- [통합 검증 명령](../../tmp/nonfixed-quote-implementation-20261017/combined-test-command.json) 및 [출력](../../tmp/nonfixed-quote-implementation-20261017/combined-pytest.txt): **1,610 PASS**, 기존 baseline node1개 deselected, 기존 pandas_ta 경고1개. 부분 검증 수를 서로 더해 고유 검사 수로 부풀리지 않는다.
- Python21개 compile·Ruff F821/F822 PASS. [코드 봉인](../../tmp/nonfixed-quote-implementation-20261017/code-seal.json)과 실제 파일 hash가 통합 검사 뒤에도 일치한다. 셸/wrapper 변경은 없어 해당 검사는 적용하지 않는다.
- 문서 로컬 링크·one-current-owner·authority·print-only parser 및 후보 staged `git diff --check`를 검증했다. 외부 sync는 실행하지 않았다.
- 기존 실패는 `test_reversal_operating_policy.py::test_shared_store_complete_carry_and_loader`의 machine report `scope_census=None`과 auxiliary census 비교다. detector는 report census와 joint census를 별도로 반환하며 테스트는 양쪽에 동일값을 요구한다. [부모 직접 실행 출력](../../tmp/nonfixed-quote-implementation-20261017/selected-parent-existing-failure.txt), [바이트 및 재현 영수증](../../tmp/nonfixed-quote-implementation-20261017/source-recovery-baseline-proof.json)을 보존했다. owner는 `src/engine/error_detectors/artifact_freshness.py`의 report/joint census contract와 해당 fixture다. 후속 조치는 이 계약의 owner 확인 후 fixture 기대값과 직접 consumer를 정합화하는 것이며 closure test는 동일 node다. 이번 source/quote 수리의 실패나 새로운 실거래 차단으로 바꾸지 않는다.
- 리뷰 추가 보완: Main에서 기존 native 진입 대기의 원 결과를 128개 제한 process-local 저장소에 원 TTL 그대로 보관하여 물리 전송 검증에 재사용한다. OFF 상태의 진단 한도 값은 실행 binding에 영향을 주지 않고 전체 원 영수증은 보존한다.
- 실제 probe 호출에서 첫 preflight 거절 뒤 새 0D만으로 1회 재계산에 도달하는 통합 회귀를 추가했다. 별도 observer 역할을 사용하며 가짜 claim/token이나 native-ready 증가가 없다. 이전 실패와 새 평가 ID·현재 ask를 구분한다.
- 원 요청 ask·geometry·spread 사실의 단위/역할을 변조하고 외부 hash를 다시 계산해도 V5/V6/compact-overlay native audit가 거부하는 의미 검증을 추가했다. 회복 계산 dependency는 V5 contract module 목록에 넣고 V6이 상속한다.
- 새 평가의 가격 outcome reference는 현재 계산 ask·평가 시각을 명시한다. trace capture와 calibration consumer가 같은 binding을 쓰며 결손은 source gap으로 제외한다. 원 native CF의 과거 가격/분모와 prior auxiliary bytes는 보존한다.

[최종 완료 영수증](../../tmp/nonfixed-quote-implementation-20261017/completion.json)이 후보 commit·code seal·검증 및 미실행 경계를 결속한다. 운영 등록·정책 포인터·환경 변경·선택 릴리스·배포·재기동·PID 소비·자연 주문/체결·비용 후 성과는 이번 구현 완료의 증거로 사용하지 않는다. 새로운 contract module hash를 소비하는 실제 전환은 후보의 exact active-policy code handoff/native parity가 필요하며 이번에는 발행하지 않았다. canonical 장후 보고서 재생성·provider/API 호출·외부 sync도 수행하지 않았다.
