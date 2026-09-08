# #71 Pattern currentness / #72 Pattern AI review 보완

기준: 2026-09-08 KST. 사용자의 권고 구현·리뷰 요청 범위이며 장후 전체 재실행, provider 호출 또는 실전 변경 지시가 아니다.

## 목적과 판정

비용 차감 후 작은 순이익과 반복 빈도를 평가하는 기존 Lab 연구가 정확한 원천·검토 세대로 기존 owner에 전달되도록 보완한다. #71/#72는 독립 튜닝축이나 매수 승인 주체가 아니다. 코드 수리와 자연 생성·PREOPEN 선택·PID 소비·실현 순익 수용은 별도다.

## 보완

- #71의 파일 존재/문자열 참조를 실제 소비로 계산하던 경로를 수정했다. Lab producer가 읽은 같은 bytes의 날짜·SHA256 receipt를 payload summary에 기록하고 run manifest가 이를 결속한다. 새 공통 helper는 기존 `src/engine/automation` 역할에 배치했다. engine root에 새 모듈을 만들지 않았다.
- 잘못된 JSON·내부 날짜·상태·receipt/schema는 명시적 결손이다. 이전 유효 feedback 사용은 허용하되 원래 소비한 세대와 최신 가용 세대를 구분한다. Swing OFF를 복구하지 않으며 enabled offline availability도 actual consumption으로 계산하지 않는다.
- #72는 필수 currentness 실패를 전수 대사한다. AI가 누락하거나 모순 KEEP를 반환해도 해당 실패 ID를 유지한다. 문자열 `swing` 언급 때문에 Scalping 결론을 삭제하지 않는다. 프롬프트는 활성 owner·작은 순익·빈도·비권한성에 맞췄다.
- 원본 provider response와 input hash를 불변으로 보존한다. metadata-only refresh의 현재 source hash와 원본 AI input hash를 분리하고, primary material 변경은 WARNING/검토 대기로 전달한다. 상세 요약에서 생략된 코호트 변경도 material fingerprint에 포함된다.
- 원본 응답의 참조 공유·퇴역 필터에 의한 변형, 응답 hash 변조, 잘못된 날짜, JSON scalar/list/null, 모순 auditor flag, 중복 ID/작업지시 key 충돌을 검증한다. provider가 직접 넣은 deterministic resolution 표시는 신뢰하지 않고 재계산한다.
- 새 원천의 검토 대기는 EV 경고와 workorder `defer_evidence`로 전달한다. 이를 완료된 구현, 실전 승격 또는 새 코드 수리의 무한 반복으로 바꾸지 않는다. 기존 scheduled reviewer가 새 원천을 검토한다. metadata refresh에서 provider 호출량·retry를 늘리지 않는다.
- material이 달라지면 이전 AI의 구체적 코드수정 제안도 새 세대의 실행 대상에서 제외한다. 현재 결정론으로 확인된 실패만 유지한다. #71이 이미 발급한 native 수리 ID가 있으면 #72의 동일 실패는 해당 작업에 연결하여 중복 구현을 막는다.
- trigger의 누락된 primary artifact/계약 코드 의존성을 보완했다. AI JSON은 검증·최종 정합성 보완 이후 기존 generation-safe writer로 한 번 publish한다.

## 조건·권한

표본 0이나 아직 미관측 순익은 이 수리의 실패 조건이 아니다. 새로운 고정 수익률, 전 horizon MFE/MAE 또는 실체결 floor를 #71/#72에 추가하지 않았다. 기존 Daily/경제성 owner의 실제 비용·full/partial 분리·rolling 비교·PREOPEN 및 operator lock 우선순위는 변경하지 않았다.

## 검증과 다음 자연 수용

기존 테스트와 새 격리 회귀에서 producer receipt → currentness → AI 판정/반복 metadata refresh → EV/workorder를 확인했다. 14개 관련 테스트 모듈 **703 passed**(13.73초). producer/consumer, wrapper, strict postclose verifier와 engine location gate를 포함한다. 영향 Python 9개 compile, Ruff E9/F63/F7/F82, 신규 helper/회귀 Ruff, 문서 print-only parser, `git diff --check`를 통과했다. parser에서 기존 `PatternLabSmallNetNaturalEvidence0908` owner는 한 번 파싱된다. 검토 범위 내 미해결 finding은 0건이다.

초기 회귀가 보존하던 모순 KEEP 정상화 기대값은 이번 실패 유지 계약에 맞게 바꿨다. warning reconciliation fixture의 중복 native ID와 transport fixture의 미정의 `resolved` 상태도 각각 유일 ID/정의된 상태로 수정하고, 잘못된 ID·schema를 거절하는 별도 부정 회귀를 추가했다. bare feedback 존재 fixture는 날짜·실제 receipt 근거를 갖추도록 바꿨다. 기존 오류를 정상 동작으로 유지하기 위해 gate를 완화하지 않았다. 병행 세션의 공유 workorder/문서 변경은 보존했으며 이 리뷰는 #71/#72 관련 수정에 한정된다.

자연 수용은 기존 `PatternLabSmallNetNaturalEvidence0908` 하나에서 이어간다. 새 OPEN을 중복 생성하지 않았다. 구세대 9/7 자료의 WARNING을 이번 코드의 자연 성공으로 바꾸거나, 누락된 과거 비용을 합성하지 않았다. 운영 산출물 재생성·provider 호출·실전 env/lock 변경·매매 process 재기동·커밋/푸시 및 외부 sync는 수행하지 않았다.

`korstockscan-review-gate`에 따라 리뷰 중 발견한 참조 공유와 원본 변형, 후속 분류 결함을 추가 수정하고 재검증했다. 이는 코드·전달 계약 검증이지 신규 수익의 증거가 아니다.

## 최종 목적 리뷰 후 추가 보완

이후 읽기 전용 재점검에서 확인한 3건에 대해 사용자가 보완 구현을 요청했다. 위의 703 passed/finding 0은 앞선 검토 시점의 결과이며 아래 추가 범위의 검증을 대신하지 않는다.

- 후행 전체를 material에서 제외하던 경로를 수정했다. 품질 원천의 의미 필드, EV의 daily economics/calibration/source gate를 fingerprint에 포함하고 모델 입력은 요약으로 제한한다. 생성시각·경로 변경과 비용·품질 판정 변경을 구별하며, 현재 품질 gate의 명시적 실패를 결정론으로 보존한다. self-feedback workorder/propagation은 별도 대사하여 순환을 만들지 않는다.
- 파일 mtime만 최신이면 검토 대기를 skip하던 trigger를 보완하고, main wrapper의 두 후행 지점과 ON인 복구 controller를 동일 generation reviewer에 연결했다. 기존 primary+retry 합계 2회 상한을 대상일 단위 예약 ledger/lock으로 공유한다. metadata-only 명령은 호출하지 않는다. 유효한 새 검토는 이전 응답 증거를 보존하며, 예산 소진·중단/거절·OFF는 명시적 미검토 source-only terminal로 남긴다. 무제한 호출이나 다음 거래일의 과거 승인 대체는 없다. verifier는 현재 의미 세대와 마지막 reconciliation을 비교하고 불일치를 복구 경로로 전달한다.
- 기존 score-recovery 재선택 owner를 profile-search v2로 보완했다. 건당 EV 동시 개선의 추가 조건 대신 양수 full EV·유효 원천일당 순익 개선·비악화 자금시간 효율을 확인한다. full 20건/2일·분산·부분체결 손실·앞쪽 학습/고정한 한 후보의 뒤쪽 검증·다른 승인 venue 비악화는 유지한다. 부분체결의 순익뿐 아니라 자금시간도 분모에 포함하며 결손은 0으로 합성하지 않는다. 기존 한 축의 bounded 범위, 상승/반등, AI correction/PREOPEN/운영 lock/수량/안전 계약은 변경하지 않았다.

격리 사례: 같은 자금 점유에서 100원×5회=500원/일 대비 70원×10회=700원/일은 새 선택을 통과한다. 자금시간을 과도하게 늘려 효율이 악화되는 경우, 자금 점유만 비례 증설한 등효율 증가, holdout 손실은 탈락한다. 부분체결 자금시간 결손은 `comparison_source_incomplete`로 분리하며 성과 부진으로 세지 않는다. 이 숫자는 합성 검증이며 실수익 주장이 아니다.

추가 리뷰에서 Pattern 세대 불일치만으로 Daily AI/실행 facts/PREOPEN을 재생성하던 불필요한 복구 확장을 제거했다. 이 경우 currentness/reviewer와 영향 workorder/EV/summary/gap/tower/checklist/strict verifier만 닫는다. metadata-only 결과가 이전 호출 횟수를 새 호출로 표시하지 않도록 0회로 대사하며, 중단/거절 결과를 다시 actionable pending으로 표시하지 않는다.

최종 검증: 직접 producer/consumer, 복구 controller, wrapper, verifier, PREOPEN 경제성 소비, engine location gate를 포함한 **15개 모듈 828 passed (16.54초)**. 영향 Python 9개 compile, Ruff E9/F63/F7/F82, `bash -n`, 문서 print-only parser, `git diff --check` PASS. parser는 `PatternLabSmallNetNaturalEvidence0908`와 `DailyThresholdNaturalAcceptance0908`를 각 1회 파싱했다. 격리된 실제 context producer → 새 material 재검토 → metadata fixed-point → verifier hash 비교, 중복 mutex·중단 예약·예산 손상·새 거래일 분리·원본 이력과 terminal 실패를 확인했다. 이 추가 검토 범위의 미해결 finding은 0건이며 병행 세션의 다른 변경 전체를 인증하는 결과가 아니다.

운영 산출물 재생성·실제 provider 호출·env/lock 변경·매매 process 재기동·커밋/푸시는 실행하지 않았다. 자연 수용은 기존 `PatternLabSmallNetNaturalEvidence0908`와 연계 Daily owner를 유지한다. 코드 검증 완료는 다음 장후 자연 실행, PREOPEN/PID 소비 또는 비용 차감 실수익 개선의 완료가 아니다.
