import os
import uvicorn
from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from service import AgentService
from agents.base_agent import BaseAgent
from agents.parser_agent import TestScenarioAgent
# from agents.rag_agent_2 import HTMLRagAgent
from util import AskRequest, FindRequest
from service import add_chunks, use_chunk_html
from agents.html_finder_agent import HtmlFinder

# --- Initialisation du service des agents ---
# agent_service = AgentService()

# --- Création de l'app FastAPI ---
agent = BaseAgent(
    name="TestAgent",
    description="Agent pour test API",
    system_prompt="You are a helpful assistant.",
    tools=[]  # tu peux ajouter des outils si nécessaire
)
parser = TestScenarioAgent()
app = FastAPI(title="LLM Agent API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:8081")],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# --- Endpoints ---
@app.get("/")
def root():
    return {"message": "API LLM is up"}


@app.post("/askagent")
def ask_agent(request: AskRequest):
    try:
        response = agent.query(request.question)
        return {"answer": response}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/parse")
def parse_scenario(request: AskRequest):
    try:
        response = parser.analyze_scenario(request.question)
        return {"answer":response}
    except Exception as e:
        print(e)
        raise HTTPException(status_code = 500, detail= str(e))

@app.post("/find/v1")
def findHtmlv1(request:FindRequest):
    """
    Gen custom Id 
    split html in chunks
    Save chunks (url , customId, chunk)

    """
    try:
        agent = HtmlFinder()
        chunked_html = use_chunk_html(request.htmlcontent)
        add_chunks(request.url, chunked_html)
        query = request.action + request.target
        return agent.search_element(url= request.url, query = query)
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))

@app.post("/find/v0")
def findHtml(request:AskRequest):
    try:
        db_path = "test_html.db"
    
        # Initialiser l'agent
        agent = HtmlFinder()
        
        # Ajouter des chunks HTML (en anglais)
        test_chunks = [
            '<button id="login-btn" class="btn btn-primary">Login</button>',
            '<input type="email" id="email" name="user_email" placeholder="Email">',
            '<input type="password" id="pwd" placeholder="Password">',
            '<a href="/forgot-password" class="link">Forgot password?</a>',
            '<button type="submit" id="submit">Submit</button>',
        ]
        
        add_chunks(
            url="https://example.com/"+request.question,
            chunks=test_chunks
        )
    
        # Test avec queries en français
        queries = [
            "click bouton login",

        ]
        result = []
        for query in queries:
            element  = agent.search_element(
                url="https://example.com/"+request.question,
                query=query
            )
            result.append(element)
        
        # if "error" not in result:
        #     print(f"\n Résultat:")
        #     print(f"   Type: {result['element']['type']}")
        #     print(f"   CSS: {result['element']['selector']['css']}")
        #     print(f"   Action: {result['element']['action']}")
        # print("\n" + "="*70)
        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))

# --- Lancement via Uvicorn ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
    
