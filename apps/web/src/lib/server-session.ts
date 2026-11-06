import { headers } from "next/headers";

/** Forward only the CloudSec Range session cookie to the internal API. */
export async function getSessionCookieHeader(): Promise<string | undefined> {
  const requestHeaders = await headers();
  const cookies = requestHeaders.get("cookie");
  if (!cookies) return undefined;

  const cookieName = process.env.SESSION_COOKIE_NAME ?? "csr_session";
  return cookies
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${cookieName}=`));
}
