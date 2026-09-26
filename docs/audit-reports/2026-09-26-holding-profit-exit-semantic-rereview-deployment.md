# 보유 익절 투표 정책·의미 감시 재검토 및 배포 — 2026-09-26

## 결정

`holding-profit-exit-estimated-policy-and-semantic-closed-loop-plan-2026-09-26.md`의 15셀 초기 정책 생산·summary/strict/bootstrap/런타임 소비 경로, 신호 전 비동기 투표, 익절 의미 감시를 재검토했다. 선택된 코드는 `4ab3491d88b36bd7ec3c53d5961c05617a3e9f33`이다. 초기 정책은 `estimated_provisional` 기준선이며 실현 또는 추정 비용 후 우위가 검증됐다는 뜻이 아니다. 정확한 체결·비용·반사실 AI 투표가 없는 셀의 EV와 선택 우위는 `null`이다.

## 리뷰에서 보완한 결함

1. 최종 SELL 영수증의 동결 스냅샷에 TP 신호와 BUY 체결 영수증 맵이 빠져 같은 BUY 세대 계보를 증명할 수 없었다. 스냅샷 키와 부분·최종 체결 필드를 보완하고, 세대 불일치 회귀를 추가했다.
2. 감시기는 부분 체결 대기, 완료 후 비용 결손, 다른 세대의 terminal 영수증을 분리하도록 했다. `trailing_peak_worsen_floor` 발동 종류의 3시장×fast/normal 분모와 claim·모델·저장·신호 시점 p50/p95/p99 계측을 추가했다. 신호 시점 provider 대기는 0으로 기록한다.
3. 강·약 되돌림폭의 dataclass 타입 선언 누락으로 환경변수를 읽는 `constants` 재로딩이 실패했다. 타입을 보완하고 과거 0.6% 합성 fixture에는 그 당시 incumbent를 명시했다. 이미 폐기된 세 스위치를 재활성화할 수 있다는 테스트 가정도 현재 OFF 계약에 맞췄다.
4. 최초 프리마켓 sentinel cron은 설치됐지만 기존 5개 구간이 workspace 소스를 직접 실행했다. router에 `holding-exit-sentinel` 작업을 추가하고 6개 구간 전체를 선택 릴리스로 결속했다. cron의 나머지 행은 유지했다.

## 테스트 데이터와 성능

| 범위 | 결과 |
| --- | --- |
| 보유 투표·익절·체결·장후/장전·트레일링·상수 확대 회귀 | 작업본과 첫 릴리스에서 각각 1,753건 통과 |
| 최종 라우팅 릴리스의 router·sentinel 회귀 | 91건 통과 |
| 합성 재생 결과 | strict 입력 형태의 합성 포지션 1,000건, 15셀, 재생 적격 신호 1,000건, 후보 270개, 제외 0건, 실현 paired EV `null` |
| 합성 재생 계산 | 0.439초 wall / 0.439초 CPU; Python 프로세스 전체 0.60초 wall / RSS 최대 32,148 KiB |
| 소규모 대상 성능 회귀 | 250건 재생과 3시장×5경로 fixture 포함 4건, 1.55초 process wall / CPU 1.71초 / RSS 최대 156,040 KiB |
| 정적 계약 | Python compile, `bash -n`, `git diff --check`, 문서 backlog print-only parser 27건·현 owner 1개 통과 |

합성 계산은 메모리 내 원장을 사용해 파일 I/O, 실제 모델 지연, 브로커 체결, 자연 장후 전체 pipeline wall/RSS를 측정하지 않는다. p95/p99 필드는 생산되지만 자연 표가 없어서 실제 지연 통계는 아직 비어 있다. `2026-09-25` observation의 strict 완료 ID는 0개이고 v10 replay가 없다. 9/26·9/28 observation과 9/28 정책 bundle도 아직 없다. 이를 0 EV, no-edge 또는 실거래 검증으로 바꾸지 않는다.

## 배포와 독립 수용 경계

| 영수증 | 상태 |
| --- | --- |
| 선택 release | `/home/ubuntu/KORStockScan-runtime-releases/holding-profit-semantic-routing-20260926-4ab3491d` / 위 commit |
| 이전 release | `holding-profit-semantic-20260926-d71b10e8` / `d71b10e84f9804cee5c8064f9da11b76e1455835` |
| selector 백업 | `tmp/runtime-release-selection-before-holding-routing-20260926.json`; 최초 전환 전 백업은 `tmp/runtime-release-selection-before-holding-profit-semantic-20260926.json` |
| cron 백업 | `tmp/runtime-cron-before-holding-routing-20260926.txt`; 최초 프리마켓 추가 전 백업은 `tmp/runtime-cron-before-holding-profit-semantic-20260926.txt` |
| 선택·cron 검증 | release-set `passed`, 124 owners, 독립 unit policy pin 실패 0, 6개 sentinel cron selector 경유, 작업본과 릴리스 변경 소스 55개 SHA 일치 |
| 실제 메인 PID | `korstockscan.service` inactive, MainPID 0, 선택 commit 소비 영수증 없음 |
| 날짜별 정책·자연 경제성 | 9/28 bundle 미생성, 자연 v10 표·청산 terminal/비용 성과 미검증 |

9/25 장후 `threshold_cycle_postclose`는 `scale_in_split_order_plan`의 source contract 차단으로 실패했다. 이전 대화에서 승인된 대기 wrapper 중단 후 전환에 따라 controller·tuning 두 대기 프로세스 그룹만 종료했다. tuning 상태는 `predecessor_wait_operator_stopped_for_release_selection`, exit 143으로 남겼다. 이를 9/25 장후 완료로 표시하지 않는다. 메인 봇과 독립 widget/episode는 재기동하지 않았다.

다음 수용 owner는 9/28 checklist의 `[HoldingProfitExitSemanticClosure0928]`이다. 9/28 프리마켓부터 sentinel의 선택 release·3시장 분모·첫 crossing/투표/SELL/비용 상태를 확인하고, 9/28 장후 원천이 완결되면 대상일 정책 bundle→summary→strict→9/29 bootstrap→실제 PID 소비를 날짜·해시로 대사한다. 자연 표본이 없는 경우에는 임시 기준선 소비와 경제성 판단 불가를 별도로 기록한다.
