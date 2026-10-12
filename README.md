# ai-auto-poster-skills

한국어 SEO 글쓰기 스킬 — **AI 오토포스터**(WordPress 플러그인)의 MCP 능력을 사용한다.

글쓰기 **지식**(스킬)과 실제 **기능**(WordPress 능력)을 분리한 구조다.
규칙이 바뀌어도 서버만 고치면 되고, 스킬은 그 사용법을 안내한다.

> 이 플러그인은 **0.1.0 초기 개발판**이다. 알려진 문제와 예정 작업은
> [ROADMAP](https://github.com/yester21/AI-Auto-Poster/blob/main/ROADMAP.md) 참조.

| 계층 | 위치 | 역할 |
|---|---|---|
| 스킬 (이 저장소) | 에이전트 호스트 | 어떻게 쓸지 — SEO 구조, H태그, 슬롭 제거, 검증 절차 |
| 능력 (`aiap/*`) | WordPress 플러그인 | 실제로 하는 일 — 실측·발행·게이트 |
| 관리 화면 | `AI 오토포스터 > AI 연결` | MCP 연결 설정, 노출할 능력, 스킬 설치 프롬프트 |

> **서버가 진실이다.** 스킬의 규칙은 서버(`aiap/get-writing-guide`)와 같은 내용이며,
> 발행 시점에 서버가 **독립적으로 다시 검사**한다. 스킬을 건너뛰어도 발행되지 않는다.

## 스킬

| 스킬 | 언제 쓰나 |
|---|---|
| **aiap-write** | 한국어 SEO 글을 쓸 때. 구조·H태그·슬롭 제거·셀프 검사 |
| **aiap-publish** | 발행·예약·게이트 실패 해결 |
| **aiap-research** | 키워드 발굴과 실측 KD |
| **aiap-cluster** | 필러 1개 + 클러스터 몇 개를 초안으로 만들고 서로 링크. 발행은 사람이 검수한 뒤 |

## 사전 요구사항

1. **[AI 오토포스터 0.1+](https://github.com/yester21/AI-Auto-Poster)** WordPress 플러그인 설치·활성화
2. **MCP Adapter** 플러그인 활성화
3. **WordPress 6.9+** (Abilities API 내장)
4. **SERP API 키** — Serper 권장 (실측 KD 용). 없으면 `analyze-keyword` 가 오류를 반환한다

설치 상태는 `aiap/list-ability-status` 로 확인할 수 있다.
비어 있으면 워드프레스 관리자 **AI 오토포스터 > AI 연결** 화면에서 어느 요건이 빠졌는지 확인한다.

가장 쉬운 설치: **AI 연결 > 스킬** 탭의 설치 프롬프트를 복사해 AI 클라이언트에 붙여 넣는다.
저장소에 닿지 않는 클라이언트는 연결된 사이트의 `aiap/get-skill-package` 능력으로 받는다 (사이트에 설치된 플러그인과 같은 버전).

## 설치

### Claude Code

```
/plugin marketplace add yester21/ai-auto-poster-skills
/plugin install ai-auto-poster@ai-auto-poster-skills
```

또는 설정에 직접 등록:

```json
{
  "extraKnownMarketplaces": {
    "ai-auto-poster-skills": {
      "source": { "source": "github", "repo": "yester21/ai-auto-poster-skills" }
    }
  },
  "enabledPlugins": {
    "ai-auto-poster@ai-auto-poster-skills": true
  }
}
```

### 수동 설치

`skills/` 아래 디렉터리를 에이전트의 스킬 디렉터리에 복사한다.

```
~/.claude/skills/aiap-write/
~/.codex/skills/aiap-write/
~/.agents/skills/aiap-write/
```

### MCP 연결

```
WordPress:  https://<site>/wp-json/mcp/mcp-adapter-default-server
OAuth:      https://<site>/.well-known/oauth-authorization-server   (PKCE S256)
```

WordPress 의 **AI 오토포스터 > AI 연결** 화면에서 연결 설정을 복사하고, **능력** 탭에서 노출할 능력을 선택한다. 비활성 능력은
**등록 자체가 건너뛰어지므로** 디스패처로도 호출할 수 없다.

## 저장소 구조

```
.
├── .claude-plugin/
│   ├── marketplace.json      source: "./"  (저장소 루트가 곧 플러그인)
│   └── plugin.json
├── skills/
│   ├── aiap-write/
│   │   ├── SKILL.md
│   │   ├── references/       필요할 때만 로드하는 상세 규칙
│   │   │   ├── seo-structure.md
│   │   │   ├── heading-rules.md
│   │   │   ├── fabrication-guard.md
│   │   │   └── korean-slop-patterns.md
│   │   └── examples/         before / after 실사례
│   ├── aiap-publish/
│   │   ├── SKILL.md
│   │   └── scripts/lint-content.py    서버 게이트의 로컬 사본
│   ├── aiap-research/
│   │   └── SKILL.md
│   └── aiap-cluster/
│       └── SKILL.md
├── scripts/validate.py       매니페스트·스킬 구조·패턴 동기화 검증
├── AGENTS.md
├── CHANGELOG.md
└── LICENSE
```

## 로컬 검사 도구

발행 전에 서버를 호출하지 않고 확인할 수 있다.
**서버가 최종 권위이며**, 이 스크립트와 서버가 다르면 서버를 따른다.

```bash
python skills/aiap-publish/scripts/lint-content.py content.html \
  --title "제목" --keyword "키워드" --target-chars 1800
# exit 0 = 통과, 1 = 게이트 실패
```

## 저장소 검증

```bash
python scripts/validate.py
```

매니페스트 형식, `SKILL.md` frontmatter, 스킬 디렉터리 규약,
그리고 **`lint-content.py` 의 패턴이 플러그인 `AIAP_Writing_Guide` 와 일치하는지**를
검사한다. 플러그인 경로를 주면 동기화까지 확인한다.

```bash
python scripts/validate.py --plugin /path/to/ai-auto-poster
```

## 한계

- KD 는 **공개된 휴리스틱**이다. 도메인 권위·백링크는 반영하지 않는다.
- 총 검색 결과 수를 주지 않는 SERP 공급자(Serper)는 규모 점수에 중간값을 쓴다.
- 스킬의 패턴 목록은 서버와 **수동 동기화**된다. 검증 스크립트가 불일치를 잡는다.

## 라이선스

MIT — `LICENSE` 참조.
