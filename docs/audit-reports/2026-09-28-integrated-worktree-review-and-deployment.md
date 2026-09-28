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

## 15:44 KST 통합 커밋·선택·재기동

- 통합 커밋 `d8aa4a646f81917ef4a39b72c3eebbc4d7ee686b`를 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/integrated-all-work-20260928-d8aa4a64`에 생성하고 작업공간 `main`을 동일 커밋에 맞췄다. 기존 `main`의 `8e8def53` 위치는 `backup/main-before-integrated-20260928` 브랜치로 보존했다. 작업공간의 `src/docs/deploy/restart.sh`는 clean이며 릴리스의 런타임 소스도 clean이다.
- 선택 전 포인터 백업은 `tmp/integrated-selection-before-deploy-20260928T154342.json`이다. 정상 재기동으로 Main PID `688047`을 얻었고 PID cwd=`/home/ubuntu/KORStockScan-runtime-releases/integrated-all-work-20260928-d8aa4a64/src`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`, `KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true`를 확인했다. 당일 정책 handoff는 15:43:51 KST PASS, release-set은 selected Main PID 결속 PASS 및 별도 systemd 소유자 124개 대사 PASS다. release-set의 `functional_runtime_health`는 `not_assessed`이므로 경제성이나 장후 기능 완료로 해석하지 않는다.
- 실제 사용 경로 참조와 source clean을 확인한 뒤 중간 스캐너 릴리스 `scanner-retirement-20260928-review`, `scanner-zero-base-20260928-review`, `diagnostics`, `fairness`, `sourcegap`, `wswait` 6개만 제거했다. 현행 `d8aa4a64`, 직전 `71caed84`, 퇴역 전용 `53854ced`, 별도 systemd가 사용하는 `30e66ae5`, 다른 세션의 세 dirty worktree는 보존했다.
- 재기동은 선택/PID/정책 영수증을 닫는다. 새 PID의 다음 자연 매수창에서 정확 `_AL` 입력·기계 action·WATCHING 편입·제출/체결을 대사하고, terminal과 실제 비용 후 순익을 별도 수용해야 한다.

## 다른 세션의 커밋된 작업본 전수 대사

릴리스 6개 정리 후 등록 worktree는 74개다. 현재 `main`의 조상 또는 동일 HEAD가 53개, 독립 이력 HEAD가 21개다. 조상 53개는 이력상 통합돼 있다. 독립 21개의 `src/deploy/restart.sh` 변경 파일과 현재 소스에 남은 추가 줄을 대조했다. 이는 **소스 존재·차이의 전수 점검**이며 각 독립 연구의 경제성·실제 PID 소비를 새로 승인하는 리뷰가 아니다.

- `1218e485` 당일 full-workspace 이력은 추가 실질 소스 줄 1,097개 중 1,093개가 현재 소스에 남았다. 차이 4개는 이후 비용 영수증 분기에서 바뀐 표현이다. 9/28 당일 별도 운영 서비스가 쓰는 `30e66ae5`는 현재 `main`의 조상이며 계속 보존했다.
- 9/26 holding-profit 두 릴리스(`d71b10e8`, `4ab3491d`)는 각 5,369/5,372개 실질 추가 줄 중 현재에 없는 줄이 57개로 동일하다. 9/25 trailing 두 릴리스(`6060f5d0`, `6c82414c`)에는 각각 59/91개의 현재에 없는 줄이 있다. 이들은 이전 정책·보고 계약이므로 현행 exit 소유권/임계치와 병합하지 않고 원본·롤백 이력을 보존했다. `eebdd3cd`와 `e61b5b05`의 실질 추가 줄은 현재에 모두 남아 있다.
- 9/23–9/24 postclose 분기 11개는 각 0–91개 현재에 없는 실질 추가 줄이 있으며, 주로 finalizer 순서·policy helper·direct summary·semantic contract와 다음 체크리스트 생성기다. `postclose-whole-recovery-20260924-v3` 등 별도 자동화 참조가 남아 있어 정리 대상에서 제외했다. 이 분기의 고유 변경은 현재 장후 체인과 owner·날짜별 strict 영수증을 대조하는 별도 변경이 필요하며 Main 거래 릴리스에 자동 병합하지 않았다.
- `53854ced` 퇴역 전용 릴리스는 현재 소스에 없는 실질 추가 줄이 0개지만 VCP/S15가 다시 켜지지 않는 복구 지점이므로 보존했다. 9/24 trailing-lineage 작업본의 HEAD는 런타임 소스 고유 차이 0개이며 작업본 관리 기록으로 보존했다.

독립 커밋의 고유 줄은 누락 기능의 증명이 아니다. 운영 역할, source 계약, 현행 테스트의 소유권이 달라질 수 있으므로 오늘의 통합 커밋은 검증된 당일 작업공간과 스캐너 릴리스를 기준으로 한다. 세 개의 dirty worktree 및 21개 독립 이력 작업본을 지우거나 현행 Main의 진입·청산 권한으로 승격하지 않았다.
