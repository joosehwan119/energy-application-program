import re
import random
import string
import requests
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from tkinter import ttk
from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

##############################
# 1. 홈페이지에서 모든 기사 URL 수집
##############################
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
            if not href.startswith("http"):
                full_url = "https://www.electimes.com" + href
            else:
                full_url = href
            urls.add(full_url)
    return list(urls)

##############################
# 2. 개별 기사 크롤링 및 전처리
##############################
def fetch_article_with_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "articleViewCon"))
        )
    except Exception as e:
        print("❗ 본문 로딩 대기 시간 초과", e)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # 디버깅용 HTML 저장
    with open("debug_output.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # 제목 추출: <h3 class="heading">
    title_tag = soup.find("h3", class_="heading")
    title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
    
    # 본문 추출: 실제 본문은 <section id="articleViewCon" class="article-view-content"> 내부
    body_section = soup.find("section", id="articleViewCon")
    if body_section:
        article_tag = body_section.find("article", class_="grid body")
        html_content = article_tag.decode_contents() if article_tag else body_section.decode_contents()
        html_content = html_content.replace("<br>", "\n").replace("<br/>", "\n")
        soup2 = BeautifulSoup(html_content, "html.parser")
        raw_body = soup2.get_text(separator="\n").strip()
        body_cleaned = re.sub(r'\n\s*\n+', '\n\n', raw_body)
        unwanted_patterns = [
            "바로가기", "기사스크랩하기", "본문 글씨 키우기", "본문 글씨 줄이기",
            "최신기사", "많이 본 기사", "전기신문 TV",
            "제보", "입력", "호수", "기사보내기", "공유 찾기",
            "기자의 다른기사", "저작권", "라이브리 댓글",
            "페이스북", "트위터", "카카오스토리", "카카오톡",
            "네이버밴드", "네이버블로그", "URL복사"
        ]
        lines = [line.strip() for line in body_cleaned.splitlines()]
        filtered_lines = [line for line in lines if line and not any(pat in line for pat in unwanted_patterns)]
        body = "\n\n".join(filtered_lines)
        if not body:
            body = "(본문이 비어 있거나 추출 실패)"
    else:
        body = "본문 없음"
    
    driver.quit()
    return title, body

##############################
# 3. 요약 기능 (빈도 기반 요약)
##############################
def summarize_text(text, n_sentences=3):
    # 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= n_sentences:
        return text
    # 단어 빈도 계산
    words = re.findall(r'\w+', text.lower())
    word_freq = Counter(words)
    # 각 문장의 점수 계산 (문장 내 각 단어 빈도의 합)
    sentence_scores = {}
    for sentence in sentences:
        sentence_words = re.findall(r'\w+', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in sentence_words)
        sentence_scores[sentence] = score
    # 상위 n 문장을 선택
    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:n_sentences]
    # 원래 순서대로 정렬
    top_sentences.sort(key=lambda s: sentences.index(s))
    summary = " ".join(top_sentences)
    return summary

##############################
# 4. 중요어 주석 기능 (전기공학 관련 용어 동적 추출)
##############################
def annotate_text(text):
    # 전기공학 관련 주요 용어와 정의 사전 (확장)
    annotations = {
        "청정수소": "청정수소: 탄소 배출 없이 생산된 수소로, 친환경 에너지 전환의 핵심입니다.",
        "바이오가스": "바이오가스: 유기성 폐자원 처리로 생성된 가스로, 발전 및 열 공급에 사용됩니다.",
        "폐기물 자원화": "폐기물 자원화: 폐기물을 재활용하거나 에너지원으로 전환하는 기술입니다.",
        "탄소중립": "탄소중립: 온실가스 배출과 흡수를 균형 맞춰 기후 변화를 완화하는 상태입니다.",
        "광역 음식물류 폐기물 자원화시설": "광역 음식물류 폐기물 자원화시설: 대규모 음식물 폐기물을 처리하여 에너지로 전환하는 시설입니다.",
        "전압": "전압: 회로 내 전위차를 나타내며 전기 에너지 전달에 필수입니다.",
        "전류": "전류: 전하의 흐름을 측정하는 단위로, 전력의 핵심 요소입니다.",
        "회로": "회로: 전기 부품들이 연결되어 전류가 흐르는 경로입니다.",
        "저항": "저항: 전류의 흐름을 방해하여 에너지 손실을 유발하는 물질의 특성입니다.",
        "인덕턴스": "인덕턴스: 전류 변화 시 회로에 유도되는 자기장의 효과를 나타냅니다.",
        "커패시턴스": "커패시턴스: 전기 에너지를 저장하는 능력을 나타내는 값입니다."
    }
    found_terms = []
    for term, definition in annotations.items():
        # 정규식으로 단어 경계 기반 검색 (대소문자 무시)
        matches = re.findall(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE)
        count = len(matches)
        if count > 0:
            found_terms.append((term, definition, count))
    # 빈도에 따라 내림차순 정렬
    found_terms.sort(key=lambda x: x[2], reverse=True)
    # 상위 5개 단어 선택 (만약 너무 많다면)
    if not found_terms:
        # 아무 단어도 없으면 기본 3개로 강제 설정
        default_terms = ["전압", "전류", "회로"]
        found_terms = [(term, annotations[term], 1) for term in default_terms]
    # 결과로 (term, definition) 튜플 목록 반환
    return [(term, definition) for term, definition, count in found_terms]

##############################
# 5. 예상 Q&A 기능 (동적 생성)
##############################
def get_expected_qa(title, annotations_list):
    qa_pairs = []
    # 각 기사에서 가장 빈도 높은 2개 단어로 Q&A 생성
    for term, definition in annotations_list[:2]:
        q = f"{title} 기사에서 {term}의 역할은 무엇인가요?"
        # 정의에서 ':' 이후의 설명만 사용
        if ':' in definition:
            answer = definition.split(":", 1)[1].strip()
        else:
            answer = definition
        qa_pairs.append((q, answer))
    # Q&A를 텍스트로 변환
    qa_text = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in qa_pairs)
    return qa_text if qa_text else "예상 Q&A가 없습니다."

##############################
# 6. GUI 클래스: 기사 로드, 탭 구성, 기사 간 이동 및 전체 기사 하이라이트 적용
##############################
class ArticleApp:
    def __init__(self, master, article_urls):
        self.master = master
        self.article_urls = article_urls
        self.current_index = 0

        master.title("전기신문 기사 분석 및 응용")

        # 상단 네비게이션 버튼 프레임
        nav_frame = tk.Frame(master)
        nav_frame.pack(pady=5)
        prev_btn = tk.Button(nav_frame, text="<< 이전", command=self.load_previous, font=("맑은 고딕", 10))
        prev_btn.pack(side=tk.LEFT, padx=5)
        next_btn = tk.Button(nav_frame, text="다음 >>", command=self.load_next, font=("맑은 고딕", 10))
        next_btn.pack(side=tk.LEFT, padx=5)
        random_btn = tk.Button(nav_frame, text="랜덤", command=self.load_random, font=("맑은 고딕", 10))
        random_btn.pack(side=tk.LEFT, padx=5)

        # Notebook 탭 생성
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")

        # 탭 1: 전체 기사 (중요어 하이라이트 적용)
        self.tab_full = tk.Frame(self.notebook)
        self.notebook.add(self.tab_full, text="전체 기사")
        self.text_full = scrolledtext.ScrolledText(self.tab_full, wrap=tk.WORD, width=80, height=30, font=("맑은 고딕", 11))
        self.text_full.pack(padx=10, pady=10)

        # 탭 2: 요약
        self.tab_summary = tk.Frame(self.notebook)
        self.notebook.add(self.tab_summary, text="요약")
        self.text_summary = scrolledtext.ScrolledText(self.tab_summary, wrap=tk.WORD, width=80, height=30, font=("맑은 고딕", 11))
        self.text_summary.pack(padx=10, pady=10)

        # 탭 3: 주석 (주석 내용은 각 기사별 동적 추출)
        self.tab_annotation = tk.Frame(self.notebook)
        self.notebook.add(self.tab_annotation, text="주석")
        self.text_annotation = scrolledtext.ScrolledText(self.tab_annotation, wrap=tk.WORD, width=80, height=30, font=("맑은 고딕", 11))
        self.text_annotation.pack(padx=10, pady=10)

        # 탭 4: 예상 Q&A
        self.tab_qa = tk.Frame(self.notebook)
        self.notebook.add(self.tab_qa, text="예상 Q&A")
        self.text_qa = scrolledtext.ScrolledText(self.tab_qa, wrap=tk.WORD, width=80, height=30, font=("맑은 고딕", 11))
        self.text_qa.pack(padx=10, pady=10)

        # 저장 버튼
        save_button = tk.Button(master, text="기사 저장하기", command=self.save_article, font=("맑은 고딕", 11))
        save_button.pack(pady=10)

        # 첫 기사 로드
        self.load_article(self.article_urls[self.current_index])

    def update_gui(self, title, full_text, summary, annotations_list, qa_text):
        self.master.title(f"전기신문 기사 분석 - {title}")
        
        # 전체 기사 탭 업데이트 (중요어 하이라이트 적용)
        self.text_full.configure(state="normal")
        self.text_full.delete(1.0, tk.END)
        self.text_full.insert(tk.END, full_text)
        # 중요어 하이라이트: annotate_text()에 정의된 단어들을 전체 기사 텍스트에서 검색
        important_terms = {term for term, _ in annotations_list}
        for term in important_terms:
            start = "1.0"
            while True:
                pos = self.text_full.search(term, start, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(term)}c"
                self.text_full.tag_add(term, pos, end)
                start = end
            self.text_full.tag_config(term, foreground="red", font=("맑은 고딕", 11, "bold"))
        self.text_full.configure(state="disabled")
        
        # 요약 탭 업데이트
        self.text_summary.configure(state="normal")
        self.text_summary.delete(1.0, tk.END)
        self.text_summary.insert(tk.END, summary)
        self.text_summary.configure(state="disabled")
        
        # 주석 탭 업데이트: 동적 주석 내용 표시 (각 항목 줄바꿈)
        annotations_text = "\n\n".join(f"{term}: {definition}" for term, definition in annotations_list)
        self.text_annotation.configure(state="normal")
        self.text_annotation.delete(1.0, tk.END)
        self.text_annotation.insert(tk.END, annotations_text)
        self.text_annotation.configure(state="disabled")
        
        # 예상 Q&A 탭 업데이트: 주석에서 추출한 단어 기반 질문 생성
        qa_text = get_expected_qa(title, annotations_list)
        self.text_qa.configure(state="normal")
        self.text_qa.delete(1.0, tk.END)
        self.text_qa.insert(tk.END, qa_text)
        self.text_qa.configure(state="disabled")
    
    def load_article(self, url):
        self.master.config(cursor="watch")
        self.master.update()
        title, full_text = fetch_article_with_selenium(url)
        summary = summarize_text(full_text, n_sentences=3)
        annotations_list = annotate_text(full_text)
        qa_text = get_expected_qa(title, annotations_list)
        self.update_gui(title, full_text, summary, annotations_list, qa_text)
        self.master.config(cursor="")

    def load_previous(self):
        self.current_index = (self.current_index - 1) % len(self.article_urls)
        self.load_article(self.article_urls[self.current_index])

    def load_next(self):
        self.current_index = (self.current_index + 1) % len(self.article_urls)
        self.load_article(self.article_urls[self.current_index])

    def load_random(self):
        self.current_index = random.randint(0, len(self.article_urls) - 1)
        self.load_article(self.article_urls[self.current_index])

    def save_article(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="기사 저장하기"
        )
        if file_path:
            try:
                content = self.text_full.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("저장 성공", f"기사 내용이 {file_path}에 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("저장 실패", str(e))

##############################
# 메인 실행부
##############################
if __name__ == "__main__":
    # 모든 기사 URL을 동적으로 수집 (전기신문 홈페이지 기준)
    article_urls = fetch_all_article_urls()
    if not article_urls:
        messagebox.showerror("오류", "기사 URL을 가져올 수 없습니다.")
        exit(1)
    # 기사 URL 목록을 랜덤하게 섞음
    random.shuffle(article_urls)
    root = tk.Tk()
    app = ArticleApp(root, article_urls)
    root.mainloop()
