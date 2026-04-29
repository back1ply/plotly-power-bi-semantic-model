# White-Label BI Shell

## Problem Statement
How might we turn this Plotly Dash app into a credible white-label BI platform that Plotly dev team judges see as "the future of Python enterprise analytics on semantic models"?

## Recommended Direction

Companies already pay for Fabric/Power BI to host their semantic model. Power BI Embedded is expensive, locked to Microsoft branding, limited customization. This app = drop in Dash, point at existing model, get fully branded analytics. For Plotly dev team judges, this is the narrative they want: Dash as a serious enterprise BI layer, not a dashboard toy.

Two things together make this unbeatable:
- **White-label shell** answers *why this exists* — theming, branding, full page suite
- **DAX editor** answers *proof it's real* — live query execution against the semantic model

## Priorities

### Priority 1 — DAX Query View (new page 4) ✅ DONE
The proof-of-concept that makes everything else believable. `PbiClient.query(dax: str)` already accepts arbitrary strings — infrastructure is done.

Scope:
- ✅ Textarea input for raw DAX
- ✅ Execute button → `pbi_client.query(user_dax)`
- ✅ ag-Grid results table
- ✅ Error feedback (Power BI returns meaningful errors)
- ✅ Schema panel on the side for reference
- ~~Query history via `dcc.Store`~~ — stripped; dead stub with no callbacks, removed to keep code clean

### Priority 2 — Dynamic Dashboard polish (page 1) ⏳ BLOCKED
Not new features — fix what feels off. Smooth transitions, consistent spacing, dropdowns that feel intentional. Requires visual review before touching code.

**Status:** No visual review done yet. Do not touch page 1 code until the review happens.

### Priority 3 — Theming layer ✅ DONE
Parameterize logo, primary color, font via a `ThemeConfig` dataclass. Mantine's `MantineProvider` already supports this. One config file = white-label switch. This is the narrative anchor for judges.

**Implemented:** `ThemeConfig` frozen dataclass in `config.py`. Three env vars:
- `APP_TITLE` (default: `"Sales Dashboard"`)
- `PRIMARY_COLOR` (default: `"blue"` — any Mantine color name)
- `FONT_FAMILY` (default: `"'Inter', sans-serif"`)

**Remaining gap:** `presentation/theme.py` still has hardcoded hex colors used by Plotly charts. These are independent of `MantineProvider` and not yet wired to `ThemeConfig`.

## Key Assumptions

- [x] `PbiClient.query()` handles arbitrary user DAX — input hardening added in `domain/utils.py`: length cap (10,000 chars), keyword allowlist (`EVALUATE`/`DEFINE`), `INFO.*` DMV block
- [ ] Mantine theming covers all custom color surfaces (sidebar, cards, charts) — not validated
- [ ] Power BI error messages are descriptive enough to show directly to users — not validated

## MVP Scope
DAX Query View (P1) ✅ + theming layer (P3) ✅ + polish pass on page 1 (P2) ⏳

## Future Work
- **Monaco editor** — syntax highlighting, line numbers, proper IDE feel
- **DAX autocomplete** — schema-aware suggestions (needs measure/column name parsing)
- **Query history** — browser-session list of past queries; `dcc.Store` pattern is the right approach, implement when needed
- **Drag-and-drop dashboard builder** — let users compose their own page layouts
- **Multi-tenant auth** — support multiple semantic models / workspaces per deployment
- **Query export** — save DAX results to CSV/Excel directly from the UI
- **Chart theming** — wire `ThemeConfig.primary_color` to `presentation/theme.py` CATEGORICAL_PALETTE

## Open Questions
- What specifically feels off on page 1 dynamic dashboard? Still needs visual review.
- ~~Should the theming config be a `.toml` / `.json` file or Python dict in `config.py`?~~ — resolved: frozen dataclass in `config.py`, env-var driven.
