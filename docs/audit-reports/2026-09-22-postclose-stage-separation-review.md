# 2026-09-22 기계정책 추가 리뷰·장후 stage 분리

사용자 승인 범위: 기계판정 코드리뷰·수정, 장후 실행기 분리 구현·반복 리뷰, 커밋·푸시·배포. 기존 장중 기계정책 generation의 선정 기준과 AI/주문/보유·청산 튜닝 범위는 확대하지 않았다.

## 변경과 리뷰

| 발견한 문제 | 수정·검증 |
| --- | --- |
| 0인 spread/depth ratio 후보가 replay 검증을 통과하고 실제 실행 검증에서 거절됨 | 기존 strategy validator에서 두 실행 임계치의 양수 조건을 일치시킴. 활성 정책 값·승률 우선/음수 EV 허용 기준 유지 |
| 통합 refresh의 collector 실패가 다른 분석/발행을 취소함 | 기존 summary owner의 stage registry·독립 dispatch·exit 집계로 변경 |
| source 대기·과도한 child 병렬화 및 중복 AI follower 계산 | stage별 lock/PID start identity, 두 compute slot, 선행 대기 별도, follower는 receipt 확인만 수행 |
| family 발행과 공동 allocation이 서로 연구/정책을 덮어씀 | 자기 family 완료 입력만 읽는 발행과 allocation-only writer 분리 |
| 라벨 부분 파일/날짜/코드·원천 교체 뒤 stale 성공 재사용 | atomic 라벨·committed receipt·KST 시각 및 input/output/prerequisite/code hash 확인, 변경 시 실패·하류 deferred |
| 개별 seal만 맞는 main report/terminal 불일치 | report SHA와 policy SHA 상호 결속 확인 |
| 중단 뒤 child 잔존·빠르게 종료한 PID의 stat 경합 | signal cancellation·process group 종료·저장 checkpoint 보존, 종료 PID race 처리 |
| summary 자기 hash 순환·과거 bootstrap PASS의 준비 완료 오판 | summary self hash 제외, 전체 완료/정책 준비 분리, native bootstrap 재검증+각 loader 확인 |

새 engine-root 모듈·daemon·DB는 만들지 않았다. `postclose_summary_handoff`, `machine_research_closed_loop_refresh`, controller/summary와 기존4개 wrapper를 수정했다. 타 작업의 widget/episode 시장 데이터·주문 수정 및 테스트 변경은 이 커밋에서 제외한다.

## 검증과 실제 재개

- 관련458tests PASS; 이후 보완한 중단·최종 handoff 경로94tests PASS. 별도 중단 테스트에서 child 종료와 저장 checkpoint 보존을 확인했다.
- `tmp/postclose-stage-separation-20260922/review-validation.log`, `handoff-final-tests.log`, `recovery/receipt.json`에 근거를 보존했다.
- 9/21 완료 payload39,349,135bytes 및 라벨351,502bytes 복사본에서 partial label 실패 → collector deferred → 완료 라벨 재검증 성공 → collector 실제1회 성공·issues0. main/AI 학습0회, 원본 전일 DONE/원 정책 변경 없음.
- 원 정책 pointer SHA256 전후 동일: `b940a42a3568ba387af1cc78295bd8eebf9c96d8870ac70e0452dbbaa2450ff7`. 경제성/새 threshold를 만들기 위한 재계산이 아니라 분리 실행기의 source barrier·실패 단계 재개 검증이다.
- 미변경 heavy grid/provider/order 테스트는 실행하지 않았다. 당일 장후 source는 아직 완료되지 않았으므로 오늘 정기 전체 stage DONE이나9/23 자연 PREOPEN 성공을 주장하지 않는다.

## 배포·자연 실행 경계

검증된 immutable release와 유효 router/systemd binding을 아래에 기록한다. 진행 중인 매매 PID에 배포 사실을 소급하지 않는다. 현재 기계정책은 `a552d63ac3c3c33b310ee7ea6cdb6b7528b5ce3905dae601a7008f498c14137d`이며 앞선 M1–M6 자연 소비 근거는 [기계정책 리뷰](2026-09-22-main-machine-policy-repair-review.md)에 있다.

오늘 정기 source_date9/22 terminal·9/23 loader/부트스트랩의 자연 확인은 [현재 checklist](../checklists/2026-09-22-stage2-todo-checklist.md)의 `PostcloseStageRunnerSeparation`에 유지한다. 이는 구현 검증과 구별되는 미래 운영 관측이다.

## 배포본 검증 및 예약 경로 보완

- 1차 코드 `97fcd5463` push, 독립 배포본451tests PASS. 완료 source 복사본의 실제 재개도 release cwd에서 성공했다. 검증 fixture는 strict source reader 계약에 맞게 공유 data의 실경로를 사용했다.
- 10:25 유효 두 장후 unit의 WorkingDirectory/ExecStart와 공통 cron postclose/finalize router를 새 배포본으로 확인했다. 검증 영수증: `tmp/postclose-stage-separation-20260922/deployment-verification.json`.
- 마지막 예약 분기 리뷰에서 OFF machine/AI stage의 불필요 scoped verification을 제거하고 pending/running/deferred follower 확인을 exit75로 반환하도록 보완했다. 추가98tests PASS. 이 수정까지 포함한 최종 코드 `90c5cbad3`을 push/배포했고10:28:50 두 unit과 postclose/finalize router의 동일 release를 확인했다. 최종 배포본 추가98tests도 PASS다. 상세는 동일 deployment 영수증에 갱신했다.
- 현재 매매 PID60693은 `main-machine-20260922-3a79e240f/src`에서 유지한다. 새 배포는 정기 장후 코드에 적용되었으며 현재 PID가 새 source를 소비했다고 표시하지 않았다. 기존 정책 bundle의 새 loader 검증 PASS, 원 정책 변경 없음.
