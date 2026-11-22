// Cloudflare Pages: tüm sayfaları şifreyle korur (HTTP Basic Auth).
// Şifre koda yazılmaz; Cloudflare'de gizli değişken olarak tutulur:
//   npx wrangler@3.114.0 pages secret put SITE_PASSWORD --project-name bistmd-tez
// Kullanıcı adı önemsizdir; yalnız şifre denetlenir. Şifre tanımlı değilse site hiç açılmaz.

function deny() {
  return new Response("Bu sayfa şifre ile korunuyor.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="BIST tez", charset="UTF-8"',
      "Content-Type": "text/plain; charset=utf-8",
      "X-Robots-Tag": "noindex, nofollow",
      "Cache-Control": "no-store",
    },
  });
}

function sameText(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function onRequest({ request, env, next }) {
  const expected = env.SITE_PASSWORD;
  if (!expected) return deny();
  const header = request.headers.get("Authorization") || "";
  if (!header.startsWith("Basic ")) return deny();
  let decoded = "";
  try {
    decoded = new TextDecoder().decode(Uint8Array.from(atob(header.slice(6)), (c) => c.charCodeAt(0)));
  } catch {
    return deny();
  }
  const password = decoded.slice(decoded.indexOf(":") + 1);
  if (!sameText(password, expected)) return deny();
  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set("X-Robots-Tag", "noindex, nofollow");
  return out;
}
