import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import arTranslation from "./locales/ar/translation";
import enTranslation from "./locales/en/translation";

const LANGUAGE_STORAGE_KEY =
  "primeerp_language";

const supportedLanguages = [
  "en",
  "ar",
] as const;

type SupportedLanguage =
  (typeof supportedLanguages)[number];

function getSavedLanguage(): SupportedLanguage {
  const savedLanguage =
    localStorage.getItem(
      LANGUAGE_STORAGE_KEY,
    );

  if (savedLanguage === "ar") {
    return "ar";
  }

  return "en";
}

function updateDocumentLanguage(
  language: string,
): void {
  const isArabic =
    language
      .toLowerCase()
      .startsWith("ar");

  document.documentElement.lang =
    isArabic ? "ar" : "en";

  document.documentElement.dir =
    isArabic ? "rtl" : "ltr";

  document.body.dir =
    isArabic ? "rtl" : "ltr";
}

const initialLanguage =
  getSavedLanguage();

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation:
          enTranslation,
      },

      ar: {
        translation:
          arTranslation,
      },
    },

    lng: initialLanguage,
    fallbackLng: "en",

    supportedLngs: [
      ...supportedLanguages,
    ],

    interpolation: {
      escapeValue: false,
    },

    react: {
      useSuspense: false,
    },
  });

updateDocumentLanguage(
  initialLanguage,
);

i18n.on(
  "languageChanged",
  (language: string) => {
    const normalizedLanguage =
      language
        .toLowerCase()
        .startsWith("ar")
        ? "ar"
        : "en";

    localStorage.setItem(
      LANGUAGE_STORAGE_KEY,
      normalizedLanguage,
    );

    updateDocumentLanguage(
      normalizedLanguage,
    );
  },
);

export default i18n;