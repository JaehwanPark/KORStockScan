# EV 개선 후보 백로그 (for Ops)

생성일: 2026-09-09 21:53:08

---

## 1. split-entry rebase 수량 정합성 report-only 감사

- **기대효과**: rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함
- **리스크**: false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능
- **필요 표본**: 재현 가능한 결함 증거; 경제성/승격 표본 floor 없음
- **검증 지표**: cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포
- **적용 단계**: `report_only_observation`

## 2. partial fill quality source attribution

- **기대효과**: partial/full 품질을 분리해 수익률 착시 방지
- **리스크**: 관찰만으로 timeout/수량/진입조건 변경 불가
- **필요 표본**: 재현 가능한 fill identity 증거; 별도 승격 floor 없음
- **검증 지표**: partial_then_expand_flag count; exact partial/full net economics
- **적용 단계**: `report_only_observation`

## 3. same-symbol repeat source attribution

- **기대효과**: 반복 거래의 수익과 손실을 함께 분리해 원인 관찰
- **리스크**: 반복 횟수만으로 cooldown 또는 매수 차단 불가
- **필요 표본**: 재현 가능한 identity/sequence 증거; 별도 승격 floor 없음
- **검증 지표**: same_symbol_repeat_flag count; exact lifecycle net economics
- **적용 단계**: `report_only_observation`
