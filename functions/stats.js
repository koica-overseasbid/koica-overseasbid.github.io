// KOICA 대시보드 집계 조회 (Cloudflare Pages Function, route: /stats)
// 보호: ?k=<STATS_KEY> 가 환경변수 STATS_KEY 와 일치해야 응답.
// 반환: 월별(또는 전체) 집계 JSON — total/byDay/byCountry/byDevice/byBrowser/byReferer
// 집계값은 모두 비개인(aggregate) 수치입니다.
function inc(o, k) { o[k] = (o[k] || 0) + 1; }

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (!env.STATS_KEY || url.searchParams.get("k") !== env.STATS_KEY)
    return new Response("forbidden", { status: 403 });
  if (!env.HITS)
    return new Response(JSON.stringify({ error: "no KV binding" }), { status: 500, headers: { "content-type": "application/json" } });

  // 일회용 초기화(설치 테스트 데이터 제거) — STATS_KEY 보호
  if (url.searchParams.get("reset") === "1") {
    let c, n = 0;
    do {
      const res = await env.HITS.list({ prefix: "h|", cursor: c, limit: 1000 });
      for (const { name } of res.keys) { await env.HITS.delete(name); n++; }
      c = res.list_complete ? null : res.cursor;
    } while (c);
    return new Response(JSON.stringify({ deleted: n }), { headers: { "content-type": "application/json" } });
  }

  const month = url.searchParams.get("month"); // "YYYY-MM" 또는 없음(전체)
  const raw = url.searchParams.get("raw") === "1"; // 원시행 내보내기(xlsx용)
  const prefix = month ? `h|${month}` : "h|";

  let cursor, total = 0, visits = 0;
  const byDay = {}, byCountry = {}, byDevice = {}, byBrowser = {}, byReferer = {};
  const rows = [];
  do {
    const res = await env.HITS.list({ prefix, cursor, limit: 1000 });
    for (const { name } of res.keys) {
      const p = name.split("|"); // h|date|cc|device|browser|ref|sess|rand
      if (p.length < 7) continue;
      total++;
      if (p[6] === "n") visits++;
      inc(byDay, p[1]); inc(byCountry, p[2]); inc(byDevice, p[3]);
      inc(byBrowser, p[4]); inc(byReferer, p[5] || "direct");
      if (raw) rows.push([p[1], p[2], p[3], p[4], p[5] || "direct", p[6] === "n" ? "new" : "pageview"]);
    }
    cursor = res.list_complete ? null : res.cursor;
  } while (cursor);

  const out = { month: month || "all", total, visits, byDay, byCountry, byDevice, byBrowser, byReferer };
  if (raw) out.rows = rows;
  return new Response(JSON.stringify(out),
    { headers: { "content-type": "application/json", "cache-control": "no-store" } });
}
