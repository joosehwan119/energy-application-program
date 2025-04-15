import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
from article.fetch import fetch_article_with_selenium
from article.summarize import deep_summarize
from article.annotate import annotate_text
from article.qa import get_expected_qa

class ArticleApp:
    def __init__(self, master):
        self.master = master
        master.title("전기신문 기사 분석 및 응용")

        # URL 입력 프레임
        url_frame = tk.Frame(master)
        url_frame.pack(pady=5)
        tk.Label(url_frame, text="기사 URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = tk.Entry(url_frame, width=80, font=("맑은 고딕", 10))
        self.url_entry.pack(side=tk.LEFT, padx=5)
        load_button = tk.Button(url_frame, text="불러오기", command=self.load_article_by_url, font=("맑은 고딕", 10))
        load_button.pack(side=tk.LEFT, padx=5)
        
        # Notebook 탭 생성 (전체 기사, 요약, 주석, 예상 Q&A)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")
        
        self.tab_full = tk.Frame(self.notebook)
        self.notebook.add(self.tab_full, text="전체 기사")
        self.text_full = scrolledtext.ScrolledText(self.tab_full, wrap=tk.WORD, font=("맑은 고딕", 11))
        self.text_full.pack(padx=10, pady=10, expand=True, fill="both")
        
        self.tab_summary = tk.Frame(self.notebook)
        self.notebook.add(self.tab_summary, text="요약")
        self.text_summary = scrolledtext.ScrolledText(self.tab_summary, wrap=tk.WORD, font=("맑은 고딕", 11))
        self.text_summary.pack(padx=10, pady=10, expand=True, fill="both")
        
        self.tab_annotation = tk.Frame(self.notebook)
        self.notebook.add(self.tab_annotation, text="주석")
        self.text_annotation = scrolledtext.ScrolledText(self.tab_annotation, wrap=tk.WORD, font=("맑은 고딕", 11))
        self.text_annotation.pack(padx=10, pady=10, expand=True, fill="both")
        
        self.tab_qa = tk.Frame(self.notebook)
        self.notebook.add(self.tab_qa, text="예상 Q&A")
        self.text_qa = scrolledtext.ScrolledText(self.tab_qa, wrap=tk.WORD, font=("맑은 고딕", 11))
        self.text_qa.pack(padx=10, pady=10, expand=True, fill="both")
        
        # 저장 버튼
        save_button = tk.Button(master, text="기사 저장하기", command=self.save_article, font=("맑은 고딕", 11))
        save_button.pack(pady=10)
    
    def update_gui(self, title, full_text, summary, annotations_list, qa_text):
        self.master.title(f"전기신문 기사 분석 - {title}")
        # 전체 기사 탭 업데이트
        self.text_full.config(state="normal")
        self.text_full.delete(1.0, tk.END)
        self.text_full.insert(tk.END, full_text)
        self.text_full.config(state="disabled")
        
        # 요약 탭 업데이트
        self.text_summary.config(state="normal")
        self.text_summary.delete(1.0, tk.END)
        self.text_summary.insert(tk.END, summary)
        self.text_summary.config(state="disabled")
        
        # 주석 탭 업데이트
        annotations_text = "\n\n".join(f"{term}: {definition}" for term, definition in annotations_list)
        self.text_annotation.config(state="normal")
        self.text_annotation.delete(1.0, tk.END)
        self.text_annotation.insert(tk.END, annotations_text)
        self.text_annotation.config(state="disabled")
        
        # 예상 Q&A 탭 업데이트
        self.text_qa.config(state="normal")
        self.text_qa.delete(1.0, tk.END)
        self.text_qa.insert(tk.END, qa_text)
        self.text_qa.config(state="disabled")
    
    def load_article_by_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("오류", "URL을 입력하세요.")
            return
        self.master.config(cursor="watch")
        self.master.update()
        title, full_text = fetch_article_with_selenium(url)
        summary = deep_summarize(full_text)
        annotations_list = annotate_text(full_text)
        qa_text = get_expected_qa(title, annotations_list)
        self.update_gui(title, full_text, summary, annotations_list, qa_text)
        self.master.config(cursor="")
    
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
