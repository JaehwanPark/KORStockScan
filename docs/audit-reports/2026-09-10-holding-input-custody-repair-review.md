# 보유 AI 입력·SELL recovery 경로 수리 리뷰

대상일: 2026-09-10 KST. 사용자 지시: 결함 보완/리뷰 반복, 커밋·푸시, 필요시 우아한 재기동. 기준 main/origin13f8c92d, 기존 frozen680773d59c88/PID657193. 다른 세션의 adaptive-exit·registry·PREOPEN 변경은 배포 제외한다.

## 원인과 수정

1. 실보유 record42433/42313의12:52:53~13:30 평가87개 중 입력차단57, Provider 성공30 중24개가 microstructure 품질 때문에 HOLD로 정상화됐다.13:15:40 request `holding_score:232140:1789013740322:7555a316` payload SHA11c1e78d0ca994ccd046eb9910a8777b7ebecef77b9a139912da3b10a7b56870에는 BBO/수량2127·922가 있으나 total depth0/0, microstructure_missing_or_stale였다.
2. normalized WS producer는 exact 0D의 `route_depth_totals.combined`를 기록하지만 AI route view는 없는 ask_total/bid_total 필드만 읽었다. 같은 exact route row의 정수·비음수 totals를 전달하고 malformed/missing은 fail closed한다. 다른 route의 flat 가격·수량 alias를 상속하지 않는다. wire/FID/API request/parser 자체는 변경하지 않았다. native-route combined 계약은 기존 path_journal validator 계약을 재사용한다.
3. 보유 경로가 blocking REST 체결/분봉 조회 전 snapshot을 조회 후 preflight에도 재사용했다. 조회 후 WS manager의 기존 get_latest_data를 단회 호출하여 AI 전용 local snapshot을 받는다. 원본 clock을 restamp하지 않으며 future/regressed/invalid/error/missing은 갱신하지 않는다. BBO·tape·type provenance 결손을 이전 snapshot에서 채우지 않고 기존 exact preflight/3초 SLA를 유지한다. 전역 holding/주문 계산 값은 바꾸지 않고 AI current price·동일 비용식의 PnL/현재점 포함 peak만 새 입력과 일치시킨다. 갱신 진단은 기존 holding pipeline에 기록한다.
4. quote freshness를 global last_ws_update_ts로 판단하면 새0B가 낡은0D를 가릴 수 있었다. 명시0D 시각을 먼저 사용하고 미래 호가는 통과시키지 않는다. 기존 source-quality override/HOLD 중립화, broker/hard/protect/emergency guard·AI 점수/호출 budget은 유지한다.
5. holding execution_pnl이 누락 비용을0으로 간주해 mark/gross를 net으로 표시했다. 비용/슬리피지가 모두 명시된 유한 비음수 값일 때만 estimated net을 계산한다. 누락/비정상은 null, 명시0은 유효하다. 사용자 비용 정책/실주문 수량은 변경하지 않는다.
6. frozen release의 src cwd에서 기존 SELL42193 journal을 찾지 못했다. canonical shared DATA_DIR를 통해 기존 `/home/ubuntu/KORStockScan/src/data/runtime/sell_receipt_recovery`를 사용하며 명시 env override는 보존한다. child symlink·checksum·identity·수량·terminal 검사는 기존대로다. 별도 data/runtime/pending159나 다른 owner의 원장을 합치지 않는다.

## 리뷰·검증

- valid normalized depth가 기존 코드에서 microstructure_missing_or_stale로 탈락하는 RED 재현1건을 확인했다. invalid negative/bool/missing totals는 계속 차단한다.
- helper source 전달/누락 미보간/시각 원본 보존, stale/future quote, 실제 blocking 조회 뒤 최신 cache가 기존3초 gate를 통과하는 경로, null cost/명시0을 회귀 검증했다.
- self review → supplemental fix → re-review → targeted validation: 1420 PASS,1 deselected,기존 pandas warning1(57.00s). 대상 holding context/AI snapshot/cache/forensic probe/scale-in/live receipt/intraday activation/restart race/Samsung handoff. Black/Ruff/compile/diff PASS.
- 제외1건 `test_holding_score_v2_payload_stays_compact_for_low_latency`는 수정 전 실행680에서도 동일5448>5000으로 실패한다. 이번 변경으로 발생한 회귀가 아니며 테스트 제한을 바꾸거나 실패를 PASS로 재표시하지 않았다. 기존 compact payload 예산 이슈는 별도 OPEN으로 인계한다. 전체 저장소 모든 결함0/전체 pytest PASS를 주장하지 않는다.
- 이번 repair의 source 전달/기존 guard/producer-consumer 범위 미해결 신규 finding0이다. 실제 자연 소스·Provider·ACK·매매빈도·net EV 수락과 구분한다. Provider replay/장후 대용량 report 재생성은 실행하지 않았다.

## 배포 수락

코드 변경만으로 활성화를 승인하지 않는다. 10개 intraday pinned code와3개 source hash, 당일 env/PID·일일 사용량을 검증하고 main/widget/episode/manual 계좌·미체결을 대사한다. exact 기존 journal 원본을 보존한 뒤 새 frozen release에서 기존 restart.sh의 prepare/drain/new-PID/commit을 사용한다. 코드 적용 필요성은 확인됐지만 실제 재기동 결과와 자연 ACK는 아래 후속 기록으로 확정한다. 원래 코드680과 당일 정책은 rollback 근거로 유지한다. 다른 기계의 재기동·정책 변경/기존 보유 편입은 하지 않는다.

진행 상태: 코드 commit `769952574cfbc3f7fa4af3115c847abc99237377`, branch `fix/holding-input-custody-20260910`를 origin에 push했다. 다른 세션 미커밋 변경과 분리했으며 main 병합은 이번 작업에 포함하지 않았다.

### 13:52~13:56 실제 적용 수락

- 새 frozen release `/home/ubuntu/KORStockScan-runtime-releases/holding-input-76995257`, PID772330. 기존 PID657193을 기존 restart.sh prepare/drain/commit으로 한 차례 우아하게 재기동했다. pinned code10개/source3개 hash 불일치0, 새 PID env verify passed/pid_passed=true, missing/mismatch 및 policy/dated fail0이다. 당일 approval SHA95a10c85…/KRX1주 일일100과 기존사용6을 보존했다. 운영 prompt/provider/수량/threshold/safety와 독립 machine 서비스는 변경하지 않았다.
- WS LOGIN13:52:13,13:52:23 collector healthy_observer_canary_with_source_row_exclusions/stop=false, trade/depth persist187/256, queue full0/0, writer error0/0, callback p99 0.828ms, free28.36GB. timestamp 제외1건은 정상 데이터로 보간하지 않는다.
- fresh broker 대사13:51:06→13:56:05: 삼성25·SKT10·와이씨1·레메디1주와 SKT SELL0022607 잔량10주 동일, 해당 미체결 exact owner1개. 삼성 기존10주 target은13:30:46에 자연 체결되어 이번 배포 효과가 아니다. 과거028050 registry deficit은 별도 OPEN, main1주 두 종목을 manual로 오분류하거나 machine에 편입하지 않는다. 기존 예수금 operator floor는 변경하지 않았다.
- 원본 SELL42193은 `tmp/holding-restart-20260910-SKM1Uc/sell_receipt_recovery`에 백업했다. 원본 파일 SHA20aed058e60df96d2754cc36a3213a36d5d31b7517271dd5d82a89ad93a6707e.13:52:09 startup consumer가 sell_completed와 entry_opportunity_recheck_sell_completed를 실제 기록했고 canonical journal은 정상 consumer 정리로 없어졌다. exact attempt eor-b6c92dd93e6f6fe836656245/BUY0026276/SELL0029892/qty1/net175원/비용35원을 대사했다. 이는10:11 기존 거래의 귀속 복구이며 신규 수익/주문이 아니다. broker actual venue UNKNOWN/SOR 불확실성은 그대로다. 수동 ACK·원장 병합은 하지 않았고 백업으로 원본 복구 가능하다.
- 실제13:55:42 와이씨 payload request holding_score:232140:1789016142850:1c8c47c9, SHA0bf24bc9f4d4414b017fa0871a8aad8c3ea9daf575c9e7403be03df880832c73: quote age87.031ms, ask/bid total17304/10793, fresh_consistent.13:55:48 레메디 request holding_score:387690:1789016148757:7ac2d6a0, SHA3a1d282b153c9a197320bdbb63d251f6d14d95eb0599e9770582d78e3669e120:219.987ms/661·3113/fresh_consistent. 실제 Provider parse 성공 및 각각 EXIT/TRIM, quality override=false를 확인했다. 강제 매도 실행이나 순이익 개선까지 입증한 것은 아니다. 비용 미제공 estimated net은 입력에서 누락/null로 유지되며 gross를 net으로 승격하지 않는다.
- 같은 창의 stale_tick_context는 여전히 preflight 차단됐다. 안전장치를 완화하여 모든 호출을 정상화한 것이 아니다. source ingress 지연/과거 수집 손실, 매매빈도·빠른 청산·비용 차감 EV와 기존 compact payload 테스트 실패는 별도 수락이다. 오늘13:30 모니터링 완료 후 이번 사용자 수리 지시에 따른 짧은 배포 검증이며 무기한 모니터링 연장은 아니다.
- 내일07:55 cron은 여전히 원 작업폴더 기동 경로다. 오늘 frozen PID 성공만으로 내일 동일 코드 사용을 보장하지 않는다. 기존 KRXDaily100NextDayStartupAcceptance0911에서 검증된 release 선택/정식 exact-date policy/100 carry/실제 PID를 확인한다. 이번 작업은 cron·배포 router를 변경하지 않았다.
