# 장후작업 현행 활성 목록

## 현행 Main-only 계약

자동 주문 owner는 Main이다. 에피소드·위젯과 독립 IPO 자동실행은 영구 퇴역한다. 과거 체결 잔여는 사용자 수동관리하며 전용 exit/cancel/알림/연구/PREOPEN을 요구하지 않는다. 공통 journal/DB, Main 원천·정책 부모·보호조건은 보존한다. 다음 영업일 실행 owner와 수용은 [체크리스트](../checklists/2026-10-19-stage2-todo-checklist.md), 원칙은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md)를 따른다.

| stage | producer / dependency |
| --- | --- |
| main_machine_policy | Main registered reversal research/publisher |
| legacy_machine_report | Main compatibility report |
| outcome_labels | Main outcome labels |
| main_auxiliary_policy | Main machine policy; pre-cutover labels/report compatibility |
| pre_submit_delay | Main source-only timing research |
| main_stop_confirmation | source date 2026-10-12 이후 기존 conditional stage; native Main stop 원천·검증된 parent carry/독립 연구 |
| summary_handoff | summary/tower/checklist/strict/controller |

공통 cron은 runtime selector로 EOD 20:05, postclose/controller/tuning 20:10, archive 20:50, finalization 05:35, PREOPEN 07:35, Main start 07:55를 실행한다. 삼성 frozen validation은 기존 Main wrapper의 선택적 report-only sidecar이며 정책 발행·startup gate가 아니다. 전용 episode final-refresh/auto-apply/fill notifier/확장 timer와 IPO cron은 제거한다. 10/8 이전 sealed stage 원 바이트는 과거 최종화 검증에 필요한 최소 증거로만 보존하며 새 stage나 미래 복구 owner를 만들지 않는다.

실행 근거와 삭제/배포 영수증은 [구현 검토](../audits/main-only-widget-episode-full-retirement-implementation-review-2026-10-08.md)에 기록한다. 과거 구성은 Git 이력이며 현행 설치 명령으로 사용하지 않는다.

## 10/11 구조 보완 작업트리

[장후 구조 구현 검토](../audits/postclose-structural-policy-completion-implementation-review-2026-10-11.md)는 cancel의 역사 경제/현재 custody, TP1 수량·자본, auxiliary 정산/비교, 숫자 EXIT vote, native capability/semantic/intake와 퇴역 writer를 보완한다. 자동화의 실제 현재 소비 코드는 runtime selector가 고른 release다. 이 작업트리 수정과 fixture receipt는 selected/PID/자연 정책 생성 증거가 아니다.

WS/lookup attention은 기존 native WS freshness report의 integrated selection과 compact generation projection으로 확인한다. 퇴역 ADM/LDM·aggregate workorder·Opening/PYRAMID publisher를 다시 만들지 않는다. `code_improvement_workorder`의 구형 요구는 selected code의 실제 cutover 근거와 대사하며, 기존 정책·summary/strict/controller의 필수 산출물은 유지한다. native policy-generation capability는 report-only이고 새 startup gate가 아니다.

프리마켓의 NXT-only 원천/주문 경로는 별도 진단할 수 있다. 정규장과 애프터장 정책 분석은 통합시장 scope를 유지하며 실제 체결시장과 원천 route는 별도 축으로 기록한다. 같은 판단·시도를 KRX/NXT 두 정책 모집단에 중복 계산하지 않는다. 통합 원천 불명은 source-gap이다.

Main market-weakness 야간 wrapper는 기존 advisory research이며 장중 취소/주문 또는 retired episode 정책을 발행하지 않는다. 숫자 EXIT 연구는 Main holding/stop의 기존 owner 안에서 원 요청·실험 계약을 소비한다. 원천/실험 결손은 incumbent carry와 명시적 gap이며 무조건 새 정책 생성을 요구하지 않는다.

퇴역 compatibility CLI는 역사 문서의 실제 명령과 forensic reader를 이행할 때까지 inert 상태로 보존한다. 해당 명령/reader 이전 후 제거하며 현행 cron·unit에서 실행 기능을 부활시키지 않는다. 이번 변경으로 cron·unit 설치, bot 재기동, selected release 또는 봉인 PREOPEN 변경을 실행하지 않는다.


## 등록 stage 밖의 활성 생산자와 마지막 소비자

위 stage 표는 dispatcher 단위다. summary의 direct source 수나 controller DONE만으로 아래 기존 작업의 의미 검증을 생략하지 않는다. 실제 예약·wrapper 분기·OFF/optional을 함께 대조하고 원천 읽기 수, 식별 가능한 제외, 소비 모수, 경제 적격, 선택/승계를 각각 남긴다. 날짜별 수치·결함·재생성 영수증은 [전체 장후 점검](../audits/postclose-complete-semantic-repair-2026-10-17.md)이 소유한다.

| 작업군 | 기존 생산자 / 마지막 소비자 | 필수 구분 |
| --- | --- | --- |
| EOD·source quality | update_kospi, observation_source_quality_audit → 날짜별 raw exclusion / 장후 preflight | 원 대상·eligible·짧은 이력 제외·격리 행·latest DB date |
| 공통 경제 원천·종목원장 | machine economic reference → canonical symbol master → WS/lookup·holding | 저장된 당일 master payload와 별도 발행 파일, 원 공식 metadata의 hash/date/종류 |
| 공식 비용·거래 fact | broker_cost_source → canonical trade snapshot → strategy_position fact sync | 공식 수집 성공과 포지션별 실제 비용 배분, 원 census run/projection/cost의 동일 세대 |
| 최초 매수 수량 | initial_quantity_policy refresh → evaluation/stage → summary/checklist | fact 전체·COMPLETED·원천 제외·경제 적격·기존 정책 PID·전용 bundle 관측; source gap은 valid-empty가 아님 |
| 수량 후행 관측 | 기존 observation queue의 cap capture → lifecycle receipt / 후보 horizon join | queued와 durable, horizon 완료와 조기 청산·재기동 중단, 원 PID/attempt/plan; 짧은 후보와 미관측 긴 구간 |
| cancel·entry split·scale-in | 각각 기존 family producer → typed policy / native consumer | 실제 제출/고유 parent/leg/잔여·terminal·Main/manual custody·유효 empty·경제 결손 |
| WS·lookup attention | intraday_ws_freshness finalize → integrated selection / compact generation | 당일 공식 master 결속·paired source·resource/filled/terminal; 진단 완료와 경제 선정 |
| 마감 snapshot·holding·trailing | postclose_exit snapshot → all-scope trailing → Main stop / bootstrap | 원 snapshot과 all-scope 연구의 code/date/window/세대, 원래 정책 carry와 새 경제적 우월성 |
| 상승누락·시장상황·입력 진단 | rising feedback/classifier, market panic breadth, verbosity/microstructure·prompt/input 진단 | raw exclusion 이후의 동일 원천, 모집단/분모, active/report-only/retired consumer |
| tuning·Parquet | 기존 build/shadowdiff/latency/system metric/report 작업 → wrapper terminal | 날짜 제외·정확한 중복·구조/원문 식별 충돌·소비 행 보존, 비교 불일치의 실패 전파 |
| 보관·최종화·오류 탐지 | 기존 archive/cleanup → native controller/finalizer → 독립 full detector | 압축의 논리 원문 세대·보호 증거·원 실패 보존, 최종화 자체 대기와 독립 완료 검사 |
| 선택적 야간 연구 | Main market weakness / optional frozen validation → advisory receipts | 실제 수행·deferred·마지막 완료·원천 결손; 필수 Main 기동 계약과 구분 |

공식 비용 수집 뒤 정식 `postclose_exit`의 completion prefix 세 종류를 한 번 봉인하고, fact sync는 `--completion-snapshot`으로 같은 원천의 작은 native projection을 소비한다. 수량 평가 뒤 마지막 AI 입력 작성이 끝나면 holding suffix만 생성해 네 종류의 최종 manifest를 봉인한다. 이후 holding/stop은 이 세대를 재사용한다. 이후 snapshot을 다시 생성하면 fact와 수량도 그 원천부터 다시 결속한다. 임시로 재구성한 보고서를 정식 snapshot의 census로 표시하지 않는다. 복구 reuse는 원 hash/비용 계약과 현재 trailing code/target 계약을 모두 확인한다.

비영업일 기본 full detector도 마지막 완료 원천일의 수량 평가를 확인한다. 정책이 소비됐거나 평가가 carry_parent라는 사실은 원천·경제성의 결손을 해소하지 않는다. 기존 최초 정책에 새로운 경제성·전 horizon·자연 표본 승인을 소급 요구하지 않는다.

Parquet 원천 영수증도 정상 raw→gzip 전환을 소비해야 한다. 원 decoded 바이트의 SHA/크기는 생성 스트림에서 한 번 봉인하고, 새 압축은 producer가 CRC 왕복 검증한 정확한 archive 세대를 작은 metadata로 인계한다. 상이 원문·영수증 없는 새 alias·세대 변경은 실패로 남기며 원 영수증을 재작성하지 않는다. health의 bounded 관측과 장후 생산자/최종 native 재평가를 구분하고 동일 호출의 검증 결과만 재사용한다.
