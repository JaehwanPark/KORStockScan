# 완료 연구 복제본·테스트 임시자료 정리 — 2026-10-18

사용자의 "연구가 종료되어 불필요한 데이터는 삭제해줘" 지시로 실행했다. 현재 선택본은 `quantity-broker-cost-monitor-20261018-900234d79`이며 이전 `e12256dec`와 함께 보존했다. 앞선 대화의 c5a 선택을 현행으로 간주하지 않았다. 원 코드·작업본·실제 원장·AI 원응답·최종 연구 결과·실패 영수증과10/19 정책 준비본은 삭제 대상에서 제외했다.

## 확인된 삭제와 공간

| 구분 | 확인된 삭제 파일 | 논리 바이트 |
| --- | ---: | ---: |
| 완료 격리 검증의 정책 중복본 |1,740|4,353,496,442|
| 종료된 pytest 합성 자료 |4,766|646,863,862|
| 합계 |6,506|5,000,360,304|

정책 중복본은 `tmp/nonfixed-quote-deployment-20261017/{isolated-policy,first-probe-policy}/{sources,generations}`에서 같은 상대경로의 canonical 원본과 전체 SHA-256·크기가 일치하는 파일만 삭제했다. 원본1,740개는 삭제 후 다시 해시 검증했다. 후보·current·미일치/고유 정책 사본은 남겼다. 테스트 자료는 실제 정책 원천과 구분되는 종료된 `pytest-N` 작업파일이며 최근 파일·심볼릭 링크·lock·직접 참조/열린 파일을 제외했다. 디렉터리 전체 재귀 삭제는 하지 않았다.

확인된 삭제 파일의 할당량은4,879,048,704바이트다. 감사·계획·journal 저장량을 차감한 순회수는 약4.86GB다. 최종 제어파일 여유분을 포함한 [정산](../../data/report/research_storage_cleanup/2026-10-18/final-accounting.json)을 별도로 남긴다. 파일시스템 사용률은 최초87%에서 최종 관측80%, 가용 공간 약39GiB였다. 아래의 별도 임시 정리가 겹쳤으므로 이 사용률 변화 전체를 이번 작업의 회수량으로 합산하지 않는다.

## 검토·중단·보완

- 현재/이전 릴리스, Git 작업본, `/proc` cwd·cmdline·maps·FD/inode, systemd·cron·외부 symlink와 native 정책 JSON/env 참조를 검사했다. 환경값·인증값은 출력하지 않았다. 일반 권한으로 읽히지 않는 과거 metadata 때문에 첫 참조 검사는 실패로 보존했고, 특권의 읽기 전용 census로 보완한 뒤 진행했다.
- 최신 선택본의 기존 release-set 및 publisher 잠금 안에서 원천·selector·준비본·수동 제외·workspace HEAD/index/기존 변경 파일의 해시를 대조했다. 각 파일의 inode·mtime·ctime·형식·원본 SHA를 재확인하고 삭제 의도와 실제 완료를 구분해 journal에 기록했다.
- 첫 삭제 시도는 사전 검토 후 일부 공용 pytest 파일이 별도로 사라져 중단됐다. 확인된5,376개 삭제와 원 실패를 보존했다. 다시 census/해시 검토 후 잔여1,130개를 삭제했다. 별도로 없어진10,546개/2,449,802,872바이트는 작업의 삭제 실적에서 제외했다. 사라진 파일의 재시도·동일 내용으로 교체된 파일·실제 원본 삭제 경계를 보완해 추가3회귀를 통과했다. 원6개와 합쳐9개 표적 검증 및 compile을 마쳤다.
- 문서 마감 중 별도 [수량 연구 정리 기록](initial-quantity-research-storage-cleanup-2026-10-18.md)의 생성과 기존10/18 owner 갱신도 확인했다. 그 작업의 삭제량·새 문서·체크리스트 내용을 보존하고 이 작업의 직접 삭제량에 합치지 않았다. 외부 작업의 릴리스/작업본 등록 목록 변경도 별도 관측으로 기록했다. 현재900/이전e122는 유지되며 이 작업의 전체 릴리스/작업본 삭제는0건이다. 공유 감사 폴더 전체 비용을 차감한 공간 계측은 이 작업의 기록 비용에 대한 보수적 상한이다.

[원 계획과 첫 시도](../../data/report/research_storage_cleanup/2026-10-18/verified-read-census/plan.json), [첫 시도 실제 삭제 journal](../../data/report/research_storage_cleanup/2026-10-18/verified-read-census/deletion-journal.jsonl), [중단·외부 결손 구분](../../data/report/research_storage_cleanup/2026-10-18/verified-read-census/partial-result.json), [재검토 후 잔여 삭제](../../data/report/research_storage_cleanup/2026-10-18/resume-after-external-expiry/result.json)을 보존했다. 고유 연구 결과를 압축하거나 삭제하지 않았으므로 archive 생성량은0이다.

## 마지막 소비자 검증

[최종 검증](../../data/report/research_storage_cleanup/2026-10-18/final-verification.json)은 `cleanup_and_readiness_verified`다. 삭제 전 정확 source10/16→target10/19 준비 세대를 확인했고, 삭제 후 실제 `900234d791b0bf31797cd4e823d0ae40296f790b`의 `current_full_contract` 검증은 PASS/findings0이다. release-set 및 cron8개 경로도 PASS다. 원10/19 체크리스트·strict/controller·준비본·기계/보조 포인터와 기존 미커밋 변경은 이 검증 시점까지 해시가 같았다. 이후 문서 마감은 이 감사와10/18 체크리스트에 한정하고10/19 봉인은 유지한다.

외부 작업의 등록 목록 변경을 관측한 뒤 release-set 잠금 안에서 [전체 준비 계약을 다시 검증](../../data/report/research_storage_cleanup/2026-10-18/post-concurrent-worktree-full-verification.json)해 PASS/findings0을 확인했다. 원 선택900/이전e122와 Main 정상 정지 상태를 유지했다. 문서 마감 뒤 세대 검사도 PASS다.

Main은 일요일 정상 정지 상태다. 재시작·provider·주문 호출은0회이며 실제 다음 영업일 PREOPEN/PID 소비·자연 주문/체결·경제 성과를 주장하지 않는다. 실제 AI 원장·응답·재현에 필요한 최종 연구 결과와 canonical 시장/거래·custody 원천은 보존했다. 운영 코드 변경이나 추가 배포, 원장 전체 재생성은 하지 않았다.
