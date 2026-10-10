---
name: aiap-research
description: "Research Korean keywords for a WordPress post using the AI Auto Poster abilities: discover keyword candidates from Google autocomplete and measure real keyword difficulty (KD) from live SERP top-10 results. Use when asked to find keywords, pick a topic, check keyword competition/difficulty, decide which keyword to target, or when the user says 키워드 찾아줘, 키워드 발굴, 경쟁 강도, KD, 어떤 키워드로 쓸까, 검색량/경쟁 조사. KD here is a published heuristic measured from real search results, not an AI guess."
license: MIT
metadata:
  author: 김대리닷넷
  version: "0.1.0"
allowed-tools: Read Write Edit Grep Glob AskUserQuestion
---

# aiap-research: 키워드 발굴과 실측

## 실측이지 추정이 아니다

`aiap/analyze-keyword` 는 구글 상위 10개 결과를 **실제로 조회**해 KD 를 계산한다.
AI 추정치로 대체하지 않는다 — SERP 미설정이면 **오류를 반환**한다.

> **KD 를 지어내지 마라.** 능력이 오류를 반환하면 사용자에게 SERP 설정을 요청하고,
> 추측값을 쓰지 마라.

## 발굴

```
aiap/discover-keywords { topic: "홈트레이닝", limit: 24 }
→ { keywords: [ { keyword, source } ], count: N }
```

구글 자동완성 실측 결과만 반환한다. `source` 는 `google` 이다.

토픽은 구체적으로. "운동" 보다 "집에서 하는 홈트레이닝" 이 쓸 만한 후보를 준다.

## 실측

```
aiap/analyze-keyword { keyword: "홈트레이닝 초보 루틴" }
→ {
    keyword, kd, label, color,
    source: "google",
    total_results, target_chars, strategy,
    signals: { strong_domains, strong_count, strong_score,
               title_hits, title_score,
               total_score, url_hits, url_score },
    items: [ { domain, title, strong } ],
    cached
  }
```

### KD 해석

| KD | 라벨 | 전략 |
|---|---|---|
| 0~24 | 매우 쉬움 | 신규 사이트·1,200자로도 노려볼 만함 |
| 25~44 | 쉬움 | 1,800자 이상이면 1페이지 현실적 |
| 45~64 | 보통 | 2,400자 이상 + 깊이 + 내부링크 필요 |
| 65~79 | 어려움 | 롱테일 변형을 메인으로 검토 |
| 80~100 | 매우 어려움 | 해당 키워드보다 하위 조합을 권장 |

### KD 산출 근거 (완전 공개)

상위 10개 실측 4개 시그널 합산.

| 시그널 | 점수 |
|---|---|
| 강세 도메인 (위키·포털·대형 매체, **도메인 경계** 판정) | 도메인당 +9 (최대 40) |
| 제목에 키워드 단어 포함 | 개당 +4.5 (최대 30) |
| 총 검색 결과 규모 (log10) — 총계를 주지 않는 공급자는 중간값 10 | 최대 20 |
| URL에 키워드 포함 (퍼센트 인코딩 디코드) | 개당 +2 (최대 10) |

**도메인 권위·백링크는 반영되지 않는다.** 이는 공개된 휴리스틱이며, 사용자에게도
그렇게 설명하라. "예상 순위" 를 단정하지 마라.

## 권장 글자수

응답의 `target_chars` 를 쓴다 (KD 로 자동 산정):

| KD | 권장 |
|---|---|
| < 35 | 1,200 |
| < 65 | 1,800 |
| ≥ 65 | 2,600 |

## 캐시

SERP 조회는 **키워드별 12시간 캐시**된다. 응답의 `cached: true` 는 캐시 적중이다.
같은 키워드를 반복 조회해도 크레딧이 들지 않는다.

> `analyze-keyword` / `discover-keywords` 는 **유료 쿼터**를 쓴다. `publish_posts`
> 권한이 필요하다. 불필요하게 반복 호출하지 마라.

## 키워드 선정

1. `discover-keywords` 로 후보를 모은다
2. 관심 후보 3~5개를 `analyze-keyword` 로 실측한다
3. **KD 가 낮고 검색 의도가 우리 글과 맞는 것**을 고른다
4. 메인 1개 + 서브 최대 4개를 정한다
5. 서브 키워드는 H2 에 자연스럽게 녹인다

판단 기준은 **KD 만이 아니다.** KD 가 낮아도 의도가 다르면 전환되지 않는다.
사용자에게 의도를 확인하라.

## 하지 말 것

- KD·검색량·순위를 추측으로 채우지 마라.
- SERP 오류를 무시하고 진행하지 마라.
- 같은 키워드를 캐시 무시하고 반복 조회하지 마라.
- `strong_domains` 목록을 함부로 늘리지 마라 — 설정 화면의 값이다.
