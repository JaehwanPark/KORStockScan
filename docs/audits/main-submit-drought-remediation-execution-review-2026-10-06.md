# Main 제출 경로 수리 실행·리뷰 — 2026-10-06

## 범위와 권한

사용자가 [계획](../proposals/main-submit-drought-priority-remediation-plan-2026-10-06.md)의 구현·반복 리뷰·배포·재기동을 승인했다. 시작 시 workspace HEAD=`36127f13`, Main selected/PID=`511664f3`/`169115`. 기존 34개 정책·PREOPEN SHA를 동결했다. 다른 작업의 삭제·조사 문서·과거 체크리스트 변경은 커밋에서 제외한다.

## 구현

- WATCHING 첫 평가·cooldown 만료·새 원천 재평가는 `is_vip_target` 가격 도달 조건 없이 기존 SCALPING 기계 경로를 호출한다. 목표 가격 산식과 실제 주문 가격, cooldown, in-flight, source, budget, owner, 수량·broker guard는 유지한다. 공통 Main 경로이며 삼성만 우회하지 않는다.
- 등록 recipe ID/version·선택 policy SHA·원 raw SHA·원 setup SHA·결정 영수증 SHA·실제 수치·두 확인 fact를 별도 ledger로 봉인한다. legacy setup 상태를 READY로 바꾸지 않는다. 실제 provider ledger의 영문 ASCII 지시·동적 enum·validator·composer·trace가 같은 ledger를 소비한다. 기본 prompt/policy 해시를 변경하면 기존 bundle 계약이 무효가 되므로 새 지시는 해당 attempt ledger에 전달한다.
- recipe ENTER_NOW와 정확한 ledger, 새 두 fact를 인정한 PASS만 legacy 확인 상태 예외를 소비한다. `PASS + CONFIRMATION_MISSING`, 실제 adverse/source 결손, 변조 정책·원천·receipt는 통과하지 않는다. 기존 `WAIT + entry_probe_intent`의 adapter/소비 경로와 최종 guard를 유지한다. raw CAUTION을 운영 PASS로 바꾸지 않는다.
- 과거 캡처 1,036개의 유일한 setup SHA 오류는 recipe의 부모 해시→선택 해시 metadata 변경이었다. 원 캡처와 raw SHA, 부모 receipt를 검증하고 그 한 필드만 부모 값으로 되돌리면 **이미 기록된 원 setup SHA**와 일치한다. 읽기 projection과 복원 receipt를 장후 로더에 추가했으며 원본·원응답·원천·결과는 수정하지 않는다. 손상된 사실을 새 hash로 봉인하는 복원은 거부한다.
- 기존 Main calibration의 하루 증분 helper와 독립 non-publishing CLI, compact replay projection, 제출 감시기의 exact revision 확인 ledger를 연결했다. 새 collector·daemon·cron·engine-root 모듈은 추가하지 않았다. 후보 연구는 정책 발행·실현 손익·실제 주문 증거가 아니다.

## 결정적 비교 결과

진입=다음 분봉 시가, 최대 20분, 비용 0.23%+슬리피지 0.10%, 순목표 +0.5%/순손절 -0.5%. 같은 봉 동시 도달·누락·미만기는 제외하며 null을 손실 0으로 채우지 않는다. 독립 기회는 동일 종목/venue/session 30분 중복 제거; discovery/WATCHING 원 관측 분모는 별도 유지한다.

| 날짜·범위 | 현재 규칙 | 후보 | 판단 |
| --- | --- | --- | --- |
| 10/6 비삼성 KRX 정규장 | 6/26승, 23.08%; 미확정 13 | D 7/39승, 17.95%; 미확정 70 | 승률 열세, 추가 완화 미선정 |
| 10/6 삼성 KRX 정규장 | 선택 0, 승률 null | C 0/2승, 두 손절 선도달 | 대체 기준 우위 없음 |
| 10/6 보조 A | 비교 가능한 실제 PASS 기준선 0 | 확인 부족 단독 6건 중 1승, 16.67% | 동일 exit 지급 크기 기준 우위 없음 |
| 10/6 보조 B | 별도 정확 응답 분모 | remote guard 1건, 프리마켓 경로 가격 미입증 | 결과 null, 미선정 |
| 10/2 비삼성 KRX 정규장 | 7/30승, 23.33% | D 9/85승, 10.59% | 열세 |
| 10/2 삼성 KRX 정규장 | 선택 0, 승률 null | C 0/4승 | 우위 없음 |

E의 30초/최대 3회 새 원천 재평가에서 직접 후보와 다른 회수 사례는 없었다. C/D와 동일 선택은 duplicate로 표시해 동률 후보를 새 승자로 만들지 않는다. 10/6은 봉인된 기존 외부 KRX 분봉, 10/2는 기존 native completed-bar 자료다. 가격 basis가 달라 두 날짜를 누적으로 합산하지 않는다. 같은 정의·정책·kernel·가격/cost/exit·원천 receipt의 일별 결과만 승리 합계/유효 결과 합계로 병합하며 보조 A/B도 별도 분모로 누적한다. 100%/80% 성공 보존·추가 표본 하한·EV 탈락 조건은 없다.

10/6 고정 prefix=290,797,093 bytes / SHA=`b6e4aa871047aade4908ec0bf77f3c4dc84551b8e984376c147ba60955e8662c`, cutoff=16:42 KST. 기계 캡처 2,690개 중 유효 2,523, 제외 167(원 raw 없는 163+cutoff 이후 4), 독립 기회 1,273. 10/2 유효 2,309/제외 607. 보고서는 `data/report/ai_decision_action_outcome_calibration/main_submit_drought_research_{2026-10-06,2026-10-02}.json`이다. 외부 가격은 실제 SOR/NXT 실행·BBO·체결 증빙으로 쓰지 않는다.

## 리뷰·수정보완·검증

수정한 결함: 임의 손상 setup의 재해시 금지; 기본 prompt 변경으로 인한 bundle 무효 방지; stale kernel cache 무효화; 전체 날짜를 중단하던 exact 보조 응답 충돌을 해당 capture만 source-gap으로 분리; source/trace 시작 byte 경계 고정; 보조 응답이 시나리오 진입 후 도착한 경우 제외; 분모·가격 basis 분리; 감시기 latest revision과 single revision 연결 및 출력 whitelist 누락 수리. broker/account/order/quantity/owner/hard safety 우회는 없다.

- 통합 표적 회귀 **904건 PASS**, 고정감시·승인·router 등 재리뷰 **219건 PASS**, 마지막 감시기·새 계약·위치 gate **182건 PASS**. 기존 Pandas FutureWarning 1건은 별도다.
- 12개 실제 ENTER_NOW 캡처와 원응답을 exact hash로 재생했다. 11개 recipe에 신규 PASS가 두 recipe fact와 원 adverse fact를 모두 인용하는 **가정 입력**에서는 11개 모두 기존 WAIT/probe intent로 전달된다. 과거 CAUTION/invalid PASS/오전 provider 미호출은 그대로이며 이 테스트를 신규 provider 응답이나 실제 진입으로 세지 않는다.
- Python compile 11개, 변경 3개 파일 Ruff, diff check PASS. probe guard 추가 회귀 **105건 PASS**; print-only parser exit 0, 신규 stable owner 1개. 총 1,410개 테스트 실행(중복 회귀 포함), compile/diff/Ruff PASS.
- 테스트·비교·원 정책 동결·배포 준비 증거: `tmp/main-submit-drought-remediation-20261006/`. Kiwoom 요청·parser·FID·recovery 구현은 변경하지 않아 official protocol gate 대상 변경은 없다. 추가 원천 수집·외부 sync·실주문·전장후 재생성은 수행하지 않는다.

## 잔여 자연 수용

배포·PID 소비·WS 수신과 실제 평가→보조→guard→주문→체결→비용 성과는 구분한다. 다음 적격 session의 recipe/provider 자연 증거가 없으면 `not_observed`다. 기존 운영 경제성·stop/plan/capital 결손은 가격 연구로 닫지 않으며 기존 Main/compact/entry-split OPEN owner가 유지한다. [당일 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)의 `MainSubmitDroughtPathAcceptance1006` 한 owner가 P0 다음 기동 수용을 소유한다. 현재 정책 값/원 PREOPEN을 유지한 승인 배포 뒤 strict/controller/native finalization을 마지막 checklist/PID 세대로 다시 봉인한다.

- 마지막 생산→상태 처리기→감시 소비 대조에서 새 확인 필드 4개가 WATCHING provenance whitelist에서 빠진 것을 추가 수리했다. 상태 처리기·async bridge·감시기·위치 회귀 **222건 PASS**. 첫 준비 릴리스는 기동 전에 철회하고 수정된 릴리스를 다시 봉인한다. 총 회귀 실행 1,632건(중복 포함).

## 최종 운영 영수증

배포 및 최종 native 검사 후 아래에 실제 receipt를 기록한다.
