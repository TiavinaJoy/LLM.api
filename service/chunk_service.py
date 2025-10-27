import re
from bs4 import BeautifulSoup

def clean_text(text:str) -> str:
    text = re.sub(r'\s+',' ',text)
    return text.strip()

def chunk_html(html: str, max_chunk_size: int = 2000):
    soup = BeautifulSoup(html, "html.parser")
    chunks = []

    sections = soup.find_all(["section", "article", "div", "form"])
    if not sections:
        sections = [soup.body or soup]

    for sec in sections:
        text = clean_text(sec.get_text(separator=" ", strip=True))
        if not text:
            continue

        if len(text) > max_chunk_size:
            for i in range(0, len(text), max_chunk_size):
                chunks.append(text[i:i + max_chunk_size])
        else:
            chunks.append(text)
    return chunks