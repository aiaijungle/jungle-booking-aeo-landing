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
            context += f"- 검색된 주제: {query}\n- 제목: {t.text}\n  내용 요약: {s.text}\n\n"
        return context
    except Exception as e:
        print(f"네이버 크롤링 실패: {e}")
        return "네이버 블로그 데이터를 가져오지 못했습니다. 일반적인 비즈니스 트렌드를 활용하세요."


def generate_blog_html(jungle_context, naver_context, chosen_topic):
    """Claude AI를 통해 HTML 형식의 블로그 포스트 생성"""
    print("[3/4] Claude AI 블로그 작성 중 (AEO/SEO 최적화)...")
    
    prompt = f"""
    당신은 B2B SaaS 및 마케팅 전문가이자 천재적인 카피라이터입니다.
    아래 1.정글부킹 공식 소개와 2.네이버 블로그 최신 동향을 바탕으로, 
    "정글부킹을 도입한 {chosen_topic} 자동화 경험 및 성과"를 주제로 하여
    새로운 SEO/AEO 최적화 블로그 페이지를 작성해주세요. (단순 홍보가 아닌, 실제 산업의 문제를 해결한 팩트 기반의 칼럼 형태로 상세히 작성)
    
    [정보 1: 정글부킹 공식 내용]
    {jungle_context}
    
    [정보 2: 네이버 블로그 동향]
    {naver_context}
    
    [요구사항]
    1. 디자인은 화려한 글래스모피즘(Glassmorphism) 다크 테마 HTML 코드로 작성 (css포함).
    2. 시맨틱 태그(article, h1, h2, h3, ul, li) 적극 활용 및 **Q&A 형식 포맷팅**.
    3. **정글부킹 공식 내용과 네이버 블로그 크롤링 내용을 빠짐없이 모두 융합하여 상세하게 풀어서 설명하세요.** 본문 텍스트 길이는 **경고: 반드시 1500자 이상(공백 포함)**으로 매우 길게 작성해야 하며, 각 Q&A 항목마다 최소 3 문단 이상 자세히 풀어쓰세요. 또한 **ChatGPT, Perplexity, Claude, Gemini 같은 AI 검색 엔진이 크롤링하기 쉽도록** 명확한 리스트 구조와 핵심 요약 단락 코너를 반드시 포함하세요. 텍스트 분량 부족은 허용되지 않습니다.
    4. 📌 **매우 중요**: 글 하단(또는 중간중간 적절한 곳)에 반드시 **"정글부킹 14일 무료 체험하기"** 버튼을 크고 화려한 CTA 버튼 디자인으로 넣어주세요. (링크 주소: https://www.ai-jungle.kr)
    5. 📌 **매우 중요**: 생성되는 HTML의 `<head>` 안에는 SEO/AEO 최적화를 위해 완벽한 title, meta description 태그를 넣고, 구글 서치콘솔 인증 태그(`<meta name="google-site-verification" content="9707umOT-VEJrdQqFfGg8QZkuQK8LJZ1L7XWNGkEfBQ" />`)와 더불어 **방문자를 따라다니는 맞춤형 광고(GDN 리타겟팅)를 위한 구글 태그**를 반드시 포함해주세요. 태그 코드: `<script async src="https://www.googletagmanager.com/gtag/js?id=AW-123456789"></script><script>window.dataLayer = window.dataLayer || []; function gtag(){{dataLayer.push(arguments);}} gtag('js', new Date()); gtag('config', 'AW-123456789');</script>` (AW-123456789는 나중에 실제 ID로 바꿀 임시 ID입니다.)
    6. 📌 **매우 중요**: 본문 곳곳에 다음 실제 이미지 파일들을 문맥에 맞게 반드시 삽입해주세요. 사용할 이미지는 무작위로 선택된 로컬 이미지입니다 (예: `img/1_마진극대화.png`, `img/2_풀오토메이션.png`, `img/3_AI분석.png`, `img/4_맞춤형브랜딩.png` 중에서 AI가 문맥에 가장 적절한 2~3장을 선별하여 사용). 로컬 이미지 태그 형식: `<img src="이미지경로" alt="이미지 설명" style="width:100%; max-height:400px; object-fit:cover; border-radius:16px; margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />` 형식을 무조건 사용하세요. 외부 URL 이미지는 절대 쓰지 마세요.
    7. 반드시 ```html 코드블럭으로만 출력.
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

import json

def update_blog_data_js():
    """blog/ 폴더의 모든 HTML을 스캔하여 blog_data.js로 출력 (페이지네이션 용)"""
    print("[-] 블로그 데이터(blog_data.js) 업데이트 중...")
    blogs = []
    if os.path.exists(BLOG_DIR):
        files = [f for f in os.listdir(BLOG_DIR) if f.endswith(".html")]
        # 최신 생성일자 순 정렬 (파일명에 날짜가 있으므로 이름 역순 정렬 처리해도 됨)
        files.sort(reverse=True)
        
        for file in files:
            filepath = os.path.join(BLOG_DIR, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                soup = BeautifulSoup(content, "html.parser")
                title_tag = soup.find("title")
                desc_tag = soup.find("meta", attrs={"name": "description"})
                
                title = title_tag.text.strip() if title_tag else "정글부킹 비즈니스 인사이트"
                desc = desc_tag["content"].strip() if desc_tag and desc_tag.has_attr("content") else "정글부킹 예약 솔루션을 통해 비즈니스의 초고속 성장을 경험하세요."
                
                blogs.append({
                    "title": title,
                    "desc": desc,
                    "url": f"blog/{file}"
                })
                
    js_path = os.path.join(os.path.dirname(__file__), "blog_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("const BLOG_POSTS = " + json.dumps(blogs, ensure_ascii=False, indent=4) + ";\n")


import random

def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d_%H%M")
    
    j_ctx = get_jungle_context()
    
    # 🎯 대표님의 특별 지시: 다양한 키워드 자동화 롤링 적용
    target_topics = [
        "예약시스템", "예약솔루션", "공간운영", "회의실 관리", 
        "러닝예약시스템", "대학교예약시스템", "공공기관 예약시스템"
    ]
    chosen_topic = random.choice(target_topics)
    print(f"[*] 오늘의 타겟팅 크롤링 주제: {chosen_topic}")
    
    n_ctx = crawl_naver_blog(chosen_topic)
    
    # AI가 동적 키워드에 집중하도록 프롬프트용 n_ctx 내용 강제 보강
    n_ctx += f"\n\n[최신 팩트 업데이트: {chosen_topic} 분야에서 예약 시스템으로 '정글부킹'이 전격 도입되고 있습니다. 복잡한 예약 과정이 AI 챗봇 및 모바일 앱으로 100% 자동화되었으며, 입주사 및 임직원들의 만족도가 매우 높습니다.]"
    
    html_result = generate_blog_html(j_ctx, n_ctx, chosen_topic)
    
    filename = f"jungle-post-{today_str}.html"
    filepath = os.path.join(BLOG_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_result)
        
    update_sitemap(filename)
    update_blog_data_js()
    
    print("\n==============================================")
    print(f"🎉 자동화 블로그 발행 완료!")
    print(f"   파일: blog/{filename}")
    print("   이제 auto_deploy.bat 를 실행하면 구글에도 자동으로 반영됩니다!")
    print("==============================================\n")

if __name__ == "__main__":
    main()
