# 최종 연구 통합·P5 사전 로딩·P6 배포 검토 — 2026-10-18

현재 상태: **현재 범위 연구 종결·지정9d 통합958d35b2b·최초 P5·P6 발행/호스트 current_full_contract·최종 선택 세대 P5까지 PASS다. 원 P5 실패4회와 P6 실패01/02를 보존했다. 실제 Main 기동·PID 소비는 하지 않았고10/19 PREOPEN/PID는 기존 owner가 유지한다.**

## 승인과 기존 연구 결과

사용자는 연구 종료 후 `9d2201141aeae409fe960ff7795a1340718a7146`에 최종 연구를 통합하고 P5 사전 로딩을 실행한 뒤 통과하면 P6 배포를 이어가도록 지시했다. 기존 별도 지시 대기는 이 승인으로 해제됐다. 실행 소유자는 [10/18 MainPolicyLoadAndExitValidation1018](../checklists/2026-10-18-stage2-todo-checklist.md), 최신 계획은 [보완안 §12](../proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md#12-최종-연구-통합과-p5p6-실행-승인)이다.

[손절 연구 종결](main-stop-remaining-research-closure-review-2026-10-18.md)과 [보유 연구 종결](../proposals/main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#17-2026-10-18-현재-원천-범위-연구-종결)의 현재 원천·등록 가설 범위 결론을 유지한다. 원 손절 세대의3072 frame 정책 비교는 CPU +7.91%/허용5% 초과로 blocked였고 신규 수치 정책 발행0이다. 이를 이번 통합 코드의 성능 PASS나 grace0 정책 승인으로 재사용하지 않는다. 보유 엄격 비용5와 별도 terminal 참고8의 분모·비용 시계·권한은 분리한다.

## 통합 범위와 검토

지정9d에는 로딩 검증590fccd70과 보유57a4659f4 선행6commit이 이미 포함돼 있다. 별도 worktree `/home/ubuntu/KORStockScan-worktrees/main-research-policy-deploy-20261018`에서 stop `eb8e18cefacad23a298fd237093732e0f0977d70`과 엄격 비용 `3ab6916e28ee3301402c6ac8b64fbc2090f49000`을 merge해 원 계보를 보존했다. holding-vote 모델의 유일 충돌은 canonical 비용 시각 helper를 보존하고 순환 import를 제거했다. 실제 Main 반복문은 stop 최종 AST를 유지하며 공통 startup loader와 trailing 연구 link를 함께 보존했다. 통합 runtime·holding 경로의 독립 읽기 검토 지적은0이었다.

새 손절 inventory의 기존17→44 확장과 보유22→23 확장과 native key/full path 차이는 원 정책 digest를 보존하는 정확한 코드 인계에서 검증해야 한다. 기존 정책·보고서·원 code-handoff의 해시를 고쳐 쓰거나 새 파일을 검증에서 제외하지 않는다. 최종 clean code·확정 회귀·실제 P5 영수증이 이 검토를 닫는다.

## 실행 경계와 보존

실행일10/18·원천10/16·대상10/19를 분리한다. 착수 selector는900234d79이며 Main·supervisor와 systemd MainPID는 없다. 비거래일 Main 강제 기동을 하지 않는다. 기존 selector·준비 index/readiness·env/manifest/verify·summary/controller·손절 원 정책9개807988bytes를 [원문 백업 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/original-operating-inputs-01.json)에 별도로 보존했다.

P5는 selector 이동 전 실제 준비 세대로12consumer를 OS 격리 child에서 로딩하고 종료·부작용 차단·원천 불변을 확인한다. P6는 필요한 native code/quantity/capability 세대와 동일 정책·128scope·두 PRE overlay를 검증하고 CoW 준비를 마친 뒤 잠금·CAS 아래 selector를 마지막에 발행한다. 실제10/19 PREOPEN·운영 PID·자연 terminal/손익은 기존 DirectFamilyPreopenPolicyHandoff가 소유하며 사전 child의 actual_pid_consumed는 false다. provider·계좌/주문·패키지·원 정책값·Main/manual custody·hard safety 권한은 이번 코드 배포로 변경하지 않는다.

## 통합에서 발견한 결함과 보완

통합 검증의 첫 시도는 **218 PASS/5 FAIL**에서 중단됐다. 실패는 최신 파일을 과거 holding 허용 쌍으로 비교하던 시험 fixture의 세대 혼용이었다. 과거 `9d2201141`의 실제 Git bytes와 당시 5쌍·2개 의존성, 현재 통합본의 실제 bytes와 확장 의존성을 각각 검증하도록 fixture를 분리했으며, 원 허용 목록과 정책 digest를 완화하지 않았다. [attempt-01 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/integrated-validation-attempt-01/validation.json)과 실패 로그는 보존한다.

두 번째 시도의 **4,829 PASS/20 FAIL**은 별도의 실제 공통 자원 결함이었다. 공유 예산이 `-3,158,152`바이트가 되어 1,024바이트 admission 제한을 우회했고, 후속 holding·경로 진단 시험에 같은 음수 상태가 전파됐다. 수량 연구 보고서의 `ResidentFacts`/`ResidentPaths`를 `deepcopy()`할 때 내부 `Claim.size`가 추가 예약 없이 복제되어 원본과 복제본이 각각 해제하는 원인을 특정했다. 최소 native 2시험에서도 수정 전 **1 PASS/1 FAIL**을 재현했으며, 별도 추적의 첫 underflow는 `-301,000`바이트였다. 이는 fixture의 과거 코드 기대와 구분되는 실제 생산자·소비자 소유권 결함이다. [attempt-02 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/integrated-validation-attempt-02/validation.json), [수정 전 최소 재현](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/budget-native-reproduction-before.log).

복제 Claim은 기존 lock 안에서 독립 예약을 획득하고, resident 컨테이너는 공유 memo/partition 관계를 보존하면서 이미 예약한 행을 다시 청구하지 않도록 수리했다. 복제 실패·overflow에서는 새로 취득한 예약만 반납하고 원 소유권을 유지하며, process-local Claim의 pickle 전송은 거부한다. 수량 feature fingerprint에도 실제 budget helper SHA를 결속했다. 예산 reset·음수 clamp·64MiB 상한 완화 없이 관련 **440 PASS(48.40초)**, compile 4개·diff 검사, 독립 리뷰 지적 0건과 **13 PASS**를 확인했다. 독립 13개는 표적 시험의 부분집합이며 453개 고유 시험으로 합산하지 않는다. [수리 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/budget-repair-validation-01/receipt.json).

공통 helper가 stop44·holding23 지문에도 정확히1회 포함되도록 보완했다. 원 stop17·holding22 digest는 보존하고 신규 키27·1을 별도 exact extension으로 검증한다. 원7f→최종3개 source pair와 handler59개 의존성을 직접 대사했다. 직접·간접 소비의 Git 변경 거부 오류명 차이만 시험에서 보완했고 원 실패 영수증은 보존한다. 독립 읽기 리뷰의 미해결 지적0, 관련215 PASS와 정정된24개 변조군 PASS를 확인했으며 이를 중복 합산하지 않는다.

이 단계의 통합 code commit은 `831741ca15f8dfba0a20afa6c5fabf4c6fe50942`다. 변경이 없는 source freeze를 유지한69개 모듈 회귀 결과를 별도 attempt03으로 기록한다. 이후 발견한 결손과 후속 commit은 아래에 구분한다.

## 전체 회귀 attempt03과 추가 인계 결손

[69모듈 attempt03](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/integrated-validation-attempt-03/validation.json)은7,578 PASS/7 FAIL,464.54초이며1,300파일 source freeze 불변·compile/Ruff/diff PASS였다. 공유 예산 음수 결함은 재발하지 않았다. 실패6개는 역사 successor target을 현재 capability code와 비교하던 시험과 새 stop/보유/로딩 코드에 대한 원 보고서→현 capability 연결 누락을 함께 드러냈다. 나머지1개는 공통 정책 로더 도입 후의 Main startup 전체 AST를 도입 전 원본과 동일시한 검사다. 각 원 실패와 로그를 유지하고 source/경제/selection 권한을 확대하지 않는 후속 수리·표적 검증으로 종결한다.

## 첫 실제 P5와 환경·읽기 비용 보완

불변 후보2855cffb0에서 실제10/19 준비본을 사용한 [P5 원 실패](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/295ed8ac5d7a44b786c6e4e0e57a94ba/final.json)는14:45:10~14:47:14 KST에 코드 인계를 통과한 뒤 environment 단계에서 `startup_environment_policy_namespace_required`로 종료됐다. 격리 정책 child는 생성하지 않았고 selector는900을 유지했다. native bootstrap이 생산하는 실제 관측 플래그4개를 파서가 거부한 결손으로 확인했다. bootstrap 역할에서만 정확4개 literal 예외를 적용하고 일반/custody namespace·shell 실행 거부·원 값/overlay 순서를 보존한다. 관련114 PASS와 실제 manifest/env 전량 일치·원문 불변 및 독립 재리뷰0을 확인했다.

이 원 시도의 진단 표본은 native 준비 검증 프로세스가12GB 이상을 읽었음을 보여준다. 이는 원천·누적 ledger의 무결성 재검증이며 원 연구 재생을 새로 실행한 결과가 아니다. PID 시작 신원이 없는 진단 표본을 운영 소비·완료 benchmark로 사용하지 않는다. 기존 postclose digest context의 호출별 메모리 재사용으로 중복 해시만 줄이며 최초 전체 해시·각 native 판정·source identity/변경 검사·기존상한·실패 종료를 유지한다. 성공과 실패의 검증된 bounded 통계를 각각 보존하고 영속 cache나 validator 판정 재사용은 추가하지 않는다. [원 실패/진단 표본](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-initial-failure-observation-01.json).

## 두 번째 실제 P5의 cold 로딩 결손

[a8f063105 P5 원 실패](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/15f8bf9dcd6e4db28795dd92645d4800/final.json)는 환경 조립·코드 context 설치 후 Main machine에서 격리 밖 쓰기를 차단했다. 원 child PID1188218/start36715671·exit1·종료true를 대사했다. code context는 설치 성공 후 forbidden 시도를 감지해 정상 폐쇄했고, aux는 machine 종속 실패·delay/stop/holding은 그 이후 문맥 폐쇄로 실패했다. 격리나 native code guard를 완화할 사유가 아니다. 원12개 결과·4개 차단 사건·해시와 native IO는 [진단 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-child-failure-observation-02.json)에 보존한다.

작은 동일 OS 격리 진단으로 V6 contract inventory가 파일 위치를 얻기 위해 quote-recovery 모듈을 실행해 requests의 IPv6 socket 생성에 진입하고, auxiliary transition의 hash-only import가 logger mkdir2/open1에 진입함을 재현했다. 별도 인접 코드 검토에서는 준비 backend의 anchor 복원이 운영 anchor 저장을 무조건 수행하는 결손도 확인했다. 실제 첫4개와 별도 확인한 anchor 저장을 구분한다. 함수 내부 lazy import·실제 파일 native hash·명시 read_only preparation을 보완하며 실제 live 기본 호출·in-memory 복원·정책값·source 검증은 유지한다.

이 시도의 native 사전 검증은 최초해시7,248,583,394bytes/186회와 같은 호출 내 재사용11,568,589,926bytes/909회를 기록했고93.5949초에 종료·entries0을 확인했다. 판정이나 영속 cache를 재사용한 것이 아니며 다른 시도의 전체 wall 시간 가속비나 trading 지연 개선으로 환산하지 않는다.

## Cold 준비 경로의 부작용 제거

원 금지 사건4건은 원문 그대로 유지한다. 정책 inventory는 동일한 canonical source 파일을 native signature/hash로 읽고 수집·주문 모듈을 hash 조회만을 위해 실행하지 않도록 수리했다. quote-recovery의 실제 route 함수와 인자는 유지하고 함수 안으로 import를 이동했다. 정상 Main은 기존 entrypoint에서 해당 모듈을 반복문 전에 이미 import하므로 첫 시세 처리에 초기화 비용을 새로 전가하지 않는다.

준비 모드의 backend 설정에는 명시적 read-only 문맥을 전달한다. anchor 복원은 원 메모리 병합·first-fact·seal·직렬화 크기 제한을 동일한 순수 helper로 계속 검사하고 저장 호출만 생략한다. 저장 성공 영수증을 대신 만들지 않으며 정상 운영 기본 호출은 유지한다. 제품9파일 독립 리뷰 지적0, 신규10시험 PASS 및 실제 V5/V6 cold native loader의 OS 격리 시험을 확인했다. 이 작은 시험을 실제10/19 P5 PASS로 대체하지 않는다. 확장 시험의212 PASS/4fixture FAIL은 [보완 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-readonly-preparation-review-closure-01.json)에 분리했고 최종 source freeze 검증에서 다시 판정한다.

해당4건은 시험 한정 보완으로4 PASS/9.02초와 독립 리뷰 지적0을 확인했다. 원 generation·machine/aux snapshot·등록 evidence/result5개를 원 SHA와 봉인을 유지한 gzip fixture로 보관하고 크기 제한 아래 tmp_path에 복원한다. 누락 원천을 합성하거나 canonical data를 시험 worktree에 연결하지 않는다. detector의 component census와 joint census는 각 실제 생산자 값으로 따로 대사한다. [시험 보완 로그](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-fixture-closure-attempt-01.log).

## P5 근거 전달과 P6 후속 계약 검토

P5 부모의 같은 호출에서 성공한 selected native 전체 검증이 실제로 읽은 원천과 frozen 검증을 관측한다. OS child는 exact run/request/root/selector/정책일·원천 신원에 결속한 근거만 소비하며 native 의미·scope·source·registry 검증은 계속 수행한다. 일반 observer/transition/postclose caller로 새 재사용을 넓히지 않는다. selector/양 HEAD/요청 경로·ancestry의 사용 시 재검사와 원천 변경 실패를 포함해 보완하고 있다. 일반 파일 한도나 TTL을 확대하지 않는다.

P6 준비 도구는 P5 결과의12consumer가 보고한 원천을 재대사한다. 실제 native closure에 있는16MiB 초과 원천은 별도1MiB 청크로 정확한 원 크기만 새로 전량 해시하며, 열기 전·FD·종료 후 신원/ancestry·길이·SHA를 대사한다. 일반 JSON/report의16MiB 한도와 unknown-large 거부는 유지한다. 이는 P5 digest TTL을 연장하는 cache 재사용이 아니다. driver29 PASS/4.29초·독립 리뷰 지적0을 확인했고 원39fa driver bytes는 [이전 검토본](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/prepare_p6_candidate-reviewed-01.py)에 보존했다. 정식 auxiliary 인계 연결 후 최종 driver를 다시 검증한다.

P6를 실행하기 전 경로 검토에서 기존 auxiliary 준비 도구의 old/current 코드 동일 조건과 새 readonly 코드가 충돌함을 확인했다. 원 manifest를 다시 봉인하거나 해당 조건만 삭제하지 않는다. 원 frozen 연구 코드와 새 실행 inventory를 별도 immutable source-code handoff로 검증하는 정식 producer/consumer를 보완하고, 이를 새 manifest sources/dependency 및 selected 세대 P5까지 인계한다. 현재는 이 보완 단계이며 P6 실행 또는 배포 성공을 주장하지 않는다.

## 최종 source freeze와 실제 원천 사전 대사

후속 수리는 `8a8fd0ba1845a69b0a829f5c4bcd551a602aea7e`에 동결했다. 지정9d·stop eb8·holding3ab·기존 선택900의 ancestry를 모두 확인했다. readonly 준비·정식 auxiliary source carry·P5 부모/child 인계·typed 논리 원천·native 자식 수명을 포함한 제품 독립 리뷰 지적0, 관련9모듈312 PASS·11compile·diff PASS는 [제품 검증 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-native-bridge-validation-01/receipt.json)에 기록했다. 코드 인계는 원59개 묶음을 보존하고 현재75개를 단일 세대로 검증한다. 원3family digest·옛 a8·현재·혼합 거부253 PASS와 G capability685 PASS는 [인계 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-readonly-native-registry-review-01.json)로 분리하며 서로 중복 합산하지 않는다.

정식 auxiliary helper는 이번 승인된 동일 적용일 carry만 생산한다. 새 carry를 다시 predecessor로 일반 재승계하는 요청은 명시 거부한다. 정규 postclose는 이 helper의 build/inspect를 호출하지 않으며 기존 native 생산 경로를 유지한다. 발행된 carry의 정상 소비·재검증은 원 predecessor를 참조한다. helper의27 PASS·독립 리뷰와 실제 P6 원천의 native inspect를 구분한다. 새 불변 후보에서 실제 원 manifest/overlay를 검사해55개 원천·128binding·정확2PRE의 native 대사를 통과했다. [실제 읽기 전용 대사](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/auxiliary-native-previous-intake-01.json).

전역 SQLite 원천은 실제1,334,284,288bytes였다. 이를 파일 해시 목록에서 조용히 생략하거나 전체 DB 해시를 반복 추가하지 않는다. 부모 native 검증이 확인한 manifest별 DB/WAL signature·ancestry·유한 ledger metadata/fingerprint를 `logical_source_receipts`로 생산하고 child→parent 및 P6 host CAS에서 exact-set과 실제 selected-row fingerprint를 새로 대사한다. unknown 파일의 원 전체 읽기/한도는 유지한다. P6 private driver35 PASS·독립 리뷰 지적0이며 [검토 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-driver-review-03.json)에 근거를 보존했다.

배포 후보의 표준6개 공유 경로·requirements·native release layout을 확인했고 selector900과 원9파일/백업 bytes는 모두 동일하다. 최종75모듈 통합 회귀는 별도 [attempt04](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/integrated-validation-attempt-04/validation.json)로 실행 중이다. 원 실패3회와 이 후속 검증을 구분하며 현재 단계에서 실제 P5/P6 성공을 표시하지 않는다.


## 최종75모듈 회귀 attempt04와 시험 입력 세대 보완

원 [attempt04](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/integrated-validation-attempt-04/validation.json)는 동결8a8 코드에서 **8,135 PASS/8 FAIL**,630.25초였다.1,309파일 불변·compile/Ruff·shell2개·diff 검사는 통과했다. 실패7건은 최신75개 의존성 세대를 고른 fixture가 과거59개 파일만 복사하여 첫 누락 auxiliary_reader_readiness에서 검사 목적보다 먼저 거부된 경우이며, 나머지1건은 옛 delay extension 해시를 현재 loader 파일에 직접 대조한 시험 기대였다. 제품의 실패폐쇄 검증은 유지한다. 과거59 세대의 실제 Git bytes와 신규75 세대를 시험 안에서 분리하고 관련 전체 모듈을 다시 검증한다. 원 실패 결과를 전체 PASS로 바꾸거나 표적 회귀와 고유 시험 수를 합산하지 않는다.

별도로 실제 불변8a8 후보의 원7f→현재 source projection을 읽기 전용 검사해 stop44·holding23·delay28과 각 원 정책 digest 보존을 모두 통과했다. [실제3family 코드 인계](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/actual-candidate-family-code-intake-01.json)는 정책/selector 발행 없이 작성됐으며 이 사전 검사만으로 P5/P6 성공을 주장하지 않는다.


시험 보완은 최종 `f7d0a9ca12b5d7c771ce6f45d617763bb7412e78`에 동결했다. 직전8a8 대비 두 시험 파일만 변경했고 모든 제품 bytes는 같다. intraday 모듈전체2,497 PASS와 prepared-handoff 모듈전체57 PASS, compile/Ruff/diff와 독립 재리뷰 지적0을 확인했다. 원 전체 회귀 실패를 보존하고 변경 없는 제품의75모듈을 반복 실행하지 않았으며, 중복 시험을 고유 통과수로 합산하지 않는다. [최종 코드 종결 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/final-code-review-closure-03.json), [시험 입력 보완 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/prepared-handoff-fixture-repair-01/receipt.json). 새 불변 관리 후보의 native layout·원 ancestry·requirements·표준6개 공유 경로 및 기존 selector 불변을 검증했다. 실제 P5 세 번째 시도는 이 최종 후보로 별도 실행한다.


## 세 번째 실제 P5의 진입지연 scratch 소유권 결손

최종f7 후보의 [세 번째 원 실패](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/1c4a5cdc233e47f99bd741daf9002c7a/final.json)는 부모 native 준비 검증 후 machine/auxiliary 로딩은 통과했으나, 진입지연의 partitioned 검증이 정책 원천 디렉터리에 임시 scratch를 만들려다 OS 격리에서 차단됐다. 유일 audit 사건은 os.mkdir1건이며 이후 context 폐쇄가 stop/quantity/entry/holding 소비에 전파됐다. 전체 P5는 실패이고 마지막 원천 재검사 단계에 도달하지 않았다. child PID1259505/start37131733·exit1·종료true와 원 보호9파일 불변은 [실패 관측](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-child-failure-observation-03.json)에 보존했다.

격리 밖 쓰기를 허용하거나 선정 재계산을 생략하지 않는다. 검증의 임시 scratch만 증명된 private run 아래로 전달하며 정상 운영·장후 기본 소유권과 원 source/selection 검증을 보존하는 후속 수리 대상으로 한다. P6·selector 발행은 아직 실행하지 않았다.


## SQLite 격리 경계 재현과 부모 실제 선정 검증의 제한 인계

private scratch만 옮긴 중간안의 작은 실제 OS 시험은 sqlite3.connect 차단으로 실패했다. [중간 재현 로그](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/delay-scratch-diagnosis-01/pytest.log)를 보존하며 실제 P5의 네 번째 실행이나 성공으로 세지 않는다. 해당 중간 code/registry bytes와 회귀2,894 PASS는 별도 중간 증거로 남기고 최종 닫힘에 재사용하지 않는다.

수리 방향은 OS의 SQLite/네트워크/프로세스/운영 잠금 차단 유지다. 같은 native 부모 호출의 원 sharded validator가 whole-population SQL 재계산을 실제 성공한 직후 원 문서·참조·선정 코드·인자를 관측하고, 전체 CLI 성공 및 exact run/request/선택본/원천에 결속한다. child에서는 native header/날짜/code와 중첩 membership을 포함한 전체 물리·논리 tree 검증을 실행하고 정확한 부모 선정 결과를 대사한다. 문서·tree source는 child→parent recheck→P6 CAS로 전달한다. 무관한 receipt 또는 active 문맥의 관측 부재는 실패하며 정상 운영/장후는 기존 전체 재계산을 유지한다. 구현 중 발견한 새 tree 재순회의 Claim 누락도 기존 예산 내로 보완한다. 이 절은 검토 중인 계약이며 실제 P5/P6 성공 근거는 후속 terminal 영수증으로 따로 판정한다.


## 제한 위임 수리·최종 CAS 종결과 새 후보

최종 보완은 `20671fc4051ce2b4ef3a9cece195d71bf89ca796`에 동결했다. 원 validator의 None 성공 반환 후에만 문서 전후 동등성·원 생성 경로·28개 native 코드 Git/bytes와 실제 관측을 봉인한다. child는 중첩 membership까지 native 물리·논리 검증을 수행하고 그 source hashes를 parent/P6까지 전달한다. 재순회의 Claim 예약과 경로별 서로 다른 해시의 충돌 거부를 유지한다. 일반 `validate`는 새 P5 분기를 제외하면 원 AST와 같다.

독립 마지막 검토는 긴 native 재검사 뒤 새 consumer source가 최종 CAS에서 빠진 P2를 발견했다. 성공 직전에 모든 consumer source를 다시 검사하도록2줄 보완했고, native tail/final binding 중 실제 child-only membership 원천이 바뀌는 두 반례를 실패폐쇄로 확인했다. core3모듈136 PASS는 이 마지막 변경 전 세대이며, 변경 후 Main/context 전체123 PASS를 별도로 기록했다. [제품 수리 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/delay-parent-verification-review-01.json).

코드 인계는 old59/75 원 assignment를 유지하고 새76 전체를 exact selector로 묶는다. 이전 완전 세대3모듈2,894 PASS와 마지막 literal 변경 후 영향40 PASS를 구분하고 고유수로 합산하지 않는다. 모든 시도 source start/end 일치·compile/diff·독립 리뷰 미해결0을 확인했다. [최종 registry 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/delay-parent-verification-registry-review-closure-04.json).

새 관리 후보의 native layout/requirements·원9d/eb8/3ab/900 ancestry와 원 보호9파일/백업 동일을 검증했다. 실제 후보의 손절44·보유23·진입지연28 인계는 각 원 정책 digest를 보존해 모두 PASS다. [실제3family 대사02](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/actual-candidate-family-code-intake-02.json), [최종 코드 종결04](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/final-code-review-closure-04.json). 실제 네 번째 P5는 이 후보로 별도 실행하며, 앞선 실패3개와 SQLite 작은 재현을 덮어쓰지 않는다.


## 네 번째 실제 P5의 부모/소비자 코드 목록 세대 결손

[206 후보 네 번째 원 실패](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/c047aaecb13e429b90eda19bb83a2dab/final.json)는 intake에서 `startup_delay_native_code_inventory_invalid`로 실패했다. 부모의 실제 `current_full_contract`는 PASS/findings0이고, 동일 원 정책/생성 경로의 target None·10/19 전체 SQL 성공 관측2개가 실제 생산됐다. child는 아직 생성하지 않았다. 원27개 목록과 각 SHA·선언은 selected900 Git 객체와 일치한다. 소비자의28개 목록은 새 `main_policy_loading.py`가 추가된 것으로, 현재 목록을 원 부모에 강제한 검사가 잘못된 경우다. 정책/선정 실패나 SQLite 차단으로 재분류하지 않는다. [실패 관측04](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-intake-failure-observation-04.json).

부모는 그 selected commit의 실제 선언 Git 객체와 파일을 대사하고 literal 목록을 AST로 추출해 정확한 원 inventory를 봉인한다. child는 그 origin/root/commit·선언 SHA·정확한 키/bytes를 확인하며 현재28개 runtime 계약은 따로 유지한다. 부분집합이나 이름을 추정하여 허용하지 않는다. 기존 원 정책·준비본/보호9파일·실패 원문과 immutable206 후보는 유지한다. 또한 private P6 발행 후 `protected_only` CAS가 새 nested source를 생략하는 결손을 원 native publication tail을 보존하면서 보완한다. P6는 아직 실행하지 않았다.

## 원 코드 목록 세대 수리 종결과 다섯 번째 실제 P5

원27개/현재28개 계약 분리와 정확한 Git 선언 검증은 `958d35b2b03f0a37462c1c0121fc14c108e709b8`에 동결했다. 원 선언의 전체 literal 목록·코드 bytes를 대사하며 누락·추가·세대 혼합·dirty 원천은 거부한다. 원 실제 관측2개의 읽기 전용 재대사는 새로운 운영 P5 영수증이 아니다. 제품/시험141 PASS·registry 영향45 PASS·compile/diff·독립 리뷰 지적0을 확인했다. [원 목록 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/delay-origin-inventory-review-01.json), [registry 영향 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/delay-origin-inventory-registry-review-05.json).

새 관리 후보의 원9d/eb8/3ab/900 ancestry·native layout·requirements·표준 공유 경로와 기존 selector 불변을 확인했다. 손절44·보유23·지연28개 실제 코드 인계가 각 원 정책 digest를 보존해 통과했다. [실제3family 대사03](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/actual-candidate-family-code-intake-03.json), [P5 진입 gate05](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/actual-p5-gate-05.json). 이 후보에서 다섯 번째 실제 P5를 실행하며 앞선4개 실패와 원 후보/영수증은 보존한다. 이 절의 코드 검토 완료를 P5/P6 완료로 표시하지 않는다.

private P6의 보호모드 CAS도 종결했다. 발행 전 전체 입력 검사와 발행 후 계획 alias 변경 허용을 구분하면서, 양 모드에서 원 P5 request/final bytes·digest·대상일·실제 candidate 검증기 path/SHA를 확인하고 nested delay 원천 및 DB selected-row 논리 영수증을 새로 검증한다. 새 원천/영수증/코드 변조는 거부하고 whole-DB byte hash는 추가하지 않는다. driver66·builder22로 총88 PASS, compile/whitespace 및 독립 리뷰 지적0이다. 이는 실제 P5/P6 실행 결과가 아닌 private 도구 검토다. 원 native publication tail과 builder bytes를 보존했다. [P6 도구 최종 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-protected-source-cas-review-closure-04.json).

## 실제 P5 통과와 P6 선택 환경 원천 계약 보완

후보958의 [다섯 번째 실제 P5](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/ce996f74c04f41269c3605964c3c3f46/final.json)는 최종 `passed`/findings0이다. 필수12개 중11개는 loaded, holding_prompt는 기존 부모 보존의 native parent_only이며 실패/누락을 이 상태로 바꾸지 않았다. child exit0·종료true·부작용 시도0과 부모의 종료 후 native/CAS 검사를 통과했다. actual_pid_consumed/runtime_effect/allowed_runtime_apply는 모두 false다. 원 실패4개를 보존하며 실제 통과 영수증 SHA는 `b9de6b3c5153f4cbf778cc89dfaf39700b27befa14b67883cc0a9ad2140f822f`다.

이 성공을 입력으로 한 첫 private P6 시도는 stage 디렉터리·child·namespace·호스트 변경 전에 intake에서 실패했다. 실제 P5 producer는 없는 선택 환경3개를 JSON null로 봉인하고 `_recheck`에서 계속 부재인지 검사한다. P6 소비자가 이를 물리 파일처럼 stat하여 FileNotFoundError가 났다. null을 빈 파일 해시로 바꾸거나 해당 원천을 누락시키지 않고 exact absence CAS를 연결한다. 원9파일과 백업 bytes는 모두 같다. [원 intake 실패](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-intake-failure-01.json). 이 실패를 P5 실패나 배포 실패로 재분류하지 않는다.

수리 후 null은 canonical 절대 경로의 실제 부재에서만 통과한다. 파일·디렉터리·leaf/부모 symlink·검사 중 생성은 거부하고 양 보호모드에서 부재 CAS를 수행한다. 기존 nonnull의 전량 해시/상한·typed 논리 원천·delay 재검증 및 native 발행 tail은 유지한다. driver와 시험 source start/end 일치·108 PASS/33.04초·compile·독립 리뷰 지적0을 확인했다. [최종 부재 계약 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-absence-cas-review-closure-03.json). 실제 P5/관리 릴리스 bytes는 바뀌지 않았다. 새 [P6 준비 attempt02](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-02/preparation-plan.json)를 실행하며 원 실패01은 보존한다.

## P6 CoW 경로 신원 대사 경계

[attempt02 원 결과](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-02/preparation-result.json)는 phase00~02(seal/before-state/setup) 성공 후 phase03의 private `isolated-policy` 시작 검사에서 실패했다. native 정책 갱신·선정 전에 호스트 P5의 delay artifact 신원을 CoW 경로에 그대로 대조해 `startup_delay_artifact_generation_changed`가 발생했다. CoW의 조상 inode가 원 호스트와 다른 것이 원인이며 C 검증기를 완화하거나 P5 원 신원을 고쳐 쓰지 않는다. 원 로그/manifest를 유지하고, 모든4개 단계의 child 종료·descendants drain·subreaper 복원 및 원 호스트9파일/백업 동일을 확인했다. selector 발행은 없었다.

private native 준비와 호스트 CAS의 호출 영역을 명시 분리한다. 호스트의 capture-before/postprivate 및 발행 전후는 원 P5 identity 검사를 유지한다. CoW 내부는 실제 mount/network namespace·읽기 전용 root·exact15개 마운트·selector shadow·읽기 전용 물리 원천 증명을 모두 확인한 단일 private 호출만 대상으로 하며, 원 정책 내용/부재 CAS와 전체 native validator를 유지한다. 이 경계의 표적 검증·독립 재리뷰 후 새 시도로 재개한다.

이 수리는 driver `7f721f7290f27f7a9d1f743b2494cb48280497c9ec77494977fec8c151bb762f`에 동결했다. host namespace는 실제 준비 시작 프로세스의 self mnt/net에서 읽어 intake에 봉인하고 runner가 intake SHA를 검증한다. 일반 사용자에게 허용되지 않은 `/proc/1` 접근을 요구하지 않는다. private 옵션은 엄격한 True·보호모드·실제 양 namespace 차이와 기존 전체 격리 가드를 먼저 요구하며 단일 호출만 사용한다. 실제15개 tiny CoW·ubuntu 소비와 마운트/namespace/env 위조 음성을 포함한117 PASS/35.64초·source start/end 동일·경고 없는 compile 및 독립 리뷰 지적0을 확인했다. 원 d4b5/attempt02/권한 중간 실패와 native publication tail은 보존했다. [최종 domain 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-cow-domain-review-closure-05.json), [실제 attempt02 독립 보존 대사](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-failure-independent-review-02.json).

새 [P6 attempt03](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-03/preparation-plan.json)의 private native 정책 단계는 코드 인계/Main 갱신/auxiliary/schema/bootstrap/parity를 통과했다. 전체 준비 결과와 호스트 발행·최종 세대 P5는 해당 terminal 영수증으로 별도 판정한다.

## P6 실제 발행과 호스트 검증

[attempt03 준비 결과](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-03/preparation-result.json)는 `prepared_for_separate_root_publication`이다. 정책/parity·4capability·수량·summary·strict/controller·10/19 준비본과 private current_full_contract가 통과했고, 5개 phase 모두 exit0·자식 종료·descendants drain·subreaper 복원을 확인했다. parity는 양쪽128scope/76,800행/598hit·신호 SHA 동일·불일치0이다.

발행 전 독립 읽기 대사와 fresh census(process0/errors0), 분리 publisher의 plan-only를 통과했다. 원 native transaction 아래54개(신규46/기존8)를 발행하고 selector를958로 이동했다. [실제 배포 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-03/deployment.json)은17:29:24 발행/17:31:09 검증 완료의 `deployed_and_policy_verified`다. [호스트 전체 검증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-preparation-attempt-03/published-native-verification.json)은 source10/16·target10/19·current_full_contract PASS/findings0이다. live pointer 변경·실제 PID 소비는 false다.

[발행 전후 독립 검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p6-publication-independent-review-03.json)는 지적0이다. 새54파일/39,247,541bytes·기존8backup·원불변15/계획갱신7 snapshot, readonly53파일/13,061,874bytes와 원128binding/2PRE/rollback/4정책영수증/env 실할당행/OPEN6owner를 대사했다. 계획된 발행 전후의 CAS 변화와 원천 결함을 구분한다. 원900·과거 준비/실패·raw 비용/수탁을 보존했다. 정식 source-code-handoff는 새 manifest.sources의 실제 참조이므로 해당 attempt03 증거 경로를 유지한다.

최종 명령 경로 확인에서 canonical7c 라우터가 새 수동 명령을 아직 노출하지 않는 배포 제어면 결손을 발견했다. 원본 SHA/백업과 canonical HEAD7c·다른 변경은 보존하고, 검토된958의 라우터 한 파일만 exact Git bytes로 반영했다. 변경은 명령 등록1개·selected CLI 분기4줄·날짜 필수 검사2줄뿐이다. source SHA 일치·격리206 PASS/compile/diff·독립 리뷰0과 canonical plan을 확인했다. [제어면 배포](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/canonical-control-router-deployment-01.json). 선택 릴리스 자체를 다시 수정하거나 Main을 기동하지 않았다.

표준 `bash deploy/run_runtime_release.sh validate-startup 2026-10-19`로 최종 세대 P5 `fc98c7d7f0eb42e99515e65b4b6514ba`를 실행한다. 원 최초 P5와 required marker는 불변으로 유지하고 완료 영수증을 별도로 남긴다. cron8+snapshot3과 release-set은 PASS, preopen/start는 새 선택본을 가리키는 **print-plan만** 확인했다. 이 단계에서 최종 P5 완료나10/19 실제 PREOPEN/PID 수용을 미리 표시하지 않는다.

## 최종 선택 세대 P5와 기술 작업 종결

[최종 P5 fc98](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/fc98c7d7f0eb42e99515e65b4b6514ba/final.json)는 `passed`/findings0·basis selected다. 부모/실행 commit958, 원 선언28개, 필수12개(11 loaded/holding_prompt parent_only), 금지 부작용0·child exit0/종료·마지막 부모 native 및 source CAS를 통과했다. validation PID1406953/start37646495는 검증 child이며 운영 Main PID가 아니다. 최종 raw SHA는 `f7497d588fd01384216cc74cb6db70b5a4940e41d1519a763ed159fc0d05e124`다.

[최종 P5 독립 리뷰](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-final-independent-review-01.json)도 지적0이다. source union3,945개의 충돌0과 원천/실행 결속을 대사했다. 대형189개는 독립 리뷰에서 ancestry/stat만 검사했고 raw를 다시 전량 읽지 않았다. 실제 native 최초/마지막 검증은 별도 PID·별도 메모리 세대에서 각각7,258,202,491bytes의 최초 읽기와 유한 재사용을 수행하고 종료/잔여0을 확인했다. 과거 PASS나 영속 cache 재사용으로 판정을 대체하지 않았다.

최종 readiness SHA `b5954f3baa1543deadcb65a77cb140cef8dfaf94d16e1f0fb8c8e93daf8b7800`와 manifest SHA `a9f915138cb5ae8861d8e2f8ed058b7fe306cc7a5574c28d4f94c131362ec8f8`가 실제 canonical index·P6 준비본·원 required marker와 일치한다. 최초 P5/marker를 덮어쓰지 않고 [완료 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-final-generation-completion-01.json)을 봉인했다. [제어 라우터 독립206검토](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/canonical-control-router-review-01.json)와 표준 plan도 대사했다.

최종 census는 Main/관련 실행0·오류0, selected code는 clean이며 원9backup·옛 불변 준비본/손절 원 정책·canonical HEAD7c와 다른 변경을 보존했다. canonical 라우터 한 파일은 검토된958 bytes의 배포 제어면 변경으로 남는다. 현행 정책의128/2PRE/rollback·비용/수탁·hard safety와 미래 OPEN6owner를 유지한다. 현재 입력·등록 가설 연구와 통합/P5/P6 기술 작업을 종료한다. 신규 수치 정책의 경제/성능 승인, 실제10/19 PREOPEN/Main PID·자연 주문/체결·비용 후 성과로 확대하지 않는다.
