# 10/15 장후 origin 부모 검증 복구 검토

대상 source/publication은 `2026-10-15`, 다음 적용일은 `2026-10-16`이다. EOD는20:56:31 `completed_with_warnings`, 당일DB2,622행·수집 대상2,626개·원천 부족4개로 종결됐다. 원본과 미수신 종목의 과거 이력을 보존한다.

## 결함과 수리

`main_machine_policy`의 원 실행 `c093f14ab2c24ec89a2ce67d67c37679`은21:03:10 `command_exit:1`로 실패했다. 승인된 누적 등록 `c15491190e72…`의 origin `cfa070c1e…`가 현재 selector와 다른 상황에서 `active_policy_code_reader_root_changed`가 발생했다. 현재 선택본 `77eaf86fe…`는 같은 부모 `1f069c6894b5…`를 엄격 검증하지만, 봉인된 origin을 현재 live reader로 다시 실행하면 실패했다. 다음날 activation도 같은 검증 함수를 소비하므로 장후 성공만으로 수리를 닫지 않는다.

기존 `continuous_reversal_policy_v6._attested_activation_parent` 안에서만, 이 displacement 또는 명시적 v4/v5/v6 코드 변경 오류에 한해 origin의 원래 dated 코드 인계 영수증을 다시 검증한다. 원 origin의 Git commit·clean source, 요청 날짜, current pointer SHA, 원 generation/bundle, 승인·봉인·정책 비재선정·provider 미호출, 전체 원천 및 코드 해시·코드 membership과 검증 중 교체를 확인한다. 일반 원천 오류는 우회하지 않는다. live loader, 등록안, 부모/보조 membership, provider, 주문·수량·보유·안전조건은 수정하지 않는다.

실제 origin의 보존 영수증은 원천847개·코드37개 해시가 일치했다. 수리한 실제 누적 부모 로더는 원 등록안·포인터를 변경하지 않고 동일 부모를 반환했다. 38가설의 기존 승인 등록과 미등록 추가12가설은 별개로 보존한다.

## 검증

- 원 코드에서 현재 reader displacement 실패를 재현했다.
- 날짜 변경·원천/코드/부모/승인/날짜/포인터/봉인/membership/중복 hash 충돌·영수증 결손 거부 회귀와 관련 원천·정책·누적 등록·PREOPEN 검사310개가 통과했다. 첫 실행의1건은 격리 작업본 `.venv` 링크 부재였으며 프로젝트 환경 연결 후 해당 실제 subprocess 검사가 통과했다.
- 현재 선택본과 수리본의 고정 workload는128 scope·76,800행·607개 신호이며 signal SHA `72a8e589d1c1288f684d16c8aa66bcf5d1787671358ce7063551627fef0e2d0d`가 일치했다. 코드 변경은 해당 v6 부모 검증 파일 하나다.
- Python compile·`git diff --check` 통과. 문서/owner는 print-only parser로 확인한다. Kiwoom wire 변경, 패키지 변경, provider 호출·주문·매매 재기동은 수행하지 않는다.

근거는 [EOD 대사](../../tmp/postclose-monitor-20261015/eod-review.json), [검사 원본](../../tmp/postclose-monitor-20261015/parent-custody-tests.log), [subprocess 재검사](../../tmp/postclose-monitor-20261015/parent-custody-subprocess-recheck.log), [신규 동일성 대조](../../tmp/postclose-monitor-20261015/parent-custody-native-parity-provenance.json)다. 이 검토는 코드 수리와 읽기 검증이며, 배포·장후 terminal·10/16 prepared/PREOPEN/PID·실현 성과를 대신하지 않는다. 운영 후속은 기존 `CumulativePolicyAdoptionDeployment1015`와 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

## 비용 세대와 최종 checklist 인계 수리

부모 검증을 복구한 실행 `e286ad714ddd438e88dc3c83a2f3d5fe`에서 분석·정책6개 stage가 모두 성공했다. 승인된38가설은 next-session 후보 `a09735ace81a…`에 반영됐으며128 scope 중22개 등록 범위가 일치한다(15개 변경·7개 승계). 원 현재 포인터는 유지됐다.

그러나22:13:49 checklist 생성이 `initial_quantity_refresh_stage_invalid`로 실패했다. 원 수량 generation `b6cf05ed0edd…`의 엄격 검증은 `quantity_fact_cost_generation_changed`를 반환했다. 공식 holding 비용 수집이 이미 fact와 수량이 비용 세대를 결속한 뒤 실행돼 생긴 선후행 오류다. 비용 결손을0으로 바꾸거나 검증을 느슨하게 하지 않는다.

기존 비용 수집을 fact 생성 앞으로 이동하고 호출 수·명령·timeout·경고/unknown 의미를 보존한다. 최종 resume의 허용 실패 지점에 checklist 생성 실패만 추가하며, 원 native 명령 증명·6개 stage·snapshot·현재 수량 영수증 검증은 그대로 유지한다. 복구는 현재 비용으로 fact와 직접 downstream·수량을 다시 결속하고 최종 handoff를 재개한다. 원 수량·원 실패·정책/보조 원천과 기존 승인 membership을 보존한다. wrapper 회귀·`bash -n`·print-only parser로 이 보완을 검증하며, Kiwoom 요청/응답·provider·매매 프로세스·주문/수량 guard를 변경하지 않는다.
