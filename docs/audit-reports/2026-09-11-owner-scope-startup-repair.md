# 9/11 07:32 소유권 정책 실패 수리와 삼성 기동 차단 원인

사용자 요청: 정상매도 원장 처리 여부 확인, 07:32 소유권 정책 적용 실패 결함 보완, 삼성 `manual_operator_exclusion_missing` 도입 주체 확인. 관찰 기준 2026-09-11 08:13 KST. 장후 모니터링 실행이 아니다.

## 판정과 수리

`code_review_closed / deployment_pending`. 격리 worktree `/home/ubuntu/KORStockScan-runtime-releases/review-owner-scope-20260911`, branch `fix/owner-scope-20260911`, commit `f6fa0f9e40c2da4e9e6aa667ea418cd4f584a8d4`에 수리를 완료했다. 운영 workspace/선택 release의 코드·공유 설정·원장·정책·프로세스는 변경하지 않았다.

- 최초 오류: 07:32:00 `symbol_owner_auto_apply_owner_or_machine_scope_mismatch:108320`. LX세미콘은 신규 profile 및 `symbol_owner_policy_standing_authority_2026-09-11.json`에 있지만 `manual_control_excluded_codes.txt`의 표시와 `manual_control_exclusion.py`의 정확한 라벨 등록이 모두 누락됐다. 기존 installer에는 LX 등록이 있으나 00:20 개별 배포에서 broad installer를 실행하지 않았고, parser 등록도 빠져 있어 행만 추가하는 수리로는 충분하지 않다.
- 격리 수리: `108320 # machine_owner_scope lx_semicon_low_price_two_leg_owner` 설정 행과 parser 라벨을 함께 추가했다. 실제 승인 파일과 전체 표시 파일을 `_validate_runtime_scope`로 대사하는 회귀 검증을 추가했다. 기존 labels census 테스트도 9/11 등록 범위를 반영했다.
- current/legacy 표시 인식, 누락·잘못된 표시 차단, 별도 명시적 manual operator veto 보존을 확인했다. 당일 authority의 종목/owner 목록, 수량, entry/exit 조건, 주문 guard와 적용 시간은 바꾸지 않았다.
- 검증: owner auto-apply·manual exclusion·9/11 추천 승인 관련 targeted pytest 85 PASS, 수리와 무관한 연구 증거/전략 전환 테스트 5개 제외. compile 및 `git diff --check` PASS. producer의 실제 scope 검사, marker consumer, 삼성의 기존 정책 소비 경로, 시간·process quiescence guard를 재리뷰했고 이 수리 범위의 미해결 finding 0이다. 운영 재발행/실제 PID 소비는 미검증이다.

## 정상매도 원장과 삼성 차단 설명

SK텔레콤 SELL `0022607`은 공통 `order_owner_registry.jsonl`에 9/10 14:35:09.392728 `FILL_RECORDED` filled10, 14:35:09.619771 `ORDER_TERMINAL` filled10으로 정상 반영됐다. 시각은 원장 관찰시각이다. 반면 `low_price_two_leg/sk_telecom_morning_state.json`은 trade_date9/10, HELD/position10으로 남았다. 공통 원장 완료와 에피소드 미정리를 구분한다. 이번 요청의 1번은 처리 여부 확인이며 상태 수정은 하지 않았다. 상세 원인은 [전일 체결 대사](2026-09-10-intraday-monitoring-1510.md#새-결함-sk텔레콤-목표-체결-후-에피소드-held-잔존)를 따른다. 이미 기록된 매도를 다시 기록하지 않는다.

삼성 `manual_operator_exclusion_missing`은 오늘 누군가 등록한 제외 항목이 아니라 preflight의 오류명이다. `git blame`상 8/11 10:49:01 커밋 `dac516494` (`add samsung morning one-share service`), Git author `JaehwanPark`가 최초 조건을 추가했다. Git author만으로 당시 실제 조작자가 사용자/에이전트인지 단정하지 않는다. 현재 `_episode_ownership_source`는 `independent_machine_ownership_source`를 통해 exact-date 정책/activation을 검증한다. 이름만 보고 수동 제외를 새로 추가하면 올바른 수리가 아니다.

08:13 읽기 전용 확인에서 main PID14564와 삼성 preflight PID15182 모두 `KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE`이 전일9/10 파일이다. 당일 발행 실패 후 전일 경로를 소비한 상태이며 삼성의 main PID/runtime verification은 PASS지만 ownership source는 비어 있다. 삼성 매매 PID0, preflight bounded wait(09:25 deadline), widget PID15604 active다. 실행 중이라는 사실은 신규 진입 성공을 뜻하지 않는다.

## 검토된 적용 범위와 남은 권한

기존 자동 적용은 07:32~07:54, 적용기의 필수 조건은 매매 프로세스 quiescence다. 현재 시간으로 원 wrapper를 반복하거나 과거 시각을 주입해 우회하지 않는다. 수리 commit의 marker parser를 실제 common main/기계 소비 코드에 반영하고 공유 marker를 함께 설치해야 한다. source 한 줄만 운영에 덧붙이거나 이전 PID가 새 코드를 읽는다고 가정하지 않는다.

오늘 즉시 복구의 별도 승인 대상은 해당 수리의 고정 배포, 현재 main/위젯 및 관련 사전검사·기계 process의 상태/미체결 보존 후 안전한 중지·재기동, 9/11 한정 시간 외 소유권 정책 복구다. 기존 지속 standing authority의 07:54 시간과 주문 안전조건을 임의 완화하지 않는다. 승인 후에는 fresh broker/registry를 대사해 기존 허용 subset만 발행하고, 부적격 custody는 그대로 skip하며 새 PID의 당일 policy/activation 소비까지 검증해야 한다. 오늘 신규1주 및 기존 custody/target/정책 pin은 유지한다.

rollback은 새 activation 이후 주문/owner 변화부터 재대사하고, 이전 정책·코드·설정 백업을 보존한다. 살아 있는 주문이나 새 원장을 전일 상태로 되돌리지 않는다. SK텔레콤 에피소드 정리는 별도 exact-original-target 반영 범위이며 이 배포로 완료됐다고 보고하지 않는다. 후속은 현재 체크리스트 `MachineProfitStagnationStartupAcceptance0911`에 연결한다.
