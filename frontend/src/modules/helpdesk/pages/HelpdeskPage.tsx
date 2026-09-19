import { useState } from "react";
import { Bot, CheckCircle2, HelpCircle, Loader2, MessageCircle, Send, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import client from "@/shared/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface Message { role: "user" | "assistant"; content: string; actions?: string[]; }
interface Advice { summary:string; priorities:string[]; recommendations:string[]; next_steps:string[]; knowledge_version:string; ai_provider:string; }

export default function HelpdeskPage() {
  const { i18n } = useTranslation();
  const isArabic = (i18n.resolvedLanguage ?? i18n.language).toLowerCase().startsWith("ar");
  const text = (ar: string, en: string) => isArabic ? ar : en;
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [advice, setAdvice] = useState<Advice | null>(null);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const companyId = Number(localStorage.getItem("company_id")) || 0;

  const ask = async (value = question) => {
    const q = value.trim();
    if (!q || loading) return;
    if (!companyId) {
      setMessages(current => [...current, { role: "assistant", content: text("لا توجد شركة نشطة. اختر الشركة أولًا ثم أعد المحاولة.", "No active company is selected. Select a company first and try again.") }]);
      return;
    }
    setQuestion("");
    const next = [...messages, { role: "user" as const, content: q }];
    setMessages(next);
    setLoading(true);
    try {
      const response = await client.post<{ answer: string; suggested_actions: string[] }>("/helpdesk/ai/answer", {
        company_id: companyId,
        question: q,
        language: isArabic ? "ar" : "en",
        conversation: next.map(item => ({ role: item.role, content: item.content })),
      });
      setMessages(current => [...current, { role: "assistant", content: response.data.answer, actions: response.data.suggested_actions }]);
    } catch {
      setMessages(current => [...current, { role: "assistant", content: text("تعذر الوصول إلى مساعد الذكاء الاصطناعي حاليًا. حاول مرة أخرى أو افتح تذكرة دعم.", "The AI assistant is temporarily unavailable. Please try again or open a support ticket.") }]);
    } finally { setLoading(false); }
  };

  const getAdvice = async () => {
    if (!companyId || adviceLoading) return;
    setAdviceLoading(true);
    try {
      const response = await client.post<Advice>("/helpdesk/ai/advice", {
        company_id: companyId,
        language: isArabic ? "ar" : "en",
        focus: "general",
      });
      setAdvice(response.data);
    } catch {
      setMessages(current => [...current, { role: "assistant", content: text("تعذر إنشاء خطة التطوير الآن. تأكد من وجود بيانات الشركة ثم حاول مرة أخرى.", "Business advisory is temporarily unavailable. Verify the company data and try again.") }]);
    } finally { setAdviceLoading(false); }
  };

  const prompts = isArabic
    ? ["كيف أنشئ فاتورة مبيعات؟", "كيف أدير المخزون والمخازن؟", "ما الفرق بين الباقات والموديولات؟", "كيف أرسل تقريرًا عبر البريد أو WhatsApp؟"]
    : ["How do I create a sales invoice?", "How do I manage inventory?", "What is the difference between plans and modules?", "How can I send a report by email or WhatsApp?"];

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8" dir={isArabic ? "rtl" : "ltr"}>
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-xl sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-bold text-cyan-300"><Sparkles className="size-4" />Prime AI Help Desk</div>
              <h1 className="text-3xl font-black sm:text-4xl">{text("مساعد PrimeERP الذكي", "PrimeERP AI Help Desk")}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">{text("اسأل عن أي موديول أو عملية أو خطوة داخل النظام، وسيشرح لك المساعد الإجابة باللغة التي تفضلها.", "Ask about any PrimeERP module, workflow or procedure and get a guided answer in your preferred language.")}</p>
            </div>
            <div className="flex size-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-cyan-950/40"><Bot className="size-8" /></div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <Card className="overflow-hidden rounded-3xl border-slate-200 shadow-sm">
            <CardHeader className="border-b bg-white">
              <CardTitle className="flex items-center gap-2 text-base"><MessageCircle className="size-5 text-blue-600" />{text("محادثة المساعدة", "Help conversation")}</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="min-h-[420px] space-y-4 bg-white p-5 sm:p-7">
                {messages.length === 0 && (
                  <div className="flex min-h-[340px] flex-col items-center justify-center text-center">
                    <div className="flex size-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><HelpCircle className="size-8" /></div>
                    <h2 className="mt-5 text-xl font-bold">{text("كيف يمكنني مساعدتك؟", "How can I help?")}</h2>
                    <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{text("اختر سؤالًا جاهزًا أو اكتب سؤالك. المساعد مصمم لشرح PrimeERP وليس لطلب كلمات المرور أو الأسرار.", "Choose a suggested question or type your own. The assistant explains PrimeERP and never needs your passwords or secrets.")}</p>
                    <div className="mt-6 grid w-full max-w-2xl gap-2 sm:grid-cols-2">{prompts.map(prompt => <button key={prompt} type="button" onClick={() => void ask(prompt)} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-start text-xs font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50">{prompt}</button>)}</div>
                  </div>
                )}
                {messages.map((message, index) => (
                  <div key={index} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
                    <div className={message.role === "user" ? "max-w-[85%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-3 text-sm leading-6 text-white" : "max-w-[90%] rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-800"}>
                      <div className="mb-1 text-[10px] font-bold opacity-60">{message.role === "user" ? text("أنت", "You") : "Prime AI"}</div>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      {message.actions?.length ? <div className="mt-3 space-y-1 border-t border-slate-200 pt-2 text-xs text-slate-500">{message.actions.map(action => <div key={action} className="flex gap-2"><CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-600" />{action}</div>)}</div> : null}
                    </div>
                  </div>
                ))}
                {loading && <div className="flex justify-start"><div className="rounded-2xl rounded-bl-md bg-slate-50 px-4 py-3 text-sm text-slate-500"><Loader2 className="inline size-4 animate-spin" /> <span className="ms-2">{text("جاري التفكير...", "Thinking...")}</span></div></div>}
              </div>
              <div className="border-t bg-white p-4 sm:p-5">
                <form onSubmit={e => { e.preventDefault(); void ask(); }} className="flex gap-2">
                  <Input value={question} onChange={e => setQuestion(e.target.value)} placeholder={text("اكتب سؤالك عن PrimeERP...", "Ask PrimeERP anything...")} disabled={loading} className="h-12 rounded-xl" />
                  <Button type="submit" disabled={loading || !question.trim()} className="h-12 rounded-xl px-5"><Send className="size-4" /></Button>
                </form>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card className="rounded-3xl border-slate-200 shadow-sm"><CardContent className="p-5">
              <h3 className="font-bold">{text("ما الذي يستطيع المساعد فعله؟", "What can the assistant do?")}</h3>
              <ul className="mt-4 space-y-3 text-sm text-slate-600">
                {[text("شرح الموديولات ووظائفها", "Explain modules and their purpose"), text("شرح خطوات تنفيذ العمليات", "Guide users through workflows"), text("اقتراح المكان الصحيح داخل النظام", "Point to the right area of the system"), text("الإجابة بالعربية أو الإنجليزية", "Answer in Arabic or English")].map(item => <li key={item} className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" />{item}</li>)}
              </ul>
            </CardContent></Card>
            <Card className="rounded-3xl border-violet-100 bg-violet-50/60 shadow-sm"><CardContent className="p-5">
              <div className="flex items-center justify-between gap-3"><h3 className="font-bold text-violet-950">{text("مستشار تطوير الأعمال", "Business improvement advisor")}</h3><Sparkles className="size-4 text-violet-600" /></div>
              <p className="mt-2 text-xs leading-6 text-violet-900/70">{text("حلل البيانات المالية الحالية واحصل على أولويات وتوصيات وخطوات قابلة للتنفيذ.", "Analyze the live financial snapshot and get priorities, recommendations and actionable next steps.")}</p>
              <Button type="button" onClick={() => void getAdvice()} disabled={adviceLoading || !companyId} className="mt-4 w-full rounded-xl">{adviceLoading ? text("جارٍ التحليل...", "Analyzing...") : text("إنشاء خطة تطوير", "Create improvement plan")}</Button>
              {advice && <div className="mt-4 space-y-3 border-t border-violet-200 pt-4 text-xs text-violet-950">
                <p className="font-semibold leading-5">{advice.summary}</p>
                <div><div className="font-bold">{text("الأولويات", "Priorities")}</div>{advice.priorities.map(x=><div key={x} className="mt-1">• {x}</div>)}</div>
                <div><div className="font-bold">{text("التوصيات", "Recommendations")}</div>{advice.recommendations.slice(0,4).map(x=><div key={x} className="mt-1">• {x}</div>)}</div>
                <div className="text-[10px] text-violet-700/70">Knowledge {advice.knowledge_version} · {advice.ai_provider}</div>
              </div>}
            </CardContent></Card>
            <Card className="rounded-3xl border-blue-100 bg-blue-50/60 shadow-sm"><CardContent className="p-5"><h3 className="font-bold text-blue-950">{text("ملاحظة أمنية", "Security note")}</h3><p className="mt-2 text-xs leading-6 text-blue-900/70">{text("لا ترسل كلمة المرور أو Access Token أو مفاتيح API أو بيانات سرية للمساعد.", "Never send passwords, access tokens, API keys or other secrets to the assistant.")}</p></CardContent></Card>
          </div>
        </div>
      </div>
    </div>
  );
}
