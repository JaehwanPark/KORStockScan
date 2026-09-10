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

진행 상태: 코드 검증 완료. commit/push/운영 수락 후 갱신 예정.
