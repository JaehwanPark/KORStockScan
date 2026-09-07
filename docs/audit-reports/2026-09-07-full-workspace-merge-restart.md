# 2026-09-07 전체 변경 병합·우아한 재기동

사용자 요청: `전체 커밋&푸시&main 병합 후 우아한 재기동`.

## 범위와 실행 경계

- 현재 작업 트리의 전체 소스·테스트·deploy wrapper·검토 문서를 대상으로 한다. 실행 중 계속 갱신되는 `data/cache`, `data/runtime`, `data/report` 산출물과 임시 파일은 보존하되 소스 커밋에서 제외한다.
- BUY Funnel schema5/exact2·controller/PREOPEN binding, AI trace caller lineage, census wrapper 실패 전파·SLA recall, micro timestamp source-quality, scanner lookup-attention source 제외·자원배분 증거 계약을 통합한다.
- 병합 전 producer/consumer·runtime authority를 리뷰하고 관련 회귀·compile·shell syntax·diff·checklist parser를 검증한다. 검증 중 소스가 바뀌면 해당 세대의 검증을 반복한다.
- 표준 `restart.sh`만 사용한다. Samsung owner handoff와 exact-date runtime verification이 실패하면 우회하지 않는다. 주문 취소·강제 매도·수량/threshold/provider/cap 변경은 요청 범위가 아니다.

## 사전 확인

- 시작 HEAD/main/origin/main: `314ca993`. 메인 봇 PID `195755`, tmux supervisor `bot`.
- 기존 PID exact-date `2026-09-07` runtime verification PASS: missing/mismatch/findings 0, runtime policy/dated override/unverified family 0.
- 12:57:40 KST read-only broker 확인: KRX/NXT inventory complete, 005930 40주·010140 10주·042660 20주, 미체결 SELL 5건. snapshot SHA256 `62899c67a12ee6bd88d56f2446dd862d9f0436e71c171e90b4901c175b189283`. 토큰은 existing cached token만 사용했고 신규 발급이나 주문 호출은 하지 않았다.
- 초기 통합 회귀 1,686 PASS, dependency deprecation warning 1건. 이후 scanner 코드 추가 변경을 확인하여 최종 검증 세대를 다시 확인한다.
- Ruff 전체 선택 파일에서 기존 `E402` 43건·`E722` 1건. 기존 HEAD의 `ai_engine_openai.py` 26건·`scalping_scanner.py` 18건과 동일하며 새 lint 진단은 없다. Python compile 및 shell syntax/diff 검사 PASS.

## 최종 결과

- 추가 scanner 검증 보완까지 포함한 마지막 재실행은 **1,689 PASS**, dependency warning 1건이다. 검증 전후 선택 소스·테스트·wrapper SHA256이 동일했다. malformed resource count의 fail-closed 처리, lineage/fill/resource census 대사, 정렬 시점 profile 고정과 versioned resource pair 검증을 재리뷰했다. traceability 표에서 이탈한 기존 5개 행은 원래 위치로 복원하고 신규 보충 설명은 표 밖에 유지했다. 검토 범위의 미해결 코드 finding은 0건이다.
- 최종 검증된 세대를 커밋 대상으로 고정한다. 커밋·병합 또는 재기동 직전 소스가 추가 변경되면 미검증 코드를 그대로 재기동하지 않고 재검증한다.
- commit·push·merge·재기동 PID·runtime verify·broker 연속성 결과는 실행 후 보강한다. 이 문서의 사전 검증은 재기동 완료 증거가 아니다.
