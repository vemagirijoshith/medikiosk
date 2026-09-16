/**
 * MediKiosk Runtime Configuration  v20260916c
 * ─────────────────────────────────────────────────────────────────────────────
 * Environment mapping (explicit — does NOT rely on window.location.port):
 *
 *   Local dev   →  http://127.0.0.1:8001
 *   Vercel prod →  https://medikiosk-yri0.onrender.com
 *
 * No secrets are stored here.
 * The Render backend URL is a public service endpoint — safe for client-side code.
 */
(function () {
  "use strict";

  var LOCAL_BACKEND      = "http://127.0.0.1:8001";
  var PRODUCTION_BACKEND = "https://medikiosk-yri0.onrender.com";

  // ── Explicit Vercel production hostnames ─────────────────────────────────
  // Any request from the canonical Vercel deployment or any *.vercel.app
  // preview branch MUST use the Render production backend — regardless of
  // port, user-agent, or any other signal.
  var hostname = (window.location.hostname || "").toLowerCase();
  var protocol = window.location.protocol;

  var isVercelDeployment =
    hostname === "medikiosk-ebon.vercel.app" ||
    hostname.endsWith(".vercel.app");

  // True ONLY when genuinely running on a developer's local machine.
  // Do NOT use window.location.port — Vercel always serves on standard port 443.
  var IS_LOCAL =
    !isVercelDeployment && (
      hostname === "localhost"    ||
      hostname === "127.0.0.1"   ||
      hostname === "0.0.0.0"     ||
      hostname.endsWith(".local") ||
      protocol === "file:"
    );

  // Unknown / staging hosts default to the production backend (safe fallback).
  var API_BASE = IS_LOCAL ? LOCAL_BACKEND : PRODUCTION_BACKEND;

  window.MEDIKIOSK_CONFIG = {
    API_BASE:           API_BASE,
    LOCAL_BACKEND:      LOCAL_BACKEND,
    PRODUCTION_BACKEND: PRODUCTION_BACKEND,
    IS_LOCAL:           IS_LOCAL,
    // Diagnostic fields — visible only in browser DevTools, never to patients
    _hostname:          hostname,
    _config_version:    "20260916c"
  };
})();
