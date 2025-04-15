import re
from collections import Counter

def basic_summarize(text, n_sentences=3):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= n_sentences:
        return text
    words = re.findall(r'\w+', text.lower())
    word_freq = Counter(words)
    sentence_scores = {}
    for sentence in sentences:
        sentence_words = re.findall(r'\w+', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in sentence_words)
        sentence_scores[sentence] = score
    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:n_sentences]
    top_sentences.sort(key=lambda s: sentences.index(s))
    return " ".join(top_sentences)

def deep_summarize(text, max_length=130, min_length=30):
    try:
        from transformers import pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        # 딥러닝 요약 실패 시 기본 요약 사용
        return basic_summarize(text)
