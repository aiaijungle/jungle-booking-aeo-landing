"""
정글부킹 블로그 생성기 — Claude + 자청 스타일 + 심리 트리거
기존 auto_blog_builder.py (OpenAI) 대신 Claude로 고품질 포스트 생성
"""
import os, sys, re, json, datetime
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent.parent
BLOG_DIR = Path(__file__).parent / "blog"
BLOG_DIR.mkdir(exist_ok=True)

# API 키 로드
env = {}
for line in (ROOT / "MASTER.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)

client = anthropic.Anthropic(api_key=env["ANTHROPIC_API_KEY"])

# ─── 정글부킹 컨텍스트 ────────────────────────────────────
JUNGLE_CONTEXT = """
[정글부킹 핵심 정보]
- 제품: AI 기반 예약·판매·정산 올인원 솔루션 (SaaS, 잔다 JANDA 운영)
- 지원 타입: 회의실, 강의실, 미팅룸, 숙박, 프로그램, 공공시설, 러닝/피트니스, 코워킹스페이스
- 핵심 기능:
  · AI 마케팅 분석 (고객 패턴 자동 분석 → 전략 제안)
  · 자동 정산 (별도 PG사 불필요)
  · 6가지 예약 타입 지원
  · 맞춤형 브랜딩 페이지
  · 풀 오토메이션 (예약→결제→정산 자동화)
- 성과: 도입 후 1600% 매출 성장 사례
- 무료 체험: 14일 무료 제공
- URL: https://www.ai-jungle.kr
- 고객: SK렌터카, 대학교, 공공기관, 러닝 크루, 코워킹스페이스 등
"""

PSYCH_ENGINE = """
[심리 트리거 — 반드시 본문에 녹여넣기]
■ 손실회피(카너먼): "지금 안 하면 매달 N만원 날린다" 구체적 손실 계산
■ 사회적 증거(뇌욕망): 구체적 숫자, 업종별 사례, 고객 수
■ 판단 오류(클루지): "대부분의 사장님이 착각하는 것"
■ 지위/경쟁(욕망의 진화): "경쟁 업체는 이미 도입했다"
■ 희소성(뇌욕망): "14일 무료 체험, 지금만"
"""

STYLE_ENGINE = """
[자청 × 카너먼 × 치알디니 스타일 규칙]
- 결론 먼저: 첫 문장에 숫자 or 충격 팩트
- 짧고 강하게: 한 문장 = 한 생각, 3줄 이상 단락 금지
- 치알디니 도입: 장면 묘사 → 문제 → 솔루션
- 카너먼 데이터: 구체적 숫자, 퍼센트, 비교
- 금지: "~것 같습니다", "~인 것으로 보입니다", 강의체, 부드러운 완충 표현
"""

HTML_TEMPLATE = """당신은 정글부킹 블로그 전문 작성가입니다.

{jungle}
{psych}
{style}

[오늘 주제] {topic}

아래 HTML 구조를 완전히 채운 블로그 포스트를 작성하세요:
- SEO/AEO 최적화 (FAQ Schema JSON-LD 3개 포함)
- OpenGraph 메타태그 포함
- 구글 검증 태그: 9707umOT-VEJrdQqFfGg8QZkuQK8LJZ1L7XWNGkEfBQ
- canonical URL: https://aiaijungle.github.io/jungle-booking-aeo-landing/blog/{filename}
- 이미지: img/1_마진극대화.png, img/2_풀오토메이션.png, img/3_AI분석.png, img/4_맞춤형브랜딩.png 중 맥락에 맞는 2개 삽입
- 이미지 태그: <img src="img/파일명" alt="설명" style="width:100%;max-height:400px;object-fit:cover;border-radius:16px;margin:2rem 0;box-shadow:0 10px 30px rgba(0,0,0,0.5);" />
- CTA: 14일 무료 체험 버튼 → https://www.ai-jungle.kr

[디자인 CSS — 다크 그린 테마]
body{{background:#0a0f0a;color:#e8f5e9;font-family:'Noto Sans KR',sans-serif;line-height:1.8}}
.container{{max-width:800px;margin:0 auto;padding:2rem 1.5rem}}
header{{background:linear-gradient(135deg,#1b5e20,#2e7d32);padding:3rem 2rem;text-align:center}}
header h1{{font-size:2rem;font-weight:900;color:#fff;line-height:1.3;margin-bottom:1rem}}
.badge{{display:inline-block;background:#ff6f00;color:#fff;padding:0.3rem 1rem;border-radius:20px;font-size:0.85rem;font-weight:700;margin-bottom:1rem}}
h2{{font-size:1.4rem;color:#69f0ae;margin:2.5rem 0 1rem;border-left:4px solid #00e676;padding-left:1rem}}
p{{margin-bottom:1.2rem;color:#c8e6c9}}
strong{{color:#69f0ae}}
.highlight-box{{background:#1b2e1b;border:1px solid #2e7d32;border-radius:12px;padding:1.5rem;margin:2rem 0}}
.highlight-box .number{{font-size:2.5rem;font-weight:900;color:#00e676}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin:2rem 0}}
.stat-card{{background:#1b2e1b;border-radius:12px;padding:1.5rem;text-align:center;border:1px solid #2e7d32}}
.stat-card .num{{font-size:2rem;font-weight:900;color:#00e676}}
.stat-card .label{{color:#81c784;font-size:0.9rem;margin-top:0.5rem}}
.psych-box{{background:linear-gradient(135deg,#1a237e,#283593);border-radius:12px;padding:1.5rem;margin:2rem 0;border-left:4px solid #5c6bc0}}
.cta-section{{background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:16px;padding:3rem 2rem;text-align:center;margin:3rem 0}}
.cta-btn{{display:inline-block;background:#ff6f00;color:#fff;padding:1rem 2.5rem;border-radius:50px;font-size:1.1rem;font-weight:700;text-decoration:none;margin-top:1rem}}
.faq-item{{background:#1b2e1b;border-radius:12px;padding:1.5rem;margin:1rem 0}}
.faq-item .q{{color:#69f0ae;font-weight:700;margin-bottom:0.5rem}}
footer{{text-align:center;padding:2rem;color:#4caf50;border-top:1px solid #1b5e20;margin-top:3rem}}
@media(max-width:600px){{header h1{{font-size:1.4rem}}.stat-grid{{grid-template-columns:1fr 1fr}}}}

완전한 HTML 파일을 ```html 코드블럭으로만 반환하세요.
"""

TOPICS = [
    ("예약 시스템 없이 운영하는 사업이 매달 잃는 것", "예약시스템 없으면 매달 손실"),
    ("회의실 관리자가 하루 3시간을 낭비하는 이유", "회의실예약 자동화 효과"),
    ("대학교 시설 예약, AI가 바꾼 3가지 현실", "대학교예약시스템 AI도입"),
    ("러닝 크루 운영자 80%가 포기하는 이유", "러닝크루 예약관리 자동화"),
    ("코워킹스페이스 공실률을 절반으로 줄인 방법", "코워킹스페이스 예약시스템"),
]


def generate_post(topic: str, seo_keyword: str, filename: str) -> str:
    prompt = HTML_TEMPLATE.format(
        jungle=JUNGLE_CONTEXT,
        psych=PSYCH_ENGINE,
        style=STYLE_ENGINE,
        topic=topic,
        filename=filename,
    )
    print(f"  Claude 생성 중: {topic[:30]}...")
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    content = msg.content[0].text
    match = re.search(r"```html\n(.*?)\n```", content, re.DOTALL)
    return match.group(1) if match else content


def update_blog_data_js():
    blogs = []
    files = sorted(BLOG_DIR.glob("*.html"), reverse=True)
    for fp in files:
        try:
            soup = BeautifulSoup(fp.read_bytes(), "html.parser")
            title = soup.find("title")
            desc = soup.find("meta", attrs={"name": "description"})
            blogs.append({
                "title": title.text.strip() if title else "정글부킹 인사이트",
                "desc": desc["content"].strip() if desc and desc.get("content") else "",
                "url": f"blog/{fp.name}"
            })
        except Exception:
            pass

    js_path = Path(__file__).parent / "blog_data.js"
    js_path.write_text(
        "const BLOG_POSTS = " + json.dumps(blogs, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8"
    )
    print(f"  blog_data.js 업데이트: {len(blogs)}개 포스트")


def update_sitemap(filename: str):
    sitemap = Path(__file__).parent / "sitemap.xml"
    if not sitemap.exists():
        return
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    new_url = f"""  <url>
    <loc>https://aiaijungle.github.io/jungle-booking-aeo-landing/blog/{filename}</loc>
    <lastmod>{date}</lastmod>
    <changefreq>monthly</changefreq>
  </url>
</urlset>"""
    content = sitemap.read_text(encoding="utf-8")
    sitemap.write_text(content.replace("</urlset>", new_url), encoding="utf-8")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="커스텀 주제 (없으면 자동 선택)")
    parser.add_argument("--all", action="store_true", help="TOPICS 전체 생성")
    args = parser.parse_args()

    if args.all:
        gen_list = TOPICS
    elif args.topic:
        gen_list = [(args.topic, args.topic[:20])]
    else:
        import random
        gen_list = [random.choice(TOPICS)]

    for topic, keyword in gen_list:
        today = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"jungle-post-{today}.html"
        html = generate_post(topic, keyword, filename)
        out = BLOG_DIR / filename
        out.write_text(html, encoding="utf-8")
        print(f"  저장: {filename} ({len(html):,}자)")
        update_sitemap(filename)

    update_blog_data_js()
    print("\n완료! auto_deploy.bat 실행하면 GitHub에 배포됩니다.")


if __name__ == "__main__":
    main()
