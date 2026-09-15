<!--
QA REPORT TEMPLATE — wp-eb-test skill

How to use this file (Phase 6):
- Copy this structure into qa-report.md and fill in every {{placeholder}}.
- Write style: caveman. Short sentences, no fluff. Keep all info, strip prose padding.
  "Block render editor. No errors. Settings persist." NOT "The block renders correctly..."
- File paths, error messages, commit SHAs, selectors: keep FULL, never trim these.
- Sections marked (OPTIONAL) — include only if relevant to this test run. A CSS-only
  change doesn't need a Security section. A pure-backend change may not need Mobile/A11y
  rows. Cut what doesn't apply, add a section if the test genuinely needs one this
  template doesn't have (e.g. a "Migration Path" section for an attribute-format change).
- Status markers: pair emoji + text, e.g. "✅ PASS", "❌ FAIL (visual)", "⚠️ CONCERN",
  "🔍 NEEDS VISUAL", "🚫 BLOCKED", "ℹ️ INFO". Never emoji alone — always keep the text
  label so the report is still greppable.
- Screenshots (only if screenshots=yes): embed inline with ![desc](path-or-cloudinary-url)
  so they render in most markdown viewers. If a Cloudinary upload failed, write
  "Cloudinary upload failed" and fall back to the local path.
-->

# QA Report: Essential Blocks — {{Block or Area Name}} — {{issue_id or scope}}

**Date:** {{YYYY-MM-DD}}
**Site:** {{site_url}}
**Scope:** {{free / pro / controls / free+pro / all}}
**Base:** {{component}} `{{base_ref}}` @ {{base_sha}} <!-- repeat per component -->
<!-- (OPTIONAL) only if this is a re-run after fixes were pulled mid-session -->
**Updated {{date}} (round {{n}}):** {{what changed and was re-tested}}

## Tested

| Component | Branch | Base | Files Changed |
|-----------|--------|------|----------------|
| {{Free/Pro/Controls}} | {{branch}} @ **{{head_sha}}** | {{base_ref}} ({{n}} commits) | {{n}} (+{{lines}}) |

Build: {{fresh / rebuilt — which commits triggered it, which build script, result}}.

## Verdict

**{{✅ PASS / ⚠️ PARTIAL / ❌ FAIL}}** ({{ship-ready / needs fixes / blocked}}).

{{2-5 caveman sentences: what was tested, what works, what's fixed, what's broken.
Call out any regression explicitly confirmed fixed or still present.}}

**Coverage: {{n}} of {{total}} tests confirmed by running (browser/curl/DB). {{n}} code-only. {{n}} N/A.**

<!-- (OPTIONAL) Only when this run verifies a fix for a reported bug. Omit for pure
new-feature testing with no prior broken state to confirm. -->
**Bug reproduced:** {{Yes -- confirmed broken on pre-fix state ({{commit/build}}), then confirmed fixed / No -- reproduction not attempted: {{why}}. Verdict based on {{code review / description matching}} only, not a confirmed broken-then-fixed comparison.}}

## Change Summary

<!-- One bullet per changed file/module, from Phase 1 diff. Label Free/Pro/Controls. -->
- `{{path}}` ({{new/modified}}) → {{what it does, one line}}.

## Fix Target

<!-- From Phase 2. What the fix/issue claims to solve, and what "done" means here. -->
{{Fix description or "No fix description provided."}}

## Test Results

| # | Test | Where | How | Result |
|---|------|-------|-----|--------|
| **{{Category header, e.g. Editor / Frontend / Security / Regression}}** ||||
| 1 | {{TC from Phase 3, format: what changed → expected result}} | {{Free/Pro/Controls}} | {{Visual / curl / DB / Code / File}} | {{✅ PASS / ❌ FAIL / ⚠️ PASS(Code) / 🔍 NEEDS VISUAL}} |

<!-- Group rows under category header rows as in the example above. Categories are
filters, not sources — only include categories the diff actually touches (Phase 3). -->

## Fail Detail

<!-- One entry per FAIL, with repro steps + evidence (console/network/snapshot excerpt).
"None." if nothing failed. -->
{{None.}}

## User Check

<!-- (OPTIONAL section, but Phase 3 requires 3-5 user-perspective tests somewhere —
put them here or fold into Test Results. Skip rows that don't apply to this change. -->
| Perspective | Verdict | Note |
|-------------|---------|------|
| Content creator | {{✅ PASS}} | {{one line}} |
| Visitor | {{✅ PASS}} | {{one line}} |
| Mobile | {{✅ PASS}} | {{one line}} |
| Accessibility | {{✅ PASS}} | {{one line}} |

## Concerns

<!-- (OPTIONAL) Non-blocking issues found outside the direct test scope. Tag severity.
Always include a Security line if the code touches user input/AJAX/DB, even if PASS. -->
- **{{LOW/MED/HIGH}} — {{title}}:** {{what, repro if found, suggested fix, blocking or not}}.
- **Security: {{✅ PASS / ⚠️ CONCERN}}.** {{sanitization/nonce/capability/escaping notes}}.

## Test Artifacts

<!-- (OPTIONAL) Anything created during testing that needs manual cleanup — this skill
is read-only and never deletes/reverts on its own. -->
Created (please clean up — not deleted per policy):
- {{Page/post/option created, ID and URL}}

State restored: {{what was verified unchanged — settings, templates, tokens, etc.}}

## Next Steps

{{Ship it. / Fix X before ship. / Blocked on Y.}} {{Optional non-blocking follow-ups.}}
