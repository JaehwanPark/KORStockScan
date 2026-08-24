# Scalp Micro-Reversion Source Exclusion Purge — 2026-08-24

## 판정

기존 source exclusion manifest가 이미 사용 금지한 정확한 7개 `trade_date+venue+session+sequence_epoch` 범위만 closed-date raw stream에서 물리적으로 제거했다. 8월 10~13일 전체 날짜, 정상 epoch, depth stream, exclusion provenance와 현재 거래일 8월 24일은 삭제하지 않았다.

## 삭제 결과

- authority: `post_session_storage_only_no_trading_authority`
- manifest: `configs/scalp_micro_reversion_source_exclusions.json.txt`
- 대상: stream `196,935`행, event reference `5,689`행
- 결과: `status=pass`, failure `0`, exact scope 잔존 `0/0`
- 선택 source bytes: `20,580,947 -> 14,641,030`, 논리적 reclaim `5,939,917 bytes`
- observation tree 실측 감소: `4,688,824 bytes`
- 정상 stream/reference 행과 depth 파일은 보존
- current observer: `healthy_observer_canary`, queue/worker/writer error `0/0/0`

세션별 결과는 [apply artifact](/home/ubuntu/KORStockScan/data/report/scalp_micro_reversion_source_exclusion_purge/scalp_micro_reversion_source_exclusion_purge_2026-08-24.json)에 기록했다.

## 보존형 추가 정리

8월 21일 정상 closed-date JSONL 14개는 삭제하지 않고 기존 gzip roundtrip 검증 경로로 압축했다.

- uncompressed source bytes: `2,200,184,707`
- observation tree 실측 감소: `2,108,674,367 bytes`
- filesystem free 증가: `2,105,872,384 bytes`
- compression failure/recovery required: `0/0`
- whole-date purge: disabled

상세 결과는 [compression artifact](/home/ubuntu/KORStockScan/data/report/scalp_micro_reversion_source_exclusion_purge/scalp_micro_reversion_closed_date_compression_2026-08-24.json)에 기록했다.

## 검증 및 권한 경계

- purge 전 전체 exact-scope dry-run count가 manifest 예상치와 일치했다.
- purge는 trade-date exclusive lock, open/stability 검사, filtered gzip 재독해, hard-link rollback, manifest current-byte 갱신을 사용했다.
- purge 후 excluded epoch 잔존 수와 임시/backup residue는 모두 `0`이다.
- P2 exclusion manifest는 파싱 가능 상태로 보존했다. 이미 생성된 파생 artifact가 삭제된 raw를 정상 입력으로 재해석하지 못하도록 exclusion provenance를 제거하지 않았다.
- 이 작업은 실주문, threshold, provider, bot, quantity/cap, broker/account/order 및 hard safety에 영향을 주지 않는다.
