"""
기존 정글부킹 블로그 11개에 SEO/AEO 태그 일괄 추가 스크립트
- canonical URL
- Open Graph 태그
- FAQ Schema (JSON-LD)
- Article Schema
- keywords 메타 태그
"""
import os
import re
from datetime import datetime

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(BLOG_DIR, "blog")
BASE_URL = "https://aiaijungle.github.io/jungle-booking-aeo-landing/blog"

# 새 블로그는 이미 최적화되었으므로 제외
SKIP_FILES = ["jungle-post-20260414_0847.html", "jungle-post-20260414_0848.html"]

def extract_title_and_desc(html):
    """HTML에서 title과 description 추출"""
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    desc_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html, re.IGNORECASE)
    title = title_match.group(1) if title_match else "정글부킹 블로그"
    desc = desc_match.group(1) if desc_match else ""
    return title, desc

def extract_questions(html):
    """HTML에서 Q&A 구조 추출 (h2 태그에서 Q1, Q2 등)"""
    questions = []
    # Q1: ... Q2: ... 패턴 찾기
    q_pattern = re.findall(r'<h2>(Q\d+:?\s*)(.*?)</h2>\s*<p>\s*(.*?)\s*</p>', html, re.DOTALL)
    for _, question, answer in q_pattern:
        q = question.strip()
        a = answer.strip()
        # HTML 태그 제거
        a = re.sub(r'<[^>]+>', '', a)
        if len(a) > 300:
            a = a[:300] + "..."
        if q and a:
            questions.append({"question": q, "answer": a})
    return questions

def build_seo_tags(filename, title, desc, questions):
    """SEO/AEO 태그 생성"""
    url = f"{BASE_URL}/{filename}"
    
    tags = []
    
    # canonical
    tags.append(f'    <link rel="canonical" href="{url}">')
    
    # keywords
    tags.append('    <meta name="keywords" content="예약시스템, AI 예약, 정글부킹, 예약 자동화, SaaS, 예약 관리, AI 솔루션">')
    tags.append('    <meta name="author" content="정글부킹">')
    tags.append('    <meta name="robots" content="index, follow">')
    
    # Open Graph
    tags.append(f'    <meta property="og:type" content="article">')
    tags.append(f'    <meta property="og:title" content="{title}">')
    tags.append(f'    <meta property="og:description" content="{desc}">')
    tags.append(f'    <meta property="og:url" content="{url}">')
    tags.append(f'    <meta property="og:site_name" content="정글부킹 블로그">')
    tags.append(f'    <meta property="og:locale" content="ko_KR">')
    tags.append(f'    <meta property="article:published_time" content="2026-04-09T00:00:00+09:00">')
    
    # Article Schema
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "author": {"@type": "Organization", "name": "정글부킹"},
        "publisher": {"@type": "Organization", "name": "정글부킹"},
        "datePublished": "2026-04-09",
        "dateModified": "2026-04-14"
    }
    
    import json
    tags.append(f'    <script type="application/ld+json">')
    tags.append(f'    {json.dumps(article_schema, ensure_ascii=False, indent=4)}')
    tags.append(f'    </script>')
    
    # FAQ Schema (if questions found)
    if questions:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        for q in questions[:5]:  # 최대 5개
            faq_schema["mainEntity"].append({
                "@type": "Question",
                "name": q["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": q["answer"]
                }
            })
        tags.append(f'    <script type="application/ld+json">')
        tags.append(f'    {json.dumps(faq_schema, ensure_ascii=False, indent=4)}')
        tags.append(f'    </script>')
    
    return "\n".join(tags)

def process_file(filepath, filename):
    """단일 파일에 SEO 태그 주입"""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 이미 canonical이 있으면 스킵
    if 'rel="canonical"' in html:
        print(f"  [SKIP] 이미 최적화됨: {filename}")
        return False
    
    title, desc = extract_title_and_desc(html)
    questions = extract_questions(html)
    
    seo_tags = build_seo_tags(filename, title, desc, questions)
    
    # </head> 바로 앞에 태그 삽입
    if "</head>" in html:
        html = html.replace("</head>", f"\n{seo_tags}\n</head>")
    elif "</HEAD>" in html:
        html = html.replace("</HEAD>", f"\n{seo_tags}\n</HEAD>")
    
    # 이미지 경로 수정 (img/ → ../img/)
    html = html.replace('src="img/', 'src="../img/')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    q_count = len(questions)
    print(f"  [OK] {filename}")
    print(f"       Title: {title[:50]}...")
    print(f"       Q&A: {q_count}개 FAQ Schema 추가")
    print(f"       + canonical, OG x7, Article Schema, keywords")
    return True

def main():
    print("=" * 60)
    print("  정글부킹 블로그 SEO/AEO 일괄 최적화 스크립트")
    print("=" * 60)
    
    if not os.path.exists(BLOG_DIR):
        print(f"[ERROR] Blog directory not found: {BLOG_DIR}")
        return
    
    files = sorted([f for f in os.listdir(BLOG_DIR) 
                    if f.endswith(".html") and f not in SKIP_FILES])
    
    print(f"\n대상 파일: {len(files)}개 (새 블로그 2개 제외)\n")
    
    updated = 0
    skipped = 0
    
    for filename in files:
        filepath = os.path.join(BLOG_DIR, filename)
        if process_file(filepath, filename):
            updated += 1
        else:
            skipped += 1
    
    print(f"\n{'=' * 60}")
    print(f"  완료: {updated}개 업데이트 / {skipped}개 스킵")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
