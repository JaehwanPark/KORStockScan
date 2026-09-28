# SCALPING 시장 발견→기계 판정 제로베이스 재설계 — 2026-09-28

상태: **VCP/S15 신규 유입 퇴역과 통합 `_AL` 발견·기계 probe·Main 감시 경로를 구현하고, 사용자 요청으로 즉시 배포·재기동했다.** 현재 선택 릴리스·PID와 관측 범위는 [구현 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md)의 후속 영수증을 따른다. 자연 제출·체결·terminal·비용 후 경제성은 별도 미수용이다. 과거 KRX/NXT 분리 패널 시험은 잘못된 route 설계의 역사적 증거이며 운영 기준이 아니다. VCP/S15 재유입이 가능한 구 릴리스는 롤백 대상이 아니다.

## 17:26 KST 기계판정 도달 우선 수리

16:58~17:21 KST 기존 PID의 zero-base probe 결과 777건(428개 고유 코드) 중 기계판정은 3건, 감시 편입은 0건이었다. `route_snapshot_missing` 608건과 `probe_worker_capacity` 155건은 감시 슬롯 이전 단계에서 발생했다. 따라서 현재 감시 TTL을 줄이는 것은 이 병목의 직접 수리가 아니다. 전 세션의 정확 route WS 기본 수신 대기를 3초에서 5초로 늘리고, 입력이 일찍 완성되면 즉시 반환한다. 동시 프로브 작업자는 2개에서 5개, 작업 예약은 8개에서 12개로 늘리되 회차당 8개 발견 claim과 공유 REST admission, WS item budget을 유지한다. 대기 영수증에는 기본·실효 대기 예산을 남겨 다음 자연 PID에서 3~5초 신규 수신·기계판정·보류·WS 등록 수를 대사한다. 최종 판정 3초 신선도와 route/transport, 주문·수량·가격·하드 가드는 변경하지 않는다. 커밋 `082ddd51`의 선택 릴리스와 PID `738184`의 기동은 확인했으며 자연 판정·주문 개선은 별도 미수용이다.

17:30~17:34 KST 새 PID의 167개 자연 probe에서도 판정 0건·`route_snapshot_missing` 166건이었다. 상승률 상위 후보의 반복 체류를 줄이고 실제 움직이는 상승 종목을 더 빨리 발견하기 위해 공식 `ka10023` 5분 거래량 급증 KOSPI/KOSDAQ 패널을 source-only로 추가한다. 기존 `ka10027`과 중복 코드는 한 큐 세대로 합치며 source kind별 결과를 남긴다. 이것은 최근 5초 체결 증명이 아니므로 정확 route WS 및 3초 최종 신선도 가드는 유지한다. 공식 요청·리뷰·실측 한계는 [활동성 원천 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1744-kst-활동성-원천-추가와-기계판정-전-병목-재리뷰)를 따른다.

활동성 원천 배포 후에도 첫 158개 probe 중 기계판정 0건이었다. Main이 5초마다 임시 probe WS 구독을 감시종목 부재로 정리하는 소유권 충돌을 발견했다. 진행 중 probe 코드는 Main의 일반 구독 정리에서 제외하고, probe 종료 시 기존 해제 경로로 넘긴다. [구독 충돌 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1752-kst-임시-ws-구독과-main-정리-충돌-수리)의 새 PID 자연 수신 결과가 실제 개선 수용의 기준이다.

충돌 수리 뒤 첫 167개 probe에서 기계판정 5건으로 회복됐으나 정확 0B 첫 수신 10건·0D 37건에 그쳤다. 자료가 준비된 후보는 즉시 반환하는 구조를 유지하면서 결손 후보의 임시 WS 관측을 기본 최대 10초, 저활동 세션의 한쪽 수신만 최대 12초로 늘리고 10 worker/16 예약으로 처리량을 보전한다. 56-item WS hard budget, 최종 3초 신선도와 주문 안전 가드는 유지한다. 이는 라이브 성과 확정이 아니라 [관측창·처리량 보완](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1800-kst-짧은-수신창-보완과-처리량-경계)의 다음 PID 시험이다.

커밋 `b158b81a`의 불변 릴리스로 정상 재기동한 Main PID `752307`은 source clean·scanner flag·당일 정책 bootstrap·release-set 결속이 통과했다. 기능·제출·비용 후 성과는 새 PID 자연 probe 영수증으로 별도 판정한다.

18:00~18:05 같은 PID의 통합 애프터마켓 probe 178건 중 활동성 원천 97건에서 기계판정 7건, 상승률 원천 81건에서는 0건이었다. 이는 세션 한정 판정 가능성 자료이며 수익성 우위 증거는 아니다. 큐는 활동성 3·상승률 1 순서로 claim하되 원천이 비면 즉시 다른 후보로 채우고, 시장별 공정성·재기동 후 순서를 보존한다. 총 probe·WS·REST 예산과 기계판정/주문 가드를 바꾸지 않는 [활동성 후보 우선 순환](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1805-kst-활동성-후보의-판정-가능성-우선-순환)이다.

커밋 `c359a8d5`의 불변 릴리스가 Main PID `755981`로 정상 기동됐고 source clean·scanner flag·당일 정책 bootstrap·release-set 결속이 통과했다. 활동성 우선 순환이 새 PID의 실제 판정·감시·제출로 이어지는지는 별도 관측 중이다.

활동성 후보는 5분 급증 목록보다 매매 시점에 가까운 1분 급증 목록을 source-only로 사용한다. 18:10 KST 공식 `ka10023 tm=1` 통합 KOSPI/KOSDAQ 첫 응답 200/200행·양의 급증/상승 123/103행을 확인했고, 상위 10개 `ka10003` 표본의 8개에서 조회 전후 최근 수 초 체결을 보았다. 이 표본은 live 판정/순익 증거가 아니며 1분 목록도 정확 WS를 대체하지 않는다. 호출 수·순환·주문 가드를 그대로 두고 [1분 원천 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1810-kst-활동성-발견-창-5분1분)의 다음 PID 수신을 대사한다.

커밋 `df9649ef`의 불변 릴리스가 Main PID `758822`로 기동됐고 source clean·scanner flag·당일 정책 bootstrap·release-set 결속이 통과했다. 1분 원천의 실제 WS·기계판정·감시·제출과 비용 후 결과는 별도다.

새 PID의 첫 74개 probe에서 활동성 56건 중 기계판정 3건, WS 등록 표본 최대 37/56개였다. 앞단 순환을 빠르게 하기 위해 제로베이스의 발견 재조회 최대 60초, 10초당 claim 12개, 16 worker/24 예약으로 상향한다. 공유 API 5/4, WS 56-item hard budget, 감시 16-slot 및 기계·주문 가드는 유지한다. [순환 가속 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1815-kst-스캘핑-발견probe-순환-가속)의 새 PID에서 실제 처리량·수신·판정과 부하를 확인한다.

커밋 `025d80f0`의 불변 릴리스가 Main PID `761794`로 정상 기동됐고 source clean·scanner flag·당일 정책 bootstrap·release-set 결속이 통과했다. 실제 분당 고유 probe·WS peak·기계판정·감시·제출 및 비용 후 결과는 별도다.

빠른 발견 회차가 진행 중인 probe의 원천 hash와 lease를 덮는 경합을 추가로 확인했다. 현재 원천과 실행 중 claim을 분리해 새 발견을 즉시 기록하면서도 도착한 판정 결과를 정확히 결속하고, 다음 dispatch에서 새 세대를 사용할 수 있게 한다. 재기동·timeout의 오래된 결과는 계속 거절한다. [18:30 경합 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1830-kst-진행-중-probe-세대-보존)의 배포·자연 결과는 별도 대사한다.

커밋 `57946bc9`의 불변 릴리스가 Main PID `768143`로 정상 기동됐고 당일 정책 검증·release-set 결속이 통과했다. 진행 중 판정 결과의 실제 수락률과 감시·제출은 새 PID 자연 영수증으로 확인한다.

새 PID 약 3분의 요청 216건 중 수락 결과 204건/204코드와 진행 중 12건을 확인했다. 기계판정 13건은 모두 비진입이고 감시 편입·제출은 없다. 판정 전 큐 유실 징후는 줄었으나 정확 `_AL` WS 0B/0D 결손은 남아 있어 source gap을 기대수익 0으로 대체하지 않는다.

애프터마켓 원천별 누적 기계판정 도달은 활동성 70/1,311건, 상승률 4/615건이었다. 이 진단에 따라 애프터마켓만 활동성 7:상승률 1로 claim을 순환하고, 프리마켓·정규장 3:1과 전체 API/WS/감시/주문 예산은 유지한다. [원천별 우선순위 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1837-kst-애프터마켓-활동성-판정-도달-우선순위)의 새 PID 결과와 비용 후 성과는 각각 별도다.

커밋 `59ebc9cd`의 불변 릴리스가 Main PID `772431`로 정상 기동됐고 당일 정책·release-set 검증이 통과했다. 새 비율의 실제 WS 수신·기계판정과 제출·비용 후 성과는 구분한다.

새 PID 첫 167개 고유 결과의 활동성 비중은 146개(87.4%)였고 기계판정 6건은 RECHECK 5·BLOCK 1이었다. 감시 편입·제출은 0건이며 정확 `_AL` WS 원천 결손이 계속된다. 뒤따르는 정규장/프리마켓의 별도 자연 표본과 실제 제출·terminal·비용 후 결과로 판단한다.

18:18~18:21 새 PID 자연 결과는 발견 약 66초 간격, 135개 고유 probe/약 2.5분, worker 보류 0, WS 등록 표본 최대 40/56이었다. 기계판정은 RECHECK 2건이며 감시 편입·제출은 0건이다. 앞단 처리량과 부하는 확인했지만, 현재 애프터마켓의 정확 WS 수신 결손을 기계가 무시하거나 원천 결손을 수익성 0으로 채우지 않는다. 정규장·프리마켓의 동일 경로 수신과 감시/제출·비용 후 결과는 자연 영수증으로 구분한다.

감시 슬롯의 더 빠른 의미적 해제는 실제 zero-base WATCHING 세대에서 신선한 연속 비진입과 반전 부재, 동일 슬롯 경쟁이 확인된 뒤 별도로 판단한다. 기존 재생에서 5분 조기 퇴출 후보의 후행 회복이 있었고 10분 적격 후보는 0이므로 체류시간이나 `BLOCK` 횟수만으로 새 퇴출 임계치를 만들지 않는다.

## 16:59 KST 세션 경계 재리뷰

주문 직전에는 감시 당시의 route·broker·venue·market session bucket과 현재 KST 매수창/세션을 다시 묶는다. 프리마켓·정규장·통합 애프터마켓 중 이전 세션의 제로베이스 WATCHING은 기존 FIFO 만료 경로로 종료해 슬롯과 동일 코드 probe를 해방한다. 수정 커밋 `527f27a3`은 영향 회귀 678건 통과 후 불변 릴리스로 재기동됐고 Main PID `725217`의 선택 커밋·cwd, 당일 bootstrap 및 release-set 결속을 확인했다. 새 PID에서 통합 `_AL` REG/REMOVE가 자연 발생했다. 실제 세션 전환 만료와 다음 프리마켓 `_NX` 수신, 제출·체결·비용 후 성과는 별도 미관측이다. [세션 경계 리뷰 영수증](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1659-kst-세션-경계-재리뷰수정재기동)에 근거한다.

## 16:32 KST 프리마켓 경로와 수신 대기 보완

정규장·통합 애프터마켓의 통합 `stex_tp=3`·`_AL`·SOR 계약은 유지한다. 프리마켓만 기존 세션의 별도 NXT 경로로 KOSPI/KOSDAQ `stex_tp=2` 패널을 읽고, probe REST/WS와 감시 WS는 `_NX`, 주문은 NXT로 결속한다. 세션 변경 전후의 다른 route claim은 평가·승격하지 않는다. 두 저활동 세션에서 정확 0B/0D 중 한쪽만 3초 안에 도착하면 WS 관측을 최대 5초로 연장한다. 사용자의 후속 결정에 따라 프로브의 최종 기계판정 직전 동일 route·transport 신선도는 2초에서 3초로 변경했다. 두 신호 모두 없는 후보는 3초에 종료하고 추가 REST는 호출하지 않는다. 커밋 `16927a86`의 불변 릴리스가 16:43 KST 새 Main PID `717094`에서 기동했고, 통합 애프터마켓 자연 패널/프로브를 확인했다. 프리마켓 `_NX` 자연 결과는 아직 미관측이다.

관측 근거와 표본 한계는 [수신시점·프리마켓 구현 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md#1632-kst-프리마켓-수신시점과-구현-리뷰)를 따른다. 3초 값도 전체 시장에서 최적인 것으로 검증되지 않았다. 특히 프리마켓 비교는 `_AL` 연속 구독 23종목이지 새 `_NX` 임시 구독의 실제 수신 시험이 아니므로 다음 자연 프리마켓의 exact-route 수신·판정·주문 전 가드를 별도로 확인한다.

## 14:56 KST 통합 route 정정과 실제 기동

사용자 정정에 따라 정규장과 통합 애프터마켓의 독립 KRX/NXT 후보 패널을 제거했다. `ka10027`은 KOSPI·KOSDAQ 각각 `stex_tp=3`으로만 호출하고 관측 원장에는 `krx_nxt_integrated` 한 route를 남긴다. 임시 WS와 감시 WS는 종목코드 `_AL`, REST tick/분봉은 명시 `_AL`, 신규 스캐너의 주문 요청은 명시 `SOR`로 결속한다. Main 감시 코호트는 정규장 `KRX`, 통합 애프터마켓 `KRX_NXT_INTEGRATED`로 유지해 브로커 route와 시장 세션 분류를 혼동하지 않는다. 장전·전환·신규 BUY 마감 세션에는 통합 패널을 호출하지 않는다. 기존 분리 route queue 파일은 보존하고 `zero_base_discovery_queue_integrated_v2`에서 새로 시작한다. 종목별 SOR 적격·주문유형·잔고·hard guard는 기존 주문 owner가 계속 검사한다.

잘못된 신규 스캐너를 14:38 퇴역 전용 릴리스 `53854ced`로 되돌려 PID `647108`의 기동·정책 검증을 확인했다. 정정된 `826f3d72`은 실제 통합 패널 2/2·400행·약 7.75초와 회귀 210건을 확인한 뒤 배포했고 PID `657079`에서 `_AL` REG/REMOVE 및 통합 queue의 자연 기계 `RECHECK` 1건을 관측했다. 리뷰 중 드러난 `strategy_tape_score_source_missing`은 신뢰 가능한 체결 주도 방향의 결손이므로 `policy_unavailable` 대신 `required_feature_insufficient`로 분류해 `d619923a`를 다시 배포했다. 당시 PID `661520`의 exact-date 정책 검증과 release-set 검사는 통과했다. REST `ka10003`의 가격변화 추정치를 신뢰 체결 방향으로 승격하지 않았으며, 기계 `ENTER_NOW`·실제 제출·비용 후 성과는 아직 확인되지 않았다.

## 결정과 원천 경계

사용자의 목표는 상승 종목 수 자체가 아니라 **기계 진입 판정이 신선한 입력을 가진 충분한 후보에 도달하고, 비용 후 기대수익이 있는 제출을 놓치지 않는 것**이다. 감시 슬롯 상한을 먼저 높이거나 기존 순위 가중치를 조정하지 않고, 시장 발견·입력 생산·짧은 평가·유효 감시를 별개 자원으로 다시 만든다. 기존 `BLOCK`은 순간 판정이고 영구 무가치 판정이 아니며, `RECHECK`는 재평가 시각을 보존한다. 주문·보유·청산 custody와 hard safety는 기존 owner를 따른다.

[11:25:30 KST 고정 재생](../audit-reports/2026-09-28-kospi-positive-machine-one-pass-source-test.md)의 독립 `ka10027` 패널에서 9/25 마스터 KOSPI 보통주 중 상승 관측 113종목만 확인됐다. 이는 오늘 KOSPI 상승 전수가 아니다. 같은 cutoff·pipeline prefix 1,572,722,152 bytes의 스캐너 source/pool/prune/promotion receipt를 code와 첫 상승 관측시각으로 연결하면, 113종목 중 source adapter 반환 93, 후보 풀 91, 감시 승격 41, 풀에 있었으나 승격 없음 50, source 반환 없음 20, 반환됐으나 풀 없음 2다. 풀만 있고 승격 없는 50종목의 **첫** prune은 `general_slot_limit` 29, `max_new_codes_reached` 18, `market_gainer_reserved_full` 1, `reentry_cooldown_no_material_upgrade` 2다. 첫 상승 후 5분 이상 관측 기회가 있었던 112종목에서도 source 없음 19, 풀 없음 21, 풀·미승격 50, 승격 41이다. 이 source/pool 연결은 **코드·시각 기준**이며 scanner receipt의 정확 route가 `UNKNOWN`일 수 있어 KRX 동일 route 발견률이 아니다. 이 분류는 후보가 기계 입력·수익성을 갖췄다는 뜻도 아니다. 같은 코드의 route/시각별 원천 적격과 downstream attempt는 다음 계약에서 다시 검증한다.

현행 `ka10027` 스캐너 호출은 [fetch 구현](../../src/scanners/scalping_scanner.py)의 요청 반환 상한 60행, 그 source의 상승 후보 상한 20개, 회차별 신규 상한 12개와 점유 슬롯 제한을 거친다. 고정 구간 66번의 `ka10027` source receipt 중 64번은 60행, 57번은 `partial_adapter_return`이었다. 이 상태는 60행 밖에 어떤 종목이 있었는지 증명하지 못한다. 독립 패널도 첫 페이지 최대 200행이며 상승 전수가 아니다. 9/28 장중 Main PID `504041`의 읽기 전용 환경 확인에서는 스캐너 감시 상한 **22**(`KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE`), WS 등록 상한 **56**, 시장 상승 source ON, 상승 후보 상한 20, 조건검색 ON이다. 앞선 대화의 “16종목”은 이 PID의 현재 설정값이 아니다. PID/설정은 시간에 따라 변할 수 있으므로 적용 판단 전에 다시 확인한다.

## 새 구조

1. **발견 원장.** KST 날짜·보통주 마스터·listing market·정확한 KRX/NXT 시장데이터 route를 고정한다. 시장 전체를 대표하는 원천의 범위·지연·페이지/연속조회 완전성이 확인될 때만 `whole_market` 분모를 선언한다. 그렇지 않으면 `observed_panel`과 `unobserved`를 명시한다. `ka10027`의 반환·미반환을 곧바로 상승/비상승이나 기회/무기회로 치환하지 않는다. 후보 원장에는 code, venue/session, source/request/receive 시각, 범위·continuation·source hash, 첫 발견과 마지막 발견을 남긴다. 같은 관측은 중복 제거하되 이전 응답을 새로운 현재 호가로 재사용하지 않는다.
2. **평가 대기열.** 발견 종목을 기존 조건검색식/스캐너 점수로 자르지 않는다. source 신선도·보통주/유동성·거래 세션·최근 미평가 시간·평가에 필요한 원천 확보 가능성으로만 탐색 순서를 정한다. 특정 고순위 종목이 매 회차 전체 평가 예산을 독점하지 않도록 재평가 예정과 미평가 종목의 공정한 순환을 기록한다. 보통주 마스터는 진입 승인 원천이 아니며, source 결손은 별도 상태다.
3. **짧은 입력 수집과 판정.** WS 구독·REST 요청의 실제 공유 예산 내에서 평가용 probe를 예약한다. `source_unavailable`, `required_feature_insufficient`, `assessed`를 분리하고 입력이 완성된 경우에만 기존 기계 판정 함수를 한 번 호출한다. `ENTER_NOW`만 기존 AI 보조·주문 안전 경로로 넘기고, `RECHECK`는 정확한 재확인 조건/기한, `BLOCK`은 새로운 source 또는 명시적 재평가 기한을 남긴다. 단순 상승률이나 condition match는 주문 권한이 없다. probe의 source가 무효하면 슬롯을 해제하되 그 종목의 기대수익을 0으로 기록하지 않는다.
4. **감시 편입·교체.** probe와 유효 WATCHING, 보유/주문 custody를 별도 계수로 기록한다. 동시 WS/CPU/요청 상한과 기존 안전 상한을 지킨다. 장기 점유 퇴출은 [기존 재생](scalping-scanner-semantic-watch-replacement-plan-2026-09-28.md)의 원칙인 **오래 점유했고, 연속으로 신선한 관측이 있었으며, 최근 반전 징후가 없음**을 만족할 때만 검토한다. `BLOCK` 횟수나 10분 체류만으로 제거하지 않는다. 새 후보와 기존 감시 세대의 동일 route·시각 자원 경쟁을 남기되, 현행 스캐너의 점수·상한을 최적화 목표나 경제 비교군으로 쓰지 않는다.

`ka10027` 전수 확대, 다른 시장 전체 소스, WS probe/REMOVE, 조건검색 제어 패킷 또는 연속조회 흐름을 실제 수정하기 전에는 [공식 API gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)로 **당시 upstream SHA와 해당 endpoint·packet·응답·한도**를 확인한다. 9/28 장중 확인한 upstream HEAD는 `953e5dbff123f437ab4d11a78a95191a685eb51f`였고, `kiwoom/_data/kiwoom_api_spec.json`의 `ka10027`·`ka10171`·`ka10173`를 열람했다. 이 리비전의 `kiwoom_docs`는 없었다. 공식 `ka10027` 계약은 `cont-yn`/`next-key` 연속조회를 정의하지만 **이것만으로 전체 상승 종목 커버리지는 증명되지 않는다**. `ka10173`의 초기 응답 `seq`는 선택 필드여서 빠진 응답을 임의의 조건식에 귀속할 수 없다. 초기 문서 작성 단계에서는 요청/파서/구독을 바꾸지 않았고, 후속 구현에서 공식 gate를 다시 확인한 뒤 source-only 패널과 임시 WS 구독을 추가했다. 검증 전의 비공식 전체 시장 소스를 런타임 입력으로 승격하지 않는다. 공유 Kiwoom 읽기 예산 5회/초, source-only 4회/초를 우회하지 않는다. 804개 참조 마스터를 종목별 REST로 한 번만 훑어도 source-only 4회/초를 전용한 이론적 최단 시간이 201초이며 다른 요청·대기·재시도를 포함하지 않는다. 따라서 모든 종목을 즉시 병렬 조회하는 방식은 채택하지 않는다.

## 조건검색식 제거 결정

현재 [WS bootstrap](../../src/engine/kiwoom_websocket.py)은 활성 목록에서 이름 키워드와 일치하는 조건식을 각각 `CNSRREQ` 실시간 push로 요청한다. [condition handler](../../src/engine/sniper_condition_handlers.py)는 직접 `WATCHING`·`COMMAND_WS_REG`까지 연결할 수 있어 스캐너의 22개 감시 상한만으로 condition 유래 WS 부담을 설명할 수 없다. 현재 PID의 tmux 시작 구간에는 목록 17식, 그중 13식 구독 요청이 기록됐다. 초기 응답 중 10개는 seq를 식별했지만 나머지 3개는 `seq=''`, `UNKNOWN_CONDITION`, 각 0행이어서 식별/응답 계약을 확인해야 한다. 이것만으로 실제 편입 0 또는 broker 장애라고 단정하지 않는다.

11:25:30 이전 pipeline에 `CONDPROM`을 남긴 것은 네 식(`scalp_candid_normal_01`, `scalp_shooting_01`, `scalp_strong_01`, `scalp_underpress_01`)의 고유 **13종목**이다. 이들의 condition 세대는 55개 promotion ID, `scalp_entry_action_decision_snapshot` 64행, 같은 condition ID의 `order_bundle_submitted`/`order_leg_sent` 0건이었다. 13코드 중 12개는 같은 날 cutoff 전 스캐너 풀에도 등장했지만, 그 풀 receipt에는 정확 route가 종종 `UNKNOWN`이고 선후관계가 달라 **동일 시각의 대체 가능성**은 증명되지 않았다. 원시 condition 편입 중 후속 pipeline 기록이 없는 건도 이 집계 밖이다. 따라서 이 숫자로 조건검색식을 수익성 0이라고 판정하지 않는다.

새 릴리스에서는 살아남는 조건식별 `list→subscribe ACK→초기 편입→실시간 I/D→중복 제거→유효 기계 입력→판정→제출`과 실제 `COMMAND_WS_REG/UNREG`, 등록 item 수·메시지량·오류·재연결을 계측한다. 조건식마다 **유일하게 제때 제공한 적격 기계 입력/진입 기회**가 있는지 확인한다. 출처 식별 불가·지속적 빈/오류·유일한 유효 입력 부재인데 구독/REG 부담만 발생한 식은 새 scanner 설정에서 제외한다. 핵심 목적은 잘못된 조건식을 고치는 데 드는 WS 예산을 회수하는 것이다. VCP/S15는 아래의 별도 퇴역 결정으로 제거하고, swing 및 기존 보유·주문·청산 경로는 소유권 대사 없이 함께 끄지 않는다. 전역 조건검색 OFF는 살아남는 조건식의 기여와 swing 소유권까지 대사된 경우에만 검토한다. 제거한 식의 재활성은 새 원천·계약·경제성 시험과 별도 승인/수용 영수증을 요구한다.

### VCP/S15 퇴역 결정과 증거 경계

- **VCP: 새 후보 유입 및 전용 진입 경로 퇴역.** 9/28 11:13 기동 Main PID `504041`의 [WS 로그](../../logs/bot_history.log)는 `vcp_candid_01`, `vcp_shooting_01`, `vcp_shooting_next_01` 세 식의 `CNSRREQ`를 보인다. 각 초기 편입은 0/1/0건이었다. 이 로그는 회전 가능한 운영 파일이므로 적용 전 고정된 구독·응답 영수증으로 다시 확인한다. clean baseline 이후 `recommendation_history`에는 `SCALPING/VCP_CANDID` 6건(5 `EXPIRED`, 1 과거 날짜 `WATCHING`), 매수 수량·매수 시각이 있는 행 0건, `VCP_SHOOTING`·`VCP_NEXT`와 해당 `trade_performance_facts` 0건이었다. 이 수치는 **실현 EV 0 또는 음의 EV의 증명은 아니다**. 후보에서 적격 진입·완료로 이어진 영수증 없이 세 조건식의 구독과 [VCP 전용 승격·감시 예외](../../src/engine/sniper_condition_handlers.py)를 유지할 근거가 부족하므로 퇴역을 선택한다. 실제 WS 메시지 절감량은 식별 계측 전까지 미상이다.
- **S15: 미구동 전용 주문 경로 퇴역.** HTS 목록의 실제 이름은 `s15_scan_base`, `s15_trigger_break`인데 [WS 구독 키워드](../../src/engine/kiwoom_websocket.py)는 각각 `_01` 접미사를 요구하므로 현재 PID는 두 식을 구독하지 않았다. clean baseline 이후 S15 추천·성과 사실은 0건이고 S15 단계 감사에서 표본을 얻지 못했다. 이는 **전략의 수익성 실패가 아니라 유입 미가동/표본 부재**다. 별도의 빠른 주문·복구 경로를 이름 매칭만 고쳐 되살리는 시험은 새 발견 구조의 목적에 맞지 않아 퇴역을 선택한다. 현재 미구독 상태이므로 S15 키워드 제거 자체의 즉시 WS 절감 효과도 주장하지 않는다.
- **결정 전제와 보전.** 위 조회는 `2026-06-05` 이후 DB/주문 소유권 원장과 현재 PID·코드/로그의 읽기 전용 조사이며, 브로커 미결 주문·보유의 독립 종결 영수증은 아니다. 작업공간 `data/runtime/s15_fast_custody/123456.json`에는 `RECOVERY_REQUIRED` 형식의 파일이 있으나 `runtime_effect=false`, `actual_order_submitted=false`이고, 당시 PID의 상대 경로인 릴리스 `src/data/runtime/s15_fast_custody`는 존재하지 않았다. 출처를 시험 파일로 단정하거나 삭제하지 않는다. 적용 직전 **선택 릴리스의 실제 cwd/env에 의해 결정되는 모든 custody 경로**, DB active row, 주문 소유권 원장, 브로커 미결·보유, Main 메모리 감시 대상을 같은 시점에 대사한다. 한 건이라도 실제 S15/VCP 주문·보유·복구 소유권이 남으면 신규 유입만 차단하고 청산·영수증·복구 호환 경로를 해당 건의 terminal 확인까지 보존한다. 과거 `WATCHING` 행은 자동으로 유효 주문 또는 0수익으로 취급하지 않으며, 현재 날짜·상태·브로커 대사 후 재편입 금지/만료를 결정한다.
- **코드 제거 범위.** [WS 구독 목록](../../src/engine/kiwoom_websocket.py)의 VCP 3식과 S15 2식, [조건 프로필·승격·S15 fast-track dispatch](../../src/engine/sniper_condition_handlers.py), [VCP 진입·FIFO 예외와 S15 bootstrap 연결](../../src/engine/kiwoom_sniper_v2.py), [VCP/S15 전용 상태 분기](../../src/engine/sniper_state_handlers.py), [S15 주문·복구 모듈](../../src/engine/sniper_s15_fast_track.py), [주문 영수증](../../src/engine/sniper_execution_receipts.py)·[계좌 동기화](../../src/engine/sniper_sync.py)·[DB loader](../../src/database/db_manager.py)의 전용 참조, source-quality 계약과 전용 테스트/allowlist를 영향 검토 대상으로 둔다. 공용 가격·수량·브로커 hard safety, 현재 보유·주문 청산 및 역사적 DB/원시 이벤트 해석은 제거하지 않는다. 남은 호환 분기는 실제 custody가 끝난 뒤 별도 삭제하며, 코드에 닿을 수 없는 신규 주문 경로가 없어야 한다.

## 구현·검증·배포 순서

1. **원천 계약을 먼저 닫는다.** 현재 source-only 시장 조사의 `observed_panel` 범위를 독립 기준으로 고정하고, 공식 원천으로 충분히 넓은 실시간 후보 집합을 안전하게 얻을 수 있는지 확인한다. 확보 불가 구간은 `unobserved`로 남긴다. 원시 condition 구독/응답 계측과 condition→WS item 귀속을 보강한다. 이 단계는 주문을 내지 않는다.
2. **새 queue/probe를 별도 owner로 만든다.** 위치 gate에 따라 `src/scanners/`를 소유자로 쓰고, 기존 Main의 감시·기계 입력/정책/주문 owner를 호출한다. 동일 코드의 route·source generation·probe→WATCHING 원자성, 재시작 복구, hard guard와 WS budget을 테스트한다. 9/28 고정 표본 및 다른 독립 날짜를 재생해 `discovered→queued→probed→input-ready→machine-action→submitted→terminal` 분모와 누락 원인을 보존한다. 현행 스캐너와의 제출 수 경쟁으로 선택하지 않고, 독립 시장 기회 분모에서 도달률·시차 및 비용 후 적격 결과를 본다.
3. **퇴역 전 custody 대사.** 적용 직전 DB `VCP_CANDID/SHOOTING/NEXT`, `S15_CANDID/FAST` 및 표기 변형, 당일·이월 감시, 실제 cwd/env의 S15 journal, 주문 소유권 원장과 브로커 양 시장 미결·보유를 대사한다. 주문번호·잔량·전략 소유권이 불명확하면 그 종목의 청산/복구 코드를 보존하고 신규 편입만 차단한다. 원본 원장과 과거 성과는 보존한다.
4. **condition 및 전용 코드 정리.** VCP 3식은 새 bootstrap과 재연결에서 실제 구독 요청을 만들지 않도록 제거하고, S15 2식의 죽은 구독 키워드도 제거한다. 다른 스캘핑 식은 식별/유일 기여/WS 비용 원장으로 별도 제거 목록을 확정한다. 구독 생성·실시간 I/D consumer·재편입·전용 주문 dispatch와 재시작 복구를 같은 식별자로 정리한다. runtime-only 이름 필터로는 이미 열린 서버 구독의 부하가 줄지 않는다. 남은 주문·보유 custody용 REG와 swing 구독은 유지한다. VCP의 FIFO/진입 예외와 S15 독립 fast-track·동기화·영수증 연결은 공용 경로의 회귀 검증과 함께 제거한다. 미결 소유권이 있으면 전용 신규 진입을 먼저 끊고 recovery-only 호환성을 terminal까지 보존한다.
5. **분리된 릴리스와 검증.** 퇴역만 담은 불변 릴리스를 먼저 만들어 신구독 VCP=0/S15=0, 신규 VCP/S15 후보·주문=0, 보유·주문 청산 경로 보전을 확인한다. 이를 새 queue 작업의 롤백 기준으로 삼아 옛 릴리스 복귀 시 VCP/S15가 조용히 재활성화되지 않게 한다. 그다음 새 발견/queue 릴리스의 기계 입력·제출 경로를 검증한다. 변경 전 공식 프로토콜 gate, 영향 Python/WS/condition/queue·주문/복구 회귀, source quality·CPU/RSS·REST 물리 호출·WS item peak, `git diff --check`, release-set/launcher/PREOPEN 검사와 구독/주문 롤백 경로를 닫는다. 장중에는 9/28 checklist의 기존 `bounded_tunable` 단일 축 규칙상 이 구조를 재기동 적용하지 않는다. 거래가 끝난 뒤 custody와 release selection을 다시 대사하여 불변 릴리스 선택·정상 기동을 수행하고 실제 PID 코드/환경/정책 SHA 및 첫 자연 source·WS·기계 판정 영수증을 별도로 확인한다. 적용 후 제출, 체결, terminal, 비용 후 EV/순익은 후속 자연 수용이며 배포 성공으로 대체하지 않는다.

계획 수립 당시에는 **1단계 원천 및 조건검색 측정만 일부 가능했고, 전체 시장 실시간 후보 계약·미평가 종목의 기계 입력·condition 원시 유입/WS 비용 귀속과 퇴역 전 브로커 custody 종결 영수증이 결손**이었다. 문서 작성만으로 릴리스 선택·재기동 권한이나 영수증이 생기지 않는다. 이후 코드 구현·검증과 남은 운영 문턱은 아래 날짜별 갱신과 [구현 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md)에 구분해 기록한다.

## 9/28 구현·코드리뷰 중간 영수증

초기 작업공간에서 신규 VCP/S15 유입 차단과 독립 대기열 핵심 계약을 구현했다. 이후 리뷰에서 `sniper_s15_fast_track.py`의 직접 S15 BUY 함수와 미사용 후보 무장 상태, `sniper_state_handlers.py`의 도달 불가능한 VCP_NEXT 매수 분기까지 제거했다. Main의 세 VCP 태그 사전 차단과 DB 재시작 로더의 WATCHING 재무장 차단은 유지하고, 주문·보유 row 및 S15 durable journal·청산 복구 참조는 남겼다. 실제 custody는 적용 직전에 다시 대사한다. 이 코드는 아직 릴리스·PID 적용 영수증이 아니다.

`src/scanners/zero_base_discovery_queue.py`는 날짜·코드·정확 route·원천 hash·관측시각을 키로 중복/오래된/충돌 관측을 구별하고, 신규 및 재평가 후보를 공정하게 claim한다. 결과는 `source_unavailable`, `required_feature_insufficient`, `assessed`로 분리하며, 원천 결손을 `BLOCK`으로 기록하지 않는다. claim 세대가 바뀌면 옛 `ENTER_NOW` 해결을 거부하고, 날짜가 다른 snapshot의 복원을 거부한다. 이는 스캐너 점수/승격 상한을 사용하지 않는 큐 원형이지만, 실제 관측 source, WS probe, Main의 동일 입력 기계 판정, WATCHING 편입과 제출은 아직 연결되지 않았다. 이 상태를 신규 스캐너 가동으로 표현하지 않는다.

공식 API 확인은 2026-09-28 약 12:13 KST의 upstream commit `953e5dbff123f437ab4d11a78a95191a685eb51f` 기준이다. 열람 경로는 `kiwoom/_data/kiwoom_api_spec.json`의 `ka10027`, `ka10171`, `ka10173`, `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`, Postman의 해당 항목이다. `kiwoom_docs`는 이 revision에 없었다. `ka10027`의 `/api/dostk/rkinfo`·`api-id`·요청 필드·`cont-yn`/`next-key`, 조건검색 목록/실시간 요청 및 REAL 02 I/D, REG/REMOVE 패킷 계약을 확인했다. 이번 코드 변경은 Kiwoom 요청/파서/패킷 형식을 바꾸지 않는다. 시장 전체 coverage와 원시 condition 식별·WS 비용은 이 확인만으로 해결되지 않는다.

코드 리뷰에서 다음 활성화 결손을 확인했다. 기존 `SCALPING_SCANNER_PROMOTED_TARGET` consumer는 Main에서 소유자 슬롯·WATCHING 상한을 적용하므로 새 큐를 이 이벤트에 그대로 연결하면 제로베이스 요구를 충족하지 않는다. `ka10027`의 현행 adapter 상한과 관측 패널은 상승 전수나 정확 route별 기계 입력을 보장하지 않는다. `analyze_target`의 기계 판정에는 유효 WS·tape·candle·비용 원천과 현재 policy bundle이 필요하다. 따라서 이 세 계약을 닫지 않고 신규 큐가 `ENTER_NOW` 또는 실주문을 만들게 하는 연결은 허용하지 않는다. 장중 체크리스트의 단일 `bounded_tunable` 규칙상 이번 구조 변경 재기동은 16:30 이후 재검토 대상이다.

12시대 읽기 전용 custody 예비 대사에서는 clean baseline 이후 VCP 과거 매수 소유 코드 4개와 현재 KRX/NXT 잔고 3행·미결 1행 사이에 코드 중복이 없었다. 기존 PID의 cwd/env 기준 S15 custody 경로는 없었고 작업공간의 `123456.json`은 `runtime_effect=false`, `actual_order_submitted=false`였다. 이 결과는 조회 시점의 **예비 무중복**이지 장후 release 적용 직전 브로커·Main 메모리·주문번호의 terminal 보증이 아니다. 원본 journal은 삭제하지 않았다.

초기 작업공간의 큐·condition·DB·WS 회귀 뒤, 실제 probe→기계 판정→Main 임시 DB→WATCHING 편입을 연결했다. 두 분리 릴리스에서 queue·probe·Main·WS·condition·S15·VCP 영향 회귀를 다시 수행하고, 실제 원천·부하 및 적용 직전 broker custody를 별도 수용한다. 코드 시험만으로 자연 제출·terminal·비용 후 수익성은 증명되지 않는다.

## 13시대 구현·리뷰 갱신

`KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true`는 기존 스캐너 루프 대신 세션별 KOSPI·KOSDAQ `ka10027` 2개 관측 패널을 읽는다. 각 패널은 최대 200행·최대 10페이지이며 `observed_panel`만 선언한다. 대기열은 KST 날짜·종목·정확 route·원천 SHA와 미평가 우선 순서를 보존하고, 회차당 최대 8개 probe를 claim한다. 2개 worker와 공유 Kiwoom 5회/초·source-only 4회/초 제한을 사용한다. 프로브는 WS 0B·0D만 임시 구독하고 동일 item·route·transport epoch·3초 이내의 새 시세를 확인한다. tick/candle REST는 정확 요청 코드를 고정하고 source-only로 분류한다. 기계 `ENTER_NOW`만 5초 이내의 source와 bundle SHA를 다시 확인해 Main의 기존 감시·AI 보조·주문 안전 경로에 넘긴다. `PROBE_READY` 임시 DB 행은 동일 ID의 메모리 감시 편입 성공에만 `WATCHING`으로 확정되며 재시작 loader는 임시 행을 재무장하지 않는다. 이 구조는 단독 주문 권한이 없다.

새 모드에서는 SCALPING 조건검색식 `CNSRREQ`와 그 원시 `I/D` 신규 편입을 중단한다. swing 조건식은 기존 독립 enable과 소유권을 따른다. 이는 새 발견 owner와 기존 조건검색 owner가 동시에 같은 슬롯을 선점하지 않도록 하는 아키텍처 전환이다. 개별 기존 식의 수익률이 0이거나 새 패널이 그 식의 모든 기회를 대체한다는 주장이 아니다. VCP 3식·S15 2식의 bootstrap 구독 및 신규 후보/주문 dispatch는 제거했고, 직접 호출 가능한 S15 신규 매수 함수도 삭제했다. S15 보유·미결 주문용 journal, SELL/취소·동기화·영수증 호환 경로와 기존 DB/원시 기록은 실제 custody가 terminal로 확인될 때까지 유지한다. 원천/구독 절감량은 실제 새 PID 영수증으로 측정한다.

리뷰에서 WS probe가 기본 4종 실시간을 요청하던 문제, 비동기 REG 완료 전 REMOVE 경합, NXT snapshot 키의 `_NX` 누락, KRX tick REST 코드가 `_AL`로 바뀔 수 있는 경로, REST 특징의 route/수신시각 결속 누락, 기계 계산 후 오래된 프로브 시각으로 감시 편입할 수 있는 경로를 찾아 수정했다. 정책 미선택 시 provider 호출 없이 `policy_unavailable`, 원천 결손 시 `source_unavailable`, 필수 특징 결손 시 `required_feature_insufficient`로 남긴다. 800개 후보의 메모리 큐 관측은 4.0ms, 8개 claim은 0.29ms였다(합성 단일 실행; 실제 API·WS 부하 측정이 아님). 공식 API 기준은 12:36 KST 재확인한 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`; 앞 절의 spec, core WS, realtime packet 및 Postman 경로와 함께 `kiwoom/_data/kiwoom_api_spec.json`의 `ka10003`(약 2312행), `ka10080`(약 23485행) 및 Postman 해당 항목을 13시대 추가 열람했다. 두 REST의 `stk_cd`는 KRX 평문, NXT `_NX`, SOR `_AL`을 명시한다. 요청 field/endpoint/FID 자체는 바꾸지 않았고, 기존 adapter에 명시 route 및 source-only 분류를 추가했다.

활성화 전 남은 문턱은 최종 회귀, 다른 날짜의 정확 WS/REST·기계 입력 재생, 조건식/WS 비용의 새 PID 계측, S15/VCP 적용 직전 브로커·DB·journal custody 재대사, PREOPEN/launcher/실제 PID 소비 확인이다. 13:42~13:44 KST source-only 실호출에서는 첫 4패널 중 2개만 완전했으나 공유 물리 호출 상한은 유지한 채 페이지 대기를 3초로 늘린 재시험에서 8.38초, 4패널 정상, 관측 757행을 확인했다. 이 수치는 시장 전수가 아니라 각 route 최대 200행의 패널 관측이다. 저장된 9/25·9/28 시장조사 패널의 큐 전용 재생에서는 원천 유효기간 120초와 패널 사이 10초 평가 dispatch를 보강했다. 관측 code-route의 첫 claim은 9/25 388/388, 9/28 845/862였으며 17건은 미claim으로 남았다. 즉시 source gap을 resolve한 모형이므로 실제 probe 처리량이나 두 날짜 기계·제출 성과로 해석하지 않는다. 장중 구조 재기동은 9/28 체크리스트의 POSTCLOSE 시간 경계 밖이다. 장기 점유 퇴출은 앞 절의 자연 재생에서 10분 적격 후보가 0이므로 실시간 퇴출 임계치를 새로 고르지 않는다. 관측 결손은 경제성 0으로 치환하지 않는다.

## 14시대 코드리뷰 수정보완

Main의 `PROBE_READY` 임시 행 생성 뒤 동기 감시 편입 또는 scheduler inbox 편입에서 예외가 나면 행·메모리 감시가 남을 수 있음을 발견했다. 두 경로가 같은 record ID의 임시 상태를 만료·해제하고 거절 영수증을 남기도록 수정했다. 기존 WS 구독이 있는 코드는 probe가 그 구독의 신선한 정확 route 0B·0D를 재사용하며 REG/REMOVE 및 요구 realtime type을 변경하지 않게 했다. 같은 평가·발견 시각의 미평가 후보는 관측 거래량을 순서 tie-breaker로 사용하되 새 유동성 탈락 하한은 만들지 않았다. S15의 호출되지 않는 그림자 후보 생성·BUY 가격 헬퍼도 제거했다. 해당 예외·재사용 회귀 41/14건, S15 custody 회귀 39건, queue/runtime/source 회귀 13건이 통과했다. 새 발견 후보 커밋과 적용 경계는 [구현 리뷰](../audit-reports/2026-09-28-zero-base-scanner-implementation-review-and-release-gates.md)에 기록한다.
