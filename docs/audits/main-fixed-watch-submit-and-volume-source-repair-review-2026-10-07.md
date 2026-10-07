# Main 고정감시 제출 증빙·거래량 원천 수리 검토

사용자 승인 범위: HPSP 제출 False와 주성 거래량 결손 점검·수리, 반복 코드리뷰·검증 완료 후 배포 및 재기동. 기존 기계·보조 12셀, TTL 3초, CAUTION 미시 확인 2개, 소스 지연 5초 및 주문·수량·자본·custody guard는 유지한다.

## 공식 원천 확인

WS 로컬 시계 수리 전에 `2026-10-07T10:36:37+09:00`에 공식 저장소 HEAD를 조회했다. `953e5dbff123f437ab4d11a78a95191a685eb51f`이며 로컬 검토 사본과 일치한다.

- 검사: `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 0B/0D, `kiwoom/core/ws_client.py`, `kiwoom/realtime/decoders.py`, `stream.py`, `packets.py`, PRD/MOCK Postman collection.
- 이 revision에는 `kiwoom_docs`가 없다. 패키지 명세에서 FID20은 HHmmss, FID15는 부호 있는 체결량, FID27/28은 원 단위 호가다. wire 필드/부호/단위/등록·재접속·auth·주문 명세를 변경하지 않는다.
- WS URL과 실전/모의 구분, 기존 parser 의미를 유지한다. 원천의 초 정밀도를 유지하고 로컬 파싱 완료를 새 수신 시각으로 사용하지 않는다. 공식 근거는 [Kiwoom 공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)다.

## 구현·검토 진행

기존 6회 False는 broker 주문 실패가 아니다. 2회 고정감시 제출 증빙 결손, 2회 AI TTL 초과, 2회 CAUTION 미시 확인 미달이다. 원 사건과 16개 주성 RECHECK 원천은 [원 분석](main-fixed-watch-submit-lineage-and-samsung-shallow-pullback-research-2026-10-07.md)에 보존한다.

수리 결과:

1. 제출 binder는 고정감시의 `watch_origin/admission/generation`과 종목·시장·세션·정확 캡처를 검증한다. 스캐너 경로는 기존 promotion을 유지한다. 고정감시를 스캐너 ID로 위장하지 않는다. sizing plan에도 원 감시 부모와 캡처 해시를 보존한다.
2. 캡처 해시가 제출 allowlist에서 빠지던 인접 결함도 보완했다. 실제 PID·bundle·종목·route·세대·평가의 현재 revision을 시작과 sizing 직전에 검증한다. 재평가가 시작되면 이전 PASS를 폐기하고 새 평가 ID로 기계→실제 AI 경로를 호출한다. timeout/불완전 재평가가 이전 PASS를 빌리지 못한다.
3. 연속 반전의 활성 probe 계약 TTL 3초를 앞 AI authority 검사에 연결했다. 자금 조회 중 다시 만료되면 실제 현재 나이로 제출을 보류하고 다음 기존 호출 경로에서 새 평가를 받는다. TTL 또는 기존 provider 재시도 간격을 늘리거나 완화하지 않는다.
4. 0B의 실제 패킷 수신 시각을 정규화·kernel·원천 observer에 동일하게 보존한다. 원천→패킷·패킷→정규화 지연은 같은 item/transport/sequence에 귀속한다. 최근 60초÷직전 60초는 120초의 유효 연속 구간이 필요하며, 결손 이유·관측 초를 별도로 기록한다. 지연·재기동 구간을 이어 붙이지 않는다.

원 사건 재현: HPSP `aims-db4c7c4b25e038b01f63`, `aims-ce70b95a90e22411d320`의 2개 원 receipt는 새 고정감시 binder PASS. 주성 16개 원 RECHECK는 그대로 재현되며 source reset 12개·transport epoch reset 4개다. 당시 유효하지 않았던 표본을 새 ENTER나 실제 주문으로 합성하지 않았다. [재현 JSON](../../tmp/fixed-watch-submit-source-repair-20261007/incident-replay.json).

검토·검증: 첫 불변 릴리스의 관련 1,577개 테스트는 PASS했으나, 실제 정책 로더에서 `reversal_kernel_code_changed`를 발견했다. 해당 v1은 선택·재기동하지 않았다. 연구 원본 커널과 보조 계약을 그대로 복구하고, 새 진단은 `src/engine/scalping/reversal_source_diagnostics.py`의 읽기 전용 원천 투영으로 옮겼다. `src/engine` 루트에 새 모듈을 만들지 않는다. 기계 feature·선택 규칙·보조 입력을 바꾸지 않으며, 동일 event/item/transport/sequence의 지연만 첨부한다. 진단 실패는 관측 불가로 남긴다.

보완 버전의 반전·보조 계약·AI transport·고정감시 관련 273개 테스트는 PASS했다. 실제 native 정책 로더에서 기존 bundle 및 기계·보조 12셀을 검증했고 kernel SHA `17b73fbd524814faa53895148364758716aac406ca41761768cb69d430178030`을 보존했다. 기존 capacity mock의 `purpose` 인자 누락 2개도 보완했으며 기대 보호조건은 바꾸지 않았다. 배포 전 최종 불변 릴리스 전체 관련 회귀·compile·wrapper 문법·diff·print-only 문서 parser 결과는 완료 증거에 기록한다. 수정 중 실행의 digest 불일치와 기각한 v1 로그도 보존한다.

배포 직전 원 PID `777785`/start ticks `95520219`/v4 bootstrap PASS, findings=[]다. 로컬 DB read-only 조회에서 고정감시 005930·034020·403870·196170·036930과 보유·주문 요청 0건을 확인했다. 이는 증권사 계좌의 독립 실시간 잔고 증명이 아니다. 기존 current OPEN `MainSubmitDroughtPathAcceptance1006`의 원천·제출 수리 범위에서 진행하며 이미 봉인된 checklist/PREOPEN·EOD·정책·기존 186개 episode pin은 변경하지 않는다.

최종 불변 릴리스에서 관련 1,773개 테스트 PASS, compile 12개·wrapper 문법·diff·print-only parser PASS이며 검토 범위의 잔여 코드 결함은 0이다. 배포·새 PID 소비·자연 거래량 회복은 아래 완료 증거로 구분하며, 실제 ENTER/PASS/주문 부재는 미관측으로 남긴다. 이 문서는 전략 완화나 강제 주문 권한을 만들지 않는다.

## 배포·실제 소비 완료 증거

- 승인된 Main 릴리스: `fixed-watch-submit-source-20261007-v2`, commit `7aa0f1e2a1ea367f3b5b1d492aedcfcb5c131db5`. 사용자 작업 branch/index와 무관한 명시 범위의 detached export이며 관련 없는 삭제/수정은 포함하지 않았다. v1은 native 로더 검사에서 기각돼 선택하지 않았다.
- 정상 재기동 후 Main PID `815021`; `2026-10-07T11:04:20+09:00` bootstrap PASS, findings=[]다. 실제 cwd는 새 릴리스 `/src`, 당일 native intraday handoff와 consumed receipt PASS, release-set PID binding 일치다. [배포 검증](../../tmp/fixed-watch-submit-source-repair-20261007/deployment-verify-v2.json).
- bundle `bf15fc240560605b7fe08796941288d9ef28a5f7c8d2cbf47692787b894f4a98`, family `e8fe8172831970c399e799efc65ac4df991f0526467239f8b944577b409333ba`, 기계·보조 12셀 모두 기존과 같다. 186개 episode pin도 native release-set 검증 PASS이며 별도 service를 재기동하지 않았다.
- 보호 목록 3,101개 중 승인된 release selector/PID attestation 1개만 변경됐고 나머지 3,100개는 원 SHA 그대로다. EOD·기존 정책·sealed PREOPEN/checklist를 재생성하지 않았다. [실제 셀 대조](../../tmp/fixed-watch-submit-source-repair-20261007/policy-cells-release-v2.json).
- 11:05 새 PID의 주성 반전은 정상 재기동 후 관측 17.10초의 거래량 warmup으로 RECHECK했고, 두산 반전은 규칙 미달로 BLOCK했다. 두산 동일 0B event의 provider→packet 145.015ms, packet→normalization 0.969ms가 새 계측에 기록됐다. 정상 지연 원인과 무효 구간을 구별하며 과거 578개 지연을 증권사·네트워크·처리 중 한 주체로 소급 단정하지 않는다.

자연 관측의 최종 결과는 [모니터링 JSON](../../tmp/fixed-watch-submit-source-repair-20261007/natural-monitor-v2.json)에 보존한다. HPSP 실제 새 ENTER/PASS/제출 발생을 강제하지 않으며, 미발생은 `not_observed`로 남긴다. 개별 보호조건 미달이나 다음 실제 지연이 발생할 수 있음은 코드 결함 0 또는 단위 검증 PASS와 별개다.

11:08:29까지의 새 normalized 원천 16MiB 말단을 독립 native 커널로 재현했다. 주성의 마지막 지연은 11:05:24이며 이후 유효 연속 구간은 184.71초다. 이는 읽기 전용 원천 replay이고 실제 PID의 새 반전 판정/ratio 소비 증명은 아니다. 새 source clock으로도 초기 원천→수신 최대 9.238초의 주성 지연 4개가 관측돼 기존 5초 guard에서 제외됐다. 지연이 사라졌다고 단정하지 않는다. [최근 원천 대조](../../tmp/fixed-watch-submit-source-repair-20261007/recent-normalized-source-v2.json).

## 자연 검증 완료

`2026-10-07T11:11:49+09:00` 기준 새 PID의 고정감시 5종목 capture·WS 실수신·선택 bundle 일치를 확인했다. 주성의 실제 반전 event `2026-10-07:SOR:SOR_REGULAR:036930:1:1039`는 11:11:39.846 판정에서 최근 60초÷직전 60초 `1.4666081807`, 연속 관측 `374.954초`, source status `ready`를 기록했다. 최종 action은 `BLOCK/selected_reversal_condition_not_met`이며 거래량 결손 RECHECK가 아니다. 삼성도 11:10:22.373의 실제 판정에서 비율 `1.3936271953`·`ready`를 기록했다. [자연 관측](../../tmp/fixed-watch-submit-source-repair-20261007/natural-monitor-v2.json).

HPSP의 당시 receipt 2개가 새 binder로 sizing에 연결되는 것은 원 사건 replay와 회귀로 검증했지만, 배포 이후 새 ENTER/PASS/제출은 자연 발생하지 않아 `not_observed`다. broker 제출/체결 성공으로 보고하지 않는다. TTL·CAUTION 기준 미달은 그대로 차단한다.

검토·배포·현재 PID 소비·주성 실제 거래량 비율 소비는 PASS이며 이 수리 범위의 잔여 코드 결함은 0이다. 전체 감시기에는 별도 `episode_current_pid_source_not_observed` 경고와 장후 `recovered_late` 경고가 남아 있어 전 시스템 경고 0 또는 장후 전체 정상으로 확대하지 않는다. 기존 episode owner의 당일 source receipt 검증과 장후 지연 이력은 이 Main 제출/거래량 수리와 별도다. 강제 주문·수동 provider 호출·장후/EOD 재생성은 수행하지 않았다. [종결 증거](../../tmp/fixed-watch-submit-source-repair-20261007/closure-v2.json).
