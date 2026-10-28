// KOICA 대시보드 방문 기록기 (Cloudflare Pages Function, route: /px)
// 방문 1건당 KV에 키 1개 기록: h|날짜(KST)|국가|기기|브라우저|유입호스트|난수
// 저장 항목은 날짜·국가·기기·브라우저·유입호스트뿐 — IP/개인식별정보/쿠키 없음.
const GIF = Uint8Array.from(atob("R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="), c => c.charCodeAt(0));
const px = () => new Response(GIF, { status: 200, headers: { "content-type": "image/gif", "cache-control": "no-store, max-age=0" } });

function browserOf(ua) {
  if (/SamsungBrowser/i.test(ua)) return "SamsungInternet";
  if (/Edg\//i.test(ua)) return "Edge";
  if (/OPR\/|Opera/i.test(ua)) return "Opera";
  if (/Firefox\//i.test(ua)) return "Firefox";
  if (/CriOS/i.test(ua)) return "ChromeiOS";
  if (/Chrome\//i.test(ua)) return "Chrome";
  if (/Safari\//i.test(ua)) return /Mobile/i.test(ua) ? "MobileSafari" : "Safari";
  return "Other";
}

export async function onRequest(context) {
  const { request, env } = context;
  try {
    if (!env.HITS) return px();
    const ua = request.headers.get("user-agent") || "";
    // 봇 제외
    if (/bot|crawl|spider|slurp|preview|monitor|headless|facebookexternalhit|lighthouse|pingdom|uptime|curl|wget|python-requests/i.test(ua)) return px();

    const url = new URL(request.url);
    const d = new Date(Date.now() + 9 * 3600000);        // KST
    const date = d.toISOString().slice(0, 10);
    const cc = (request.cf && request.cf.country) || "XX";
    const device = /Mobile|Android|iPhone|iPad|iPod/i.test(ua) ? "mobile" : "desktop";
    const browser = browserOf(ua);
    let ref = "direct";
    const r = url.searchParams.get("r") || "";
    if (r) { try { ref = new URL(r).hostname || "direct"; } catch (e) { ref = "direct"; } }
    ref = (ref || "direct").replace(/[^a-z0-9.\-]/gi, "").slice(0, 60) || "direct";

    const sess = url.searchParams.get("s") === "1" ? "n" : "p"; // n=새 방문(세션), p=추가 페이지뷰
    const rand = (crypto.randomUUID && crypto.randomUUID()) || (Date.now() + "" + Math.random());
    const key = `h|${date}|${cc}|${device}|${browser}|${ref}|${sess}|${rand}`;
    await env.HITS.put(key, "1");
  } catch (e) { /* 집계 실패는 페이지에 영향 없음 */ }
  return px();
}
