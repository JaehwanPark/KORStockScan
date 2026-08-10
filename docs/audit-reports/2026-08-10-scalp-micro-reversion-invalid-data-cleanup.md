# Scalp Micro-Reversion Invalid Data Cleanup — 2026-08-10

## 판정

`2026-08-10 10:00 KST` 기준 현재 REGULAR canonical stream 수집은 정상이다. 08:34 storage incident의 Gate B 불합격 legacy path와 잘못된 CWD 아래 남은 legacy path만 삭제했다. 현재 수집 파일과 정상 epoch는 삭제하지 않았다.

## 삭제 전 증적

| 분류 | 파일 | Bytes | Rows | SHA-256 |
| --- | --- | ---: | ---: | --- |
| 08:34 실패 세션 legacy path | `data/observations/scalp_micro_reversion_forward/trade_date=2026-08-10/venue=SOR/session=SOR_PREMARKET/market_path.jsonl` | 536,855,845 | 292,727 | `ad299a91b01468e14a43890892a02f9d8f97eb845d0815278dd3e943527281f3` |
| 08:34 실패 세션 V1 reference | `data/observations/scalp_micro_reversion_forward/trade_date=2026-08-10/venue=SOR/session=SOR_PREMARKET/event_references.jsonl` | 645,856 | 614 | `f325e2e51c09eaad3bd02afa6cf480f084780051b1747440231b1e8448dc03f5` |
| 잘못된 CWD legacy path | `src/data/observations/scalp_micro_reversion_forward/trade_date=2026-08-10/venue=SOR/session=SOR_PREMARKET/market_path.jsonl` | 2,265,035 | 1,236 | `f177f8d48587bc110c9169858f5196417725b8ecc3fc8e1b2fffc7ee2701bbd6` |
| 잘못된 CWD V1 reference | `src/data/observations/scalp_micro_reversion_forward/trade_date=2026-08-10/venue=SOR/session=SOR_PREMARKET/event_references.jsonl` | 4,210 | 4 | `73ab850375f98422ac5579e8d39e461a7a9046b8f73f51ed214848aa06814e08` |

삭제 직전 PID `93795`의 `/proc/93795/fd`를 3회 점검해 위 경로의 open descriptor가 없음을 확인했다. 네 파일의 mtime은 현재 PID 시작 시각 `09:44:30 KST`보다 이전이며, 현재 writer는 `KRX_REGULAR`과 `SOR_REGULAR`의 `market_stream*.jsonl`만 사용한다.

## 삭제 결과

- 네 파일 `539,770,946 bytes`를 명시적 절대경로 검증 후 삭제했다. 삭제는 복구 불가능하다.
- 두 `session=SOR_PREMARKET` leaf directory도 비어 있음을 확인한 뒤 제거했다.
- observation root 사용량은 약 `550 MiB`에서 `44 MiB`로 감소했고 filesystem 사용률은 `72%`에서 `71%`, free는 약 `23 GiB`다.
- 삭제 직후 collector는 `healthy_observer_canary`, callback `62,500`, p95/p99 `0.111930/0.194600ms`, drop/invalid/gap/writer/self-disable/manifest/projection error `0`, reference coverage `100%`, `stop_required=false`를 유지했다.

## 보존 및 제외 경계

- 정상 수집 epoch `1786322680207508487`와 REGULAR canonical stream은 보존한다.
- 최초 canonical 재수집 epoch `1786322360935918570`의 stream 1,391 rows와 V2 reference 63 rows는 구조·authority 계약은 유효하지만 process window가 Gate B 불합격이다. 현재 writer와 같은 REGULAR 파일에 섞여 있어 장중 rewrite는 금지하고 epoch exclusion으로 유지한다.
- 삭제 전 canonical 검증은 JSON parse, authority/schema, `series_sequence == source_sequence`, duplicate key를 모두 통과했다. 정상 epoch 56개 series의 sequence gap/out-of-order는 `0/0`이다.
- 이 정리는 source-quality/storage cleanup이며 P2 discovery, selection, sim/runtime, threshold, provider, broker/order 권한을 열지 않는다.
