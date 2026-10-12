---
name: aiap-cluster
description: "Plan and draft a pillar + cluster content set (필러 콘텐츠와 클러스터 콘텐츠) for a WordPress site using the AI Auto Poster abilities: split a seed keyword into one pillar and a few cluster keywords, reject keywords with the same search intent (measured SERP overlap), create all posts as drafts, and connect pillar↔cluster internal links. A human reviews and publishes. Use when the user says 필러 콘텐츠, 클러스터 콘텐츠, 토픽 클러스터, 주제 묶음, 허브 글, 연관 글 여러 개 만들어 줘, pillar page, topic cluster, cornerstone."
license: MIT
metadata:
  author: 김대리닷넷
  version: "0.1.0"
allowed-tools: Read Write Edit Grep Glob AskUserQuestion
---

# aiap-cluster: 필러·클러스터 초안 만들기

필러 1개(주제 전체를 다루는 글)와 클러스터 몇 개(하위 질문 하나씩)를 **초안으로** 만들고 서로 링크한다.
**발행은 사람이 한다.** 이 스킬은 발행하지 않는다.

## 먼저 알아 둘 것 — 공식 근거와 한계

- 필러·클러스터는 네이버·구글 공식 문서에 없는 업계 용어다. **순위가 오른다고 약속하지 마라.**
  네이버는 사이트 안 링크 10개보다 외부 사이트 10곳의 언급이 신뢰도에 유리하다고 적었다.
- 공식 근거는 두 가지뿐이다.
  - 네이버 「콘텐츠 작성시 권장 사항」 ②: 전체 콘텐츠의 절반 이상을 핵심 주제로
  - 네이버 「웹 콘텐츠 스팸사례」 저품질 콘텐츠 대량 생성, 구글 스팸 정책 scaled content abuse·doorway
    → **같은 의도의 글을 여러 개 만들지 않는다. 한꺼번에 많이 만들지 않는다.**
- 필러 개수 제한은 없다. 묶음마다 필러 1개다.
- 묶음당 클러스터 상한(기본 5)·의도 겹침 기준(상위 10개 중 4개)·필러 글자수는 **플러그인 기준**이다.

## 흐름

```
1. aiap/discover-keywords        후보 모으기
2. aiap/analyze-keyword          후보 실측 (KD·권장 글자수)
   (선택) kdr-seo/keyword-volume 네이버 월간 검색량 — KDR SEO 가 있고 키가 설정된 경우
3. 필러 1개 + 클러스터 N개 고르기  ← 여기서 사용자에게 확인받는다
4. aiap/check-keyword-overlap    같은 검색 의도 키워드 합치기
5. aiap/create-cluster           묶음 저장 → clusterId
6. aiap/create-post × (1+N)      초안 (clusterId·clusterRole·focusKeyword)
7. aiap/link-cluster             링크 자리 연결 → complete 확인
8. aiap/get-cluster              게이트·링크 상태 보고
9. 사용자에게: "관리자 > AI 오토포스터 > 클러스터 에서 검수하고 예약 발행하세요"
```

### 3. 고르기

- **필러**: 주제를 대표하는 넓은 키워드. 사이트 핵심 주제(가장 많은 카테고리) 안에 있어야 한다.
- **클러스터**: 필러 안의 하위 질문 하나씩. "방법", "비용", "준비물", "초보 루틴"처럼 **답이 다른 질문**이어야 한다.
  단어만 바꾼 변형(“홈트 루틴” / “홈트레이닝 루틴”)은 같은 글이다.
- 클러스터는 적게 시작한다 (3~5개). 상한을 넘기면 `create-cluster` 가 거부한다.
- 고른 목록을 사용자에게 보여 주고 확인받은 뒤 진행한다.

### 4~5. 의도 겹침과 묶음 저장

```
aiap/check-keyword-overlap { keywords: ["홈트레이닝", "홈트 초보 루틴", "홈트 준비물", ...] }
→ { groups: [ ["홈트 초보 루틴", "홈트 루틴 초보"] ], pairs: [...] }
```

`groups` 에 들어간 키워드끼리는 한 글로 합친다 (대표 하나만 남긴다).
`create-cluster` 는 SERP 가 설정돼 있으면 같은 검사를 다시 하고, 겹치면 **거부**한다 (`aiap_same_intent`).

```
aiap/create-cluster {
  topic: "홈트레이닝",
  pillarKeyword: "홈트레이닝",
  clusterKeywords: ["홈트 초보 루틴", "홈트 준비물", "홈트 다이어트 효과"],
  categoryId: 3
}
→ { id: "c_1a2b3c4d5e", warnings: [...], site_focus: {...} }
```

`warnings` (주제 집중도, SERP 미설정)는 **사용자에게 그대로 전한다.**

### 6. 초안

필러부터 쓴다. 모든 글은 `aiap-write` 규칙을 따르고 `aiap/check-content-quality` 로 검사한다.

```
aiap/create-post {
  title, content, status: "draft",
  focusKeyword: "홈트레이닝",          ← 계획의 키워드와 같아야 한다 (띄어쓰기 무시)
  metaDescription: "...",
  clusterId: "c_1a2b3c4d5e",
  clusterRole: "pillar"               ← 클러스터 글은 "cluster"
}
```

- 묶음 글은 `draft` 로만 만들 수 있다.
- 필러의 권장 글자수는 한 단계 위다 (1200→1800, 1800→2600, 2600→3400). 응답의 `cluster.targetChars` 를 따른다.
- `categoryId` 를 묶음에 줬으면 글에 따로 넘기지 않아도 그 카테고리로 들어간다.

#### 링크 자리

다른 묶음 글로 가는 링크는 **주소를 쓰지 말고 자리만 둔다.** 아직 주소가 없기 때문이다.

```html
<a data-aiap-link="pillar">홈트레이닝 전체 가이드</a>
<a data-aiap-link="홈트 준비물">준비물 정리</a>
```

| 글 | 넣을 링크 |
|---|---|
| 필러 | 모든 클러스터로 하나씩, 문맥에 맞는 문단 안에 |
| 클러스터 | 필러로 하나 (도입부나 결론). 다른 클러스터로는 필요할 때만 |

앵커 텍스트는 대상 글을 설명하는 말로 쓴다 ("여기", "자세히" 금지 — 네이버·구글 공통).

### 7. 연결

```
aiap/link-cluster { clusterId }
→ { complete: true|false, clusters: [ {keyword, links_to_pillar, pillar_links_here} ], not_created: [], unresolved: {} }
```

- `complete: false` 면 빠진 링크를 `aiap/update-post` 로 넣고 다시 연결한다.
- `unresolved` 는 계획에 없는 키워드로 둔 자리다. 키워드를 고친다.
- 연결되지 않은 자리가 남으면 발행 게이트 `links_resolved` 가 발행을 막는다.
- 발행되지 않은 글로 가는 링크는 방문자에게 글자로만 보이고, 그 글이 발행되면 링크가 된다. 발행 순서는 신경 쓰지 않아도 된다.

### 9. 넘기기

발행하지 마라. 사용자에게 다음을 알린다.

- 만든 글 목록 (역할·키워드·게이트 등급)
- 검수 화면: **관리자 > AI 오토포스터 > 클러스터**
- 검수할 때 확인할 것: 수치·사실, **운영자의 경험·관점 추가** (네이버: AI 생성 콘텐츠를 그대로 게시하지 말 것), 클러스터끼리 내용 중복
- 검수 표시한 글만 예약 발행할 수 있고, 검수 뒤에 에이전트가 글을 고치면 표시가 지워진다

## 하지 말 것

- 계획에 없는 키워드로 글을 늘리기 — `create-post` 가 거부한다
- 같은 의도의 키워드를 단어만 바꿔 여러 글로 만들기
- 링크 주소를 직접 쓰기 (`?p=123`, 추측한 고유주소)
- `aiap/publish-post` 로 묶음 글 발행 — 검수 표시가 없으면 거부된다
- "상위노출", "순위 상승" 같은 약속
