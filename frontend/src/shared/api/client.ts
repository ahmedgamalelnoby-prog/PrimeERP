import axios from "axios";

import env from "../config/env";

const client = axios.create({
  baseURL: env.API_BASE_URL,

  timeout: 30000,

  headers: {
    "Content-Type": "application/json",

    Accept: "application/json",
  },
});

export default client;