# KOICA 현지입찰공고 대시보드 (공개 자료 기준)

KOICA 전자조달 현지입찰공고(공고일·마감일·개찰일) 대시보드를 **Cloudflare Pages**로 공개 배포합니다.
데이터는 대국민 공개 정보이며, **GitHub Actions가 매일 09:00(KST) KOICA를 수집해 `index.html`을 저장소에 커밋**하면 Cloudflare가 자동 재배포합니다.

**공개 주소: https://koica-overseasbid.pages.dev**

## 동작 구조
```
GitHub Actions (매일 09:00 KST, cron)
   → 헤드리스 크로미엄으로 KOICA 수집 → index.html 저장소 커밋 [skip ci]
        │
        ▼
Cloudflare Pages (저장소 연결) → 커밋 감지 시 자동 재배포
열람자  →  https://koica-overseasbid.pages.dev  링크로 접속
```
- KOICA가 GitHub 클라우드 IP를 차단하면 수집이 실패하고, 저장소의 **직전 `index.html`(마지막 정상 데이터)** 이 그대로 유지됩니다(사이트는 계속 정상).
  차단이 잦으면 로컬(맥)에서 수집·push하는 방식으로 전환합니다.

## 최초 1회 설정 (계정 소유자만 가능)
> 계정 생성·인증은 보안상 본인이 직접 하셔야 합니다.

1. GitHub 로그인(없으면 github.com 가입) 후 **새 public 저장소** 생성 (예: `koica-bid-dashboard`).
2. 저장소 **Settings → Pages → Build and deployment → Source: GitHub Actions** 선택.
3. 이 폴더를 원격에 연결·푸시:
   ```bash
   cd ~/koica-biddash/site
   git remote add origin https://github.com/<계정>/<저장소>.git
   git branch -M main
   git push -u origin main
   ```
4. 저장소 **Actions** 탭 → 워크플로가 자동 실행(또는 `Run workflow`) → 완료되면 Pages URL 활성화.

## 파일
| 파일 | 설명 |
|---|---|
| `index.html` | 배포되는 대시보드(폴백 겸 초기본). Actions가 매일 최신으로 교체 |
| `refresh.py` | KOICA 수집·빌드 (Playwright 헤드리스) |
| `dashboard_template.html` | 화면 소스 |
| `.github/workflows/deploy.yml` | 매일 자동 수집·배포 워크플로 |

## 갱신 주기 변경
`.github/workflows/deploy.yml`의 `cron` 값을 수정(UTC 기준). 예: `0 0 * * *` = 09:00 KST.
