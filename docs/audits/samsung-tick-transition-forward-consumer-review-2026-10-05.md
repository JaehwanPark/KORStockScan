# 삼성 1틱 전환 후보 — 이후 날짜 소비자 구현·검증

작성일: 2026-10-05 KST. 사용자 `다음액션 실행`에 따라 [앞선 연구의 후속 연결](samsung-continuous-tick-transition-research-review-2026-10-05.md#6-종료보존다음-소유)을 구현했다. 새 가설 탐색이나 운영 정책 적용은 범위가 아니다.

## 1. 완료한 연결

[오프라인 소비자](../../src/engine/scalping/samsung_tick_transition_forward_validation.py)와 [회귀](../../src/tests/test_samsung_tick_transition_forward_validation.py)를 추가했다. 위치는 기존 연구 모듈과 같은 `src/engine/scalping`이며 engine root·매매 실행 경로·API parser는 변경하지 않았다.

- 원 `absorption_p60_tick_shift1_v1`의 후보 ID·1틱 이동/10틱 폭/60 경계/5초 endpoint·unknown 승계·2026-10-05 이후 날짜를 고정한다.
- 원 연구 frozen과 원흡수 frozen을 수정하지 않는다. 원 frozen의 `not_implemented`는 작성 당시 상태로 남고, 별도 소비자 계약이 현재 `implemented`를 증명한다.
- 등록 시 원 frozen/evidence/source SHA·원흡수 parent·기존 삼성 동등성 migration을 검증한다. 새 소비자 코드와 의존 코드의 물리 SHA를 별도 계약으로 고정한다. 이후 코드나 계약이 달라지면 새 날짜 실행을 거부한다.
- 검증은 후보 재선정 없이 기존 정책 B0·원흡수 A0·H2·고정1틱 후보의4개만 비교한다. 전체 origin과 MAIN_FIXED_WATCH를 분리한다.
- 정책 publisher·주문·API·수집·runtime 재시작 경로는 없다. 새 후보의 운영 선택 여부를 자동 결정하지 않는다.

최종 소비자 계약: [consumer-contract-v2.json](../../tmp/samsung-tick-forward-consumer-20261005/consumer-contract-v2.json).

## 2. 실제 입력과 계산

| 입력 | 소유 생산 경로 | 소비 방법 |
|---|---|---|
| 원 Main 판정 | `data/report/machine_observation_projection/machine_observation_projection_<date>_0_1.json[.gz]` | source/evidence/raw SHA·원 날짜·판정시각·종목/시장·native·실제 bundle/action 검증 |
| 완료 가격 | `data/report/machine_completed_price_source/machine_completed_price_source_<date>.json` | 기존 price-source 검증·원 비용/stop·10분→미도달 시60분 경로 재사용 |
| 체결 | `data/observations/scalp_micro_reversion_forward/trade_date=<date>/venue=SOR/session=SOR_REGULAR/market_stream.manifest.json`와 선언 shards | 기존 정규화 reader로005930_AL만 읽고 보관 사본의 물리 SHA·수신시각·seq·epoch 결속 |

체결을 새로 수집하지 않는다. 입력이 모두 있을 때만 기존 shards의 정규화 결과를 실행 디렉터리의 `normalized-trades.json.gz`에 저장한다. 이 사본의 SHA와 원 manifest/shard SHA를 결과에 함께 남긴다.

현재10tick의 기준 시각은 기존 연구에서 사용한 두 출처로 제한한다. 원 `entry_machine_input_as_of`에서 feature가 일치하면 그 구간을 사용하고, 불일치하면 원 feature receipt/BBO receipt의 시각만 검사한다. 임의로 과거 구간을 훑거나 미래 가격에 맞는 구간을 선택하지 않는다. fallback receipt는 종목005930_AL·경로krx_nxt_integrated와 과거 시각을 확인한다.

원현재10tick의 재계산·raw 결속을 통과한 뒤 직전1tick까지 연결한다. Main과 독립 collector의 epoch를 같은 값으로 치환하지 않는다. 이 증빙은 기존 연구와 같은 **독립 archive의 원 feature 대사**이며 Main transport의11개 tick을 직접 입증하거나 운영 입력 수집 개선이 완료됐다는 뜻은 아니다.

원 판정의 정확한 policy generation과 활성화 시각을 `samsung_policy_compatibility.source_bundle`로 검증한다. 삼성 행동이 달라진 parent를 과거 후보와 임의로 비교하지 않는다. 잘못된 row는 사유와 함께 격리하고, 중복 trace·봉인 파일 변경 등 재현 계약 위반은 명시적으로 실패한다.

시각·구간·행동 계산을 먼저 끝낸 뒤 결과 label을 계산한다.10분 내 손절은 이후 반등으로 덮어쓰지 않고, 완전한60분 미도달만 비용 후 종료값을 계산한다. 검열/가격/비용/stop 결손은0으로 채우지 않는다. 조건 미식별 수를 성능과 별도로 기록한다.

## 3. 리뷰·회귀·과거 대사

- 첫 구현18개 및 관련99개 회귀 PASS 후, 재리뷰에서 fallback 시각의 종목·경로 검사를 명시적으로 보강했다.
- 최종 **103 PASS**. 등록 계약/원 frozen 변조, 과거 날짜 거부, source 부재·빈 입력·원천 탈락, 실제 정규화 shard 소비, 원본 변경, 원행동 변경, unknown 승계, fallback 시각·다른 종목/경로, 비용/손절/미도달 및 engine 위치 gate를 검증했다.
- 실제 역사519관측을 새 소비자로 재계산했다. **원 receipt·조건·행동 차이0**,4개 정책의 선택 ID·지표 차이0이다. 새 날짜 검증으로 표기하지 않았으며, 역사 지표 대사는 원 봉인 label을 재사용했다.
- 정상 intake 회귀는 테스트 디렉터리의 합성10/6 원천을 사용했다. 해당 통합 테스트의 bundle 조회와 가격 index I/O는 격리 대역이고, source/receipt/정규화/판정/가격경로 계산은 실제 함수를 사용했다. 실제 운영 parent/migration은 원 frozen 등록 과정 및 기존 compatibility 회귀로 별도 확인했다.
- Python compile·diff·문서 link·print-only parser와 보호 SHA를 확인했다. 검토 범위의 미해결 코드 결함은 없다. 전체 거래 suite·외부 API·새 원천 수집·배포/PID 소비·신규 성능 검증은 수행하지 않았다.

[최종 회귀 로그](../../tmp/samsung-tick-forward-consumer-20261005/final-tests.log), [역사 대사](../../tmp/samsung-tick-forward-consumer-20261005/historical-parity-final.json).

초기 `consumer-contract.json` 및 `readiness-2026-10-06`는 route 보강 전 코드의 기록이다. **현재 실행에는 v2 계약을 사용한다.** 원 연구/정책 frozen을 다시 발행하지 않았다.

## 4. 10월6일 실제 준비 점검

[v2 준비 결과](../../tmp/samsung-tick-forward-consumer-20261005/readiness-v2-2026-10-06/result.json)의 상태는 **`waiting_new_source_date`**다. 실제 root에서10/6의 원 판정 projection·완료 가격·체결 manifest 세 경로가 모두 부재다. 관측0은 대기 상태이며 정책 성능0이나 후보 탈락이 아니다.

구현이 없는 상태는 해소했다. 남은 것은 새 날짜 원천을 소비하는 실제 검증이다. 데이터가 없는 동일 상태를 반복 재계산하지 않는다. 수집 방식·예약 실행·장후 자동화 체인을 변경하지 않았으므로, 이 CLI를 장후 자동 실행에 연결했다고 주장하지 않는다.

## 5. 다음 실행과 보호 경계

기존 `SamsungFrozenCandidateValidation1006`가 실제 이후 날짜 검증을 소유한다. 원천 세 경로가 생성된 뒤 검토된 workspace에서 다음을 실행한다. 기존 승인 release에는 이 신규 오프라인 모듈이 없으므로, 과거 H2 CLI의 selected-release cwd 지시와 구분한다. 소비자 계약이 코드 SHA를 확인하며, output은 새 generation이어야 한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_tick_transition_forward_validation \
  --root /home/ubuntu/KORStockScan \
  --contract tmp/samsung-tick-forward-consumer-20261005/consumer-contract-v2.json \
  --date 2026-10-06 \
  --output tmp/samsung-tick-forward-consumer-20261005/forward-2026-10-06-run-01
```

새 날짜 결과에서 전체/상시감시·현재 receipt/추가 조건 가용성·확정 승률·완전 경로 양수 비율·미확정 분모를 함께 검토한다. 동결 후보가 원흡수·H2보다 나은지는 그 결과로 판단한다. 오늘의519관측·6선택을 미래 검증 표본으로 재사용하지 않는다.

선택 release/current/10/6 정책·체크리스트·prepared receipt 및 기존 frozen을 포함한 **9개 보호 SHA 불변**을 확인한다. 운영 삼성 정책과 Main/Widget/Episode 준비·PID 소유는 기존 상태를 유지한다.
