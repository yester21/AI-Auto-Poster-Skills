---
name: aiap-publish
description: "Publish a Korean post to WordPress through the AI Auto Poster abilities, or check content against the server-side publish gate before publishing. Use when asked to publish, post, schedule, or verify a blog post on WordPress via AI Auto Poster / aiap abilities, when a publish attempt returned aiap_gate_failed, when told the gate rejected the content, or when the user says 발행해줘, 포스팅 올려줘, 예약 발행, 게이트 통과, or asks why publishing failed. Covers the draft-then-publish flow, gate failure handling, and scheduled publishing."
license: MIT
metadata:
  author: 김대리닷넷
  version: "0.1.0"
allowed-tools: Read Bash
---

# aiap-publish: 발행과 게이트

글을 발행하고, 발행 게이트가 거부했을 때 원인을 해결한다.

## 핵심 — 게이트는 우회할 수 없다

```
aiap/check-content-quality   ← 미리 검사 (부작용 없음)
        ↓
aiap/create-post             ← 등록. publish/future 면 게이트 통과 필요
aiap/publish-post            ← 저장된 본문으로 게이트 재검사 후 발행
```

`publish` / `future` 는 **서버가 저장된 본문으로 다시 검사**한다. 스킬에서
검사를 건너뛰고 발행을 시도해도 거부된다. `status` 를 `draft` 로 낮추는 것 외에
우회로는 없고, 그것은 사용자가 명시적으로 요청했을 때만 한다.

## 표준 흐름

### 1. 초안 등록

```
aiap/create-post {
  title: "...",
  content: "<HTML>",
  status: "draft",
  focusKeyword: "<포커스 키워드>",
  metaDescription: "<메타 설명>"
}
→ { postId: 123, status: "draft", editLink: "...", seo: { provider: "kdr", updated: [...], skipped: [] } }
```

**항상 draft 로 먼저 만들라.** 초안 상태에서는 게이트가 발행을 막지 않으므로
반복 개선이 자유롭다.

**`focusKeyword` 를 반드시 넘겨라.** `publish-post` 의 게이트(`h2_keyword`)가 이 키워드를 쓴다.
키워드와 설명은 켜져 있는 SEO 플러그인(KDR SEO → Rank Math → Yoast 순)에 저장되고,
`seo.provider` 가 저장한 곳이다. `seo.skipped` 에 내용이 있으면(SEO 플러그인 없음) 사용자에게 알려라.

### 2. 검사

```
aiap/check-content-quality {
  content: "<HTML>",
  title: "...",
  keyword: "<포커스 키워드>"
}
```

`grade` 가 **A 또는 B** 이고 `failures` 가 비어야 한다.

### 3. (선택) 로컬 사전 검사

능력을 호출하기 전에 빠르게 확인하려면:

```bash
python scripts/lint-content.py content.html --title "제목" --keyword "키워드" --target-chars 1800
```

종료 코드 `0` = 통과, `1` = 실패. **서버가 최종 권위다** — 이 스크립트와 서버가
다르면 서버를 따른다.

### 4. 수정

```
aiap/update-post { postId: 123, content: "<고친 HTML>" }
```

### 4-1. KDR SEO 판정 (KDR SEO 가 켜진 사이트)

```
kdr-seo/analyze { postId: 123 }
→ { scores: { naver, google }, requiredFailures: [...], checks: [...] }
```

`requiredFailures` 가 비어야 발행된다. 고칠 때는 `kdr-seo/analyze { title, content, keyword, description }` 로
미리 확인한 뒤 `aiap/update-post` 로 저장한다. 키워드·설명은 `aiap/set-seo-meta` 로 바꾼다.

### 5. 발행

```
aiap/publish-post { postId: 123 }
→ { postId: 123, status: "publish", permalink: "...", gate: { grade: "A", ... } }
```

### 예약 발행

```
aiap/publish-post { postId: 123, status: "future", date: "2026-10-15 08:00" }
```

`date` 는 **사이트 시간** `Y-m-d H:i` 또는 `Y-m-d H:i:s`. 서버가 다음을 검증한다.

- 넘치는 날짜(`2월 31일`) → 거부
- 이미 지난 시각 → 거부
- 형식 오류 → 거부

WordPress 네이티브 예약 발행을 쓰므로 **WP-Cron 이 동작해야** 한다. 방문이 드문
사이트면 시스템 크론 연동을 사용자에게 안내하라.

## 게이트 실패 처리

`aiap_gate_failed` 오류가 오면 **재시도하지 말고 원인을 고쳐라.** 오류의
`data` 에 `failures`, `checks`, `grade`, `hits` 가 들어 있다.

| `failures` 항목 | 원인 | 조치 |
|---|---|---|
| `no_s1` | S1 패턴 검출 | `hits.S1` 을 보고 해당 표현 제거 |
| `links_verified` | `example.com` 류 링크 | **링크 삭제** (지어내지 말 것) |
| `h2_min` | H2 3개 미만 | 섹션 분리 |
| `no_h1` | 본문에 H1 | H1 → H2 |
| `h2_keyword` | 키워드 포함 H2 없음 | H2 하나에 키워드 반영 |
| `length` | 권장의 70% 미만 | 분량 보강 |
| `naturalness` | 등급 C/D | S1/S2 정리 후 재검사 |
| `links_resolved` | 클러스터 링크 자리(`data-aiap-link`)가 남음 | `aiap/link-cluster` 로 연결 (`aiap-cluster` 스킬) |
| `aiap_not_reviewed` | 묶음 글에 사람 검수 표시가 없음 | 발행하지 말고 사용자에게 검수 화면을 안내 |
| `aiap_kdr_required` | KDR SEO 필수 항목 위반 (T3 제목 단어 반복, B1 키워드 과다, T4/D6 중복, T5 키워드 불일치 등) | 오류 문구의 ref·메시지대로 고치고 `kdr-seo/analyze` 로 다시 확인 |

```
# 실패 응답 예
{
  "code": "aiap_gate_failed",
  "message": "발행 게이트를 통과하지 못했습니다: ...",
  "data": {
    "passed": false,
    "failures": ["no_s1", "links_verified"],
    "checks": { "no_s1": false, "links_verified": false, ... },
    "grade": "D"
  }
}
```

## 오류 코드

| 코드 | 의미 | 조치 |
|---|---|---|
| `aiap_gate_failed` | 게이트 거부 | 위 표대로 수정 |
| `aiap_forbidden` | 권한 부족 | `publish_posts` 필요. 사용자에게 알려라 |
| `aiap_input` | 입력 누락 | 필수 인자 확인 (`date` 등) |
| `aiap_404` | 글 없음 | postId 확인 |
| `aiap_time` | 예약 시각 오류 | 넘침/과거/형식 확인 |
| `aiap_ability_disabled` | 관리자가 능력을 껐음 | **재시도 금지.** 사이트 관리자에게 `AI 오토포스터 > AI 연결 > 능력` 안내 |

## 권한

| 능력 | 필요 권한 |
|---|---|
| `aiap/create-post` (draft) | `edit_posts` |
| `aiap/create-post` (publish/future) | `edit_posts` + `publish_posts` |
| `aiap/publish-post` | `edit_post`(대상) + `publish_posts` |
| `aiap/update-post` | `edit_post`(대상) |

`aiap_forbidden` 이 오면 **권한을 우회하려 하지 말고** 사용자에게 필요한 권한을 알려라.

## 하지 말 것

- 게이트 실패를 `status: "draft"` 로 회피하지 마라 (사용자가 요청한 경우 제외).
- 실패한 발행을 그대로 반복하지 마라. 원인을 먼저 고쳐라.
- `aiap_ability_disabled` 를 재시도하지 마라. 그건 관리자의 결정이다.
- `date` 를 UTC 로 넘기지 마라. **사이트 시간**이다.
- `example.com` 링크를 다른 더미로 바꾸지 마라. **삭제**가 정답이다.
