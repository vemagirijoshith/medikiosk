/**
 * MediKiosk Runtime Configuration
 * Handles environment-based API base URL selection for Local vs Production (Vercel -> Render).
 *
 * Local:      http://127.0.0.1:8001
 * Production: https://medikiosk-yri0.onrender.com
 *
 * Note: No secrets or credentials are stored here.
 * The Render backend URL is public and safe to expose in client-side code.
 */
(function () {
  const LOCAL_BACKEND = "http://127.0.0.1:8001";
  const PRODUCTION_BACKEND = "https://medikiosk-yri0.onrender.com";

  // Detect local development environment
  const hostname = window.location.hostname;
  const isLocal =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0" ||
    hostname === "" ||
    window.location.protocol === "file:" ||
    window.location.port === "8001";

  // When on Vercel (https://medikiosk-ebon.vercel.app) or any remote domain, route to Render backend
  const apiBase = isLocal
    ? (window.location.origin.includes(":8001") ? "" : LOCAL_BACKEND)
    : PRODUCTION_BACKEND;

  window.MEDIKIOSK_CONFIG = {
    API_BASE: apiBase,
    LOCAL_BACKEND: LOCAL_BACKEND,
    PRODUCTION_BACKEND: PRODUCTION_BACKEND,
    IS_LOCAL: isLocal,
  };
})();
