import os
import sys
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
try:
    import openai
except ImportError:
    print("openai 모듈이 없습니다. 'pip install openai'를 실행해주세요.")
    sys.exit(1)

from dotenv import load_dotenv

BASE_URL = "https://aiaijungle.github.io/jungle-booking-aeo-landing"
BLOG_DIR = os.path.join(os.path.dirname(__file__), "blog")
SITEMAP_PATH = os.path.join(os.path.dirname(__file__), "sitemap.xml")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.html")

# .env 에서 인증키 가져오기 (마케팅 자동화 폴더의 .env 활용)
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "03_마케팅_자동화", ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip() and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("\n⚠️ OPENAI_API_KEY가 없습니다!")
    print("OpenAI 홈페이지에서 발급받은 API 키(sk-...)를 입력해주세요.")
    API_KEY = input("비밀번호 입력하듯 여기에 붙여넣기 (마우스 우클릭) 후 엔터: ").strip()
    
    # 입력받은 키를 .env에 자동 저장해주는 센스
    if API_KEY:
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"\nOPENAI_API_KEY={API_KEY}\n")
        print("\n✅ 키가 .env에 저장되었습니다. (다음부터는 그냥 실행됩니다!)")
    else:
        sys.exit(1)

client = openai.OpenAI(api_key=API_KEY)


def get_jungle_context():
    """자사 랜딩페이지(index.html)에서 정글부킹 핵심 내용 추출"""
    print("[1/4] 자사 랜딩페이지 내용 분석 중...")
    with open(INDEX_PATH, "rb") as f:
        soup = BeautifulSoup(f, "html.parser")
        text = soup.get_text(separator=' ', strip=True)
        # 핵심만 2000자 이내로 컷
        return text[:2000]


def crawl_naver_blog(query="정글부킹"):
    """네이버 블로그 검색을 통해 최근 동향 크롤링"""
    print("[2/4] 네이버 블로그 최신 동향 크롤링 중...")
    url = f"https://search.naver.com/search.naver?where=view&sm=tab_jum&query={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        titles = soup.find_all("a", class_="api_txt_lines total_tit")
        snippets = soup.find_all("div", class_="api_txt_lines dsc_txt")
        
        context = ""
        for t, s in zip(titles[:5], snippets[:5]):
            context += f"- 제목: {t.text}\n  요약: {s.text}\n"
        return context
    except Exception as e:
        print(f"네이버 크롤링 실패: {e}")
        return "네이버 블로그 데이터를 가져오지 못했습니다."


def generate_blog_html(jungle_context, naver_context):
    """Claude AI를 통해 HTML 형식의 블로그 포스트 생성"""
    print("[3/4] Claude AI 블로그 작성 중 (AEO/SEO 최적화)...")
    
    prompt = f"""
    당신은 B2B SaaS 및 마케팅 전문가이자 천재적인 카피라이터입니다.
    아래 1.정글부킹 공식 소개와 2.네이버 블로그 최신 동향을 바탕으로, 
    정글부킹의 장점을 강력하게 어필하는 "새로운 SEO/AEO 최적화 블로그 페이지"를 작성해주세요.
    
    [정보 1: 정글부킹 공식 내용]
    {jungle_context}
    
    [정보 2: 네이버 블로그 동향]
    {naver_context}
    
    [요구사항]
    1. 디자인은 화려한 글래스모피즘(Glassmorphism) 다크 테마 HTML 코드로 작성 (css포함).
    2. 시맨틱 태그(article, h1, h2) 적극 활용.
    3. 글자수는 충분히 길고 설득력 있게 작성 (Pain point 자극 및 해결 스토리).
    4. 📌 **매우 중요**: 글 하단(또는 중간중간 적절한 곳)에 반드시 **"정글부킹 14일 무료 체험하기"** 버튼을 크고 화려한 CTA 버튼 디자인으로 넣어주세요. (링크 주소: https://www.ai-jungle.kr)
    5. 📌 **매우 중요**: 생성되는 HTML의 `<head>` 안에는 SEO/AEO 최적화를 위해 완벽한 title, meta description 태그를 넣고, 반드시 구글 서치콘솔 인증을 위한 다음 태그를 포함해주세요: `<meta name="google-site-verification" content="9707umOT-VEJrdQqFfGg8QZkuQK8LJZ1L7XWNGkEfBQ" />`
    6. 반드시 ```html 코드블럭으로만 출력.
    """
    
    try:
        print("  [gpt-4o-mini] 최강 가성비 모델로 시도 중...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        content = response.choices[0].message.content
    except Exception as e:
        print(f"  [실패] gpt-4o-mini 생성 에러 - {e}")
        sys.exit(1)
        
    # ```html 블럭 안의 내용만 추출
    match = re.search(r"```html\n(.*?)\n```", content, re.DOTALL)
    if match:
        return match.group(1)
    return content


def update_sitemap(filename):
    """sitemap.xml에 새로운 블로그 파일 주소 추가"""
    print("[4/4] 사이트맵(sitemap.xml) 자동 업데이트 중...")
    if not os.path.exists(SITEMAP_PATH):
        return
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_url_tag = f"""  <url>
    <loc>{BASE_URL}/blog/{filename}</loc>
    <lastmod>{date_str}</lastmod>
    <changefreq>monthly</changefreq>
  </url>
</urlset>"""

    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # </urlset> 직전에 새로운 url 태그 삽입
    new_content = content.replace("</urlset>", new_url_tag)
    
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d_%H%M")
    
    j_ctx = get_jungle_context()
    n_ctx = crawl_naver_blog("정글부킹")
    
    html_result = generate_blog_html(j_ctx, n_ctx)
    
    filename = f"jungle-post-{today_str}.html"
    filepath = os.path.join(BLOG_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_result)
        
    update_sitemap(filename)
    
    print("\n==============================================")
    print(f"🎉 자동화 블로그 발행 완료!")
    print(f"   파일: blog/{filename}")
    print("   이제 auto_deploy.bat 를 실행하면 구글에도 자동으로 반영됩니다!")
    print("==============================================\n")

if __name__ == "__main__":
    main()
