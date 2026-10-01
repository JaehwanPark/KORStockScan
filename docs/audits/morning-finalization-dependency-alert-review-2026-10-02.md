# 10/2 아침 최종화·로그 정리 경보 점검

## 원인과 적용 경계

07:00 경보의 원천일은 10/1, 예정 적용일은 10/2다. 선택 릴리스는 `semantic-postclose-monitor-20261001-c6453530`. 05시 최종화는 `predecessor_terminal_failure`로 cleanup 전에 종료됐다. 로그 정리의 별도 실행 실패가 아니라 선행 실패 때문에 미실행된 상태를 같은 경보에 중복 집계했다.

- [10/1 장후 상태](../../data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-01.status.json)는 20:57:11 `command_failed`, exit 2다. 실제 마지막 실패 module은 `scale_in_split_order_plan`, 상태는 `blocked_source_contract`다.
- [10/1 원천 감사](../../data/report/observation_source_quality_audit/observation_source_quality_audit_2026-10-01.json)는 pipeline raw와 AI archive가 없어서 `source_quality_raw_missing` / `machine_ai_archive_missing_or_invalid`다. Main은 전일 승인된 OFF 상태였으므로 새 판정 원천을 재실행으로 복구할 수 없다. 0건을 정상 무기회·비용 후 수익 0으로 처리하지 않는다.
- 기계 stage는 원천 감사에서 deferred, 보조·label·legacy stage는 미생성이다. 구 독립 worker 중단과 이후 배포 때문에 일부 stage는 deferred/code_changed다. 실패한 전체 체인을 성공으로 재봉인하거나 결손 원천을 합성하지 않는다.
- 10/2 Main 기동 준비는 별도의 닫힌 9/30 원천과 승인된 기존 정책을 사용한다. 현재 selected `c6453530`의 정식 준비·전체 verify는 PASS이며 실제 PREOPEN·Main PID·Widget·Episode 소비는 `FinalPolicyStartupAcceptance1002`가 확인한다. 장후 실패와 기동 준비 성공은 다른 수용이다.

## 코드 보완과 검증

기존 `CronCompletionDetector`에서 exact-source finalization의 최신 명시적 pre-cleanup FAIL과 cleanup run marker 부재를 함께 확인한다. 이 경우 cleanup은 `blocked_by_finalization` warning과 부모 reason/log/marker를 남기며 finalization FAIL은 유지한다. 다른 날짜·다른 job·알 수 없는 reason·실행 중 세대 변경·후속 recovery START·이미 실행한 cleanup의 원래 판정은 억제하지 않는다. 새 runtime module·cron·서비스·API 호출·정책 변경은 없다.

표적 검증은 cron detector 및 finalization/generation 회귀, Python compile, diff, 문서 print-only parser다. 실제 로그의 순수 detector 계산에서 summary는 finalization 실패 한 원인만 포함하고 cleanup 상태는 `blocked_by_finalization`이다. 원본 FAIL·미실행 cleanup evidence는 보존한다. full detector의 자동 복구나 Telegram 발송은 수동 호출하지 않는다.

최종 표적 회귀 **84 PASS / 3.48초**, compile·diff·audit 링크·print-only parser 통과. 설치 wrapper 시험이 실제 배포 lock을 사용해 별도 디스크 정리와 충돌한 기존 fixture 결함도 고쳤다. 시험의 PROJECT_DIR/runtime lock을 임시 경로로 격리하고 기존 cron stub·finalizer 보존 기대를 유지했다. 실제 lock 보유 작업을 중단하거나 우회하지 않았다.

이 수리는 감시 원인 분류의 종결이며 10/1 전체 장후 DONE을 의미하지 않는다. 10/1 계산의 closure는 복구 불가능한 원천 결손으로 blocked다. 새 유효 원천·정책 생성은 기존 10/2 기계/보조 POSTCLOSE owner가 확인하며, 과거 결손을 새 표본으로 소급 대체하지 않는다.

## 배포·장전 준비 종결

- 선택 release `cron-finalization-dependency-20261002-9dcbd482`, source commit `9dcbd482f0737e577ccf35b059ca17ab15d258e1`. 물리 root에서 표적 회귀 **84 PASS / 5.33초**. 이전 `c6453530`와 runtime source diff는 `error_detectors/cron_completion.py`뿐이며 매매·정책·bootstrap 코드는 동일하다.
- 첫 정식 prepare/verify는 삭제된 historical release 때문에 stage code 및 historical PREOPEN ownership을 확인하지 못해 FAIL이었다. 별도 디스크 정리의 삭제 명세·보존 Git ref와 원 stage SHA를 메모리 계산으로 대사해 필요한 세 root만 복원했다: `integrated-postclose-review-20261001-90c06298`, `postclose-final-audit-recovery-20261001-faf65ec6`, `machine-holdout-source-replay-20261001-c7cf32b1`. 각 원래 경로·Git SHA·clean source를 보존하며 현재 실행 release로 선택하지 않는다. 이 경로는 현재 장전/장후의 historical proof consumer가 필요로 하므로 단순 미선택이라는 이유로 삭제하면 안 된다. [복원 영수증](../../data/runtime/startup_readiness/2026-10-02/cron_finalization_dependency_transition/9dcbd482/historical_release_restoration.json).
- 복원 후 `next_preopen_readiness --prepare --source-date 2026-09-30 --target-date 2026-10-02`, `--verify --target-date 2026-10-02` 모두 PASS/결손 0. [현재 준비본](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json)의 env bytes·Main/compact policy receipts는 배포 직전과 같다. 원 source controller/summary bytes 불변을 확인했다. 실패한 최초 시도를 PASS로 수정하지 않았다.
- 07:10·07:15 정규 full detector가 새 root/commit을 실제 소비했다. 07:15 artifact freshness PASS, cron은 원 finalization FAIL만 보고하고 cleanup `blocked_by_finalization`과 부모 marker를 기록한다. 정규 health의 전체 severity는 원 실패 때문에 FAIL이며 GREEN으로 주장하지 않는다. [최종 readback](../../data/runtime/startup_readiness/2026-10-02/cron_finalization_dependency_transition/9dcbd482/readback.final.json).
- cron bytes/8 route 불변, release-set PASS, Episode 122 instance·366 policy pin 및 독립 Widget owner source pin 유지. 07:35 PREOPEN/07:55 Main start print-plan은 최신 selector다. 매매 서비스 재기동·예약 선행 실행·주문·API·정책 재계산은 없다. 실제 기동은 기존 `FinalPolicyStartupAcceptance1002`가 담당한다.
