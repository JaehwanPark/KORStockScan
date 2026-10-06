# 위젯 전체 제거 실행·반복 리뷰

기준: 2026-10-06 KST. Owner: `WidgetFullRetirement1006`.

## 결정 및 권한

사용자가 전체 제거계획 실행과 반복 코드리뷰를 승인했다. 서버의 위젯 자동/수동 주문, 화면/API, 수집·알림·연구·발행, 장후/감시/배분 연결을 제거하고 Main·에피소드 공통 기능을 분리한다. Windows는 설치되어 있으며 운영자가 직접 제거할 예정이다. 새 매수·매도·취소 주문이나 custody 재분류는 실행하지 않았다.

## 소유권 종결

신규 BUY 전송 전 차단 후 `2026-10-06T08:22:29.175890+09:00` broker 완전조회에서 KRX/NXT 잔고, 미체결, 당일 주문이 정상 빈 결과였다. 원장의 과거 cancel 2건은 원 주문번호·종목·수량과 `취소확인`을 대조해 terminal을 append했다. 위젯 15개 position의 잔여 수량과 active intent는 0이다. 공통 원장은 보존했다.

증거: [대사](../../tmp/widget-retirement-execution-20261006/broker-after-freeze.json), [과거 취소 종결](../../tmp/widget-retirement-execution-20261006/legacy-order-reconcile.json), [custody](../../tmp/widget-retirement-execution-20261006/custody-terminal.json).

## 구현 및 리뷰에서 보완한 결함

- 위젯 전용 모듈·Windows 배포 소스·web blueprint·unit·장후 stage·owner/배분 분기를 제거했다. 공통 비용은 `src/trading/market/comparison_cost.py`, 에피소드 집계는 `src/engine/monitoring/episode_source_research.py`로 이관했다. 비용·수량·Main 삼성 고정 감시·에피소드 격리와 hard safety를 유지한다.
- 역사 owner context는 읽을 수 있으나 새 widget 주문 reserve/정책 선택은 거부한다. 과거 정책의 widget 문자열이 에피소드 로더와 검증을 깨뜨리지 않도록 역사 계약과 신규 권한을 분리했다.
- 장후 stage schema를 v3으로 바꾸고, producer의 attempt archive·wrapper PID·종료 검증을 유지했다. 새 날짜의 v2 PASS는 재사용하지 않는다. 정책 발행의 source generation, dependency hash, publication hash를 검증한다.
- 위젯 collector가 기록하던 공통 episode fact는 기존 Main 비동기 WS 저장 worker로 이관했다. 받은 데이터를 기록하며 추가 구독/API는 하지 않는다. 새 Main PID의 자연 소비는 별도 인계 대상이다.
- 공통 약세 guard 환경변수 이름만 변경한다. 설치값을 그대로 보존하며 위젯 제거에 따른 guard 해제·수량/cap 증가를 허용하지 않는다.
- 삭제 모듈 import, 기존 widget-positive fixture, 동적 장후 경로, 원천/정책 hash 훼손, 옛 릴리스의 widget 복원, web 인증키/drop-in 잔재를 반복 점검했다. 에피소드 수를 61개로 고정한 테스트는 고정 입력과 미래 unit 조회 금지 검사로 보완했다.

## 공식 API 근거

상류 `Kiwoom-Securities/Kiwoom-REST-API` SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`를 `2026-10-06T08:17:28.947634+09:00`에 조회했다. REST/WS specs/core, realtime REG/REMOVE/FID, 잔고·미체결·주문조회, Postman을 대조했다. `kiwoom_docs` 부재는 근거 receipt에 명시했다. 프로토콜을 추측해 바꾸거나 실제 주문을 실행하지 않았다. [조회 receipt](../../tmp/widget-retirement-execution-20261006/official-reference-receipt.json).

## 검증 및 제한

최종 대상 회귀는 **3,382 PASS · 기존 skip 1건**이다(78개 파일). Python 124개 compile/F821, 변경 shell `bash -n`, diff 검증을 통과했다. 초기 실패를 수정하고 최종 회귀를 다시 실행했다.

- [회귀](../../tmp/widget-retirement-execution-20261006/regression-closure.log), [후속 검증](../../tmp/widget-retirement-execution-20261006/final-supplemental.log), [컴파일·lint](../../tmp/widget-retirement-execution-20261006/compile-and-lint-final.json), [삭제 import census](../../tmp/widget-retirement-execution-20261006/deleted-import-census.json).
- 프로젝트 전체 pytest collection의 기존 PYRAMID import 오류와 변경 범위 밖 F821 3건은 이번 수정과 구분한다. 변경 Python의 F821와 대상 compile/bash/diff 검증은 통과했다. 대상 회귀의 기존 skip 1건은 유지한다. 데이터 정리 후 공통 비용·장후·publication/retirement 회귀 132건도 통과했다. [정리 후 검증](../../tmp/widget-retirement-execution-20261006/post-cleanup-validation.log).
- 전용 service/timer 11개는 중지·삭제·mask했다. Main/에피소드 매매 프로세스는 이 제거 작업에서 재기동하지 않는다. 신규 선택 릴리스와 설치 경로는 다음 자연 기동용이며 현재 PID 소비와 구분한다.
- 위젯 전용 원천은 archive 내용·파일별 SHA/size와 open FD를 확인한 후 운영 경로에서 제거한다. Main이 사용하는 과거 가격 관측·주문 이벤트, 공통 custody, 에피소드 fact, 혼합 역사 admission/cohort/cost receipt는 보존한다.

## Gate 및 다음 행동

| Gate | 현황 | 종료 증거 |
|---|---|---|
| G0 | 통과 | fresh broker·원 custody 종결 |
| G1 | 서버 설치·API·신규 owner/dispatch 제거 검증 통과 | 전용 unit/dispatch 0, API 404, 새 owner 거부 |
| G2 | 새 코드 계약·대상 회귀 통과; 자연 장후 대기 | 새 날짜 v3 stage/필수 원천에 widget 없음 |
| G3 | 공통 기능 회귀 및 import 검증 | Main·에피소드 비용/WS/수량/custody/guard 보존 |
| G4 | 서버 archive·삭제 완료; 외부 제거 대기 | Windows 직접 제거 후 운영자 확인 |
| G5 | `natural_acceptance_pending` | 10/6 자연 장후 및 다음 Main/에피소드 기동·소비 receipt |

G4 외부와 G5 자연 증거가 남아 있으므로 전체 제거의 최종 완료를 선언하지 않는다. 다른 family의 기존 source gap·격리는 해당 owner가 관리하며 위젯 복원 또는 임의 활성화로 해결하지 않는다.

## 최종 배포·정리 receipt

- 코드 커밋: `b53a3835c90ebfc31812117688b836edb4250b85`. 선택 릴리스: `widget-retired-20261006-b53a3835`. 설치 경로 13개를 반영했으며 Main·에피소드 재기동은 하지 않았다. 웹은 새 릴리스로 재기동했고 실제 PID cwd를 대조했다. source archive와 기존 작업본 patch를 보존했다.
- 전용 unit/timer 11개 모두 mask/inactive/PID 0. 설치된 widget 실행·의존 참조 0. 옛 혼합 widget/episode drop-in 25개는 보관 후 제거했으며, 공통 설정의 effective environment·cwd·실행/조건 명령은 제거 전후 동일하다. 위젯 인증키/drop-in 3파일과 옛 timer/stamp 6개도 제거했다. mask와 영구 거부 설정은 재복원 방지용이다.
- 에피소드 unit 122개의 새 릴리스 경로 및 정책 pin 366개 검증 통과. 상태 목록의 과거 failed 39개를 현재 기능 실패 39개로 해석하지 않는다. 이 receipt는 `functional_runtime_health=not_assessed`, Main PID `not_attested`다. 현재 Main·에피소드 PID가 새 코드를 소비했다는 증거는 아니다.
- 공통 episode fact producer는 새 Main의 기존 WS 저장 worker에서 소비된다. 현재 Main은 재기동하지 않았으므로 이 producer 전환의 자연 소비도 G5 대기다. 기존 episode 자체 원천과 공유 raw를 유지하며 즉시 소비를 주장하지 않는다.
- root 화면 200. 실제 과거 `/api/widget/samsung-price`, `/api/widget/samsung-order`(POST), `/api/widget/doosan-price`, `/api/widget/hanwha-ocean-price`는 모두 404. 공통 `dostk` API는 위젯 전용 API로 오인해 삭제하지 않았다.
- 전용 운영/연구 데이터 **2,668파일 · 550,620,404바이트**와 임시 전환 릴리스의 **2,589파일 · 106,597,771바이트**를 archive 내용/해시 확인 후 삭제했다. 삭제 직전 open reference 0. 정리 실행 전후 free space 증가 **669,908,992바이트(약 639MiB)**. archive·새 릴리스 생성 전후를 포함한 전체 세션 증가와는 구분한다. 삭제 source의 bytecode 16개도 정리했다.
- 가격 관측 4종, 과거 widget 주문 이벤트, 공통 order-owner 원장, episode fact, 혼합 역사 admission/cohort/cost receipt 31개는 살아 있는 소비/추적을 위해 유지했다. 과거 ID/schema의 위젯 문자열은 새 owner/주문/정책 권한이 아니다.
- 위젯 데이터 제거 후 **10/6 Main dated/effective 및 에피소드 적용 정책 로더 통과**. 에피소드 61개 정책과 격리 3개를 유지한다. 10/7 Main effective incumbent는 로드되며 exact dated/에피소드 정책은 아직 미발행이다. 오늘 자연 장후/PREOPEN 생성이 필요한 상태이며 새 정책 발행·정상 기동 완료로 표시하지 않는다.

[배포](../../tmp/widget-retirement-execution-20261006/deployment-final.json), [설치 검증](../../tmp/widget-retirement-execution-20261006/installed-retirement-final.json), [릴리스·policy pin](../../tmp/widget-retirement-execution-20261006/release-set-final.json), [웹](../../tmp/widget-retirement-execution-20261006/web-final.json), [공통 설정 보존](../../tmp/widget-retirement-execution-20261006/obsolete-dropin-cleanup.json), [삭제 manifest](../../tmp/widget-retirement-execution-20261006/storage-cleanup-final.json), [실제 정책 로더](../../tmp/widget-retirement-execution-20261006/surviving-policy-loaders-final.json), [장후 route](../../tmp/widget-retirement-execution-20261006/postclose-route-final.json), [cron](../../tmp/widget-retirement-execution-20261006/cron-final.json).
