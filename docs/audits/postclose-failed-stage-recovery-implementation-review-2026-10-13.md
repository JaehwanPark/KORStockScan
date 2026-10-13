# 2026-10-13 장후 실패 단계 수리·재개 검토

사용자 지시: 실패한 지점부터 고쳐서 재실행. 원 source/publication은 `2026-10-13`, 다음 적용일은 `2026-10-14`다. 부모 실행본은 `main-rest-reduction-20261013` / `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`이며 작업본의 다른 I/O·REST 변경은 수리에 포함하지 않았다.

## 수정과 수용 경계

- 초기 수량 CLI의 heavy admission만 기존 dispatcher와 동일한 14,400초로 맞췄다. 두 compute slot·writer 순서·검증된 inherited descriptor·종료 회수는 유지한다. 수량·가격·정책 선정·주문·provider 로직은 변경하지 않았다. 60초보다 긴 정상 선행 heavy 작업 뒤 실제 슬롯 취득·해제를 확인하는 회귀를 추가했다.
- 같은 날짜의 joint 최초 등록은 `continuous_reversal_operating_comparison_v1`의 실제 machine/auxiliary, 승인 request와 frozen source receipts로 stage를 결속한다. 구 `source.json`·fixed-watch sidecar·call-freeze/provider-results를 합성하거나 복원하지 않는다. 승인·exact date·sealed body·48 cell/route·source byte hash·false runtime/order authority와 auxiliary 정책 소비 검증을 유지한다. Initial operator designation에 독립 경제성 비교 gate를 추가하지 않는다. 새 source 변경은 stage reuse를 무효화한다.
- `run_threshold_cycle_postclose.sh SOURCE_DATE --resume-from-initial-quantity`는 실제 native main 실패의 마지막 명령이 초기 수량일 때만 지원한다. 원 command metrics, producer-issued artifact reuse receipts·본문/Markdown SHA·5개 aftermarket code hash, 완료 prefix·정책 날짜·EOD·preflight·machine/delay/labels terminal을 검증한 뒤 START한다. 원 실패를 attempts에 보존하고 source-only scoped resume receipt를 새 main에 결속한다. 기존 prefix와 bot action을 생략하고 초기 수량부터 기존 하류를 실행한다. 일반 cron 동작은 유지한다.

## 리뷰·검증

구현→self review→보완→re-review를 수행했다. 입력이 변경됐거나 다른 명령이 실패했거나 원 main이 실행 중인 경우 재개를 거부한다. 등록 report의 authority/date 변조와 원천 변경이 실패하는지 확인했다. 실제 실패 machine 출력의 읽기 전용 validation은 issues 0이고, 기존 초기 수량 current 정책도 수정 코드에서 검증됐다. 이는 새 정책/PID/경제성 수용을 뜻하지 않는다.

- Admission·stage·wrapper 회귀: 117 PASS.
- Joint source/registration 회귀: 43 PASS 및 환경에서 누락됐던 frozen parent/source/evidence 사본을 격리된 fixture 영역에 공급한 native publication 회귀 1 PASS. 실제 provider/store 호출은 사용하지 않았다.
- Python compile, `bash -n`, `git diff --check`, 문서 print-only parser PASS. 기존 checklist owner 8개와 다른 사용자 편집은 유지한다.

코드 gate 범위에서 finding 0이다. 실제 재실행·새 stage terminal·summary/checklist/strict/controller·다음 PREOPEN/PID와 비용 후 성과는 각각 후속 증거로 기록한다. 설치 cron/서비스·bot 재기동·수동 env/lock/provider/threshold·주문 권한을 추가하지 않는다. 미래 05:35 최종화는 별도 예정 owner다.
