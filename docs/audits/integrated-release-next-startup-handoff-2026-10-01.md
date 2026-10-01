# 통합 릴리스와 다음 기동 인계: 2026-10-01

## 승인과 적용 경계

사용자가 전체 작업트리 통합 배포 및 10/2 Main·Widget·Episode 정상 기동 준비를 요청했다. 기계·보조 장후 보완 작업과 미래일 정책 준비 문서를 함께 커밋하고 불변 릴리스에 반영한다. 오늘 Main은 꺼 둔다. 기존 정확일자 정책, 격리 profile, 수량·custody·broker/hard safety는 유지한다.

장중 기존 정책과 새 장후 계산 코드는 다른 적용 경계를 갖는다. 새 기계/보조 선택 로직은 10/2 원천의 장후 계산부터 실행된다. 신규 공통 모듈 `src/engine/scalping/postclose_entry_validation.py`를 반드시 릴리스에 포함한다.

## 배포 전 검증과 보완

- 작업본의 10/2 Main 정책 원천 영수증 2개와 닫힌 9/30 controller 검증을 통과했다. 장전 manifest 생성의 환경값·selected families는 기존 준비본과 같다.
- Widget 로더는 작업본과 기존 소비 릴리스에서 동일한 3종목·4세션·정책 hash를 읽는다.
- Episode 로더는 동일 hash의 58 ready와 기존 격리 3개를 유지한다.
- 최초 통합 검증은 895 passed / 3 failed였다. 실패 3개는 기존 선택 릴리스에서도 재현된 구 wrapper 시험 계약이다. 단계 worker fixture·동일 원천일·EOD fail-closed 기대를 현재 계약에 맞췄다. 기본 날짜 resolver의 dependency banner를 전달하지 않도록 마지막 출력행의 ISO date를 검사하고 dispatcher 회귀 2개를 추가했다. 새 매매 판단이나 API 요청은 추가하지 않는다.
- 구 릴리스 `machine_group` 분석 서비스가 실행 중이어서 전환 전에 기존 systemd stop으로 정리했다. 원래 timer와 실패/중단 증거는 보존하며 해당 작업을 성공으로 바꾸지 않는다.

## 통합 전환 완료 조건

불변 릴리스의 표적 회귀·clean source를 확인한 뒤 공통 selector와 Widget/Episode 및 관련 collector·postclose service pin을 같은 릴리스로 맞춘다. timer/arguments/기존 policy path와 hash pin은 그대로 유지한다. active Widget/collector만 기존 상태를 보존한 채 정상 서비스 재기동한다. Episode는 자신의 예약에서 기동하고 퇴역 Samsung 신규 진입은 복원하지 않는다. 선택/서비스 변경은 release-set lock 안에서 수행하며 이전 선택·drop-in을 보관한다.

새 릴리스 선택 뒤 `next_preopen_readiness --prepare --source-date 2026-09-30 --target-date 2026-10-02`와 `--verify --target-date 2026-10-02`를 해당 불변 릴리스에서 실행한다. 구 준비본을 재라벨링하지 않는다. 실제 10/2 PREOPEN과 Main PID는 미래 수용이며 준비 PASS로 대신하지 않는다.

## 10/2 장후 완료 뒤의 다음 기동

1. 10/2 exact source의 기계·보조·Widget·Episode 단계 영수증, 비용/검증/선정 또는 정당한 carry를 확인한다. 의미적으로 후보가 탈락한 carry와 계산/원천 실패를 구분한다.
2. 동일 generation의 summary → strict verifier `--require-summary-handoff` → 전체 controller `done` → finalization terminal을 확인한다. 중간 stage 성공이나 exit 0만으로 종결하지 않는다.
3. 선택된 불변 릴리스의 finalizer가 다음 거래일 격리 장전 준비본을 생성한다. 필요 시 그 릴리스에서 `next_preopen_readiness --prepare --source-date 2026-10-02` 및 산출 target의 `--verify`를 실행한다. 계산 기준은 다음 KRX 거래일이며 현재 repository calendar 산출은 **2026-10-06**이다.
4. 준비 후 코드 릴리스를 바꾸면 선택·source hash가 달라지므로 새 릴리스에서 준비를 다시 생성·검증한다. 기존 prepared receipt의 commit/hash를 수정하지 않는다.
5. 다음 거래일 기존 07:32 custody → 07:35 PREOPEN → 07:55 Main start 예약을 사용한다. PREOPEN이 dated machine/auxiliary를 검증·활성화하고 운영 bootstrap을 생성한다. Widget는 날짜 전환 정책 로딩, Episode는 각 profile preflight/live timer를 따른다.
6. 같은 코드 릴리스에 정책만 갱신된 정상 흐름은 매일 commit·배포나 Main 수동 기동을 요구하지 않는다. active Widget의 정책 날짜 전환을 검증한다. 정책 결손·stale·CAS·custody/broker guard 실패는 원인을 복구하고 해당 owner부터 재검증하며 우회하지 않는다.

실제 PID 정책 소비·주문·체결·terminal·비용 후 성과는 별도 수용이다. 외부 Project/Calendar sync는 실행하지 않는다.
