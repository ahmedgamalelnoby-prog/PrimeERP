import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, FileText, Loader2, ShieldCheck } from "lucide-react";

import { getLegalDocument, type LegalDocumentType } from "@/modules/legal/services/legal.service";

export default function LegalDocumentPage() {
  const { type } = useParams<{ type: LegalDocumentType }>();
  const documentType: LegalDocumentType = type === "privacy" ? "privacy" : "terms";
  const [document, setDocument] = useState<Awaited<ReturnType<typeof getLegalDocument>> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getLegalDocument(documentType)
      .then((data) => active && setDocument(data))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [documentType]);

  const isPrivacy = documentType === "privacy";
  const title = document ? document.title_ar : (isPrivacy ? "سياسة الخصوصية" : "شروط الاستخدام");
  const content = document?.content_ar ?? "";

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10" dir="rtl">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex items-center justify-between">
          <Link to="/login" className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700">
            <ArrowRight className="size-4" /> العودة لتسجيل الدخول
          </Link>
          <div className="flex items-center gap-2 text-sm font-bold text-slate-700">
            {isPrivacy ? <ShieldCheck className="size-5 text-blue-600" /> : <FileText className="size-5 text-blue-600" />}
            PrimeERP
          </div>
        </div>

        <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <header className="border-b border-slate-200 bg-slate-950 px-6 py-8 text-white sm:px-10">
            <p className="text-sm font-semibold text-blue-300">PrimeERP • المستند القانوني</p>
            <h1 className="mt-2 text-3xl font-bold">{title}</h1>
            {document && <p className="mt-2 text-sm text-slate-400">الإصدار {document.version}</p>}
          </header>

          <section className="px-6 py-8 sm:px-10 sm:py-10">
            {loading ? (
              <div className="flex min-h-64 items-center justify-center text-slate-500">
                <Loader2 className="me-2 size-5 animate-spin" /> جاري تحميل المستند...
              </div>
            ) : (
              <div className="whitespace-pre-wrap text-base leading-8 text-slate-700">
                {content}
              </div>
            )}
          </section>
        </article>
      </div>
    </main>
  );
}
