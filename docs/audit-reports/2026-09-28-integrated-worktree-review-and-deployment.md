# 2026-09-28 통합 작업본 리뷰와 배포 영수증

## 범위와 결정

2026-09-28 15:30 KST 기준 등록된 worktree 79곳의 `src`, `deploy`, `restart.sh` 변경과 실경로 `docs` 변경을 조사했다. 현재 작업공간과 별도 미완료 worktree 3곳에 소스 수정이 있었다. 릴리스 후보는 현재 Main 선택본 `71caed8458c1a98c5f1b655de2c64b9be38a824a` 위에 현재 작업공간의 차이 23개 소스 파일, 1개 체크리스트, 18개 새 문서를 정확 복사해 만들었다. 선택본에 이미 포함된 작업공간의 미추적 소스·테스트 9개는 내용이 같아 한 번만 포함했다. 별도 worktree 원본은 그대로 보존한다.

| 별도 작업본 | 변경 | 함께 검토한 결과 | 통합 판정 |
| --- | --- | --- | --- |
| `/home/ubuntu/KORStockScan-ai-quality-economic` (`c4eafffd`, 8/15) | micro-reversion 경제 원천/제공자 예산 4개 소스·테스트와 8/14 체크리스트 | raw fee/tax/master 및 가격 schema를 v2→v3로 올리고 공식 URL·원본 byte 증거를 강제한다. 현재 v2 원천과 migration/capture 없이 합치면 연구 입력이 일괄 차단된다. Main 주문 권한은 없고 당일 릴리스 소비 근거도 없다. | 원본 보존, 별도 소스 계약·자료 준비 후 재검토. 오늘 Main 릴리스에 미포함. |
| `/home/ubuntu/KORStockScan-worktrees/exploration-lifecycle-20260911` (`badfb232`, 9/11) | entry split/scale-in guard 4개 소스·테스트 | probe target/기존 holding 보호와 분할 계획 변경 대부분은 현재 소스에 이미 반영됐다. `can_consider_scale_in`의 exploration identity 독립 차단은 현재 소스의 명시적 소유권 회귀와 충돌한다. 현행은 활성 probe 생명주기만 차단한다. | 구형 추가매수 차단은 적용하지 않음. 원본 보존. |
| `/home/ubuntu/KORStockScan-worktrees/postclose-stepwise-20260917` (`f204ab79`, 9/17) | 장후 source quality/replay/pyramid 등 27개 소스·테스트 | source generation 검사는 현재 소스에 이미 반영. 나머지 고유 변경에는 NXT 전용 `_NX` BBO 재생, null 경제 지표, 장후 경로 alias, 구형 Main handler provenance가 섞여 있다. 9/28 통합 `_AL`/SOR 후보 계약과 현재 장후 소비자를 기준으로 별도 쌍대 재생·계약 검증이 필요하다. | 9/17 장후 연구 원본은 보존하고 당일 거래 Main 릴리스에 미포함. 완료나 실패로 분류하지 않음. |

현재 작업공간의 다른 세션 변경에는 보유청산 census 봉인, 저가 2-leg/물타기 분할과 경제성, pre-submit 원천 lineage, pipeline event 재기동 drain, trade review, scanner Main 편입 테스트가 포함됐다. 릴리스 후보는 이 변경 전체를 포함한다. 이들은 출처 누락·부분체결·실제 비용을 0 또는 실현 수익으로 채우지 않으며 주문·제공자·정책 임계치를 늘리지 않는다.

## 코드리뷰와 검증

- 9/11 탐색 identity 추가매수 차단을 시험 적용했으나 현행 회귀 5건과 충돌했다. 현행 계약은 탐색 표지만으로 물타기 차단 권한을 만들지 않는다. 시험 변경을 되돌리고 활성 probe 생명주기 차단과 보유 중 restriction 보존만 유지했다.
- 기존 AI 감사 테스트 1건은 가짜 제공자 호출에 전송 증거가 없는데 `computed_not_sent`를 요구했다. 실제 v3 전송 영수증은 `not_attempted`이며, 가짜 호출로 전송 완료를 꾸미지 않도록 기대값을 수정했다.
- 릴리스 worktree의 `data` 심볼릭 링크를 no-follow strict JSONL 독자가 거부해 장후 테스트 2건이 실패했다. `strategy_position_performance_report`의 신뢰된 DATA_DIR 루트만 해석하도록 수정해 릴리스 작업본에서도 두 테스트가 통과했다. 하위 원천의 no-follow 검증은 유지했다.
- 첫 통합 후보 영향 테스트 2,041건 통과·3건 실패를 원인별로 격리했다. 구형 추가매수 guard 시험에서는 2,043건 통과·5건 실패했으므로 되돌렸다. 이후 AI 감사 기대, DATA_DIR 루트, 백그라운드 로그 등록과 경합하는 테스트 fixture 순회를 수정했다. 같은 관리 릴리스 작업본에서 최종 영향 회귀 **2,044건 통과**(95초), Python compile, `bash -n`, `git diff --check`, 문서 print-only parser를 통과했다. pandas-ta 경고 1건은 기능 실패가 아니다.
- Kiwoom 요청·응답 parser/REG/REMOVE/주문 protocol 변경은 이번 통합 차이에 없다. 스캐너 `_AL`/SOR 및 WS 대기 변경은 선행 리뷰의 공식 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`와 15:11 KST 확인을 따른다. 추가매수 guard는 주문 허가를 좁힐 뿐 broker 요청을 바꾸지 않는다.

## 릴리스·런타임 수용 단계

통합 커밋, 불변 릴리스 선택, 실제 PID/cwd/env, 당일 정책 handoff, 자연 발견→판정→제출, broker 체결·terminal, 실제 비용 후 성과는 서로 다른 영수증으로 기록한다. 아직 자연 제출/체결 및 비용 후 경제성은 확인되지 않았다. 퇴역 전용 `53854ced`는 rollback으로 유지한다. 다른 systemd/cron이 사용하는 릴리스와 세 별도 dirty worktree는 삭제하지 않는다.
