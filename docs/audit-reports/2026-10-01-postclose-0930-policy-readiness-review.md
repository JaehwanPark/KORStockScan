# 2026-09-30 장후 결과 및 2026-10-02 장전 준비 점검

점검 시각: 2026-10-01 16:43 KST. 원천 거래일은 2026-09-30이다. 이 문서는 단계 종료, 분석 유효성, 정책 발행, 실제 PID 소비를 구분한다. 오늘 메인 봇은 기동하지 않는다.

## 계산과 원천

| 경로 | 확인 결과 | 판정 |
| --- | --- | --- |
| 원천 감사 | 140,449 이벤트, 식별된 불량 38행 격리, 현재 hard blocking contract gap 0. 경고 23종은 별도로 보존. | 식별 가능한 불량만 제외한 입력 허용. 전체 무결성 PASS로 확대 해석하지 않음. |
| 기계 주 정책 | `main_machine_policy` 영수증 성공. 정확 KRX 정규장 기존 `ENTER_NOW`의 VWAP 승률 정책이며 미진입 전환의 주 탐색은 아님. | 기존 정책 유지. |
| 기계 전체 평가 | `legacy_machine_report` 2026-10-01 14:36 재계산 성공. 자연 입력 2,409시도, 운영 비교쌍 0, 독립 승계 후보 0. 미진입 전환 0. 변경 판정의 주문 소유자·완료 비용 후 결과가 없어 `machine_operating_population_unbound`. | 탐색 종료와 정책 우위 입증은 다름. 승격 불가. |
| 보조 AI | 자연 판정 6시도의 1·3·5·10분 가격 경로는 정확 `_AL` 완료봉으로 확인됨. 5건은 정확 손절 거리 및 동일 시도의 사전 주문 계획·소유자 결속이 없고, 1건은 자연 응답 transport가 무효. 경제 비교 가능쌍 0. | `source_contract_blocked`, 기존 `contract_v4` 유지. 가격 결손으로 오분류하지 않음. |
| 보조 AI 사전 계획 | 6건 모두 writer·trace 계획 해시 0. 최초 결손은 probe 예약이 필요한 범위 3건, 정확 브로커 예산 2건, 공통 지연 가드 1건. 관측 전용 경로는 예약·계좌 금액·체결을 합성하지 않음. | 과거 원천 복구 불가. 다음 자연 시도에서 정확 계획·소유자·비용 결속 검증 필요. |
| 보조 AI 별도 판단 품질 | 9/29~30 44건 중 고정 10분 진단 모집단 10건(학습 5, holdout 5). 기존 정책 대비 승계 후보 없음. 후보 프롬프트 응답은 중복 시도 오류로 새 완료본이 없음. | 진단 모집단은 주 운영 경제성 비교쌍 0건을 대체하지 않음. |
| 진입 분할·취소·저가주 | `entry_split` 운영 비교는 실주문 2시도의 주문 소유자 등록·완료 비용 결속이 없어 0쌍. `entry_cancel_wait`는 실제 dispatch/parent lineage 미분류로 0쌍. 저가주 2단도 profile별 결속 부족. | 세 family 모두 비용 후 우위 정책 승계 근거 없음. |
| 제출 전 지연 | 운영 절대 경로 기준 `pre_submit_delay` 단계·원천 ledger 영수증 유효. 모형은 `model_not_validated`이므로 기존 정책 유지. | 상대 경로로 점검할 때 나타난 `compact_generation_changed`는 점검 오탐. |
| 기타 활성 단계 | `widget_policy`, `collector_recommendation`, `machine_attribution`, `machine_timing`, `market_weakness`, `research_capacity`, `legacy_policy_approval` 영수증 유효. `episode_policy`와 공동 `research_allocation`은 명시 OFF. 위젯·attribution의 PARTIAL/warning 및 timing 표본 축적은 별도 경제성·자연 증거 결손으로 보존. | 단계 종료를 수익 개선 또는 다음 PID 소비로 승격하지 않음. |

## 최종 인계 결함과 수리

늦은 복구 실행에서 단계 `publication_date=2026-10-01`, `effective_date=2026-10-02`를 9/30 원천의 장전 준비일에 그대로 대입해 `runtime_summary_prepared_effective_date_missing`이 났다. 실제 9/30 원천의 준비일은 10/1이다. 단계의 정책 발행·적용일 계약은 유지하고, 요약 하위 프로세스에만 **원천일의 다음 거래일**을 `prepared_effective_date`로 전달하도록 수리한다. 이 필드는 영수증에도 봉인하고 검사한다. 이후 최신 요약·checklist·strict verifier·controller를 재생성해 이전 02:32 PASS를 새 세대의 근거로 재사용하지 않는다.

10/1 07:35 장전 bootstrap은 당시 선택 릴리스 `90c06298`의 영수증이고, selector는 이후 여러 번 교체되었다. 과거 영수증의 릴리스 해시를 새 릴리스로 고쳐 쓰지 않는다. 10/2 준비는 10/1 장후 원천·정책이 종료된 뒤 **새 선택 릴리스에서 10/2 bootstrap/verify를 생성**하고, 같은 릴리스의 bot PID가 실제 소비하는지 장전에서 확인해야 닫힌다.

첫 복구 재실행은 준비일 결손을 통과했으나, 현재 selector가 바뀌었다는 이유로 10/1 07:35의 원래 장전 세대를 `selected_release_mismatch`로 거부했다. 선택 변경 기록을 역추적하면 `90c06298`은 03:18에 선택되어 장전 생성·검증 시점에 유효했고 07:48에 교체되었다. 과거 선택 백업의 연속성, 시각, 해당 불변 릴리스의 Git HEAD와 코드 청결성을 검증해 **그 날짜의 장전 사실만** 결속하도록 수리한다. 이 경우에도 현재 선택 릴리스의 장전 승인이나 실제 PID 소비는 생기지 않는다. 선택 기록 또는 원본 릴리스 검증이 안 되면 계속 `source_gap`으로 막는다.

두 번째 복구 실행에서 15개 활성 단계 영수증 검사가 모두 통과했고 `summary_handoff=succeeded`, strict `pass`였다. 전체 controller를 별도로 실행해 `done`과 whole-chain strict `pass`를 확인했다. 여기서 controller가 `summary_verified` 파일을 `done`으로 교체하며 요약 단계 영수증의 출력 해시가 낡아지는 추가 결함을 발견했다. 검증된 최종 controller 출력에 한해 요약 영수증을 다시 봉인하고, 다른 입력·코드·전제 결손이 있으면 봉인하지 않도록 수리했다. **최종 릴리스에서 다시 봉인한 뒤 단계 영수증 전체를 재확인해야 이 결함이 닫힌다.**

## 10/2 장전 종료 조건

1. 10/1 장후의 원천 감사, 기계·보조 AI·독립 family terminal, 최신 요약과 strict controller가 정확 10/1 원천일로 닫힌다. `source_gap`은 결손으로 남기며 성공 정책으로 합성하지 않는다.
2. 10/2 정책 bootstrap이 현재 선택 릴리스 SHA, source date, 정책·환경 해시와 일치하고 검증을 통과한다. qualifying candidate가 없으면 마지막 검증 incumbent를 승계한다.
3. 기존 07:55 라우터가 한 메인 봇만 기동하고 실제 PID의 cwd·commit·bootstrap 소비가 일치한다. 이 점검 시각에는 PID 소비를 주장하지 않는다.
