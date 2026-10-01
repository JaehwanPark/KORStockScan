# 10월 2일 봇·에피소드·위젯 최종 정책 기동 준비

원천/확인일: 2026-10-01 KST. 기동 대상일: 2026-10-02 KST.

사용자는 내일 세 소비자가 오늘 최종 재생성한 정책으로 정상 기동하기를 명시했다. 이 지시로 동일 정책의 다음 날짜 승계 발행을 수행했다. 현재 메인 봇 기동, 주문, threshold·수량·provider·custody·hard safety 변경은 수행하지 않았다. 실제 내일 기동은 아직 미관측이다.

## 확인 결과와 조치

| 소비자 | 확인 근거 | 준비 결과 |
| --- | --- | --- |
| Main | 선택 릴리스 `459d718f8082cc6b9b0ca532eeda40b52c42dc29`; 9/30 닫힌 controller·summary와 10/2 기계/보조 정책에 결속된 준비본을 선택 릴리스에서 재검증 | `next_preopen_readiness --verify --target-date 2026-10-02`: `pass`, findings 0. 운영 10/2 bootstrap·당일 성공 영수증·PID 소비는 아직 없음 |
| Episode | 기존 10/1 적용본 `validate_applied=True`; 최종 9/30 후보와 기존 적용본 및 10/2 정식 baseline 발행기의 61개 실행 정책 완전 일치 | 10/2 applied 발행·readback·실제 systemd 소비 릴리스 로더 확인. 58개 `ready`, 기존 격리 3개 유지 |
| Widget | 실제 systemd 소비 릴리스 `30e66ae584a78911211d461483c01ecf03f6887c`의 10/2 `WidgetAutoTradePolicyLoader` | 3개 종목·4개 session 정책 유효. 10/1과 enabled/entry states/TP/add/cooldown/exit action/new-entry eligibility 실행 필드 동일 |

Episode의 원래 PREOPEN 발행 경로는 `candidate_source_quality_hash_mismatch`로 실패한다. 그 후보의 effective date도 `2026-10-01`이어서 10/2 재사용 조건을 충족하지 않는다. 이 후보를 튜닝·경제성 근거로 재승인하거나 원천 해시를 고쳐 쓰지 않았다. 이미 검증된 incumbent와 실행값이 완전히 같은 `baseline_applied_payload`를 사용하고, 사용자 지시·원본 스냅샷·해시·원천 결손을 별도 승계 영수증에 기록했다. `source_date/source_candidate=null`은 신규 후보 승격이 없는 안전 승계 발행기 계약이다.

- [10/2 Episode applied](../../data/threshold_cycle/low_price_two_leg/applied/low_price_two_leg_policy_2026-10-02.json)
- [사용자 지시·동일 정책 승계 영수증](../../data/runtime/startup_readiness/2026-10-02/episode_policy_carry.json)
- [로더 확인 영수증 및 기존 격리 목록](../../data/runtime/startup_readiness/2026-10-02/policy_validation.json)
- [Main 준비본 인덱스](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json)

Episode 정책 해시: `590642d99e263254fc10663b01f62966d6461f78a63a4574998115296a738ebb`. 사용자 지시 전 incumbent, 최종 후보, 새 10/2 applied가 모두 같다. 기존 `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday` 격리를 해제하지 않았다. 원래 파일은 보존하고 원본 적용본·후보를 `data/runtime/startup_readiness/2026-10-02/`에 별도 보관했다. 양 소비 릴리스에서 정식 PREOPEN CLI가 새 파일을 `exact_date_policy_reused`로 인정하며, `--write`의 기존 policy-apply lock 경로도 확인했다.

## 일정과 당일 수용

- cron 서비스 active, release-set 검사 passed, 예약 라우팅 8개 검증.
- 07:32 owner custody 자동 발행 → 07:35 Main PREOPEN → 07:55 Main start는 기존 예약을 사용한다.
- Widget 서비스는 현재 active이며 날짜 전환 시 해당 날짜 정책을 다시 읽는 경로가 있다. 이미 실행 중인 서비스에는 기동 timer의 다음 발화가 표시되지 않을 수 있다. 이것을 내일 새 PID 생성 영수증으로 해석하지 않는다.
- Episode preflight/live timer 122개 모두 다음 예약이 10/2이다. 오늘 확인한 `hanse_morning` preflight 실패는 `main_bot_inactive`였다. 내일 Main 실제 기동 후 각 profile의 당일 preflight를 통과해야 한다.
- 내일 05:00 최종화는 원천 없는 10/1을 대상으로 실패할 수 있다. 그 실패와 9/30 원천의 10/2 준비본은 별도 세대이며, 현재 준비본 검증은 그 실패에 의존하지 않는다. 10/1 failed 기록을 success로 덮거나 finalization을 건너뛰지 않았다.

당일 closure는 10/2 PREOPEN `succeeded`와 선택 릴리스, Main PID cwd/commit/bootstrap hash, Widget 날짜 전환 정책 소비, Episode 당일 preflight·정책 hash·해당 시각 서비스 소비를 확인한다. custody 또는 broker/quote hard guard의 정당한 차단은 기동을 강행할 이유가 아니다. 정책 준비·PID 소비·주문·체결·비용 후 성과를 각각 구분한다.

## 리뷰·검증

구현은 기존 발행기를 통한 동일 정책 JSON 발행에 한정했다. 실행값·원본·승계 권한·원자 발행/readback·소비 릴리스 로더를 리뷰하고, 정식 `--write` 잠금 경로 및 두 릴리스의 재사용 경로로 재확인했다. 코드/릴리스/cron/systemd 설정은 변경하지 않았다.

- 선택 Main 릴리스: readiness·wrapper 시험 27 passed.
- 실제 Widget/Episode 릴리스: 관련 applied/baseline/quarantine 시험 8 passed, Widget loader 시험 11 passed.
- 같은 릴리스의 더 넓은 두 파일 시험은 244 passed / 2 failed였다. 두 실패는 테스트의 9/17 입력과 현재 날짜에서 생성한 publication date가 7일 source-age 한도를 넘으며 `baseline_candidate_stale`이 되는 기존 fixture다. 이번에 코드 변경은 없고, 사용한 안전 승계·실제 로더 표적 시험은 통과했다. 전체 suite PASS라고 주장하지 않는다.
- 문서 print-only parser 성공, `FinalPolicyStartupAcceptance1002` 현재 parsed owner 1개, 링크 결손 0, diff whitespace 검증 통과. 코드 변경이 없으므로 compile, 새 protocol 검증, provider/broker 호출, 전체 보고서 재생성과 외부 sync는 실행하지 않는다.

되돌림은 10/2 최초 preflight 이전에 이 작업의 미래일 applied만 제거하는 범위다. 당일 소비/보유가 생긴 뒤에는 기존 custody·rollback owner를 따른다. 오늘 메인 봇을 기동하지 않았고 내일의 PID·자연 주문/성과 영수증은 생성하지 않았다.
