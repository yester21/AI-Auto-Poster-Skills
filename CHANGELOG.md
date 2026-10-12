# Changelog

이 저장소의 모든 주요 변경을 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/),
버전은 [Semantic Versioning](https://semver.org/lang/ko/) 을 따른다.

## [Unreleased]

### 추가

- **aiap-cluster** — 필러·클러스터 초안 묶음 (키워드 의도 겹침 확인 → 묶음 저장 → 초안 → 링크 연결 → 사람 검수)
  - 필러는 글·페이지, 클러스터는 글만. 기존 서비스 페이지를 필러로 지정(`pillarPostId`), `aiap/search-content` 로 찾기, "이 주제의 글" 블록·`[aiap_cluster]` 숏코드 안내
- `lint-content.py` 에 `links_resolved` 게이트 (서버 게이트와 같음)
- KDR SEO 판정 연결: 발행 전 `kdr-seo/analyze` 로 필수 항목 위반(`requiredFailures`)을 고치게 안내 (aiap-write·aiap-publish·aiap-cluster), `aiap_kdr_required` 오류 처리
- `validate.py --plugin` 에 스킬 목록 동기화 검사 (플러그인 `AIAP_Skills::SUMMARIES` ↔ `skills/`)
- README: 워드프레스 **AI 연결 > 스킬** 탭의 설치 프롬프트, 사이트에서 받는 방법(`aiap/get-skill-package`)

### 변경

- 키워드 밀도 기준(0.4~2.5%)을 지움 — 공식 근거 없는 수치. 제목·설명 길이와 온페이지 점수는 SEO 플러그인이 판정
- `create-post` 에 `focusKeyword`·`metaDescription` 을 함께 넘기도록 안내 (켜진 SEO 플러그인에 저장)
- 관리 화면 이름 `AI (MCP)` → `AI 연결` (설정·능력·스킬 탭)

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
