# Next Session Prompt

We're building a white-label Dash BI shell over a Power BI semantic model (Plotly competition entry).
Working dir: F:\Shehab Projects\plotly-power-bi-semantic-model
Read AGENTS.md before touching any code — it has strict validation and arch rules.

## Context

Architecture: Clean Architecture — domain / application / infrastructure / presentation / components / pages.
Nav routes single source of truth: `presentation/constants.py`.
Theming: `ThemeConfig` frozen dataclass in `config.py` (APP_TITLE, PRIMARY_COLOR, FONT_FAMILY env vars).
`layout.py` passes ThemeConfig to MantineProvider + build_sidebar.
DAX input hardening: `domain.validate_dax_query()` called before every `client.query()`.

## Four tasks — do in order, finish + verify each before starting next

---

### Task 1: Chart theming
File: `presentation/theme.py`
Problem: CATEGORICAL_PALETTE is hardcoded hex colors (primary is #228be6 = Mantine blue).
MantineProvider themes the UI but Plotly charts are independent — they ignore CSS variables.

Goal: make chart palette respond to PRIMARY_COLOR env var.

Constraints:
- PRIMARY_COLOR is a Mantine color NAME (e.g. "blue", "violet", "teal") not a hex.
- Need a mapping from Mantine color name → hex for the primary slot of CATEGORICAL_PALETTE.
- Only swap index [0] (primary accent). Remaining 6 colors stay as-is unless PRIMARY_COLOR maps to one of them (avoid duplicates).
- ThemeConfig is already instantiated in app.py — pass it through to wherever CATEGORICAL_PALETTE is built, or build the palette lazily from ThemeConfig at import time.
- Do NOT hardcode a giant Mantine color table — map only the default palette colors (blue, violet, teal, green, yellow, orange, red, pink, cyan, grape, indigo, lime). Use their `5` shade hex values (the ones currently in theme.py).

---

### Task 2: Monaco editor with real DAX grammar

File: `pages/dax_query.py`
Problem: DAX editor is `dmc.Textarea` — no syntax highlighting, no line numbers.

#### Step 2a — Build the DAX grammar (run once, output is a static asset)

Create `scripts/build_dax_grammar.mjs`:
- Fetch `syntaxes/dax.tmLanguage.json` from `microsoft/powerbi-vscode` on GitHub (raw.githubusercontent.com)
- Convert TextMate → Monarch format using npm package `tm-to-monarch` (dev dependency only, never ships to prod)
- Wrap the output as a Monaco language registration call:
  ```js
  monaco.languages.register({ id: 'dax' });
  monaco.languages.setMonarchTokensProvider('dax', <converted grammar>);
  ```
- Write result to `assets/dax-monarch.js`

Run: `node scripts/build_dax_grammar.mjs`
Commit the generated `assets/dax-monarch.js`. Re-run once per year when DAX updates.
Add `tm-to-monarch` to package.json devDependencies (or run via `npx`).

#### Step 2b — Wire Monaco into the Dash page

Package: `dash-monaco-editor` (PyPI). Add to pyproject.toml dependencies.
If unmaintained/broken, fall back to injecting Monaco via CDN in `app.index_string` and wrapping with `html.Div` + clientside callbacks.

Component requirements:
- language: `"dax"` (registered via the grammar script above)
- theme: `"vs-dark"`
- value wired to existing callbacks via id `"dax-query-input"` — must keep this id so nothing else breaks
- height: ~300px
- Load `assets/dax-monarch.js` before Monaco initializes (use `app.clientside_callback` or script ordering in `index_string`)

VALIDATION_LAYOUT in `dax_query.py` must be updated to declare the new component id.

The existing clientside schema-insert callback does cursor-position injection into the textarea — verify it still works with Monaco's value model, update if needed.

---

### Task 3: Query export
File: `pages/dax_query.py` + `presentation/callbacks.py`
Problem: No way to download ag-Grid results.

Goal: add "Export CSV" button that downloads current grid data.

Approach:
- Add `dcc.Download(id="dax-query-download")` to layout and VALIDATION_LAYOUT
- Add `dmc.Button("Export CSV", id="dax-query-export", ...)` next to existing Run/Clear buttons
- Callback: Input("dax-query-export", "n_clicks") + State("dax-query-results", "rowData") → Output("dax-query-download", "data")
- Use `dcc.send_data_frame(df.to_csv, "query_results.csv", index=False)`
- Disable button when rowData is empty
- Style: `variant="subtle"`, `color="gray"`, `size="sm"` — matches existing Clear button

---

### Task 4: DAX autocomplete
Depends on Task 2 (Monaco) being done first.
File: `pages/dax_query.py`

Goal: schema-aware field suggestions while typing.

Approach:
- Schema is already loaded in `serve_layout` via `repo.fetch_schema()` — has table names, columns, measures
- Serialize to JSON, inject via `dcc.Store(id="dax-schema-store")` populated at layout render time
- Add to VALIDATION_LAYOUT
- Write a clientside callback that reads the store and calls `monaco.languages.registerCompletionItemProvider("dax", ...)`
- Completion items:
  - Tables → `'TableName'` (trigger: `'`)
  - Columns → `'TableName'[ColumnName]` (trigger: `[` after a table name)
  - Measures → `[MeasureName]` (trigger: `[`)
- CompletionItemKind: use `Field` for columns, `Function` for measures, `Module` for tables

If `registerCompletionItemProvider` isn't accessible via the Monaco package's JS API, document as blocked in `docs/ideas/white-label-bi-shell.md` Future Work and skip.

---

## Verification gates (AGENTS.md requirement — do not skip)

After ALL four tasks:
```
pyright
ruff check .
ruff format .
pytest tests/ --cov=domain --cov=application --cov=infrastructure --cov=presentation
```

Fix any failures before declaring done. Do not suppress type errors with `# type: ignore`.

## Files to read first (orientation)
- AGENTS.md
- presentation/theme.py
- presentation/callbacks.py (DAX execute section ~line 235)
- pages/dax_query.py
- config.py (ThemeConfig)
- pyproject.toml (to add Monaco dependency correctly)
