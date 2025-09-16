from agent import Agent  # ton code Agent doit être dans agent.py

def main():
    # Crée l'agent (le modèle sera chargé automatiquement)
    agent = Agent()
    print("Agent prêt !")

    prompt = "Répond seulement avec un JSON valide: Quelle est la capitale de la France ?"
    reponse = agent.ask(prompt)
    print(f"\n Réponse : {reponse}\n")

if __name__ == "__main__":
    main()
