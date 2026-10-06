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

## 첫 배포·운영 영수증 — 가격 manifest 보완 전

- 구현 커밋 `95b6a016` + WATCHING provenance 추가 수리 `b9831035e8c705088813a14e6330b44a9b8390c8`. 최종 immutable release=`/home/ubuntu/KORStockScan-runtime-releases/main-submit-drought-20261006-b9831035`. 기동 전 준비한 첫 release는 소비 전에 철회했다.
- 재기동 직전 두 native KRX/NXT 잔고·미체결 snapshot 일치, Main 5종목 잔고/미체결/전체 날짜 미해결 intent/custody 잔량 0. 기존 native graceful restart에서 이전 PID `169115` 종료→새 PID **290462**; 19:52:28 당일 bootstrap/환경/해시 PASS. launcher PID/cwd receipt가 최종 release를 소비한다. 19:52:56 이후 WS 0D 및 0B 첫 수신도 확인했다.
- 최종 release-set check PASS, Main PID binding=`matches_selected_release`; 남은 episode 31개 profile/62개 route의 기존 `511664f3` pin과 186개 원 정책 pin PASS. 현재 inactive인 episode를 기동하거나 퇴역 Widget/episode를 복원하지 않았다.
- 원 정책·PREOPEN 34개 SHA 불변. 기계 정책값·기본 AI 정책/prompt hash·수량·청산·broker/provider/custody guard 변경 없음. 공통 WATCHING 평가 허용과 recipe 근거 소비는 이번에 수정한 실행 동작이다.
- 새 PID/checklist를 읽은 native summary→tower/checklist→strict/controller→cleanup→final detector **19:56:48 DONE**. chain=`159ba4fcdf2db547b062f83851c89a6319b61c4aebb185d4ae6b4cc964396131`, 원 snapshot=`de8c7a024a0ad4b385fda97148f5e1043fdc6e3161eb981ecbd12f7b081bf112` 유지. strict binding=`beae58085a4971b24f75f74bead8045452ca65e55d0d3cf5be08a3e7c9596b8a`, summary=`00b7bc3ad80ad6138c6acbcbffe7f63bdb4a073cbea9a018c2e14488081e754e`. 과거 10/2 복구이며 새 미래 PREOPEN/전장후 생산자를 재실행하지 않았다.
- 19:57:52 당일 읽기 전용 full detector **FAIL 0**, process PASS, operational mutation 0. cron cleanup/finalization은 원 06:50 상한 이후 완료를 뜻하는 `recovered_late` 경고로 유지한다. 원 Main/compact 운영 경제성·stop/plan 결손과 episode 원천 경고는 그대로이며 이번 가격 CF로 해소 처리하지 않는다. 19:58:33 독립 검사에서 marker/controller issues 0, 현재 checklist SHA 일치, PID/cwd와 원 정책 34개 불변을 재확인했다.
- 최종 증거: `runtime-verification.json`, `release-set-after.json`, `terminal-verification.json`, `current-date-health.json`, `exact-contract-replay.json`, 회귀 로그. 다음 적격 KRX 정규장 recipe 자연 수용은 **not_observed**이며 기존 stable owner에 남았다. 이번 코드 검토 범위의 미해결 finding은 0이다.


## 최종 소비 대조 추가 수리: 가격 manifest 세 개

20:00 최종 dirty 대조에서 별도 문서 작업이 추가한 진단을 확인했다. reader는 기본 manifest 39종목만 읽고 같은 디렉터리의 이미 수집된 22·393종목을 누락했다. 위 6/26·7/39는 당시 가격 부분집합 계산이며 454종목 전부의 소비 결과가 아니다. 세 원 manifest의 검증 합집합, bytes 미기재 자료의 SHA 검증 후 실제 byte receipt, 중복 hash 제거 및 충돌 종목 격리를 수리했다. 원 manifest/가격은 수정하지 않았으며 추가 테스트와 calibration 회귀 **245건 PASS**. 당일/비교일을 새 kernel로 재계산하고 이전 PASS를 재사용하지 않는다. 외부 차트 가격의 조정/호가단위 의미는 미입증이므로 가격 CF에만 쓰고 실제 체결 가능 가격·손익으로 표현하지 않는다. 별도 추가 문서의 C2/D2/E2 연구 제안은 이번 고정 후보에 섞지 않는다.


## 가격 소비 수리 이후 최종 상태

- `fbfc9dd6432e337b61ab63744216f32b80875bc6`를 immutable `main-submit-drought-20261006-fbfc9dd6`에 배포하고 native graceful restart로 **Main PID 338586 / 20:03:45 bootstrap PASS**를 확인했다. 두 fresh broker/custody snapshot은 5종목 flat으로 일치했다. 원 정책 값은 유지하며 가격 helper만 추가 보완했다.
- 새 kernel로 10/6와 10/2를 재계산하고 두 native projection의 원천·내용·kernel SHA를 검증했다. 10/6 외부 **454종목** receipt를 소비했다. 비삼성 현재 규칙 **7/36승 19.44%(미확정 3)**, D **16/102승 15.69%(미확정 7)**. 삼성 C는 0/2, A는 1/6, B는 미확정 1, E는 직접 후보와 동일이다. A/B/C/D/E 추가 완화 미선정. 10/2 결과와 가격 basis를 섞지 않는다. 앞의 6/26·7/39는 가격 부분집합의 이전 결과로 보존한다.
- 회귀 실행 **1,877건 PASS(중복 포함)**, 가격 충돌 종목 격리·다중 manifest 검증·byte receipt 테스트, compile/Ruff/diff/parser PASS. 최종 generation 및 당일 full health는 마지막 native 재봉인 영수증에 기록한다.

- 최종 native 재봉인 **20:07:09 DONE**, chain=`984c687309ace40be891c0520295fdda3654b4f6132ef9b695198bf4fb7bf2b7`, snapshot=`de8c7a024a0ad4b385fda97148f5e1043fdc6e3161eb981ecbd12f7b081bf112` 불변. 현재 checklist strict binding=`797d61f63277d82b3eb27377e8d092ccd5efd94970268d84c6070432be347bd0`, summary=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`. 20:07:52 당일 non-mutating full health **FAIL 0 / process PASS / cron PASS / operational mutation 0**, log scanner의 warning은 변경 없는 과거 로그 감사 기록이며 현재 error burst는 없다.
- **20:08:31 독립 terminal 검증 PASS**: marker/controller issues 0, 최신 checklist SHA와 source-date generation 일치, Main PID 338586/cwd 및 원 정책·PREOPEN 34개 hash 확인. 최종 코드 review 범위의 미해결 finding 0. 기존 Main/compact/episode 원천·운영 경제성 결손과 다음 적격 정규장 자연 recipe 수용은 별도 OPEN/`not_observed`로 유지한다. 다른 작업이 추가한 계획 §11과 그 연구/삭제 dirty는 본 커밋에서 보존·제외한다.
