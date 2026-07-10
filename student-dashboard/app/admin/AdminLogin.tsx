"use client";

import { useActionState } from "react";
import { login, type LoginState } from "./actions";

const initialState: LoginState = {};

export default function AdminLogin({ configured }: { configured: boolean }) {
  const [state, formAction, pending] = useActionState(login, initialState);

  return (
    <div className="admin-login">
      <form action={formAction} className="admin-login-card">
        <div className="admin-login-icon">🔐</div>
        <h1 className="admin-login-title">لوحة الإدارة</h1>
        <p className="admin-login-sub">أدخل كلمة المرور للمتابعة</p>

        <input
          type="password"
          name="password"
          placeholder="كلمة المرور"
          className="admin-input"
          autoFocus
          required
          disabled={!configured}
        />

        {state.error && <div className="admin-login-error">{state.error}</div>}
        {!configured && (
          <div className="admin-login-error">
            لم يتم ضبط متغير ADMIN_PASSWORD في ملف البيئة.
          </div>
        )}

        <button type="submit" className="admin-btn admin-btn-primary" disabled={pending || !configured}>
          {pending ? "جارٍ التحقق…" : "دخول"}
        </button>
      </form>
    </div>
  );
}
