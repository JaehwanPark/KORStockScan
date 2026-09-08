# Claude scalp pattern lab / Scalping pattern automation 소액 순이익 보완 리뷰

기준: 2026-09-08 KST. #67/#69 구현 요청에 따른 source-only 수정이며 장후 모니터링·실전 적용 실행 지시가 아니다.

## 판정

코드·연결 계약은 보완 종결, 자연 생성·실전 소비·경제성 수용은 OPEN이다. 목표는 비용 차감 후 작은 양수 순이익을 유효한 빈도로 반복하는 전략 연구다. 무조건 BUY, 고정 큰 수익률 floor, source-only의 실주문 권한 전환은 구현하지 않았다.

## 구현

| 결함 | 보완 | 경계 |
| --- | --- | --- |
| Claude만 ON인데 2개 lab 합의 요구 | 단일 활성 lab source-only 입력 허용; 후행 workorder의 solo 재보류도 해당 typed 기존-owner 전달에 한해 제거 | Gemini 복구·새 runtime 권한 없음 |
| 폐기 ADM/LDM 보고서·표본 부족 | retired/not_applicable, 복구 사유 0; 기존 generic AI ADM-only 응답도 exact interpretation/후속 사유 대사 후 종결 | 다른 active source gap이나 혼합 gap은 해제하지 않음 |
| 표시 profit_rate로 경제성 추정 | 기존 main paired v2 self-hash·global source contract·실제 terminal·비용 대사 재사용 | 과거 gross/zero 표시 복원값 배제, 슬리피지 이중 차감 금지 |
| 수익 패턴이 추천에 미연결 | rolling 동질 코호트의 이익과 손실을 모두 포함한 net/cadence 후속 연구 생성 | winner-only·승률만·고정 큰 수익률 floor 금지; 증분 EV는 기존 owner 평가 |
| 동일 날짜/코호트/선행조건 훼손 | 날짜-bound sequence join, 이미 결합한 flags 보존, 실제 full/partial 근거 없으면 unknown | normal entry_mode만으로 full fill 추정 금지 |
| NaN/Inf/boolean/누락 metric | 유효 손익에서 제외; funnel 미관측을 0으로 만들지 않음; empty CSV stale 잔류 제거 | 해당 행/날짜 격리, 정상 원천 유지 |
| rolling 표기와 누적 계산 불일치 | 일별·최근 10거래일·누적 및 profile별 코호트 분리 | 평가창별 원천 유효일·미관측일 공개 |
| 낡은 fallback/latency 및 허위 표본 대기 | 신규 추천 제거; 기존 canonical ledger는 보존; 진단 필드 구현과 전략 효과 분리 | lock/threshold/provider/매매 process 변경 없음 |
| 날짜만 최신인 구세대 artifact | run manifest의 EV/observability/source 3종 SHA256, 동일 bytes parse/hash, v3 target/권한 검사 | 실패 후 이전 파일을 새 정상 결과로 사용하지 않음 |

새 파일 `analysis/claude_scalping_pattern_lab/economic_evidence.py`는 기존 lab의 오프라인 분석 역할에 배치했다. `src/engine` root에 새 모듈을 추가하지 않았고 Kiwoom 요청/응답·주문 프로토콜을 수정하지 않았다.

## 계산·전달 계약

- 입력: `data/report/main_scalping_lifecycle_paired/main_scalping_lifecycle_paired_DATE.json`. 기존 producer가 매입/매도 총액 필드를 출력하는 코드 연결을 확인했다. 새 DB/API 호출이나 별도 비싼 producer를 추가하지 않는다.
- 경제성: 실제 매도금액 − 실제 매입금액 − 대사된 수수료·세금 = 순익. 금액가중 순EV, 평균 순수익률·분산 진단, 유효 원천일당 완료수·순익, 자금시간 효율을 분리한다. 자금시간 결손은 진단 null이며 새 공통 승인 floor가 아니다.
- 범위: main real submitted만; 미종결·부정확한 비용·중복 identity·다른 session/venue·source 오류는 제외. full-only/partial-only/partial-then-full과 scale-in 분리. profile 없는 코호트는 unversioned diagnostic이며 기존 score-recovery로 가장하지 않는다.
- 신규 `net cadence` 결과는 기존 score-recovery profile이 확인된 initial-only 코호트만 해당 family에 연결한다. 나머지는 계측/경제성 관찰이다. 동질 코호트의 손실도 함께 계산하며 `counterfactual_incremental_ev=null`은 기존 owner 검증 전 상태다.
- 전달: lab → automation → EV/workorder. source-only 전달 가능과 전략별 approval → PREOPEN → PID 소비는 별도다. 현재 두 lab은 여전히 `runtime_effect=false`, `allowed_runtime_apply=false`다.

## 리뷰·검증

- 1차 리뷰: 잘못된 full-fill 추정, 손실 flags 중복 merge, 숫자/빈 CSV, 비용 근거·평가창 결손을 수정했다.
- 2차 producer-to-consumer 회귀에서 workorder의 `solo → defer_evidence` 재차단을 검출하고 typed 기존-owner 연구 입력의 예외를 추가했다. unknown/권한 불명 후보의 일반 대기 조건은 유지한다.
- 격리 fixture에서 `분석 → payload/Markdown/manifest → automation → 실제 workorder 분류`를 실행했다. 순EV +0.002%의 작은 양수 사례도 연구로 전달되고, 음수·불완전 비용·중복·부분체결·권한 변조 사례를 구분한다. 같은 입력으로 두 번 재생성했을 때 추천과 작업지시가 같음을 확인한다. 이는 자연 거래·실수익 증거가 아니다.
- 최종 재리뷰: 날짜만 맞고 source generation이 바뀐 입력을 automation과 currentness consumer가 모두 차단하는 회귀를 추가했다. 표본 0건 자체는 generation 검증 실패 조건으로 사용하지 않는다. 검토 범위 내 미해결 finding은 0건이다.
- 검증: 관련 12개 테스트 모듈 627 passed; 변경 Python compile, 신규 분석/회귀 Ruff, 문서 print-only parser, `git diff --check` 통과. 동일 fixture 2회 재생성에서 추천/workorder fixed-point를 확인했다.
- 실제 canonical 보고서 재생성·provider 호출·매매 process 재기동·실전 env/lock 변경은 실행하지 않았다. 기존 설치 wrapper의 lab 호출과 `PYTHONPATH` 연결은 읽기 전용으로 확인했다. 다음 장후 자연 실행이 이 코드의 운영 산출물 검증 단계다.

## 기존 실제 자료 읽기 전용 확인

- 범위: clean baseline 6/5 ~ 9/7. 기존 canonical 파일을 수정하거나 다시 생성하지 않았다.
- 새 계약으로 self-hash/global source 검증된 원천은 8/25~9/7의 10거래일. 나머지 55개 기대 거래일은 missing/invalid source로 격리된다. 미래 관측을 막는 영구 all-history gate로 사용하지 않는다.
- 경제성 후보 0건. 기존 경제성·체결 조건을 통과한 과거 5개 행도 `entry_notional_krw` / `exit_amount_krw`가 없어 최종 대사에 사용할 수 없었다. 현재 producer의 해당 필드 출력은 존재하므로 다음 자연 generation에서 확인한다.
- 9/7의 과거 net +453 KRW 귀속 복원은 이번 보완의 신규 수익이 아니다. 스냅샷의 과거 301개 표시 완료 거래로 결손을 채우거나 gross/zero를 비용 검증값으로 바꾸지 않았다.

## 다음 자연 수용 owner

[9/8 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)의 `PatternLabSmallNetNaturalEvidence0908` 단일 OPEN owner에서 source → v3 generation → workorder 전달을 확인한다. 20개 유효 원천 거래일에도 owner-bound 양수 연구 코호트가 없으면 source/연결/통합·폐기를 재검토한다. 운영 lock 해제, 자동 매수, API 증설 또는 보고서 반복 생성으로 표본을 만들지 않는다.

`korstockscan-review-gate`에 따라 코드 종결과 자연/경제성 수용을 분리하고 외부 Project/Calendar sync 및 매매 process 조작을 실행하지 않았다.

## 커밋 전 독립 재리뷰·보완

2026-09-08 10:12 KST 기준, 병행 세션의 위젯 수정은 `c1bd9660`으로 main에 반영됐다. 이번 lab 변경은 그 commit을 기준으로 별도 worktree에 고정했다. 공유 작업폴더에서 동시에 수정 중이던 `src/engine/scalping/score_recovery_economics.py`는 이번 변경에 포함하지 않았다. 공유 폴더의 417 passed/1 failed는 해당 병행 모듈의 partial-loss veto 변경 때문에 발생했으며, 이 결과를 이번 고정 변경본의 통과 근거로 사용하지 않는다.

추가 발견한 두 결함을 수리했다.

- 날짜 열이 없는 sequence가 거래 ID만으로 full-fill 또는 손실 패턴 flag에 결합될 수 있었다. 준비 단계와 손실 진단의 fallback join 모두 거래 ID와 날짜를 요구하며, null/빈 key와 중복 key는 결합하지 않는다. 날짜 없는 입력은 unknown 상태를 유지한다.
- generic AI 리뷰에서 퇴역 ADM 이름의 substring만으로 mixed active-source 결함도 종결할 수 있었다. 관측된 ADM-only legacy 문장과 허용된 followup의 정확한 조합만 해결하고, 혼합/불명 원인은 남긴다.

신규 재현 테스트 3건이 수정 전에 실패했고 수정 뒤 통과했다. 날짜가 다르거나 null/빈 날짜인 손실 진단도 추가 검증했다. 고정 worktree의 lab prepare/economics/automation/currentness/AI review/propagation/workorder/EV/score-recovery 및 widget policy/receipt **11개 모듈 391 passed**. 기존 fixture의 2회 생성→automation→workorder fixed-point도 포함한다. 실제 Provider 호출이나 canonical 장후 report 재생성은 하지 않았다.

10:11 읽기 전용 process 확인에서 main PID `461794`는 09:27 시작 상태로 살아 있고 widget PID `21846`도 유지됐다. 이번 lab 수정은 장후 one-shot producer/consumer가 다음 정상 실행에서 읽는 코드다. 이미 반영된 위젯 변경도 blocked-policy 목록 직렬화 순서를 고정하는 변경이며 Entry membership/수량/target을 바꾸지 않는다. 이 변경을 소비시키기 위한 추가 매매 process 재기동은 필요하지 않다. 다음 자연 policy/receipt와 장후 generation은 기존 OPEN acceptance에서 확인한다. 코드 배포를 현재 PID 소비나 경제성 성공으로 판정하지 않는다.

최종 게이트: 고정 변경본의 Python 12개 compile/Black/Ruff E9/F63/F7/F82, 문서 print-only parser, `git diff --check` PASS. 별도 기존 canary pin 테스트도 27 passed이며 frozen 측정값을 변경하지 않았다. 이번 고정 범위의 unresolved finding은 0이다. 이후 공유 폴더에 추가된 owner policy-search/maintenance/AI summary 변경은 병행 세션의 미완료 변경으로 보존하고 이 커밋의 검증 결과에 합산하지 않는다.
