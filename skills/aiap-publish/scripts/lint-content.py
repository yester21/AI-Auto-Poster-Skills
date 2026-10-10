#!/usr/bin/env python3
"""Offline pre-check mirroring the AI Auto Poster server-side publish gate.

Usage:
  python lint-content.py <content.html> [--title TITLE] [--keyword KW] [--target-chars N]
  cat content.html | python lint-content.py - [--keyword KW]

Exit codes:
  0  gate passed
  1  gate failed (violations printed)
  2  usage error

IMPORTANT: the server is authoritative. This script lets you catch problems before
calling the ability, but `aiap/check-content-quality` and the gate inside
`aiap/create-post` / `aiap/publish-post` re-run the same checks server-side.
If this script and the server disagree, THE SERVER WINS.

The patterns below mirror AIAP_Writing_Guide (plugin v0.1.0). If the plugin's
patterns change, regenerate/update this list rather than editing one side only.
"""
import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- AIAP_Writing_Guide::forbidden_patterns() ---------------------------------

S1_GROUPS = {
    "발명 금지 (factuality)": [
        r"example\.com|example\.org|example\.net|example\.edu",
        r"placeholder",
        r"yourdomain|your-domain|도메인\.com",
        r"/reports/20\d\d/.*-appendix",
        r"lorem ipsum",
    ],
    "템플릿 잔여어": [
        # 조사가 뒤에 붙으므로(샘플에서/샘플을) 뒤쪽 경계를 요구하지 않는다
        r"(^|[^가-힣])샘플",
        r"여기에 .{0,10}(입력|작성)",
        r"TODO|FIXME|XXX",
        r"\{\{|\}\}|\$\{",
        r"\[.{0,20}\]\s*$",
    ],
    "번역투 (즉시 수정)": [
        r"에 대해(서)?",
        r"를 통해(서)?",
        r"에 의해",
        r"에 있어서",
        r"되어진다|되어졌다|되어집니다",
        r"가지고 있다|가지고 있습니다",
        r"라고 할 수 있다|라고 할 수 있습니다",
    ],
}

S1_ANCHORS = {
    "발명 금지 (factuality)": ["URL 예시", "장문 URL 예시 링크", "예시 링크", "여기에 링크", "출처 링크 삽입"],
    "템플릿 잔여어": ["에서 다룹니다", "를 참고하세요", "위 내용을 참조"],
}

S2_GROUPS = {
    "AI 상투 어휘": [
        r"결론적으로",
        r"다양한 측면에서",
        r"매우 중요(하다|합니다)",
        r"핵심적(이다|입니다)",
        r"효과적(이다|입니다)",
        r"지속가능한",
        r"혁신적(이다|입니다)",
        r"주목할 만하다",
        r"시사하는 바가 크다",
        r"귀중한 통찰",
    ],
}

GRADES = {  # (max S1, max S2, publishable)
    "A": (0, 2, True),
    "B": (2, 5, True),
    "C": (4, 9, False),
    "D": (99, 99, False),
}

TARGET_BY_KD = ((35, 1200), (65, 1800))  # else 2600
DUMMY_HREF = re.compile(r"example\.(com|org|net)|placeholder|yourdomain", re.I)


def to_plain(html: str) -> str:
    """Tags -> space, then collapse whitespace.

    strip_tags concatenates neighbours ('</h2><p>' -> ''), which destroys word
    boundaries and makes boundary-anchored patterns misfire silently.
    """
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", html)).strip()


def count_hits(groups, anchors, haystack):
    hits = []
    for label, patterns in groups.items():
        for pat in patterns:
            for m in re.finditer(pat, haystack, re.I | re.U):
                hits.append("%s: %s" % (label, m.group(0).strip()))
        for anchor in anchors.get(label, []):
            if anchor and anchor.lower() in haystack.lower():
                hits.append("%s: %s" % (label, anchor))
    # de-duplicate, preserve order
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def filler_lists(html: str) -> int:
    """Lists with <3 items, or where every item is <=12 chars."""
    count = 0
    for block in re.findall(r"<(ul|ol)\b[^>]*>(.*?)</\1>", html, re.I | re.S):
        items = [to_plain(t) for t in re.findall(r"<li\b[^>]*>(.*?)</li>", block[1], re.I | re.S)]
        items = [i for i in items if i]
        if not items:
            continue
        if len(items) < 3 or all(len(i) <= 12 for i in items):
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("content", help="path to HTML file, or - for stdin")
    ap.add_argument("--title", default="")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--target-chars", type=int, default=0)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    if args.content == "-":
        html = sys.stdin.read()
    else:
        try:
            with open(args.content, "r", encoding="utf-8") as fh:
                html = fh.read()
        except OSError as exc:
            print("cannot read %s: %s" % (args.content, exc), file=sys.stderr)
            return 2

    plain = to_plain(html)
    haystack = "\n".join([plain, args.title, html])  # raw HTML included: URL patterns live in href

    s1 = count_hits(S1_GROUPS, S1_ANCHORS, haystack)
    s2 = count_hits(S2_GROUPS, {}, haystack)
    filler = filler_lists(html)
    if filler:
        s2.append("채우기용 구조: 항목 3개 미만이거나 전부 한 줄짜리 리스트 %d개" % filler)

    h1 = len(re.findall(r"<h1\b", html, re.I))
    h2_titles = re.findall(r"<h2\b[^>]*>(.*?)</h2>", html, re.I | re.S)
    h2 = len(h2_titles)
    kw = args.keyword.strip()
    h2_with_kw = sum(1 for t in h2_titles if kw and kw.lower() in to_plain(t).lower())

    dummy = len(re.findall(r"href=[\"'][^\"']*(?:example\.(?:com|org|net)|placeholder|yourdomain)", html, re.I))
    chars = len(plain)

    target = args.target_chars or 1200

    grade = "D"
    for g, (max_s1, max_s2, _pub) in GRADES.items():
        if len(s1) <= max_s1 and len(s2) <= max_s2:
            grade = g
            break
    publishable = GRADES[grade][2]

    checks = {
        "no_s1": len(s1) == 0,
        "links_verified": dummy == 0,
        "h2_min": h2 >= 3,
        "no_h1": h1 == 0,
        "h2_keyword": True if not kw else h2_with_kw >= 1,
        "length": chars >= int(target * 0.7),
        "naturalness": len(s1) <= 2 and len(s2) <= 5,
    }
    failures = [k for k, v in checks.items() if not v]
    passed = not failures

    report = {
        "passed": passed,
        "grade": grade,
        "publishable": publishable,
        "counts": {"S1": len(s1), "S2": len(s2)},
        "hits": {"S1": s1, "S2": s2},
        "metrics": {
            "chars": chars, "h1": h1, "h2": h2, "h2_with_kw": h2_with_kw,
            "dummy_links": dummy, "target_chars": target,
        },
        "checks": checks,
        "failures": failures,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("grade=%s  S1=%d  S2=%d  chars=%d/%d  h2=%d  dummy_links=%d"
              % (grade, len(s1), len(s2), chars, target, h2, dummy))
        for h in s1:
            print("  S1  " + h)
        for h in s2:
            print("  S2  " + h)
        if failures:
            print("GATE FAILED: " + ", ".join(failures))
        else:
            print("GATE PASSED")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
