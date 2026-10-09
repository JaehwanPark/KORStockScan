# Main 보조 프롬프트 실제 연구 검토 — 2026-10-08

Owner: `DirectFamilySourceRepairMainMechanisticEntry`.

최종 추가 연구는 아래 “3차 완결 비교”에 기록했다. 수정된 세 비교 157/157쌍 완료, 누적 653/800회 차감·실제 응답 640개다. 다음 문단부터 400회 단계까지는 중간 이력이다. 총 상한 400회 중 **398회 예약·차감, 실제 응답 386개, 미응답 예약 12개, 잔여 2회**다. 후속 추가 연구에서는 실제 응답 198개를 확보했다. 실제 native 대비 채택 기준을 충족한 scope가 없어 정책을 발행하거나 봇을 재기동하지 않았다.

## 원천과 비교 계약

- 최초 v5 부모: `cdacf6eed9d77e95d0bdf1a417ec2549323ea2491b91e41b8f948b900434895f`.
- 추가 연구 v6 부모: `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`.
- 원천일: 9/21·22·23·28·29·30, 10/2·6·7의 9영업일, normalized 58 partition. 최초 확인점 117,763건, 확정 77,903/U 39,860.
- v6는 변경 없는 115 scope의 원 native 결과를 재사용하고 변경된 13 scope를 전체 관련 prefix에서 다시 탐지했다. 122,298개 확인점 census에서 고정 hash reservoir 181개만 저장했다. 기계 목록을 다시 선발하거나 기존 원장을 복제하지 않았다.
- WIN/FAIL_STOP/FAIL_TIMEOUT은 확인 ask·비용 .0023·30분·비용 후 +.4%·soft −3% 선도달 계약이다. 원천/응답 무효와 U는 실패나 정상 veto가 아니다. 확정 W/F 내 표집은 label/verdict를 사용하지 않는다.
- 승률은 유효 공통 쌍에서 TP/(TP+FP), 동률이면 TP 수로 판단한다. PASS 분모 0은 null이다. 개발 지점 20개와 그 뒤 검토한 고정 표본 80개는 추가 후보 평가에서 제외한다.

## 최초 연구에서 발견한 문제

1. H1 개발의 공통 유효 쌍 18개에서 승리 2개를 추가 PASS했으나 실패 2개도 추가 PASS했다. 개발 결과만으로 정책을 채택하지 않았다.
2. 실제 v5 native 전송을 재현한 현행 응답 32개 중 22개가 512토큰에 도달하며 JSON 파싱에 실패했다. 정상 차단이 아니라 응답 계약 결손이다. native 비교의 공통 유효 쌍은 10개였고 scope별 채택 기준을 만족한 후보는 없었다.
3. 현행 arm이 유형별로 다른데 최초 H2는 `existing_wording` arm을 사용했다. 따라서 처음의 1,024토큰 비교도 일부 범위에서는 입력 구성과 문구가 함께 바뀐 비교다. 문구 단독 효과로 해석하지 않는다.
4. 표본은 scope별 순환으로 정했으나 호출 순서는 날짜순 저장 순서를 따랐다. 연구 호출을 봉인된 selector 순서로 수정했다. 같은 80개 명단을 유지했으며 W/F에 따라 재추출하지 않았다.
5. 임시 스크립트 이름 `h2.py`가 httpcore의 선택 의존성 import와 충돌했다. 후속 1회는 저장된 stack으로 원인을 확인했고, 앞선 동일 `BlockingIOError` 10회도 같은 환경에서 발생했으나 개별 stack은 없다. 이 11회 및 중단 시 불확실 예약 1회는 모두 예산에서 차감·보존했다. 이 12회를 실제 AI 응답으로 보고하지 않는다. 스크립트 이름을 변경하고 모듈 CLI로 전환했으며, 로컬 예외가 나면 해당 묶음을 즉시 중지하도록 보완했다.

## 추가 연구 설계

현재 릴리스 `pre-after-intraday-20261008-v1`의 실제 reader가 128개 binding을 검증하여 작은 불변 capture를 남겼다. 연구 코드와 실제 reader hash 차이를 무시하도록 운영 검증을 풀지 않았다. 오프라인 대조군만 해당 capture를 참조하고 실제 발행은 기존 live parent/reader 검증을 유지한다.

H3는 현행 arm별로 등록한다: `existing_wording`, `reversal_complete_source_v7`, `reversal_entry_geometry_v5`, `reversal_fact_roles_v2`. 각 범위의 현행/후보 `candidate_input` bytes 일치를 확인했다. 과거 맥락과 현재 반전의 위험을 구별하고 비용·spread를 중복 반영하지 않도록 하며, 필수 signal ref를 유지한 간결한 JSON을 요구한다.

각 arm에서 실제 native 설정 5개 확인점과 같은 생성 설정의 최대 20개 확인점을 사전 고정했다. native/controlled의 동일 후보 요청은 shared store에서 exact 재사용한다. 새 candidate를 매 장후 자동 생성하는 기능은 추가하지 않는다.

## 증거와 구현

- [연구 계획](../proposals/main-auxiliary-prompt-research-and-intraday-adoption-plan-2026-10-08.md)
- [최초 allowance](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/allowance.json)
- [400회 추가 승인](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/allowance-topup-400.json)
- [v6 모집단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/v6-machine-research-population.json)
- [v6 H3 실험 명단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/v6-h3-experiments.json)

## 최종 결과

아래는 v6에서 현행/후보의 입력과 1,024토큰 생성 설정을 맞춘 **78개 확인점 중 유효 공통 58쌍**이다. 승률 표기는 `WIN+PASS / 전체 PASS`다. `—`는 PASS 분모 0으로, 0%나 100%가 아니다. 시장별 합계는 진단용이며 실제 선택은 세부 symbol type·price band·route scope로 한다.

| 구분 | 시장 | 유효 쌍 | 현행 PASS 승률 | H3 PASS 승률 | 주요 변화 |
| --- | --- | ---: | --- | --- | --- |
| 삼성 | PRE | 4 | 1/1, 100% | — | 기존 승리 PASS 1개를 더 차단 |
| 삼성 | REGULAR | 2 | — | 1/1, 100% | 승리 1개를 복원했으나 현행 승률은 미정의 |
| 삼성 | AFTER | 3 | — | — | 양쪽 모두 승리 지점을 차단 |
| 비삼성 | PRE | 14 | 2/2, 100% | 1/1, 100% | 승리 PASS 1개 감소 |
| 비삼성 | REGULAR | 20 | 2/2, 100% | 3/3, 100% | 합계 승리 PASS 1개 증가; 세부 scope의 비교는 별도 |
| 비삼성 | AFTER | 15 | 1/3, 33.3% | 1/2, 50% | 실패 PASS 1개 감소 |

동일한 58쌍 전체의 참고 합계는 6/8→6/7이다. 유형별 추출 비중이 다른 표본의 혼합값이므로 전 시장 누적 승률이나 전체 정책 교체 근거로 사용하지 않는다. 현행 응답은 78개 중 65개, H3는 70개가 유효했다. H3의 나머지 8개는 잘림이 아닌 인용 중복 2개·위험과 근거 연결 결손 6개였다.

세부 scope에서 개선한 곳은 `other_non_fixed|AFTER|GE_100000|SOR` 하나다. 9/22의 `003670` 동일 종목 두 지점에서 현행은 실패를 PASS·승리를 CAUTION, H3는 실패를 CAUTION·승리를 PASS로 판정했다(0/1→1/1). 표본은 2개이며, 실현 매매 손익이 아니다.

이 두 지점을 다시 실제 native 전송 계약으로 확인했으나 현행 응답이 모두 잘려 유효 공통 쌍은 0이었다. 출력 한도만 1,024로 바꾼 native 비교에서는 현행이 둘 다 CAUTION, H3가 승리만 PASS했다. 승리 복원은 관찰됐지만 현행 PASS 분모가 0이어서 정해 둔 승률 우월성 비교는 미정의다. 작은 표본이라는 별도의 최소표본 gate를 추가해서 보류한 것이 아니다.

## 출력 계약 실험과 다음 보완 대상

최초 native pilot 20개에 위 scope의 미호출 확인점 1개를 보충한 **동일 21개 입력**을 비교했다. 두 비교에서 현행의 system/user/schema/model/reasoning은 동일하고 출력 한도만 바꿨다. 이미 저장된 exact 요청 2개는 마지막 보충에서 재사용하여 총 예산 2회를 남겼다.

| 현행 전송 | 실제 응답 | JSON 잘림 | 최종 유효 응답 | H3와 유효 공통 쌍 |
| --- | ---: | ---: | ---: | ---: |
| 실제 native, 512 tokens | 21 | 16 | 5 | 5 |
| native 그대로, 1,024 tokens | 21 | 0 | 20 | 18 |

512 제한 때문에 정상 비교를 잃는 결함이 재현됐다. 1,024에서 남은 1개는 PASS의 필수 근거 인용 결손이었다. H3 역시 이 21개에서 인용 오류 2개가 남아 공통 쌍은 18개다. 설정만 맞춘 비교와 실제 native 비교를 섞거나, 깨진 응답을 정상 veto로 간주하지 않았다.

우선 보완 대상은 실제 보조 전송의 출력 한도와 근거 인용 구조다. 검증한 1,024토큰 설정을 운영 전송에 연결할 때에는 기존/등록 프롬프트 각각의 실제 요청 body를 대조하고, 원 응답을 보존한 채 필수 signal coverage·risk binding 검증을 유지해야 한다. 인용 ID 중복·잘못된 배열 배치를 줄이는 출력 설계는 별도 후보로 검증한다. 이번 연구에서 validator를 완화하거나 무효 응답을 PASS로 복구하지 않았다.

새 보조 문구의 **장중 적용 완료는 아니다**. 최초 요청에는 기계·보조의 기존 운영 한도 변경이나 주문 보호 완화가 없으며, 원천일 10/7의 기존 15,228회 사용 기록도 그대로다. 잔여 2회는 자동으로 다음 장후 예산이 되지 않는다.

## 구현·리뷰·저장 검증

- 추가 예산은 기존 key와 최초 allowance를 보존하고 승인된 400회 top-up만 참조한다. 정기 100회 경로와 별도다. 개발 사례·미완료/무효 응답을 성과 분모에 넣지 않는다.
- 연구 설정/불변 campaign/평가 경로를 분리했다. 정기 latest 덮어쓰기를 막고, 개발·설정만 맞춘 비교·출력 한도 가상 변경 결과의 직접 발행을 차단한다. 등록 프롬프트가 이미 운영 대조군이면 raw registry 전송을 재사용한다.
- 실제 reader capture는 부모·128 scope·입력 버전·원 코드 SHA를 검증한다. 코드가 다른 연구 세션을 이유로 운영 reader 검증을 풀지 않았다.
- 리뷰에서 불확실 호출의 원 응답 보존, 로컬 예외 시 묶음 중단, 정정된 U가 누적 표본으로 복귀하는 문제, 날짜순 호출, 출력 설정/입력 arm 혼동을 보완했다.
- 연구/원장/기존 튜닝/v6 연결 회귀 **60 PASS**, compile 및 `git diff --check` 통과. 실제 provider는 테스트로 호출하지 않았다. 문서는 링크·단일 owner·print-only parser로 검증한다. 다른 세션의 broker/WS/clock/배포 변경은 이 검토 범위에 포함하지 않는다.
- 연구 메타데이터 디렉터리는 집계 시 약 9.4 MiB, 직접 참조하는 요청/응답 압축 object는 약 2.62 MiB다(기존 재사용 object 포함, 공유 DB 오버헤드·작업용 코드 checkout은 별도). normalized 원장 복제는 0건이다.
- [최종 기계가독 집계](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/execution-review.json), [확인점별 CSV](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/pair-results.csv). 원 응답은 기존 shared comparison store에 보존했다.

## 3차 완결 비교 — 추가 허용 지시 반영

사용자 “한도를 추가해도 되니 불완전 연구로 종료하지 마라” 이후 응답 결손을 보완하고, 수정된 세 연구의 **157/157 공통 쌍을 모두 완료**했다. 예정 호출 미완료 또는 무효 응답으로 제외한 쌍은 세 연구 모두 0이다. 기존 실패한 출력 계약 실험은 진단 이력으로 보존하며 그 무효 응답을 성공한 비교에 합치지 않는다.

- 누적 상한 **800회**, 차감 **653회**, 실제 응답 **640개**, 미응답 예약 **13개**, 잔여 **147회**. 398회 단계 이후 실제 응답 254개를 추가했으며 새 compact 응답은 전부 원 union validator를 통과했다.
- 200→400→600→800 승인은 각각 불변 파일을 이전 승인 hash로 연결한다. 같은 예산 key를 사용하고 실패/불확실 예약을 환불하거나 초기화하지 않았다. 정기 장후 원천일 기록 15,228회는 그대로다.
- 추가 미응답 1건은 새 schema를 만들면서 이전 `response_schema_sha256`를 남긴 로컬 검사 결함이었다. HTTP 요청 전에 ValueError가 발생한 stack을 보존하고 schema/instance hash를 함께 갱신했다. 이후 실제 provider payload projection 검사를 회귀 테스트에 추가했다. 이 1건도 차감을 보존했다.
- 초기 H4 준비 스크립트의 arm 순서 불일치는 호출 전 수정했다. 해당 사용하지 않은 설정은 역사 자료로 남기고 `-v2` 캠페인의 60쌍 전부에서 현행/후보 arm·입력·schema 일치를 검증했다. 잘못 연결한 설정으로 AI를 호출하지 않았다.

### 응답 계약 보완의 범위

원 입력의 시각·수치·신호·비용·목표를 보존하고 긴 신호/근거 ID를 짧은 별칭으로 바꿨다. 모든 신호의 확인을 명시적으로 응답하고, 하나의 핵심 위험과 그 위험에 연결된 근거를 선택하도록 schema를 구성했다. 원 provider 응답과 receipt는 수정하지 않으며, 재집계 때 원 ID로 되돌려 기존 validator로 다시 검증한다. 잘림·미응답·근거 결손에 PASS를 만들어 넣지 않는다.
공통 출력 지침도 함께 바뀌므로 이를 **ID 길이 하나의 단독 효과**로 해석하지 않는다. 응답 계약 보완 비교는 기존 판단 본문/arm/model/1,024토큰을 유지한 패키지 비교다. nested anyOf와 enum 구성은 [OpenAI 공식 Structured Outputs 문서](https://developers.openai.com/api/docs/guides/structured-outputs)를 확인했다.
연구 코드 owner는 `src/engine/scalping/reversal_auxiliary_research_wire.py`다. `G.request`의 기존 운영 계약을 바꾸지 않는 연구 전용 projection이며, 연구의 compact 결과를 현재 운영 registry에 그대로 발행하지 못하도록 차단한다.

### A. 같은 출력 계약에서 위험 문구 비교 — 새 60점

이전 검토 178점을 제외하고 결과를 보기 전에 scope별 hash 표본을 고정했다. 양쪽 모두 같은 compact 입력/응답 계약이다. 따라서 아래 “현행”은 **현행 판단 문구를 공통 연구 형식으로 실행한 대조군**이며 운영 512토큰 호출 자체가 아니다.

| 구분 | 유효 쌍 | 현행 문구 PASS 승률 | H4 후보 PASS 승률 |
| --- | ---: | ---: | ---: |
| non_samsung|AFTER | 14 | 7/13 (53.8%) | 7/13 (53.8%) |
| non_samsung|PRE | 18 | 8/10 (80.0%) | 13/16 (81.2%) |
| non_samsung|REGULAR | 22 | 22/22 (100.0%) | 19/19 (100.0%) |
| samsung|AFTER | 2 | PASS 0 — 승률 null | 1/1 (100.0%) |
| samsung|PRE | 2 | 1/1 (100.0%) | 1/1 (100.0%) |
| samsung|REGULAR | 2 | 2/2 (100.0%) | 2/2 (100.0%) |

전체 혼합 집계는 40/48(83.3%)→43/52(82.7%)로 악화했다. 비삼성 정규의 승리 3건 추가 차단과 프리의 실패 1건 추가 통과가 있어 전역 교체하지 않는다. `other_non_fixed|PRE|20000_TO_100000|NXT`에서는 1/1→2/2로 같은 100% 승률에서 승리 PASS가 1개 늘었다.

### B. 기존 판단 본문을 유지한 응답 계약 패키지 비교 — 65점

기존 1,024토큰 대조군의 유효 응답 65개를 전부 사용했다. 응답의 유효성으로만 선택하고 W/F·PASS 여부로 제외하지 않았다. 그 원 요청/응답 ID를 그대로 재사용했으며 새 형식에서도 65/65 유효 쌍을 완료했다. 이 표본은 이미 본 사례에 대한 원인 분리 연구로, 새 문구의 독립 평가로 재사용하지 않는다.

| 구분 | 유효 쌍 | 기존 응답 계약 PASS 승률 | 새 응답 계약 PASS 승률 |
| --- | ---: | ---: | ---: |
| non_samsung|AFTER | 15 | 1/3 (33.3%) | 6/12 (50.0%) |
| non_samsung|PRE | 14 | 2/2 (100.0%) | 7/9 (77.8%) |
| non_samsung|REGULAR | 22 | 2/2 (100.0%) | 20/21 (95.2%) |
| samsung|AFTER | 5 | 0/1 (0.0%) | 3/4 (75.0%) |
| samsung|PRE | 4 | 1/1 (100.0%) | 2/2 (100.0%) |
| samsung|REGULAR | 5 | PASS 0 — 승률 null | 5/5 (100.0%) |

승리 PASS는 6→43개로 늘었지만 실패 10개도 모두 PASS했다. 혼합 PASS 승률 81.1%는 같은 기계 표본 55/65(84.6%)보다 낮다. **응답이 유효해진 것과 오판 차단 성능 개선은 다르므로**, 출력 계약 보완만으로 전체 정책 개선을 선언하지 않는다.

### C. AFTER의 스프레드 내 반등·단기 가격 정체 가설 — 새 32점

B와 A의 오판 분석에서 AFTER의 `confirmation_pct <= spread_pct`와 `return_10t_pct <= 0`가 동시에 나타나는 사례를 확인했다. 과거 매도 우세/VWAP 미회복 단독 veto를 되살리지 않고, 신호 전체에서 독립적인 가격 진전이 없는 조합을 현재 위험으로 판정하도록 H5를 고정했다. 비반전 신호에 확인 수치를 합성하지 않고 비용을 다시 차감하지 않는다.
이전 검토 238개 key를 제외한 새 표본 32개를 고정한 후 양쪽 64회 실제 호출을 완료했다. 표본/W/F를 보고 seed나 후보 문구를 바꾸지 않았다.

| 구분 | 유효 쌍 | 현행 문구 PASS 승률 | H5 후보 PASS 승률 | 승리 차단 변화 | 실패 차단 변화 |
| --- | ---: | ---: | ---: | ---: | ---: |
| non_samsung|AFTER | 28 | 16/23 (69.6%) | 9/13 (69.2%) | +7 | +3 |
| samsung|AFTER | 4 | 2/3 (66.7%) | 3/4 (75.0%) | -1 | +0 |

비삼성 전체는 실패 3개를 차단하는 대신 승리 7개를 추가 차단해 승률도 소폭 낮아졌다. 전체 AFTER 교체는 하지 않는다. 삼성 AFTER의 개선은 실패 차단이 아니라 승리 1건 복원이며, 이를 실패 탐지 향상이라고 설명하지 않는다.

### 세부 경로별 연구 후보와 실제 적용 상태

| 연구 후보 | 정확 scope | 대조→후보 PASS 승률 | 판단 |
| --- | --- | --- | --- |
| h4_wording | `other_non_fixed|PRE|20000_TO_100000|NXT` | 1/1 (100.0%) → 2/2 (100.0%) | 공통 compact 계약 아래 개선 |
| h5_after_quote_bounce | `other_non_fixed|AFTER|LT_20000|SOR` | 3/4 (75.0%) → 1/1 (100.0%) | 공통 compact 계약 아래 개선 |
| h5_after_quote_bounce | `other_non_fixed|AFTER|20000_TO_100000|SOR` | 3/4 (75.0%) → 3/3 (100.0%) | 공통 compact 계약 아래 개선 |
| h5_after_quote_bounce | `samsung|AFTER|ALL|SOR` | 2/3 (66.7%) → 3/4 (75.0%) | 공통 compact 계약 아래 개선 |

위 네 경로는 연구의 raw 승률/동률 TP 기준을 충족한 후보다. 최소 표본·일수·EV·기존 제출 통과 같은 추가 채택 요건은 적용하지 않았다. 각 scope의 실제 비교 분모를 그대로 공개하며, 표본이 없는 다른 경로까지 일반화하거나 기존 등록 정책을 철회하지 않는다.
**운영 채택·배포·PID 소비는 미실행**이다. 현행 운영 요청은 compact 형식/decoder를 지원하지 않아 해당 결과를 문구만 복사하면 연구와 다른 요청이 된다. 이는 경제성 추가 gate가 아니라 전송 계약 불일치다. 장중 인계에는 동일 encoder/schema/decoder의 실제 registry/provider 경로 연결, 원 raw receipt 보존, 정확 payload parity, 기존 source/claim/주문 보호 검증을 먼저 완료해야 한다. 현 연구 결과를 실제 운영 native 512토큰 대비 우월성이 검증된 결과로 바꾸어 부르지 않는다.
개선되지 않은 경로는 현행 유지다. 새로운 REGULAR 후보를 선택하지 않았으므로 무표본 PRE/AFTER에 이번 후보를 새로 복사하지 않는다. 기존 부모의 상속 상태를 그대로 유지한다.

### 검증·보관·재현

- 구현→리뷰→schema hash/arm 연결 보완→재리뷰→관련 **76개 테스트 PASS**. 무실호출 provider projection, 원 사실/ID roundtrip, 거부/누락/잘못된 근거 차단, 예산 이력, 원 응답 보존, 독립 namespace, 정확 campaign 발행 방지, 원장 재사용을 검증했다. Python compile과 diff 검사를 수행했다. Kiwoom 경로와 매매 프로세스는 변경하지 않았다.
- 최종 봉인 보고서: `data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/reports/f9ba2741499504163b7a68964839b482cc8a794c4cb5178fba8d7a2cc2798e7f.json`.
- 행별 결과: `data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/completed-study-pairs.csv`. 원 snapshot·provider request/result는 공유 object store의 기존 ID로 참조한다.
- 최종 세 연구/기존 호출의 직접 참조 압축 object 합계 약 4.12 MiB(재사용 포함, 공유 DB overhead 제외). 대형 원장 복제 0개. 확인 시 디스크 75%, 여유 37 GiB.
- 이전 불완전 프로토콜의 planned/reserved 상태는 이력으로 남는다. 해당 캠페인은 자동 실행 owner가 없으며 이번 완료의 분모에서 분리했다. 불확실 예약을 재시도하거나 미응답을 정상 차단으로 재분류하지 않는다.
- 별도 세션의 source 진단·REST/WS 계획·현재 checklist 변경은 보존했다. 본 연구 때문에 봉인 checklist·정기 장후 최신 보고서를 덮지 않았다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry` 한 개다.
