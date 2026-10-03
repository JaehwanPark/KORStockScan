# 장후 승패 결함 보완·통합 배포·다음 기동 준비 — 2026-10-03

Owner: 오늘 checklist `PostcloseOutcomeReadinessClosure1003`.

최신 사용자 지시는 보완·반복 리뷰, 배포·기동·정책 재생성 및 다음 거래일 기동 가능 여부 전체 점검이다. 이전 신규 변경 배포 대기를 해제한다. 기존 OFF/퇴역, provider, 수량, 주문/custody 및 hard safety는 각 owner를 유지한다.

## 실행 순서와 수용

1. **원천 승패**: 기존10분 완료 분봉 CF 안에서 비용 결합 목표/정확 손절의 선도달을 대칭으로 계산한다. 180초는 속도/품질 진단이며 늦은 손절을 결손으로 처리하지 않는다. 원본 frozen 원천은 보존하고 기존 명시적 late-stop 사유만 별도 해석한다. 미도달·동일 봉 동시 도달·진짜 결손은 임의 승패/0 손익으로 치환하지 않는다.
2. **후보 비교**: 결과 미평가 행은 incumbent/candidate 공통 비교 분모에서 제외하고 이유·변경 수를 유지한다. 미평가 기존 ENTER 변경 하나 때문에 후보 전체를 탈락시키지 않는다. native identity, 동일 비교집단, 독립 학습/후단, 지원수, 비용 및 catastrophic safety를 검증한다.
3. **리뷰·재계산**: 기존56개 작업 파일을 snapshot으로 보존한다. producer→비교→publisher→loader를 리뷰·수정하고 표적 pytest/compile/diff/parser 후 보유 원천 격리 재계산으로 선정 결과와 자원 사용을 기록한다.
4. **승인된 배포**: 리뷰된 기존 작업본과 보완을 통합 커밋하고 immutable release를 만든다. 공통 selector와 기존 독립 systemd routes를 release-set lock 안에서 교체하며 백업/롤백을 보존한다. 원천 worker가 진행 중이면 코드/입력을 교체하지 않는다. 기동은 기존 날짜·bootstrap·custody guard를 통과하는 경로로만 실행한다.
5. **장후 재생성**: source10/2를 유지한다. 기존 terminal과 재사용 검증을 보고 영향 stage부터 직접 하류를 순서대로 갱신한다. 실제 publication/effective date, staged/current policy를 대사한다. 새 cancel reconciliation 계약이 발행되면 native controller가 summary→관측 tower→checklist를 생성하며 strict가 tower의 동일 원천·projection을 요구한다. 기존 계약 이전 보고서에 이 요건을 소급하지 않는다. 최신 tower→checklist→strict `--require-summary-handoff`→controller 및 정확10/6 prepared bootstrap/loader를 확인한다. 이전 PASS로 최신 실패를 숨기지 않는다.
6. **적용 범위**: 삼성005930 fixed watch와 그 외 scanner 종목의 실제 machine/auxiliary loader 선택·정책 hash를 확인한다. 연구 partition과 운영 분리 정책을 구별한다. 정식 적격 전용 후보가 없으면 같은 기본정책 승계를 명시하고 분리 적용이라고 보고하지 않는다.

## 결과 경계

배포·서비스 기동·정책 선정·10/6 준비·당일 PREOPEN/실제 PID·자연 주문·실현 성과는 별도로 기록한다. 토요일에 미래 PREOPEN 영수증을 합성하거나 OFF 에피소드를 표본 확보 목적으로 켜지 않는다. 미래 기동을 무조건 보장하는 대신 준비 검증의 통과/결함/미도래 항목과 직접 근거를 남긴다.

임시 증거: `tmp/postclose-outcome-readiness-closure-20261003/`. 기존 계획과 연구 기록의 배포 대기는 그 시점 이력으로 보존하며 본 승인과 결과가 현재 후속 owner다.
