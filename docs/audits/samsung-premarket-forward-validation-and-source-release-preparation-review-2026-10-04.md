# 삼성전자 장전 독립 검증·원천 수리 배포 준비 리뷰

## 1. 처분

사용자 다음액션 지시에 따라 [준비계획](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md)을 실행했다. **C1 운영 source 수리의 정확한6개 파일 patch와 선택 릴리스 기준 격리 검증을 완료했고, C2 장전 관측 가설2개의 이후 날짜 계약을 고정했다.** 미래 성능 evaluator/자연 데이터 검증까지 완료했다고 표시하지 않는다.

실제 commit·배포·재기동·정책 발행·API/provider·주문·수집 확대는0이다. 기본정책 적용 상태나 다음 영업일 전체 정상기동을 준비 테스트로 확정하지 않는다. 실행상 현재 남은 것은 새 자연 날짜 원천 intake와 별도 운영 적용 절차다.

## 2. C1 배포 준비 증거

- 사용자 workspace HEAD `5fcbea3222c206e809191100da1b33de49ffee10`, 선택 release commit `a17bd6d2587e1204eacd0cd283bcbd854eb71bfc`를 구분했다. workspace 전체 dirty 변경을 release 후보로 섞지 않았다.
- [package](../../tmp/samsung-premarket-forward-preparation-20261004/package.json)와 [C1 patch](../../tmp/samsung-premarket-forward-preparation-20261004/source-repair-C1.patch)에6개 코드/test 대상·physical SHA·base commit·수리 문서 증빙을 기록했다.
- 최종 `candidate-final-worktree`는 해당 release commit의 detached worktree다. patch 적용check와6개 파일 byte 일치 PASS다. 이 worktree는 새 immutable 운영 릴리스가 아니며 selector/systemd route를 바꾸지 않았다.
- rollback 기준은 C1 적용 전의 선택 `a17bd6d2`다. source archive/정책/projection 덮어쓰기를 rollback으로 쓰지 않는다. 새 capture 정상 여부·cache dependency·live PID는 적용 시 자연 receipt로 별도 확인한다.

## 3. producer→public loader 최종 소비

새 test `test_entry_setup_source_repair_readiness.py`가 실제 수정 producer 재계산→canonical capture writer→public incremental loader→warm projection을 tmp fixture로 연결한다. unsupported/micro/hard BLOCK 각각에서3개 mode/economics 조합을 실행했다.

| 조건 | 소비 결과 | 증명 범위 |
| --- | --- | --- |
| 기본 모드, 유효 cost/path | 1행·경제성 계약 유효 | 새 source는 repair opt-in 없이 기본 장후 소비 가능 |
| 기본 모드, cost 없음 | 0행·cost 결손 counter | 경제성 결손 제외 규칙을 유지 |
| independent 모드, cost/path 없음 | 1행·경제성 계약 미확정 | source 보존과 경제성 미확정을 구분 |

모든 경우 source validator 오류0·원trace/action/native watch 보존, historical repair proof 자동등록0, warm cache 재사용을 확인했다. 이 합성 fixture는 미래 실제 capture·상시감시 support·정책 후보나 실제 손익 증거가 아니다. 기본 loader 수리는 원천 경제성 결손을 없애지 않는다.

## 4. C2 장전 고정 계약과 대기

[frozen 계약](../../tmp/samsung-premarket-forward-preparation-20261004/final-v2-cold/frozen-contract.json)의 scope는 삼성전자005930·Main 장전이며 archive는 exact005930_NX·NXT_PREMARKET다. 검토 target10/6 bundle `3c500f6a…`, exact parent `656cfd8e…`를 봉인했다. contract SHA는 `458ce71a62727a21bafb218f42ad56bee2f8c79c0641920ede81379e4996807f`이다.

고정 가설은 **완료봉 distribution 속 현재 매수 흡수**, **가격변화0에서 ask 소진** 두 가지다. 과거1초·proof≥0.5·refill≤0.5·소진>0·하향재호가false·delta≥원parent1.0 조건을 고정했다. threshold·phase·가격/비용/기간을 후단에서 재선정하지 않는다. 원hard guard 실패와 미확인 guard/source를 다르게 처리한다.

[원천 inventory](../../tmp/samsung-premarket-forward-preparation-20261004/final-v2-cold/source-inventory.json)는10/6의projection/raw capture/trade manifest/depth manifest **4개 경로 부재**, `waiting_new_source_date`다. 새 원천 수집/API를 실행하지 않았다. 파일존재만으로 canonical/route/epoch/parent/cost/성능을 검증했다고 표시하지 않는다.

현재 제공한 consumer는 계약검증·순수 가설 mask·파일 inventory다. 새 날짜 성능 evaluator는 원천 intake 이후 별도 후속 구현/리뷰가 필요하다. 독립 비교는 처음3개 적격 자연 날짜, 같은population의parent/candidate 각각binary≥3·독립날짜≥2, parent 대비 비용반영 승률우위를 연구 gate로 제안한다. 소표본 연구 PASS는 정식policy/운영경제성 승인과 구분한다. parent binary0은 비교미식별이며0% 기준을 만들지 않는다. 기존 성공100%/80% 보존 veto는 없다.

`SamsungPremarketForwardValidation1006`을 별도 OPEN owner로 등록했다. 기존 정규장 두 후보 owner와10/6 checklist bytes는 유지했다. 기존 계약은 수리 전 kernel을 봉인한 역사 receipt이므로, 미래 실행 시 자신의 kernel 변경/replan 규칙을 따른다. 신규 장전 계약으로 기존 두 후보의 검증 성공을 대신하지 않는다.

## 5. 리뷰·수정보완·검증

리뷰 보완은 다음과 같다.

1. legacy KRX-only fixture가 장전 scope를 증명하지 못했다. 전체continuous fixture로 바꾸고 KRX fallback 거부 회귀를 추가했다.
2. 미확인 guard proof가 hard 제외로 기록되던 분기를 `source_gap/null`로 수정했다. None·숫자1·unknown에 대한 회귀를 추가했다.
3. 독립모드 roundtrip만으로 기본 경제성 소비를 주장할 수 없었다. 실제 기본모드의 유효cost/path·결손 두 조합을 추가해9회귀로 보완했다.
4. 계약을 다시hash해도 가설/비용/공통 조건/기간/권한/kernel 변경을 거부하도록 전체 고정 spec 대조를 확인했다. gzip projection inventory, null/NaN/bool 입력과 source absence를 검증했다.

5. parent와 모든 내부hash를 함께 바꾸는 self-consistent 변조를 추가 검토했다. 검토 원bundle/parent를 계약 외부의 고정anchor로 묶고 두 추가회귀로 교체를 거부했다.

최종 C1 관련5suite **455 tests PASS**, C2 **33 tests PASS**, 총 고유488tests다. 이전449개 준비본과34개 중복 포함 실행은 역사 진단이며 최종 합계에 중복하지 않는다. C1 compile/diff, C2 compile, 최종 diff/link/owner 및 print-only parser를 확인했다. 최종 `final-v2-cold/final-v2-warm` 계약/inventory 두 파일의bytes가 일치한다. 앞선 `final-cold/final-warm`은 외부anchor 고정 전의 역사 출력이며 최종 kernel 검증에 쓰지 않는다. 검토 범위 내 미해결 구현 결함0이며 미래 evaluator와 실제 성능은 미검증이다.

최종 [closure](../../tmp/samsung-premarket-forward-preparation-20261004/closure.json)에185개 기존source/kernel/문서seal·98개policy/handoff·selector/선택release files·10/3/10/6 checklist 보존을 기록했다.186개 baseline seal 중 이번 승인된10/4 checklist만 before snapshot과old/new SHA로 변경을 추적한다. C1/C2 신규파일·package·frozen output·test logs를 별도로 봉인했다.

PID cmdline의정확한module token으로 Main/widget PID를 확인했으나 `/proc/<pid>/cwd`는 `PermissionError`다. `pid-readiness.json`의`pid_policy_consumption=not_proven`이 최종 상태다. intake baseline의`/proc/.../cwd` 문자열/substring 후보를 실제release consumption 증거로 사용하지 않는다. selected release 파일 확인은 PID 소비 증거가 아니다.

이번 변경은 Kiwoom request/parser/FID/continuation/order protocol을 수정하지 않아 official upstream reference gate는 비해당이다. 거래 전체suite·실제장후 automation·정책 재발행·배포/PREOPEN/PID consumption·natural 실행·실현경제성 검증은 실행하지 않았다. 외부Project/Calendar sync와token 조회도0이다.
