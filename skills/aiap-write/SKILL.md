---
name: aiap-write
description: "Write Korean SEO blog posts for WordPress through the AI Auto Poster plugin. Use when asked to write, draft, or generate a Korean blog post/article for a WordPress site, to write SEO content from a keyword, to research a keyword and write about it, or when the user says 오토포스터, 글 써줘, 블로그 글 작성, SEO 글, 키워드로 글, 포스팅 써줘, or wants content published through WordPress MCP abilities. Covers Korean SEO structure, H-tag rules, AI-slop and translationese removal, and pre-publish verification. The plugin's server-side gate re-checks everything, so this skill's rules mirror it exactly."
license: MIT
metadata:
  author: 김대리닷넷
  version: "0.1.0"
allowed-tools: Read Write Edit Grep Glob AskUserQuestion
---

# aiap-write: 한국어 SEO 글쓰기

WordPress 의 **AI 오토포스터** 능력(`aiap/*`)을 통해 한국어 SEO 글을 쓰고 발행한다.

## 무엇보다 먼저 — 서버가 진실이다

이 스킬의 규칙은 **서버가 같은 내용을 들고 있다.** `aiap/get-writing-guide` 를 호출하면
서버측 규칙을 그대로 받는다. 그리고 발행 시점에 서버가 **독립적으로 다시 검사**한다.

```
이 스킬 (지식)  ──┐
                  ├──→  같은 규칙
aiap/get-writing-guide ──┘
                          ↓
              aiap/create-post / aiap/publish-post
                          ↓
                  AIAP_Quality::gate()  ← 우회 불가
```

즉 **이 스킬의 규칙을 건너뛰어도 발행되지 않는다.** 규칙이 바뀌었을 가능성이 있으면
먼저 `aiap/get-writing-guide` 를 호출해 서버 값을 확인하라. 스킬과 서버가 다르면
**서버가 이긴다.**

## 능력 확인

작업 전에 `aiap/list-ability-status` 로 사용 가능한 능력을 확인한다.

| 능력 | 용도 |
|---|---|
| `aiap/get-writing-guide` | 규칙 전문 (먼저 호출) |
| `aiap/list-ability-status` | 능력 가용성 진단 |
| `aiap/analyze-keyword` | 키워드 실측 KD → 권장 글자수 |
| `aiap/discover-keywords` | 키워드 발굴 (구글 자동완성) |
| `aiap/check-content-quality` | **발행 전 검사 (반복 호출)** |
| `aiap/create-post` | 글 등록 (draft 권장) |
| `aiap/update-post` | 초안 수정 |
| `aiap/publish-post` | 공개/예약 발행 (게이트 재검사) |
| `aiap/set-seo-meta` | 포커스 키워드·메타 설명 |

빠른 경로가 아닌 능력은 `mcp-adapter-execute-ability` 에
`ability_name: "aiap/..."` 로 호출한다.

> `aiap/list-ability-status` 가 비어 있거나 오류면 서버에 **MCP Adapter** 또는
> **Abilities API**(WP 6.9+)가 없는 것이다. 사이트 관리자에게
> `관리자 > AI 오토포스터 > AI (MCP)` 화면을 확인하도록 안내하라. 추측으로 진행하지 마라.

## 작업 흐름

### 1. 규칙과 키워드 확보

```
aiap/get-writing-guide
aiap/analyze-keyword { keyword: "<메인 키워드>" }
```

`analyze-keyword` 는 **실측값만** 반환한다. SERP 미설정이면 오류를 반환하며 AI 추정으로
대체하지 않는다. 오류가 나면 사용자에게 SERP 설정을 요청하고, **KD 를 지어내지 마라.**

`target_chars` 가 응답에 포함된다: KD<35 → 1,200자 · KD<65 → 1,800자 · 그 외 2,600자

### 2. 목차 구성

H2 를 3~12개. 순서는 검색 의도 순으로: 정보 → 방법 → 비교 → 주의 → 결론.

### 3. 초안 작성

도입부 2~3문단 → H2 본문 → 짧은 결론. 자세한 규칙은 아래와 `references/` 참조.

### 4. 셀프 검사 (반복)

```
aiap/check-content-quality { content: "<HTML>", title: "<제목>", keyword: "<키워드>" }
```

응답의 `grade` 가 **A 또는 B** 가 될 때까지 4단계와 5단계를 반복한다.
`failures` 배열이 비어 있어야 `passed: true` 다.

### 5. 발행

초안을 먼저 만들고 검사하는 흐름을 권장한다.

```
aiap/create-post { title, content, status: "draft" }
aiap/check-content-quality { ... }          # 등급 확인
aiap/publish-post { postId }                # 게이트 재검사 후 발행
```

예약 발행은 `status: "future"` + `date` (사이트 시간 `Y-m-d H:i`).

**게이트가 거부하면 우회하지 마라.** `failures` 를 읽고 본문을 고친 뒤 다시 시도한다.
`status` 를 `draft` 로 낮춰 회피하는 것은 사용자가 명시적으로 요청했을 때만 한다.

## 본문 구조 규칙

| 항목 | 기준 |
|---|---|
| 도입부 | 2~3문단, 첫 200자 안에 메인 키워드 1회 |
| H2 | 3~12개 |
| 각 H2 아래 | 첫 문단 3문장 이상 |
| 결론 | 마지막 H2 뒤 짧은 결론 |
| 리스트/표 | 1개 이상 — **단, 점수 채우기용 금지** |
| 내부 링크 | 1개 이상 |
| 외부 링크 | 최대 3개, **실제 확인한 URL만** |
| 키워드 밀도 | 0.4~2.5% |

## H 태그 규칙

| 규칙 | 값 |
|---|---|
| **H1** | **본문에 쓰지 않는다.** 테마가 글 제목을 H1 으로 출력한다 |
| H2 | 본문 섹션의 유일한 최상위 |
| H3 | 반드시 H2 하위에 |
| 키워드 | H2 중 **최소 1개**에 포함 |
| H2 길이 | 30자 이내, 마침표 없음 |

## S1 — 하나라도 있으면 발행 거부

`references/fabrication-guard.md` 와 `references/korean-slop-patterns.md` 참조.

### 발명 금지 (factuality)

- `example.com` · `example.org` · `placeholder` · `yourdomain` 류 URL **절대 금지**
- "URL 예시", "장문 URL 예시 링크", "여기에 링크" 같은 **앵커 텍스트 금지**
- 확인하지 않은 통계·출처·인용을 만들지 않는다
- **URL 을 검증할 수 없으면 링크를 빼고 문장을 다시 쓴다.** 링크를 지어내지 마라

> 실제 사고 사례: 한 사이트에서 `https://example.com/reports/2026/...-appendix`
> 라는 더미 링크가 앵커 텍스트 "장문 URL 예시 링크" 와 함께 **실서비스에 발행**됐다.
> "외부 링크를 넣어라"는 요구를 리터럴 플레이스홀더로 채운 결과다.

### 템플릿 잔여어

`샘플`, `TODO`, `FIXME`, `여기에 입력`, `{{ }}`, `${ }` — 플레이스홀더를 실제 내용으로
바꾸거나 문장을 삭제한다. 한국어에서는 조사가 붙으므로 `샘플에서`·`샘플을` 도 모두 해당한다.

### 번역투

| 패턴 | 고칠 방향 |
|---|---|
| `~에 대해(서)` | 목적격 조사로 — "물가에 대해 설명" → "물가를 설명" |
| `~를 통해(서)` | "~로" — "링크를 통해 확인" → "링크에서 확인" |
| `~에 의해` | 능동으로 — "전문가에 의해 검증" → "전문가가 검증" |
| `되어진다` / `되어집니다` | "~된다" / "~집니다" |
| `가지고 있다` / `가지고 있습니다` | "있다" / "있습니다" |
| `라고 할 수 있다` / `라고 할 수 있습니다` | 단정하거나 삭제 |

**합니다체로 쓸 때 평서형만 보고 넘기지 마라.** 이 플러그인의 게이트는
`되어집니다`·`가지고 있습니다` 같은 활용형도 잡는다.

## S2 — 3회 이상 반복되면 등급 하락

- AI 상투 어휘: `결론적으로`, `다양한 측면에서`, `매우 중요합니다`, `핵심적입니다`,
  `효과적입니다`, `지속가능한`, `혁신적입니다`, `주목할 만하다`, `시사하는 바가 크다`
- 채우기용 구조: 항목 3개 미만이거나 **모든 항목이 한 줄짜리**인 리스트

## 자연도 등급

| 등급 | 조건 | 발행 |
|---|---|---|
| **A** | S1 0건 + S2 ≤2 | ✅ |
| **B** | S1 ≤2 + S2 ≤5 | ✅ |
| C | S1 ≤4 + S2 ≤9 | ❌ 추가 윤문 |
| D | 그 외 | ❌ |

## 발행 게이트

| 게이트 | 기준 |
|---|---|
| `no_s1` | S1 패턴 0건 |
| `links_verified` | `example.com`·`placeholder` 링크 0건 |
| `h2_min` | H2 3개 이상 |
| `no_h1` | 본문에 H1 0건 |
| `h2_keyword` | 키워드 포함 H2 1개 이상 |
| `length` | 권장 글자수의 70% 이상 |
| `naturalness` | 등급 A 또는 B |

## 윤문할 때 — 의미 보존 6항

원문을 다듬을 때 **반드시** 아래를 지킨다. 하나라도 어기면 윤문이 아니라 훼손이다.

1. 수치·날짜·인명·기관명·제품명이 모두 보존되었는가
2. 인과관계 방향이 뒤바뀌지 않았는가
3. `있다/없다`, `가능/불가능` 이 반전되지 않았는가
4. 직접 인용이 그대로인가
5. 핵심 주장·결론이 변경되지 않았는가
6. 격식체/반말이 일관되게 유지되었는가

**변경률 가드**: 어절 기준 변경률이 50% 를 넘으면 출력하지 말고 사용자에게 확인을
요청한다. 30~50% 면 "변경률이 큼"을 알린다.

## 출력 형식

```markdown
## 분석
감지: S1 N건 / S2 M건 · 등급 X

## 본문
<HTML>
```

발행까지 요청받았다면 마지막에 결과를 보고한다.

```
발행 완료: <제목>
- postId: N / 상태: publish
- 게이트: 등급 A (S1 0 / S2 1)
- 링크: example.com 0건
```

## 하지 말 것

- `example.com` 류 URL 을 만들지 마라. 링크가 필요하면 **실제로 접근해 확인**하라.
- KD·검색량·순위를 **추측으로 채우지 마라.** `analyze-keyword` 가 오류면 사용자에게 알려라.
- 게이트 실패를 `status` 변경으로 회피하지 마라.
- H1 을 쓰지 마라.
- 리스트·표를 점수 채우기용으로 만들지 마라.
- 서버와 스킬이 다르면 **서버 값을 따르라.**

## 참고 문서

| 파일 | 내용 |
|---|---|
| `references/seo-structure.md` | 본문 구조·밀도·링크 상세 |
| `references/heading-rules.md` | H 태그 규칙과 예시 |
| `references/fabrication-guard.md` | 발명 금지 — 실제 사고 사례 포함 |
| `references/korean-slop-patterns.md` | 번역투·상투어 전체 목록과 교정 |
| `examples/before-1.md` / `after-1.md` | 실제 윤문 예시 |
