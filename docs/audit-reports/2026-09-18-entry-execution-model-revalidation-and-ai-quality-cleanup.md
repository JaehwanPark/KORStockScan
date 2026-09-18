# Entry 실행 모델 재검증 및 AI 품질 과거 산출물 정리

2026-09-18 KST. 사용자 승인 범위는 재사용 entry 실행 모델 재검증·반복 코드 리뷰/수정보완·관련 commit/push/배포 및 불필요한 과거 `ai_decision_quality_daily_materialization` 산출물 삭제다. 이전 승인된 compact family의 제한 재생성으로 다음 PREOPEN carry 정책 연결도 확인한다. 전체 장후 재실행·주문·봇 재시작·env/provider/threshold/guard/cron 변경은 실행하지 않는다.

현재 선택 배포를 재확인해 이전 unsupported-only 모델이 아닌 `7eac0e1b6`의 운영 경제성 구현을 기준으로 검토했다. [Entry 경제성 완결 review](2026-09-18-entry-split-economic-completion-review.md)의 초기 완전체결·frozen 정책/TTL/원 비용 owner·독립 full holding SELL 지원 범위와 partial/no-fill cancel/late fill·ADD/partial SELL·시장/AI 입력 결손의 unsupported/pending/null 경계를 유지한다.

| 발견 및 보완 | 검증 경계 |
|---|---|
| Compact가 검증 모델을 승인하면서 legacy 고정 기간/고정 비용 `arms`를 읽음 | 비용 후 EV·원화 순익·stress는 검증된 독립 `operating_arms`만 사용. legacy/path는 백분율 진단이며 일별 순익/승격 근거 불가. |
| 운영 결과의 stress EV/진입 시각 누락 | 기존 원가 owner로 계산한 stress 순익의 동일 budget EV 및 실제 모델 최초 체결 시각 생성. |
| 운영 depth의 다른 종목/venue/session 재결속 가능 | 원 native scope를 명시 검사. frozen 구현 버전 불일치도 source gap, 순익null. |
| 모델 validated flag만 확인하고 정확 scope·선행 완료 근거 미소비 | 동일 구현/scope·봉인된 actual model calibration/holdout·20개의 독립 episode·compact 학습 이전 완료 가용 시점을 검사. 모델과 후보 holdout 분리. |
| 최초 체결 전 pending reservation 누락 | 한 포지션 CF 예약을 최초 주문 관측부터 독립 청산까지 적용. 충돌은 순익null. |
| 정상 큰 atomic 운영 generation이 16MiB 제한으로 빈 입력 처리 | atomic JSON/gzip generation을 정상 읽기. 큰 JSONL 원천은 기존 streaming projection을 유지. 추가 성능 guard/서비스/module 없음. |

Self review→보완→재리뷰→영향 회귀361건 PASS(병행 완료 순익 수리 `a849b77e8` 보존·rebase 후 최종 재검증), 최신 변경의 owner/model 경계 보완16건 및 compact producer→calibration→publisher→consumer→summary 연결17건 PASS. compile/diff/document parser와 최종 immutable release 검증은 `/home/ubuntu/KORStockScan/tmp/entry-execution-revalidation-20260918/validation.json` 및 로그가 소유한다. 합성 model/정책 fixture는 실제 체결·경제적 개선이 아니다. source hashes/commit·release/selector CAS·actual PID 미소비는 같은 디렉터리 `deployment.json`에 기록한다.

과거 baseline은 `build_quality_baseline(labels)`의 일자별 진단 산출물이며 운영/누적 라벨/paired evaluator의 역사 입력이 아니다. source/deploy에서 same-day materialization와 wait 소비만 확인했다. active policy/모델/current 소비 후보 JSON2,755개에서 삭제 후보 path/hash 참조0을 확인했고, 각 일자의 원 라벨이 보존돼 재생성 가능하다. 최신 source9/17와 이전9/16 baseline은 유지했다. 이전35개(7/27–9/15), 총6,814,689bytes를 native generation lock·active FD·path/mtime/size/hash 검증 후 삭제했다. 관련198개 라벨/paired/control/lifecycle/current/selector 파일의 byte hash는 삭제 전후 일치한다. 실제 원천/체결/계정·custody/order ledger/모델·holdout/policy/release/rollback 증거와 가족 stage 자체는 보존한다. `cleanup-plan.json`, `cleanup.json`이 삭제 목록/원 해시/원 라벨/보호 증거를 소유한다.

실제9/17 entry report는 모델 source_gap·validated scope0·candidate0·운영 EV/일별 순익null이다. compact 실제21건의 원 stop/응답 계약/terminal 결손은 소급 생성하지 않는다. 유효 경제성 비교가 없으면 기존 Main compact9scope를 다음9/21 준비 정책으로 carry하고 entry 정책은 keep-original을 유지한다. 제한 재생성/정책/consumer/family strict 최종 결과는 `regeneration.json`에 기록하며, 전체 native DONE 및 다른 family blocker는 바꾸지 않는다. 자연 정확 버전/PID·완전 source/model holdout·별도 candidate holdout·비용 완료 실현 성과는 기존 KiwoomCommonHealthOpportunityCostAcceptance0917 owner의 OPEN이다. 정확 ETA는 미확정이다.

Project/Calendar 외부 sync와 provider 호출·실제 주문·봇 restart/full PREOPEN은 실행하지 않는다.
