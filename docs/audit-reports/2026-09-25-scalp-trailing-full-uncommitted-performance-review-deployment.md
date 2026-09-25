# 스캘핑 익절 전체 미커밋 변경 성능·리뷰·배포 기록

기준: 2026-09-25 KST. 범위는 4축×3시장 bootstrap·실거래 입력 전이·장후 재생·과거 중립 시나리오·17개 운영 입력 민감도, 관련 보고서·소비자·문서의 전체 미커밋 변경이다. 실제 임계값 선택, 메인 프로세스 재시작, 독립 위젯·에피소드 소유자 변경, 자연 수익 승인은 범위에 없다.

## 코드리뷰와 보완

- 앞선 4축 리뷰의 공통 ID 분모, 보수적 체결수량·슬리피지 검열, source hash·비용·정확 시계 검증을 다시 확인했다. 실제 익절 뒤 후보는 실행 가능 후행 bid·경쟁 청산 경로가 없으면 `censored_after_actual_take_profit`이며 비용 후 효과를 만들지 않는다.
- 이번 재리뷰에서 한 포지션의 전이들이 같은 4축 시장 vector hash를 주장하면서 실제 vector payload가 서로 다른 경우, position outcome이 첫 값만 확인하는 결함을 수정했다. 전이 전체 payload가 같아야 연결하며, 다른 값은 결손으로 격리한다.
- NXT 원천에서 실제 `0B` 수신시각이 없으면 런타임 guard는 stale로 취급한다. 운영 재생도 같은 의미로 처리하게 고치고 `_AL`·`_NX`, `nxt_only`·`krx_nxt_integrated` route 회귀를 확인했다. 변경된 호출/호가/체결의 반사실 결과는 여전히 미식별이다.

## 성능·계산 검증

합성 자료는 329개 포지션×256개 평가를 같은 정규장 경로에 놓았다. 전이 시각·bid/AI freshness·청산 신호·매도 체결시각을 일관되게 묶은 뒤 원천 결손 0건을 확인했다. 최초 성능 시도는 청산 신호를 마지막 평가보다 8분 뒤로 둔 fixture 오류로 329건 모두 source gap이 되어 폐기했고, 아래 수치에는 넣지 않았다.

| 범위 | 1회 / 반복 wall | 1회 / 반복 CPU | 최대 RSS | 결손 | 반복 결과 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4축 329포지션×256전이 | 62.876 / 62.705초 | 62.872 / 62.674초 | 403,488KB | 0 | SHA256 `313eac7f19d49365cdc4677811106fef9c291f3301a4a02eaa3db15d9b639ef6` 일치 |
| 운영 입력 329포지션×40전이 | 0.411 / 0.410초 | 0.411 / 0.410초 | 79,876KB | 0 | SHA256 `1378bd514760614fd79d378b668d8eae43155b6f6d22858479206f97c68a4537` 일치 |
| 9/23 보존 원천 holding-exit 보고서 읽기 전용 빌드 | 60.093초 | 60.089초 | 1,703,272KB | 엄격 적격 0 | 4축·운영 입력 모두 `hold_population_census_or_empty` |

합성 계산에는 원천 파일 I/O·provider 호출·주문이 없다. 보존 보고서 빌드는 저장하지 않았고 전체 postclose strict handoff도 실행하지 않았다. 9/23 보존 자료의 엄격 적격 0건 때문에 이 계측은 자연 4축 경제성이나 세 시장 노출의 성능 수용이 아니다. 기존 monitor wrapper의 1,200초 timeout과 60초 빌드 시간은 별개이며, 다음 새 자연일의 전체 stage wall/CPU/RSS·대기·handoff를 관측해야 한다.

영향 범위 pytest **444건 통과**, 관련 Python compileall·Ruff·`bash -n`·`git diff --check` 통과. 문서 backlog print-only parser는 26개 작업을 읽었다. 메인 release-set 선택 전 검사는 PASS이나 `functional_runtime_health=not_assessed`였고 메인 PID는 없었다.

## 배포·수용 경계

사용자가 승인한 전체 미커밋 사항은 immutable 메인 release로 고정하고 `data/runtime/runtime_release_selection.json`의 원자적 선택 영수증에 정확한 root/commit·이전 root·rollback을 기록한다. 장후 wrapper가 실행 중이면 selector를 바꾸지 않는다. 새 선택은 이후 메인/예약 작업의 코드 경로이며 실제 PID 소비, 9/28 자연 체결·비용 후 EV, 운영 입력 변경 후보 및 공유 quote/REST owner 안전 승인은 별도 판정한다. 임계값·provider·주문 정책은 이 배포에서 변경하지 않는다.
