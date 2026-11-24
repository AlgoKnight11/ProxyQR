// Configuration for API Endpoints
// In local development, leave API_BASE empty to use the same host.
// In Netlify production, set this to your deployed backend URL (e.g. "https://api.yourdomain.com")
const CONFIG = {
  API_BASE: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "" 
    : "" // Replace with backend URL when deployed to Netlify (e.g. "https://proxyqr-backend.onrender.com")
};

function getApiUrl(path) {
  return `${CONFIG.API_BASE}${path}`;
}
