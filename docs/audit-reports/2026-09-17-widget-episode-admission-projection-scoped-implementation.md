# Widget/episode admission 원천 대사·compact projection 부분 구현 — 2026-09-17

## 1. 판정·범위

사용자의 잔여 구현·반복 리뷰·검증·commit/push·배포 지시에 따라 전체 폐루프 계획의 **F0/C0 및 F1/C1·P1 선행 원천 계약 일부**를 구현했다. 전체 F0–F5/C0–C8/P1–P6 완료가 아니다. 신규 종목 catalog 자동 편입·전향적 seed 이중-window·joint capital 선정 gate·next-date 실제 소비/성과 회수는 미완료다. 기존 R1–R5 코드 closure는 유지한다.

운영 owner는 당일 checklist의 `KiwoomCommonHealthOpportunityCostAcceptance0917` 한 개를 재사용한다. source-only admission readiness는 live signal/policy selection/주문 권한이 아니다. 기존 기계 진입·compact AI·가격·수량/leg·scale-in 및 main/widget/episode/manual custody와 broker/hard safety는 변경하지 않았다.

## 2. 발견 결손·수리

1. 기존 handoff는 `liquid_common/top_20/forward_exact`만 대사했다. Primary recall 분모는 그대로 보존하고, 별도 admission ledger에서 모든 forward panel/window의 native ID·원본 location·행 hash·scope를 보존한다. Retrospective panel은 admission에 쓰지 않는다. 같은 native projection은 중복이며, identity/원래 candidate 증거가 상충하면 첫 행을 winner로 삼지 않고 해당 ID를 source gap으로 남긴다.
2. 오늘 census canonical JSON은 점검 시 **41,371,316 bytes**로 기존 4MiB reader 상한 밖이었다. 원본을 크게 읽거나 상한을 올리는 대신 기존 census `write_report`가 `<canonical stem>.admission.json`을 함께 발행한다. 새 CLI/collector/cron/report producer는 없다. Full JSON byte SHA·file generation(device/inode/size/mtime/ctime), projection digest 및 원본 행 hash를 결속한다. 원본→projection→MD는 date별 nonblocking publication mutex 아래 원자 rename/fsync로 발행한다. 경쟁 writer는 기존 자료를 덮어쓰기 전에 실패한다. Parent 교체·append·sidecar 손상/alias/nonregular/oversize는 source gap이고 구 PASS/full fallback으로 가리지 않는다.
3. Widget CLI의 per-symbol checkpoint에서는 census 전체를 반복 decode/복제하지 않고 final combined report에서 한 번 읽는다. Episode는 admission evidence phase를 경제성 replay fingerprint와 분리하여 canonical census generation이 바뀌어도 정상 cached 경제성 grid를 재실행하지 않고 ledger만 갱신한다. helper revision 변경은 기존 report cache를 무효화한다.
4. Admission은 official KOSPI/KOSDAQ common-equity binding·exact source date·원래 forward candidate timestamp/명시적 bool을 확인한다. Widget KRX regular와 episode KRX/NXT regular overlap lane을 구분한다. Root generation clock이 있으면 그 이후 candidate를 배제하며 없는 clock을 증명된 것으로 표시하지 않는다. 미래 순익·actual fill·AI/submitted 후행 stage로 admission 우선순위를 정하지 않는다.

원장 보존식은 `input projections = admitted + deferred_capacity + source_gap + excluded_by_contract + duplicate_projection`이다. 기존 catalog 안의 causal candidate도 `pending_consumer_source_validation`; 신규 causal symbol은 `pending_catalog_admission / research_catalog_capacity_contract_pending`으로 남긴다. Catalog 변경·수집 용량·executable 검증 없이 자동 등록/승격됐다고 표시하지 않는다. 빈 input은 full-session valid-zero 증거가 아니다.

## 3. 기대효과·자동화·조건

놓친 기회의 연구 전달 누락과 초과 크기 census의 전수 source-gap 처리를 줄이는 **선행 원천 수리**다. 작은 비용 후 수익을 빈번하게 만드는 정책 자체나 실제 참여/순익 개선을 입증한 것은 아니다. 체결 거래만 admission하거나 positive outcome만 선택하지 않으며, 검증된 미진입 원래 candidate를 후속 연구 대상으로 보존한다.

기존 census cron의 자연 report refresh가 projection을 자동 발행하고, 기존 widget/episode 장후 consumer가 자동 읽는다. API 요청/Provider 호출·호가 신선도·quantity/depth·EV/tail/window floor·timer·실주문 guard는 변경하지 않았다. 불합리한 4MiB full-report 병목은 reader 상한 완화가 아닌 writer projection으로 해결한다. Capacity/seed/joint contract는 미구현 상태이므로 제거해서 임의 승격하지 않는다.

## 4. 리뷰·검증·배포 상태

반복 리뷰에서 malformed primary/master field의 전역 예외, 후행 AI progress에 따른 native dedup 오인, admission 변화에 따른 전체 economic replay, publisher 경쟁 write를 보완했다. Synthetic large-parent fixture에서 parent >5MiB/projection <4KiB, 단 한 번의 sidecar read·native count parity·원본 행 hash 보존·parent rewrite/corrupt/race 차단을 검증했다. 운영 41MiB 원본 full scan/API/Provider/production 보고서 재생성은 하지 않았다.

Workspace의 12개 관련 suite **601 passed**를 확인했다. Compile·shell/diff check·print-only parser의 기존 current owner 유일성1도 통과했다. 최종 supplemental fix 및 managed release 재검증·unit routing receipt는 아래에 추가한다. 매매 프로세스 변경이 없는 source-only scope이며 main 및 독립 trader/episode PID는 재기동 대상이 아니다. Evaluation 20:10/final refresh 21:15는 아직 예정 전이므로 unit pin 변경과 실제 자연 실행을 구분한다.

## 5. 잔여·다음 acceptance

- F0: 전체 contract/performance oracle, N/D/G/K·요청량/read bytes/CPU/RSS/critical-path 실측 미완료.
- F1/C1–C2/P1: budgeted catalog writer/reader·automatic research admission·coverage debt·source index의 나머지 구현 미완료.
- F2/C3/P2: 과거 seed를 역적용하지 않는 신규 seed bootstrap·prospective windows/executable fact index 미완료.
- F3/C4/P3–P4: exact allocation snapshot과 공동 자본 gate·state-aware incremental replay 미완료.
- F4/C5–C6/P5: versioned publisher/reader migration·next-date activation/actual acknowledgement 미완료.
- F5/C7–C8/P6: version attribution 회수·strict handoff fixed point·storage/scale benchmark·mature economics 미완료.
- 기존 common-health 통합계획 U2–U4 전수 consumer parity/U5 및 나머지 자연·경제성 acceptance도 이번 부분 구현으로 닫지 않는다.

오늘 자연 producer가 만든 projection의 크기·parent binding·native conservation, 20:10/21:15 동일 generation 소비·각 unit terminal을 확인해야 한다. 장중 기동 가능한 immutable source-only release와 next-date policy consumption/실체결 비용 후 EV는 별도 상태다.

## 6. 실제 배포 receipt — 12:18:38 KST

- Source/main commit `d395cf069271fcebed3c8204dfded5b155f916d9`와 managed branch `release/widget-episode-admission-20260917` 모두 원격 push 완료. Release root는 `/home/ubuntu/KORStockScan-runtime-releases/widget-episode-admission-20260917`다. 다른 세션의 wrapper/verifier/문서/generated 변경은 제외했으며 checklist는 이번 추가 한 줄만 선택적으로 commit했다.
- Workspace 관련12 suite601건, 마지막 supplemental targeted143건, managed shared-path 동일12 suite **601 passed**. 코드/import root 및 변경 module4개의 SHA 일치, source-clean·compile·3 wrapper shell 검증·diff check·print-only current owner1 확인. 이번 검토 범위 finding0이며 전체 계획 finding0/완료가 아니다.
- `korstockscan-samsung-widget-evaluation.service`와 `korstockscan-machine-microstructure-final-refresh.service`의 working directory/PYTHONPATH/project/python/ExecStart를 해당 root로 pin하고 daemon-reload했다. CPUQuota200%·MemoryMax512MiB/2GiB·timeout·timer20:10/21:15와 기존 기타 env/guard를 보존했다. 두 unit 모두 inactive/MainPID0로 **not_yet_due**이며 과거 Result=success를 오늘 실행 성공으로 세지 않는다. 조기 service start나 report 재생성은 하지 않았다.
- Main326500·widget trader327012·episode auto-expansion327094 및 메인 selector SHA `ebb089e169777e36c758d206f0d582aebb2e1582f538ca996d779362f5fb5f56` 모두 보존했다. 기존 research collectors pin도 보존했다. 매매 코드/PID 변경이 없어 broker/order API·Provider 호출·재기동은0이다.
- 오늘 projection은 점검 시 아직 미생성이다. 기존 cron의 다음 자연 report refresh(현행15:15/19:45 등)와 source finalization이 원래 cadence에서 발행해야 한다. 41MiB 원본 full scan/조기 재생성으로 이를 가장하지 않았다. Policy publication/actual consumer acknowledgement·자연 ENTER/SELL·비용 차감 EV/순익은 미입증이다.
- Scoped validation은 `data/runtime/runtime_release_validation/widget-episode-admission-20260917-d395cf06.json`; operating DONE이나 전략 승인 marker가 아니다. 원래 physical mount 자료는 `tmp/runtime_release_mounts/widget-episode-admission-20260917.AQXzJI`에 보존했다. Rollback은 두 unit의 이번17-z drop-in을 보존 위치로 이동하고 daemon-reload하여 기존16-z research root77abb524로 복귀하는 최소 범위다. 실행 중 여부를 먼저 확인하며 main selector/트레이더는 건드리지 않는다.
