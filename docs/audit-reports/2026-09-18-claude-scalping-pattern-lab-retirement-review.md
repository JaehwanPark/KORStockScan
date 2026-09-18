# Claude Scalping Pattern Lab 폐기 검증

작성일: 2026-09-18 KST. 사용자 승인: 구현·반복 리뷰/수정/검증·관련 commit/push·immutable 배포와 불필요 산출물 삭제. 봇 재시작·주문·조기 PREOPEN 확정은 제외한다.

Owning plan: [PLR0–PLR6](../proposals/claude-scalping-pattern-lab-and-automation-retirement-plan-2026-09-18.md). 관련 source만 격리 worktree에서 검증하며 다른 세션 변경과 실행 중 release를 보존한다.

## 변경과 리뷰

- 전용 Claude 코드/config/prompt/output·scalping automation·cron wrapper와 전용 테스트를 삭제했다. Main 및 보조 tuning override 실행도 제거했다.
- EV/workorder/runtime summary/tower/checklist의 source intake와 Main trigger/controller/verifier/freshness 요구를 폐기했다. source identity로 과거 orders/non-selected를 제외하며 같은 ID의 다른 독립 owner와 기존 family는 보존한다.
- 공용 currentness/AI review/propagation은 기존 Swing caller 때문에 유지한다. 삭제 모듈 import·Claude producer 소비를 제거하고 Main `--exclude-swing` 호출은 파일/provider 접근 전 retired terminal을 반환한다. Swing OFF를 활성화하지 않는다. 공유 observability는 기존 Gemini caller의 계산만 보존한다.
- 리뷰에서 삭제 import, old monitoring override, unknown-profile recovery, obsolete source fingerprint, preserved AUTO task 전이 및 retired OFF에 따른 verifier false warning을 보완했다. 비퇴역 source/hash/정책 검사와 hard safety는 유지한다.

## 검증·배포·삭제 증거

격리 successor의 targeted pytest 20파일 **1,135 PASS**(Main consumer375 + 기타 계약760), 수정 Python33개 compile PASS, shell3개 `bash -n` PASS, `git diff --check` PASS와 print-only parser PASS다. 저장 보고서와 반환값의 일치, 삭제/과거 양수 입력, unknown-profile recovery 차단 및 독립 owner 보존을 검증했다. 합성 회귀는 자연 경제성 실증이 아니다. `tmp/claude-lab-retirement-20260918/validation.json` 및 두 tests 로그를 따른다. 배포·제한 refresh·cleanup은 후속 실제 receipt에서 고정한다.

## 정책과 경제성 경계

Lab 전용 실전 정책은 없으며 이번 폐기는 기존 다음 적용일 정책 값을 새로 계산하거나 승격하지 않는다. 모델 ΔEV·실제 순익·인과적 EV 개선은 이번 코드 제거로 입증되지 않는다. 9/21 정책/PREOPEN 원천의 보호 SHA와 자연 적용·완료 손익은 기존 독립 owner의 경계를 유지한다. 선택된 successor는 미래 invocation에 사용되고 실제 Main PID 소비/재시작은 수행하지 않는다.
