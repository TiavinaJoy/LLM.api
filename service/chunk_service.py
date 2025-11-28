import re
from bs4 import BeautifulSoup
from html_chunking import get_html_chunks
import sqlite3
from typing import List, Dict

DB_NAME = "llm_api.db"

def use_chunk_html(
    html: str,
    max_tokens: int = 300,
    is_clean_html: bool = True,
    attr_cuttoff_len: int = 25
) -> List[str]:
    """
    Découpe un HTML en chunks et retourne une liste de strings.
    """
    chunks = get_html_chunks(html, max_tokens, is_clean_html, attr_cuttoff_len)
    return list(chunks)
    
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def add_chunks(url: str, chunks: List[str]):
        """
        Ajoute de nouveaux chunks HTML au vector store.
        
        Args:
            url: URL de la page
            chunks: Liste de chunks HTML
        """
        # Ajouter à SQLite
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS html_chunks
                     (url TEXT, chunk TEXT)''')
        
        c.executemany(
            "INSERT INTO html_chunks (url, chunk) VALUES (?, ?)",
            [(url, chunk) for chunk in chunks]
        )
        
        conn.commit()
        conn.close()

def get_chunks(url:str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT chunk FROM html_chunks WHERE url = ?", (url,))
    rows = c.fetchall()
    conn.close()
    return rows