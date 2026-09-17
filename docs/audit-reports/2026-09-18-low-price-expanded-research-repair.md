# 2026-09-18 저가주 확장 연구 결함 보완·배포 검증

- Owner: `LowPriceExpandedResearchRepair0918`. 사용자 승인: 결함 보완→코드리뷰/수정보완→검증→커밋/푸시→배포/기동. 구조적 결손·유의미한 비용 차감 EV 확인을 성능보다 우선한다.
- Base: selected `677ffa694decb0797a66e947bedc17ec4cac479d`; PYRAMID·AVG_DOWN 개선을 포함한 기준 릴리스를 보존한다. 기존 workspace의 병행 변경은 포함하거나 덮어쓰지 않는다.

## 구현·리뷰 결과

1. 86MB 연구 보고서를32MiB로 거부하던 정책 생성/재로딩을 생산자의 기존128MiB stable regular-file reader로 통일했다. 날짜/스키마/내용 해시/발행/소유권/미청산/승격 가드는 유지한다.
2. 보고서 무손실 compact ASCII 저장과 파싱 전 byte buffer 해제로 같은 전체 모집단·경제 필드를 유지하며 메모리 중복을 줄였다. 신규 패키지·생산자 모듈·성능 가드·grid/비용/표본 기준 변경은 없다.
3. 공동 평가 missing-reference 목록을 정렬하여 JSON 저장/재로딩 후 입력 해시가 변하지 않게 했다.
4. 기존 로직 개선 추천은 `source_only_existing_logic_review_required`, 소비자는 기존 연구 owner로 전달한다. 자동 확장 미지원 lane을 자동 승격 가능으로 표시하던 모순을 닫았다. native 추천 ID/spot/custody/quantity를 보존하고 신규 매매 연결을 만들지 않는다.
5. 비교 EV 결손을 `baseline_custody_censored`/`baseline_no_completed_outcome`으로 표시한다. EV uplift는null을 유지하며 후보 replay 값을 실제 이익으로 바꾸지 않는다.
6. 원천 실패에 실제 관측 날짜/품질 metadata를 보존하여 7종목의 결손을 진단할 수 있게 했다. 기존 API 요청/응답 파싱·continuation·provider budget·auth·WS/FID/order flow는 변경하지 않았다.
7. 필수 preflight의 legacy4-field/current5-field generation 비교 오탐을 수리했다. 지원 필드/타입/claimed ctime/변경 탐지·archive digest cache를 검증하며 불명확한 generation은 거부한다.

## 검증·유의미한 결과

- 첫 관련5개 suite259 PASS. 리뷰에서 추천 소비/EV 결손 표현을 보완하고 재리뷰/회귀 검증261 PASS. compile 및 scoped git diff --check PASS. 신규 production Python module0.
- 원본9/17 보고서/분석/동결 추천 ledger는 보존했다. successor 보고서는 `data/report/low_price_two_leg_expanded_candidate_research/repair_20260918/low_price_two_leg_expanded_candidate_research_2026-09-17.json`이다.
- native reader/recommendation builder/contract writer로 기존 경제 결과를 전달 갱신했다. 모든 profile hash·원 추천 ID·candidate/current economics·spot 불변을 확인했다. 전체204종목 raw replay/grid 재계산·market API/provider call0. 약40.31초, 결과86,229,776bytes; 이는 새 경제 분석이나 새 실현 이익이 아니다.
- 팬오션028670 오전: 비용0.23% 반영 후보 replay EV+0.280032%, holdout signal4/완료다리5/미청산1. 비교 기준은 미청산 이월1로 baseline EV/EV uplift null, `baseline_custody_censored`. 로직 검토 추천1, 신규 종목 추천0, 신규 승격0, 기존 profile3 보존.
- 실제 native 정책 생성+write+load를 scratch publication에서512MiB unit으로 검증했다. 별도 native load 검증 RSS441,492KiB/약431MiB,2.40초, rc0. systemd가 출력한 MemoryPeak256KiB는 Python RSS와 불일치하여 peak 판정에 사용하지 않았다. 기존 서비스 환경으로 native owner 권한3개를 별도로 확인했다. package install/real order test0.

## 남은 수집·경제성/운영 경계

- 같은 날짜widget 공동 평가 입력은 부재하므로 joint gate는 `allocation_blocked/exact_date_joint_peer_missing_or_invalid`, combined EV/net null이다. peer 생성 전 이 재실행 성공을 공동 자본배분 PASS로 쓰지 않는다.
- 미청산·7종목 과거 결손은 의미를 변경하거나 거래를 만들어 해소하지 않는다. 다음 정상 수집의 실제 source/수량/BBO와 maturity를 확인한다. 신규580개 사전등록은580종목 또는 실제 수집 성공의 뜻이 아니다.
- 9/17 전체 native chain의 strict/controller/finalization/정지 cron 복원은 별도 OPEN이다. 이 배포가 전일 체인 DONE이나 Main PID/PREOPEN 승인 성공을 만들지 않는다.
- 이번 scoped 배포는 current selected 후속 commit을 새 immutable root로 발행하고 원래 low-price auto-expansion unit의 실행 root만 갱신한다. 같은 서비스 환경/512MiB·CPU/Restart/interval/owner/custody/주문 가드는 유지한다. 실제 selector/root/PID/소비 결과는 아래 후속 receipt에 별도 기록한다.

## 배포·기동 실소비 확인

- Code commit: `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`, branch `fix/low-price-report-repair-20260918`; remote SHA 일치로 push 확인. 새 immutable release: `/home/ubuntu/KORStockScan-runtime-releases/low-price-research-repaired-20260918`. 이전 selected677ffa의 PYRAMID/AVG_DOWN 변경을 부모로 보존했다. router selected release/source clean/share 경로 검증 PASS.
- 현재9/18 동결 정책을 successor 보고서로 교체하는 native publication은 `research_same_date_publication_conflict`로 거부됐으며 정책/발행 manifest는 바뀌지 않았다. guard를 우회하지 않았다. successor는 연구 handoff/진단 증거이며 현재 서비스가 읽는 보고서는 원본 SHA98deba85603155f3b39fb291f205682c576c4ea4f06b9c7de07f5ba5c8242a3f이다.
- 실제 원본 정책 native load는512MiB unit에서 rc0/2.57초. Python ru_maxrss525,724KiB는 프로세스 RSS이며 cgroup 한도와 동일한 peak 계측으로 취급하지 않는다. 실제 service --check-active도 같은 기존512MiB와 기존 owner 환경에서 PASS. earlier scratch의431MiB는 successor 보고서 검증값이다.
- 기존 unit의 실행/검증 root만 소유한 새 drop-in으로 갱신했다. 원래17개 drop-in 해시·EnvironmentFile·MemoryMax536870912·CPUQuota250ms·Restarton-failure·interval6초 보존. Main이나 다른 소비 서비스, 정지 cron은 재시작/변경하지 않았다.
- 실제 `korstockscan-low-price-two-leg-auto-expansion.service`: active/running, PID41757, cwd 새 release, native episode receipt `data/runtime/machine_research_closed_loop/consumers/episode_2026-09-18_41757.json`, accepted profile3/owner activation validated, policy hash5cd93e2f3520ac0a420a10fc022b523036736e044d1ae9b9961df6ba8cdb89cc, 신규 승격0. 두 차례 상태 관측에서 NRestarts0; 후속 MemoryCurrent148,824,064bytes. 이것은 서비스 소비 확인이며 실제 주문·체결·수익 증거가 아니다. selected manifest의 Main actual_pid_consumed는false를 유지한다.
- `tmp/low-price-report-repair-20260918/deployment-receipt.json` 및 service-owned-dropin.json/service-before.txt/selection-before-low-price.json에 변경·복구 경로를 보존했다. 복구 시 다른 세션 후속 selector/override 여부를 먼저 비교하고 이번 소유 drop-in/선택만 되돌린다.
- canonical print-only backlog parser에서 stable owner1개 확인. runtime follow-up audit commit은 code commit과 별도이며 immutable code root를 옮기지 않는다.

## 잔여 결손의 owner·다음 조치·종결 기준

| 결손 | owner/evidence | 다음 조치·종결 기준 |
| --- | --- | --- |
| 고정9/17 widget 공동 입력 부재 | widget 연구 producer / `joint_inputs_widget_2026-09-17.json` 부재 | 선행 widget producer가 같은 날짜 native 입력을 생성한 뒤 joint 검증 재실행. 날짜·내용 해시·권한 확인 및 비용 차감 combined EV/net 생성이 종결 기준. 단순 대기만으로 고정 날짜 입력은 복구되지 않는다. |
| 팬오션 baseline custody censoring | 저가주 연구 owner / successor economic_comparison_status=baseline_custody_censored | 기존 held 이월과 청산 결과를 보존하고 다음 정상 수집의 완료·비용 유효 결과로 paired 비교한다. candidate와 baseline EV 및 uplift가 모두 유효해야 개선 폭을 평가할 수 있다. 현재 null을0으로 바꾸거나 carry를 지우지 않는다. |
| 7종목 원천 결손·prospective maturity | 해당 원천/prospective 생산자 / source_failure_details 및 원 candidate registry | 정상 거래일 실제 날짜·BBO/수량·원천 성공을 검증하고 유효 수집창을 누적한다. 같은 실패 재요청을 반복하거나 과거 bar를 합성하지 않는다. 자연 생성/원천 계약/표본 충족을 별도로 확인하며 ETA는 미확정. |

이번 구현·리뷰·검증·push·배포·서비스 기동은 종결했다. 자연 수집·비교/공동 EV 및 전일 전체 postclose chain은 위 증거가 갖춰질 때까지 OPEN이다.
