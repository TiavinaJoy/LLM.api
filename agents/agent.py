import sqlite3
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

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


class Agent:
    """Agent de base : Phi-3"""

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

    def ask(self, prompt: str) -> str:
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
