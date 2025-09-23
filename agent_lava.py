from llama_cpp import Llama
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()
hf_token = os.getenv("HF_ACCESS_TOKEN")
os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
N_CTX = 4096  # Taille du contexte souhaitée

class Agent:
    def __init__(self):
        self.model_repo = "second-state/Llava-v1.5-7B-GGUF"  # Hugging Face repo LLaVA v1.5 7B
        self.model = None
        self.ready = False
        print("threading...")
        threading.Thread(target=self.__load_agent, daemon=True).start()
        while not self.is_ready():
            print("Chargement du modèle")
            time.sleep(10)
        print(f"is READY === {self.ready}")

    def __load_agent(self):
        try:
            # Charge le modèle depuis Hugging Face (download automatique si absent)
            self.model = Llama.from_pretrained(
                repo_id=self.model_repo,
                n_ctx=N_CTX,
                verbose=False,
                use_auth_token=True
            )
            self.ready = True
            print('Modèle prêt')
        except Exception as e:
            import traceback
            print(f"Erreur lors du chargement du modèle: {e}")
            traceback.print_exc()
            self.ready = False
            return
        print("Sortie du thread de chargement")

    def is_ready(self) -> bool:
        return self.ready

    def get_max_tokens(self, prompt: str):
        # Tokenize pour calculer le nombre max de tokens restant
        tokens = self.model.tokenize(prompt.encode('utf-8'))
        return max(0, N_CTX - len(tokens))

    def ask(self, prompt: str) -> str:
        print(prompt)
        if self.model is None:
            self.__load_agent()
        self.model.reset()
        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        formatted_prompt = formatted_prompt.encode('utf-8', errors='ignore').decode('utf-8')

        # Stop tokens spécifiques à Phi-3/LLaVA
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
            repeat_penalty=1.1
        )
        return response['choices'][0]['text']
