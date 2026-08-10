#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOICA 현지입찰공고 자동 갱신 스크립트 (헤드리스 크로미엄)
 - KOICA 전자조달 목록/상세를 실제 브라우저 세션으로 수집 → data.min.js 갱신 → index_standalone.html 재빌드
 - KOICA 서버는 curl/외부 스크립트 접근을 차단하므로 실제 브라우저(Playwright)로만 수집됩니다.
사용: (venv 활성화 후)  python refresh.py
"""
import json, sys, datetime, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
LIST_URL = "https://nebid.koica.go.kr/oep/lobi/localBidManageList.do?P_PRCURE_BSNS_SE_CD=ABID"

# 페이지 컨텍스트에서 실행될 수집 로직 (refresh_snippet.js 와 동일 규칙)
COLLECT_JS = r"""
async () => {
  const base = location.origin + '/oep';
  const PAGE_SIZE = 500, CONCURRENCY = 10;
  const REGION_MAP = {
    '동남아시아':['베트남','캄보디아','라오스','인도네시아','필리핀','동티모르','미얀마','태국'],
    '서남아태평양':['네팔','방글라데시','파키스탄','스리랑카','피지','몽골'],
    '아프리카':['우간다','케냐','탄자니아','에티오피아','모잠비크','르완다','세네갈','가나','나이지리아','코트디부아르','카메룬'],
    '유라시아중동':['요르단','이라크','우즈베키스탄','키르기스스탄','타지키스탄','우크라이나','튀니지','알제리','이집트'],
    '중남미':['페루','볼리비아','에콰도르','콜롬비아','과테말라','파라과이','도미니카','엘살바도르'],
  };
  const COUNTRIES = ['에콰도르','우즈베키스탄','이라크','우간다','코트디부아르','파라과이','키르기스','키르기즈','키르키즈','라오스','캄보디아','나이지리아','베트남','요르단','우크라이나','과테말라','네팔','세네갈','페루','케냐','모잠비크','볼리비아','에티오피아','방글라데시','동티모르','콜롬비아','피지','탄자니아','알제리','인도네시아','파키스탄','타지키스탄','가나','카메룬','도미니카','엘살바도르','튀니지','몽골','필리핀','이집트','르완다','미얀마','스리랑카'];
  const NORM = {'키르기스':'키르기스스탄','키르기즈':'키르기스스탄','키르키즈':'키르기스스탄'};
  const EXTRA = {'아르빌':'이라크','키르기스공화국':'키르기스스탄','호치민':'베트남'};
  const OVERRIDE = {'L2024-00011':'이라크'};                 // KOICA-KOTRA 사무소(이라크)
  const C2R = {}; for (const [r,cs] of Object.entries(REGION_MAP)) cs.forEach(c=>C2R[c]=r);
  const matchC = t => { for (const c of COUNTRIES) if (t.includes(c)) return NORM[c]||c;
    for (const [k,v] of Object.entries(EXTRA)) if (t.includes(k)) return v; return null; };
  const country = (nm,pj,no) => { const pre=(no||'').replace(/-\d+$/,''); if(OVERRIDE[pre]) return OVERRIDE[pre];
    return matchC(nm) || matchC(pj||'') || '기타/공통'; };
  const region  = co => C2R[co] || '기타/공통';
  const fyOf = no => (no.match(/^L(\d{4})/)||[])[1] || '?';
  const amtOf = a => { const m=(a||'').match(/([\d,]+)/); return m?+m[1].replace(/,/g,''):null; };
  const post = async (url,p)=>{ const r=await fetch(url,{method:'POST',credentials:'include',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(p).toString()}); return r.text(); };

  const listHtml = await post(base+'/lobi/localBidManageList.do',
    {P_PRCURE_BSNS_SE_CD:'ABID',P_PAGE_NO:'1',P_PAGE_SIZE:String(PAGE_SIZE),
     P_BID_KOREAN_NM_S:'',P_PBLANC_BEGIN_DE_S:'',P_PBLANC_END_DE_S:''});
  const ldoc = new DOMParser().parseFromString(listHtml,'text/html');
  const items = [];
  ldoc.querySelectorAll('table tbody tr').forEach(tr=>{
    const m=(tr.getAttribute('onclick')||'').match(/localBidManageDetailInqire\('([^']+)','([^']+)'\)/);
    const td=[...tr.querySelectorAll('td')].map(t=>t.textContent.trim());
    if(m&&td.length>=7) items.push({bidNo:td[1],name:td[2],type:td[3],method:td[4],noticeDate:td[5],mgr:td[6],pblancNo:m[1],odr:m[2]});
  });
  const pick=(pairs,label)=>{const p=pairs.find(x=>x[0]===label);return p?p[1]:'';};
  const out=new Array(items.length); let idx=0;
  async function worker(){
    while(idx<items.length){ const i=idx++, it=items[i];
      try{
        const html=await post(base+'/lobi/localBidManageDetail.do',{P_LOAZ_BID_PBLANC_NO:it.pblancNo,P_PBLANC_ODR:it.odr});
        const doc=new DOMParser().parseFromString(html,'text/html');
        const pairs=[]; doc.querySelectorAll('th').forEach(th=>{const td=th.nextElementSibling;pairs.push([th.textContent.trim(),td?td.textContent.trim().replace(/\s+/g,' '):'']);});
        const pj=pick(pairs,'사업명'); const co=country(it.name,pj,it.bidNo);
        out[i]={no:it.bidNo,nm:it.name,ty:it.type,me:it.method,mg:it.mgr,pj,amt:amtOf(pick(pairs,'집행한도금액(달러)')),
          co,rg:region(co),fy:fyOf(it.bidNo),nd:pick(pairs,'공고일자')||it.noticeDate,bd:pick(pairs,'설명회개최일자'),
          dl:pick(pairs,'입찰서제출마감일자'),od:pick(pairs,'개찰일자')};
      }catch(e){ const co=country(it.name,'',it.bidNo);
        out[i]={no:it.bidNo,nm:it.name,ty:it.type,me:it.method,mg:it.mgr,co,rg:region(co),fy:fyOf(it.bidNo),nd:it.noticeDate,bd:'',dl:'',od:''}; }
    }
  }
  await Promise.all(Array.from({length:CONCURRENCY},worker));
  return out;
}
"""

def log(m): print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {m}", flush=True)

def collect_once(p):
    browser = p.chromium.launch(headless=True)
    try:
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
            locale="ko-KR", ignore_https_errors=True)
        page = ctx.new_page()
        page.goto(LIST_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        return page.evaluate(COLLECT_JS)
    finally:
        browser.close()

def main():
    data = None
    with sync_playwright() as p:
        for attempt in range(1, 4):   # KOICA가 클라우드 IP를 간헐 차단 → 최대 3회 재시도
            log(f"KOICA 수집 시도 {attempt}/3…")
            try:
                data = collect_once(p)
            except Exception as e:
                log(f"시도 {attempt} 예외: {e}")
                data = None
            if data and len(data) >= 5:
                break
            log(f"시도 {attempt} 실패({len(data) if data else 0}건) — 재시도 대기")
            if attempt < 3:
                import time; time.sleep(15)

    if not data or len(data) < 5:
        log(f"수집 실패: {len(data) if data else 0}건. 페이지 구조 변경 또는 차단 가능성.")
        sys.exit(1)

    kst = datetime.timezone(datetime.timedelta(hours=9))
    built = datetime.datetime.now(tz=datetime.timezone.utc).astimezone(kst).strftime("%Y-%m-%d %H:%M")
    (HERE/"data.min.js").write_text(
        "window.BIDS="+json.dumps(data, ensure_ascii=False, separators=(",",":"))
        + ";window.BUILT="+json.dumps(built)+";", encoding="utf-8")
    log(f"data.min.js 갱신: {len(data)}건 (기준일시 {built} KST)")

    # 단일 파일 재빌드
    tpl = (HERE/"dashboard_template.html").read_text(encoding="utf-8")
    js  = (HERE/"data.min.js").read_text(encoding="utf-8")
    (HERE/"index_standalone.html").write_text(
        tpl.replace('<script src="data.min.js"></script>', '<script>\n'+js+'\n</script>'), encoding="utf-8")
    log("index_standalone.html 재빌드 완료 ✅")

if __name__ == "__main__":
    main()
