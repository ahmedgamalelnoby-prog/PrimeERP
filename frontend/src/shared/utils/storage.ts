import { STORAGE_KEYS } from "../constants/storage";

export const storage = {

  getAccessToken() {
    return localStorage.getItem(
      STORAGE_KEYS.ACCESS_TOKEN
    );
  },

  getRefreshToken() {
    return localStorage.getItem(
      STORAGE_KEYS.REFRESH_TOKEN
    );
  },

  setTokens(
    access: string,
    refresh: string
  ) {
    localStorage.setItem(
      STORAGE_KEYS.ACCESS_TOKEN,
      access
    );

    localStorage.setItem(
      STORAGE_KEYS.REFRESH_TOKEN,
      refresh
    );
  },

  clear() {
    localStorage.removeItem(
      STORAGE_KEYS.ACCESS_TOKEN
    );

    localStorage.removeItem(
      STORAGE_KEYS.REFRESH_TOKEN
    );
  },

};