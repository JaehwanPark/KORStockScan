# 2026-09-11 장후 모니터링·implement-now 2-pass 검토

- source date: `2026-09-11`
- review scope: 장후 필수 체인, authoritative recommendation intake, 허용된 source-only 구현과 직접 consumer
- runtime authority: 코드·report·handoff 수리만 허용. 주문·수량·가격·threshold·provider·hard safety는 변경하지 않음

## 운영 장애와 수리

최초 실패는 22:13:06 postclose verifier의 `code_improvement_workorder_native_id_duplicate`였다. Pattern Lab의 날짜가 붙은 concrete review와 generic follow-up이 모두 `order_pattern_lab_ai_review_ai_review_followup_2026_09_11`을 발급했다.

- `2881a209`: generic follow-up ID를 `order_pattern_lab_ai_review_generic_ai_review_followup_2026_09_11`로 분리하고 충돌 회귀 테스트를 추가했다.
- canonical Pattern Lab metadata-only refresh 뒤 12개 ID가 모두 유일했고 workorder 58개도 모두 유일했다.
- 후행 verifier에서 새로 드러난 결함은 microstructure 진단 주문이 `non_selected_orders`에만 남는 handoff 불일치였다. verifier는 source의 모든 진단 주문을 selected handoff에서 요구한다.
- `0d6a82ae`: `microstructure_reaction_context` native 주문을 max-order 한도 밖에서도 selected handoff로 보존했다. 실제 9/11 generation에서 필수 두 ID가 selected에 포함됐다.

검증 결과는 Pattern Lab/workorder/verifier 402건 통과, 전체 관련 suite 1,270건 통과다. release의 공유 `data` symlink 때문에 `git check-ignore` 두 검사가 환경상 exit 128이었고, 동일 observation-source-quality 파일을 일반 worktree에서 다시 실행해 175건 전부 통과했다. compile과 `git diff --check`도 통과했다. P0~P2 미해결 코드 finding은 0이다.

## Pass 1 전수 판정

최신 전수 intake는 78행이며 구현 요청 26, 비구현 52다. 구현 요청 26개는 모두 `runtime_effect=false`, `allowed_runtime_apply=false`다. 이미 producer가 `closure_requires_new_evidence=true`와 `implementation_only_closure_allowed=false`를 선언한 8개는 기존 evidence blocker를 유지했다. 나머지 18개는 관련 producer·consumer·테스트를 다시 검토했다.

추가 코드 결함은 위 두 handoff 결함뿐이었다. 18개 요청의 instrumentation과 report 계약은 관련 테스트를 통과했지만 다음 exact evidence가 아직 없으므로 `blocked_missing_evidence`로 분류한다.

| Native ID 묶음 | 최신 직접 근거 | 남은 acceptance |
| --- | --- | --- |
| Entry prompt 2개 | KRX exact parent 3개, NXT 2개의 `exact_cost_aware_label_parent_missing` | 같은 parent의 검증 비용·outcome을 기존 bounded offline consumer에 결속 |
| Broker/fill/post-submit/source taxonomy/Telegram 5개 | exact-attempt contract는 pass이나 `BROKER_RECEIPT` event 0; submitted bundle은 NXT probe 2개 | 실제 broker receipt·fill/cancel·post-submit terminal을 같은 attempt에 결속 |
| Microstructure 2개 | `evaluation_venue_missing_or_conflicting=117`, `evaluation_anchor_contract_missing=1` | 원 row의 venue/route 및 anchor identity가 있는 새 exact source |
| Unknown-token provenance 1개 | source-fetch JSON unknown 2,570, candidate-pool JSON unknown 280 등 reviewed warning 4단계 | 원 producer가 명시적 provenance 또는 reviewed unavailable label 발급 |
| Pipeline compaction 1개 | raw-derived 155,243 대 producer 154,793, manifest valid, raw suppression OFF | 원 producer의 lossless flush/identity parity receipt |
| Scanner/WS 7개 | 20:00 snapshot의 subscription state unavailable 29, current freshness unusable; 과거 row의 repair·BBO·terminal 연결이 불완전 | 새 exact generation의 ranked→terminal 보존과 REMOVE/REG/cooldown/BBO receipt |

결손 값을 0이나 정상 상태로 합성하지 않았고 provider 재호출, WS 재구독, threshold 완화, 주문·매매 process 재기동은 수행하지 않았다.

## 위젯·에피소드 추천

- widget expansion 10개는 모두 `research_watch`이며 표본 수집 외 runtime enrollment 권한이 없다.
- widget signal 4개는 모두 holdout 실패로 runtime promotion이 거절됐다. 9/14 runtime policy는 observation-only, selected symbol 0이다.
- low-price 추천 5개는 source-only review/defer 또는 evidence 부족이며 새 live profile 설치 조건을 충족하지 않았다.
- 20:10 widget evaluation은 네 producer가 9/11을 사용해 성공했고, 21:15 machine final refresh는 `expansion → attribution → weakness → timing → approval → checklist`를 완료해 22:21:10 success로 종료했다.

따라서 이번 generation에는 새 위젯/에피소드 매매 service를 설치·기동할 승인 가능한 native recommendation이 없다. 기존 서비스와 policy pin은 유지한다.

## Pass 2와 fixed-point

21:05 paired replay terminal 뒤 변경된 AI calibration/optimizer fingerprint를 반영해 workorder를 다시 생성하고 companion을 최신 native ID, row hash와 source hash에 재결속했다. Pass 2 재-intake 결과는 `intake_total=79`, `implementation_requested_total=27`, `nonimplementation_total=52`, `eligible_actionable_open=0`, `implement_now_unaccounted_count=0`, `intake_unaccounted_count=0`이다. 21:05 replay에서 KRX/NXT prompt parent 두 ID가 새로 생기고 이전 NXT ID 하나가 제거됐다. 두 신규 ID도 동일한 exact cost-aware label 결손을 직접 확인해 `blocked_missing_evidence`로 분류했다. decision-changed eligible 항목은 0이고 현재 27개 구현 요청은 모두 명시적으로 분류돼 fixed-point다. Evidence blocker는 코드 완료나 경제성 완료로 바꾸지 않는다.
