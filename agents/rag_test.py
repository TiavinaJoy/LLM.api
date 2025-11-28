"""
Test de recherche vectorielle avec des BLOCS HTML réalistes
"""
import sqlite3
import os

# Chunks HTML réalistes (blocs regroupés logiquement)
HTML_BLOCKS = {
    "https://example.com/login": [
        # Bloc 1: En-tête de page
        """
        <header class="navbar">
            <div class="logo">
                <img src="/logo.png" alt="Company Logo">
            </div>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
        </header>
        """,
        
        # Bloc 2: Formulaire de connexion
        """
        <div class="login-form">
            <h2>Sign in to your account</h2>
            <form id="login-form" method="POST">
                <div class="form-group">
                    <label for="email">Email address</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="user_email"
                        class="form-control"
                        placeholder="Enter your email"
                        required
                    >
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="user_password"
                        class="form-control"
                        placeholder="Enter your password"
                        required
                    >
                    <small class="form-text">
                        <a href="/forgot-password" class="forgot-link">
                            Forgot your password?
                        </a>
                    </small>
                </div>
            </form>
        </div>
        """,
        
        # Bloc 3: Boutons d'action
        """
        <div class="action-buttons">
            <button 
                type="submit" 
                id="login-btn" 
                class="btn btn-primary btn-lg"
                form="login-form"
            >
                Login
            </button>
            <button 
                type="button" 
                id="google-login" 
                class="btn btn-outline-secondary"
            >
                <img src="/google-icon.png" alt="Google">
                Sign in with Google
            </button>
        </div>
        """,
        
        # Bloc 4: Pied de page du formulaire
        """
        <div class="form-footer">
            <p>Don't have an account?</p>
            <a href="/signup" class="signup-link">
                Create an account
            </a>
            <div class="terms">
                By signing in, you agree to our 
                <a href="/terms">Terms of Service</a> and 
                <a href="/privacy">Privacy Policy</a>
            </div>
        </div>
        """,
        
        # Bloc 5: Footer général
        """
        <footer class="page-footer">
            <div class="footer-content">
                <div class="social-links">
                    <a href="/facebook">Facebook</a>
                    <a href="/twitter">Twitter</a>
                </div>
                <p>© 2024 Company Name. All rights reserved.</p>
            </div>
        </footer>
        """
    ]
}

def create_test_database():
    """Crée une base de données de test avec des blocs HTML."""
    db_path = "test_html_blocks.db"
    
    # Supprimer l'ancienne DB si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Créer la table
    c.execute('''CREATE TABLE html_chunks
                 (url TEXT, chunk TEXT)''')
    
    # Insérer les blocs
    for url, chunks in HTML_BLOCKS.items():
        for chunk in chunks:
            c.execute("INSERT INTO html_chunks (url, chunk) VALUES (?, ?)",
                     (url, chunk.strip()))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created: {db_path}")
    print(f"📦 {len(HTML_BLOCKS['https://example.com/login'])} HTML blocks stored")
    
    return db_path


def test_searches():
    """Teste la recherche avec différentes queries en français."""
    from HTMLRagAgent_Multilingual import HTMLRagAgent
    
    # Créer la DB
    db_path = create_test_database()
    
    # Initialiser l'agent
    print("\n🚀 Initializing HTMLRagAgent...")
    agent = HTMLRagAgent(db_path=db_path, persist_dir="./chroma_test_blocks")
    
    # Queries de test en français
    test_queries = [
        ("trouve le bouton de connexion", "click"),
        ("trouve le champ email", "type"),
        ("trouve le lien mot de passe oublié", "click"),
        ("trouve le bouton google sign in", "click"),
        ("trouve le champ mot de passe", "type"),
        ("trouve le lien créer un compte", "click"),
    ]
    
    print("\n" + "="*70)
    print("TESTS DE RECHERCHE MULTILINGUE (FR → EN)")
    print("="*70)
    
    results = []
    
    for query, expected_action in test_queries:
        print(f"\n{'='*70}")
        result = agent.search_element(
            url="https://example.com/login",
            query=query,
            top_k=2  # Seulement 2 blocs car ils sont plus gros
        )
        
        if "error" not in result:
            element = result['element']
            print(f"\n✅ TROUVÉ:")
            print(f"   Type: {element['type']}")
            print(f"   Action: {element['action']}")
            print(f"   CSS: {element['selector']['css']}")
            print(f"   XPath: {element['selector']['xpath']}")
            print(f"   Confiance: {element.get('confidence', 'N/A')}")
            
            # Vérifier si l'action correspond
            if element['action'] == expected_action:
                print(f"   ✅ Action correcte attendue")
            else:
                print(f"   ⚠️  Action attendue: {expected_action}, reçue: {element['action']}")
            
            results.append({
                "query": query,
                "success": True,
                "element": element
            })
        else:
            print(f"\n❌ ERREUR: {result.get('error', 'Unknown error')}")
            results.append({
                "query": query,
                "success": False
            })
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"✅ Réussis: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['query']}")
    
    print("\n💡 Note: Les blocs HTML permettent une meilleure compréhension du contexte!")


if __name__ == "__main__":
    test_searches()