// API base URL is injected at build time via REACT_APP_API_URL.
// When running behind the nginx reverse proxy (Docker), leave it empty so all
// API calls go to the same origin and nginx routes them to the backend service.
// For local development without Docker, set REACT_APP_API_URL=http://localhost:8080
// in a frontend/.env.local file.
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

export default API_BASE_URL;
