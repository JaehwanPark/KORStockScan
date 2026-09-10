# 12:52~13:30 장중 모니터링·배포 관리

상태: 13:30까지 모니터링 완료, 종료 대사13:30:21 KST. 대상일2026-09-10. 사용자가 이 세션에 장중 모니터링과 배포 관리를 맡겼다. 다른 세션의 진행 작업을 중지하거나 변경한 기록은 아니다. 운영 전체 정상 판정은 아니며 아래 미해결 입력·custody·배포 수락을 보존한다.

## 배포 기준과 경계

- 메인 PID657193, 현재 고정 코드 `680773d59c882a775d31979ad8a069b5ea06a1b8`, `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-680773d59c88`. Git main `13f8c92d`와 실행 코드 차이는 문서/병합 이력이며 코드가 동일하다.
- 이 모니터링 동안 현재 배포본을 직접 수정하지 않는다. 배포가 필요한 검증된 결함만 별도 release/code-policy hash·owner/broker 대사·review gate를 닫은 뒤 처리한다. 다른 세션의 미완료 adaptive-exit/공용 registry 변경은 메인 배포에 포함하지 않는다.
- KRX 당일 승인 SHA `95a10c8513acedad7044678cf026ce47ecf5c2f041aeec107ee8f3341da20da0`, V2.14/evidencev10/composerv11/1주/일일100,15:30 만료. 기존 사용량/정책/수량/guard를 수정하지 않는다. 단순 DROP/WAIT 또는 표본 부족은 강제 BUY·재기동 사유가 아니다.
- 프로세스·실행 코드·승인 hash와 공유 env 변경을 관찰한다. 이 문서는 조정 기록이지 다른 세션의 쓰기를 강제로 막는 mutex가 아니다. 현재 main/widget/episode는 데이터·원장을 공유하며 독립 주문 소유권을 유지한다.
- 위젯 적응형 청산은 별도 개발 작업이며 이 요청으로 신규 활성화·기존 보유 편입을 하지 않는다. 기존 exact-date timer는 정상 예정 실행을 관찰하고 조기 기동하지 않는다.
- 내일07:55 cron의 작업폴더 기동 경로는 현재 미통일 상태다. 별도 `KRXDaily100NextDayStartupAcceptance0911`의 배포 경로/정책/실제 PID acceptance와 이번13:30까지 관찰 완료를 구분한다.

## 시작 관측

- 12:53:46 collector: `healthy_observer_canary_with_source_row_exclusions`, stop 없음, queue full0/0, writer error0/0, writer3/3, trade/depth persisted117777/174216, callback p95/p99=0.097/0.119ms, available disk 약30.16GB. invalid depth timestamp4는 원천 제외로 보존하며 전체 정상 원천으로 합치지 않는다.
- 12:53:53 읽기 전용 broker: KRX/NXT 조회 성공, 삼성전자35·SK텔레콤10·232140 1주. 미체결 SELL0022607(SK텔레콤10),0015751(삼성10), 각 exact registry owner1개. [broker 원본](../../tmp/intraday-monitor-20260910-1050/broker-125354.json).
- 삼성 오전 base leg는 target0018662 10주 체결/COMPLETE, base_plus_1tick은 target0015751 10주 보유. 정확한 실현비용/체결시각은 별도 확인한다.
- 028050의 과거 registry10/broker0 deficit은 기존 미해결 이력이다. 232140은 registry 외 잔여1주이며 실제 main 주문/보유 기록을 확인하기 전 manual로 단정하지 않는다. 계좌 전체 정합성 PASS 아님.
- widget heartbeat12:53:47, latest detector12:53:34 pass. process 생존만으로 adaptive-exit 활성화 또는 경제성 개선을 주장하지 않는다.

## 도래 작업 분류

- `WidgetEpisodeApprovedNextDayExecution0910`, `RuntimeEnvIntradayObserve0910`: 지난 window 이후 자연 소비/독립 custody acceptance 계속 점검. 전체 경제성은 OPEN.
- `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910`: 수집 복구 이후 정상 영속과 식별된 source row 제외 확인.12:00:28~12:24:50 과거 수집 손실은 복원하지 않는다.
- `SimProbeIntradayCoverage0910`: OFF/퇴역/비우선 영역 권한·리소스 간섭만 확인하며 성과 재생성은 하지 않는다.
- `IntradaySourceQualityGateCheck0910`14:20 및16:30 이후 장후 작업은 종료13:30 밖/not_yet_due.07:35/07:55 다음날 수락은9/11 대상이다. 미래 producer를 조기 실행하지 않는다.
- 13:10~13:29 설치된 독립 기계 preflight/기동은 각 실제 예정 시각에 관찰한다. 특히 NHN/한국전력13:25 preflight→13:29 기동을 확인하되13:30 이후 신호창 완료를 선행 주장하지 않는다.

## 후속 관측

13:03 수리 검증: `sniper_execution_receipts._sell_receipt_recovery_directory`의 기본값을 canonical shared DATA_DIR의 기존 `src/data/runtime/sell_receipt_recovery`로 결속했다. 명시 env는 보존하고 journal child symlink/체크섬/identity/수량/기존 recovery guard를 완화하지 않았다. 위치 해석만으로 파일 생성·복사·주문·원장 변경은 없다. 현재 PID는 아직 옛 relative default이며 재기동 필요성이 있는 배포 결함이다. 원본42193의 SHA `20aed058e60df96d2754cc36a3213a36d5d31b7517271dd5d82a89ad93a6707e`, checksum PASS·final_pending_db_commit true·pending lifecycle leg1을 확인했다. 과거10:11 흥구석유1주 매도 귀속이며 새 수익이 아니다.

별도 격리 코드에서 관련152 tests PASS(기존 pandas 경고1), cwd 독립/shared mount·explicit env·child symlink 거부3개 회귀 포함. Ruff/compile/diff PASS, Black 공백 보완 후 재검증한다. 검토 범위 미해결 code finding0이며 실제 journal consumer/ACK는 아직 별도 수락이다. Kiwoom 요청/응답/FID/재연결 코드는 변경하지 않았다.

12:56까지 새 PID 자연 Entry OpenAI21회(DROP9/WAIT12), entry-price Bedrock10회, holding OpenAI4회는 parse 성공이다. 별도 Entry3/holding5회는 provider 미호출/input_preflight_blocked이며 모델 실패로 세지 않는다. 와이씨232140은 main 주문0048572가12:48:54 1주12030원 체결, main holding record42433으로 추적했다. 일일 cap5/100, 일반 수량 확대 없음. 공용 registry만의 remainder1은 수동 보유 확정 근거가 아니다.

12:55 이후 stale exchange timestamp 제외가 증가했다.13:03:35 cumulative trade6174/depth11877 제외, 최근 반례의 exchange→packet receive lag12.652초, packet→normalization2ms. 로컬 socket read 이전 backlog와 외부 전송을 이 증거만으로 구분하지 않으며 임의 freshness 완화나 source-gap 복원은 하지 않는다. 이번1회 pipeline 증거 추출은 약1GiB를 읽고631MiB 파생본을 만들었으므로 재실행하지 않고 이후 bounded tail/경량 snapshot으로 관찰한다. 추출 process699359는 우선순위를 낮췄고 종료 확인했다. 운영 원본·checkpoint·lock 삭제는 없다.

13:10 자연 preflight: 미래에셋·삼성중공업·SK이터닉스·TYM은 당일 authority ready/exit0이다. SK텔레콤·영원무역 midday는 exit4 terminal quarantine이며 각각 `research_economics_nonpositive_under_current_cost`, `research_half_robustness_review_requires_new_profile_revision`이다. 둘 다 exact-date policy의 `unified_round_trip_cost_revalidation_nonpositive` 격리 대상으로, 단순 시스템 기동 장애나 토큰 결손이 아니다. 격리를 풀거나 실패를 성공으로 바꾸지 않았다.13:14 자연 service가 주문 없이 차단되는지 추가 확인한다.

수정 후 최종152 tests PASS(17.01s, 기존 경고1), Black/Ruff/diff PASS. 실행 중680 release는 변경하지 않았고, 경로 수정은 개발 폴더와 별도 `/tmp/kss-krx100-merge-q6l75zPS/review`에 격리했다. 이번 감시 중 restart/정책 설치/주문 조작은 없다. 승인 artifact self-hash95a10c…와 JSON file SHA2a07a2…는 서로 다른 해시 계약으로, self-hash와 PID pin의 일치를 확인했다.

13:14 자연 기동: 승인 low-price4개는 systemd dependency preflight를 재확인한 뒤13:14:07~12 시작/당일 READY, 삼성 midday PID723185도 실행/당일 READY이다. 격리2개는 dependency 차단/PID0으로 신규 주문 없이 유지한다.13:15 CJ CGV·한세·카카오 preflight 모두 당일 ready이다.

13:12 읽기 전용 broker는 삼성35/SKT10/와이씨1/레메디1·기존 target SELL2개를 확인했다([broker](../../tmp/intraday-monitor-20260910-1050/broker-131204.json)). 레메디387690은12:56:53 주문0049308→12:57:04 1주18,550원 실제 체결, 일일cap6/100이며 와이씨와 별개 main 보유다. 공용 registry 외 잔여는 main 실체결 확인과 분리하고 임의 귀속/통합하지 않았다.

13:15:43 와이씨 main record42433 holding은 Provider parse PASS라도 raw model EXIT/data_quality stale→effective HOLD로 정상화됐다. 이유는 `microstructure_missing_or_stale`/`holding_context_source_quality_unusable_defer_to_deterministic_guards`다. 이를 모델 HOLD 또는 정상 판단품질로 세지 않으며 기존 deterministic 보호의 실제 작동은 별도다.13:14:43 입력차단 사례는 bbo age2,265.677ms/fresh이나 trade·price3,375.896ms/stale이므로 호가/체결을 같은 원인으로 일반화하지 않는다.13:16 시점 collector trade timestamp reject7,997는 최근 약5분 증가 없음, depth15,286은 소량 증가이며 과거 제외/입력 차단 자체가 복구됐다는 뜻은 아니다.

13:24 삼성E&A/SD바이오센서 PID736498/736539·당일 READY 확인. CJ CGV/한세/카카오13:19 자연 기동도 당일 상태 갱신 완료이며, 앞선 거래일 상태/시작 직후 미갱신과 실제 실패를 구분했다. 삼성 오전 base SELL0018662는12:48:43 10주268,000원 실제 체결/기계 상태target_filled_at12:48:43.757249다. 이번12:52 이후 새 성과가 아니며 수수료/세금이 없는 state만으로 net을 계산·합산하지 않는다.

배포 재검증:13:18 고정release git src/restart/deploy dirty0, 승인10 code hashes·3 source hashes 불일치0, tmux657124 cwd=고정release/src, main13f8c92 유지. 신규 독립 기계 service는 개발 작업폴더를 참조하며 전체 고정배포 격리는 아직 아니다. 선택한 삼성 midday·미래에셋 process에서 명시 adaptive env 없음, live CLI는 adaptive services를 새로 주입하지 않으며 이번 세션의 신규 활성화 없음이다. 다른 세션의 코드 변경 권한/전체 리뷰 완료를 대신 선언하지 않는다.

## 종료 판정

- 배포: PID657193/고정680773d59c88 유지, frozen src/restart/deploy dirty0, KRX 당일 self-hash/PID pin 일치/일일6/100. 이 세션에서 restart·실주문·정책·수량·cap·cron/systemd 설정을 변경하지 않았다. 미완료 적응형 청산 변경을 메인 release에 넣지 않았다. 전체 기계/내일07:55의 공통 release routing은 아직 미통일이다.
- 13:30:21 collector: trade/depth persisted223149/350990, queue full0/0, writer error0/0, writer3/3, p95/p99=0.101078/0.130355ms, stop false, disk available28.93GB(십진). timestamp 제외 trade7997/depth15290는 정상 표본과 분리한다. canary가 저장 가능하다는 사실은 전수 제외 증명·Provider replay/R3 승격 완료가 아니다.
- 마지막 [broker 대사](../../tmp/intraday-monitor-20260910-1050/broker-133022.json): 삼성35/SKT10/와이씨1/레메디1, 기존 SELL0022607·0015751 각10주 유지/등록 owner 각1개. 이 감시 구간 신규 main 체결은 레메디 BUY0049308 1주이며 미청산이다. 삼성10주 완료와 와이씨1주 진입은 감시 시작 전이다. 신규 실현 순이익 개선은 증명되지 않았다. 기존028050 registry10/broker0 결손은 해결하지 않았고 main2종목의 registry 외 잔여를 수동 소유로 재분류하지 않았다.
- 기계: 승인 low-price11개+삼성midday1개가 예정 기동했다. SKT/영원midday2개는 기존 비용/연구 quarantine으로 주문 없이 차단. 미래에셋midday는 window 종료/NO_TRADE, 다른 profile은 무신호 평가 또는 신호창 대기였다. NHN·한국전력은13:29 기동/당일 READY 확인이며13:30 이후 전체 신호창 완료를 선행 승인하지 않는다.
- AI 품질: 정확한 감시 구간12:52:53 이상/13:30:00 미만, 실제 main 보유 record42433(와이씨)/42313(레메디)만 분리하면87개 평가 기록 중 Provider 호출·parse 성공30, 입력검사 차단57이다. 그30개 중24개는 원모델 EXIT/TRIM이 microstructure 품질 부족으로 effective HOLD가 됐다(와이씨 EXIT9/TRIM3, 레메디 EXIT5/TRIM7). 단순 Provider/parse 성공을 판단·청산 정상으로 표시할 수 없으며 이것이 다음 입력 복구의 우선 근거다. 실제 주문 없는 TRIM/EXIT도 체결로 세지 않는다. 전체 trace의 ID 미결속 행을 이 실보유 모집단에 섞지 않았다.

## 수리·리뷰와 남은 수락

`implementation -> self-review -> 공백 보완 -> 재리뷰 -> targeted validation`을 완료했다. 경로 수리 범위152 tests/Black/Ruff/compile/diff PASS, 관련 producer/startup consumer·checksum·symlink·explicit env·기존 guard 보존을 검토했다. 수정 두 파일은 root와 별도 격리 트리가 동일하며 현재 frozen runtime에는 미적용이다. 새 커밋·push·main 병합도 이번 요청에서 실행하지 않았다. 원본42193 SHA는 종료에도20aed058…e6707e로 동일하며 수동 ACK/삭제/원장 통합은 없다.

| 남은 상태 | 정확한 owner/근거 | 다음 수락 조건 |
| --- | --- | --- |
| source_quality | `RuntimeEnvIntradayObserve0910`: main 보유87행 중 입력차단57/호출 후 quality override24 | exact ws capture→holding context→prepared payload의 source별 age·microstructure 결손 원인을 닫고 raw/effective/실제 후단을 재대사; freshness·safety 완화로 우회하지 않음 |
| source_quality | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910`: timestamp 제외·bounded64 tail/과거 수집 gap | 유효 원천과 식별 가능한 제외를 보존하고 전수 증명 미완료/Provider hold를 유지; 같은 대용량 replay 반복하지 않음 |
| runtime path 미반영 | `RuntimeEnvIntradayObserve0910`: 원본42193 pending leg1, frozen relative default | 별도 검증된 고정release/코드·정책 일치/owner 대사 후 허용된 기동에서 원본 checksum과 exact companion ACK 확인; 코드 리뷰 완료를 자연 ACK로 대체하지 않음 |
| custody | `WidgetEpisodeApprovedNextDayExecution0910`: 028050 과거 deficit | 실제 수동 successor/broker receipt/기존 owner ledger·비용을 대사, 다른 owner로 흡수 금지 |
| 다음날 배포 수락 | `KRXDaily100NextDayStartupAcceptance0911`: 작업폴더07:55 cron |9/11 exact 후보/activation·실제 PID root/commit·오늘pin 미상속/일일100 소비 확인; 이번13:30 종료와 별개 |

기존 일일 OPEN owner에 결과를 기록하며 새 중복 작업을 만들지 않았다.14:20 이후·장후 producer는 not_yet_due로 조기 실행하지 않았다. print-only parser29 tasks PASS, 외부 Project/Calendar 동기화는 실행하지 않았다.
