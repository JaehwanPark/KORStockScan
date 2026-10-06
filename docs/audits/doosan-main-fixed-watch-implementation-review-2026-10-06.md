# 두산 에피소드 제거·Main 고정감시 구현 검토

작성일: 2026-10-06 KST. Owner: [전환 계획](../proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), 현재 checklist의 `DoosanEpisodeToMainFixedWatch`.

## 결정과 권한

사용자가 구현·반복 리뷰를 지시했고, **초기 정책 적격성 입증은 필요 없다**고 후속 기준을 정했다. 두산 `034020` 초기 정책은 현재 Main 비삼성 정책 지정이다. 경제성/native support/새 독립 날짜 검증 부족 때문에 최초 지정을 관측 전용으로 보류하지 않는다. 실제 exact-date/hash, source freshness, broker/account/order/quantity/cooldown, custody와 수동 veto는 유지한다.

이번 결과는 작업본 구현·오프라인 연구·리뷰 검증이다. 설치된 unit 삭제, release 선택 변경, owner policy 실발행, 정책 재생성의 운영 반영, Main 재기동·실주문은 실행하지 않았다. 이전 다른 수리의 배포 승인·PID 영수증을 이번 소유권 전환에 재사용하지 않았다. 이 초기 지정은 새 수익성 입증이 아니다.

## 구현

- 두산 3개 episode profile와 관련 window/override/pin/dispatch/연구 목록, 설치·제거 목록과 전용 timer 6개를 작업본에서 제거했다. 공용 template과 다른 종목 profile은 유지했다. 원본 census 61개에서 두산을 뺀 58개 profile의 직렬화 값은 변경하지 않았다.
- `owner_retirement.py`의 symbol/owner 제외를 static/dynamic profile, auto expansion, prospective/joint research, collection/owner 정책과 전송 직전 BUY에 적용한다. renamed ID와 suffix로 두산 episode 신규 주문을 복원할 수 없다. 기존 cancel/SELL·과거 custody·주문·가격 원장은 삭제하거나 Main으로 재귀속하지 않는다.
- Main fixed watch는 삼성·두산의 session/admission/generation/target 상태를 분리하고 기존 정원에서 두 slot을 예약한다. 두산 launcher flag는 staged ON이며 현재 PID 적용 영수증은 없다. 두산의 기존 Main 비삼성 정책·공통 진입/보유/청산/수량/주문 경로를 사용한다.
- 관측 전용 exact item을 Main이 승계할 때 현재 transport epoch와 0B/0D 등록을 확인하고 새 REAL 수신으로 quote/tape를 채운다. 과거 관측 quote를 실행 필드로 복사하지 않는다. 같은 종목의 다른 item은 REMOVE하지 않는다. 신선도·warmup·실제 venue 증빙·기존 API read 예산은 완화하지 않았다.
- 과거 episode policy bundle은 전체 원본 hash를 검증한 뒤 두산만 runtime projection에서 제외한다. 다른 종목 policy가 옛 두산 행 때문에 읽기 실패하지 않는다. 공용 native fact writer와 frozen joint cohort도 퇴역 revision을 실행·연구 모집단에서 제외하면서 원 증거는 보존한다.
- 두산의 Main·수동 owner 세트를 기존 native owner validator/apply/registry가 수용하도록 좁게 확장했다. 다른 종목 owner 세트는 확대하지 않는다. 최초 전환은 broker/custody flat와 모든 날짜의 미확정 intent 확인이 필요하다. 후속 일자 갱신은 이미 결속된 Main 보유를 유지하며 옛 episode 미종결 노출은 허용하지 않는다. 기존 수동 veto가 계속 우선한다.
- 유한 연구 생산자는 `src/engine/monitoring/main_fixed_watch_policy_research.py`이고 기존 Main 장후 stage에 연결했다. `source_target_date`가 원천 날짜를 소유하며 `target_date`는 다음 적용일이다. recovery는 해당 bounded diagnostic만 재생성할 수 있다. 독립 두산 cron/stage/order loop는 추가하지 않았다.

## 실제 오프라인 연구

[연구 보고서](../../tmp/doosan-main-execution-20261006/research/main_fixed_watch_policy_research_2026-10-06.json)와 봉인 계약은 원천 날짜 2026-10-06, 적용 목표 2026-10-07, 연구 하한 2026-09-29를 사용한다. 현재 부모 bundle은 `bd76748c22aaf913af104996be3073664ef355f24c3e6291c47f28e107aedabe`다. 소비 원천 6파일은 총 1,719,141,657 bytes이며 parent/source/kernel/candidate manifest를 hash에 결속했다.

| 항목 | 실제 결과 |
|---|---:|
| 봉인 후보 | baseline 1 + family 3 × parameter 3 = 10 |
| 두산 원천 행 | 25 |
| Main 원 native opportunity lineage 부족 | 24 |
| 연구 venue/session 외 | 1 |
| Main fixed-watch 적격 기회 | 0 |
| scanner 진단 적격 기회 | 0 |

연구 결과는 `source_gap`이다. 0기회는 상승 패턴 부재·zero EV·실제 거래 손실·초기 정책 부적격의 증거가 아니다. 과거 episode 거래를 새 Main admission으로 합성하지 않았다. 초기 지정은 `current_main_non_samsung`, `initial_policy_preproof_required=false`, `entry_runtime_eligible=true`다. 연구 보고서 자체는 runtime/apply/order 권한이 없고 실제 순이익은 null이다. 미래 개선 후보는 원 admission별 중복 제거, source/cost/path 확인과 시간순 train→holdout 비교를 사용한다. holdout 성과로 다른 train 후보를 다시 고르지 않는다.

## 검토·수정 반복

1. 옛 두산 행이 공유 policy 전체를 무효화하던 경로를 원 hash 검증 후 projection 제외로 수정했다.
2. Main 승계 이후에도 관측 quote만 남던 경로를 정확한 현재 item의 소비 owner 전환과 신규 REAL 수신으로 수정했다.
3. native Main/수동 owner 발행과 loader의 세트 불일치를 수정했고, explicit manual veto 회귀를 보완했다.
4. 퇴역 연구 revision이 다른 episode 원천 기록을 중단하던 경로를 제거했다. frozen joint manifest의 옛 member는 audit 검증 후 퇴역 사유로 제외한다.
5. 최초 flat 조건이 이후 Main holding의 다음 날짜 갱신을 막지 않도록 최초 전환과 후속 native owner 갱신을 분리했다.
6. 다음 적용일을 원천 날짜로 읽어 정상 보고서를 거부하던 장후 consumer 경로를 `source_target_date`로 보완했다.
7. WS 검증 fixture가 실제 shared snapshot/fact writer를 시작하지 않도록 출력·수집을 격리했다.

검증 로그는 [작업 증빙 디렉터리](../../tmp/doosan-main-execution-20261006/)에 보존한다. 기존 영향 범위 1,002건 PASS 뒤 전환 전용 검증을 추가했고, 최종 리뷰에서 발견한 위 결함은 후속 targeted regression 345건 PASS로 재검증했다. 최종 통합 회귀는 1,129건 PASS(64.22초)이며 신규/기존 계약을 함께 재검증했다. Python compile, 변경 shell의 `bash -n`, `git diff --check`도 확인했다. Pytest의 pandas 기존 deprecation warning은 별도 환경 경고이며 패키지는 변경하지 않았다.

## Kiwoom 공식 참조

공식 `Kiwoom-Securities/Kiwoom-REST-API` revision `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieval `2026-10-06T13:00:18.162068+09:00`. `kiwoom/specs.py`, `kiwoom/core/client.py`, realtime `packets/schemas/stream/decoders/events.py`, packaged API spec와 Postman을 확인했다. 현 revision에는 `kiwoom_docs`가 없음을 [참조 manifest](../../tmp/doosan-main-execution-20261006/official-reference.json)에 남겼다. wire/FID/REST parser/authentication/continuation semantics는 변경하지 않았고 새 REG/REMOVE 패킷 형식도 만들지 않았다. 기존의 read-only account collector와 guarded order envelope를 사용하며 실제 broker 호출은 이 작업에서 하지 않았다.

## 준비와 남은 운영 증거

[retirement 준비 manifest](../../tmp/doosan-main-execution-20261006/retirement-prepared.json)는 3 profile의 live/preflight service instance 6개와 timer 6개를 닫힌 목록으로 지정한다. 현재 설치된 전용 timer 원본 6파일의 hash를 기록했다. 공용 template과 이미 퇴역한 widget collector mask는 제거 대상이 아니다. 기본 prepare는 broker·systemd·policy 변경을 하지 않는다.

| Gate | 이번 결과와 다음 폐쇄 검사 |
|---|---|
| G0 | `not_observed`: 실제 전환 직전 fresh all-venue broker·custody·all-date intent 확인 필요. 과거 planning flat receipt 재사용 금지 |
| G1 | workspace 삭제/dispatch 회귀 PASS. 설치 파일은 보존 상태이며 authorized reviewed-manifest apply 필요 |
| G2 | 새 코드/동적 재등록/전송 직전 BUY 차단 PASS. 외부 retirement receipt와 구 release 차단의 실제 적용은 pending |
| G3 | 두 종목 독립 target/정원/session/rearm 회귀 PASS. 현 PID 자연 동시 감시는 `not_observed` |
| G4 | exact 등록 승계→신규 REAL→Main quote 회귀 PASS. 자연 venue/freshness/장 시작 부하 증거는 `not_observed` |
| G5 | 초기 부모 지정과 유한 연구 폐쇄. 연구 native 기회 `source_gap`; 초기 지정 보류 사유 아님 |
| G6 | 미실행: 검토된 immutable release → installed retirement → 기존 owner policy/PREOPEN·strict/controller → Main 기동 → 자연 소비 확인 필요 |

다음 전환은 [운영 절차](../runtime-release-routing.md#main-fixed-watch-owner-retirement-transition)를 따른다. 두산 episode 또는 식별되지 않는 주문 process·두산 잔여 exit service가 살아 있으면 삭제를 하지 않는다. 기존 Main과 확인된 다른 종목 episode는 정지하지 않는다. 두 번의 matching native broker snapshot과 flat 원장을 확인한 뒤 전용 파일만 삭제하고, 삭제 전에 `entry_retired` 영수증을 기록해 reload 실패 때도 구 release가 BUY owner를 복원하지 못하게 한다. 외부 영수증은 아직 발행하지 않았다.


## 최종 완료 기록

- [최종 통합 pytest 로그](../../tmp/doosan-main-execution-20261006/final-all-tests.log): **1,129 passed**, 기존 pandas deprecation warning 1개. 검토한 변경 범위에 미해결 코드 결함은 없다.
- [연구 재계산](../../tmp/doosan-main-execution-20261006/research-final.log), [실측 성능](../../tmp/doosan-main-execution-20261006/research-performance.txt): elapsed 23.02초, max RSS 180,044 KiB. 최종 source/candidate/parent hash와 보고서 readback 검증 PASS. native 지원 0과 초기 preproof 불필요는 별개로 유지했다.
- Python compile, 수정 wrapper/launcher `bash -n`, `git diff --check` PASS.
- [print-only parser](../../tmp/doosan-main-execution-20261006/checklist-parser.log): 현재 `DoosanEpisodeToMainFixedWatch` owner 정확히 1개, Due 2026-10-07. Project/Calendar 외부 sync는 실행하지 않았다.
- 운영 전환은 pending: 실제 broker 조회·설치 제거·release 배포·재기동·현재 PID 소비는 이번 결과에 포함하지 않는다. 기존 사용자 데이터 삭제와 별도 제주 전환 proposal은 변경하지 않았다.

## 후속 배포 승인과 전환 리뷰

사용자가 반복 리뷰·보완 및 배포·재기동을 명시 승인했다. 추가 리뷰에서 전 종목 주문 프로세스 정지를 요구하던 retirement gate를 두산 episode/미식별 프로세스 차단으로 좁혔다. Main과 확인된 다른 종목 episode의 argv·실행 파일·cwd를 실제 procfs에서 확인하며, 읽기 실패·unknown/dynamic profile·중복 override는 차단한다. native flat/미확정 intent·active exit service·두 번의 정확한 broker snapshot 검사도 유지한다. CLI의 explicit account 결손은 검증된 standing authority로 결속했고, 불일치 계좌는 차단한다. 후속 회귀 122 PASS, compile/bash/diff 검사 PASS다.

당일 두산 owner 정책은 이미 Main 권한이 있다. intraday handoff는 기존 bootstrap/PREOPEN/owner 정책을 보존하고 code retirement guard로 episode BUY를 배제한다. 다음 PREOPEN의 정상 producer부터 Main·수동 owner만 발행한다. 오늘 장후의 새 source date 10/6 → 10/7 준비는 예정된 native chain이며, 아직 생성되지 않은 미래 원천·PID를 PASS로 기록하지 않는다.

Installed retirement retains six permanent service-instance masks after flat closure. Removing timers cannot restore those IDs through generic templates; other episode templates, code pins and active processes are preserved. Reload/mask readback failure retains the `entry_retired` rollback guard and reviewed retry.

## 운영 readback 후속 리뷰

14:23 실제 두산 broker/custody all-date intent 0을 다시 확인하고 terminal 퇴역 영수증을 발행했다. timer 6파일 삭제와 live/preflight instance 6개 mask를 확인했다. root가 발행한 control receipt가 launcher에게 읽히지 않는 결함을 0644 원자 발행과 회귀로 보완했다. 14:24 Main bootstrap/PID 검증과 삼성·두산 독립 fixed-watch admission, exact 0B/0D 새 수신을 확인했다. 감시기 release-set checker는 봉인된 두산 inactive mask만 제외하도록 보완했다. final-refresh installer가 낮은 우선순위 파일 때문에 이전 ExecStart를 유지하던 지점을 `~zzzz` pin으로 수정했다. 추가 targeted 검증 139 PASS, compile/bash/diff PASS다.

owner PREOPEN의 실제 승인 파일은 wrapper가 고르는 `symbol_owner_policy_standing_authority_2026-09-11.json`이다. 해당 native 파일로 다음 10/7 scope 20종목·두산 Main/수동을 검증했다. 예전 default 9/4 authority(18종목)로 직접 검사한 scope drift는 현재 예약 경로의 결함이 아니므로 현재 blocker로 사용하지 않는다. 당일 owner policy 20종목/모든 적용 완료는 보존한다.
