# 2026-04-13 장전 전 원격 프로파일링 / 원격 수집 안정화 AI 코딩 작업지시서

## 목적

본 문서는 `2026-04-13` 장전 전에 확정해야 하는 2개 운영 항목을 코드베이스 관점에서 정리한 별도 작업지시서다.

1. `0-1b 원격 경량 프로파일링`의 수행 방식을 반복 가능한 운영 절차로 고정
2. `fetch_remote_scalping_logs`를 장중 갱신 파일에도 재현 가능하게 보강

핵심 원칙은 아래와 같다.

- 실전 매매 로직은 바꾸지 않는다.
- `원격 관측`과 `본서버 롤아웃`을 섞지 않는다.
- 프로파일링은 `관측`, 원격 fetch 보강은 `운영 안정화`로 분리한다.
- 장전 전 필수 수정은 최소 범위만 반영한다.

## 최종 판정

### 1. `0-1b 원격 경량 프로파일링`

- **장전 전 방식 고정은 필요하다.**
- 다만 **코드베이스 수정은 필수 조건이 아니다.**
- 이유:
  - 현재 목표는 `live 경로`의 hot path 후보를 찾는 것이지, 새 계측 프레임워크를 심는 것이 아니다.
  - 프로파일링용 계측 코드를 급히 넣으면 오히려 latency path 자체를 바꿀 수 있다.
  - 따라서 `2026-04-13` 1차 운영은 `원격 운영자/개발자 수동 실행` 기준으로 가는 편이 맞다.

### 2. `fetch_remote_scalping_logs`

- **장전 전 코드 보강이 필요하다.**
- 이유:
  - 현재 구현은 활성 JSONL을 바로 `tar`로 읽는다.
  - `2026-04-10 16:00 KST` 자동 수집 실패 원인이 이미 `file changed as we read it`로 확인됐다.
  - 이는 운영자 절차 문제가 아니라 구현 방식의 취약점이다.
  - 따라서 `2026-04-13` 전에는 최소한 `remote snapshot copy -> tar` 구조로 바꾸는 것이 맞다.

## P0. 장전 전 필수 수정

## 작업 1. `fetch_remote_scalping_logs` live JSONL 수집 안정화

### 목표

원격 서버의 활성 로그 파일이 장중/장후에도 append 중일 때, 수집이 깨지지 않도록 한다.

### 현재 문제

- 파일: `src/engine/fetch_remote_scalping_logs.py`
- 현재 방식:
  - 원격 live 파일 경로를 그대로 `tar -czf -`에 전달
- 실제 실패 이력:
  - `pipeline_events_2026-04-10.jsonl`이 읽는 중 변경되어 종료

### 수정 원칙

1. 원격 live 파일을 직접 tar로 읽지 않는다.
2. 먼저 원격 임시 디렉터리에 `cp` 또는 `cat > snapshot` 방식으로 사본을 만든다.
3. 그 사본만 tar로 묶는다.
4. 작업 종료 시 원격 임시 디렉터리는 정리한다.

### 권장 구현 방식

#### 원격 단계

- `mktemp -d`로 임시 디렉터리 생성
- 필수 파일:
  - `logs/sniper_state_handlers_info.log`
  - `logs/sniper_execution_receipts_info.log`
  - `data/pipeline_events/pipeline_events_<date>.jsonl`
  - `data/post_sell/post_sell_candidates_<date>.jsonl`
  - `data/post_sell/post_sell_evaluations_<date>.jsonl`
- 각 파일을 아래 둘 중 하나로 사본화
  - `cp -p`
  - `cat "$src" > "$tmp/$name"`
- 이후 `tmp` 내부 사본만 `tar -czf -`
- `trap 'rm -rf "$tmpdir"' EXIT`로 정리

#### 로컬 단계

- 기존처럼 `tmp/remote_<date>/remote_scalping_<date>.tar.gz`로 저장
- 해제 경로도 기존 유지

### 필수 예외 처리

1. 필수 파일 누락은 기존처럼 실패로 본다
2. optional snapshot JSON은 있으면 포함, 없으면 계속 진행
3. live copy 단계 실패 시 어떤 파일에서 깨졌는지 stderr에 남긴다

### 완료 기준

- 장중 append 중인 `pipeline_events`에도 수집이 종료되지 않는다
- `tmp/remote_<date>/`에 기존과 같은 산출물이 남는다
- 자동 cron과 수동 실행이 같은 경로를 사용한다

### 권장 테스트

1. 단위 테스트
   - `src/tests/test_fetch_remote_scalping_logs.py`
   - `_build_remote_tar_command_with_live_snapshot()` 또는 동등 helper의 명령문 검증
2. 수동 검증
   - 원격에서 대상 JSONL에 append가 발생하는 상황에서 표준 커맨드 1회 실행
   - `--include-snapshots-if-exist` 포함 경로 재확인

---

## P1. 장전 전 있으면 좋은 보강

## 작업 2. `snapshot-only fallback` 옵션 추가

### 목표

live JSONL 사본화가 다시 실패해도, 최소한 장후 판단에 필요한 snapshot JSON은 반드시 회수한다.

### 권장 형태

- CLI 옵션 예시:
  - `--snapshot-only-on-live-failure`
- 동작:
  1. 기본 수집 시도
  2. live JSONL 사본화 실패 시 warning 출력
  3. `trade_review`, `performance_tuning`, `post_sell_feedback` snapshot만 다시 묶어 회수

### 주의

- 이것은 `필수 로그 수집 성공`과 같은 의미가 아니다.
- 결과 상태를 아래처럼 구분해서 남긴다.
  - `status=ok`
  - `status=partial_snapshot_only`
  - `status=failed`

### 완료 기준

- 원격 live file race가 재발해도 장후 의사결정용 snapshot JSON은 회수 가능

---

## P2. `0-1b 원격 경량 프로파일링` 방식 고정

## 판정

- `2026-04-13` 장전 전 **반드시 코드로 구현할 항목은 아니다.**
- 1차 운영은 아래처럼 `수동 표준 절차`로 고정한다.

### 수행 주체

1. 트리거 판정:
   - 시스템운영자
2. 실제 실행:
   - 원격 서버 접근 권한이 있는 개발자 또는 운영자
   - 필요 시 Codex가 명령/로그 정리 지원
3. 장후 해석:
   - 운영자 + 전략 검토 담당

### 수행 방식

1. 패키지 설치 없이 진행
2. 원격 `songstockscan`에서만 수행
3. `08:20~08:35`, `10:20~10:35`, `13:20~13:35` 3개 고정 윈도우 사용
4. 우선순위:
   - OS 기본 sampling / 프로세스 상태 확인
   - 이미 코드에 있는 timing/log와 pipeline event 상관관계 확인
   - 필요 시 매우 얇은 내장 timing instrumentation 추가 여부는 `4/13 장후`에 재판정

### 1차 운영 명령 예시

아래는 예시이며, 실제 PID/세션명은 원격 상태에 맞게 고정한다.

```bash
ssh windy80xyt@songstockscan.ddns.net \
  "ps -ef | grep -E 'bot_main|gunicorn' | grep -v grep"
```

```bash
ssh windy80xyt@songstockscan.ddns.net \
  "top -b -n 1 -H -p <PID>"
```

```bash
ssh windy80xyt@songstockscan.ddns.net \
  "ps -L -p <PID> -o pid,tid,pcpu,pmem,etime,cmd"
```

### 자동 실행 경로

- 장전/장중 baseline 수집은 로컬 표준 경로로 고정한다.
  - `PYTHONPATH=. .venv/bin/python -m src.engine.collect_remote_latency_baseline --date 2026-04-13 --window preopen`
- cron wrapper:
  - `deploy/run_remote_latency_baseline.sh preopen`
  - `deploy/run_remote_latency_baseline.sh midmorning`
  - `deploy/run_remote_latency_baseline.sh afternoon`
- 관련 운영 cron 설치:
  - `deploy/install_stage2_ops_cron.sh`
- 함께 설치되는 운영 잡:
  - `10:00`, `12:00` `run_monitor_snapshot`
  - `16:00` `fetch_remote_scalping_logs --include-snapshots-if-exist --snapshot-only-on-live-failure`
- 결과 산출물:
  - `tmp/remote_latency_baseline/<date>/...json|md`
  - `logs/remote_latency_baseline.log`
  - `logs/remote_latency_baseline_cron.log`

### 장중 추가 실행 트리거

아래 중 하나라도 충족하면 정해진 시간 외 추가 1회를 허용한다.

1. `quote_stale=False latency_block`가 장중 초반에 반복 누적된다
2. `budget_pass -> submitted` 전환이 거의 없는데 `budget_pass`는 계속 쌓인다
3. 운영자가 `fresh quote인데 DANGER` 사례를 대표 표본으로 2~3건 이상 확보했다

### 장후 산출물

아래 3개를 남기면 충분하다.

1. hot path 후보 1~3개
2. 해당 후보가 관측된 시간대
3. `pipeline_events / performance_tuning snapshot`과의 대응 관계

## 이번 단계에서 하지 말 것

- `py-spy`, `pyinstrument` 같은 신규 패키지 설치
- live path 전반에 대형 instrumentation 코드 삽입
- 본서버에 동일 계측 강제 적용
- 프로파일링 결과만으로 즉시 실전 로직 완화

## 2026-04-13 장전 기준 최종 액션

1. **필수**
   - `fetch_remote_scalping_logs`를 live snapshot copy 방식으로 보강
2. **권장**
   - snapshot-only fallback 옵션 추가
3. **운영 절차로 처리**
   - `0-1b 원격 경량 프로파일링`은 `collect_remote_latency_baseline` + cron wrapper 기준으로 먼저 수행
4. **장후 재판정**
   - 수동 프로파일링만으로 hot path 후보 설명이 부족할 때만 경량 instrumentation 코드 추가 여부를 재검토

## shadow canary 장초반 점검 명령

- `src/engine/check_watching_prompt_75_shadow_canary.py`를 사용한다.
- 목적:
  - `tmux bot` / `bot_main.py` / shadow env 준비상태 확인
  - 장초반 `pipeline_events` 파일 생성 및 갱신 확인
  - 오전/장후 `remote fetch + shadow report` 자동 연결

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary \
  --date 2026-04-13 \
  --phase open_check
```

- `open_check`는 장초반 수집 readiness를 보는 용도다.
- `midmorning`, `postclose`는 `fetch_remote_scalping_logs`와 shadow report까지 같이 수행한다.
