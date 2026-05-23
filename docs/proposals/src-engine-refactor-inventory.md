# src/engine Refactor Inventory

기준: `2026-05-23 KST`

## 판정

- 리팩터링은 전체 일괄 이동이 아니라 safe slice 방식으로만 진행한다.
- 기존 `src.engine.<module>` import와 `python -m src.engine.<module>` 실행 경로는 현재 compatibility surface다.
- `MetaPathFinder` shim은 사용하지 않는다. 이동한 파일은 명시적 wrapper module로 old import/CLI를 유지한다.

## Phase 0 Inventory

현재 repo 기준 확인값:

- `src/engine/*.py`: `131`
- `if __name__ == "__main__"` 진입점: `71`
- `deploy/*.sh`의 `src.engine` module/import 참조 라인: `72`
- `src.engine` module 실행을 포함한 deploy script 파일: `20`
- `src/tests/*.py`의 `src.engine` import/monkeypatch 참조 라인: `397`
- `src.engine` 참조가 있는 test 파일: `132`
- README/docs/deploy/tests/engine 내 current path 참조 파일: `345`

## 이동 금지 / 후순위 파일

초기 slice에서 이동하지 않는다.

- runtime/order/provider/threshold/bot restart 경로:
  - `kiwoom_sniper_v2.py`
  - `sniper_state_handlers.py`
  - `kiwoom_orders.py`
  - `ai_engine_openai.py`
  - `threshold_cycle_preopen_apply.py`
- 현재 삭제/retired된 파일:
  - `offline_live_canary_bundle.py`
  - `offline_gatekeeper_fast_reuse_bundle/*`
  - `offline_live_canary_bundle/*`
  - `april_follow_through_backfill.py`
  - `*.bak`
  - `*.backup`

## 단계별 Gate

각 slice는 아래 순서로 닫는다.

1. 구현: 최대 2~4개 report-only/infra 파일만 이동한다.
2. 코드리뷰: wrapper CLI 전달, public API re-export, monkeypatch 경로, deploy 경로, runtime 권한 누출을 확인한다.
3. 수정보완: 누락 import, wrapper 오류, 테스트/문서 경로 불일치를 즉시 수정한다.
4. 재검증: targeted tests, old/new import smoke, old/new CLI smoke, parser, `git diff --check`를 실행한다.

## Phase 1 Skeleton

이번 변경은 하위 패키지 skeleton과 side-effect-free `__init__.py`만 만든다.

- `automation`
- `scalping`
- `swing`
- `lifecycle`
- `risk`
- `ai`
- `monitoring`
- `infrastructure`

파일 이동, deploy 변경, runtime env 변경은 하지 않는다.
