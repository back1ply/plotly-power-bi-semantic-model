/**
 * Power BI Embedded report initializer.
 *
 * Watches for navigation to /embed, fetches an embed token from the
 * Flask /api/embed-config endpoint, and calls powerbi.embed() to render
 * the report inside #embed-container.
 */
(function () {
  "use strict";

  var EMBED_PATH = "/embed";
  var CONTAINER_ID = "embed-container";
  var DATA_ATTR = "pbi-initialized";

  function updateLoading(visible) {
    // We try to find the Mantine loading overlay. 
    // In Dash, ID might be slightly transformed or nested.
    var loader = document.getElementById("pbi-embed-loading");
    if (loader) {
        loader.style.display = visible ? "block" : "none";
    }
  }

  function initEmbed(force) {
    var container = document.getElementById(CONTAINER_ID);
    if (!container) return;
    
    if (!force && container.getAttribute(DATA_ATTR)) return;

    var powerbi = window.powerbi;
    if (!powerbi) {
      // If not loaded yet, wait and retry once
      console.warn("[embed_init] powerbi-client not loaded yet, retrying in 500ms...");
      setTimeout(function() { initEmbed(force); }, 500);
      return;
    }

    // Guard: mark immediately to prevent double-init on rapid mutations
    container.setAttribute(DATA_ATTR, "true");
    updateLoading(true);

    fetch("/api/embed-config")
      .then(function (r) {
        if (!r.ok) throw new Error("embed-config HTTP " + r.status);
        return r.json();
      })
      .then(function (cfg) {
        var pbiClient = window['powerbi-client'];
        var models = (pbiClient && pbiClient.models) || powerbi.models;
        
        if (!models) {
            throw new Error("Power BI models not found. Check if powerbi-client is correctly loaded.");
        }

        var config = {
          type: "report",
          tokenType: models.TokenType.Embed,
          accessToken: cfg.accessToken,
          embedUrl: cfg.embedUrl,
          id: cfg.reportId,
          settings: {
            panes: {
              filters: { visible: false },
              pageNavigation: { visible: true },
            },
            background: models.BackgroundType.Transparent,
          },
        };
        
        // Reset container if forcing
        if (force) {
            powerbi.reset(container);
        }

        var report = powerbi.embed(container, config);
        
        report.on("loaded", function() {
            updateLoading(false);
            console.log("[embed_init] Report loaded");
        });

        report.on("error", function(event) {
            console.error("[embed_init] Report error:", event.detail);
            updateLoading(false);
        });
      })
      .catch(function (err) {
        console.error("[embed_init] Failed to embed report:", err);
        // Don't overwrite if we already have an error message displayed
        if (container.innerHTML.indexOf("Report Loading Failed") === -1) {
            container.innerHTML =
              '<div style="color:red;padding:2rem;text-align:center;">' +
              '<h3>Report Loading Failed</h3>' +
              '<p>' + err.message + "</p>" +
              '<button onclick="window._pbiInitEmbed(true)" style="margin-top:1rem;padding:0.5rem 1rem;cursor:pointer;">Retry</button>' +
              '</div>';
        }
        updateLoading(false);
        // We do NOT remove DATA_ATTR here to prevent the MutationObserver from 
        // triggering an infinite loop when we update innerHTML.
        // The user can still retry via the button which passes force=true.
      });
}

  // Observe DOM mutations to detect Dash SPA navigation to /embed
  var observer = new MutationObserver(function () {
    if (window.location.pathname === EMBED_PATH) {
      // Delay slightly to ensure the container is in the DOM
      setTimeout(function() { initEmbed(false); }, 100);
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Expose for Dash callbacks
  window._pbiInitEmbed = initEmbed;
})();
