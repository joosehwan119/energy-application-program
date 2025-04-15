import re
# 이번에는 자동 추출 대신 커스텀 사전 항목만 사용합니다.

def annotate_text(text):
    # 전기에 관련된 단어 3개에 대한 정의 (국어사전 스타일)
    elec_dict = {
        "전압": "전압: 회로 내 전위차를 나타내며, 전기 에너지 전달에 필수적입니다.",
        "전류": "전류: 전하의 흐름으로, 전기 에너지의 이동을 나타냅니다.",
        "회로": "회로: 전기 부품들이 연결되어 전류가 흐르는 경로입니다."
    }
    results = []
    # 텍스트에 해당 단어들이 존재하는지 확인합니다.
    for term, definition in elec_dict.items():
        if term in text:
            results.append((term, definition))
    # 만약 3개 미만으로 찾으면 기본 항목으로 채웁니다.
    if len(results) < 3:
        results = list(elec_dict.items())
    return results[:3]
