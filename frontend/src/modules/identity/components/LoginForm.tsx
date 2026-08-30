import {
  type FormEvent,
  useState,
} from "react";

import { useLogin } from "../hooks/useLogin";

export default function LoginForm() {
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [tenantSlug, setTenantSlug] = useState("");

  const {
    isSubmitting,
    errorMessage,
    submitLogin,
  } = useLogin();

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    if (!loginValue.trim() || !password) {
      return;
    }

    try {
      await submitLogin({
        login: loginValue,
        password,
        tenantSlug,
      });
    } catch {
      // يتم عرض الخطأ من خلال errorMessage.
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      <div>
        <label
          htmlFor="login"
          style={{
            display: "block",
            marginBottom: "6px",
            fontWeight: 600,
          }}
        >
          اسم المستخدم أو البريد الإلكتروني
        </label>

        <input
          id="login"
          name="login"
          type="text"
          autoComplete="username"
          value={loginValue}
          onChange={(event) =>
            setLoginValue(event.target.value)
          }
          disabled={isSubmitting}
          required
          style={{
            width: "100%",
            minHeight: "44px",
            padding: "10px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "8px",
            boxSizing: "border-box",
          }}
        />
      </div>

      <div>
        <label
          htmlFor="password"
          style={{
            display: "block",
            marginBottom: "6px",
            fontWeight: 600,
          }}
        >
          كلمة المرور
        </label>

        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) =>
            setPassword(event.target.value)
          }
          disabled={isSubmitting}
          required
          style={{
            width: "100%",
            minHeight: "44px",
            padding: "10px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "8px",
            boxSizing: "border-box",
          }}
        />
      </div>

      <div>
        <label
          htmlFor="tenantSlug"
          style={{
            display: "block",
            marginBottom: "6px",
            fontWeight: 600,
          }}
        >
          كود المؤسسة
        </label>

        <input
          id="tenantSlug"
          name="tenantSlug"
          type="text"
          value={tenantSlug}
          onChange={(event) =>
            setTenantSlug(event.target.value)
          }
          disabled={isSubmitting}
          placeholder="اختياري"
          style={{
            width: "100%",
            minHeight: "44px",
            padding: "10px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "8px",
            boxSizing: "border-box",
          }}
        />
      </div>

      {errorMessage && (
        <div
          role="alert"
          style={{
            padding: "10px 12px",
            borderRadius: "8px",
            backgroundColor: "#fee2e2",
            color: "#991b1b",
          }}
        >
          {errorMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={
          isSubmitting ||
          !loginValue.trim() ||
          !password
        }
        style={{
          minHeight: "44px",
          border: 0,
          borderRadius: "8px",
          padding: "10px 16px",
          fontWeight: 700,
          cursor: isSubmitting
            ? "not-allowed"
            : "pointer",
          opacity: isSubmitting ? 0.7 : 1,
        }}
      >
        {isSubmitting
          ? "جارٍ تسجيل الدخول..."
          : "تسجيل الدخول"}
      </button>
    </form>
  );
}