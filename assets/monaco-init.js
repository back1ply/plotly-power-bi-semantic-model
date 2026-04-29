// Initializes Monaco Editor on the DAX query page.
// Depends on: Monaco CDN loader (injected via app.index_string), dax-monarch.js
(function () {
  "use strict";

  function initMonacoEditor() {
    var container = document.getElementById("dax-editor-container");
    if (!container || window._dashMonacoEditor) return;

    // Wait for Monaco loader if not yet available
    if (!window.require) {
        setTimeout(initMonacoEditor, 100);
        return;
    }

    require.config({
      paths: {
        vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs",
      },
    });

    require(["vs/editor/editor.main"], function () {
      if (!monaco.languages.getLanguages().some(l => l.id === 'dax')) {
        monaco.languages.register({ id: "dax" });
      }

      // 1. Language Configuration
      monaco.languages.setLanguageConfiguration("dax", {
        comments: {
          lineComment: "--",
          blockComment: ["/*", "*/"],
        },
        brackets: [
          ["[", "]"],
          ["(", ")"],
          ["{", "}"],
        ],
        autoClosingPairs: [
          { open: "(", close: ")" },
          { open: "{", close: "}" },
          { open: '"', close: '"' },
        ],
      });

      // 2. Tokenizer (Monarch)
      if (window._daxMonarchTokens) {
        monaco.languages.setMonarchTokensProvider(
          "dax",
          window._daxMonarchTokens
        );
      }

      // 3. Expanded Completion Provider (Functions + Schema)
      monaco.languages.registerCompletionItemProvider("dax", {
        triggerCharacters: ["'", "[", ".", "(", " "],
        provideCompletionItems: function (model, position) {
          var word = model.getWordUntilPosition(position);
          var range = {
            startLineNumber: position.lineNumber,
            endLineNumber: position.lineNumber,
            startColumn: word.startColumn,
            endColumn: word.endColumn,
          };
          
          var items = [];
          
          // Add DAX Functions if we have the monarch tokens list
          if (window._daxMonarchTokens && window._daxMonarchTokens.keywords) {
            window._daxMonarchTokens.keywords.forEach(function(kw) {
              items.push({
                label: kw,
                kind: monaco.languages.CompletionItemKind.Function,
                insertText: kw + "(",
                command: { id: "editor.action.triggerSuggest", title: "Re-trigger suggestions" },
                range: range,
                sortText: "0_" + kw
              });
            });
          }

          var schema = window._daxSchemaData;
          if (schema && schema.tables) {
            var lineContent = model.getLineContent(position.lineNumber);
            var textBeforeCursor = lineContent.substring(0, position.column - 1);
            var isAfterTableQuote = /'[^']*$/.test(textBeforeCursor);
            var isAfterBracket = /\[[^\]]*$/.test(textBeforeCursor);

            schema.tables.forEach(function(table) {
              if (!isAfterBracket) {
                items.push({
                  label: "'" + table.name + "'",
                  kind: monaco.languages.CompletionItemKind.Module,
                  insertText: isAfterTableQuote ? table.name + "'" : "'" + table.name + "'",
                  detail: "Table",
                  range: range,
                  sortText: "1_" + table.name
                });
              }

              table.columns.forEach(function(col) {
                items.push({
                  label: col,
                  kind: monaco.languages.CompletionItemKind.Field,
                  insertText: isAfterBracket ? col + "]" : "[" + col + "]",
                  filterText: table.name + " " + col,
                  detail: "Column (" + table.name + ")",
                  range: range,
                  sortText: "2_" + table.name + "_" + col
                });
              });

              table.measures.forEach(function(measure) {
                items.push({
                  label: "[" + measure + "]",
                  kind: monaco.languages.CompletionItemKind.Method,
                  insertText: isAfterBracket ? measure + "]" : "[" + measure + "]",
                  filterText: measure,
                  detail: "Measure (" + table.name + ")",
                  range: range,
                  sortText: "3_" + measure
                });
              });
            });
          }

          return { suggestions: items };
        },
      });

      var editor = monaco.editor.create(container, {
        value: window._lastDaxValue || "",
        language: "dax",
        theme: "vs-dark",
        fontSize: 14,
        fontFamily: "Consolas, 'Courier New', monospace",
        automaticLayout: true,
        minimap: { enabled: false },
        wordWrap: "on",
        fixedOverflowWidgets: true,
        suggestOnTriggerCharacters: true,
        quickSuggestions: true,
        tabSize: 4,
        insertSpaces: true,
        detectIndentation: false, // Force our settings
        scrollBeyondLastLine: false,
        renderLineHighlight: "all",
        scrollbar: { vertical: "visible", horizontal: "visible" },
        // Accessibility and Tab handling
        tabIndex: 0,
        "semanticHighlighting.enabled": true
      });

      // Trap Tab key for indentation and prevent focus jumping out
      editor.onKeyDown(function(e) {
        if (e.keyCode === monaco.KeyCode.Tab && !e.ctrlKey && !e.metaKey) {
            // Monaco handles indentation by default, but we stop the event 
            // from bubbling to the browser/Dash to prevent layout shifts.
            e.stopPropagation();
        }
      });

      // Explicitly handle container resize for extra robustness in Dash
      if (window.ResizeObserver) {
        var ro = new ResizeObserver(function() {
            if (editor) editor.layout();
        });
        ro.observe(container);
      }

      window._dashMonacoEditor = editor;

      // Tracks the last value Monaco pushed to the store so we can ignore echoes.
      // Scoped here so it resets on each editor mount (e.g. after page navigation).
      window._isMonacoSettingValue = false;
      window._lastDaxValueSentToStore = "";

      var debounceTimer;
      editor.onDidChangeModelContent(function(e) {
          if (window._isMonacoSettingValue) return;

          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(function() {
              var val = editor.getValue();
              window._lastDaxValue = val;
              if (window.dash_clientside && window.dash_clientside.set_props) {
                  window._lastDaxValueSentToStore = val;
                  window.dash_clientside.set_props("dax-query-input", { data: val });
              }
          }, 200);
      });

      // Handle External Updates (Format, Clear, Schema-insert bouncing back via store).
      // Uses executeEdits instead of setValue to preserve undo history.
      window._updateMonacoFromExternal = function(data) {
          if (!editor || data === undefined || data === null) return;
          // Ignore values that Monaco itself last sent — prevents overwriting fast-typed input.
          if (data === window._lastDaxValueSentToStore) return;
          var currentVal = editor.getValue();
          if (currentVal === data) return;
          var model = editor.getModel();
          var fullRange = model.getFullModelRange();
          window._isMonacoSettingValue = true;
          editor.executeEdits('external-update', [{
              range: fullRange,
              text: data,
              forceMoveMarkers: true,
          }]);
          window._isMonacoSettingValue = false;
          var lastLine = model.getLineCount();
          editor.setPosition({ lineNumber: lastLine, column: model.getLineMaxColumn(lastLine) });
      };
    });
  }

  // Improved container watching
  function watchForContainer() {
    var observer = new MutationObserver(function (mutations, obs) {
      if (document.getElementById("dax-editor-container")) {
        initMonacoEditor();
      } else {
        // Cleanup if container gone
        if (window._dashMonacoEditor) {
            window._dashMonacoEditor.dispose();
            window._dashMonacoEditor = null;
        }
        window._daxCompletionRegistered = false;
      }
    });
    
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
    
    // Initial check
    if (document.getElementById("dax-editor-container")) {
        initMonacoEditor();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watchForContainer);
  } else {
    watchForContainer();
  }

  // Expose for Dash clientside callbacks
})();

