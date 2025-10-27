from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from service.chunk_service import chunk_html, store_chunk
from service.db_service import init_db
from agent import Agent
import json
import re
import traceback
import sqlite3

agent = None
app = FastAPI(title= "LLM Agent API")

init_db()

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
        chunks = chunk_html(request.content)
        for section in chunks:
            store_chunk(request.url, section) 
            ###### Dockerisation sqlite à faire !!!!!!!!!!!
    except Exception as e:
        print(e)
    