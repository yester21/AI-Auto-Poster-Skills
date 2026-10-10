#!/usr/bin/env python3
"""Validate the ai-auto-poster-skills repository.

Usage:
  python scripts/validate.py
  python scripts/validate.py --plugin /path/to/ai-auto-poster

Checks:
  1. .claude-plugin/marketplace.json and plugin.json exist and are valid
  2. marketplace uses the "source": "./" form (repo root IS the plugin)
  3. every skills/*/SKILL.md has YAML frontmatter with name + description
  4. the skill directory name matches the frontmatter `name`
  5. skills declare allowed-tools (this repo's convention)
  6. required supporting files exist
  7. with --plugin: the S1/S2 patterns in scripts/lint-content.py match
     AIAP_Writing_Guide exactly (drift here means the local pre-check and the
     server-side gate disagree — the dangerous direction is a pattern the server
     enforces but the local script misses)

Exit code 0 = all checks passed.
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("  PASS  %s" % label)
    else:
        FAIL += 1
        print("  FAIL  %s%s" % (label, ("  -- " + detail) if detail else ""))


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_frontmatter(text):
    """Return dict of top-level scalar frontmatter keys (handles quoted values)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    data = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'") and len(val) >= 2:
            val = val[1:-1]
        data[key] = val
    return data


# --- plugin pattern extraction ------------------------------------------------

KNOWN_LABELS = {
    "발명 금지 (factuality)",
    "템플릿 잔여어",
    "번역투 (즉시 수정)",
    "AI 상투 어휘",
    "채우기용 구조",
    "S1",
    "S2",
}


def php_block_strings(php_text, key):
    """Extract array-element strings from every `'<key>' => array( ... ),` block.

    Only standalone quoted lines count as elements. Being loose here is worse than
    useless: a naive "every quoted string in the block" scan also picks up the
    adjacent `advice` value, other array keys, and words quoted inside `//`
    comments — producing false "drift" that trains you to ignore the check.
    """
    out = set()
    for m in re.finditer(r"'%s'\s*=>\s*array\((.*?)\),\s*\n" % key, php_text, re.S):
        body = re.sub(r"//[^\n]*", "", m.group(1))  # drop line comments
        for line in body.splitlines():
            mm = re.match(r"^'((?:[^'\\]|\\.)*)',?$", line.strip())
            if not mm:
                continue
            s = mm.group(1)
            if s and s not in KNOWN_LABELS:
                out.add(s)
    return out


def py_group_strings(py_text, name):
    """Extract r"..." literals from a python dict literal `name = { ... }`."""
    m = re.search(r"^%s\s*=\s*\{(.*?)^\}" % re.escape(name), py_text, re.S | re.M)
    if not m:
        return set()
    return set(re.findall(r'r"((?:[^"\\]|\\.)*)"', m.group(1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", default="", help="path to the ai-auto-poster plugin")
    args = ap.parse_args()

    print("=== ai-auto-poster-skills validation ===")
    print("root: %s\n" % ROOT)

    # 1-2. manifests
    print("-- manifests --")
    mp_path = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    pl_path = os.path.join(ROOT, ".claude-plugin", "plugin.json")

    check("marketplace.json exists", os.path.isfile(mp_path))
    check("plugin.json exists", os.path.isfile(pl_path))

    mp = None
    if os.path.isfile(mp_path):
        try:
            mp = json.loads(read(mp_path))
            check("marketplace.json is valid JSON", True)
        except Exception as exc:
            check("marketplace.json is valid JSON", False, str(exc))

    if isinstance(mp, dict):
        check("marketplace has name", bool(mp.get("name")))
        check("marketplace has owner", bool(mp.get("owner")))
        plugins = mp.get("plugins")
        check("marketplace has non-empty plugins", isinstance(plugins, list) and len(plugins) > 0)
        if isinstance(plugins, list) and plugins:
            p0 = plugins[0]
            check('plugin source is "./"', p0.get("source") == "./", "got %r" % p0.get("source"))
            check("plugin entry has name", bool(p0.get("name")))

    if os.path.isfile(pl_path):
        try:
            pj = json.loads(read(pl_path))
            check("plugin.json is valid JSON", True)
            check("plugin.json has name (kebab-case)", bool(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", pj.get("name", ""))))
        except Exception as exc:
            check("plugin.json is valid JSON", False, str(exc))

    # 3-6. skills
    print("\n-- skills --")
    skills_dir = os.path.join(ROOT, "skills")
    check("skills/ exists", os.path.isdir(skills_dir))

    if os.path.isdir(skills_dir):
        names = sorted(d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d)))
        check("at least one skill", len(names) >= 1, "found %d" % len(names))

        for name in names:
            sdir = os.path.join(skills_dir, name)
            skill_md = os.path.join(sdir, "SKILL.md")
            print("  [%s]" % name)
            check("    SKILL.md exists", os.path.isfile(skill_md))
            if not os.path.isfile(skill_md):
                continue
            text = read(skill_md)
            fm = parse_frontmatter(text)
            check("    has YAML frontmatter", fm is not None)
            if fm is None:
                continue
            check("    frontmatter has name", bool(fm.get("name")))
            check("    frontmatter name matches directory", fm.get("name") == name,
                  "name=%r dir=%r" % (fm.get("name"), name))
            desc = fm.get("description", "")
            check("    description is substantial (>=80 chars)", len(desc) >= 80, "len=%d" % len(desc))
            check("    declares allowed-tools", bool(fm.get("allowed-tools")))
            check("    body is non-trivial", len(text) > 1500, "len=%d" % len(text))

        for required in [
            os.path.join("aiap-write", "references", "fabrication-guard.md"),
            os.path.join("aiap-write", "references", "korean-slop-patterns.md"),
            os.path.join("aiap-publish", "scripts", "lint-content.py"),
        ]:
            check("exists: skills/%s" % required.replace(os.sep, "/"),
                  os.path.isfile(os.path.join(skills_dir, required)))

    # 7. pattern sync
    print("\n-- pattern sync (skill vs server) --")
    lint_path = os.path.join(skills_dir, "aiap-publish", "scripts", "lint-content.py")
    if not args.plugin:
        print("  SKIP  pass --plugin <path> to verify against AIAP_Writing_Guide")
    elif not os.path.isdir(args.plugin):
        check("plugin path exists", False, args.plugin)
    else:
        guide_path = os.path.join(args.plugin, "includes", "class-aiap-writing-guide.php")
        check("plugin guide file exists", os.path.isfile(guide_path), guide_path)
        if os.path.isfile(guide_path) and os.path.isfile(lint_path):
            php = read(guide_path)
            py = read(lint_path)

            php_patterns = php_block_strings(php, "patterns")
            php_anchors = php_block_strings(php, "anchors")
            php_all = php_patterns | php_anchors

            py_s1 = py_group_strings(py, "S1_GROUPS")
            py_s2 = py_group_strings(py, "S2_GROUPS")
            py_anchor = py_group_strings(py, "S1_ANCHORS")
            py_all = py_s1 | py_s2 | py_anchor

            check("extracted PHP patterns", len(php_all) > 15, "got %d" % len(php_all))
            check("extracted Python patterns", len(py_all) > 15, "got %d" % len(py_all))

            missing_in_py = sorted(p for p in php_all if p not in py)
            missing_in_php = sorted(p for p in py_all if p not in php)

            check(
                "every server pattern is present in lint-content.py",
                not missing_in_py,
                "MISSING: " + " | ".join(missing_in_py[:8]),
            )
            if missing_in_php:
                # not fatal: the local script may hold extra convenience patterns,
                # but it should be a deliberate decision, so report it.
                print("  NOTE  lint-content.py has %d pattern(s) not in the server: %s"
                      % (len(missing_in_php), " | ".join(missing_in_php[:8])))

    print("\n=== summary: pass=%d fail=%d ===" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
