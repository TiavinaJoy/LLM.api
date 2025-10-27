from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import Agent
import json
import re
import traceback
import sqlite3
DB_NAME = "llm_api.db"
agent = None
app = FastAPI(title= "LLM Agent API")



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


class AskRequest(BaseModel):
    prompt: str

class FindHtmlRequest(BaseModel):
    url: str
    content: str

@app.on_event("startup")
def start_app():
    init_db()
    agent = Agent()


@app.get("/health")
async def health_check():
    return {"status": "ok", "llm_agent":agent.is_ready()}

@app.post("/ask")
async def ask_llm(request:AskRequest):
    try:
        raw_response = agent.ask(request.prompt)
        print(raw_response)
        # Nettoyage : enlever ```json ... ``` si présent
        cleaned = re.sub(r"```json\s*|```", "", raw_response, flags=re.IGNORECASE).strip()
        # Essayer de parser en JSON
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # si impossible, renvoyer juste texte
            parsed = {"response": cleaned}
        return parsed
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/findHtml")
async def findHtml(request: FindHtmlRequest):
    try:
        print(request.url, request.content)
    except Exception as e:
        print(e)
    