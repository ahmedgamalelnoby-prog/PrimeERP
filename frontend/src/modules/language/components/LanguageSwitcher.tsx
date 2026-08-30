import { Globe2 } from "lucide-react";
import { useLanguage } from "../hooks/useLanguage";

export default function LanguageSwitcher() {

    const {
        isArabic,
        toggleLanguage,
    } = useLanguage();

    return (

        <button
            type="button"
            onClick={toggleLanguage}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4"
        >

            <Globe2 className="size-4" />

            {isArabic
                ? "English"
                : "العربية"}

        </button>

    );

}