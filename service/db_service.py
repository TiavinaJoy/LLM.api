import sqlite3

DB_NAME = "llm_api.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS htmlchunk( 
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   url TEXT NOT NULL, 
                   chunk TEXT NOT NULL 
                   );
""")
    conn.commit()
    conn.close()

def insert_chunk(url:str, chunk:str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("Insert into htmlchunk(url, chunk) VALUES (?, ?)", (url, chunk))
    conn.commit()
    conn.close()