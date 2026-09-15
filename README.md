# Essential Blocks QA Skills

Claude Code skills for QA-testing the [Essential Blocks](https://essential-blocks.com/) WordPress
plugin ecosystem (free, pro, and the shared controls submodule).

## Skills

### [wp-eb-test](wp-eb-test/)

QA-tests Essential Blocks by analyzing code changes against `main`/`master`, building a test
checklist directly from the diff, verifying the fix through code analysis, visually confirming
behavior in the browser, and producing a markdown verdict report.

- Diffs the free/pro/controls repos against a base branch
- Builds a targeted test checklist from the actual changed code, not generic templates
- Classifies each test as pass-by-code, needs-visual-confirmation, or a concern
- Runs visual verification in the browser (editor → save → frontend → FSE)
- Writes a markdown QA report with a clear ship / no-ship verdict

See [wp-eb-test/SKILL.md](wp-eb-test/SKILL.md) for the full argument reference and workflow.

### [wp-eb-reproduce](wp-eb-reproduce/)

Generates a visual reproduction guide for failed test cases from a `wp-eb-test` QA report (or any
similar test report). Extracts every FAIL item and produces step-by-step reproduction
instructions, optionally with before/after screenshots.

See [wp-eb-reproduce/SKILL.md](wp-eb-reproduce/SKILL.md) for the full argument reference and workflow.

Both skills are strictly read-only against the codebase/site under test: no commits, pushes, or
file edits other than writing their own reports.

## Installation

Copy the skill directory you want into your Claude Code skills folder:

```bash
cp -r wp-eb-test ~/.claude/skills/wp-eb-test
cp -r wp-eb-reproduce ~/.claude/skills/wp-eb-reproduce
```

## Usage

Invoke either skill from a Claude Code session, e.g.:

```
/wp-eb-test
/wp-eb-test focus="slider"
/wp-eb-test scope=free build=no mode=investigate

/wp-eb-reproduce report=qa-report.md
/wp-eb-reproduce report=qa-report.md screenshots=yes
```

## Configuration

Both skills look for an optional `defaults.json` in the plugin directory for site URL, WP
credentials, and other run defaults — see the example in
[wp-eb-test/SKILL.md](wp-eb-test/SKILL.md). This file is local-only and should never be
committed; credentials are otherwise asked for interactively when needed.
