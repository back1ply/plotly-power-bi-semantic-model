// DAX syntax mode for Ace Editor.
// Keywords match assets/dax-ace-completions.js — keep both in sync.
(function () {
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

  var keywordSet = {};
  keywords.split("|").forEach(function (k) { keywordSet[k] = true; });

  ace.define(
    "ace/mode/dax",
    [
      "require", "exports", "module",
      "ace/lib/oop",
      "ace/mode/text",
      "ace/mode/text_highlight_rules",
    ],
    function (require, exports, module) {
      var oop = require("ace/lib/oop");
      var TextMode = require("ace/mode/text").Mode;
      var TextHighlightRules =
        require("ace/mode/text_highlight_rules").TextHighlightRules;

      var DaxHighlightRules = function () {
        this.$rules = {
          start: [
            // Line comment --
            { token: "comment", regex: /--.*$/ },
            // Block comment start
            { token: "comment", regex: /\/\*/, next: "block_comment" },
            // Table reference: 'Table Name' — doubled '' escapes single quotes inside names
            { token: "string", regex: /'(?:[^']|'')*'/ },
            // Column / measure reference: [Field]
            { token: "variable", regex: /\[[^\]]*\]/ },
            // String literal: "..."
            { token: "string", regex: /"(?:[^"\\]|\\.)*"/ },
            // Number
            { token: "constant.numeric", regex: /\b\d+(?:\.\d+)?\b/ },
            // Identifier or keyword (case-insensitive)
            {
              token: function (val) {
                return keywordSet[val.toUpperCase()] ? "keyword" : "identifier";
              },
              regex: /[A-Za-z_]\w*/,
            },
            // Operator
            { token: "keyword.operator", regex: /[=<>!&|+\-*\/^]+/ },
            // Parens
            { token: "paren.lparen", regex: /[(]/ },
            { token: "paren.rparen", regex: /[)]/ },
            // Punctuation
            { token: "punctuation", regex: /[,;]/ },
          ],
          block_comment: [
            { token: "comment", regex: /\*\//, next: "start" },
            { token: "comment", regex: /(?:[^*]|\*(?!\/))+/ },
          ],
        };
      };
      oop.inherits(DaxHighlightRules, TextHighlightRules);

      var Mode = function () {
        this.HighlightRules = DaxHighlightRules;
        this.lineCommentStart = "--";
        this.blockComment = { start: "/*", end: "*/" };
      };
      oop.inherits(Mode, TextMode);

      exports.Mode = Mode;
    }
  );
})();
