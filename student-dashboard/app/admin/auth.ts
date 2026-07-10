import { cookies } from "next/headers";
import { createHash } from "crypto";

export const ADMIN_COOKIE = "admin_auth";
const COOKIE_PATH = "/admin";

/** Token stored in the cookie — a hash of the password, never the password itself. */
export function adminToken(): string {
  const pw = process.env.ADMIN_PASSWORD || "";
  return createHash("sha256").update(`injaz-admin::${pw}`).digest("hex");
}

/** Whether an admin password is configured on the server at all. */
export function isAdminConfigured(): boolean {
  return Boolean(process.env.ADMIN_PASSWORD);
}

/** Read the auth cookie and check it matches the current password hash. */
export async function isAuthed(): Promise<boolean> {
  if (!isAdminConfigured()) return false;
  const store = await cookies();
  return store.get(ADMIN_COOKIE)?.value === adminToken();
}

export const cookieOptions = {
  httpOnly: true as const,
  sameSite: "lax" as const,
  path: COOKIE_PATH,
  secure: process.env.NODE_ENV === "production",
};
