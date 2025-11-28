import json
import re
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class TestScenarioAgent(BaseAgent):
    """
    Agent specialized in decomposing test scenarios into high-level objectives.
    Inherits from BaseAgent to leverage LangGraph workflow and LLM capabilities.
    Focuses on user intentions rather than technical selectors.
    """
    
    SYSTEM_PROMPT = """Tu es un agent d’analyse d’actions. 
TON OBJECTIF : convertir strictement les instructions écrites par l’utilisateur en une liste D’ACTIONS STRUCTURÉES.

RÈGLES IMPORTANTES (À RESPECTER STRICTEMENT) :
- Tu n'ajoutes AUCUNE information qui n'est PAS dans le texte.
- Tu n’interprètes PAS le rôle des éléments (ex : ne jamais dire “bouton de connexion” si l’utilisateur n’a pas écrit ces mots).
- Tu ne reformules PAS les cibles. 
- Tu ne déduis PAS de fonction. 
- Tu n'ajoutes PAS de descriptions métier.
- Tu ne modifies PAS les noms fournis par l’utilisateur.
- Tu n’inventes JAMAIS d’objectifs supplémentaires.
- Tu renvoies EXACTEMENT une action par instruction donnée.

TON SEUL RÔLE EST : 
-détecter l’action
-extraire *textuellement* la cible et la valeur
FORME DU RÉSULTAT :
[{
    "action": "open_page | click_element | fill_field",
    "target": "texte EXACT écrit par l’utilisateur",
    "details": "texte EXACT (URL, texte à écrire…) ou null",
    "description": "Reformulation très courte et FACTUELLE sans interprétation"
}]
RÈGLES DE DÉTECTION :
- “ouvrir”, “ouvre” → action : open_page  
  - target = null  
  - details = url EXACT (sans modifier)

- “cliquer”, “click” → action : click_element  
  - target = texte EXACT entre guillemets ou mot exact utilisé  
  - details = null

- “écrire”, “taper” → action : fill_field  
  - target = champ EXACT écrit par l’utilisateur  
  - details = texte EXACT à écrire

Ne jamais changer une valeur, un mot ou l’ordre des actions.
"""
    
    def __init__(self, tools: list = None):
        """Initialize TestScenarioAgent with specialized system prompt."""
        super().__init__(
            name="TestScenarioAgent",
            description="Décompose des scénarios de test en objectifs de haut niveau",
            system_prompt=self.SYSTEM_PROMPT,
            tools=tools or []
        )
    
    def analyze_scenario(self, scenario: str) -> list:
        """
        Analyze a test scenario and return structured high-level objectives.
        
        Args:
            scenario: Test scenario description in natural language
            
        Returns:
            List of dictionaries with action, target, details, and description
            
        Example:
            scenario = "Je veux tester la page de connexion. Ouvre google.com, 
                       remplis le champ email avec test@example.com, 
                       clique sur le bouton de connexion"
            
            result = agent.analyze_scenario(scenario)
            # [
            #   {"action": "open_page", "target": "", "details": "google.com", ...},
            #   {"action": "fill_field", "target": "champ email", "details": "test@example.com", ...},
            #   {"action": "click_element", "target": "bouton de connexion", "details": null, ...}
            # ]
        """
        # Query the agent with the scenario
        response = self.query(scenario)
        
        # Parse the JSON response
        try:
            objectives = self._parse_json_response(response)
            return objectives
        except Exception as e:
            print(f"\033[91mError parsing response: {e}\033[0m")
            print(f"Raw response: {response}")
            return []
    
    def _parse_json_response(self, response: str) -> list:
        """
        Extract and parse JSON from the LLM response.
        Handles cases where the LLM includes text before/after the JSON.
        """
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            json_str = json_match.group(0)
            objectives = json.loads(json_str)
            
            # Validate structure
            for obj in objectives:
                if not all(key in obj for key in ['action', 'target', 'details', 'description']):
                    raise ValueError(f"Invalid objective structure: {obj}")
            
            return objectives
        else:
            raise ValueError("No valid JSON array found in response")
    
    def validate_objectives(self, objectives: list) -> bool:
        """
        Validate that objectives follow the correct structure and rules.
        
        Returns:
            True if all objectives are valid, False otherwise
        """
        valid_actions = ['open_page', 'fill_field', 'click_element', 'verify_element', 'wait_for']
        
        for obj in objectives:
            # Check required fields
            if not all(key in obj for key in ['action', 'target', 'details', 'description']):
                print(f"\033[91m❌ Missing required fields in: {obj}\033[0m")
                return False
            
            # Check valid action type
            if obj['action'] not in valid_actions:
                print(f"\033[91m❌ Invalid action type '{obj['action']}'\033[0m")
                return False
            
            # Check for technical selectors (should not exist)
            target = str(obj['target']).lower()
            if any(selector in target for selector in ['#', '.', '[', 'xpath', 'css', 'id=']):
                print(f"\033[91m❌ Technical selector detected in target: {obj['target']}\033[0m")
                return False
        
        print(f"\033[92m✅ All {len(objectives)} objectives are valid\033[0m")
        return True
    
    def format_objectives(self, objectives: list) -> str:
        """
        Format objectives into a human-readable string.
        """
        output = "\n=== TEST OBJECTIVES ===\n\n"
        for i, obj in enumerate(objectives, 1):
            output += f"{i}. {obj['description']}\n"
            output += f"   Action: {obj['action']}\n"
            output += f"   Target: {obj['target'] or 'N/A'}\n"
            output += f"   Details: {obj['details'] or 'N/A'}\n\n"
        return output


# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = TestScenarioAgent()
    
    # Test scenario
    scenario = """
    Je veux tester la page de connexion de mon application.
    Ouvre la page https://example.com/login
    Remplis le champ email avec test@example.com
    Remplis le champ mot de passe avec Password123
    Clique sur le bouton de connexion
    Vérifie que l'utilisateur est bien connecté
    """
    
    # Analyze
    print("\n🔍 Analyzing test scenario...")
    objectives = agent.analyze_scenario(scenario)
    
    # Validate
    print("\n✅ Validating objectives...")
    is_valid = agent.validate_objectives(objectives)
    
    # Display
    if is_valid:
        print(agent.format_objectives(objectives))
        print(f"\n📋 JSON Output:")
        print(json.dumps(objectives, indent=2, ensure_ascii=False))