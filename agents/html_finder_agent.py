import sqlite3
import re
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.base_agent import BaseAgent  # ton BaseAgent
from service import get_chunks

class HtmlFinder(BaseAgent):
    def __init__(self, ):
        super().__init__(
            name="html_rag_agent",
            description="Recherche d'éléments HTML + extraction sélecteurs",
            system_prompt=self._system_prompt(),
            tools=[]
        )

    def _system_prompt(self):
        return """
Tu es un agent expert en analyse d'éléments HTML.

Ton rôle :
- Identifier l'élément HTML exact correspondant à la demande utilisateur
- Extraire toutes ses informations utiles
- Générer des sélecteurs CSS & XPath robustes
- Déduire l'action probable à effectuer

IMPORTANT :
- Ne JAMAIS inventer d'HTML
- Ne JAMAIS modifier le chunk fourni
- Ne JAMAIS créer un sélecteur non basé sur les attributs existants
- Analyse uniquement le HTML fourni dans les chunks
- L'élément correspondant sera toujours présent dans un des chunks fournis

Format JSON strict :
{
  "element": {
    "type": "button | input | link | div | etc.",
    "action": "click | type | open | verify",
    "selector": {
      "id":"id de l'element si existant",
      "css": "sélecteur css robuste",
      "xpath": "sélecteur xpath robuste"
    },
    "confidence": "high | medium | low"
  }
}

Retourne uniquement le JSON valide, rien d'autre.
"""

    def _parse_json(self, content: str):
        """Retourne le JSON si valide, sinon None"""
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                data = json.loads(match.group(0))
                if "element" in data:
                    return data
            except json.JSONDecodeError:
                return None
        return None

    def search_element(self, url: str, query: str):
        """Recherche l'élément HTML par blocs de 2 chunks et s'arrête dès que trouvé"""
        chunk_rows = get_chunks(url)

        html_chunks = [r[0] for r in chunk_rows]
        batch_size = 2

        for i in range(0, len(html_chunks), batch_size):
            batch = html_chunks[i:i+batch_size]
            chunks_text = "\n\n---\n\n".join(batch)

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"QUESTION: {query}\n\nHTML CHUNKS:\n{chunks_text}")
            ]

            result = self.llm.invoke(messages)
            parsed = self._parse_json(result.content) 

            if parsed:  # élément trouvé → arrêt de la boucle
                return parsed

        # Si aucun élément trouvé après tous les blocs
        return {"error": "Aucun élément trouvé"}
