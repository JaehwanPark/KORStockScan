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
