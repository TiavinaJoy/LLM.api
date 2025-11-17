import sqlite3
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# ---------------------------------------------------
# 🔥 AGENT PHI-3 = Classe de base
# ---------------------------------------------------
from llama_cpp import Llama
import os
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import threading
import time

load_dotenv()
hf_token = os.getenv("HF_ACCESS_TOKEN")
os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
N_CTX = 4096


class AgentPhi3:
    """Agent de base : Phi-3 réel"""

    def __init__(self):
        self.model_name = "Phi-3-mini-4k-instruct-q4.gguf"
        self.model_repo = "microsoft/Phi-3-mini-4k-instruct-gguf"
        self.model_path = os.path.join("models", self.model_name)
        self.model = None
        self.ready = False

        threading.Thread(target=self.__load_agent, daemon=True).start()
        while not self.is_ready():
            print("Chargement du modele…")
            time.sleep(10)

    def __load_agent(self):
        os.makedirs("models", exist_ok=True)

        if not os.path.exists(self.model_path):
            print(f"Téléchargement du modèle…")
            hf_hub_download(
                repo_id=self.model_repo, filename=self.model_name, local_dir="models"
            )
            print(f"Téléchargement terminé")
        else:
            print("Modèle déjà téléchargé")

        try:
            self.model = Llama(model_path=self.model_path, verbose=False, n_ctx=N_CTX)
            self.ready = True
            print("Modèle prêt")
        except Exception as e:
            print(f"Erreur: {e}")
            self.ready = False

    def is_ready(self) -> bool:
        return self.ready

    def get_max_tokens(self, prompt: str):
        tokens = self.model.tokenize(prompt.encode("utf-8"))
        return max(0, N_CTX - len(tokens))

    def _call_phi(self, prompt: str) -> str:
        """Méthode utilisée par AgentRAG pour appeler Phi-3"""
        if self.model is None:
            self.__load_agent()

        self.model.reset()

        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        formatted_prompt = formatted_prompt.encode("utf-8", errors="ignore").decode(
            "utf-8"
        )

        stop_tokens = [
            "<|end|>",
            "<|user|>",
            "<|assistant|>",
            "\n\n\n",
            "###",
            "Instruction",
        ]

        response = self.model(
            formatted_prompt,
            max_tokens=self.get_max_tokens(formatted_prompt),
            temperature=0.1,
            stop=stop_tokens,
            echo=False,
            repeat_penalty=1.1,
        )
        return response["choices"][0]["text"]


# ---------------------------------------------------
# 🔥 MULTI-RAG (inchangé)
# ---------------------------------------------------


@dataclass
class ChunkResult:
    id: int
    url: str
    chunk: str


class AgentRAG(AgentPhi3):
    """
    Agent RAG qui utilise directement Phi-3 comme base
    """

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _check_chunk_relevance(self, chunk: str, user_query: str) -> Optional[str]:
        prompt = f"""Analyse ce chunk HTML et détermine s'il contient l'élément nécessaire pour réaliser l'objectif.

Chunk HTML:
{chunk}

Objectif: {user_query}

Réponds "SELECTEUR: xxx" ou "NON".
"""
        response = self._call_phi(prompt).strip()

        if response.startswith("SELECTEUR:"):
            return response.replace("SELECTEUR:", "").strip()

        return None

    def find_element(self, user_query: str) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT id, url, chunk FROM html_chunks")

        for row in self.cursor:
            chunk_id, url, chunk = row
            selector = self._check_chunk_relevance(chunk, user_query)

            if selector:
                return {
                    "chunk": ChunkResult(id=chunk_id, url=url, chunk=chunk),
                    "selector": selector,
                }

        return None

    def ask_with_rag(self, user_query: str) -> Dict[str, Any]:
        result = self.find_element(user_query)

        if result:
            chunk_result = result["chunk"]
            selector = result["selector"]

            context_prompt = f"""Contexte HTML trouvé:
URL: {chunk_result.url}
Chunk:
{chunk_result.chunk}

Objectif: {user_query}
Sélecteur: {selector}

Explique pourquoi ce sélecteur est optimal.
"""

            response = self._call_phi(context_prompt)

            return {
                "response": response,
                "found_chunk": True,
                "selector": selector,
                "chunk_id": chunk_result.id,
                "url": chunk_result.url,
                "chunk": chunk_result.chunk,
            }

        fallback_prompt = f"""Aucun élément trouvé pour: {user_query}.
Explique quel élément serait nécessaire et un sélecteur typique."""

        response = self._call_phi(fallback_prompt)

        return {
            "response": response,
            "found_chunk": False,
            "selector": None,
            "message": "Aucun élément HTML correspondant trouvé",
        }

    def get_chunk_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM html_chunks")
        return self.cursor.fetchone()[0]

    def get_chunk_by_id(self, chunk_id: int) -> Optional[ChunkResult]:
        self.cursor.execute(
            "SELECT id, url, chunk FROM html_chunks WHERE id = ?", (chunk_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return ChunkResult(id=row[0], url=row[1], chunk=row[2])
        return None

    def list_urls(self) -> List[str]:
        self.cursor.execute("SELECT DISTINCT url FROM html_chunks")
        return [r[0] for r in self.cursor.fetchall()]

    def get_chunks_by_url(self, url: str) -> List[ChunkResult]:
        self.cursor.execute(
            "SELECT id, url, chunk FROM html_chunks WHERE url = ?", (url,)
        )
        return [
            ChunkResult(id=row[0], url=row[1], chunk=row[2])
            for row in self.cursor.fetchall()
        ]

    def close(self):
        self.conn.close()

    def __del__(self):
        if hasattr(self, "conn"):
            self.close()
