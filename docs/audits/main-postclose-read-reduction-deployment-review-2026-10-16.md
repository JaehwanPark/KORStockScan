# 반복 읽기 개선 재리뷰·배포·07:55 기동 수용 — 2026-10-16

사용자가 코드리뷰·수정보완 반복 후 배포와07:55 정상기동 오류 확인을 명시했다. 기준 구현은 `5af75ddb7cbc219b91c45b238c6be9f8540a2ed9`, 원 선택본은 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`이다. 구현1922개 PASS와 격리 입력 읽기량66.7% 감소는 [원 구현 리뷰](main-postclose-read-reduction-implementation-review-2026-10-16.md)의 결과이며 실제 배포·기동 수용과 구분한다.

## 재리뷰와 보완

07:38 확인 당시 기존 선택본의 정규 PREOPEN이 실행 중이었다. 도중에 selector를 바꾸지 않았다. PREOPEN은07:40:43 succeeded/exit0, bootstrap native 검증은 PASS/findings0으로 완료됐다. 당일 기계 bundle은 `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`로 정규 활성화됐으며 이를 신규 코드의 활성화로 재라벨링하지 않는다.

배포 리뷰에서 delay 코드 계약에 원천 검증 구현 파일도 포함됨을 확인했다. 검토한 source verifier를 바꿨다는 이유로 기존 준비 정책의 code pin을 재작성하지 않는다. 기존 `intraday_release_handoff._verify_entry_code_delta`의 정확한 source-pair 계약에 아래 한 파일만 추가했다.

- 파일: `src/engine/scalping/pre_submit_delay_initial_policy.py`.
- 원 SHA: `ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0`.
- 검토 SHA: `037af000399c501362c62a63e4361501c041e3db0289b1edd059b839e36e0a47`.

검토된 전체 파일 쌍만 인정한다. 임의의 `verify_source` 함수를 허용하는 AST allowlist를 만들지 않았다. 별도 AST 투영에서 변경 함수가 `verify_source`뿐이며 나머지 producer·qualification·selection·정책 상수가 동일함을 확인했다. native 기계 계약37개 파일도 선택본과 모두 동일하다. [원천 코드 대사](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/producer-code-projection.json).

기존 인계·ordered 배포·digest·delay 시험을 다시 수행해 **1995 PASS**를 확인했다. 원/후속/dirty/source-digest 변조 거부와 readonly 동작의 parameter matrix에 새 source map과 해당 producer 파일을 포함했다. 정책 값·원 보고서·원천 봉인·계좌/주문/수량·hard safety와 원 phase deadline은 그대로다.

## 배포 순서와 원본 보존

원 선택본·현재 정책·수동 제외·원 체크리스트·당일 PREOPEN/bootstrap/env/verify·prepared index/readiness10개를 [배포 전 manifest](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/before-manifest.json)에 결속해 private backup으로 보존했다. secret/env 내용은 출력하지 않는다.

당일 PREOPEN을 이미 열었고07:30 code-refresh 경계를 지났으므로 준비본을 새 코드로 재발행하지 않는다. 기존07:55 정기 기동의 native PID 소비를 확인한 뒤, 검토 candidate의 기존 ordered driver로 predecessor 검증→graceful drain→selector→동일 정책 handoff→native 기동/새 PID attestation을 수행한다. 진행 중인 wrapper·이전 PID 위로 selector를 먼저 바꾸지 않는다. 원 PREOPEN·bootstrap·정책을 유지하며 이전 PID와 새 PID의 결과를 분리한다.

실행 owner는 기존 `DirectFamilyPreopenPolicyHandoff`다. 원 봉인 체크리스트 bytes와 OPEN stable ID를 보존하며 새 배포 인계는 별도 감사/transition 영수증으로 남긴다. 배포 후보·실제 기동·오류 탐지의 최종 결과는 아래 후속 영수증까지 미완료다. 코드 PASS를 실제 PID 소비·자연 주문·비용 후 성과로 확대하지 않는다.
