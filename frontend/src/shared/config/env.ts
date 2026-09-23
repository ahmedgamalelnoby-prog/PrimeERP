const configuredApiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, "");

const env = {
  API_BASE_URL: configuredApiUrl
    ? configuredApiUrl.endsWith("/api/v1")
      ? configuredApiUrl
      : `${configuredApiUrl}/api/v1`
    : "http://localhost:8001/api/v1",

  APP_NAME: import.meta.env.VITE_APP_NAME ?? "PrimeERP",
  APP_VERSION: import.meta.env.VITE_APP_VERSION ?? "1.0.0",
};

export default env;
