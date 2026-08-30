import { useState } from "react";
import axios from "axios";

import { useAuth } from "./useAuth";

interface LoginFormValues {
  login: string;
  password: string;
  tenantSlug: string;
}

export function useLogin() {
  const { login } = useAuth();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    null
  );

  const submitLogin = async ({
    login: loginValue,
    password,
    tenantSlug,
  }: LoginFormValues) => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await login(
        loginValue.trim(),
        password,
        tenantSlug.trim() || null
      );
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else if (
          Array.isArray(detail) &&
          detail.length > 0
        ) {
          setErrorMessage(
            detail
              .map((item) => item.msg)
              .filter(Boolean)
              .join(", ")
          );
        } else if (error.response?.status === 401) {
          setErrorMessage(
            "اسم المستخدم أو كلمة المرور غير صحيحة."
          );
        } else if (error.response?.status === 422) {
          setErrorMessage(
            "بيانات تسجيل الدخول غير مكتملة أو غير صحيحة."
          );
        } else {
          setErrorMessage(
            "تعذر الاتصال بالخادم. برجاء المحاولة مرة أخرى."
          );
        }
      } else {
        setErrorMessage(
          "حدث خطأ غير متوقع أثناء تسجيل الدخول."
        );
      }

      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    isSubmitting,
    errorMessage,
    submitLogin,
  };
}