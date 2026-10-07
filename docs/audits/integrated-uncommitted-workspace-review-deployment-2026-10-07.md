# 전체 미커밋 작업본 통합 리뷰·배포 — 2026-10-07

사용자는 전체 미커밋 변경의 코드리뷰·보완·통합 배포·재기동을 승인했고, 후속 질문에 **기존 미커밋 변경 리뷰·보완·통합 배포**로 범위를 확정했다. 새 Main 다중 정책·삼성 상승 눌림 계획과 추가 raw 삭제 계획은 문서로 포함한다. 신규 분기 구현·정책 발행이나 추가 원천 삭제를 실행하는 권한으로 확대하지 않는다.

## 작업본과 배포본 대조

기준 workspace HEAD는 `8f0e8fd80dcd9450b3a2cbacc60296bbc7f279a5`, 기존 선택 릴리스는 `fixed-watch-submit-source-20261007-v2`/`7aa0f1e2a1ea367f3b5b1d492aedcfcb5c131db5`, Main PID는 `815021`이다. [검토 시작 inventory](../../tmp/integrated-uncommitted-review-20261007/workspace-before.json)에 46개 변경/삭제/신규 경로의 SHA와 상태를 동결했다.

- 현재 배포된 `src`/`deploy`/`restart.sh` 1,305개 파일은 작업본 파일 bytes와 전부 일치한다. untracked였던 반전 진단 모듈·고정감시 회귀도 실제 파일로 대조했다. Git의 추적 여부 때문에 생기는 diff의 가상 삭제를 실제 누락으로 오판하지 않는다. [대조 결과](../../tmp/integrated-uncommitted-review-20261007/deployed-source-parity.json).
- HPSP 고정감시 증빙·TTL 재평가·WS 수신 시계·주성 거래량 진단 수리는 앞선 실제 배포와 같다. [선행 리뷰](main-fixed-watch-submit-and-volume-source-repair-review-2026-10-07.md)의 불변 릴리스 1,773 PASS 및 실제 PID/주성 비율 소비 근거는 그 당시 기록으로 보존한다. 이번 실행에서 같은 1,773개를 다시 돌렸다고 합산하지 않는다.
- 운영자 제외 종목 파일은 두산 설명 comment만 바뀌었고 실제 code 목록은 동일하다. 옛 모델 backup·퇴역 정책/보고서 원천의 10개 tracked 삭제는 이미 존재하던 삭제 상태를 통합하며, 현재 정책/모델/수량/custody 보존 hash를 대조했다. 과거 원본을 checkout으로 재유입하지 않는다.
- 연구 결과·추가 삭제·다중 정책 계획은 evidence/proposal 구분을 유지한다. 신규·변경 문구의 로컬 링크 1,205개 모두 존재한다. 변경하지 않은 역사 문서의 이미 삭제된 옛 근거를 복원하거나 현재 실행 owner로 되살리지 않는다.
- `data/source_quality/file_source_retirement.apply.lock`는 실행 중 공유하는 잠금 inode이므로 삭제하지 않고 정확 경로를 `.gitignore`에 추가해 커밋에서 제외한다.

## 추가 발견·보완

1. **FD 관측 결손:** 삭제 CLI가 접근 거부 PID를 경고에만 남기고 다른 프로세스의 open 여부를 모른 채 삭제/검증 성공을 기록할 수 있었다. census가 불완전하면 해당 실행은 `fd_census_incomplete`로 보류하고 삭제하지 않는다. 기본 dry-run도 verified로 표시하지 않는다.
2. **삭제 후 durability 실패:** `unlink` 성공 뒤 directory `fsync` 실패를 `skipped`/삭제 0으로 기록하던 결함을 수정했다. 실제 삭제 수량을 유지하고 `deleted_durability_unconfirmed`·`post_delete_errors`를 남기며 후속 삭제를 중단하고 남은 미처리 수량을 기록하며 CLI는 exit 1을 반환한다. 이를 재실행 가능한 미삭제 파일로 위장하지 않는다.
3. **manifest 증거 교체:** 검증한 내용과 이후 summary 해시에 사용한 파일이 서로 다른 세대일 수 있었다. 최초 읽은 동일 bytes를 파싱·내용 seal 검증·summary SHA에 사용한다.

수정 전 추가 회귀 4개는 모두 실패했고 기존 17개는 PASS했다. 수정 후 삭제 CLI 21개 PASS, CLI exit-code 회귀까지 보완한 최종 21개도 PASS했다. 새 삭제는 pytest 임시 디렉터리에서만 수행했다. 운영의 과거 sealed 삭제 journal/manifest는 그대로 보존한다.

## 검토·검증과 권한

삭제 CLI·릴리스 라우터·장중 handoff·모듈 위치·문서 파서 관련 **213개 PASS**. compile·wrapper `bash -n`·`git diff --check`와 print-only parser를 확인한다. 기존 실행 코드의 bytes가 동일해 키움 protocol parser를 새로 수정하지 않았다. 선행 WS 변경의 공식 upstream SHA/문서 증거는 선행 리뷰에 남아 있다.

기계/보조 12셀·연구 kernel/보조 계약·AI TTL/CAUTION·운영자 veto·주문/수량/자본/custody guard를 변경하지 않는다. current checklist·EOD·기존 정책/PREOPEN을 다시 발행하지 않는다. 단발 삭제 CLI는 cron·봇·장후 호출과 연결되지 않아 예약 자동화/정책 문서의 실행 규칙을 변경하지 않는다.

최종 불변 릴리스 검증을 통과한 동일 작업본을 커밋·통합 배포하고, 기존 native intraday handoff와 정상 재기동으로 현재 PID 소비를 검증한다. 새 전략 적용·주문·체결·승률 개선은 이 코드 통합의 완료 조건 또는 결과로 주장하지 않는다. 배포·PID·자연 수신·남은 경고는 아래 실제 완료 증거에 기록한다.
