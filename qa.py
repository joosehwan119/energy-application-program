def get_expected_qa(title, annotations_list):
    # Q&A를 자동 생성하는 대신 기사와 관련된 한 가지 질문을 생성합니다.
    if title:
        question = f"{title} 기사에서 가장 주목할 만한 내용은 무엇인가요?"
        answer = "기사의 주요 정보를 파악해보세요."
        return f"Q: {question}\nA: {answer}"
    else:
        return "예상 Q&A가 없습니다."
