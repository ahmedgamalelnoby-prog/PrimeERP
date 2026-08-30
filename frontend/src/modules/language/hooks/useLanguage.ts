import { useTranslation } from "react-i18next";

export function useLanguage() {
    const { t, i18n } = useTranslation();

    const language =
        i18n.resolvedLanguage ??
        i18n.language;

    const isArabic =
        language.startsWith("ar");

    const toggleLanguage = async () => {
        await i18n.changeLanguage(
            isArabic ? "en" : "ar",
        );
    };

    return {
        t,
        language,
        isArabic,
        toggleLanguage,
    };
}