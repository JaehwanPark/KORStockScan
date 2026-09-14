# Machine AI PASS submit 경로 코드리뷰·배포 결과

작성 시각: `2026-09-14 09:54 KST`

## 판정

- 코드리뷰와 배포는 완료됐다. 기계 판정이 `ENTER_NOW`이고 같은 exact context의 AI 판정이 유효한 `PASS`이면 legacy probe marker가 최종 action을 `WAIT`로 되돌리지 않고 기존 submit guard로 `BUY` 후보를 전달한다.
- 전역 1주 제출 제한은 없다. `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY=1`과 `one_share_exploration` 명칭은 첫 probe 계획에 남아 있지만 실제 신규·추가매수 수량은 `position_sizing_dynamic_formula:2026-09-11`, residual과 scale-in은 각 전용 owner가 결정한다. prompt policy나 exploration cap guard는 `qty != 1`을 거절하지 않는다.
- 배포·PID 소비는 검증했다. 실제 submit/fill/terminal과 비용 차감 순이익 개선은 신규 자연 표본으로 별도 판정한다.

## 구현과 보완

- `src/engine/ai_engine_openai.py`: exact `ENTER_NOW + PASS`를 기존 submit guard로 전달하고 `VETO → DROP`, CAUTION/INSUFFICIENT/transport 오류는 기존 fail-closed `WAIT`를 유지했다. 최근 청산 직후 재진입 차단은 machine PASS 경로에도 적용했다.
- `src/engine/sniper_state_handlers.py`: 통합 `_AL` source의 KRX 정규장과 KRX/NXT 애프터마켓 session 의미를 clock scope로 정규화했다. 실제 route 변경은 계속 fail-closed하며, 예상 가능한 `entry_context_revalidation_route_changed` race는 process ERROR가 아닌 정보성 block으로 기록한다.
- quantity-owner, route/session handoff, AI transport, async entry bridge, scale-in, owner coexistence와 manual exclusion 회귀 테스트를 현행 계약에 맞췄다.

## 리뷰와 검증

- 검토 범위 finding은 0이다. workspace와 detached release에서 각각 Entry AI/route/quantity-owner/custody targeted test `608 passed`를 확인했다.
- Python compile, 문서 print-only parser `27`개, `git diff --check`가 통과했다.
- 확장 `test_sniper_scale_in` 묶음에는 변경 전에도 재현되는 오래된 route/holding 계약 실패가 남아 있어 전체 suite 성공으로 표시하지 않았다. 이번 1주 owner·AI PASS·route 정규화에 직접 관련된 회귀는 모두 통과했다.
- commit/push: `895cd2fd0830889735fa33edd4d29cff207091b4`, `origin/main`.

## 배포와 재기동

- release: `/home/ubuntu/KORStockScan-runtime-releases/machine-ai-pass-submit-repair-20260914`
- 공통 selector와 독립 매매기계 systemd drop-in 17개가 같은 release를 가리키며 cron route 9개 검증이 통과했다.
- 재기동 전 broker 대사: KRX/NXT inventory 정상, 보유 `005930` 25주, 미체결 주문 0건.
- canonical `restart.sh` 결과: 이전 PID `67225` 종료, 새 PID `149630` 기동. PID cwd와 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT=895cd2fd...`, source dirty=false를 확인했다.
- exact-date runtime env verify는 `status=pass`, PID mismatch 0, runtime policy failure 0, unverified selected family 0이다.
- WS REG 뒤 `0B`와 `0D` first-data가 수신됐다. `2026-09-14 09:54` full error detector는 7개 detector 모두 PASS, operational mutation 0이었다.
- 이미 실행 중인 독립 주문 owner는 현재 episode/custody를 보존하려고 강제 재시작하지 않았다. systemd의 후속 실행 경로는 새 release로 설치됐으며 각 프로세스의 실제 새 PID 소비는 다음 안전한 자연 기동 receipt로 확인한다.

## 남은 자연 수용조건

- 같은 bundle/hash의 자연 `mechanistic ENTER_NOW → AI PASS → BUY candidate → final guard → accepted submit` lineage를 확인한다.
- 실제 수량이 dynamic sizing 결과와 일치하고, probe/residual/scale-in owner가 혼합되지 않았는지 확인한다.
- submit/fill/terminal 이후 실제 비용을 결속해 비용 차감 EV와 작은 순이익 빈도에 대한 효과를 별도로 판정한다.
