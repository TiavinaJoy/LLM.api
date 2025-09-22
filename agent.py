from llama_cpp import Llama
import os
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import threading
import time

load_dotenv()
hf_token = os.getenv("HF_ACCESS_TOKEN")
os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token

class Agent:
    def __init__(self):
        self.model_name = "Phi-3-mini-4k-instruct-q4.gguf"
        self.model_repo = "microsoft/Phi-3-mini-4k-instruct-gguf"
        self.model_path = os.path.join("models", self.model_name)
        self.model = None
        self.ready = False
        print("threading...")
        threading.Thread(target=self.__load_agent, daemon=True).start()
        while not self.is_ready():
            print("Chargement du modele")
            time.sleep(10)
        print(f"is READY ==={self.ready}")
        # self.__load_agent()

    def __load_agent(self):
        os.makedirs("models", exist_ok=True)
        if not os.path.exists(self.model_path):
            print(f"Téléchargement du modèle...")
            hf_hub_download(
                repo_id = self.model_repo,
                filename = self.model_name,
                local_dir ="models"
            )
            print(f"Téléchargement terminé")
        else:
            print("Modèle déjà téléchargé")
        try:
            self.model = Llama(model_path=self.model_path, verbose = False)
            self.ready = True
            print('Modèle prêt')
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.ready = False
            return
        print("Sortie du thread de chargement")
        

    def is_ready(self) ->bool:
        return self.ready
    
    def ask(self, prompt:str) ->str:
        print(prompt)
        if self.model is None:
            self.__load_agent()

        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        
        # Stop tokens spécifiques à Phi-3
        stop_tokens = [
            "<|end|>", 
            "<|user|>", 
            "<|assistant|>",
            "\n\n\n",  # Évite les générations trop longues
            "###",
            "Instruction",  # Évite les "Instruction 2", etc.
        ]
        response = self.model(
            formatted_prompt, 
            max_tokens = 512, 
            temperature = 0.1, 
            stop=stop_tokens, 
            echo = False, 
            repeat_penalty= 1.1
        )
        return response['choices'][0]['text']
        