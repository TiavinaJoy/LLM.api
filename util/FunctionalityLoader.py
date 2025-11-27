import requests
import os

class FunctionalityLoader:
    @staticmethod
    def load_functionalities() -> list[str]:
        """
        Loads functionalities from the MCP server.
        """
        api_url = os.getenv("API_URL", "http://localhost:8001")
        
        # Option 1: GET request
        response = requests.get(
            f"{api_url}/functionalities",
        )
                
        if response.status_code == 200:
            data = response.json()
            return data["functionalities"]
        else:
            raise Exception(f"Error loading functionalities: {response.text}")

