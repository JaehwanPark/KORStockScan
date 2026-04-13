# Codex 실행 프롬프트 — 스캘핑 HOLDING AI 프롬프트 재설계

이 문서는 더 이상 단독 실행 지시서로 쓰지 않는다.

## 현재 역할

- 북극성 설계 참조 문서: [2026-04-13-scalping-holding-prompt-final-design.md](./2026-04-13-scalping-holding-prompt-final-design.md)
- 실제 구현/실행 지시서: [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)

## 운영 원칙

1. 최종 설계안은 아키텍처 목표를 설명한다.
2. 실제 코딩 작업은 `AI 프롬프트 코딩지시서`의 `P1 -> P2 -> P3 -> P4 -> P5` 순서를 따른다.
3. 문서 파편화를 막기 위해 세부 실행 범위는 `AI 프롬프트 코딩지시서` 안에서만 유지한다.

## 현재 기준

- `작업 5`: WATCHING/HOLDING 프롬프트 물리 분리만 수행
- `작업 6`: HOLDING context 주입
- `작업 8/9`: 감사값 + 공통 feature helper 이식
- `작업 10`: hybrid override 제한 연결
- `작업 11/12`: HOLDING critical + raw 축소 A/B
- `PRESET_TP EXTEND/EXIT`: 위 단계 관측 후 별도 canary

세부 범위는 아래 문서를 본다.
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
