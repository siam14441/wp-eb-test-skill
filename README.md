# wp-eb-test

A Claude Code skill that QA-tests the [Essential Blocks](https://essential-blocks.com/) WordPress
plugin ecosystem (free, pro, and the shared controls submodule). It analyzes code changes against
`main`/`master`, builds a test checklist from the actual diff, verifies the fix through code
analysis, visually confirms behavior in the browser, and produces a markdown verdict report.

## What it does

- Diffs the free/pro/controls repos against `main`/`master` (or a specified branch)
- Builds a targeted test checklist directly from the changed code, not generic templates
- Classifies each test as pass-by-code, needs-visual-confirmation, or a concern
- Runs visual verification in the browser (editor → save → frontend → FSE)
- Writes a markdown QA report with a clear ship / no-ship verdict

It is strictly read-only against the codebase under test: no commits, pushes, or file edits other
than writing its own report.

## Installation

Copy this directory into your Claude Code skills folder:

```bash
cp -r wp-eb-test ~/.claude/skills/wp-eb-test
```

## Usage

Invoke it from a Claude Code session, e.g.:

```
/wp-eb-test
/wp-eb-test focus="slider"
/wp-eb-test scope=free build=no mode=investigate
```

See [SKILL.md](SKILL.md) for the full argument reference and workflow.

## Configuration

The skill looks for an optional `defaults.json` in the plugin directory for site URL, WP
credentials, and default scope/build/test settings — see the example in [SKILL.md](SKILL.md).
This file is local-only and should never be committed; credentials are otherwise asked for
interactively when needed.
