# DAX Editor Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Monaco Editor with a Dash-native DAX editor that has zero sync race conditions, no CDN dependency, and proper syntax highlighting + schema autocomplete.

**Architecture:** A shared "Strip Monaco" task removes all current editor glue code. Then **choose one track**: Track A uses `dash-ace` (a published Dash component wrapping Ace Editor, simpler, 1-day effort) or Track B builds a custom CodeMirror 6 `DashComponent` (best-in-class, 2-3 day effort). Both tracks wire into the same Dash layout and callback structure — only the component import and one JS asset file differ post-migration.

**Tech Stack:**
- Track A: `dash-ace` (PyPI), Ace Editor custom mode (JS), existing `dcc.Store` for schema
- Track B: CodeMirror 6 npm packages, `dash-component-boilerplate` scaffold, React + TypeScript

---

## Shared Context (read before any task)

### File Map

| File | Status | Purpose |
|------|--------|---------|
| `assets/monaco-init.js` | **DELETE** | Monaco bootstrap, two-way sync, completions |
| `assets/dax-monarch.js` | **KEEP** | DAX keyword/operator list — source of truth for both tracks |
| `assets/dax-ace-mode.js` | **CREATE (Track A)** | Ace syntax mode for DAX |
| `assets/dax-ace-completions.js` | **CREATE (Track A)** | Ace custom completer wired to `window._daxSchemaData` |
| `components/dax_editor/` | **CREATE (Track B)** | Full CodeMirror 6 DashComponent package |
| `pages/dax_query.py` | **MODIFY** | Swap editor widget, remove `dax-editor-sync-ack` store |
| `presentation/callbacks.py` | **MODIFY** | Remove clientside sync callbacks; Execute reads `State("editor-id", "value")` directly |
| `app.py` | **MODIFY** | Remove Monaco CDN `<script>` tag from `index_string` |
| `tests/test_callbacks.py` | **MODIFY** | Update `State` references in Execute callback test |

### DAX Keywords (verbatim from `dax-monarch.js` — use in both tracks)

```javascript
const DAX_KEYWORDS = [
  "EVALUATE","RETURN","VAR","DEFINE","MEASURE","COLUMN","TABLE",
  "CALCULATE","CALCULATETABLE","FILTER","ALL","ALLEXCEPT","ALLSELECTED",
  "ALLNOBLANKROW","REMOVEFILTERS","KEEPFILTERS","USERELATIONSHIP","CROSSFILTER",
  "RELATED","RELATEDTABLE","SUMMARIZE","SUMMARIZECOLUMNS","ADDCOLUMNS",
  "SELECTCOLUMNS","TOPN","RANKX","ROW","UNION","INTERSECT","EXCEPT",
  "NATURALINNERJOIN","NATURALLEFTOUTERJOIN","GENERATE","GENERATEALL","CROSSJOIN",
  "VALUES","DISTINCT","HASONEFILTER","HASONEVALUE","SELECTEDVALUE","ISINSCOPE",
  "IF","IFERROR","SWITCH","COALESCE","NOT","AND","OR","IN","TRUE","FALSE","BLANK",
  "ISBLANK","ISERROR","ISLOGICAL","ISNUMBER","ISTEXT","ISNONTEXT","ISFILTERED",
  "ISCROSSFILTERED","HASONEVALUE","CONTAINSROW","CONTAINS",
  "SUM","SUMX","AVERAGE","AVERAGEX","MIN","MINX","MAX","MAXX","COUNT","COUNTA",
  "COUNTX","COUNTROWS","COUNTBLANK","DISTINCTCOUNT","DISTINCTCOUNTNOBLANK",
  "DIVIDE","ABS","CEILING","FLOOR","ROUND","ROUNDUP","ROUNDDOWN","TRUNC","INT",
  "MOD","POWER","SQRT","EXP","LOG","LOG10","LN","SIGN","RAND","RANDBETWEEN",
  "TODAY","NOW","DATE","TIME","YEAR","MONTH","DAY","HOUR","MINUTE","SECOND",
  "WEEKDAY","WEEKNUM","DATEDIFF","DATEADD","EDATE","EOMONTH","NETWORKDAYS",
  "CALENDARAUTO","CALENDAR","SAMEPERIODLASTYEAR","PARALLELPERIOD",
  "DATESINPERIOD","DATESBETWEEN","DATESMTD","DATESQTD","DATESYTD",
  "TOTALYTD","TOTALQTD","TOTALMTD","PREVIOUSDAY","PREVIOUSMONTH",
  "PREVIOUSQUARTER","PREVIOUSYEAR","NEXTDAY","NEXTMONTH","NEXTQUARTER","NEXTYEAR",
  "STARTOFMONTH","STARTOFQUARTER","STARTOFYEAR","ENDOFMONTH","ENDOFQUARTER","ENDOFYEAR",
  "FORMAT","CONCATENATE","CONCATENATEX","LEFT","RIGHT","MID","LEN","UPPER","LOWER",
  "TRIM","SUBSTITUTE","SEARCH","FIND","REPLACE","REPT","FIXED","TEXT","VALUE",
  "EXACT","CONTAINS","LOOKUPVALUE","EARLIER","EARLIEST","PATH","PATHITEM",
  "PATHITEMREVERSE","PATHCONTAINS","PATHLENGTH","TREATAS",
  "GENERATE","GENERATESERIES","SEQUENCE","SAMPLE"
];
```

### Callback Architecture (same for both tracks)

After migration the Execute server callback reads from `State("dax-editor", "value")` directly — no intermediate `dcc.Store("dax-query-input")` needed. Schema-insert clientside callback calls a global `window._daxEditorInsert(expr)` function exposed by the asset JS.

---

## Task 0 (Shared): Strip Monaco

**Files:**
- Delete: `assets/monaco-init.js`
- Modify: `app.py` (lines ~85-87)
- Modify: `pages/dax_query.py`
- Modify: `presentation/callbacks.py`

- [ ] **Step 1: Delete Monaco bootstrap**

```bash
rm "assets/monaco-init.js"
```

- [ ] **Step 2: Remove Monaco CDN from `app.py`**

In `app.py`, find the `index_string`. Remove this line:
```html
<script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs/loader.js"></script>
```
Leave the `powerbi-client` script tag in place.

- [ ] **Step 3: Strip the editor container and stores from `pages/dax_query.py`**

In `serve_layout()`, replace the hidden stores block:
```python
# REMOVE these two stores — no longer needed:
# dcc.Store(id="dax-query-input", data=""),
# dcc.Store(id="dax-editor-sync-ack", data=0),
# KEEP:
dcc.Store(id="dax-schema-store", data=schema_data),
dcc.Download(id="dax-query-download"),
```

Replace the `html.Div(id="dax-editor-container", ...)` with a temporary placeholder so the app still starts:
```python
html.Div(
    id="dax-editor-placeholder",
    children="Editor loading...",
    style={"height": "350px", "border": "1px solid gray"},
)
```

- [ ] **Step 4: Remove clientside sync callbacks from `presentation/callbacks.py`**

Inside `_register_dax_callbacks`, delete these three clientside callbacks entirely:
1. `Store → Monaco` sync (Output `"dax-editor-sync-ack"`, Input `"dax-query-input"`)
2. Schema-insert callback (Output `"dax-query-input"`, Input `{"type": "schema-insert", ...}`)
3. Schema-store callback (Output `"dax-editor-sync-ack"`, Input `"dax-schema-store"`)

Keep: `_execute_dax_query`, `_clear_dax_query`, `_export_dax_results`, `_toggle_export_button`, format+copy clientside callback.

Temporarily update `_execute_dax_query` State to avoid crash (will fix properly per track):
```python
# Temporarily stub — will be corrected in Track task
State("dax-schema-store", "data"),  # placeholder
```

- [ ] **Step 5: Verify app starts without errors**

```bash
python app.py
```
Expected: App runs, `/dax` page loads showing "Editor loading..." placeholder, no console JS errors.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: strip Monaco editor and sync glue code"
```

---

## TRACK A — dash-ace

### Task A1: Install `dash-ace` and basic integration

**Files:**
- Modify: `pyproject.toml`
- Modify: `pages/dax_query.py`
- Modify: `presentation/callbacks.py`

- [ ] **Step 1: Add dependency**

In `pyproject.toml`, under `[project] dependencies`, add:
```toml
"dash-ace>=0.0.5",
```

Install it:
```bash
pip install dash-ace
```

Verify:
```bash
python -c "import dash_ace; print(dash_ace.__version__)"
```
Expected: prints version, no ImportError.

- [ ] **Step 2: Replace placeholder with `DashAceEditor` in `pages/dax_query.py`**

Add import at the top:
```python
import dash_ace
```

Replace the `html.Div(id="dax-editor-placeholder", ...)` with:
```python
dash_ace.DashAceEditor(
    id="dax-editor",
    value="",
    mode="text",
    theme="monokai",
    tabSize=4,
    enableBasicAutocompletion=False,
    enableLiveAutocompletion=False,
    placeholder="EVALUATE\n    ROW(\"Value\", 1)",
    style={"height": "350px", "width": "100%", "fontSize": "14px"},
),
```

- [ ] **Step 3: Wire Execute to read from editor directly**

In `presentation/callbacks.py`, update `_execute_dax_query` signature:
```python
@app.callback(
    Output("dax-query-results", "rowData"),
    Output("dax-query-results", "columnDefs"),
    Output("dax-query-status", "children"),
    Input("dax-query-execute", "n_clicks"),
    State("dax-editor", "value"),          # <-- was dax-query-input
    prevent_initial_call=True,
)
@safe_callback
def _execute_dax_query(_: int, dax: str | None) -> tuple[list, list, str]:
    """Execute a DAX query against the semantic model and return results."""
    if not dax or not dax.strip():
        return [], [], "No query entered"
    error = validate_dax_query(dax)
    if error:
        return [], [], f"✗ {error}"
    t0 = time.perf_counter()
    try:
        rows = repo.query(dax.strip())
        elapsed = time.perf_counter() - t0
        if not rows:
            return [], [], f"✓ 0 rows · {elapsed:.2f}s"
        columns = list(rows[0].keys())
        col_defs = [{"field": col, "headerName": col} for col in columns]
        return rows, col_defs, f"✓ {len(rows):,} rows · {len(columns)} cols · {elapsed:.2f}s"
    except Exception as exc:
        return [], [], f"✗ {exc}"
```

- [ ] **Step 4: Wire Clear, Format, Copy to use `Output("dax-editor", "value")`**

Update the format+copy clientside callback output and the clear server callback:
```python
# Clear:
@app.callback(
    Output("dax-editor", "value"),
    Input("dax-query-clear", "n_clicks"),
    prevent_initial_call=True,
)
@safe_callback
def _clear_dax_query(_: int) -> str:
    return ""
```

Format+copy clientside callback — change outputs to `Output("dax-editor", "value", allow_duplicate=True)` and `Output("dax-query-status", "children")`, State to `State("dax-editor", "value")`.

- [ ] **Step 5: Run test suite**

```bash
pytest tests/ -x -q
```
Expected: all pass (no State ID mismatches).

- [ ] **Step 6: Browser smoke test**

Start app (`python app.py`), navigate to `/dax`. Verify:
- Editor renders with monokai theme
- Typing in editor works
- Execute runs (even with plain text mode, no syntax highlight yet)
- Clear empties editor

- [ ] **Step 7: Commit**

```bash
git add pages/dax_query.py presentation/callbacks.py pyproject.toml
git commit -m "feat: integrate dash-ace editor, wire callbacks to editor value"
```

---

### Task A2: DAX Syntax Highlighting Mode

**Files:**
- Create: `assets/dax-ace-mode.js`

Ace syntax modes are registered globally via `window.ace.define`. The rules below use regexes matching `dax-monarch.js` exactly.

- [ ] **Step 1: Create `assets/dax-ace-mode.js`**

```javascript
// DAX syntax mode for Ace Editor.
// Keywords sourced from dax-monarch.js — keep in sync.
(function() {
  "use strict";

  var keywords = (
    "EVALUATE|RETURN|VAR|DEFINE|MEASURE|COLUMN|TABLE|" +
    "CALCULATE|CALCULATETABLE|FILTER|ALL|ALLEXCEPT|ALLSELECTED|" +
    "ALLNOBLANKROW|REMOVEFILTERS|KEEPFILTERS|USERELATIONSHIP|CROSSFILTER|" +
    "RELATED|RELATEDTABLE|SUMMARIZE|SUMMARIZECOLUMNS|ADDCOLUMNS|" +
    "SELECTCOLUMNS|TOPN|RANKX|ROW|UNION|INTERSECT|EXCEPT|" +
    "NATURALINNERJOIN|NATURALLEFTOUTERJOIN|GENERATE|GENERATEALL|CROSSJOIN|" +
    "VALUES|DISTINCT|HASONEFILTER|HASONEVALUE|SELECTEDVALUE|ISINSCOPE|" +
    "IF|IFERROR|SWITCH|COALESCE|NOT|AND|OR|IN|TRUE|FALSE|BLANK|" +
    "ISBLANK|ISERROR|ISLOGICAL|ISNUMBER|ISTEXT|ISNONTEXT|ISFILTERED|" +
    "ISCROSSFILTERED|CONTAINSROW|CONTAINS|" +
    "SUM|SUMX|AVERAGE|AVERAGEX|MIN|MINX|MAX|MAXX|COUNT|COUNTA|" +
    "COUNTX|COUNTROWS|COUNTBLANK|DISTINCTCOUNT|DISTINCTCOUNTNOBLANK|" +
    "DIVIDE|ABS|CEILING|FLOOR|ROUND|ROUNDUP|ROUNDDOWN|TRUNC|INT|" +
    "MOD|POWER|SQRT|EXP|LOG|LOG10|LN|SIGN|RAND|RANDBETWEEN|" +
    "TODAY|NOW|DATE|TIME|YEAR|MONTH|DAY|HOUR|MINUTE|SECOND|" +
    "WEEKDAY|WEEKNUM|DATEDIFF|DATEADD|EDATE|EOMONTH|NETWORKDAYS|" +
    "CALENDARAUTO|CALENDAR|SAMEPERIODLASTYEAR|PARALLELPERIOD|" +
    "DATESINPERIOD|DATESBETWEEN|DATESMTD|DATESQTD|DATESYTD|" +
    "TOTALYTD|TOTALQTD|TOTALMTD|PREVIOUSDAY|PREVIOUSMONTH|" +
    "PREVIOUSQUARTER|PREVIOUSYEAR|NEXTDAY|NEXTMONTH|NEXTQUARTER|NEXTYEAR|" +
    "STARTOFMONTH|STARTOFQUARTER|STARTOFYEAR|ENDOFMONTH|ENDOFQUARTER|ENDOFYEAR|" +
    "FORMAT|CONCATENATE|CONCATENATEX|LEFT|RIGHT|MID|LEN|UPPER|LOWER|" +
    "TRIM|SUBSTITUTE|SEARCH|FIND|REPLACE|REPT|FIXED|TEXT|VALUE|" +
    "EXACT|LOOKUPVALUE|EARLIER|EARLIEST|PATH|PATHITEM|" +
    "PATHITEMREVERSE|PATHCONTAINS|PATHLENGTH|TREATAS|" +
    "GENERATESERIES|SEQUENCE|SAMPLE"
  );

  window.ace.define(
    "ace/mode/dax",
    ["require", "exports", "module",
     "ace/lib/oop",
     "ace/mode/text",
     "ace/mode/text_highlight_rules"],
    function(require, exports, module) {
      var oop = require("ace/lib/oop");
      var TextMode = require("ace/mode/text").Mode;
      var TextHighlightRules = require("ace/mode/text_highlight_rules").TextHighlightRules;

      var DaxHighlightRules = function() {
        this.$rules = {
          start: [
            { token: "comment",     regex: /--.*$/ },
            { token: "comment",     regex: /\/\*/, next: "block_comment" },
            { token: "string",      regex: /'[^']*'/ },       // 'Table Name'
            { token: "variable",    regex: /\[[^\]]*\]/ },    // [Column]
            { token: "string",      regex: /"(?:[^"\\]|\\.)*"/ },
            { token: "constant.numeric", regex: /\b\d+(?:\.\d+)?\b/ },
            {
              token: function(val) {
                return keywords.split("|").indexOf(val.toUpperCase()) >= 0
                  ? "keyword"
                  : "identifier";
              },
              regex: /[A-Za-z_]\w*/
            },
            { token: "keyword.operator", regex: /[=<>!&|+\-*\/^]+/ },
            { token: "paren.lparen",     regex: /[(]/ },
            { token: "paren.rparen",     regex: /[)]/ },
            { token: "punctuation",      regex: /[,;]/ }
          ],
          block_comment: [
            { token: "comment", regex: /\*\//, next: "start" },
            { token: "comment", regex: /[\s\S]/ }
          ]
        };
      };
      oop.inherits(DaxHighlightRules, TextHighlightRules);

      var Mode = function() {
        this.HighlightRules = DaxHighlightRules;
        this.lineCommentStart = "--";
        this.blockComment = { start: "/*", end: "*/" };
      };
      oop.inherits(Mode, TextMode);

      exports.Mode = Mode;
    }
  );

  // Set mode on the Ace instance once it exists
  function applyDaxMode() {
    var editorEl = document.getElementById("dax-editor");
    if (!editorEl) { setTimeout(applyDaxMode, 100); return; }
    var aceInstance = window.ace && window.ace.edit
      ? window.ace.edit(editorEl.querySelector(".ace_editor") || editorEl)
      : null;
    if (!aceInstance) { setTimeout(applyDaxMode, 100); return; }
    aceInstance.session.setMode("ace/mode/dax");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyDaxMode);
  } else {
    applyDaxMode();
  }
})();
```

- [ ] **Step 2: Update `DashAceEditor` to use dax mode in `pages/dax_query.py`**

Change `mode="text"` to `mode="dax"`:
```python
dash_ace.DashAceEditor(
    id="dax-editor",
    value="",
    mode="dax",        # <-- changed
    theme="monokai",
    tabSize=4,
    enableBasicAutocompletion=False,
    enableLiveAutocompletion=False,
    placeholder="EVALUATE\n    ROW(\"Value\", 1)",
    style={"height": "350px", "width": "100%", "fontSize": "14px"},
),
```

- [ ] **Step 3: Browser verify highlighting**

Start app, navigate to `/dax`. Type:
```
EVALUATE ROW("Col", [Measure])
```
Expected: `EVALUATE` and `ROW` highlighted as keywords, `[Measure]` as variable, `"Col"` as string. If mode fails to load (no highlight), check browser console for Ace define errors.

- [ ] **Step 4: Commit**

```bash
git add assets/dax-ace-mode.js pages/dax_query.py
git commit -m "feat: DAX syntax highlighting mode for Ace editor"
```

---

### Task A3: Schema Autocomplete

**Files:**
- Create: `assets/dax-ace-completions.js`
- Modify: `presentation/callbacks.py` (schema-store clientside callback)

`dash-ace` exposes Ace's completer API. We register a custom completer that reads `window._daxSchemaData` (populated by the existing schema-store clientside callback in `callbacks.py`).

- [ ] **Step 1: Create `assets/dax-ace-completions.js`**

```javascript
// Schema-aware + DAX keyword completions for Ace Editor.
// Reads window._daxSchemaData set by Dash schema-store callback.
(function() {
  "use strict";

  var DAX_KEYWORDS = [
    "EVALUATE","RETURN","VAR","DEFINE","MEASURE","COLUMN","TABLE",
    "CALCULATE","CALCULATETABLE","FILTER","ALL","ALLEXCEPT","ALLSELECTED",
    "ALLNOBLANKROW","REMOVEFILTERS","KEEPFILTERS","USERELATIONSHIP","CROSSFILTER",
    "RELATED","RELATEDTABLE","SUMMARIZE","SUMMARIZECOLUMNS","ADDCOLUMNS",
    "SELECTCOLUMNS","TOPN","RANKX","ROW","UNION","INTERSECT","EXCEPT",
    "NATURALINNERJOIN","NATURALLEFTOUTERJOIN","GENERATE","GENERATEALL","CROSSJOIN",
    "VALUES","DISTINCT","HASONEFILTER","HASONEVALUE","SELECTEDVALUE","ISINSCOPE",
    "IF","IFERROR","SWITCH","COALESCE","NOT","AND","OR","IN","TRUE","FALSE","BLANK",
    "ISBLANK","ISERROR","ISLOGICAL","ISNUMBER","ISTEXT","ISNONTEXT","ISFILTERED",
    "ISCROSSFILTERED","CONTAINSROW","CONTAINS",
    "SUM","SUMX","AVERAGE","AVERAGEX","MIN","MINX","MAX","MAXX","COUNT","COUNTA",
    "COUNTX","COUNTROWS","COUNTBLANK","DISTINCTCOUNT","DISTINCTCOUNTNOBLANK",
    "DIVIDE","ABS","CEILING","FLOOR","ROUND","ROUNDUP","ROUNDDOWN","TRUNC","INT",
    "MOD","POWER","SQRT","EXP","LOG","LOG10","LN","SIGN","RAND","RANDBETWEEN",
    "TODAY","NOW","DATE","TIME","YEAR","MONTH","DAY","HOUR","MINUTE","SECOND",
    "WEEKDAY","WEEKNUM","DATEDIFF","DATEADD","EDATE","EOMONTH","NETWORKDAYS",
    "CALENDARAUTO","CALENDAR","SAMEPERIODLASTYEAR","PARALLELPERIOD",
    "DATESINPERIOD","DATESBETWEEN","DATESMTD","DATESQTD","DATESYTD",
    "TOTALYTD","TOTALQTD","TOTALMTD","PREVIOUSDAY","PREVIOUSMONTH",
    "PREVIOUSQUARTER","PREVIOUSYEAR","NEXTDAY","NEXTMONTH","NEXTQUARTER","NEXTYEAR",
    "STARTOFMONTH","STARTOFQUARTER","STARTOFYEAR","ENDOFMONTH","ENDOFQUARTER","ENDOFYEAR",
    "FORMAT","CONCATENATE","CONCATENATEX","LEFT","RIGHT","MID","LEN","UPPER","LOWER",
    "TRIM","SUBSTITUTE","SEARCH","FIND","REPLACE","REPT","FIXED","TEXT","VALUE",
    "EXACT","LOOKUPVALUE","EARLIER","EARLIEST","PATH","PATHITEM",
    "PATHITEMREVERSE","PATHCONTAINS","PATHLENGTH","TREATAS",
    "GENERATESERIES","SEQUENCE","SAMPLE"
  ];

  function buildCompletions() {
    var completions = DAX_KEYWORDS.map(function(kw) {
      return { value: kw, meta: "keyword", score: 1000 };
    });

    var schema = window._daxSchemaData;
    if (schema && schema.tables) {
      schema.tables.forEach(function(table) {
        completions.push({ value: "'" + table.name + "'", meta: "table", score: 900 });
        (table.columns || []).forEach(function(col) {
          completions.push({
            value: "[" + col + "]",
            caption: col + " (" + table.name + ")",
            meta: "column",
            score: 800
          });
        });
        (table.measures || []).forEach(function(m) {
          completions.push({
            value: "[" + m + "]",
            caption: m + " (" + table.name + ")",
            meta: "measure",
            score: 850
          });
        });
      });
    }
    return completions;
  }

  function registerCompleter(aceInstance) {
    var langTools = window.ace.require("ace/ext/language_tools");
    langTools.addCompleter({
      getCompletions: function(editor, session, pos, prefix, callback) {
        callback(null, buildCompletions());
      }
    });
    aceInstance.setOptions({
      enableBasicAutocompletion: true,
      enableLiveAutocompletion: true,
    });
  }

  // Expose insert-at-cursor for schema panel click callbacks.
  window._daxEditorInsert = function(expr) {
    var aceInstance = window._daxAceEditor;
    if (!aceInstance) return;
    var cursor = aceInstance.getCursorPosition();
    var line = aceInstance.session.getLine(cursor.row);
    var before = line.substring(0, cursor.column);
    var sep = (before && !/[\s\n]$/.test(before)) ? " " : "";
    aceInstance.session.insert(cursor, sep + expr);
    aceInstance.focus();
  };

  function applyCompletions() {
    var editorEl = document.getElementById("dax-editor");
    if (!editorEl) { setTimeout(applyCompletions, 150); return; }
    var inner = editorEl.querySelector(".ace_editor");
    if (!inner) { setTimeout(applyCompletions, 150); return; }
    var aceInstance = window.ace.edit(inner);
    window._daxAceEditor = aceInstance;
    if (window.ace.require) {
      registerCompleter(aceInstance);
    } else {
      setTimeout(function() { registerCompleter(aceInstance); }, 300);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyCompletions);
  } else {
    applyCompletions();
  }
})();
```

- [ ] **Step 2: Re-add schema-store clientside callback in `presentation/callbacks.py`**

Inside `_register_dax_callbacks`, add:
```python
app.clientside_callback(
    """
    function(schemaData) {
        if (!schemaData || !schemaData.tables) return window.dash_clientside.no_update;
        window._daxSchemaData = schemaData;
        return window.dash_clientside.no_update;
    }
    """,
    Output("dax-schema-store", "data"),    # <-- writes back to same store (no-op value)
    Input("dax-schema-store", "data"),
    prevent_initial_call=False,
)
```

Wait — writing back to the same store as input creates a circular dependency. Use a dedicated ack store or a different output. Add `dcc.Store(id="dax-schema-ack", data=0)` to layout and use that as the output:

In `pages/dax_query.py`, add to hidden stores:
```python
dcc.Store(id="dax-schema-ack", data=0),
```

In `presentation/callbacks.py`:
```python
app.clientside_callback(
    """
    function(schemaData) {
        if (!schemaData || !schemaData.tables) return window.dash_clientside.no_update;
        window._daxSchemaData = schemaData;
        return window.dash_clientside.no_update;
    }
    """,
    Output("dax-schema-ack", "data"),
    Input("dax-schema-store", "data"),
    prevent_initial_call=False,
)
```

- [ ] **Step 3: Re-add schema-insert clientside callback**

In `presentation/callbacks.py` inside `_register_dax_callbacks`:
```python
app.clientside_callback(
    """
    function(nClicks) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }
        const anyClicked = nClicks && nClicks.some(function(n) { return n && n > 0; });
        if (!anyClicked) return window.dash_clientside.no_update;

        const propId = ctx.triggered[0].prop_id;
        const idStr = propId.substring(0, propId.lastIndexOf('.'));
        let expr = '';
        try { expr = JSON.parse(idStr).expr; } catch(e) {
            return window.dash_clientside.no_update;
        }
        if (!expr) return window.dash_clientside.no_update;

        if (window._daxEditorInsert) {
            window._daxEditorInsert(expr);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("dax-schema-ack", "data", allow_duplicate=True),
    Input({"type": "schema-insert", "expr": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
```

- [ ] **Step 4: Verify autocomplete in browser**

Navigate to `/dax`. Type `SU` — should show `SUM`, `SUMX`, `SUMMARIZE`, etc. in dropdown. Type `[` — should show column completions from schema.

- [ ] **Step 5: Commit**

```bash
git add assets/dax-ace-completions.js presentation/callbacks.py pages/dax_query.py
git commit -m "feat: schema-aware DAX autocomplete and schema-insert for Ace editor"
```

---

### Task A4: Update Tests

**Files:**
- Modify: `tests/test_callbacks.py`

- [ ] **Step 1: Update any test that references `"dax-query-input"` State**

Search for old store ID:
```bash
grep -rn "dax-query-input" tests/
```

For each match, replace `"dax-query-input"` with `"dax-editor"` in the State.

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -x -q
```
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "test: update DAX callback tests for Ace editor state IDs"
```

---

### Task A5: Cleanup

**Files:**
- Delete: `assets/dax-monarch.js` (optional — keep if you want keyword reference, it no longer does anything)
- Run: `pyright`, `ruff check .`, `ruff format .`

- [ ] **Step 1: Run validation gauntlet**

```bash
pyright && ruff check . && ruff format . && bandit -r . -c pyproject.toml
```
Expected: zero errors (Pyright "not accessed" warnings on `_update_active_nav` etc. are pre-existing Dash decorator false-positives, ignore them).

- [ ] **Step 2: Final browser test**

Navigate to `/dax`. Verify:
- Syntax highlighting (keywords colored)
- Autocomplete triggers on typing
- Schema panel click inserts at cursor
- Execute runs query and shows results
- Clear empties editor
- Format button reformats text
- Export CSV button enables after results appear

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: finalize dash-ace migration, remove monaco remnants"
```

---

---

## TRACK B — Custom CodeMirror 6 DashComponent

### Task B1: Scaffold the DashComponent Package

**Files:**
- Create: `components/dax_editor/` (entire package)

This uses `dash-component-boilerplate` to generate a React-based Dash component.

- [ ] **Step 1: Install scaffold tool**

```bash
pip install cookiecutter
```

- [ ] **Step 2: Generate component package**

```bash
cd components
cookiecutter gh:plotly/dash-component-boilerplate
```

Answer prompts:
```
project_name: dax_editor
author_name: <your name>
author_email: <your email>
github_org: local
description: CodeMirror 6 DAX editor Dash component
use_async: false
```

This creates `components/dax_editor/` with `src/lib/components/DaxEditor.react.js`, `dax_editor/__init__.py`, etc.

- [ ] **Step 3: Install JS deps**

```bash
cd components/dax_editor
npm install
npm install @codemirror/view @codemirror/state @codemirror/language \
  @codemirror/autocomplete @codemirror/commands @codemirror/theme-one-dark \
  @lezer/highlight
```

- [ ] **Step 4: Verify scaffold builds**

```bash
npm run build
```
Expected: `dax_editor/dax_editor.min.js` generated, no errors.

- [ ] **Step 5: Verify Python import**

```bash
cd ../..   # back to project root
pip install -e components/dax_editor
python -c "import dax_editor; print(dax_editor.__version__)"
```
Expected: version printed, no error.

- [ ] **Step 6: Commit scaffold**

```bash
git add components/dax_editor/
git commit -m "chore: scaffold CodeMirror 6 DashComponent package"
```

---

### Task B2: Implement Core Editor with DAX Syntax Highlighting

**Files:**
- Create: `components/dax_editor/src/lib/daxLanguage.js`
- Modify: `components/dax_editor/src/lib/components/DaxEditor.react.js`

- [ ] **Step 1: Create `daxLanguage.js`**

```javascript
// DAX language definition for CodeMirror 6 using StreamLanguage.
// Keywords verbatim from assets/dax-monarch.js.
import { StreamLanguage } from "@codemirror/language";
import { tags } from "@lezer/highlight";

const DAX_KEYWORDS = new Set([
  "EVALUATE","RETURN","VAR","DEFINE","MEASURE","COLUMN","TABLE",
  "CALCULATE","CALCULATETABLE","FILTER","ALL","ALLEXCEPT","ALLSELECTED",
  "ALLNOBLANKROW","REMOVEFILTERS","KEEPFILTERS","USERELATIONSHIP","CROSSFILTER",
  "RELATED","RELATEDTABLE","SUMMARIZE","SUMMARIZECOLUMNS","ADDCOLUMNS",
  "SELECTCOLUMNS","TOPN","RANKX","ROW","UNION","INTERSECT","EXCEPT",
  "NATURALINNERJOIN","NATURALLEFTOUTERJOIN","GENERATE","GENERATEALL","CROSSJOIN",
  "VALUES","DISTINCT","HASONEFILTER","HASONEVALUE","SELECTEDVALUE","ISINSCOPE",
  "IF","IFERROR","SWITCH","COALESCE","NOT","AND","OR","IN","TRUE","FALSE","BLANK",
  "ISBLANK","ISERROR","ISLOGICAL","ISNUMBER","ISTEXT","ISNONTEXT","ISFILTERED",
  "ISCROSSFILTERED","CONTAINSROW","CONTAINS",
  "SUM","SUMX","AVERAGE","AVERAGEX","MIN","MINX","MAX","MAXX","COUNT","COUNTA",
  "COUNTX","COUNTROWS","COUNTBLANK","DISTINCTCOUNT","DISTINCTCOUNTNOBLANK",
  "DIVIDE","ABS","CEILING","FLOOR","ROUND","ROUNDUP","ROUNDDOWN","TRUNC","INT",
  "MOD","POWER","SQRT","EXP","LOG","LOG10","LN","SIGN","RAND","RANDBETWEEN",
  "TODAY","NOW","DATE","TIME","YEAR","MONTH","DAY","HOUR","MINUTE","SECOND",
  "WEEKDAY","WEEKNUM","DATEDIFF","DATEADD","EDATE","EOMONTH","NETWORKDAYS",
  "CALENDARAUTO","CALENDAR","SAMEPERIODLASTYEAR","PARALLELPERIOD",
  "DATESINPERIOD","DATESBETWEEN","DATESMTD","DATESQTD","DATESYTD",
  "TOTALYTD","TOTALQTD","TOTALMTD","PREVIOUSDAY","PREVIOUSMONTH",
  "PREVIOUSQUARTER","PREVIOUSYEAR","NEXTDAY","NEXTMONTH","NEXTQUARTER","NEXTYEAR",
  "STARTOFMONTH","STARTOFQUARTER","STARTOFYEAR","ENDOFMONTH","ENDOFQUARTER","ENDOFYEAR",
  "FORMAT","CONCATENATE","CONCATENATEX","LEFT","RIGHT","MID","LEN","UPPER","LOWER",
  "TRIM","SUBSTITUTE","SEARCH","FIND","REPLACE","REPT","FIXED","TEXT","VALUE",
  "EXACT","LOOKUPVALUE","EARLIER","EARLIEST","PATH","PATHITEM",
  "PATHITEMREVERSE","PATHCONTAINS","PATHLENGTH","TREATAS",
  "GENERATESERIES","SEQUENCE","SAMPLE"
]);

const daxStream = {
  name: "dax",
  token(stream, state) {
    // Line comment
    if (stream.match(/--.*$/)) return "lineComment";
    // Block comment start
    if (stream.match("/*")) { state.inBlock = true; return "blockComment"; }
    if (state.inBlock) {
      if (stream.match("*/")) { state.inBlock = false; return "blockComment"; }
      stream.next();
      return "blockComment";
    }
    // Table reference: 'Name'
    if (stream.match(/'[^']*'/)) return "string2";
    // Column/measure reference: [Name]
    if (stream.match(/\[[^\]]*\]/)) return "variableName";
    // String literal: "..."
    if (stream.match(/"(?:[^"\\]|\\.)*"/)) return "string";
    // Number
    if (stream.match(/\d+(?:\.\d+)?/)) return "number";
    // Identifier or keyword
    if (stream.match(/[A-Za-z_]\w*/)) {
      return DAX_KEYWORDS.has(stream.current().toUpperCase()) ? "keyword" : "variableName2";
    }
    // Operator
    if (stream.match(/[=<>!&|+\-*\/^]+/)) return "operator";
    // Delimiter
    if (stream.match(/[(),;]/)) return "punctuation";
    stream.next();
    return null;
  },
  startState() { return { inBlock: false }; },
  blankLine(state) {},
  copyState(state) { return { inBlock: state.inBlock }; },
};

export const daxLanguage = StreamLanguage.define(daxStream);
```

- [ ] **Step 2: Implement `DaxEditor.react.js`**

```jsx
import React, { useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { EditorView, keymap, lineNumbers } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, indentWithTab } from "@codemirror/commands";
import { oneDark } from "@codemirror/theme-one-dark";
import { daxLanguage } from "../daxLanguage";

/**
 * DaxEditor: CodeMirror 6 DAX editor as a Dash component.
 * Props: value (string), schema (object), setProps (Dash callback).
 */
const DaxEditor = ({ id, value, schema, setProps, style }) => {
  const containerRef = useRef(null);
  const editorRef = useRef(null);
  const isExternalUpdate = useRef(false);

  // Build editor on mount
  useEffect(() => {
    if (!containerRef.current || editorRef.current) return;

    const updateListener = EditorView.updateListener.of((update) => {
      if (update.docChanged && !isExternalUpdate.current) {
        setProps({ value: update.state.doc.toString() });
      }
    });

    const state = EditorState.create({
      doc: value || "",
      extensions: [
        lineNumbers(),
        daxLanguage,
        oneDark,
        keymap.of([...defaultKeymap, indentWithTab]),
        updateListener,
        EditorView.lineWrapping,
      ],
    });

    editorRef.current = new EditorView({
      state,
      parent: containerRef.current,
    });

    // Expose insert-at-cursor globally for schema-panel callbacks
    window._daxEditorInsert = (expr) => {
      const view = editorRef.current;
      if (!view) return;
      const { from } = view.state.selection.main;
      const lineText = view.state.doc.lineAt(from).text;
      const col = from - view.state.doc.lineAt(from).from;
      const before = lineText.substring(0, col);
      const sep = (before && !/[\s\n]$/.test(before)) ? " " : "";
      view.dispatch({
        changes: { from, insert: sep + expr },
        selection: { anchor: from + sep.length + expr.length },
      });
      view.focus();
    };

    return () => {
      editorRef.current.destroy();
      editorRef.current = null;
    };
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  // Sync external value changes (Clear, Format)
  useEffect(() => {
    const view = editorRef.current;
    if (!view) return;
    const current = view.state.doc.toString();
    if (current === value) return;
    isExternalUpdate.current = true;
    view.dispatch({
      changes: { from: 0, to: current.length, insert: value || "" },
    });
    isExternalUpdate.current = false;
  }, [value]);

  return (
    <div
      id={id}
      ref={containerRef}
      style={{ height: "350px", fontSize: "14px", ...style }}
    />
  );
};

DaxEditor.defaultProps = { value: "", schema: null, style: {} };

DaxEditor.propTypes = {
  id: PropTypes.string,
  value: PropTypes.string,
  schema: PropTypes.object,
  setProps: PropTypes.func,
  style: PropTypes.object,
};

export default DaxEditor;
```

- [ ] **Step 3: Build and verify**

```bash
cd components/dax_editor && npm run build
```
Expected: build succeeds, `dax_editor/dax_editor.min.js` updated.

- [ ] **Step 4: Replace placeholder in `pages/dax_query.py`**

```python
import dax_editor as dax_editor_module

# In serve_layout, replace placeholder div with:
dax_editor_module.DaxEditor(
    id="dax-editor",
    value="",
    style={"height": "350px"},
),
```

- [ ] **Step 5: Wire Execute, Clear, Format callbacks (same as Task A1 Step 3-4)**

Follow exact same changes as Track A Task A1 Steps 3-4 — `State("dax-editor", "value")`, `Output("dax-editor", "value")`.

- [ ] **Step 6: Browser verify**

Navigate to `/dax`. Confirm dark theme, line numbers, DAX keyword highlighting, typing works, Execute works.

- [ ] **Step 7: Commit**

```bash
git add components/dax_editor/ pages/dax_query.py presentation/callbacks.py
git commit -m "feat: CodeMirror 6 DaxEditor component with DAX syntax highlighting"
```

---

### Task B3: Schema Autocomplete Extension

**Files:**
- Create: `components/dax_editor/src/lib/daxCompletions.js`
- Modify: `components/dax_editor/src/lib/components/DaxEditor.react.js`
- Modify: `presentation/callbacks.py`
- Modify: `pages/dax_query.py`

- [ ] **Step 1: Create `daxCompletions.js`**

```javascript
import { autocompletion, CompletionContext } from "@codemirror/autocomplete";

const DAX_KEYWORDS = [
  "EVALUATE","RETURN","VAR","DEFINE","CALCULATE","CALCULATETABLE","FILTER",
  "ALL","ALLEXCEPT","SUMMARIZE","SUMMARIZECOLUMNS","ADDCOLUMNS","SELECTCOLUMNS",
  "IF","IFERROR","SWITCH","NOT","AND","OR","IN","TRUE","FALSE","BLANK",
  "SUM","SUMX","AVERAGE","AVERAGEX","MIN","MAX","COUNT","COUNTROWS","DISTINCTCOUNT",
  "DIVIDE","RELATED","RELATEDTABLE","VALUES","DISTINCT","TOPN","RANKX",
  "FORMAT","CONCATENATE","LEFT","RIGHT","MID","LEN","UPPER","LOWER","TRIM",
  "TODAY","NOW","DATE","YEAR","MONTH","DAY","DATEDIFF","DATEADD",
  "TOTALYTD","TOTALQTD","TOTALMTD","SAMEPERIODLASTYEAR","PARALLELPERIOD",
  "ISBLANK","ISERROR","ISNUMBER","ISTEXT","LOOKUPVALUE","COALESCE","SELECTEDVALUE"
  // Full list is in daxLanguage.js DAX_KEYWORDS — import from there in production
];

function buildOptions(schema) {
  const options = DAX_KEYWORDS.map(kw => ({
    label: kw,
    type: "keyword",
    boost: 10,
  }));

  if (schema && schema.tables) {
    schema.tables.forEach(table => {
      options.push({ label: `'${table.name}'`, type: "class", boost: 9 });
      (table.columns || []).forEach(col => {
        options.push({
          label: `[${col}]`,
          detail: table.name,
          type: "property",
          boost: 8,
        });
      });
      (table.measures || []).forEach(m => {
        options.push({
          label: `[${m}]`,
          detail: `${table.name} (measure)`,
          type: "function",
          boost: 9,
        });
      });
    });
  }
  return options;
}

export function daxCompletionExtension(schemaRef) {
  return autocompletion({
    override: [
      (context) => {
        const word = context.matchBefore(/[\w'[\]]+/);
        if (!word && !context.explicit) return null;
        return {
          from: word ? word.from : context.pos,
          options: buildOptions(schemaRef.current),
        };
      },
    ],
  });
}
```

- [ ] **Step 2: Update `DaxEditor.react.js` to use completions**

Add import and `schemaRef` at top of file:
```jsx
import { daxCompletionExtension } from "../daxCompletions";

// Inside DaxEditor component, before useEffect:
const schemaRef = useRef(schema);
useEffect(() => { schemaRef.current = schema; }, [schema]);
```

In the `EditorState.create` extensions array, add:
```jsx
daxCompletionExtension(schemaRef),
```

Add `schema` to the component's `useEffect` dependency check — if schema changes, rebuild completions. Since `schemaRef` is a ref, no rebuild needed; completions read `schemaRef.current` live.

- [ ] **Step 3: Pass schema from Dash layout**

In `pages/dax_query.py`, update `DaxEditor`:
```python
dax_editor_module.DaxEditor(
    id="dax-editor",
    value="",
    schema=schema_data,   # <-- pass initial schema
    style={"height": "350px"},
),
```

No clientside callback needed — schema is static, passed at render time. Remove `dax-schema-ack` store.

- [ ] **Step 4: Build**

```bash
cd components/dax_editor && npm run build
```

- [ ] **Step 5: Browser verify completions**

Navigate to `/dax`. Type `SUM` — should show `SUM`, `SUMX`, `SUMMARIZE`. Type `[` — should show column/measure completions.

- [ ] **Step 6: Commit**

```bash
git add components/dax_editor/ pages/dax_query.py
git commit -m "feat: schema-aware autocomplete in CodeMirror 6 DaxEditor"
```

---

### Task B4: Schema-Insert from Panel

**Files:**
- Modify: `presentation/callbacks.py`
- Modify: `pages/dax_query.py`

- [ ] **Step 1: Add `dax-schema-ack` store to layout**

In `pages/dax_query.py`, hidden stores:
```python
dcc.Store(id="dax-schema-ack", data=0),
```

- [ ] **Step 2: Add schema-insert clientside callback**

In `presentation/callbacks.py` inside `_register_dax_callbacks`:
```python
app.clientside_callback(
    """
    function(nClicks) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }
        const anyClicked = nClicks && nClicks.some(function(n) { return n && n > 0; });
        if (!anyClicked) return window.dash_clientside.no_update;

        const propId = ctx.triggered[0].prop_id;
        const idStr = propId.substring(0, propId.lastIndexOf('.'));
        let expr = '';
        try { expr = JSON.parse(idStr).expr; } catch(e) {
            return window.dash_clientside.no_update;
        }
        if (!expr || !window._daxEditorInsert) return window.dash_clientside.no_update;
        window._daxEditorInsert(expr);
        return window.dash_clientside.no_update;
    }
    """,
    Output("dax-schema-ack", "data"),
    Input({"type": "schema-insert", "expr": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
```

- [ ] **Step 3: Browser verify insert**

Click a column badge in the schema panel while cursor is in editor. Confirm expression inserted at cursor position.

- [ ] **Step 4: Commit**

```bash
git add presentation/callbacks.py pages/dax_query.py
git commit -m "feat: schema-panel click-to-insert for CodeMirror 6 editor"
```

---

### Task B5: Tests and Validation

**Files:**
- Modify: `tests/test_callbacks.py`

- [ ] **Step 1: Update State ID references**

```bash
grep -rn "dax-query-input\|dax-editor-sync-ack" tests/
```

Replace all with `"dax-editor"` (value state) or remove ack references.

- [ ] **Step 2: Run full suite**

```bash
pytest tests/ -x -q
```
Expected: all pass.

- [ ] **Step 3: Run validation gauntlet**

```bash
pyright && ruff check . && ruff format . && bandit -r . -c pyproject.toml
```

- [ ] **Step 4: Final browser test**

Verify: syntax highlighting, autocomplete, schema insert, Execute, Clear, Format, Copy, Export CSV.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: CodeMirror 6 DaxEditor — complete, tested, validated"
```

---

## Decision Summary

| Criterion | dash-ace | CodeMirror 6 |
|-----------|----------|--------------|
| Effort | ~4 hours | ~2 days |
| CDN dependency | None (bundled) | None (npm) |
| Syntax highlighting | Good (Ace streams) | Excellent (Lezer) |
| Autocomplete UX | Basic (ext/language_tools) | Rich (CM6 API) |
| Undo/redo | Built-in | Built-in |
| React integration | Dash component (no hooks) | Full React lifecycle |
| Ongoing maintenance | Low | Low (modern codebase) |
| DAX mode exists | No (write it) | No (write it) |

**Choose Track A** if you want it done today.  
**Choose Track B** if DAX editor is a core feature users will live in.
