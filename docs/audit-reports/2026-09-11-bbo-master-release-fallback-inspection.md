# BBO·master / 배포 형상 / V2.14 fallback 점검

관찰2026-09-11 12:03~12:09 KST. 사용자 점검 요청에 따른 코드·원천·PID·DB 읽기 전용 대사다. 전략/코드/배포/주문을 변경하지 않았다. 당일 정오 market report SHA256 `3b63ee383247d0388a56d4d61e60b2399784b1352c9aa41750949bb758bbae0e`를 사용했다.

## 0. BBO 및 공식 master

정오 주요 forward-exact / verified common-stock 모집단은 아래와 같다. 이전 모니터링 문서의 retrospective KRX92행/BBO0은 별도 진단 표이며 주요 모집단의 BBO가 모두 끊겼다는 뜻이 아니다.

| Scope | episode | exact BBO | coverage | resolved | right-censored |
| --- | ---: | ---: | ---: | ---: | ---: |
| KRX regular | 78 | 63 | 80.77% | 40 | 16.67% |
| NXT premarket | 40 | 39 | 97.50% | 24 | 35.14% |
| NXT overlap | 157 | 139 | 88.54% | 65 | 39.81% |

전체 valid BBO2015개: 외부census1005·기존WS704·prune306. 예약1468/request1468/중복0/보존차0이며 collector configuration receipt는현재PID231446이다. 따라서 runtime hook 전체 미반영은 아니다. KRX미연결15episode의 최초외부요청14개는 `ka10004_shared_read_budget_deferred`, 알파칩스117670의1개는 `ka10004_bbo_invalid_or_crossed`. 엑스게이트09:00/제일일렉트릭09:05 등은 다음5분capture에서정상BBO가있어도 observed_at이최초crossing+300초를넘어 join되지않았다. collector5분간격과validity300초 경계에 조회지연이더해지므로 단순대기만으로이미닫힌episode가복구되지않는다. KRX liquid panel capture cadence는PASS이나 KRXall/NXT의실패capture누락이전체cadence blocker를남긴다.

권고: 원래조회5/sec·source-only4/5·일일cap을유지하면서 미획득episode의유효기간내 재수집우선순위/기존예산배치를검토한다. 중복패널요청·반복이미충족episode보다 미획득exact source를우선할수있는지평가하고,5분이후늦은호가를과거성공으로결속하지않는다.95% floor하향 또는API동시성증가로현재결손을숨기지않는다.

master 자체는9/10공식KIS원천의2549행, binding verified/hash정상이다. 두원본archive SHA도metadata와일치한다. 전체347종목중47missing이며 primary는289episode중14missing/9종목,verified275episode다. primary미확인9종목은 ETN이름7개(760028/520102/530031/520093/580068/520099/530133),0197X0(SOL SK하이닉스선물단일종목인버스2X),900270(헝셩그룹)이다. 보존된공식raw master에서0197X0는security_group EF,900270은FS이며 현행경제성master의ST/보통주 필터에해당하지않는다. ETN7개는이보존된KOSPI/KOSDAQ master에없어별도공식상품분류근거가필요하다. 이름만으로보통주또는누락오류로승격하지않는다.

현재report는 primary의모든non-verified lookup을하나의 `official_symbol_master_lookup_gap`으로처리한다. 따라서 master파일손상·실제보통주누락·계약상비대상상품을분리하는진단보완이필요하다. 검증된비보통주는 `intended_source_or_universe_exclusion`, 진짜미확인은source gap으로분리하고검증된275episode의부분진단을유지해야한다. 보통주만담긴master에ETF/ETN/FS를억지로EQUITY로추가하는방식은부적절하다.

## 1. 배포본과 작업본

12:07:58 snapshot의workspaceHEAD `1d3ac104`, dirty변경별도. main선택/실제PID231446은 `c15a02cb` / hardstop-detector-20260911, source clean. snapshot의tracked code차이166파일(source66/test46/deploy53/restart1),병행untracked작업4파일을별도보존했다. 이는미배포필요작업166개를뜻하지않는다. 전체경로·양쪽파일SHA는 `tmp/runtime-comparison-20260911-1203/code-comparison.json`에있다. 다른세션변경으로이후수는바뀔수있다.

| 독립 실행 owner | 실제/선택 commit | 상태 |
| --- | --- | --- |
| main | c15a02cb | PID231446 active |
| widget | a2e14f5d | PID273930 active |
| fill notifier | b49e7ecb | PID273913 active |
| Samsung morning | acf139cd | 오전window종료/inactive |
| Samsung midday/afternoon | e0116f6d | 예약전/inactive |
| low-price template | 431e33ca | profile별정상timer소비 |

핵심역방향누락: 배포에있는탐색제한e2388dbb수리의 `_clear_superseded_entry_setup_exploration_arm` holding/주문증거보존, `can_consider_scale_in` 직접guard, `recover_probe_runtime_bundle_for_stock` target/terminal/금지flag복구가workspace에없다. workspace를통째로배포하면이수리가빠질위험이있다. 반면workspace의정체청산공통함수추출·기계adaptive/알림확장은별도owner로 main누락결함과합치지않는다.

`ai_engine_openai.py`, `entry_setup_live_policy.py`, `market_opportunity_census.py`, `buy_funnel_sentinel.py`, `process_health.py`는workspace와main배포의실제파일byte가동일하다. 따라서현금부족제외·hard-stop수동이관분류는현재작업본과배포본이같으며,V2.14선택코드버전차이가fallback원인은아니다. fallback계측d8808da7은별도브랜치에만있고두경로모두미반영이다.

## 2. V2.14 fallback

11:20~점검시각bounded trace의 live Entry는V2.14 12회/V2.13 10회다. V2.13은우리금융지주316140/42972 8회와현대건설000720/42767 2회. 읽기전용DB조회에서두record모두SCALPING/position_tag=SCALP_BASE다. 현대건설현재status EXPIRED는호출당시status로소급하지않는다.

현재activation의eligible_position_tags는SCANNER만이다. 실제PIDenv를동일선택코드에읽어넣은순수정책조회에서SCALP_BASE는 `fallback_position_owner_out_of_scope`/V2.13/비적용, SCANNER는 `active_bounded_krx_canary`/V2.14/cap100으로재현됐다. Provider호출·정책발행없이확인했다. 현재정책범위와관측fallback은일치한다. 과거trace사유null은현재재현값으로덮어쓰지않는다.

잔여는둘이다. (1) 승인범위밖이라는사유가trace에없는계측결함은d8808da7에서214tests로수리완료/미배포. (2) 모든SCALPING경로에V2.14를사용하려는목표라면현재SCANNER한정정책은그목표보다좁다. SCALP_BASE의stage/custody/후단guard를대사한뒤기존owner의승인범위확대를별도검토해야하며,이번점검에서범위또는BUY판정을바꾸지않았다. 일일100미적용이나Provider실패가이두종목fallback의직접원인이라는근거는없다.

## 검토 결과

읽기전용원인점검완료. 신규trading/API코드수정없으므로trading test/Provider재실행은하지않았다. 문서링크·owner·분모·시각·비권한경계와print-only parser/diff검증을수행한다. 기존RuntimeEnvIntradayObserve0911의후속범위에구체적인연결결손·역방향수리누락·fallback사유반영이남는다.
