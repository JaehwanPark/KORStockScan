# Entry split 최종 재리뷰·정리와 다음 AI decision quality 분석

2026-09-18 KST. 사용자 승인: entry split 코드 재리뷰·수정·검증·관련 commit/push·immutable successor 배포 및 불필요한 과거 산출물 삭제. 다음 작업은 읽기 전용 분석이며 코드·정책·원천·API·재실행을 변경하지 않는다. 봇 재시작·주문·조기 PREOPEN 확정은 이전 금지 경계를 유지한다.

## 1. Entry split 재리뷰 결과

기존 ES0–ES6 구현과535건/소비19건 증거를 재사용하고 새 결함의 영향 경로만 수정했다. `build_entry_split_post_apply_performance`가 유효 real Main COMPLETED/cost/profit/정확 policy/PID receipt를 확보해도 capital/reserve 정보가 하나라도 없으면 완료 episode와 순익까지 전부 제외했다. 집계 회귀2건과 producer→집계 회귀1건이 수정 전 FAIL을 재현했다.

수정 후 정책/version별 중복 제거한 순익·frozen budget EV·tail은 평가하고, 노출 필드별 covered episodes를 기록한다. 누락/비수치/음수 노출은0으로 대체하지 않고 해당 합계를 null·source_gap·owner·closure로 반환한다. model error 미지원 null 및 비용/lineage/PID/정책 적용 필수 계약과 conflict quarantine은 유지한다. producer의 capital join 실패에서도 signed 완료 비용 receipt와 null 노출을 보존하고 별도 model_support_status/source_gap으로 승격을 차단한다. 실제 모델 net error가 계산된 COMPLETED만 comparable count에 포함한다. 이는 price/quantity/budget/guard/운영 청산 계약 변경이 아니다.

재리뷰에서는 기존 supported 경제성→model chronological holdout→candidate 별도 holdout→Daily/PREOPEN/장중 소비 및 unsupported/inactive fallback 계약을 다시 확인했다. 영향 회귀538PASS·소비19PASS, compile/diff/print-only parser 증거는 `tmp/entry-split-final-review-20260918/`가 소유한다. 기존 합성 활성 회귀는 자연 수집/EV 성과가 아니다. 실행 중 selected release 대신 별도 successor worktree에서 수정했다.

## 2. 과거 산출물 정리

최근20 source dates 바깥의 참조 없는 재생성 가능 Markdown30개/33,554bytes를 삭제했다. JSON148개(report76/policy72)와 generation·모델/holdout/outcome·현재 source9/17/prepared9/21 정책·rollback은 SHA 그대로 보존했다. active wrapper/열린 파일과 기존 refresh lock을 확인한 후 삭제했다. `cleanup-before.json`에 개별 경로·SHA·이유, `cleanup.json`에 보존 검증을 남겼다. historical JSON은 incremental/모델 재현 근거여서 단순히 오래됐다는 이유로 삭제하지 않았다.

## 3. 다음 작업과 실행 결과

선택 배포본 `deploy/run_threshold_cycle_postclose.sh`에서 entry split 직후는 `scalping.ai_decision_quality --date TARGET_DATE --mode postclose --write`다. inventory의 #76이며 다음 #77 R0–R3 연구와는 별도 단위다. 기계/보조 AI 실행 흔적과 원 prompt/request/payload, source-quality/context/promotion 계약 및 같은 venue/session 가격 경로를 사용해 기존5개 산출물을 만든다.

| 산출물 | source9/17 관측 결과 |
|---|---|
| control manifest | 전체 trace4578, 정확 control은 compact_v3/openai/gpt-5.4-nano의 KRX10건. 기타 stage 부재는 scoped input 상태이며 복원 권한 아님. |
| outcome labels |63개: pending25/partial18/mature20. pending25는 모두 source_quality_blocked·primary 부적격. |
| baseline |source eligible15 중 primary10분 결과14, primary pending1. KRX10/통합 애프터마켓4. |
| paired preparation |정확 요청10/결과0/실행false/비교0/승격false. candidate는 offline decision_quality_v2_6_entry. |
| candidate lifecycle |event/state/evaluable0. V2.14/V2.15 전용 adapter namespace의 상태이며 현행 compact/Main 체결0과 동일하지 않음. |

생성일은9/18 00:17:08 KST이고 원 평가일은9/17이다. 기존 native 로그의 해당 command exit0·52.893초·peak child RSS964,616KiB(약942MiB)를 확인했다. I/O의9,983,176은 child block operations이며 읽은 byte/행 수로 해석하지 않는다. 현재 코드의5개 산출물 validator도 오류0이다. 계약 PASS는 후보 실행/승격/실제 성과 PASS와 다르다.

## 4. 튜닝과 런타임 역할

이 단위는 원천/라벨/control baseline와 offline paired 요청을 materialize한다. 직접 AI 호출로 challenger를 실행하거나 정책/env/주문을 바꾸지 않는다. 원 요청/가격 경로는 후행 R0–R3·optimizer·consumer가 참조할 수 있지만 현재 기계-primary/AI PASS|VETO|CAUTION|INSUFFICIENT 정책의 경제성 선정은 기존 `ai_action_outcome_calibration`의 machine/compact case table→compact paired evaluator→optimizer/consumer→dated mechanistic policy→PREOPEN/PID owner다. generic BUY|WAIT|DROP challenger를 현행 compact auxiliary와 같은 런타임 후보로 취급할 수 없다.

최신 source audit는 machine4508(BLOCK2103/RECHECK1637/ENTER_NOW21/SOURCE_INVALID747), trace-assessed3341 + feature excluded419 + source excluded747 =4507로 분모를 보존한다. 전체4578 중 provider not called4515는 기계 non-entry/preflight를 포함하므로 전부 AI 원천 결손이 아니다. 실제 provider attempts63은 archived request/prompt/outcome63 모두 연결됐다. 현행 compact variant의 자연 호출은21(KRX11·통합 애프터마켓10), prompt partition2개 모두 measurable다. control10·baseline14·historical provider63·현행 compact21을 합치거나 동일 분모로 주장하지 않는다.

## 5. EV·순익 판정

baseline의 source_quality_adjusted_ev_pct −0.25559409535%는 같은 판단의 이후10분 `end_return_pct`에서 BUY는 경로 수익, WAIT/DROP은 비노출0을 사용한 평균이다. 실제 submit/fill·SELL·비용 차감 paired 경제성 또는 현재 policy actual net EV가 아니다. KRX10건 −0.60756483688%, 통합 애프터마켓4건 +0.624332758475%도 같은 진단이다. 진단 win rate7.142857%는14개 판단 중 양수1개이며 체결 승률이 아니다.

false_buy5/긴축 stop adverse-first5/놓친 target-first2는 원 판단 조사 단서다. stop/cost/capital lineage가 없는 상태에서 순익 개선으로 해석하지 않는다. primary eligible15의3분 entry quality 경로는14건 `exact_stop_distance_missing_or_invalid`이고 실제 적용 성과로 전환할 수 없다. paired 결과0이므로 challenger EV·ΔEV/순익은 null이고 후보 경제성 미확정이다. 최종 downstream source audit의 AI_PASS4는 submitted0·guard blocked0·rejected0·lineage_gap4, admitted terminal0이며 이4건을 유효 no-edge 또는 submit0의 경제적 실패로 확정하지 않는다.

## 6. 시간 대기와 구조 결손

| 구분 | 근거·owner·closure |
|---|---|
| 앞으로 자연 표본/holdout 축적 | 정상 영업일의 동일 prompt/bundle/venue/session 신규 판단·완료 비용 표본과 미사용 chronological window는 시간이 필요하다. 기존 compact/기계 evaluator owner에서 sample/coverage/독립 검증 후 dated policy/PID 및 rolling/cumulative cost 성과 확인. ETA=null. |
| 고정 과거 가격창 결손 |primary pending1은098460의9/17 10:38:37 판단;1/3/5/10분없고20/30/60분만존재한다. 기록된 ka10080 coverage가10:51부터이고 continuation page limit에 도달했다. 하루 더 기다려9/17 앞10분이 생성되지는 않는다. 원 가격-source owner의 해당 과거 same-route 창 backfill/coverage 입증 또는 source-gap 제외가 closure다. 이번에는 조회하지 않음. |
| context/semantic 계약 결손 |32개 KRX label의 canonical venue/session 불일치,20개 semantic validation 불통과,18개 nonlive/validator 미적용,10개 JSON/8개 response schema 비강제가 있음. 겹치는 counts라 합산금지. 대표 입력은 trace KRX와 canonical integrated venue 및 비어 있는 context projection이 섞임. source producer/schema/consumer가 원 exact payload와 대조해 잘못된 행/정규화/중복 projection을 구분하고 producer→consumer 회귀와 새 자연 valid 입력으로 닫아야 한다. 이미 유실된 원 필드는 시간만으로 복구 안됨. |
| 현재 역할과 legacy 평가 차이 |generic full decision challenger와 retired canary lifecycle은 현재 auxiliary PASS/VETO contract 및 실제 Main receipt와 다르다. 기존 compact owner에 필요한 원천/라벨을 연결하고 독립 정책 승격 근거로 legacy 결과를 사용하지 않는 것이 closure. retired adapter를 복원하지 않음. |
| terminal lineage4 |AI_PASS→final guard/submit/broker terminal 연결을 기존 sniper emitter/owner journal/sentinel에서 확인해야 한다. pending maturity0이어서 단순 성숙 대기가 아님. 실제 terminal receipt/hash/version join을 입증하거나 gap으로 격리. |
| preparation/result0 |이 command는 의도적으로 candidate provider를 실행하지 않으므로 시간이 흘러도 prepared request에 challenger 결과가 생기지 않는다. 현행 registered compact challenger evaluator의 지원 scope·guard·비용·독립 holdout을 통해 검증해야 하며 legacy 요청 자동 실행을 요구하지 않음. |

## 7. 유지 가치와 다음 판단

원천·날짜별 라벨·control의 scoped 품질 관측은 유지 가치가 있다. 현재 이 작업의 직접 비용 차감 EV 개선 기여는 입증되지 않았다. legacy paired 준비와 retired lifecycle의 반복 생산을 경제성 연구의 중심으로 유지할 근거도 없다. 다음 개선은 새로운 producer를 만들지 않고 기존 기계/compact evaluator에 분모·prompt partition·source/cost/terminal 연결을 결속하고, 위 고정 과거 결손을 valid-no-edge와 분리하는 순서다. 지원 가능한 자연 scope에서 비용 차감 paired 독립 holdout을 통과할 때만 현재 dated 정책에 승격한다. 다음 작업 구현/재생성/삭제는 이번 읽기 전용 범위에서 하지 않았다.

## 8. 증거와 한계

`tmp/entry-split-final-review-20260918/validation.json`, `deployment.json`, `cleanup.json`, `next-task-analysis.json`, `next-task-native-receipt.json`가 code SHA·회귀·원 산출물 SHA·source binding·배포 receipt를 소유한다. native source manifest와 현재 manifest 일치 여부는 analysis receipt에 기록한다. 전수 raw/활성 JSONL을 읽지 않고 기존 manifest·5개 bounded JSON·1MiB native log tail만 사용했다. 봇/PID/자연 정책 적용/실제 EV 개선은 확인 완료로 보고하지 않는다. 이전 source9/17의 prepared9/21 inactive keep-original 정책을 유지하며 과도한 장후/성능 재검사를 생략한다.
