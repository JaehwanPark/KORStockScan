# 2026-09-29 전체 워크스페이스·5슬롯 프로브 통합 배포 리뷰

## 선택과 범위

- 정규 워크스페이스의 당시 미커밋 49개 추적 파일과 코드·문서 미추적 11개를 `8ee3f76d`에 봉인하고, 현재 선택 릴리스 `bbde9aa7`와 5슬롯 수리 `7c849df0` 위에 병합했다. 리뷰 수리 후 Main/source commit은 `11435b62497843153a0142c32e0ab657f16c10b1`이다. 9/28 원천 재구축 전 요약 백업 2개는 데이터 원천 대사용으로 보존했으며 실행 소스에 포함하지 않았다.
- 이 범위는 정규 워크스페이스의 전체 변경이다. 별도 8/15 AI 경제성 작업트리, 9/17 장후 작업트리, 9/28 구 릴리스 4개의 고유 미커밋 소스는 현재 계약과 충돌하거나 선택 릴리스 밖의 별도 계보다. 이번 실거래 릴리스에 혼합하지 않고 보존했다. 삭제 대상으로 간주하지 않는다.
- 공식 키움 WebSocket 계약 조회 근거는 [5슬롯 수리 리뷰](2026-09-29-zero-base-probe-five-slot-observation-review.md)의 upstream commit `953e5dbff123f437ab4d11a78a95191a685eb51f`/점검 경로다. 5개와 10·15초는 키움이 공시한 상한이 아니라 로컬 관측 예산이다.

## 리뷰와 검증

- 제로베이스/WS/장후 원천 연결 655개와 나머지 변경 소유 모듈 2,159개, 합계 **2,814개 테스트 PASS**. EOD gate로 이동한 source wait 테스트를 현 계약에 맞게 수정했고, 기계 평가 계약 결손의 식별 가능 행·ID 진단 필드를 구현해 불일치를 해소했다. 영향 Python 18개 compile, wrapper `bash -n`, `git diff --check`, 문서 print-only parser 26개 항목 PASS.
- 배포 전 `--check-release-set` PASS. 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/integrated-whole-workspace-probe5-20260929-11435b62`의 `src/deploy/restart.sh`가 커밋과 일치하고 공유 `data/logs/tmp/.venv/docs/restart.flag` 경로가 정규 워크스페이스와 일치한다.
- 첫 PID `1313551`에서 이전 선택 릴리스에도 있었던 sparse 릴리스 포장 결손 `configs/scalp_micro_reversion_canary_guard.toml`을 발견했다. 해당 커밋의 tracked `configs`를 새 릴리스에 복원하고 정상 절차로 재기동했다. 최종 Main PID `1316234`의 `/proc` cwd는 새 릴리스 `src`, 선택 영수증의 `actual_pid_consumed=true`, 정책 bootstrap 검증 PASS다. 재기동 후 같은 설정 파일 결손 로그는 확인되지 않았다.
- widget evaluation·machine microstructure final refresh의 비활성 서비스 두 개는 같은 릴리스 코드로 systemd pin을 교체했다. 두 timer는 active이며 서비스를 수동 실행하지 않았다. 독립 widget trader/low-price/episode owner는 기존 `30e66ae5` 커밋을 유지하고 릴리스 집합 점검은 PASS다. cron 필수 8경로 라우팅 PASS.

## 첫 자연 정규장 관측과 다음 판정

- 12:57~13:04 KST 로그에서 `zero_base_probe` REG 104개, 대응 REMOVE 99개, 관측된 동시 임시 등록 최대 5개, 활성 등록 중 동일 코드 재REG 0개였다. 대응 구독의 REG→REMOVE 최소는 로그의 초 단위로 10초, 중앙값 15초이며 10초 미만은 0개였다. 이는 프로브 구독만 센 값이며 별도 감시·보유·source-only WS 총량이 아니다.
- 같은 창의 파이프라인 프로브 결과 108개 중 기계판정 `assessed` 38개(35.2%), `source_unavailable` 52개, `required_feature_insufficient` 13개, `policy_unavailable` 5개였다. `route_snapshot_missing`은 20개다. 이전 12:05~12:12 창의 383개 중 57개(14.9%) 기계판정·220개 route 결손과 모수·시간대·후보 구성이 달라 인과적 개선이나 수익 개선으로 단정하지 않는다.
- 감시 편입 영수증은 이 관측창에 1개였다. 정규장 한 창만으로 감시 상한을 늘리지 않는다. 프리마켓·통합 애프터마켓의 자연 REG→수신→REMOVE, 동시 슬롯, 판정/결손 비율과 감시 점유율, loop 지연·REST/WS 압력을 같은 창으로 대조해야 한다. 주문·체결·비용 후 경제성은 별도 수용이다.
- 12:59의 source-only `kt00011` 읽기 timeout 1건과 13:01~13:03의 I/O wait 경보(최대 67.19%)는 남아 있다. 이 창에는 이 리뷰의 대용량 파일 검사도 겹쳤으므로 프로브 수리만의 자원 효과로 귀속하지 않는다. 감시 상한 증설 전 독립적인 동일 창 압력 재측정이 필요하다.

## 정리와 보존

- 고유 소스 변경이 없고 실행 PID가 점유하지 않는 중복 임시 작업트리 11개를 제거했다. Main 정규 워크스페이스는 통합 커밋으로 정리됐으며 원천 요약 백업 2개만 미추적 상태로 보존한다.
- 기존 릴리스 삭제 후보를 commit 선조 관계, source 변경, 선택 백업, systemd pin, 문서 경로와 실행 PID로 점검했다. 구 장후 릴리스 4개에는 고유 미커밋 source 변경이 남아 있고 다른 후보는 운영·rollback·감사 참조 또는 독립 계보가 있으므로 릴리스 디렉터리는 삭제하지 않았다. 현재 릴리스와 직전 `bbde9aa7`, 독립 machine `30e66ae5`는 운영 보호 대상이다.
- 선택 전 manifest 백업은 `tmp/integrated-whole-workspace-selection-before-20260929T125513.json`이다. 롤백은 이 선택 백업과 직전 릴리스·정책/계좌 상태를 다시 검증한 뒤 별도 전환으로 수행해야 한다.
