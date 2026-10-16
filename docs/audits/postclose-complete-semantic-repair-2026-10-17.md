# 장후 전체 생산자·소비자 정밀 수리와 다음 기동 준비

원천일은 2026-10-16, 다음 영업일은 2026-10-19다. 점검 시작 선택은 b8ca6f665이며 실제 Main은 EOD 후 자연 정지 상태다. 10/17 당일 체크리스트는 없고 10/19의 기존 실행 owner로 인계한다. 이 문서는 사용자 지시의 구현·리뷰·재생성 작업 기록이며 마지막 절의 native 영수증 전에는 완료를 주장하지 않는다.

이전 검토는 수량의 native terminal과 부모 유지 결과를 확인했으나 실제 fact 생산 세대와 입력 제외를 충분히 대사하지 못했다. dispatcher 7개와 direct summary 9개는 전체 작업 모수가 아니다. 설치 cron·wrapper·내부 side producer로 확인한 34개 논리 작업을 아래와 같이 다시 대조했다. 새 job·stage·서비스를 만든 숫자가 아니다.

## 확정 결함과 수리 범위

| 계약 | 재현 / 보완 | 검증 및 권한 |
| --- | --- | --- |
| IQ171 대용량 fact 입력 | 작은 native dependency와 bounded scalar metadata로 원 census run/projection/cost를 검증한다. 93/250MiB sidecar를 4MiB 제한 앞에서 거부하던 오류를 수리한다. | 단순 상한 인상이나 거대 JSON decode 없이 작은/큰 표현·압축·손상·세대 변경을 대사 |
| fact 생산 순서와 결속 | 임시 report의 census에 fact를 연결한 뒤 정식 postclose snapshot으로 바꾸던 반복 결함이다. 정식 completion prefix를 먼저 생성하고 source-bound fact → 수량 평가 뒤 AI 입력 작성 종료 후 holding suffix를 생성한다. | 원 snapshot/census/cost에 봉인한 작은 fact projection, top300 표시 전에 전체 fact 모수 보존, DB DELETE 전/commit 전 검증과 rollback |
| IQ172 atomic 실행 | 감사 문서의 68be 기준 날짜/0행 ready 결함은 후속 272/c63/b8에 이미 반영돼 있다. 최신 표현에서 producer valid와 retained/excluded/미관측을 재검증한다. | 원 plan/leg/probe identity와 8 plans/10 orders를 기존 검증 원본과 구분; 새 사실을 만들지 않음 |
| IQ173 수량 의미 판정 | 경제 원천 결손을 valid_empty로 표시하던 조건을 수리한다. fact 전체·COMPLETED·원천 제외·경제 적격·정책 PID·전용 bundle 관측을 각각 공개한다. 비영업일 기본 sweep도 마지막 완료 원천일을 점검한다. | unknown invalid exclusion도 source gap, 미완료/다른 owner/기준일 밖 정상 제외와 구분. 최초 정책에 새 경제 승인 gate 없음 |
| IQ174 실제 비용 | completed5와 원 완료 모수의 배분 실패를 record/order별로 대사한다. 삼성 10원·HPSP 20원 공식 일지/주문 필드 합계 차이와 다중 포지션을 보존한다. | 공식 upstream 현재953e5dbff123f437ab4d11a78a95191a685eb51f의 spec/core/Postman을 재확인. 새 API·임의 배분·actual 비용 모델 대체 없음 |
| IQ175 capture lifecycle | 후행453/finish1의 미종료5를 조기 fixed exit2와 native PID drain3에 연결한다. 시작/종료/교체/정리/shutdown/다음 PID의 dead-process 관측을 기존 큐와 작은 영수증으로 기록한다. | queued와 durable·원 PID/attempt/plan을 분리. 과거 finish를 만들지 않고 후보별 관측 horizon을 평가하며 짧은 관측을 전20분 부족으로 일괄 폐기하지 않음 |
| all-scope trailing | holding 연구의 코드 해시가 최신 AI/실행 코드와 달라 10/19 실제 reader가 거부했는데 전체 준비 PASS가 이를 설명하지 못했다. 현재 코드·target·봉인 세대의 작은 관측을 summary/detector로 연결하고 원 producer를 갱신한다. | 작은 관측은 full native replay가 아니다. 실제 selector/bootstrap 검증은 원 native verifier 유지, optional 연구는 기존 부모 유지 경계 보존 |
| WS 공식 master | 경제 원천 report는 당일 canonical payload를 가졌지만 standalone master 발행이 빠져 9/16 metadata가 소비됐다. 기존 verified payload와 원 공식 metadata 바이트를 대사해 기존 발행 파일을 생성한다. | 네트워크·퇴역 collector 재생 없이 기존 원본만 사용. 잘못된 날짜/원천/authority/동일 경로 충돌은 거부 |
| Parquet identity/보존 | 같은 record·시각의 다른 stage/content가 합쳐질 수 있는 식별자와 같은 집계만 보는 shadow 검증을 수리한다. native ID 또는 전체 원문 fingerprint, 정확 중복/충돌/날짜 제외, source→output 보존과 실제 출력 바이트를 검증한다. | 실제 10행 차이는 날짜 필터 제외이며 10건 유실로 주장하지 않는다. 현재일 원천 식별 비교와 기존 3일 집계 비교 범위를 공개하고 불일치를 실패로 전파 |

## 전체 작업별 최초 대조

수치는 원 관측 시점이다. 재생성 뒤의 판정과 동일 바이트/소비 결속은 마지막 검증 JSON으로 대체한다. 원 실패와 이전 산출물은 그대로 보존한다.

| 작업 | 실행 성격 | 원천·제외·적격 / 마지막 소비자 |
| --- | --- | --- |
| EOD common daily/venue eligibility | scheduled | stored3904 official venue rows; EOD short history exclusions4; must retain actual original EODreceipt; actual EOD/DB consumer |
| market panic breadth | wrapper enabled | sample65=indices2+industry63; bothmarketsready; risk source-only; no economic tuner |
| observation quality preflight/final | wrapper enabled | 344472 retained; originalbad6excluded; machine58=35+16excluded+7quarantine; machine/aux/cancel/split/WS sources |
| rising missed feedback | wrapper enabled | retired dedicated scout not active; native source-only feedback remains; rising classifier |
| Main machine policy | registered native stage | separate62partitions/22scopecomparisons/48operatingcells/128nativecontractscopes; future19 staged machine bundle; PIDpending |
| economic reference and symbol master | machine prerequisite | 7815eligiblepairs=2605symbols*3venues; canonicalmasterverified2605; DEFECT standalone10/16masterpublicationmissing; WS/allscope usemissing/stale master |
| official completed cost freeze | wrapper enabled boundedwarning | actual allroundtripcostknown0; do notzero aggregate/cyclegap; exactfact/cancel/split/holding |
| execution fact sync | wrapper enabled DBrefresh | 8facts=completed5+holding3; costeligiblecompleted0/excluded5; crossentrycompletedcensus9; actualquantity/scalein/holding outcomeconsumers |
| scale in AVG_DOWN split | wrapper enabled | DBreceipt_confirmed AVG_DOWN positivefill inventory0; factprojection empty; skipped_no_actual_fill and unchangedparent; notinitialBUY9 |
| pre-submit delay | registered native stage | 231cells/default0/nonzero2 unchanged; nativecode/sourcecheck then future19 candidate |
| entry split | wrapper enabled | raw sizing9=8plans+1deferred; currentatomic8plans/10orders; fullwindow28attempts26intents distinct; IQ172fixedb8 emitted_date/conservation; economicsunknown |
| outcome labels | registered native stage | 34=29mature+5partial; exact supplement20/hashmismatch14; fixedelapsedmissingpaths sourcegap; nofakefutureETA |
| entry cancel wait | wrapper enabled | 9currentresearchparents;3currentcustodyopen;6historicalresiduals unresearched; atomiccustody3known; terminal/costhistorysourcegaps retained |
| initial quantity refresh | wrapper mandatory conditionalcurrent | natural sizing9 butreportedpriorvalid_emptylineagereadyincorrect;6typeparent profiles unchanged; IQ171IQ173 repairs delegated; costeligible0 notnoactivity |
| pipeline verbosity parity | wrapper enabled | 344472raw/211076highvolume; full211076=producer211076; commonminute211074 each; excludedtails2each; v2_shadow_parity_pass; suppressionfalse |
| legacy machine compatibility calibration | registered native stage | legacydiagnostic5325natural; comparisonpopulation0; wrapperreportcomplete!=economiccomplete; calibration + microstructure context boundexactSHA |
| microstructure compatibility context | existing calibration sideproducer | 5325cases=173costadjusted+5152excluded; inputs11599capture; sourcecalibrationbyteSHAmatch; counterfactualdiagnostic only noactualEV orpromotion |
| auxiliary policy/replay | registered native stage | 100requests=47completed+53planned; common22/expected50pairs; storedresponseonly; future19 providerpolicycarried |
| Main AI prompt consumer | wrapper finalconsumer | 128scopehandoffnewready membershipnoPID; priorcohortfollowupnotapplicable; ready_continuous_reversal_handoff; noEVclaim |
| WS freshness/lookup attention | wrapper enabled finalized | 492280aggregated; sourcesmissing[] but exactofficialmastermissing; lookup2190fillmissing+20invalid; diagnostic_generated != integratedattention selection; masterpublicationdefect |
| rising missed classifier/TP1 | wrapper enabled | nativevalid_emptyverified; previouspublicpolicyfile16source15 distinctfuture19sourcepolicy; incumbentpreserved validempty noselectededge |
| postclose exit snapshot fourartifacts | wrapper mandatory | trade/post_sell/missed/holding4artifacts; completedcensus9strictcosteligible0; nativehashmanifest; allscopeextensiondependency mustalsoverify |
| all scope trailing/situation research | holding source subproducer | 504population/32partitions/20832scope; rawcensusincomplete; contractsealed7fe vsselected3a8; DEFECT future19 verify_extension/build_selectionhold_source_gap afterAIenginecodechanged |
| holding numeric vote | holding source subproducer | experiment_not_armed; no inventnumericexperiment; holdincumbent; 4familyfixture/nativeevidence |
| Main stop confirmation | registered conditional stage | 9cellsparentcarry; currentholding sourcehashbound; mustrefresh ifholdingextensionbytechanges |
| Samsung frozen sidecar | optional reportonly existing contract | userdeletedobservations; oldsource_sealinvalid retained; notmandatory startup; noautomaticrestoration |
| runtime approval summary | registeredsummaryconsumer | 9/9 directowners excludesquantity/trailing subconsumers; directcomplete econmixed/sourcegap; doesnotproveall activeworks |
| tuning control tower | registeredsummaryconsumer | summarysourceSHA includesquantitystage; noquantitysemanticinspection prior; towerpass !=perwork semanticcomplete |
| next checklist / strict/controller | native finalconsumer | oldrun16a preserved; finalsummarycodeb8; weekendexisting19OPENowners5; neednewsummarynativeclosure afterfixes |
| tuning parquet pipeline/post_sell/systemmetrics + shadowdiff | separate20:10cron | pipeline decoded344472→parquet344462, difference10 allmain_stop_source; selected single source scan found31204distinct legacyrecord/timekeys, zero duplicatekeys; datefilter disposition inferred from code, exactexcludeddate values pending native regenerate receipt. Post_sell9; systemmetrics 원 4742 읽기와 당일 출력1378은 날짜/시점 분모가 다르다. 현재10/16 raw1440 모두 시각유일, 출력 최대22:57 이후23:59까지62개가 후행 추가됐으며 재생성 대상이다. Existing3day10aggregatemetricsallmatch.; Synthetic confirmedweak identitysameclockstage/fields/nativeID collision; comparator10metricscannotdetectunmeasuredrowloss and exits0onfalse. Repair fullsource identityparity for currentdate and explicit CLI failure; native reusepending. |
| archive/storage cleanup | separatecron+nativefinalize | logicalsourcecompressionmetadata + nativeancestry preserved; nohistorydeletionor fakegreen |
| market weakness advisory research | separateevery40minnightcron | source16 completed_with_source_gaps; native47natural58binding34; replayepochunverified488114; noMainpolicyorretiredorders; unknownoutcomesretained |
| nextpreopenprepared/fullverifier | nativefinalization | preparedPASSfuture19selectedb8 actualPIDfalse; doesnotexecute futurePREOPEN per-family publisher; confirmedtrailinggapescaped |
| 시장기회 최종 진단 | 기존 optional report-only producer | 19:45:26 보고서 뒤 19:50/19:55에 raw 8 snapshots/1600 observations 추가. 기존 raw와 당일 공식 master로 --write만 재생성한다. Main/holding 필수 consumer와 별개이며 --capture·새 gate·퇴역 worker 복원 없음 |

## 리뷰·증거와 재생성 원칙

- 변경은 별도 작업트리에서 구현 → self review → 독립 교차 리뷰 → 보완 → 표적 검증을 반복한다. DB 원천 변경은 대상 날짜의 전체 모수/계획 payload를 확인하고 원 source/cost 변경 시 rollback한다. actual 결손은 NULL, 합계가 실제로 0인 적격 거래는 0으로 유지한다.
- 정식 완료 prefix는 한 번 생성하고 동일 세대로 fact와 수량을 연결한다. holding/trailing은 마지막 AI request/payload/decision 작성 이후에 생성하며 앞선 prefix를 다시 만들지 않는다. 원 scope/date/policy·source quality·주문/안전 guard를 유지한다.
- 이후 영향 생산자부터 summary → tower → checklist → strict --require-summary-handoff → native controller/finalization → 독립 full detector → next-preopen current_full_contract 순으로 닫는다. 잘못된 과거 해시를 새 코드 실행으로 재라벨링하지 않는다.
- 승인된 다음 기동용 선택만 갱신한다. 주말 매매 bot 기동, 새 provider/API/주문, threshold/cap/가격/수량 변경, 퇴역 원천 복원 및 외부 Project/Calendar 동기화는 수행하지 않는다.

원 증거:

- [수량 최초 정밀 감사](initial-quantity-runtime-postclose-result-review-2026-10-17.md)
- [전체 작업 최초 대조](../../tmp/postclose-complete-repair-20261017/active-work-semantic-census-before.json)
- [비용·후행 원천과 실제 종료 근거](../../tmp/postclose-complete-repair-20261017/quantity-historical-cost-capture-diagnostic.json)
- [공식 비용 계약 재확인](../../tmp/postclose-complete-repair-20261017/official-cost-contract-inspection.json)
- [fact 생산자 독립 리뷰](../../tmp/postclose-complete-repair-20261017/bounded-fact-projection-independent-review.json)

## 코드 리뷰와 재검증 기록

- 27개 표적 모듈의 통합 검증은 2,851건 통과 후 압축 alias 기존 기대값 한 건에서 실패했다. 생산 코드의 원 논리 원천 계약은 동일 decoded SHA/크기·gzip CRC 검증 뒤 무손실 alias 전환을 허용하므로, 단순 동일 gzip 출현을 오류로 보는 오래된 회귀를 분리했다. 상이 원문 gzip은 실패하도록 유지하고, 동일 alias→원문 제거→상이 gzip 거부를 실제 native verifier로 검증했다. 해당 모듈 50건 통과 및 독립 리뷰 finding 0이며 운영 검증·정책은 완화하지 않았다.
- snapshot은 prefix/full 완료 namespace와 종료코드·성공 cooldown을 분리했다. suffix는 hidden candidate를 native 검증한 뒤 canonical을 원자 교체하며, 검증 중 원천 변경이면 failed candidate와 기존 canonical 바이트/부재를 보존한다. prefix→suffix의 물리 raw seal과 장후 완료 후 무손실 압축의 논리 원천 검증은 구분한다. 관련 115건 통과, 독립 phase 48건·wrapper 배치 2건 통과다.
- fact 생산자/수량 소비자는 260건, capture lifecycle 결합은 78건, WS master·Parquet 결합은 74건을 통과했다. 교차 리뷰에서 발견한 transaction 경합, 전체 fact 모수, pending/native 세대 구분, Parquet zero-output/출력 바이트 결속을 보완했다. 수량 health의 전체 native 평가 재실행을 제거하고 호출 내 동일 세대 metadata를 memo한다. current ancestry와 stage/report/evaluation/parent/following/timeout/candidate 결속, NULL·valid_empty 모순, committed pointer 바이트 한도, gzip alias·파일 교체·FIFO를 bounded 관측으로 검증한다. 전체 detector334건·독립31건 통과이며 `native_validated=false`, `bounded_contract_validated=true`로 full native 검증과 구분한다. 추가 phase regular-fd 수리도70건 통과했다.
- Parquet↔archive 후속 교차 리뷰에서 물리 파일 고정과 CRC→rename 사이 원문 결속 결함을 추가 수리했다. 원 JSONL binary stream의 CRLF/공백 포함 decoded SHA/크기를 봉인하고, 최종 archive inode에서 CRC/왕복 검증한 새 ctime 세대를 작은 receipt로 인계한다. 기존 ctime/size 없는 receipt는 그대로 보존하고 필요시 최초 CRC 검증만 수행한다. 관련167건 통과 및 독립 재검토 뒤 최종 통합 결과로 마감한다.
- 원 보고서·checklist·대상 DB fact/집계 17행은 `tmp/postclose-complete-repair-20261017/before-native-regeneration`에 보존했다. native source inode/ctime을 바꾸는 hardlink를 사용하지 않았다. 당시 cron routing8개와 release-set 검사도 통과했으며 거래 Main/PID는 정지 상태다.

최종 코드 게이트: 통합 pytest 2,919건 통과. 실행 중 마지막 compactor 소유권 수리로 source guard가 변경 파일 두 개를 검출했다. 이를 무시하지 않고 source SHA 차이를 기록하고, 최종 두 파일을 포함한 Parquet/compactor/Main-stop 독립264건을 재검증했다. 나머지 source SHA는 통합 검증 시작과 끝이 모두 같다. [검증 결속](../../tmp/postclose-complete-repair-20261017/final-validation-attestation.json), [최종 독립 리뷰](../../tmp/postclose-complete-repair-20261017/parquet-archive-stop-independent-review-final.json). Python compile·bash 문법·diff·print-only parser도 통과했으며 unresolved in-scope code finding은0이다. 실제 native 재생성/최종 선택·기동 준비는 아래 별도 영수증으로 마감한다.

최종 native 결과와 재검증 영수증은 아래에 추가한다.
