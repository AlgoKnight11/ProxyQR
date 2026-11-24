// Configuration for API Endpoints
const CONFIG = {
  API_BASE: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "" 
    : "https://proxyqr-vigz.onrender.com"
};

function getApiUrl(path) {
  const base = (CONFIG.API_BASE || "").trim().replace(/\/$/, "");
  return `${base}${path}`;
}
