import re
from bs4 import BeautifulSoup
from service.db_service import insert_chunk
from html_chunking import get_html_chunks
import sqlite3


def useChunkHtml(
    html, max_tokens: int = 300, is_clean_html: bool = True, attr_cuttoff_len: int = 25
):
    return get_html_chunks(html, max_tokens, is_clean_html, attr_cuttoff_len)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def store_chunk(url: str, chunk: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    sql_insert = "INSERT INTO htmlchunk (url, chunk) VALUES (?, ?)"
    cursor.execute(sql_insert, (url, chunk))
    lastRowId = cursor.lastrowid
    conn.commit()
    conn.close()
    return lastRowId
