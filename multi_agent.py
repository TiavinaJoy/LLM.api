"""
Système Multi-Agent pour QA Testing IA
Architecture: Agent Simple (base) + Agent RAG (héritage)
Les chunks HTML (~300 tokens) sont pré-insérés - le LLM gère la recherche
"""

import sqlite3
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ChunkResult:
    """Résultat d'un chunk trouvé"""
    id: int
    url: str
    chunk: str


class AgentSimple:
    """Agent de base pour les requêtes simples avec Phi"""
    
    def __init__(self, model_name: str = "phi"):
        self.model_name = model_name
        self.conversation_history = []
    
    def ask(self, question: str) -> str:
        """
        Pose une question simple au modèle Phi
        
        Args:
            question: La question de l'utilisateur
            
        Returns:
            La réponse du modèle
        """
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        response = self._call_phi(question)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _call_phi(self, prompt: str) -> str:
        """
        Appel au modèle Phi
        À implémenter avec l'API Phi réelle
        
        Exemple avec ollama:
        import ollama
        response = ollama.chat(model='phi', messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
        """
        return f"[Réponse Phi pour: {prompt}]"
    
    def reset_history(self):
        """Réinitialise l'historique de conversation"""
        self.conversation_history = []


class AgentRAG(AgentSimple):
    """
    Agent RAG qui hérite de AgentSimple
    Lit les chunks pré-insérés et laisse le LLM analyser le HTML
    """
    
    def __init__(self, db_path: str, model_name: str = "phi"):
        super().__init__(model_name)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _check_chunk_relevance(self, chunk: str, user_query: str) -> Optional[str]:
        """
        Demande au LLM si le chunk contient l'élément recherché
        
        Args:
            chunk: Le chunk HTML à analyser
            user_query: La requête de l'utilisateur
            
        Returns:
            Le sélecteur optimal si trouvé, None sinon
        """
        prompt = f"""Analyse ce chunk HTML et détermine s'il contient l'élément nécessaire pour réaliser l'objectif.

Chunk HTML:
{chunk}

Objectif: {user_query}

Si le chunk contient l'élément qui permet de réaliser cet objectif:
- Réponds avec le sélecteur CSS ou XPath le plus optimal et robuste pour cibler cet élément
- Privilégie dans l'ordre: id, data-testid, name, puis classe unique, puis XPath
- Format: SELECTEUR: ton_selecteur

Si le chunk ne contient PAS l'élément:
- Réponds UNIQUEMENT: NON

Exemples:
- Si objectif "Valider le formulaire" et que tu trouves <button type="submit" id="submit-btn">: réponds "SELECTEUR: #submit-btn"
- Si objectif "Saisir l'email" et que tu trouves <input name="email" id="email-input">: réponds "SELECTEUR: #email-input"
- Si l'élément n'existe pas: réponds "NON"
"""

        response = self._call_phi(prompt).strip()
        
        if response.startswith("SELECTEUR:"):
            return response.replace("SELECTEUR:", "").strip()
        return None
    
    def find_element(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Trouve un élément HTML en parcourant les chunks un par un
        S'arrête dès qu'un chunk pertinent est trouvé
        
        Args:
            user_query: L'objectif de l'utilisateur (ex: "Valider le formulaire")
            
        Returns:
            Dict avec le chunk et le sélecteur optimal, ou None
        """
        # Parcourir tous les chunks un par un
        self.cursor.execute("SELECT id, url, chunk FROM html_chunks")
        
        for row in self.cursor:
            chunk_id, url, chunk = row
            
            # Demander au LLM si ce chunk contient l'élément et obtenir le sélecteur
            selector = self._check_chunk_relevance(chunk, user_query)
            
            if selector:
                # Élément trouvé - s'arrêter immédiatement
                return {
                    "chunk": ChunkResult(id=chunk_id, url=url, chunk=chunk),
                    "selector": selector
                }
        
        return None
    
    def ask_with_rag(self, user_query: str) -> Dict[str, Any]:
        """
        Pose une question avec recherche RAG
        Le LLM trouve l'élément et retourne le sélecteur optimal
        
        Args:
            user_query: L'objectif de l'utilisateur (ex: "Valider le formulaire")
            
        Returns:
            Dict avec la réponse, le sélecteur optimal et le contexte trouvé
        """
        # Chercher le chunk contenant l'élément
        result = self.find_element(user_query)
        
        if result:
            chunk_result = result["chunk"]
            selector = result["selector"]
            
            # Construire le prompt avec le contexte trouvé
            context_prompt = f"""Tu es un assistant QA spécialisé dans les tests d'interface web.

Contexte trouvé:
URL: {chunk_result.url}
Chunk HTML:
{chunk_result.chunk}

Objectif de l'utilisateur: {user_query}
Sélecteur optimal identifié: {selector}

Explique pourquoi ce sélecteur est le meilleur choix pour réaliser cet objectif.
Mentionne les attributs de l'élément et pourquoi ce sélecteur est robuste."""

            response = self._call_phi(context_prompt)
            
            return {
                "response": response,
                "found_chunk": True,
                "selector": selector,
                "chunk_id": chunk_result.id,
                "url": chunk_result.url,
                "chunk": chunk_result.chunk
            }
        else:
            # Pas de chunk pertinent trouvé - utiliser l'agent simple
            fallback_prompt = f"""Aucun élément HTML correspondant n'a été trouvé dans la base de données.

Objectif: {user_query}

Explique quel type d'élément serait nécessaire pour réaliser cet objectif et donne des exemples de sélecteurs typiques."""
            
            response = self._call_phi(fallback_prompt)
            
            return {
                "response": response,
                "found_chunk": False,
                "selector": None,
                "message": "Aucun élément HTML correspondant trouvé dans la base"
            }
    
    def get_chunk_count(self) -> int:
        """Retourne le nombre total de chunks dans la base"""
        self.cursor.execute("SELECT COUNT(*) FROM html_chunks")
        return self.cursor.fetchone()[0]
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[ChunkResult]:
        """Récupère un chunk spécifique par son ID"""
        self.cursor.execute(
            "SELECT id, url, chunk FROM html_chunks WHERE id = ?",
            (chunk_id,)
        )
        row = self.cursor.fetchone()
        
        if row:
            return ChunkResult(id=row[0], url=row[1], chunk=row[2])
        return None
    
    def list_urls(self) -> List[str]:
        """Liste toutes les URLs distinctes dans la base"""
        self.cursor.execute("SELECT DISTINCT url FROM html_chunks")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_chunks_by_url(self, url: str) -> List[ChunkResult]:
        """Récupère tous les chunks d'une URL spécifique"""
        self.cursor.execute(
            "SELECT id, url, chunk FROM html_chunks WHERE url = ?",
            (url,)
        )
        return [
            ChunkResult(id=row[0], url=row[1], chunk=row[2])
            for row in self.cursor.fetchall()
        ]
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()
    
    def __del__(self):
        """Destructeur pour fermer la connexion"""
        if hasattr(self, 'conn'):
            self.close()


# Exemple d'utilisation
if __name__ == "__main__":
    print("=== Agent Simple ===")
    agent_simple = AgentSimple()
    response = agent_simple.ask("Qu'est-ce qu'un test QA?")
    print(f"Réponse: {response}\n")
    
    print("=== Agent RAG ===")
    agent_rag = AgentRAG("qa_chunks.db")
    
    # Statistiques
    print(f"📊 Nombre de chunks dans la base: {agent_rag.get_chunk_count()}")
    urls = agent_rag.list_urls()
    print(f"📊 URLs distinctes: {len(urls)}")
    for url in urls[:3]:  # Afficher les 3 premières
        print(f"  - {url}")
    print()
    
    # Recherche d'élément par objectif
    print("--- Objectif: 'Valider le formulaire' ---")
    result = agent_rag.ask_with_rag("Valider le formulaire")
    
    if result['found_chunk']:
        print(f"✓ Élément trouvé!")
        print(f"🎯 Sélecteur optimal: {result['selector']}")
        print(f"URL: {result['url']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"\nChunk HTML:\n{result['chunk']}\n")
    else:
        print(f"✗ Élément non trouvé")
    
    print(f"Réponse du LLM:\n{result['response']}\n")
    
    # Autres exemples d'objectifs
    print("--- Objectif: 'Saisir l'adresse email' ---")
    result = agent_rag.ask_with_rag("Saisir l'adresse email")
    if result['found_chunk']:
        print(f"🎯 Sélecteur optimal: {result['selector']}")
    print(f"Réponse: {result['response']}\n")
    
    print("--- Objectif: 'Cliquer sur le lien de déconnexion' ---")
    result = agent_rag.ask_with_rag("Cliquer sur le lien de déconnexion")
    if result['found_chunk']:
        print(f"🎯 Sélecteur optimal: {result['selector']}")
    print(f"Réponse: {result['response']}\n")
    
    agent_rag.close()