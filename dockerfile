# Image Python officielle 
FROM python:3.11-slim 
# Installer dépendances système pour compiler llama-cpp-python 
RUN apt-get update && apt-get install -y \ 
    build-essential \ 
    cmake \ 
    git \ 
    && rm -rf /var/lib/apt/lists/*

# Créer le dossier de travail 
WORKDIR /app 
# Copier le requirements et installer les packages 
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt 
# Copier le reste du projet 
COPY . . 
# Commande par défaut 
CMD ["python", "main.py"]