# Main 다중 정책·미사용 파일 실행 검토 — 2026-10-07

사용자는 두 계획의 구현·반복 코드리뷰·통합 배포·재기동·미사용 파일 삭제를 승인했고, 새 정책을 오늘 적용하도록 지정했다. 이전 기존 미커밋 변경만 통합하던 작업과 이번 신규 기능 실행을 구분한다.

## 구현·연구 대조

기존 K kernel와 V1 auxiliary contract는 원 SHA를 유지한다. 공통 scalping branch module은 normal native past-only first/confirm/pending/invalid/expiry를 live/offline에서 공유한다. 새 native v2는 12셀·phase별 계약·raw cumulative Fraction 선택·parent CAS·준비/활성 분리를 강제한다. FIRST 요청 bytes를 보존하며 삼성 REGULAR/SOR/005930_AL에 CONFIRMED 분기를 추가한다.

필수 item 결손으로 기존 50개 중 18개를 제외했다. 공통 engine 유효 확인점 32/32 WIN, 독립 target clocks 6개다. 수정 문구 5 arm×32점 실제 재호출 160회에서 complete_source_v7 PASS 25/32, PASS WIN 25/25였다. 이전 문구 160회와 모두 합친 실제 호출은 320회다. 후행 결과는 input/prompt에 들어가지 않는다. 이 수치는 실현 PnL이나 미래 승률 보장이 아니다.

## 발견·수정 및 재검토

- 같은 확인 틱의 legacy first turn과 신규 origin low가 다를 때 primary FIRST에 원 anchor fact를 사용하던 결함을 독립 coincident first fact/input으로 수정했다.
- bar 파일을 캐시 fingerprint에 포함하고 읽은 bytes와 SHA를 동일하게 결속했다. 생성 cache는 frozen source/event/bar/code/label에 귀속한다.
- future candidate와 active current를 구분하여 준비만으로 당일 소비되지 않도록 했고 native 다음 영업일 activation과 장후 producer/direct consumer를 연결했다.
- 실제 새 코드 PID 확인 후 장중 activation을 허용한다. 과거 checklist bytes가 현행 작업으로 바뀐 경우 원 Git blob SHA를 검증한 historical checklist snapshot을 보존한다. 당시 strict PASS를 오늘 whole-chain 완료로 바꾸지 않으며 모든 나머지 generation hash 검증을 유지한다.
- signal ID별 durable provider request/parent intent CAS와 기존 sequential broker leg owner를 결속했다. generation 변경·retry·충돌·크래시 중복 요청을 거부한다.
- 미사용 파일 typed class/date/manifest/reader/FD/identity/hash/nonraw 보존을 검증한다. snapshot 날짜 충돌과 유효 요청일 겹침은 삭제하지 않는다.

## 검증과 후속 수용

최종 관련 회귀, immutable release 검증, compile/bash 문법/diff/parser 및 native source/bootstrap 검사 결과는 아래 실제 완료 절에 기록한다. 실제 bar/원천 접두 재생과 160회 수정 문구 호출을 완료했으며 provider를 mock한 연결 시험은 장후 native producer→candidate→direct consumer 정합성 검사로만 사용했다.

현행 10/4~6 bounded shadow diff는 원 비교의 모든 metric과 일치했다. 혼합 archive nonraw 1,949개는 원 bytes로 보존했고 raw 256개는 보존 대상으로 복제하지 않았다. 실제 삭제는 fresh selected reader/보호/FD 증빙으로 진행한다.

자연 장후 완료, 신규 조건 발생, 제출·체결·실현 비용 손익은 code review/선택/activation/PID 소비와 구분한다. EOD 재생성과 주문 강제 실행은 이번 장중 시험에 포함하지 않는다. 기존 episode 186개 pin과 5개 상시감시, 초기 수량 347개 과거 행·manual/custody/order guards를 유지한다.


## 배포 전 gate 완료

최종 관련 회귀 1,044 PASS(기존 pandas_ta Copy-on-Write warning 1개), 위치 검사 3 PASS. 변경 Python 30개 compile, 관련 wrapper bash -n, git diff --check, print-only parser PASS. 현행 실행 owner는 기존 Main stable ID와 AdditionalUnusedRawFileDeletion1007가 각각 하나다. native source6 전체 stored generation 검사는 원 커밋 checklist snapshot으로 policy/controller/summary/stage/terminal hash를 재검증하여 PASS했다. 이는 신규 오늘 장후 generation 검증이 아니다.

[최종 회귀](../../tmp/multi-policy-final-regression-20261007.log), [위치 검사](../../tmp/multi-policy-location-tests-20261007.log), [과거 장후 source 사전검사](../../tmp/intraday-preserved-source-preflight-20261007.json), [실제 bounded reader 비교](../../tmp/additional-unused-raw-shadow-diff-20261007.json), [미사용 body open 차단 소비 검증](../../tmp/additional-unused-raw-execution-20261007/current-consumer-proof.json).


## 실제 배포·오늘 활성화·PID 소비

- 불변 릴리스 `main-parallel-reversal-20261007-v1`, 실행 commit `039af7c1c55132c4a367989322be54140a69fdef`. 같은 불변 릴리스 관련 **1,047 PASS**, src/deploy/restart source clean 및 실제 native 12셀 loader/186개 독립 episode pin 검증 PASS다. [불변 회귀](../../tmp/main-multi-policy-deployment-20261007/immutable-tests.log), [release set·기존 bootstrap·candidate 사전검사](../../tmp/main-multi-policy-deployment-20261007/immutable-native-preflight.json).
- 기존 PID 823272를 graceful 종료하고 **12:33:52 새 PID 854451**의 runtime env bootstrap PASS와 native code handoff 소비를 확인했다. **12:34:04.693** native parent CAS로 오늘 v2를 활성화했다. original dated 10/7 v1 파일과 PREOPEN·bootstrap bytes는 유지한다. [재기동](../../tmp/main-multi-policy-deployment-20261007/restart.log), [활성화](../../tmp/main-multi-policy-deployment-20261007/intraday-activation.json).
- 활성 bundle `5f441047e2bd85cb2900c47cb68dbcf2e268974840e898d295c45fd7b96813c5`, family `5ab251bfc5194d8065547f71eb505076a442867a63e6ff27323f78ef7894d700`. 실제 Main PID가 **12:34:48.915955**에 같은 bundle/branch/phase를 소비한 sealed receipt를 작성했다. [실제 정책 소비](../../data/runtime/mechanistic_entry_policy/consumed/2026-10-07/854451.json), [bootstrap·인계·준비 확인](../../tmp/main-multi-policy-deployment-20261007/deployment-verify.json).
- 12:41:57 자연 관측에서 005930·034020·403870·196170·036930 5종목 모두 새 PID WS 수신과 machine capture가 있다. bounded tail의 source 진단을 함께 보존하며 현재 PID/새 policy 계약 관측은 누적 18건에서 일치, receipt issues={}다. 과거 PID 관측과 원천 신선도/필수 feature guard를 그대로 구분했다. [자연 수신·관측](../../tmp/main-multi-policy-deployment-20261007/natural-monitor.json), [판정 증빙 대조](../../tmp/main-multi-policy-deployment-20261007/machine-semantics.json).
- 현 관측 범위에는 신규 CONFIRMED ENTER/운영 AI 응답/제출·체결이 없다. 자연 장후 전체 완료·다음 영업일 PREOPEN/PID는 해당 예약 시각의 별도 수용이다. 다음 candidate 준비만으로 오늘 정책이 바뀌지 않는 fixture 및 native 직접 소비 연결 검증은 PASS지만 미래 성공을 대신하지 않는다.

## 실제 파일 삭제·공간·보존

95개 파일을 12:38:26~12:39:52에 삭제했다. exclusion backup 16개, 범위 밖 Parquet 39개, threshold snapshot 5개, sentinel raw 사본 34개, nonraw를 분리 보존한 혼합 archive 1개다. deleted_paths_remaining=0, skipped=[], post_delete_errors=[], FD 미관측=[], 보호 5,415개 및 별도 새 활성 policy hashes 모두 일치한다. DB mutation과 새 raw backup은 없다.

삭제 할당량 24,528,977,920 bytes(**22.844391GiB**). nonraw 1,949개·256개 raw member 분류는 원 bytes/hash로 확인했다. 최종 nonraw 보존 할당량은 525,750,272 bytes이며 계획/보존 시점의 지연 할당 측정 525,729,792 bytes와 구분한다. 최종 보존 비용 반영 순 할당 회수량은 **22.354748GiB**다.

실제 df 삭제 직전 available 31,555,252,224→삭제 후 56,050,724,864 bytes, 순 증가 **22.813187GiB**, usage **80%→64%**. 이 df 구간은 보존 작업 이후 시작하므로 전체 보존 비용 반영 순 할당량과 같다고 주장하지 않는다. 현재 로그/자연 writer 영향도 실제 df에 포함한다.

[typed manifest](../../data/report/additional_unused_raw_retirement/2026-10-07/manifest.json), [dry-run journal](../../data/report/additional_unused_raw_retirement/2026-10-07/dry-run.jsonl), [실제 delete intent·완료 journal](../../data/report/additional_unused_raw_retirement/2026-10-07/apply.jsonl), [보존/공간 결과](../../data/report/additional_unused_raw_retirement/2026-10-07/execution-result.json), [퇴역 날짜 ledger](../../data/report/additional_unused_raw_retirement/2026-10-07/retired-snapshots.json).

삭제 후 완료 manifest 선택과 현재 canonical/threshold/flow 경로는 동일하며 candidate body open=0이다. 10/4~6 실제 in-memory bounded shadow diff의 **10개 지표 모두 원 비교와 동일**하다. [삭제 후 소비 재검증](../../tmp/additional-unused-raw-execution-20261007/post-delete-consumer-proof.json), [삭제 후 비교](../../tmp/additional-unused-raw-execution-20261007/post-delete-shadow-diff.json). 초기 수량 347개 과거 행을 포함한 보호 정책/보고서/모델/잠금은 유지했다.

## 남은 관측·기존 경고

오늘 코드·native 활성화·실제 PID 소비 PASS와 전 시스템 경고 0을 구분한다. 12:40 기존 전체 감시기는 source 10/6의 `postclose_handoff_generation_invalid`/`strict_checklist_generation_stale` 및 episode `episode_current_pid_source_not_observed`를 보고했다. 당일 checklist 변경을 원 장후 strict의 공유 문서 경로가 검사하는 상태이며, 과거 증빙을 최신 whole-chain PASS로 바꾸거나 경고를 삭제하지 않았다. 오늘 native 인계의 original Git checklist snapshot과 모든 나머지 source generation 검사는 별도로 PASS다.

잔여 의미감시 owner는 현재 체크리스트 `SemanticMonitorProducerConsumerRefresh1007`, episode owner는 `EpisodeCaptureSequence1006`이다. source 10/6 controller/strict/finalization을 historical 소비 계약과 대조하는 개선 및 해당 episode 실제 PID source 관측은 별도 closure test다. 새로운 오늘 거래 실패나 broker False로 집계하지 않는다. Main owner의 자연 신규 신호/다음 장후 수용과 AdditionalUnusedRawFileDeletion1007의 다음 정규 작업 자연 완료도 OPEN으로 유지한다. 현재 체크리스트 frozen bytes는 배포 후 변경하지 않았다.

실행 코드 commit은 위 039af7c1이며 이 완료 문서는 별도 문서 commit으로 보관한다. 다른 사용자의 main-only-widget-episode 계획 및 생성 nonraw 보존 파일은 stage/overwrite하지 않았다.
