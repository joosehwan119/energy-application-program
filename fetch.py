import re
import time
import requests
from bs4 import BeautifulSoup

# Selenium 관련 모듈
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def fetch_all_article_urls(home_url="https://www.electimes.com/"):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(home_url, headers=headers, timeout=10)
    except Exception as e:
        print("홈페이지 요청 실패:", e)
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "news/articleView.html?idxno=" in href:
            full_url = href if href.startswith("http") else "https://www.electimes.com" + href
            urls.add(full_url)
    return list(urls)

def fetch_article_with_selenium(url):
    options = Options()
    # 디버깅 시 headless 모드를 끌 수 있습니다.
    # 나중에 백그라운드 실행하려면 아래 주석 해제:
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    # 기사 본문 영역이 로드될 때까지 최대 20초 대기
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#articleViewCon article.grid.body"))
        )
    except Exception as e:
        print("본문 로딩 대기 시간 초과:", e)
        driver.quit()
        return ("제목 없음", "(본문 추출 실패)")
    
    # 페이지 하단까지 스크롤 (lazy loading 촉진)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # 폴링 방식: 최대 20초 동안 0.5초 간격으로 본문 텍스트 길이가 충분히 로드되었는지 확인
    max_wait = 20
    interval = 0.5
    elapsed = 0
    article_text = ""
    while elapsed < max_wait:
        try:
            article_element = driver.find_element(By.CSS_SELECTOR, "#articleViewCon article.grid.body")
            article_text = article_element.text.strip()
            if len(article_text) > 100:  # 충분한 텍스트가 로드되었다고 판단
                break
        except Exception:
            pass
        time.sleep(interval)
        elapsed += interval

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # 디버깅용 HTML 저장 (필요하면 debug_output.html 확인)
    with open("debug_output.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # 기사 제목 추출
    title_tag = soup.find("h3", class_="heading")
    title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
    
    # 기사 본문 추출: <article class="grid body"> 영역 내의 <p> 태그들을 결합
    article_tag = soup.select_one("#articleViewCon article.grid.body")
    if article_tag:
        paragraphs = article_tag.find_all("p")
        if paragraphs:
            raw_body = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        else:
            raw_body = article_tag.get_text(separator="\n").strip()
        body_cleaned = re.sub(r'\n\s*\n+', '\n\n', raw_body)
        body = body_cleaned if body_cleaned else "(본문이 비어 있거나 추출 실패)"
    else:
        body = "본문 없음"
    
    driver.quit()
    return (title, body)
