import { useEffect, useState } from "react";
import { Save, ShieldCheck, FileText, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

import { getLegalDocument, updateLegalDocument, type LegalDocument, type LegalDocumentType } from "@/modules/legal/services/legal.service";

export default function LegalManagementPage() {
  const [type, setType] = useState<LegalDocumentType>("terms");
  const [document, setDocument] = useState<LegalDocument | null>(null);
  const [form, setForm] = useState({ title_ar: "", title_en: "", content_ar: "", content_en: "", is_published: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = async (nextType: LegalDocumentType) => {
    setLoading(true);
    try {
      const data = await getLegalDocument(nextType);
      setDocument(data);
      setForm({
        title_ar: data.title_ar,
        title_en: data.title_en,
        content_ar: data.content_ar,
        content_en: data.content_en,
        is_published: data.is_published,
      });
    } catch (error) {
      console.error(error);
      toast.error("تعذر تحميل المستند القانوني");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(type); }, [type]);

  const save = async () => {
    setSaving(true);
    try {
      const data = await updateLegalDocument(type, form);
      setDocument(data);
      toast.success(`تم حفظ ${type === "terms" ? "شروط الاستخدام" : "سياسة الخصوصية"} — الإصدار ${data.version}`);
    } catch (error) {
      console.error(error);
      toast.error("تعذر حفظ المستند. تأكد من صلاحيات مدير النظام.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="p-6" dir="rtl">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-600">إعدادات النظام</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-950">المستندات القانونية</h1>
          <p className="mt-2 text-sm text-slate-500">إدارة شروط الاستخدام وسياسة الخصوصية التي تظهر للمستخدمين قبل الدخول.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl border bg-white p-3 shadow-sm">
            <button onClick={() => setType("terms")} className={`mb-2 flex w-full items-center gap-3 rounded-xl px-4 py-3 text-right text-sm font-semibold ${type === "terms" ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50"}`}>
              <FileText className="size-5" /> شروط الاستخدام
            </button>
            <button onClick={() => setType("privacy")} className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-right text-sm font-semibold ${type === "privacy" ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50"}`}>
              <ShieldCheck className="size-5" /> سياسة الخصوصية
            </button>
          </aside>

          <section className="rounded-2xl border bg-white p-6 shadow-sm">
            {loading ? (
              <div className="flex min-h-96 items-center justify-center text-slate-500"><Loader2 className="me-2 size-5 animate-spin" /> جاري التحميل...</div>
            ) : (
              <div className="space-y-5">
                <div className="flex items-center justify-between gap-4 border-b pb-5">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">{type === "terms" ? "شروط الاستخدام" : "سياسة الخصوصية"}</h2>
                    {document && <p className="mt-1 text-xs text-slate-400">الإصدار الحالي: {document.version}</p>}
                  </div>
                  <label className="flex items-center gap-2 text-sm text-slate-600">
                    <input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} /> منشور للمستخدمين
                  </label>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <input className="h-11 rounded-lg border px-3" value={form.title_ar} onChange={(e) => setForm({ ...form, title_ar: e.target.value })} placeholder="العنوان بالعربية" />
                  <input className="h-11 rounded-lg border px-3" value={form.title_en} onChange={(e) => setForm({ ...form, title_en: e.target.value })} placeholder="English title" dir="ltr" />
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">المحتوى بالعربية</label>
                    <textarea className="min-h-[420px] w-full rounded-xl border p-4 leading-7 outline-none focus:ring-2 focus:ring-blue-200" value={form.content_ar} onChange={(e) => setForm({ ...form, content_ar: e.target.value })} />
                  </div>
                  <div dir="ltr">
                    <label className="mb-2 block text-sm font-semibold text-slate-700">English content</label>
                    <textarea className="min-h-[420px] w-full rounded-xl border p-4 leading-7 outline-none focus:ring-2 focus:ring-blue-200" value={form.content_en} onChange={(e) => setForm({ ...form, content_en: e.target.value })} />
                  </div>
                </div>

                <div className="flex justify-end border-t pt-5">
                  <button onClick={() => void save()} disabled={saving} className="inline-flex h-11 items-center gap-2 rounded-lg bg-blue-600 px-6 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50">
                    {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} حفظ ونشر إصدار جديد
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
