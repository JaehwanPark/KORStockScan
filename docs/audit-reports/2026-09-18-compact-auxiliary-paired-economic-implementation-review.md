# 2026-09-18 Compact auxiliary paired 경제성 구현 review

사용자 승인 범위는 [CP0–CP5 계획](../proposals/compact-auxiliary-ai-paired-economic-tuning-and-consumer-closed-loop-improvement-plan-2026-09-18.md)의 구현·반복 코드 review/수정·targeted validation·commit/push·immutable release 배포와 제한 장후 재생성이다. 실제 주문·bot restart·manual env/provider/threshold/guard·cron 복원은 포함하지 않는다. 다른 세션의 entry split 변경과 작업본 미커밋 변경을 보존하며 clean origin/main 기반 별도 worktree에서 진행한다.

## 구현과 review 보완

- 기존 batch의 compact 실행 분기에서 실제 current `ENTER_NOW` screen을 한 번 stream하여 입력을 동결하고 등록 nano 후보·기존 provider budget·누락 응답 checkpoint만 실행한다. 기존 BUY/WAIT·holding 연구는 이 분기의 선행 조건에서 분리한다.
- Provider input hash와 정규화한 semantic input hash는 별개다. JSON string capture를 raw-byte hash로 재직렬화하여 탈락시키던 구현 오류를 수정했다. 같은 입력의 다른 request envelope도 각각 결속한다. 입력 identity는 미래 cost/outcome과 분리하여 유효 응답을 재사용한다.
- 동일 verdict의 Δ0을 공통 분모에 포함하고 CAUTION 후속 routing·terminal·비용 결손을 null로 둔다. 기존 owner 실행 CF의 가격/수량/leg/exit/cost를 재사용한다. 금액 portfolio는 공통 한 포지션 allocation·비중복 실행만 인정하고 이미 zeroed reservation이나 겹친 자금 재사용은 미확정으로 남긴다.
- 기존 자연 방향 추천만으로 후보를 승격하던 selector를 paired proof 기반으로 변경했다. Source/cohort/current incumbent·독립 episode/날짜·chronological freeze/holdout·원 owner 경제성 재계산·tail/stress·일별 순익·미사용 holdout을 검증한다. Runtime inference 비용 차이 미확정은 승격하지 않는다. Holdout consumption ledger는 기존 publisher lock 아래 같은 proof 재시도만 허용한다.
- 기존 publisher가 다음 적용일 policy를 생성하며 machine/다른 scope 값과 과거 source/generation을 보존한다. PREOPEN 동결·미등록 prompt·미래 stage owner 충돌은 우회하지 않는다. Calibration/optimizer/consumer의 unrelated section도 보존한다.
- Native/follower의 최종 generation을 Daily·EV·runtime approval·tower section·적용일 checklist와 family strict verifier까지 결속한다. Family PASS는 원 native 실패·다른 family 상태를 덮지 않는다. 전체 tower가 없는 경우 existing tower folder의 명시적 compact scope receipt로 한정한다.

새 코드 소유 경계는 기존 scalping 패키지의 offline helper 한 파일이다. 새 engine-root module/CLI/cron/DB/collector/독립 publisher는 추가하지 않는다. 테스트 변경은 기존 관련 파일의 새 계약 회귀이며 변경 전 natural-only 승격·legacy follower 실행 순서 전제는 제거했다.

## 검증과 실제 결과

최종 source validation, 제한 재생성·정책/strict receipt, selected release는 아래 closure record와 `tmp/compact-auxiliary-paired-20260918/`의 owning receipts를 따른다. Fixture의 양수 ΔEV는 실제 결과로 집계하지 않는다. 실제 유효 sample·독립 holdout·자연 PID 소비/실현 비용 후 성과는 별도 acceptance다.


## 외부 소유 경제성 의존 결손

병행 entry split의 최종 source `363131824`를 포함해 재리뷰했다. [기존 owner review](2026-09-18-entry-split-execution-model-source-and-consumer-review.md)는180초/±0.5%/고정0.23% 연구 exit·cost·reservation을 supporting diagnostic으로만 인정하며 운영 청산·실제 비용·자본 모델 및 validated scope는 미구현/미입증이다. Compact 승격도 이 미검증 모델을 경제성 증거로 사용하지 않도록 기존 `execution_model_validation`의 검증 상태를 소비한다. 현재 실제 proof로 승격 가능한 cohort는 없다.

따라서 구현된 연결 루프와 다음 날짜 carry 발행을 CP2의 운영 경제성 구현 완료 또는 양수 EV 도출로 발표하지 않는다. 물리적인 historical stop/quote/owner plan 결손은 시간만으로 복구되지 않는다. 유효 input·당시 plan/exit/cost·검증된 owner 모델·reviewed inference 비용/원화 차이를 제공하는 기존 owner가 다음 closure이며, 그 뒤 current compact 독립 날짜 holdout과 적용 버전 자연 COMPLETED 경제성을 확인한다. 이 작업에서 다른 세션의 운영 모델/실행 sizing 코드를 재구현하지 않는다.


실제 제한 재생성에서 비교0건의 빈 portfolio가 `{}`/평가됨으로 표시되는 추가 결함을 발견했다. 빈 비교는 null/미평가로 수정하고, 정상 no-fill은 해당 날짜의 비용 차이를 포함한0과 구분한다. 새 계약 generation으로 최종 검증·immutable successor 배포·재생성을 수행한다. 최초 generation의 PASS를 최종 source의 증거로 재사용하지 않는다.


## 최종 closure record

- Source review/수정/재검증: **645 PASS**, compile·affected Ruff F/E9·두 wrapper bash-n·diff check·print-only parser PASS. Selected immutable source의 public compact orchestration8 PASS(32 deselected). 검증 원문은 `tmp/compact-auxiliary-paired-20260918/compact-final-tests.txt`, `pytest-selected-compact.txt`, `validation.json`을 따른다.
- Atomic push: source `89cfb622f3c337d6ab156567aca24b50b8530703`를 origin/main 및 `review/compact-paired-economic-20260918`에 push했다. Selected managed root는 `/home/ubuntu/KORStockScan-runtime-releases/compact-auxiliary-paired-final-reviewed-20260918`; clean source/shared6·selector CAS·router print plan을 확인했다. 실제 Main restart/PID 전환은 실행하지 않았으며 actual_pid_consumed=false다. 배포 receipt는 `deployment.json`이다.
- 제한 재생성: 실제 source **2026-09-17**, publication **2026-09-18**, effective **2026-09-21**. 자료21건을 대사했고 비교 가능0건, provider calls0, 판정은 `source_contract_blocked`/`incumbent_preserved`다. 제외는 손절 거리 결손11·자연 응답 계약 불일치9·후행 경로 미확정1이다. ΔEV·portfolio 일별 순익은 모두 **null**, 유효 비교 후 no-edge0건과 구분한다.
- 다음 적용 정책: [9/21 Main policy](/home/ubuntu/KORStockScan/data/runtime/mechanistic_entry_policy/policy_2026-09-21.json), bundle `4d4bce68f1e27fe50afab4b24645406d469d701326a7bc86b91d2a121d737332`, `entry_machine_auxiliary_compact_v3` 보존. 기존 machine/AI 및9 scope가 유효 incumbent과 동일함을 확인했다. 신규 경제성 후보 승격0이며 dated carry 생성은 양수 EV 실적이 아니다.
- 마지막 소비: calibration→optimizer→consumer→policy→Daily·EV·runtime approval·tower section→9/21 checklist→family strict의 동일 최종 generation을 확인했다. Family strict **PASS/issues0**, whole native DONE=false. 기존 summary의 unrelated 값과 원 status/generated_at, entry split의 원 보고서 SHA를 보존했다(`regeneration.json`). 9/17 원 native/resource 실패·다른 family·다음 PREOPEN/실제 PID는 closure로 위장하지 않는다.

잔여 경제성 acceptance는 원 물리적 stop/plan/quote 계약, existing owner의 운영 청산·실제 비용·자본/독립 model 검증, reviewed runtime inference 원화 차이, current compact forward holdout과 적용 버전 자연 COMPLETED 비용 후 원장이다. Owner 모델 미지원은 시간이나 단순 표본 증가로 해소되지 않는다. ETA=null. 전체 legacy/holding 연구·native chain/PREOPEN·performance sweep·주문·외부 sync를 실행하지 않았다.
