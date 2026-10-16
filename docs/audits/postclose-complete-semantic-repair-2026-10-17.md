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
| 누적 수량의 이월 완료 전이 | 10/15 원 fact의 HOLDING4가 10/16 완료9건 안에 있으나 entry-day DB만 읽어 not_completed로 탈락했다. 원 DB·snapshot·영수증은 보존하고, 작은 완료일 projection을 정확한 ID/원 추천일/실제 BUY/owner/terminal/census/cost로 메모리에 결합한다. | 실제 대사 COMPLETED9/HOLDING7→COMPLETED13/HOLDING3. 평가일 이전·서로 다른 terminal·다른 owner·세대 경합은 거부한다. 명시된 추가매수 횟수는 단조성 검증 후 반영하여 초기진입 경제성에서 제외하고, 없는 횟수는 원 entry 관측을 유지한다. 비용 NULL은 그대로다. |
| IQ174 실제 비용 | completed5와 원 완료 모수의 배분 실패를 record/order별로 대사한다. 삼성 10원·HPSP 20원 공식 일지/주문 필드 합계 차이와 다중 포지션을 보존한다. | 공식 upstream 현재953e5dbff123f437ab4d11a78a95191a685eb51f의 spec/core/Postman을 재확인. 새 API·임의 배분·actual 비용 모델 대체 없음 |
| IQ175 capture lifecycle | 후행453/finish1의 미종료5를 조기 fixed exit2와 native PID drain3에 연결한다. 시작/종료/교체/정리/shutdown/다음 PID의 dead-process 관측을 기존 큐와 작은 영수증으로 기록한다. | queued와 durable·원 PID/attempt/plan을 분리. 과거 finish를 만들지 않고 후보별 관측 horizon을 평가하며 짧은 관측을 전20분 부족으로 일괄 폐기하지 않음 |
| all-scope trailing | holding 연구의 코드 해시가 최신 AI/실행 코드와 달라 10/19 실제 reader가 거부했는데 전체 준비 PASS가 이를 설명하지 못했다. 현재 코드·target·봉인 세대의 작은 관측을 summary/detector로 연결하고 원 producer를 갱신한다. | 작은 관측은 full native replay가 아니다. 실제 selector/bootstrap 검증은 원 native verifier 유지, optional 연구는 기존 부모 유지 경계 보존 |
| WS 공식 master | 경제 원천 report는 당일 canonical payload를 가졌지만 standalone master 발행이 빠져 9/16 metadata가 소비됐다. 기존 verified payload와 원 공식 metadata 바이트를 대사해 기존 발행 파일을 생성한다. | 네트워크·퇴역 collector 재생 없이 기존 원본만 사용. 잘못된 날짜/원천/authority/동일 경로 충돌은 거부 |
| WS zero-base attach 소비 | 당일 작은 native cache의 정확한 attach에 session이 있지만 legacy promoted/scan-generation 조건 때문에 zero-base lineage10건에서 누락된다. | 원 promotion/code/record/source/time 결속으로 실제 보존된 session만 소비한다. 통합 route를 물리 체결 venue로 바꾸지 않으며 BBO·실제 체결 결손은 유지한다. 후속 리뷰·native 재생성 대상 |
| 시장기회 active scanner 연결 | active zero-base claim/result/attach와 legacy upstream consumer의 불일치가 upstream0에 포함된다. 설치 owned-log cron4행을 읽지 못하는 오래된 기대값과 단일 예정 capture 구간의 불가능한 최소3회 조건도 확인했다. | 발견·승격·실주문을 구분하고 정확한 원 식별자·시간·route·source lineage를 검증한다. 외부524 opportunity episode를 Main 실제 발굴실패524건으로 해석하지 않는다. 후속 리뷰·native 재생성 대상 |
| machine stage 선택 상태 | 원 native operating comparison은 선택된 machine component인데 stage의 schema 분기 누락으로 no_valid_candidate로 기록됐다. | 새 producer 분기를 수리하고, 현재 overview는 검증된 native terminal/report와 원 stage 실행 영수증·code SHA를 함께 제시한다. 원 stage/aux 바이트는 보존하며 reporting 수정을 위해 provider 연구를 재실행하지 않는다. operator 초기 계약에 새 경제성 gate를 요구하지 않는다. |
| Parquet identity/보존 | 같은 record·시각의 다른 stage/content가 합쳐질 수 있는 식별자와 같은 집계만 보는 shadow 검증을 수리한다. native ID 또는 전체 원문 fingerprint, 정확 중복/충돌/날짜 제외, source→output 보존과 실제 출력 바이트를 검증한다. | 실제 10행 차이는 날짜 필터 제외이며 10건 유실로 주장하지 않는다. 현재일 원천 식별 비교와 기존 3일 집계 비교 범위를 공개하고 불일치를 실패로 전파 |

## 전체 작업별 최초 대조

수치는 원 관측 시점이다. 재생성 뒤의 판정과 동일 바이트/소비 결속은 마지막 검증 JSON으로 대체한다. 원 실패와 이전 산출물은 그대로 보존한다.

| 작업 | 실행 성격 | 원천·제외·적격 / 마지막 소비자 |
| --- | --- | --- |
| EOD common daily/venue eligibility | scheduled | requested/eligible2626, actual stored quote rows2622; short-history exclusions4(179880/266690/468670/486510); original terminal completed_with_warnings and actual DB consumer agree. Official venue metadata rows are a separate denominator. |
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

위 코드 게이트는 첫 커밋18905f3bc의 범위다. native 결과의 전체 의미 대사 중 WS zero-base session 소비와 시장기회 active scanner/설치 capture 읽기 계약의 추가 결함을 발견하여 수리·리뷰를 다시 진행한다. 첫 게이트를 전체 최종 완료로 해석하지 않는다. 최종 native 결과와 재검증 영수증은 아래에 추가한다.

## 후속 의미 대사와 보완

- 10/16 completion prefix는 실제 native producer로 839.039초에 완료했다. trade_review 536.407초, missed counterfactual 292.357초이며 3종 prefix만 완료로 표시한다. 10/15 원본 스트림 fact7건은145.556초, 10/16의18,008B scalar fact8건은3.972초에 적재했다. 최초 수량 refresh는2.696초이며 이월 완료4건의 누적 소비 결함을 이후 대사에서 찾아 추가 수리했다. 작은 관측 검증과 전체 native source replay는 구분한다.
- WS는 원 cache의 session10건(장전5/통합 장후5)을 정확한 promotion/record/source/원 시각에 연결한다. 통합 route를 물리 체결 venue로 바꾸지 않는다. 시장기회 native source는 claim1724/result1660, confirmed attach5/rejected5로 분리하며 실패한 장전5건을 승격하지 않는다. 새 선택 코드의 native 보고서 재생성은 별도 단계다.
- labels34건은 price horizon mature29/partial5와 별개로 canonical-primary 입력 결손이 있다. 원 trace/archived request 해시 불일치의 보조 검증을 primary 승격으로 바꾸지 않는다. weakness의 별도30분 라벨과 legacy10분 라벨을 섞지 않으며 outcome_U58을 임의 확정하지 않는다.
- 마지막 교차 리뷰에서 추가매수 횟수의 presence/단조성, 과거 양수 횟수 보존, 최신 완료 세대, 다른 custody가 Main 연구를 차단하는 조건, 압축 footer/CRC/deflate 예외의 모니터 전파, stage overview의 후행 원천 경합을 보완했다. 첫 결합938건은 통과했으나 실행 중 custody 보완이 반영되어 source guard가 실패했다. 이 로그는 보존하고 해당 실행을 최종 코드 승인으로 쓰지 않는다.
- cancel-wait9/30은 원 dated report의 native8개 이벤트가 남아 있어 빈 격리 해시의 전파와 실제 부재를 구분한다. 원 native census·이벤트·논리 원천이 모두 일치할 때만 복구하며 비용·terminal 결손은 보존한다. 10/1은 알려진 날짜별 execution/report/manifest의 plain/gzip 원천이 없고 당시 exact-date 보고서도 source_missing을 기록한다. 이를 verified zero로 바꾸지 않는다.

추가 근거: [이월 완료4 원천 대사](../../tmp/postclose-complete-repair-20261017/quantity-carry-overlay-current-native-bounded-verification.json), [수량 overlay 구현·리뷰](../../tmp/postclose-complete-repair-20261017/quantity-completion-overlay-implementation-review.json), [역사 cancel 원천 보존 조사](../../tmp/postclose-complete-repair-20261017/cancel-historical-original-source-recovery-assessment.json), [기계·연구11개 작업 대사](../../tmp/postclose-complete-repair-20261017/final-semantic-group-machine.json).

후속 코드 게이트도 종료했다. source SHA를 시작·끝에 고정한 9개 모듈 통합1,042건 통과(57.91초), Python compile·diff·print-only parser PASS다. cancel 복구는 독립3개 모듈133건 통과, 수량/모니터·WS·시장기회/stage 교차 리뷰도 미해결 finding0으로 닫혔다. [최종 source 결속 검증](../../tmp/postclose-complete-repair-20261017/supplemental-validation-attestation-v2.json), [cancel 독립 리뷰](../../tmp/postclose-complete-repair-20261017/cancel-native-ancestry-independent-review-final.json). 다음 단계는 이 exact code를 다음 정규 기동용으로 선택한 후 영향받은 native 생산자와 전체 최종 소비자를 실제 재생성·검증하는 것이다. 아직 미래 PREOPEN/PID/자연 주문·비용경제성 완료를 뜻하지 않는다.

## 실제 재생성에서 발견한 추가 계약과 반복 보완

- 058d432d3 선택 후 첫 native 수량 refresh는 `timeout_research_shared_source_mismatch`로 실패했다. 완료일 overlay를 가진 첫 census와 후속 timeout의 JSON/shared 재-census 사이에 완료 세대 헤더가 빠졌다. 실패 영수증을 보존하며, 행·cohort·작은 봉인 원천으로 공유 context를 독립 검증하고 전달하도록 후속 수리한다. 코드 검증1,042건 통과가 native 실행 성공을 대신하지 않는다.
- cancel native 재생성은98.915초에 완료했다. 원9/30 이벤트8개는 각 실행 stage2개씩 복구됐고, 원9/30·실패 조상15의 바이트는 그대로다. 10/1만 과거 격리를 유지한다. 9/30 미분류2와 전체 역사 미분류5·terminal/cost 미확정10, 현재일 미분류6은 별도 원천 결손이다. 실제 수량·종결·비용을 추정하지 않는다.
- WS native 최종화9.713초 후10/10의 원 세션을 확인했다. 두 경제 후보는 exact BBO/session 경로를 복구했으나20분 horizon의 exit BBO가 없어 right_censored2/EV NULL이다. 원 lookup2190의 실제 체결 결손과 exact source record 결손도 남는다.
- 시장기회 native17.508초의 의미 대사에서 기대 cron marker의 `KRX_` 누락을 추가 발견했다. 실제 설치4행과 원 receipt는 정상이다. 상수1줄·독립 literal4행 회귀를 수리했고96건 독립 검증을 통과했다. 새 코드에서 보고서만 다시 발행한다. 별도 확대 suite의2건 실패는 변경 전058에서도 동일 재현됐다. 하나는 시각을 고정하지 않은 scanner receipt 테스트의 비영업 시간 axes, 하나는 이미 퇴역한 builder 속성을 사용하는 fixture다. 운영 guard/퇴역 producer를 복원하지 않는다.
- 지연 정책 native stage는271.656초에 succeeded로 완료했다. 이전 source/code contract 불일치는 원 producer가 다시 검증한 세대로 대체하며 기본 지연/운영 권한을 변경하지 않는다.

후속 원 실패와 성공의 각 명령·실행 릴리스·소요 시간은 [native 실행 기록](../../tmp/postclose-complete-repair-20261017/native-operations.jsonl)에 별도 보존한다.

공유 원천 후속 수리는 독립348건, 최종 결합685건을 통과했다. 원 entry 상태·명시 횟수와 작은 native terminal/census·원천 세대로 재구성하며 JSON 왕복, 정상 count1→2, 전체 context 삭제와 summary만 삭제, 후행 세대 변조를 검증한다. 실제 실패는 publish 이전으로 기존 committed pointer와 원 report/evaluation/timeout 세대가 교체되지 않았음을 확인했다. [후속 결합 source-guard](../../tmp/postclose-complete-repair-20261017/supplemental-validation-attestation-v3.json), [공유 census 독립 리뷰](../../tmp/postclose-complete-repair-20261017/quantity-shared-census-independent-review-final.json), [실패 세대 보존](../../tmp/postclose-complete-repair-20261017/quantity-timeout-shared-census-failure-custody.json), [시장기회 marker 독립 리뷰](../../tmp/postclose-complete-repair-20261017/moc-trigger-independent-review-final.json). 미해결 in-scope 코드 지적0이며 다음 native 재생성 결과는 별도 검증한다.

## 885 원 native 결과의 교차 대사와 마지막 reader 보완

- 수량 native 재생성은6.576초에 완료했다. 전체 fact16=완료13+보유3, 원 이월4가 정확히 반영됐다. 경제성 제외는 비용/terminal12+원 과거 fact 오류1이며 적격0·실현손익 NULL이다. report와 timeout의 census는 완전히 같다. 평가 carry를 무활동 valid_empty로 바꾸지 않는다.
- 선택 릴리스의 data symlink로 작은 완료 원천을 읽을 때 canonical receipt 경로와 문자열이 달라 모니터가 잘못 거부하는 결함을 추가 확인했다. 실제 공유 directory를 resolve하여 pin하고, 읽는 중 link 교체/다른 실 root를 거부한다. unrelated child 쓰기는 mount 교체로 오인하지 않는다. 독립366건 및 실제 원 report 대사 PASS다.
- 시장기회 최종 native16.909초 뒤 모수는524=Main 적격271+명시 제외253이다. 별도 master-common514와 다르다. 원 관측1724=결과1660+pending64, runtime attach10=최종화5+미확정5를 보존한다. 실제 installed trigger/cadence PASS이며 BBO/EV 미확인은 그대로다.
- holding suffix는885 코드로158.532초에 기계적으로 완료했지만 frozen vote reader의 `main:+ID` 기대와 원 completed source의 plain ID가 달라11개 모두 잘못 제외된 의미 결함을 추가 발견했다. 원11쌍·report/manifest/completion 바이트를 보존하고 canonical Main ID exact reader로 수리했다. owner/원 source reference/symbol/관리 flag 충돌과 다른 namespace는 거부한다. AI vote의 별도 record:ID는 그대로다. 실제 비용 결손11·진입형 제외4·중복 SELL5는 중첩 사유로 남는다.
- 전체 최종화를 앞두고 자체 orchestration을 중지했으며885 holding의 완료와 후행 Main-stop의 미종결 시도4da272...를 구분해 보존했다. Main-stop receipt를 DONE으로 만들지 않고 새 holding 뒤 기존 owner로 재실행한다. 거래 Main에는 기동/종료 동작이 없었다.
- 마지막 변경은 독립 holding160건 및 결합480건, source SHA 전후 일치·compile·diff·print-only parser PASS다. [검증 결속](../../tmp/postclose-complete-repair-20261017/supplemental-validation-attestation-v4.json), [경로 독립 리뷰](../../tmp/postclose-complete-repair-20261017/quantity-observer-data-alias-independent-review-final.json), [holding 독립 리뷰](../../tmp/postclose-complete-repair-20261017/holding-vote-native-identity-independent-review-final.json). 이 코드로 holding family fixture와 suffix/full native 검증을 새로 마감해야 한다.


## be86 native 종료와 추가 원천 대사

- holding family fixture116건과 suffix157.585초를 새 코드로 완료했다. 앞선 completion prefix3종의 SHA는 그대로이고, frozen Main ID 오제외11건은0이다. 실제 비용 결손11·normal 진입4·중복 SELL5의 중첩 제외는 그대로 남는다. all-scope는 당일 master2605×route8=20840scope,504population/32partitions다. 기존20832는 과거 master 분모였으며 현재 값으로 혼용하지 않는다.
- Main-stop은102.783초에 새 native terminal을 발행했다. 이전 중단 시도는 보존한다. 별도 full native trailing 검증21.637초도 통과했다. bounded health는 이 검증을 대신하지 않는다.
- tuning5단계는139.627초에 실제 완료했다. 최종 pipeline은344472→344472, 정확 중복0·날짜 제외0·전체 원천 identity SHA252623940f0930635a9c1b3cdcb2bd1b24d47b961dbf08c94ae623be897ea519다. 최초344462+10행 날짜 제외 추정은 새 native 결과가 부정하므로 최종 판단에 쓰지 않는다. post_sell9, systemmetrics1440분 전체를 보존했고 종전 후행62분 누락을 해소했다. 원본 파일 전체4218행은 다른 날짜를 포함한 별도 모수다. 기존3일10집계와 당일 전체 identity는 모두 일치하지만 모든 변환 필드의 의미 검증을 주장하지 않는다. archive는0건 압축,98건 보호·13건 미검증 skip으로 전체 압축 성공이 아니다.
- summary/handoff102.769초 뒤 전체 finalizer519.630초가 실제 native controller DONE/PASS, summary 검증, cleanup, prepared19, detector 종료까지 완료했다. 독립 current_full_contract 검증도81.477초에 PASS/findings0이다. 선택be86·원천16·다음영업일19이며 실제 PID 소비는 아직 false다.
- 마지막 원천 대사에서49013의 기술적 fact 연결 오류1건은 원30 plain/sidecar가 남아 있어 복구 불가로 닫을 수 없음을 확인했다. 원snapshot281859734B와 sidecar36372864B는 동일 원 run/census와 원 inode identity를 보유하며, 동명 gzip은 다른 과거 run이다. 원본과 DB 행을 따로 보존했다. 기존 header만으로 성공을 만들지 않고 실제 원 selfseal/census를 검증하는 명시적 legacy adapter를 구현·리뷰한 뒤 새 fact 실행을 발행한다. 실제 broker 비용은 별도 미보존이므로 경제 NULL/제외를 유지한다.
- 수량13완료와 holding11의 차이 중49266은 DB 완료 상태지만 profit_rate와 원sell_time이 NULL이다. 원 display 복원과 canonical terminal 모수의 차이를 별도 추적하며 임의 적격 승격하지 않는다. 최종 수량/summary/controller/prepared는 이 추가 대사가 끝난 세대로 다시 닫는다.

근거: [be86 full native 준비 검증](../../tmp/postclose-complete-repair-20261017/pre-supplemental-be86-final-next-preopen-full-verification.json), [be86 별도 native trailing 검증](../../tmp/postclose-complete-repair-20261017/pre-supplemental-be86-trailing-full-native-verification.json), [최종 튜닝 의미 대사](../../tmp/postclose-complete-repair-20261017/final-semantic-group-final-consumers.json), [원30 세대 조사](../../tmp/postclose-complete-repair-20261017/quantity-legacy49013-native-header-assessment.json). 추가 복구 전 세대의 준비 PASS를 최종 복구 후 검증으로 재사용하지 않는다.


## 원 native fact 복구와 진단 역할 분리의 후속 수리

- 49013의 원30 snapshot/sidecar는 바꾸지 않는다. 기존 fact producer의 명시적 `--completion-snapshot` 경로에서 원 sidecar 전체 canonical selfseal·완료행/전체 projection SHA·source/run census와 원 snapshot identity/전체 byte SHA를 검증한다. 새 검증은 기존 fact-sync 아래 별도 immutable proof로 보존하며 과거 DONE·dependency 영수증을 만들지 않는다. 이후 동일 세대는 작은 proof로 검증한다. 원 cost metadata 부재와 현재 count0/no-official은 별도 기록하고 실제 비용/PnL/수익률은 NULL로 변환한다. 원 holding window와 native ancestry는 그대로다. 표적315건 및 독립37건·source SHA 전후 일치·compile/diff PASS로 코드 게이트를 닫았다. 실제 원30 적합성은 새 선택 코드의 최초 native 실행으로 확인해야 한다.
- compact 보조평가의 요청/가격 진단과 canonical-primary·경제성 적격을 혼합하던 반복 결함을 분리한다. 같은 기존 ai_decision_quality owner가 원 라벨의 byte/content/행 SHA·exact 요청·Main owner·item/route·session/clock·실제 horizon에 결속한 별도 `.compact_diagnostic.json`을 발행하고, 현재 detector 소비자도 이 projection을 검증해 읽는다. 원 labels/control/native outcome stage/auxiliary/weakness의 바이트와 기존 모수·지표·primary/경제성 판정은 보존한다. 실제 bounded 원본의 순수 계산은20 available/14 과거 hash gap이다. 정규장 경계를 넘는 가격 coverage, 다른 route/owner/date/hash·FIFO·alias 변경은 실패한다. 별도 가격 관측은 primary/EV 승격을 허용하지 않는다.
- 49266은 원 DB sell_time/profit NULL과 canonical terminal2 대 displayed/fact3의 admission 차이다. fact의18:17:40은 SELL 신호 시각이며 실제 체결 시각으로 확정할 수 없다. 원 writer나 실제 fill을 추정하지 않으며 유효 손익 모수로 승격하지 않는다. [완료 적격 대사](../../tmp/postclose-complete-repair-20261017/record49266-canonical-completion-admission-assessment.json).
- 임시공간 budget 경고는 실행 중 native 자료가 아닌22개 inactive backup root의23790파일을 별도 cold archive로 전환해 보완했다. 전체 원문 SHA·tar member·gzip EOF/CRC와 CRLF/NUL·손상 footer·foreign replacement 경합 검증 및 독립 리뷰를 마친 뒤 private 소유 경로에서만 raw 사본 표현을 전환했다. 원본6453254040B는 압축804310124B로 보존되어 실제5648943916B를 확보했다. 현재/과거 정책·native 원 data·선택/PID·source 날짜는 바꾸지 않았다. 기존 backup 경로의 복원 위치는 [보관 지도](../../tmp/postclose-complete-repair-20261017/offline-backup-archive-location.json), [전체 원문·복원 manifest](../../data/audit/postclose-offline-backups-20261017/preservation.json), [전환 종료](../../data/audit/postclose-offline-backups-20261017/transition-completed.json)에 남긴다.

후속 근거: [fact source 수리·검증](../../tmp/postclose-complete-repair-20261017/quantity-legacy-original-adapter-implementation-review.json), [fact 최종 독립 리뷰](../../tmp/postclose-complete-repair-20261017/legacy-original-fact-independent-review-final-v3.json), [진단 overlay 수리](../../tmp/postclose-complete-repair-20261017/compact-diagnostic-overlay-repair-self-review.json), [보관 전환 독립 리뷰](../../tmp/postclose-complete-repair-20261017/offline-backup-custody-independent-review-final.json). 이 후속 코드의 선택·실제 fact/수량·진단 발행·전체 최종화는 아래 최종 실행 영수증에서 별도로 마감한다.

## 14038cb68 실제 복구와 과거 holding 소비자의 후속 수리

- 원09/30의 최초 전체 native 검증과 fact 재적재는31.016초에 완료됐다. 원 snapshot281859734B·sidecar36372864B·서로 다른 과거 gzip의 바이트/물리 세대는 그대로다. 원49013은 실제 비용 근거가 없어 기존의 잘못된0원/0%를 NULL로 보완했고, 작은 immutable proof22052B를 현재 fact 소비자가 검증한다. 과거 DONE/dependency는 만들지 않았다. [독립 실제 대사](../../tmp/postclose-complete-repair-20261017/original0930-native-fact-recovery-independent-semantic-verification.json).
- 수량 재생성3.066초 후 전체16fact=완료13+보유3, 경제성 제외는 완료 비용/수량 결손13·미완료3이다. 원49013의 기술적 fact 오류는 해소됐고 적격0·손익/평균수익률 NULL·이월4·6개 유형의 기존 수량 단계와 분할/timeout 설정을 유지한다. report/timeout의 전체 census도 같다. [실제 수량 의미 대사](../../tmp/postclose-complete-repair-20261017/quantity-native-14038cb68-after-legacy-final-semantic-verification.json).
- 별도 compact 진단은0.913초에 발행했고 현재 direct/nested auxiliary 소비자에서20 available/14 과거 hash gap으로 검증됐다. canonical labels 등 원11개 파일의 SHA는 그대로다. 별도 전체 native trailing 검증20.573초도 통과했다. 이는 이 후속 holding 수리 이전 세대의 검증이며 최종 인계로 재사용하지 않는다.
- 전체 holding 기간을 다시 대조하여09/29 원 plain snapshot·09/30 원 completed sidecar·10/02와10/06의 원0건 sidecar가 현재 소비자에서 잘못 거부되는 경로를 확인했다. 원 native manifest/full byte SHA·전체 완료 census·비용 metadata presence와 원 cutoff를 보존하는 reader를 보완한다. 09/29의48376은09/28 매수→09/29 완료이므로 holding의 완료일 기간과 수량의09/29 이후 매수 기간을 혼용하지 않는다. 원09/29는 selfseal 없는 raw snapshot인 사실을 별도 kind로 기록하며 sidecar selfseal을 꾸며 넣지 않는다.
- 10/07·08·12·13·14의 작은 gzip도 원 dated native manifest와 full decoded SHA·EOF/CRC·전체0건 census가 일치함을 독립 검증했다. 과거 raw inode를 복원하거나 archive receipt를 만들지 않고 현재 물리 gzip과 원 논리 manifest를 결속해 valid-empty 원 payload를 소비하는 경로를 별도로 수리한다. 10/01·05·09·11의 intraday_light 원천과 원 open_census 결손은 이 계약으로 postclose 완료 승격하지 않는다. [압축5일 실제 대사](../../tmp/postclose-complete-repair-20261017/holding-five-small-gzip-native-census-triage.json).
- 위 intraday_light4일의 발행 의무도 구분한다. local KRX calendar상10/01은 거래일,10/05·09는 공휴일,10/11은 일요일이다. 부분 원천을 full-EOD0건으로 바꾸지 않고 publication not_due와 실제 원천 미검증을 별도로 기록한다. 원10/09의 holding_events2는 cutoff12:00:04 당시3058B 원 prefix의 해시가 일치하며 actual_order_submitted=false·telemetry_provenance_only인 진단2건이다. 후행19KB 전체를 원 cutoff로 읽거나2건을 제거하지 않는다. [캘린더 대사](../../tmp/postclose-complete-repair-20261017/holding-intraday-light-calendar-triage.json), [원2건 정확 시점 대사](../../tmp/postclose-complete-repair-20261017/holding-1009-two-original-events-review.json).
- 새 공통 validator의 실제 의존성을 holding family/vote/전체 trailing/Main-stop code generation에 추가한다. 압축 전 proof 발행뿐 아니라 native archive가 먼저 존재하는 최초 검증도 full decoded SHA·CRC·원 identity/manifest/census로 검증하며 bare/다른 run gzip은 거부한다. 원 source bytes·cost NULL·canonical terminal 조건·퇴역/수동 custody·provider/주문 권한은 그대로다.
- 05:35 정기 finalizer는 effective_date10/17의 비거래일 조건으로 SKIP했다. 이것을10/16 장후 완료로 해석하지 않는다. 최종 보완 코드의 리뷰/검증을 마친 뒤 원 source_date10/16·다음영업일10/19에 대한 기존 native 복구 owner로 최종화한다. 실제 Main은 EOD 종료 상태이며 주말에 새 매매 PID를 시작하지 않는다.

위 후속 reader는 코드 게이트와 새 선택 릴리스의 실제 재생성으로 별도 마감한다. 기존 be86/14038의 PASS를 새 코드 검증이나 최종 준비 완료로 바꾸지 않는다.

추가 검증의 실패도 보존한다. v6 통합은 source SHA 전후 일치 상태로965건 통과 후 preserved-report capability의 구 successor target 검사1건에서 멈췄다. 기존 exact prior hash와 원 report/fixture는 유지하고, 리뷰한 새 코드 target만 갱신하며 독립 current fixture를 다시 요구한다. 원 코드 승인·native validation·경제성·PID 수용을 서로 대체하지 않는다. 같은 시점의 실제 작은 원천 reader 점검에서는10/07만 통과하고10/08·12·13·14가 원 native manifest9필드 형식을 거부하는 추가 결함을 발견했다. base6+cost/window3의 알려진 원 형식을 typed로 지원하고 원 비용 및 window 내부 결속을 검증하며, 과거 전체 window를 재실행하거나 원 영수증을 재봉인하지 않는다. [v6 실패 보존](../../tmp/postclose-complete-repair-20261017/supplemental-integration-v6-attestation.json). 새 코드/실제5일 reader와 v7 통합 검증을 통과하기 전에는 이 실패를 해소로 표시하지 않는다.

## 최종 코드 소비 경계의 추가 교차 검증

- known9 manifest 및 calendar bounded intake 보완은115건과 독립115건을 통과했다. 실제 과거5일 gzip은 helper→holding resident→capture_window 모두 통과했고 원15개 source의 SHA·5stat가 그대로다. 원 archive receipt나 과거 inode는 새로 만들지 않았다. calendar4일도 bounded 실제 검증으로 별도 닫았다. [최종 reader 독립 리뷰](../../tmp/postclose-complete-repair-20261017/holding-original-reader-independent-review-final.json), [실제5일 소비](../../tmp/postclose-complete-repair-20261017/holding-five-small-gzip-current-consumer-independent-final.json), [calendar4일](../../tmp/postclose-complete-repair-20261017/holding-four-partial-calendar-current-consumer-bounded-p2-attempt-2.json).
- preserved capability의4개 map은 family/prior를 모두 보존하고 target만 실제 현재4개 code generation으로 갱신했다. 기존 권한·native_validated=false·독립 current fixture 조건은 그대로이며 관련286건 독립 검증을 통과했다. [정확 pair 독립 검증](../../tmp/postclose-complete-repair-20261017/reviewed-capability-pair-target-refresh-independent-final.json).
- Parquet 변환은 원 profit_rate/PnL/cost/outcome/시각을 0 또는 체결로 바꾸지 않는다. 현재10/16의 관련3열9행에도 bool·비유한값 오염이 없다. 다만 shadow 집계가 bool/NaN/무한대를 valid profit으로 세는 결함을 작은 fixture에서 재현했다. 단일 파일의 finite 숫자형 검사와 별개로, 여러 날짜를 union할 때 BOOL True가 DOUBLE1.0으로 변환돼 raw 완료1/Parquet2가 되는 추가 결함을 다시 재현했다. 이는 현재9행의 오염 주장이 아니며, union 전에 각 파일의 원형식에서 유효성을 판정하고 집계한 count만 합쳐야 한다. [변환·현재9행 점검](../../tmp/postclose-complete-repair-20261017/parquet-transform-economics-narrow-readonly-review.json), [실제2일 union 결함](../../tmp/postclose-complete-repair-20261017/shadow-union-bool-promotion-reproduction.json).
- v7 통합은13모듈1083건·source SHA 전후 일치·compile/diff/print-only parser PASS(81.459초)다. 그러나 그 뒤 발견한 union 결함의 완료를 대신하지 않는다. 이 마지막 후속 변경만 별도 표적 검증하고 v7의 나머지 source SHA가 그대로인지 대조해 전체 게이트를 닫는다. [v7 보존](../../tmp/postclose-complete-repair-20261017/supplemental-integration-v7-attestation.json).
- Mainstop 장후 CLI는 pipeline을 읽고 report/policy/cache만 발행하며 live capture sink를 열지 않는다. 원 pipeline과 Parquet를 다시 만드는 대신 변경된 shadow consumer 한 단계만 native 재실행한다. [writer 경로 검토](../../tmp/postclose-complete-repair-20261017/main-stop-postclose-historical-pipeline-writer-readonly-trace.json).
- 다음 정규 기동은 실제 cron07:35 PREOPEN→07:55 Main 순서다. workspace router는 매호출 선택 릴리스로 위임하고, 새 PID barrier/record-pid는 선택 릴리스 코드가 소유한다. 두 router의 바이트가 같다고 주장하지 않는다. 원16 live pointer/env/manifest는 불변이며 prepared19의 실제 당일 활성화와 PID 소비는 아직 미래 수용이다. [기동 경로 검증](../../tmp/postclose-complete-repair-20261017/next-startup-preopen-main-route-readonly-verification.json).

마지막 union 보완은 성공한 bounded 등록의 정확한 원 파일 tuple을 재사용하고 각 파일에서 실제 숫자형·finite를 먼저 판정한 count만 합친다. 원 producer/Parquet·손익/NULL/시각·다른 집계는 바꾸지 않는다. 실패한 등록의 stale tuple과 읽는 중 파일 변경도 거부한다. v8의84건·compile/diff/print-only parser가4.230초에 통과했으며, v7 이후 변경은 이 집계/저장소·기존 테스트4파일뿐이고 나머지14개 source SHA는 같다. v7의1083건과 이 추가 gate를 연결해 검증하며 서로 다른 시도의 통과 건수를 고유 테스트 합계로 더하지 않는다. [최종 후속 source 결속](../../tmp/postclose-complete-repair-20261017/supplemental-integration-v8-attestation.json), [자가 리뷰](../../tmp/postclose-complete-repair-20261017/shadow-completed-profit-original-type-union-repair-self-review.json). 독립 동일 fixture 대사와 새 선택 코드의 정식 shadow consumer 실행은 별도 마감한다.

독립 최종 gate도84건 통과·source stable·finding0으로 닫았다. 원2일 fixture를 다시 작성하지 않고 byte SHA·5stat를 보존한 채 raw1/Parquet2→raw1/Parquet1과 모든 집계 일치를 확인했다. [동일 fixture 독립 검증](../../tmp/postclose-complete-repair-20261017/shadow-original-type-before-union-independent-final.json). 미해결 in-scope 코드 지적은0이며, 다음 단계는 이 exact source 커밋의 선택·정식 재생성·마지막 소비자 검증이다. 코드 gate만으로 이를 완료했다고 주장하지 않는다.
