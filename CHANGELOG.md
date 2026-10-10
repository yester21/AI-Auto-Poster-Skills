# Changelog

이 저장소의 모든 주요 변경을 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/),
버전은 [Semantic Versioning](https://semver.org/lang/ko/) 을 따른다.

## [0.1.0] - 2026-10-10

AI 오토포스터 0.1(WordPress Abilities API 기반 MCP 능력 구조)에 맞춘 첫 개발판.

### 추가

- **aiap-write** — 한국어 SEO 글쓰기
  - 본문 구조 규칙, H 태그 규칙
  - S1(발명·템플릿 잔여어·번역투) / S2(AI 상투어·채우기용 구조) 검출
  - 자연도 등급 A~D 와 발행 게이트
  - 의미 보존 6항, 변경률 가드
  - `references/fabrication-guard.md` — 실제 사고 사례 기반 발명 금지 범주
  - `examples/before-1.md` / `after-1.md` — 실제 측정값이 있는 윤문 예시
- **aiap-publish** — 발행과 게이트
  - draft → 검사 → 발행 흐름
  - `aiap_gate_failed` 원인별 조치 표
  - 예약 발행(WordPress 네이티브 `future`)
  - `scripts/lint-content.py` — 서버 게이트의 로컬 사본 (exit 0/1)
- **aiap-research** — 키워드 발굴과 실측 KD, KD 산출 근거 공개
- `scripts/validate.py` — 매니페스트·스킬 구조·**패턴 동기화** 검증
- GitHub Actions — 검증 + 픽스처 계약(pass 는 exit 0, fail 은 exit 1)

### 설계 노트

- 플러그인이 AI API 키를 갖지 않으므로 스킬에는 AI 자격증명 관련 내용이 없다.
  지능은 이 스킬을 읽는 에이전트가 담당한다.
- 서버가 발행 시점에 게이트를 재검사하므로 스킬을 건너뛰어도 발행되지 않는다.
  스킬과 서버가 다르면 **서버가 이긴다.**
- 패턴 동기화는 수동이다. `validate.py --plugin` 이 불일치를 잡는다.

### 알려진 한계

- KD 는 공개된 휴리스틱이며 도메인 권위·백링크를 반영하지 않는다.
- 총 검색 결과 수를 주지 않는 SERP 공급자(Serper)는 규모 점수에 중간값을 쓴다.
- `validate.py` 의 `--plugin` 검사는 플러그인 저장소 경로가 필요하다 (CI 에서는 생략).
