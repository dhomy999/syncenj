"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ADMIN_COOKIE, adminToken, cookieOptions, isAdminConfigured } from "./auth";

export type LoginState = { error?: string };

export async function login(
  _prev: LoginState,
  formData: FormData
): Promise<LoginState> {
  if (!isAdminConfigured()) {
    return { error: "لم يتم ضبط كلمة مرور الإدارة على الخادم (ADMIN_PASSWORD)" };
  }

  const entered = String(formData.get("password") || "");
  if (entered !== process.env.ADMIN_PASSWORD) {
    return { error: "كلمة المرور غير صحيحة" };
  }

  const store = await cookies();
  store.set(ADMIN_COOKIE, adminToken(), {
    ...cookieOptions,
    maxAge: 60 * 60 * 8, // 8 hours
  });

  redirect("/admin");
}

export async function logout(): Promise<void> {
  const store = await cookies();
  store.set(ADMIN_COOKIE, "", { ...cookieOptions, maxAge: 0 });
  redirect("/admin");
}
