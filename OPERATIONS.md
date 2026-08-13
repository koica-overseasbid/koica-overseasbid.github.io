# KOICA 해외사무소 현지입찰 대시보드 — 운영 · 인수인계 문서

> 이 문서는 담당자 변경·해외발령·퇴사 시 후임이 그대로 이어받을 수 있도록 작성되었습니다.
> **민감정보(토큰·비밀번호·개인 로그인 계정)는 여기 적지 않습니다.** 해당 정보는 별도 내부 인계로 전달하세요.

---

## 1. 개요
- **무엇**: KOICA 전자조달 현지입찰공고의 **공고일·입찰서제출마감일·개찰일**을 한 화면에서 보는 웹 대시보드.
- **공개 주소**: https://koica-overseasbid.pages.dev
- **데이터 출처**: KOICA 전자조달 현지입찰공고 (https://nebid.koica.go.kr/oep/lobi/localBidManageList.do?P_PRCURE_BSNS_SE_CD=ABID)
- **갱신 주기**: 매일 1회(평일 09:00 KST) 자동, 필요 시 수동 갱신.

## 2. 전체 구조
```
매일 09:00 KST
  → (담당자 PC) launchd/스케줄러가 refresh.py 실행
      → 헤드리스 크로미엄으로 KOICA 수집(500여 건) → index.html 생성
  → GitHub 저장소에 index.html 커밋 · push
      → Cloudflare Pages가 커밋 감지 → 자동 재배포
열람자 → https://koica-overseasbid.pages.dev
```
- **왜 개인 PC에서 수집하나?** KOICA 서버는 curl·스크립트·해외/클라우드 IP 접속을 차단합니다. **실제 브라우저 + 국내망**에서만 데이터가 수집됩니다. (그래서 GitHub 클라우드 자동수집은 차단되어 실패함)

## 3. 구성 자산
| 자산 | 내용 | 위치/소유 |
|---|---|---|
| **GitHub 저장소(public)** | `koica-overseasbid/koica-overseasbid.github.io` — 소스·index.html·워크플로 | GitHub 조직 `koica-overseasbid` |
| **호스팅** | Cloudflare Pages 프로젝트 `koica-overseasbid` (Git 연결형 자동배포) | 담당자 Cloudflare 계정 |
| **수집기** | `~/koica-biddash` (Python venv + Playwright/크로미엄, refresh.py) | 담당자 PC(맥) |
| **스케줄** | launchd `com.koica.biddash` (매일 09:00 KST) | 담당자 맥 |

## 4. 매일 자동 갱신 동작 흐름
1. launchd가 `~/koica-biddash/run_refresh.sh` 실행
2. `refresh.py`가 KOICA 수집(실패 시 최대 3회 재시도) → `index_standalone.html` 생성
3. 결과를 `site/index.html`로 복사 → `git commit` → `git push`
4. Cloudflare Pages가 push 감지 → 자동 재배포(1~2분)
- 조건: **PC가 09시에 켜져(또는 잠자기+자동기상) 있어야** 함. 꺼져 있으면 그날은 직전 데이터 유지, 다음 실행 시 갱신.

## 5. 자주 쓰는 조작 (터미널)
```bash
# 지금 즉시 갱신 (수집→push→Cloudflare 배포)
bash ~/koica-biddash/run_refresh.sh

# 로그 확인
tail -n 40 ~/koica-biddash/logs/refresh.log

# 자동 갱신 끄기 / 켜기
launchctl unload ~/Library/LaunchAgents/com.koica.biddash.plist
launchctl load   ~/Library/LaunchAgents/com.koica.biddash.plist

# 맥을 켜두지 않아도 매일 자동으로 깨워 실행 (전원 연결 필요, 관리자 비번 필요)
sudo pmset repeat wakeorpoweron MTWRF 08:58:00
```
- 갱신 확인: 사이트 새로고침 후 상단 "기준일시" 날짜가 오늘인지 확인.

## 6. 화면·기능 수정 방법
- 소스: `~/koica-biddash/dashboard_template.html` (HTML/CSS/JS 단일 파일)
- 빌드: `python build_standalone.py` → `index_standalone.html` 생성
- 반영: `site/index.html`로 복사 후 `git push` → Cloudflare 자동배포
- (권장 검증) 브라우저로 `index_standalone.html`을 열어 확인 후 배포.

## 7. 문제 대응 (Troubleshooting)
- **사이트가 안 바뀜**
  - Cloudflare 프로젝트가 **Git 연결(자동배포)** 인지 확인(Settings → Builds & deployments). Direct Upload면 자동배포 안 됨.
  - Production branch가 `main`인지 확인.
  - ⚠️ **커밋 메시지에 `[skip ci]`를 넣지 말 것** — Cloudflare가 배포를 건너뜁니다.
  - Cloudflare → Deployments 탭에서 최신 배포/오류 확인, 필요 시 Retry.
- **데이터가 며칠째 그대로**
  - PC가 09시에 꺼져 있었거나 수집이 차단됨 → `bash ~/koica-biddash/run_refresh.sh` 수동 실행.
- **수집 0건 / 실패**
  - KOICA 페이지 구조 변경 또는 IP 차단. **국내망 + 실제 브라우저 환경**에서 재시도. 로그(`logs/refresh.log`) 확인.
- **push 실패(인증)**
  - GitHub 토큰 만료/회수. 새 PAT(scope: repo, workflow) 발급 후 재인증.

## 8. 담당자 변경·해외발령·퇴사 시 체크리스트 ⚠️
- [ ] **GitHub 조직**(`koica-overseasbid`)에 후임/부서 공용계정을 **Owner로 추가** (Settings → People → Invite member → Owner)
- [ ] **Cloudflare** Pages 프로젝트에 후임/팀원 추가 또는 **KOICA 관리 계정으로 이전** (Members/Manage account)
- [ ] **수집기(PC)를 국내망 상시 PC/서버로 이전** — ⚠️ **해외로 개인 맥을 반출하면 현지 IP 차단으로 수집 불가!** 반드시 국내망 기기.
- [ ] GitHub 인증 토큰(PAT) 재발급 후 새 담당자/기기에 설정
- [ ] 개인 이메일 기반 계정이면 **KOICA 공용 이메일 기반으로 전환** 검토
- [ ] 이 문서 + 계정/크리덴셜 위치를 후임에게 인계

## 9. 개인 종속 위험 (반드시 인지)
현재 수집은 **담당자 개인 맥**, 호스팅·저장소는 **담당자 개인계정 기반 조직/계정**에 묶여 있습니다.
- 담당자 부재 시 **자동 갱신 중단** 및 계정 접근 단절 위험.
- **해외 발령 시** 개인 맥을 가져가면 현지 IP 차단으로 **수집 자체가 불가**.
- → 지속가능화: **부서 상시 PC에서 수집 + 계정 공동관리(Owner/팀원 추가) + 본 문서 인계**.

## 10. 장기 근본 개선
- KOICA가 **나라장터로 전환 완료**하면, 현지입찰 데이터가 나라장터/공공데이터포털 **공식 API**로 제공될 수 있음. 그 경우 **스크래핑·개인기기 없이 클라우드에서 24시간 자동** 수집 가능 → 완전한 기관 자산화.
- (현재 상태: 현지입찰은 아직 공식 API로 제공되지 않아 브라우저 수집이 필요함. 전환 여부는 주기적으로 확인.)

## 부록. 새 PC에서 처음부터 재구축
```bash
# 1) Python3 + 가상환경 + Playwright
python3 -m venv ~/koica-biddash/.venv
source ~/koica-biddash/.venv/bin/activate
pip install playwright
python -m playwright install chromium

# 2) 저장소 clone (수집 소스/스크립트 포함)
git clone https://github.com/koica-overseasbid/koica-overseasbid.github.io.git ~/koica-biddash/site

# 3) refresh.py 동작 확인 → run_refresh.sh 경로 수정 → 스케줄러 등록(launchd/작업스케줄러)
# 4) GitHub 인증(PAT) 및 Cloudflare Git 연결 확인
```

---
*최종 갱신: 이 문서는 운영 변경 시 함께 업데이트하세요.*
