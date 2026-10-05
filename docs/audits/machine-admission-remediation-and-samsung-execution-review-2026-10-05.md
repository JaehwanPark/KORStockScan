# 기계 수용조건 보완·삼성 검증·저장공간 정리 — 2026-10-05

## 1. 판단과 범위

[실행계획](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md)의 P0~P5와 S1~S3를 구현하고 기존 원천으로 재생했다. 비삼성 후보는 **학습 적격, 새 날짜 검증 대기**다. 삼성은 목표 도달률 개선과 비용 후 양수 비율 동률을 구분했으며 최신 후보의 이후 날짜 adapter를 준비했다. 성공100%/80% 보존과 선택50% coverage는 신규 admission 계약의 탈락 조건이 아니다.

기계 후보의 관측 평가 계약을 바꾸는 구현이다. 운영 주문·수량·custody·보조 AI·청산·hard guard를 변경하지 않았다. 원천 추가 수집 및 실계좌/API 호출은 없다. P6 배포·정확한 날짜 준비의 최종 상태는 같은 실행 폴더의 `closure.json`에 별도 기록한다. 기동 준비와 다음 영업일 실제 PID 소비는 별개다.

## 2. 수정과 리뷰

- 역할 위치: 순수 장후 수용 검증은 `src/engine/scalping/entry_admission_acceptance.py`, 삼성 오프라인 adapter는 같은 package의 `samsung_absorption_acceptance_research.py`에 둔다. engine root 새 모듈은 만들지 않았다.
- `main_machine_observation_admission_acceptance_v1`: 원 관측 최초 신호→비중복 점유→종목/날짜/venue/session 동일 가중. 학습30·검증10 경계확정 군집, 양쪽 raw 승률 상승·지원조정 점수+5pp. 성공 보존과 coverage는 진단이다.
- 계산/학습 적격/검증 실행/최종 선택을 분리한다. `candidate_evaluated`의 기존 eligibility 의미를 유지하면서 실제 계산 여부를 새 필드로 전달한다. 기존 native 분모·3건1승·부적격 사유는 `native_diagnostics`에 보존한다.
- 최신 source 날짜만 미소비 forward로 사용할 수 있다. 이미 소비한 최신 날짜보다 앞선 날짜를 검증으로 골라 미래 학습이 섞이는 것을 금지한다. 후보 선택0일과 입력 원천 날짜를 분리한다.
- generator·publisher·dated loader·stage verifier가 같은 계산을 재검증한다. runtime approval summary에도 새 상태·사유와 삼성 미등록 상태를 전달한다. holdout 실제 평가가 없으면 소비 receipt를 발행하지 않는다.
- 기존 승리 보존 진단은 trace 교집합으로 수정했다. 해당 native 진단은 retained0/new1/excluded17이다.
- 재리뷰에서 이미 채택된 recipe가 다음날 다시 들어왔을 때 발생하던 예외를 제거했다. 같은 정책은 비교 후 정상 승계한다. 삼성 미래 입력의 원 raw 종목/venue/session과 가격 request 결속도 추가했다.
- 테스트 초기 실패는 새 관측 계약 없이 빈 analysis를 사용하던 fixture와 날짜가 바뀐 비용 계약, 부동소수점 단정 비교에서 발생했고 보완했다. 현재 구현과 과거 테스트 입력을 혼용하지 않았다.

## 3. 비삼성 재생 결과

원 projection8,793행을 읽고 실제 생성기를 호출했다. 관측 연구7,069개 전체의 raw/hash/시각/부모·후보 행동/가격 경로는 이전 연구와 차이0이다. 비삼성 원401선택의 identity/raw/action/binary 및 선택 집합 차이도0이다.

| 항목 | 기존 | 후보 |
| --- | ---: | ---: |
| 전체 탐색 날짜 선택 |217|197|
| 경계확정 종목/날짜 군집 |95|83|
| 목표/손절/미도달 |80/75/6|93/48/5|
| 군집 승률 |45.7496%|70.1979%|
| 지원조정 점수 |37.5763%|61.4088%|

이번 acceptance 학습은 탐색 완료된9/29·9/30·10/2 전체다. 과거 연구 분할의9/29·9/30 **42.59→67.75%**,10/2 탐색 비교 **53.70→75.00%**도 보존한다.10/2를 미사용 holdout으로 부르지 않는다.

`computed=true, train_qualified=true, validation_evaluated=false, selected=false, fresh_validation=not_observed`. 최종 미선정 이유는 **`admission_recipe_forward_date_after_2026_10_02_required` 하나**다. native124개만 비교하던 부적격 결과를 전체 관측 후보 성능으로 사용하지 않는다. 미확정은 그대로 공개하며 실제 체결/PnL이 아니다.

## 4. 삼성 S1~S3

전체519관측에서68개 신호 구간, fixed-watch206관측에서31개 구간을 구성했다. 첫 신호는 행동/시각/원천 구간만 읽고 이후 가격 label을 보지 않는다. 전체 및 상시감시 모두 최초 신호 축소 후 비중복 선택이 이전과 같았다. 반복8건을 독립8날짜로 세지 않는다. fixed-watch는9/30·10/2만 있고9/29 학습을 상시감시 자료로 합성하지 않는다.

|10/2 동일 고정 선택|기존|흡수 후보|결론|
|---|---:|---:|---|
|선택|2|8|같은 모집단의 서로 다른 진입 시점|
|목표/손절/완전60분 미도달|0/0/2|4/2/2|경계와 시간종료 분리|
|목표/손절 승률|정의 불가|66.67%|`not_identifiable`|
|미도달 포함 목표 도달률|0/2=0%|4/8=50%|`improves`|
|경로 종료 비용 후 양수 비율|1/2=50%|4/8=50%|`no_improvement`|

미도달은 목표·원 손절 미도달이며 가격자료 부재가 아니다. 기존 고정60분 CF 평균−0.2300%, 후보−0.3079%는 별도 진단으로 남는다. 위 도달률 개선을 새 운영 주지표로 소급 채택하지 않는다.

원 capture 전체 feature와 기존 as-of receipt로 `absorption_p60_v10` replace를 재생했다. 최신 snapshot 전체 feature가 과거에 보관되지 않은 결손은 추가 복원되지 않았다. 서로 다른 시점의 일부 필드를 섞어 새 성과를 만들지 않았다.

새 frozen은 원 parent·recipe·평가 목적·현재 kernel·증빙 hash와 `later_source_after_date=2026-10-05`를 결속한다. 기존 foreign/program veto2개 계약은 보존한다. 미래 adapter는 자동 생산된 원 projection과 완료 가격만 읽으며, 원 raw 내부의 exact tick receipt가 없으면 해당 관측을 source gap으로 제외한다. 종목/route/hash/시각/parent/원 비용/stop을 검증하고 결손을0으로 채우지 않는다.10/6 입력 부재는 **`waiting_new_source_date`**다. 신규 정책 등록/성능 검증 완료가 아니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_absorption_acceptance_research --root /home/ubuntu/KORStockScan --frozen tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json --date 2026-10-06 --output tmp/samsung-absorption-forward-20261006/intake.json
```

출력은 기존 파일을 덮어쓰지 않는다. source가 같은 상태에서 반복 실행하지 않고, parent/kernel이 달라지면 재계획한다. 현재 S1~S3 연구는 종료하며 자연 후속 검증은 `SamsungFrozenCandidateValidation1006`이 소유한다.

## 5. 원천·저장공간 보존

기존 projection gzip3개의 종전 압축 bytes가 앞 작업에서 보관되지 않은 한계는 그대로 기록한다. 이번 연구 요청은 새 물리 SHA를 별도 선언하고, 바뀐 과거 코드1개는 기존 SHA와 일치하는 보관 사본을 사용했다. 이전 frozen 보고서는 수정하지 않았다. 새 재생7,069관측 차이0은 논리적 재현 증거이며 잃어버린 종전 압축 bytes 복원이 아니다.

정리 전 가용15.647GiB. 현재/rollback·systemd/cron·PID/FD·고유 source·연구 참조를 대사한37개 등록 작업본에는 삭제 적격 전체 worktree가0개였다. 해당 작업본과 원천은 보존했다.

- 선택적 연구 캐시: 소유자 `research_cache_storage.write`의 lock·process/persistent pin·파일 identity 검사를 사용해342,289개 catalog entry를 정리했다. 원천/정책 제거 및 영구 cache cap 변경은 없다. 캐시 누락 시 기존 owner가 로컬 원천에서 계산한다.
- 과거 증분 모니터5파일: 무손실 gzip 보관 후 원 논리 SHA/크기 및 개방 FD를 검증했다.9/29·9/30·10/2 상태는 유지했다. 과거 원 상태는 보관본에서 복구 가능하며 consumer는 누락 시 raw 재구성한다.
- 사용 종료 profile checkpoint2,796파일: tar.gz47MiB에 보관하고 모든 member의 SHA를 검증했다. 실제 분봉/API 응답 cache는 보존했다.
- 미사용 작업본의 재생성 가능한 bytecode10,648경로를 정리했다. 현재/이전 선택과 실제 PID 작업본은 제외했다. hardlink 해제에 따른 ctime 변화는 device/inode/size/mtime 및 내용 SHA 재검증으로 구분했다. 대응 `.py` 없는 항목은 삭제하지 않았다.

중간 가용량은 약22.43GiB였다. 최종 쓰기·배포 후 실제 용량은 closure에 재측정한다.25GiB 관리 목표에 못 미치더라도 가격 원천·Parquet·운영 snapshot·유일 연구 증빙을 삭제해 목표를 맞추지 않는다. 제거한 optional cache는 다음 연구에서 재구성 비용이 발생할 수 있다.

## 6. 증빙·남은 경계

- [실제 생성·삼성 연구](../../tmp/admission-remediation-execution-20261005/replay-v2/), [401선택 대사](../../tmp/admission-remediation-execution-20261005/replay-v2/selected-401-parity.json), [7,069관측 대사](../../tmp/admission-remediation-execution-20261005/replay-v2/observation-parity.json)
- [360 표적 회귀](../../tmp/admission-remediation-execution-20261005/final-tests.log), [소비자 별도 회귀](../../tmp/admission-remediation-execution-20261005/consumer-tests.log), [계산/동결 검증](../../tmp/admission-remediation-execution-20261005/replay-validation.log)
- [참조 census](../../tmp/admission-remediation-execution-20261005/cleanup-census.json), [캐시/모니터 정리](../../tmp/admission-remediation-execution-20261005/storage-cleanup-result.json), [프로파일 복원 manifest](../../tmp/admission-remediation-execution-20261005/profile-cache-archive.json), [bytecode 결과](../../tmp/admission-remediation-execution-20261005/bytecode-cleanup.json)

검토 범위의 코드·계산·출처 차이를 닫았다는 결과다. 미래 자연 데이터의 품질, 새 후보의 독립 우월성, 실제 기동과 비용 후 실현 수익을 확정하지 않는다. 삼성/비삼성 다음 날짜 검증과 Main/Widget/Episode 당일 수용은 기존 개별 owner에 남긴다. 새 API 프로토콜/주문 handler를 변경하지 않아 Kiwoom upstream gate와 provider 테스트를 호출하지 않았다.

## 7. P6 배포·정확한 날짜 준비 완료

- 코드 커밋 `c8c00c06d943b50c47c7fe17184a399a1f2814c8`, 선택 release `machine-admission-acceptance-20261005-c8c00c06`. 이전 `machine-admission-source-review-20261005-3e982ece`를 rollback으로 보존했다. Main 실제 PID 소비는 아직 없다.
- workspace 표적360회귀와 별도 생성기235회귀를 합쳐 **595 PASS**, 선택된 물리 release에서 중복 포함 **97 PASS**. compile·로컬 링크·diff·print-only parser를 통과했다. 전체 저장소 또는 미래 시장 동작의 무결함을 주장하지 않는다.
- inactive 장후 분석 unit2개만 새 release에 연결했다. 서비스 재기동은 없으며 Widget 거래 PID3614517의 실제 cwd는 기존 `postclose-winrate-readiness-20261003-e6d4d3b9`다. 서비스 설정을 PID 소비로 간주하지 않았다.
- 원천 품질 최종 audit는 구현 hash 변경에 따라 정식 producer로 재생성했다. Main 보고서는 실제 격리 재생 결과를 정식 publisher로 전달했다. 첫 발행 도구에서 빠졌던 CLI `publication_date` 메타데이터를 보완한 뒤 stage를 다시 검증했으며, 현재·10/6 정책 bytes는 처음부터 끝까지 유지됐다.
- 전체 stage15개는 활성 단계 성공·명시 OFF 상태이며 loader의 Main/Widget/Episode 조회가 통과했다. 전체 strict `whole_native_chain` PASS, controller `done`,10/6 prepared `current_full_contract` PASS·findings0으로 재봉인했다. 최초 준비 시도는 최종 controller 완료 전 실행되어 거절됐고, 최종화 지침의 `POSTCLOSE_STAGE_WORKER=1` 전체 DONE 경로를 완료한 뒤 순차 재실행했다. 요약 전용 성공을 전체 완료로 사용하지 않았다.
- 새 비삼성 보고서는 학습 적격·새 날짜 대기를 전달한다. 이미 발행된10/6 incumbent은 불변으로 보존되어 새 보고서와 당시 발행 보고서 hash가 다르며 `existing_incumbent_preserved`로 명시된다. 새 후보 선정이나 삼성 후보 등록이 아니다.

현재 bundle `6785d52e…`,10/6 bundle `3c500f6a…`, KRX 기계 정책 `d94fecaf…`를 유지한다. `day_of_activation_required=true`, `actual_pid_consumed=false`다. 다음 영업일 Main/Widget/Episode의 당일 수용, 격리 해제, 실제 주문 및 수익은 준비 PASS의 보증 범위가 아니다. 별도 승인된 Widget/Episode pin과 격리는 그대로다. Plan Rebase §7의 이전80% 문구(D8)는 기준 문서 유지보수 권한 경계에 따라 이번에 편집하지 않았으며 새 acceptance의 탈락 조건으로 사용되지 않는다.

최종 저장공간은 **15.647→22.244GiB, 순증가6.596GiB**다. 추가로 optional catalog의 논리 행을 보존한 VACUUM과 종료 pytest fixture1개 정리를 수행했다. 재계산·보관본·새 release 쓰기를 포함한 실측이며 각 정리 창의 회수량을 단순 합산하지 않았다.25GiB 목표에는 미달하지만 검증된 후보를 소진했다.

최종 증거: [closure](../../tmp/admission-remediation-execution-20261005/closure.json), [전체 controller](../../tmp/admission-remediation-execution-20261005/controller-final.log), [10/6 준비 검증](../../tmp/admission-remediation-execution-20261005/prepared-verify-final.json), [235 생성기 회귀](../../tmp/admission-remediation-execution-20261005/generator-regression.log), [97 물리 release 회귀](../../tmp/admission-remediation-execution-20261005/physical-tests.log), [catalog 정리](../../tmp/admission-remediation-execution-20261005/optional-catalog-vacuum.json), [pytest 정리](../../tmp/admission-remediation-execution-20261005/pytest-cleanup-result.json).
