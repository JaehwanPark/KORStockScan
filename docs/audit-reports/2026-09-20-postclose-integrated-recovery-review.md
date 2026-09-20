# 통합 장후 복구 리뷰·실행 증거

원천일 2026-09-17, 실제 준비 발행일 2026-09-20, 적용 예정일 2026-09-21. 9/18은 봇 중지에 따른 관측 미적재다. 운영 봇/주문/조기 PREOPEN을 실행하지 않는다.

## 코드 검증

선택된 메인 개선 code d9e2cdae3 및 리뷰 a189e7d57을 baseline으로 분리 작업본에서 구현했다. 날짜/범위·run/commit/clock/exit/proof를 결속하고 실제 불변 verification attempt와 원 실패를 보존한다. main strict 이전 DONE과 final detector 이전 DONE 경합을 제거했다. summary-only는 전체 완료가 아니다.

widget/machine 독립 wrapper의 exact-date terminal/source hash를 최종 summary/checklist에 포함한다. 역사 복구는 현재 계좌/cost 수집을 하지 않으며 알림을 끌 수 있다. 복구 정책은 원천/발행/적용일을 구분하고 기존 loader가 같은 날짜 계약으로 검증한다. main/compact 정책이 여러 적용일에 공존해도 명시 날짜로 검증한다. checklist 본문·ID·장전 시간창을 대사한다.

영향 회귀 **498 passed (17.70s)**. 범위: wrapper/finalization/cron completion, verifier/controller/direct handoff, checklist/summary, widget/episode dated policy, compact paired publisher/consumer, entry split 및 cancel wait emitter/evaluation/runtime/attribution. 합성 회귀이며 자연 표본·경제성 결과가 아니다. 로그 `/tmp/postclose-integrated-targeted-tests-20260920.log`. Python compile, 변경 shell bash -n, git diff --check 통과. print-only parser27건 중9/21 owner11건이며 외부 sync는 실행하지 않았다.

기존 배포본에서도 확장 정책 테스트2건이 실패함을 재현했다. fixture가 현재 paired 경제성 계약의 원천/terminal/policy identity를 포함하지 않았고 고정 종목과도 겹쳤다. 실제 paired 함수를 사용하는 독립 종목 fixture로 수정했으며 promotion gate는 완화하지 않았다.

## 인계 경계

기존 메인 리뷰의 ME8 alias 일부, ME9/10 전체 운영 경제성 OPEN을 보존한다. 메인 모집단2,281/대리값 비교/정책 carry를 실제 비용 후 실행 EV 완료라고 해석하지 않는다. 정책 준비·전체 실행 terminal·자연 PREOPEN/PID·실제 완료손익은 각각 별도다.

## 실행 상태

코드 검증 이후 커밋/푸시·immutable successor·A–H 실행/재사용·서비스 source binding·9/21 consumer 검증 증거를 추가한다. 이 초안의 실행 준비 상태는 전체 재생성이나 정상기동 readiness 완료가 아니다.


## 최초 복구 실행에서 발견한 추가 결함

- `70f957b7b`는 origin/main 및 feature push 후 immutable 배포됐다. 배포본55개 회귀와 consumer/preflight117개 회귀도 통과했다. main run `b63ad15ea7ac49b8b4a90e67be990d0e`의 원 실패·선행 성공을 보존한다.
- widget은 저장 snapshot 부재 종목에서 캐시 토큰 부재로 실패했다. historical retained-source-only 모드를 추가해 보존된 지원 입력을 계속 계산하고 부족 종목은 기존 quarantine 분모에 남긴다. completed prefix(advisory/auto)는 원 run/code/소스 hash 및 미변경 의존을 검증해 재사용한다. 새 source-context의 기존 partial receipt는 별도 attempt로 보존한다.
- low-price expansion은 캐시 검사 이전 토큰 요구로 저장 원천도 전부 false exclusion했다. 캐시를 먼저 검증하고 missing cache에만 기존 token/조회 경로를 호출하도록 수정한다. historical recovery는 remote 조회 없이 null·구체 missing 원인을 보존한다. 정상시장 API parser/요청/토큰발급/주문 계약은 변경하지 않는다.
- 공식 upstream current SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/core/auth.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`을 확인했다. ka10080 POST `/api/dostk/chart`, 운영/모의 분리와 auth token 발급 endpoint를 확인했으며 실제 token issue/refresh는 하지 않는다. 조회 시각과 원문은 `tmp/postclose-integrated-recovery-20260920/official-reference/index.json` 및 같은 폴더에 보존했다.
- 재시도는 원 sim/rising feedback 성공 metric과 산출물 hash, 미변경 코드/원천 세대를 결속한 adoption receipt를 사용한다. 이 성공을 현재 코드로 다시 실행한 것으로 위조하지 않고 기존 플래그로 해당 두 실행만 생략한다. 다른 필수 producer/strict gate는 그대로 실행한다.
