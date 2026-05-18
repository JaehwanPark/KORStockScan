# EV 개선 후보 백로그 (for Ops)

생성일: 2026-05-18 07:58:23

---

## 1. split-entry rebase 수량 정합성 shadow 감사

- **기대효과**: rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함
- **리스크**: false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능
- **필요 표본**: rebase_integrity_flag 케이스 20건 이상
- **검증 지표**: cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포
- **적용 단계**: `shadow-only`

## 2. partial → fallback 확대 직후 즉시 재평가 shadow

- **기대효과**: 나쁜 포지션 확대(확대 직후 peak_profit < 0) 코호트 조기 감지
- **리스크**: 정상 확대 패턴도 일부 차단 가능 — shadow 관찰 선행 필수
- **필요 표본**: partial_then_expand 코호트 30건 이상
- **검증 지표**: 확대 후 90초 내 held_sec soft stop 비율 감소 여부
- **적용 단계**: `shadow-only`

## 3. partial-only 표류 전용 timeout shadow

- **기대효과**: 1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리
- **리스크**: full fill 전 짧은 대기 케이스를 오분류할 수 있음
- **필요 표본**: partial-only 코호트 20건 이상
- **검증 지표**: partial-only held_sec 중앙값, timeout 이후 실현손익 분포
- **적용 단계**: `shadow-only`
