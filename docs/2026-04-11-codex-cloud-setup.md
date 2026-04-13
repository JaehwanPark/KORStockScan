# KORStockScan Codex Cloud 셋업 가이드

기준일: `2026-04-11`

## 판정

저장소 측 준비는 완료 상태다.  
`Codex Cloud` 워크스페이스/환경에서 1회 연결만 하면 바로 작업 가능하다.

## 근거

- 프로젝트 지시 파일: `AGENTS.md` (Codex가 자동 로드)
- Codex 작업지시 자동화: `.github/workflows/build_codex_daily_workorder.yml`
- 클라우드 재현 설치 스크립트:
  - `deploy/codex_cloud_setup.sh`
  - `deploy/codex_cloud_maintenance.sh`

## 다음 액션

1. ChatGPT에서 GitHub 앱 연결
   - `Settings -> Apps -> GitHub`
   - KORStockScan 저장소 접근 권한 허용
2. (Business/Enterprise) Codex Cloud 활성화 확인
   - 워크스페이스 관리자에서 `Allow members to use Codex cloud` 활성화
3. Codex에서 Cloud Environment 생성
   - Repository: `KORStockScan`
   - Setup script:
     ```bash
     bash deploy/codex_cloud_setup.sh
     ```
   - Maintenance script:
     ```bash
     bash deploy/codex_cloud_maintenance.sh
     ```
4. 에이전트 실행 전 검증 커맨드 등록(권장)
   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.build_codex_daily_workorder --help
   ```
5. 작업 시작
   - Codex는 시작 시 `AGENTS.md`를 자동으로 읽는다.
   - 문서/체크리스트 수정 시 기존 원칙대로 `문서 -> GitHub Project -> Calendar` 체인을 유지한다.

## 운영 메모

- Cloud setup 단계는 인터넷 사용이 가능하므로 의존성 설치는 위 setup script로 고정한다.
- Agent 단계 인터넷은 기본 비활성일 수 있으니, 외부 조회가 필요한 작업만 워크스페이스 정책에 맞춰 허용한다.
- 환경 변경(패키지 추가/업그레이드)이 필요하면 기존 운영 원칙대로 사전 승인 후 반영한다.
