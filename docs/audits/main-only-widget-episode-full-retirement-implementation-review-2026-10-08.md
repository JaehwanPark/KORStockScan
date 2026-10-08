# Main-only 전체 퇴역 구현 검토 — 2026-10-08

사용자가 에피소드·위젯 전체 제거, 반복 코드리뷰/보완, 배포·재기동과 불필요 임시/과거 파일 정리를 승인했다. 과거 체결 잔여는 사용자 수동관리이며 계좌 조회·매도·broker flat을 작업의 조건으로 두지 않는다.

공통 journal은 원 owner/fill/terminal을 변경하지 않고 수동관리 지시만 한 번 append한다. Main 자동 실행 투영은 Main 수량만 사용하고 구 owner의 pending intent를 실행/차단 권한으로 사용하지 않는다. Main 정책과 부모, DB·수동 veto·hard/order guard는 유지한다. 전용 production 코드/설치 payload/test를 제거하고 Main 공통 digest, packet source validation, adverse flow, 시장일, 재기동 flag, native Main/manual custody를 살아 있는 역할 package로 옮겼다.

리뷰에서 남은 취소대기/수량 연구의 간접 import, 삭제된 handoff를 참조하는 restart wrapper, 동결 재생의 파일 생성, 장후 intake NameError와 옛 checklist 복원 발행을 발견해 보완했다. read-only journal 조회는 hash-chain 및 전후 파일 세대 검증을 수행하며 실제 주문 예약은 flock을 유지한다. frozen replay는 기록된 common journal과 명시적 부재만 읽는다. 과거 strict/controller/finalization은 기존 13개 stage의 원 바이트를 검증하며 미래 stage는 6개 Main 구성만 발행한다.

Kiwoom official reference HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`은 실제 조회 SHA를 evidence JSON과 대조한다. 공식 specs/core/realtime/패킷/schema/Postman을 확인했다. API wire/FID/auth/호출 제한 변경은 없다. 로컬 retired-owner guard와 전용 WS writer 제거만 수행한다.

검증·배포·삭제 결과는 이하 최종 영수증에 기록했다. 자연 다음 장후/기동은 예정 시각 전에는 관측되지 않은 상태다.

배포 직전 검증에서 보유종목 보조정책의 10/7 summary가 삭제된 stage의 원 입력 집합을 요구하는 결함을 발견했다. 옛 코드의 원 계약으로 summary를 검증한 후 원 terminal·immutable strict·입력/출력 hash를 퇴역 영수증에 한 번 결속했다. 읽기 전용 소비자는 이 동일 바이트만 확인하며 현재/미래 날짜나 producer 재실행에는 적용하지 않는다. 옛 실행본을 보관하거나 10/7 장후를 다시 생성할 필요가 없다. 원천·terminal·strict·archive 변조와 cutover 날짜 회귀를 포함한 관련 168개 검사가 통과했다.

설치 삭제 후 현장 리뷰에서 감시기가 당일 오전의 과거 episode 예약을 신규 누출로 오인하고, systemd의 정상적인 빈 설치 조회(exit 1)를 결손으로 분류함을 확인했다. 수동관리 사건의 정확한 시각을 퇴역 영수증에 결속하고 그 이후 모든 자동 owner action을 탐지한다. 빈 stdout/stderr의 exit 1만 정상 빈 목록이며 권한 오류는 계속 결손이다. 과거 history와 현재 누출, 매도/취소, 잘못된 시각, 권한 오류를 검증했다. Main/manual custody 보호와 당일 정책은 유지한다. 해당 보완을 포함한 255개 검사가 통과했다.

최종 소비 경로 리뷰에서 Main launcher 외의 웹·예약 작업에 공통 native 계좌/원장 식별자 전달이 누락됨을 확인했다. router는 제한된 두 키를 shell 실행 없이 읽고 retired receipt가 있는 상태의 결손/변조·중복·상대경로를 차단한다. 웹 unit은 같은 파일을 EnvironmentFile로 읽는다. router/퇴역/summary/custody 관련 216개 검사가 통과했다. 운영 문서의 옛 flat 전제·전용 서비스 복구/설치 명령도 현행 Main-only 계약으로 대체했다.

검증은 핵심 폐쇄 회귀 615개, Main/manual/watch/order 155개, frozen full replay 98개와 후속 archive 168개·monitor 255개·identity 216개 등 변경별 범위로 실행했다. 중복 검사를 전체 고유 테스트 수로 합산하지 않는다. 전체 src/tests 수집에는 기존 PYRAMID 테스트가 이미 없는 `_pyramid_quality_decision`을 import하는 별도 오류가 있어 전체 suite 성공을 주장하지 않는다. 운영 성능의 통제된 전후 비교나 신규 손익 검증은 이번 삭제 결과와 구분한다.

구 실행 릴리스 삭제 뒤 두 번째 장중 handoff 준비에서, 원 strict가 기록한 옛 docs symlink를 무조건 읽어 FileNotFoundError가 발생했다. 없는 원 경로는 정확히 봉인된 Git/보존 snapshot·직전 실제 PID consumption으로만 복구하도록 수정했다. 원 snapshot 변조는 계속 차단하며 새 문서로 원 세대를 대체하지 않는다. 삭제된 원 경로 성공·snapshot 손상 실패를 포함한 handoff/router/퇴역/summary/custody 286개 회귀가 통과했다. 실패한 준비 중에는 기존 Main PID를 중지하지 않았다.

최종 배포는 `main-only-retired-20261008-v5` / `2e056fc144ec08bdf0e0d3fc3d3063575ace4ca9`다. Main PID 161317, 웹 PID 161479의 cwd/식별자 일치·웹 HTTP 200을 확인했다. Main 128경로·48운영 scope의 `consumed_exact`·bootstrap/handoff PASS와 12:55 감시 5 heartbeat가 관측됐다. 원 전략 pointer의 바이트 SHA `6ab9aed09de80a0a6d25886a061132853c70ff586c3cad11c3f90a1cc726a11f`와 journal의 원 1,904,385바이트 prefix SHA를 보존했다. 다음 자연 장후/기동은 아직 예정 전이며 EOD·10/7 연구 재실행은 하지 않았다.

서버에는 gunicorn(enabled)·대체 web(disabled) 두 unit만 남았고 episode/widget/독립 IPO 예약·worker·설치/재설치 payload를 제거했다. 전용 소스/배포/테스트 325파일, unit/timer 217개·설치 파일 562개, 초기 구 worktree 107개와 최종 후속 릴리스 4개, 전용 데이터 5,182파일·검증된 복제본을 삭제했다. 현재/복구 Main-only 릴리스와 미통합 research dirty 작업본, Main hash 참조 6,223파일·원천·DB/journal·고유 미검증 자료는 보존했다. 디스크 사용률 76%→68%, 12:57 전후 가용 50,439,606,272바이트(46.98 GiB)다. 각 단계 free delta는 활성 원천 증가와 겹치므로 단순 합산하지 않는다.

12:55 자연 full 감시 결과는 과거 지연 완료의 cron warning만 있으며 `strict_checklist_generation_stale`와 퇴역 owner 누출은 없었다. `recovered_late`는 숨기거나 새 finalization 성공으로 재작성하지 않았다. 코드 범위 내 미해결 결함 0과 테스트 성공은 운영의 모든 미래 결함·손익이나 통제된 성능 비교의 완료를 의미하지 않는다. 전체 suite의 기존 PYRAMID import 수집 오류와 다음 자연 Main 장후 확인은 분리해 남긴다.

증거: [최종 배포/정책/삭제 검증](../../data/report/main_only_retirement/2026-10-08/deployment_final_v5.json), [설치 삭제](../../data/report/main_only_retirement/2026-10-08/installed_retired_unit_deletion.json), [worktree 정리](../../data/report/main_only_retirement/2026-10-08/worktree_cleanup_result.json), [전용 데이터 정리](../../data/report/main_only_retirement/2026-10-08/data_cleanup_result.json), [복제본 정리](../../data/report/main_only_retirement/2026-10-08/copy_cleanup_result.json), [최종 구 릴리스 정리](../../data/report/main_only_retirement/2026-10-08/final_superseded_release_cleanup.json).
