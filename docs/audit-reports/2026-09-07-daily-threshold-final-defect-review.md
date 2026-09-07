# Daily threshold 최종 결함 보완

## 판정과 경계

Daily threshold 중앙 통합/장전 handoff는 유지한다. 이번 구현은 사용자 최종 리뷰에서 확인된 source 격리, 표본 순환 의존, 기간/조건 진단, AI 입력 상한과 성능 검증의 결함을 보완한다. 기존 운영 lock·실전 env·수량·주문·provider 경로·매매 프로세스는 변경하지 않는다.

실행 중인 9/7 main wrapper PID 895257의 코드를 교체하지 않도록 `/tmp/korstockscan-daily-review.82BXBN`에서 수정·검증했다. 운영 경로 반영 여부는 아래 종결 기록으로 별도 판단한다. 이 보고서는 장후 전체 정상 종료 또는 수익개선 판정이 아니다.

## 보완 내용

| 결함 | 보완 | 확인 기준 |
|---|---|---|
| 일부 과거 partition 오류가 모든 후보 차단 | 검토된 producer dependency와 실제 primary window/daily 입력으로 격리. 독립 owner의 유효 후보 보존. 미식별·잘못된 실패 상세는 fail-closed. gzip EOF 오류도 읽기 실패로 기록 | 과거 holding 오류/Entry split·entry price·독립 pyramid 영향 분리, 같은 family의 유효 window 오류는 차단 |
| 적용된 probe만 표본으로 인정 | 기존 WAIT collector에 ON/OFF와 독립적인 당시 설정/hash·시장 구간·상승/반등·가격 관측을 추가. 60~64 관측 누락 보완. 신규 관측 계약이 있으면 invalid 관측을 applied marker로 우회하지 않음 | 미적용 exact 관측의 CF 표본 가능, applied와 unapplied 계수 분리, 당시 가격만 사용, 실제 BUY/action 변경 없음 |
| 달력 5일을 표본 5일처럼 사용 | rolling 5/10/20을 기존 KRX 거래일 도우미로 구성. daily 운영 window와 clean baseline은 유지 | 주말·휴일 제외, 9/7 rolling 5는 9/1·2·3·4·7 |
| 비용 completeness 분모의 경계 사례 | 빈 날 제외 계약을 재검증하고, candidate count 없이 경제성 sample count만 있는 날도 비용 계약 분모에 포함. 중복 비용 판정 로직 제거 | empty+valid 창은 PASS, positive-count missing-cost는 FAIL |
| 2% 절대 EV 문턱의 타당성을 입증하지 않고 무한 대기 | `condition_feasibility`로 근거 결손·양수지만 절대 floor 미달·절대 EV floor 도달·비양수 EV를 구분하고 다음 행동 명시 | 양수 0.5%를 no-edge로 오인하지 않음. 이 진단은 runtime authority 없음 |
| AI hard cap 표시와 실제 payload 불일치 | 후보 identity/decision 보존 후 긴 설명을 hash로 축약. 여전히 초과하면 provider·key 조회 전 차단하고 coverage repair도 우회 호출하지 않음 | 30개 Unicode 후보 보존/120,000자 이내; 초과 입력 OpenAI/Gemini 모두 호출 0 |
| 축약 계측과 정규 CLI의 입력 범위 혼동 | `--benchmark-inputs-only` 추가. 동일 CLI의 daily/직접 calibration merge/정규 누적 source loader/DB/window/context까지 실행하고 저장·provider 직전에 반환 | 실제 source loader 사용/DB skip=false/저장·Provider 호출 0 회귀 |

새 순수 관측 모듈은 `src/engine/scalping/score_recovery_observation.py`다. live 관측과 장후/PREOPEN이 공유하는 계약이며 engine root에 새 모듈을 만들지 않았다. 새 회귀는 `src/tests/test_daily_threshold_final_review.py`가 소유한다.

## 조건 재설계와 경제성 수용

표본 20, 비용 차감 CF EV 2%, close 1%, MFE 조건과 제출 drought의 기존 실전 gate를 임의로 낮추지 않았다. 이번에 정정한 것은 관측 분모·거래일 window·오류 전파·판정 진단이다. 새로운 분포 근거 없이 2%를 다른 숫자로 바꾸는 것은 수익개선 검증이 아니다. `positive_edge_below_absolute_floor`가 실제 새 자료에서 관측되면 같은 cohort의 증분 net EV/불확실성/정책 적용 범위를 근거로 절대 문턱의 대체 또는 제거를 결정한다. 이 정량 재설계는 완료로 주장하지 않는다.

당시 설정·시장 구간 hash가 다른 관측을 공통 runtime 승인 근거로 합치지 않는다. source-only CF는 실제 full/partial 체결 품질이나 realized net profit의 대체 근거가 아니다. 새로운 관측 계약은 해당 코드가 로드되는 다음 정상 매매 process 시작 이후 생성되므로, 9/7 과거 snapshot에 해당 필드가 없다는 이유로 기존 운영 lock을 풀거나 장후 전체 실패로 처리하지 않는다.

## 성능 및 회귀

- 9/4 정규 CLI 동일 입력 계측: **46.438초, process 최대 RSS 378.09 MiB**, DB 조회 포함, cumulative/rolling 5·10·20 source window 모두 포함.
- AI context 32,061자, 현재 apply/AI review 후보 각각 0, Provider 호출 0, report 저장 0. production 경로 쓰기 차단 audit hook을 둔 별도 process에서 실행했다.
- 이전 9.9초·274MB는 정규 CLI 전체 경로 개선의 확정 근거로 사용하지 않는다. 이번 수치 역시 서버 부하에 따른 단일 실행 계측이며 SLA 또는 실제 수익개선을 보장하지 않는다.
- 10-file 확장 회귀 **2,051 PASS**. 최초 임시 작업본의 누락된 analysis wrapper로 1 FAIL이 있었으며, 동일 원본 fixture를 복사한 뒤 같은 전체 범위를 재검증했다. 코드 수정으로 실패를 숨기지 않았다.
- 운영 작업 트리 1차 **2,053 PASS** 후 비용 sample-only 분모의 중복 판정 제거와 당시 가격의 event→candidate 문자열 전달 회귀를 보강했다. 최종 같은 10-file 통합 검증은 **2,055 PASS / 63.05초**다. Black 6파일·Ruff 관련 3파일·compile 6파일·`git diff --check`와 print-only 문서 parser가 PASS했다. 전체 저장소의 무관한 테스트나 Provider 호출은 수행하지 않았다.
- final-review 경계 사례, producer→consumer→PREOPEN, 기존 wrapper/verifier/EV/registry 및 live collector 관련 회귀를 검토했다. 추가 종결 결과는 아래에 기록한다.

## 종결 기록

- 운영 경로 반영: 9/7 21:47 KST 완료. 원 main PID 895257이 21:44:45 verifier 실패로 종료되고 관련 동일-code producer가 실행 중이지 않음을 확인한 뒤, 원본 snapshot 일치 검사 후 변경분만 반영했다. 최종 통합 검증 및 producer/consumer/PREOPEN 권한 재리뷰를 닫았으며 이번 코드 보완 범위의 미해결 finding은 0이다. 절대 문턱의 정량 재설계·자연 경제성 수용까지 완료했다는 뜻은 아니다.
- 별도 운영 상태: 원 main의 실패 및 controller `blocked_recoverable_action_failed`는 이번 코드 반영 전 실행 결과다. 이 작업은 해당 운영 체인을 재실행하거나 정상화한 것이 아니며 장후 전체 GREEN을 선언하지 않는다.
- 자연 generation/PREOPEN/PID/실수익: 기존 `DailyThresholdNaturalAcceptance0908` owner에서 각각 확인한다. 코드/테스트 PASS로 이 acceptance를 닫지 않는다.
- 별도 매매 프로세스 재기동, env/lock 변경, 운영 report 재생성, commit/push는 실행하지 않았다.
