# 10/15 장전 최종화·정책 생성 검증 경보 수리

05:51:38 경보의 source는2026-10-14, target은2026-10-15다. 원 선택본은 `e74ec5c56`이며 Main은 정지 상태다. 이 기록은 코드 검증·실제 준비 복구·후속 배포와 예약 기동을 구분한다.

## 원인과 수리

- 최종화는05:43:41에 새 controller를 발행했으나 준비 단계의 고정120초 제한으로 실패했다. cleanup 종료→실패는120.315초이며 원 직접 준비 성공은178.140초였다. wrapper가 원 exit code를 버렸으므로 과거 exit124가 직접 기록됐다고 주장하지 않는다. [원인 대사](../../tmp/sentinel-integrated-postclose-20261014/prepared-contract-alert-055138-readonly-diagnosis.json)를 보존한다.
- 예약 wrapper는 기존 작업본의 미배포 수정에서 양의 정수 `POSTCLOSE_FINALIZATION_PREPARE_TIMEOUT_SEC` 기본600초를 가져오고, 기존06:50 마감에 따른 budget cap·kill grace10초·실패 detector·wrapper exit1을 유지한다. 이제 실제 준비 자식의 exit code도 로그에 남긴다. 이는 준비 검증 시간이며 AI 신호5초·보고서130/40/180초 예산 변경이 아니다.
- 보조 평가의 코드 세대는 선택본과 일치했지만 해당 세대의 fixture 검증 영수증이 없어 `policy_generation_unverified`는 정당했다. 별도의 현재 운영 정책이 verified라는 이유로 checklist 생성기가 capability warning을 누락한 것이 `UNRESOLVED_CURRENT_OWNER`의 원인이다. [정확 경보·원천](../../tmp/sentinel-integrated-postclose-20261014/auxiliary-generation-alert-20261015T055138-review.json)을 보존한다.
- checklist owner는 기존 capability OWNERS와 source/code/contract 세대에서 직접 투영한다. 경제성 repair와 같은 ID이면 증거를 합치고, 기존 PREOPEN 작업·manual OPEN·이력·권한을 유지한다. 이번 자동 경고의 provenance marker만 조건부 갱신에 사용하며 verified 전환에서 낡은 자동 경고를 제거한다.

## 검증과 실제 실행 경계

wrapper25개와 checklist84개 표적 시험이 PASS했고, 독립 리뷰의 미해결 지적은0이다. compile·bash 문법·diff 검사도 PASS다. [wrapper 검증](../../tmp/sentinel-integrated-postclose-20261014/finalization-wrapper-600s-source-validation-20261015.json), [checklist 독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/checklist-generation-independent-review-20261015.json)에 코드 해시를 결속한다.

실제 e74 정상 prepare를600초 외부 한도로 실행해06:45:52에178.616초/exit0으로 복구했다. 현재 정책·후보·selector·controller·summary·checklist·원 준비·평가 bytes는 그대로이고 새 c737 controller 세대의 준비 영수증을 발행했다. [실제 실행](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/prepare-execution.json)의 새로운 readiness SHA는 `1cf11dd039ae493ba4bd19e228592cefd98df3cc14ce3a4e56a3f989e6ccada0`다. 별도 full verify도06:48:21에 `current_full_contract`/findings 없음으로 통과했다. 최종화 terminal은 별도로 확인한다. 원05:51 실패를 성공으로 덮어쓰지 않는다.

보조 검증 경보는 기존 표적 fixture 검증→native evaluate를 사용해 닫는다. 원50쌍·100요청·예산·응답·resolution 내용과 기존 immutable 평가·정책/C15를 보존하고 provider·정책 재선정은 실행하지 않는다. [기존 경로 리뷰](../../tmp/sentinel-integrated-postclose-20261014/auxiliary-generation-existing-native-closure-review.json)에 재실행 범위와 원천 대사를 기록한다. 실제 완료는 별도 영수증으로 확인하며 이후 필요한 summary/checklist/controller/prepared만 재결속한다.

새 코드의 배포·준비·정규07:35 PREOPEN/07:55 Main PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다. 현재 코드 검증을 배포 또는 기동 성공으로 표시하지 않는다. 원천 누락·미성숙 경제성은 null/원 상태로 보존한다.
