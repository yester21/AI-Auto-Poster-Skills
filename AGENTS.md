# AGENTS.md

이 저장소는 **AI 오토포스터** WordPress 플러그인의 스킬 팩이다.
에이전트가 이 저장소를 수정할 때 지킬 규칙을 적는다.

## 절대 규칙 — 서버가 진실이다

스킬의 규칙은 플러그인의 `AIAP_Writing_Guide` 와 **같은 내용**이어야 한다.
발행 시점에 서버가 독립적으로 재검사하므로, 둘이 어긋나면:

- 서버가 아는 패턴을 스킬이 모르면 → 에이전트가 통과했다고 착각하고 발행 시도 → **거부됨**
- 스킬에만 있는 패턴은 → 스킬이 막고 서버는 통과시키므로 **혼란**

**패턴을 바꾸려면 서버(`class-aiap-writing-guide.php`)를 먼저 고치고,
그 다음 이 저장소의 `lint-content.py` 와 문서를 맞춘다.** 반대 순서는 금지다.

## 동기화 대상

| 이 저장소 | 플러그인 |
|---|---|
| `skills/aiap-publish/scripts/lint-content.py` | `AIAP_Writing_Guide::forbidden_patterns()` |
| `skills/aiap-write/references/*.md` | `AIAP_Writing_Guide` 의 각 메서드 |
| `skills/aiap-research/SKILL.md` 의 KD 표 | `AIAP_Google::kd_label()` / `kd_strategy()` |
| `skills/aiap-write/SKILL.md` 의 게이트 표 | `AIAP_Writing_Guide::publish_gates()` |

## 수정 후 반드시 실행

```bash
python scripts/validate.py --plugin /path/to/ai-auto-poster
python skills/aiap-publish/scripts/lint-content.py tests/fixtures/pass.html \
  --title "물가는 왜 체감과 다를까" --keyword "물가 체감" --target-chars 1800   # exit 0 이어야 함
python skills/aiap-publish/scripts/lint-content.py tests/fixtures/fail.html \
  --keyword "물가 체감" --target-chars 1800                                    # exit 1 이어야 함
```

`pass.html` 이 exit 0, `fail.html` 이 exit 1 이 아니면 픽스처나 스크립트가 깨진 것이다.

## 예시·문서에 수치를 쓸 때

**측정하지 않은 게이트 수치를 쓰지 마라.** 이 저장소의 예시 문서는 실제 측정값을 싣는다.
추정으로 수치를 적으면 이 스킬이 경고하는 "발명" 을 스스로 하는 셈이다.

수치를 바꾸려면 스크립트를 돌려 나온 값을 그대로 옮긴다.

## 스킬 작성 규칙

1. `skills/<name>/SKILL.md` 에 YAML frontmatter 필수: `name`, `description`,
   `license`, `metadata.author`, `metadata.version`, **`allowed-tools`**
2. 디렉터리 이름 = frontmatter `name`
3. `description` 에 **트리거 문구를 총망라**한다 (한국어 표현 포함). 스킬 자동 활성화의 핵심이다
4. 상세 내용은 `references/` 로 분리한다 — "해당 범주를 감지했을 때만 로드" 를 명시해
   토큰을 아낀다
5. 실행 도구는 `scripts/` 에 둔다
6. `allowed-tools` 는 **최소로**. 발행 스킬은 `Read Bash` 면 충분하다

## 매니페스트

- `.claude-plugin/marketplace.json` 의 plugin `source` 는 **`"./"`**
  (저장소 루트가 곧 플러그인). `plugins/<name>/` 중첩을 쓰지 않는다
- `.claude-plugin/plugin.json` 은 `name` 필수, kebab-case

## 하지 말 것

- 서버를 고치지 않고 이 저장소의 패턴만 바꾸지 마라
- `example.com` 류 더미를 예시에 넣지 마라 (단, `tests/fixtures/fail.html` 은 예외 —
  실패를 재현하는 픽스처다)
- 검증하지 않은 수치·게이트 결과를 문서에 쓰지 마라
- `allowed-tools` 를 `Bash` 포함 전체로 넓히지 마라
