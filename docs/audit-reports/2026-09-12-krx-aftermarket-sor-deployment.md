# KRX/NXT 통합 애프터마켓 SOR 배포 receipt

기준 시각: 2026-09-12 10:44:26 KST
대상 자연 거래일: 2026-09-14

## 판정

`AM-S26` 코드·배포 blocker는 해소됐다. 선택 release는 `/home/ubuntu/KORStockScan-runtime-releases/krx-aftermarket-sor-r2-20260914`, commit `a0ab279c002b026b82b6447d4a0a3d1be1cab2ef`이다. 9/14 실제 main PID·세션 전환·canary 주문·체결 venue·장후 terminal은 미래 자연 증거이며 아직 완료로 선언하지 않는다.

## 고정 코드와 승인

- 작업본 root `/home/ubuntu/KORStockScan`에서만 수정했고 기존 선택 release는 제자리 수정하지 않았다.
- 코드 고정: `f8917fa1` 후 cron reconciliation 보완 `a0ab279c`; 최종 release의 `src/deploy/restart.sh`는 clean이다.
- 승인 artifact: `data/runtime/krx_aftermarket_sor_canary_approval/krx_aftermarket_sor_canary_approval_2026-09-14.json`; canonical payload SHA256 `ddb4f9e78bc83baa0f87d6a7250756b7ea1ed3f959759702c1dddbfd46eb6822`.
- 권한: main initial `ENTRY_BUY`, one share, existing cap/cooldown/hard guards, route `SOR`, 2026-09-14 16:00~19:40 KST. 자격·owner·hash·root·commit·session·quantity 불일치는 broker transport 전 차단한다.
- Kiwoom official reference: `Kiwoom-Securities/Kiwoom-REST-API` commit `234560d213acd8871ae344b5481aecd2f30287fa`.

## 설치·재기동

- main selector를 최종 release/commit으로 교체했고 PREOPEN/start print-plan이 같은 root를 가리킨다. 배포 전 selector는 `tmp/krx-aftermarket-sor-20260914/runtime_release_selection.before.json`에 보존했다.
- 9개 runtime-router cron은 `cron_routing_verified=true`; 관찰 cron은 transition 제외, 16:00~20:00 integrated label, BUY 19:40 종료, holding/WS 19:50 종료로 설치했다. router backup은 `tmp/runtime-release-cron-8vujy3dq`다.
- 17개 독립 unit의 `zzz-krx-aftermarket-sor.conf`가 최종 root를 고정한다. 기존 drop-in은 `tmp/krx-aftermarket-sor-20260914/systemd-before`에 보존했다.
- 당시 active였던 read-only Doosan/Hanwha/Samsung collector와 fill notifier만 각각 1회 재기동했다. 새 PID는 각각 `58398`, `58400`, `58402`, `58736`이고 모두 active/running, `Result=success`, 최종 root 소비다. 비활성 매매·사전검증·분석 service는 강제 기동하지 않았다.

## 검증과 잔여

- 코드 gate: 최종 보완 전 AM-S26P 영향 suite `709 passed`; 최종 cron 보완 test `1 passed`; Python compile, shell syntax, `git diff --check`, review P0~P2 finding 0.
- 배포 gate: approval loader exact-date dry validation PASS, 17 unit drop-in hash/root PASS, systemd unit verify PASS, main/postclose cron route PASS. 실제 broker/provider 호출·주문·보고서 재생성은 이 배포 중 실행하지 않았다.
- 잔여 acceptance는 체크리스트 `KrxAftermarketSorCanary0914`가 소유한다. 실제 기회가 없으면 기회 부재로 남기며, 비용 후 EV/순익은 완료 표본 후 별도 판정한다.

## 17:56 KST successor-policy release update

- Main selector is now `/home/ubuntu/KORStockScan-runtime-releases/prompt-quantity-sor-r3-20260912` / `8e084abfd2bb8dedfe507b2f30c32a591a71275a`; its source tree is clean and shares canonical data/logs/tmp/.venv/docs with the workspace.
- The canary approval was rebound to that exact root/commit without changing its date, time window, one-share cap, SOR route/type, existing caps/cooldowns/hard guards, or rollback owner.
- This release separates prompt selection from quantity/residual/scale-in owners and adds the exact-date, hash-bound post-canary successor policy. It requires broker acceptance and receipt, SOR/type contract, source-quality, a valid central sizing policy, and current symbol venue eligibility. Natural 9/14 execution and subsequent PREOPEN/PID evidence remain pending.

## 18:10 KST prompt-activation ownership correction

- Main selector is now `/home/ubuntu/KORStockScan-runtime-releases/prompt-activation-owner-r4-20260912` / `724a25ce7a23e675bed7f0fd9fc9c5c3f77dc61b`; its source tree is clean and shares canonical data/logs/tmp/.venv/docs with the workspace.
- The exact 9/14 canary approval was rebound to this root/commit and its canonical artifact hash was verified. Its date/window, one-share cap, SOR route/type, existing caps/cooldowns/hard guards, and rollback owner did not change.
- Prompt activation no longer treats entry-split probe leg quantity as an activation invariant. Probe-first/recheck and the durable daily quantity policy remain independent guards. No main PID was running, so no service was restarted and natural 9/14 PREOPEN/PID/canary evidence remains pending.
