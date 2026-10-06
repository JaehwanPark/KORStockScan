# 과거 장후 최종화 연결 복구 리뷰 — 2026-10-06

## 판정

10/2 원천의 원 적용일 10/6 최종화가 16:08:38 native DONE으로 복구됐다. 16:10:07 당일 health artifact는 FAIL 0, cleanup/finalization 모두 `recovered_late`, Main process health PASS다. 오전 기한 준수·새 정책 생성·실제 비용 수익 개선·10/7 기동 성공의 증거는 아니다.

## 원인과 보완

1. 최초 정리 실패는 provider 원장의 companion 결손이었다. [원천·정리 감사](fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md)의 원본 보존 복구로 15:09:46 cleanup 자체는 완료했지만 최종화는 실패 상태로 남았다.
2. 퇴역 이후 v3 소비자가 과거 v2 완료 영수증까지 거부했다. 과거 발행일에만 원 digest/date/run/code/output/input/prerequisite를 검증하는 읽기 호환성을 추가했다. 새 producer와 cache/check는 v3를 유지한다. 퇴역 Widget producer를 복원하지 않는다.
3. 정책 보존 재기동은 원 PREOPEN manifest와 현재 PID의 release가 다르다. Native 당일 인계 권한·frozen 파일·실제 consumed PID/start ticks/cwd·canonical bootstrap을 검증해 장후 소비자에 연결했다. Read-only 검증은 독립 report release에서도 가능하며 prepare/consume의 selected cwd 요건은 유지했다.
4. 원 기계 단계가 참조한 `designated-machine-policy-20261005-3d0e5106` 경로가 없었다. Git의 원 commit을 동일 경로에 복원하여 원 code hash를 검증했다. 정책 및 v2 영수증 원본을 변경하지 않았다. 해당 root는 현재 선행 증명의 보존 의존성이다.
5. 과거 복구는 원 source/effective date를 유지하며 적용일 PREOPEN 시각이 지났으면 다음 날짜 준비를 생성하지 않는다. Summary만 재생성한 뒤 현재 checklist/tower/strict/controller, native cleanup/detector와 finalization chain을 닫았다.

## 리뷰와 검증

- 수정 commit: `72716b6c` → `999ee899` → `eeccb1f4`. `999ee899`는 사전 정책 증명 실패로 소비되지 않았고 기존 selector/PID를 유지했다. Failed attempts 및 sealed 원본 복귀 실패도 보존했다.
- 구현 → 자기 리뷰 → 발견 결함 보완 → 재리뷰 → 관련 회귀: 각각 400/444/94 PASS. 이 숫자는 서로 중복되는 실행별 결과이며 합산 고유 테스트 수가 아니다. Compile, affected shell `bash -n`, diff check와 print-only parser PASS. 외부 동기화와 전 종목 재훈련은 실행하지 않았다.
- 회귀 범위: 과거 digest·date·입출력·원 코드 변경 거부, 새 v3 producer의 v2 재사용 거부, holiday effective date와 historical PREOPEN, frozen env/manifest 변경·미소비·이전 PID·다음 날짜 거부, 독립 read-only 검증과 prepare/consume cwd 차단, native migration 실패 시 FAIL 및 detector 실행.
- 최종 검증에서 현재 선행 12개와 summary의 결손 0, whole-chain strict PASS/controller DONE. 검토한 수정 범위의 미해결 코드 finding은 0이다. 아래 별도 원천 warning과 자연 수용은 남는다.

## 실제 반영과 완료 증거

| 항목 | 확인 결과 |
| --- | --- |
| Main release | `postclose-finalization-handoff-20261006-eeccb1f4` / `eeccb1f4127a39d7454c8bb464f1018cb4365812` |
| Main 실제 소비 | PID `60572`, 16:05:35 bootstrap/PID PASS, native intraday consumed 일치 |
| 정책 보존 | 원 정책·입력·선행·PREOPEN 30개 SHA 불변; holding-vote 원 SHA `95e5caf57a53e25a932b135335c40cbd4e17dd5084c7a889b2880b7d22dc1717` 불변 |
| 사전 custody | fresh KRX/NXT Doosan 잔고 0·미체결 0·미확정 intent 0. 다른 owner의 정책/에피소드 PID는 유지 |
| Release set | 116 Episode route·348 policy pin PASS; 기존 failed 3개는 그대로 표시 |
| Native cleanup | 16:08:30 DONE; storage/data/compression 실패 0 |
| Native finalization | 16:08:38 DONE; `preopen=not_applicable_historical_recovery` |
| Chain SHA | `2ffd804360a6c73ec5b0b861245aebbe934a7b5012b5f5d9214620d26a22d6f7` |
| Snapshot SHA | `de8c7a024a0ad4b385fda97148f5e1043fdc6e3161eb981ecbd12f7b081bf112` |
| Final detector | `cron-20261006T160830-105951`, report SHA `326e7abfb046fbdc1033ffc2f5f7a513469ecace742c96234445c5859d427c55` |
| 완료 뒤 health | 16:10:07 FAIL 0 / process PASS / 두 job `recovered_late` / operational mutation 0 |

실행별 로그, 실패/복귀 사본, before/after SHA와 검사 결과는 `tmp/postclose-finalization-contract-recovery-20261006/`에 보존한다. Native 완료는 `logs/postclose_finalization_cron.log`, 현재 탐지 결과는 `data/report/error_detection/error_detection_2026-10-06.json`에서 확인한다.

## 별도 미완료 상태

- 오전 06:50을 넘긴 복구이므로 `recovered_late` 경고를 지우지 않는다.
- Main/auxiliary 운영 paired 경제성, exact plan/label 원천 및 Episode semantic producer 변경 warning은 본 연결 복구로 대체하지 않는다.
- 자연 고정감시 판정 A3와 10/6 장후·10/7 기동은 [현재 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)의 `FixedWatchSourceAndCleanupRepair1006` 및 `FixedWatchBudgetSummaryPostcloseAcceptance1006`에서 별도 수용한다. 과거 정리 복구를 내일 기동 확정으로 표시하지 않는다.

## 18:35 세대 불일치의 후속 복구

- 새 경보의 원인은 완료 이후 변경된 공유 체크리스트다. 16:06 strict가 검증한 SHA `fe556921b48e5220c6f656a22e94130e602c452221e2339d051864eccb828f80`와 에피소드 퇴역 작업 후 SHA `bb500b328ebe08033040e49942927e9bb0e446a71bcc433285add09ff4d9f9db`가 달라졌다. 기존 DONE을 현재 유효 완료로 재사용하지 않았다.
- 후속 정책 보존 재기동의 release/PID도 기존 summary와 달랐다. 현재 `511664f3`의 native intraday 소비를 검증한 summary부터 tower/checklist/strict/controller를 갱신했다. 원 source=`2026-10-02`, effective=`2026-10-06`을 유지하고 정책 생산자·전체 장후 wrapper를 재실행하지 않았다.
- 원천일의 선행 12개와 summary를 canonical data 경로에서 읽기 검증했고, 관련 finalization/controller 회귀 33개 및 shell syntax가 통과했다. 기존 정책·원천·선행 영수증·PREOPEN·holding-vote·main terminal·snapshot manifest 등 보호 파일 38개의 SHA가 모두 동일하며 Main PID `169115`의 start ticks/cwd도 유지됐다.
- 18:42:37 첫 native 재시도는 strict PASS/controller DONE/18:45:02 cleanup DONE 이후 정기 full detector와 잠금이 겹쳐 `final_detector_failed`로 종료했다. 해당 FAIL을 보존했고 활성 잠금을 제거하지 않았다. 정기 탐지 종료와 잠금 해제 후 18:45:58 한 번 재시도했다.
- 18:48:26 native finalization 및 final detector DONE. Chain=`ec5cad3eb7fa7014513e14a77a72a42de6777be49bbb8e47a9a4ae1a23ea0fcf`; snapshot=`de8c7a024a0ad4b385fda97148f5e1043fdc6e3161eb981ecbd12f7b081bf112`로 원 snapshot 세대는 유지됐다. Detector=`cron-20261006T184821-265246`/report SHA=`76640974fceeff2c99d9b0377418467ca8630fe6588d23b273144cd3ccfa70ee`, 7개 detector의 FAIL은 0이다.
- 18:49:16 독립 읽기 검증에서 controller/marker issues 0, 현재 checklist SHA와 strict binding `83bd11c6882417abcdd6c776c5776561fd422b50575e9adc0d87fdfd6d04b76c` 일치, cleanup/finalization 모두 `recovered_late`를 확인했다. Native 자동 checklist 갱신은 기존 OPEN stable ID와 권한을 보존했고 print-only parser 27개 항목 및 diff check를 통과했다.
- 18:50:50 당일 full health artifact에서도 FAIL 0, Main process health PASS, cleanup/finalization `recovered_late`를 확인했다. `strict_checklist_generation_stale` 및 후속 실패 marker 경보가 해소됐으며 해당 health 사본은 같은 증거 디렉터리의 `current-date-health.json`에 보존한다.
- 실행 전후 사본·보호 해시·실패/완료 기록·독립 재검증은 `tmp/postclose-strict-generation-reseal-20261006/before.json`, `after.json`, `recovery-attempts.log`, `checklist-parser.txt`에 보존한다. 추가 Python/shell 코드 변경·배포·봇 재기동은 없었다. 완료 이후 체크리스트나 소비 세대가 다시 바뀌면 같은 native 연결을 재검증해야 한다.
- 이 복구는 원 10/2 완료 연결을 복구한 결과다. 기한 초과 경고와 기존 운영 경제성/plan/label 원천 결손은 유지하며, 10/6 자연 장후 및 10/7 기동 성공을 대신하지 않는다.
