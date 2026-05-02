// Schema-aware + DAX keyword completions for Ace Editor.
// Reads window._daxSchemaData populated by Dash schema-store callback.
(function () {
  "use strict";

  var _completerRegistered = false;

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
    var completions = DAX_KEYWORDS.map(function (kw) {
      return { value: kw, meta: "keyword", score: 1000 };
    });

    var schema = window._daxSchemaData;
    if (schema && schema.tables) {
      schema.tables.forEach(function (table) {
        completions.push({
          value: "'" + table.name + "'",
          meta: "table",
          score: 900,
        });
        (table.columns || []).forEach(function (col) {
          completions.push({
            value: "[" + col + "]",
            caption: col + " (" + table.name + ")",
            meta: "column",
            score: 800,
          });
        });
        (table.measures || []).forEach(function (m) {
          completions.push({
            value: "[" + m + "]",
            caption: m + " (" + table.name + ")",
            meta: "measure",
            score: 850,
          });
        });
      });
    }
    return completions;
  }

  // Expose insert-at-cursor for schema panel click callbacks.
  // Resolves the Ace instance fresh each call to survive SPA re-mounts.
  window._daxEditorInsert = function (expr) {
    var wrapperEl = document.getElementById("dax-editor");
    if (!wrapperEl) return;
    var aceInstance = ace.edit(wrapperEl);
    var cursor = aceInstance.getCursorPosition();
    var line = aceInstance.session.getLine(cursor.row);
    var before = line.substring(0, cursor.column);
    var sep = before && !/\s$/.test(before) ? " " : "";
    aceInstance.session.insert(cursor, sep + expr);
    aceInstance.focus();
  };

  function registerCompleter(aceInstance) {
    if (_completerRegistered) return;
    var langTools = ace.require("ace/ext/language_tools");
    if (!langTools) {
      console.warn("ace/ext/language_tools not available — DAX completions disabled");
      return;
    }
    langTools.addCompleter({
      getCompletions: function (editor, session, pos, prefix, callback) {
        callback(null, buildCompletions());
      },
    });
    _completerRegistered = true;
  }

  function applyCompletions(attempt) {
    attempt = attempt || 0;
    if (attempt > 50) return; // ~7.5s max wait
    var wrapperEl = document.getElementById("dax-editor");
    if (!wrapperEl) {
      setTimeout(function () { applyCompletions(attempt + 1); }, 150);
      return;
    }
    // dash-ace renders the editor into the wrapperEl directly
    var aceInstance = ace.edit(wrapperEl);
    window._daxAceEditor = aceInstance;
    registerCompleter(aceInstance);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { applyCompletions(0); });
  } else {
    applyCompletions(0);
  }
})();
